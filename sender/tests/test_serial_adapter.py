import contextlib
import io
import json
import sys
import unittest
from unittest.mock import Mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from sender.serial_adapter import C, SerialAdapter, clean_text, open_local_port, poll_once
from sender import serial_cli
from shared.python.contract import validate_event


def line(name, **fields):
    return json.dumps({'v': 1, 'event': name, **fields}).encode() + b'\n'


class SerialChecks(unittest.TestCase):
    def setUp(self):
        self.writes = []
        def write(data):
            self.writes.append(data)
            return len(data)
        self.adapter = SerialAdapter(write, lambda: '12345678')
        self.adapter.start(0)

    def ready(self):
        self.adapter.feed(line('hello', role='tx', max_text_bytes=C['MAX_TEXT_BYTES']) + line('ready'), 0.1)
        self.assertEqual(self.adapter.state, 'ready')

    def event(self, name, now=1, **fields):
        self.adapter.feed(line(name, **fields), now)

    def accepted(self, now=1):
        self.event('accepted', now, session='12345678', seq=0)

    def test_cleanup_and_bounds_no_silent_loss(self):
        self.assertEqual(clean_text(' \tSpirit,\r\n what is\vyour\fname? '), 'Spirit, what is your name?')
        self.assertEqual(clean_text('x' * 48), 'x' * 48)
        for text in ('', ' \n', 'x' * 49, 'é', 'Hi\0', 'Hi\x1c', 'x' * 4097):
            with self.subTest(text=repr(text[:50])), self.assertRaises(ValueError):
                clean_text(text)

    def test_shared_event_fixtures_with_split_reads(self):
        fixtures = json.loads((ROOT / 'shared/fixtures/events.json').read_text())
        for fixture in fixtures:
            if fixture['role'] != 'tx':
                continue
            with self.subTest(fixture=fixture['id']):
                if fixture['valid']:
                    validate_event(fixture['value'], 'tx')
                else:
                    before = len(self.adapter.diagnostics)
                    data = json.dumps(fixture['value']).encode() + b'\n'
                    for byte in data:
                        self.adapter.feed(bytes([byte]), 0.1)
                    self.assertGreater(len(self.adapter.diagnostics), before)
        self.assertEqual(self.adapter.state, 'handshake')

    def test_handshake_requires_hello_then_ready(self):
        self.assertEqual(self.writes, [b'HELLO\n'])
        self.event('ready', 0.1)
        self.assertEqual(self.adapter.state, 'handshake')
        self.adapter.feed(b'{"v":1,"event":"hello","role":"rx","max_text_bytes":48}\n', 0.1)
        self.event('ready', 0.1)
        self.assertEqual(self.adapter.state, 'handshake')
        self.ready()

    def test_boot_timeout_and_late_events_require_explicit_reconnect(self):
        self.adapter.tick(C['HOST_BOOT_TIMEOUT_MS'] / 1000)
        self.assertEqual(self.adapter.state, 'reconnect_required')
        self.adapter.feed(line('hello', role='tx', max_text_bytes=48) + line('ready'), 6)
        self.assertEqual(self.adapter.state, 'reconnect_required')
        self.adapter.start(7)
        self.adapter.feed(line('hello', role='tx', max_text_bytes=48) + line('ready'), 7.1)
        self.assertEqual(self.adapter.state, 'ready')

    def test_shared_send_vectors(self):
        vectors = json.loads((ROOT / 'docs/protocol-vectors.json').read_text())
        for case in vectors['serial_cases']:
            if case.get('expected') != 'accepted':
                continue
            self.adapter.state = 'ready'
            _, session, seq, payload = case['line'].strip().split('\t')
            self.adapter.session, self.adapter.seq = session, int(seq, 16)
            self.adapter.send(bytes.fromhex(payload).decode(), 1)
            self.assertEqual(self.writes[-1], case['line'].encode())

    def test_pacing_and_accurate_local_result(self):
        self.ready()
        result = self.adapter.send(' Hi\n spirit ', 1)
        self.assertEqual(result.text, 'Hi spirit')
        for name in ('accepting', 'sending', 'guard'):
            self.assertEqual(self.adapter.state, name)
            with self.assertRaises(RuntimeError):
                self.adapter.send('Other', 1.1)
            if name == 'accepting':
                self.accepted(1.1)
            elif name == 'sending':
                self.event('sent', 2, session='12345678', seq=0)
        self.assertTrue(result.local_sent)
        self.assertEqual(result.status, 'local_sent_waiting_ready')
        self.event('ready', 2.6)
        self.assertEqual(result.status, 'local_sent')
        self.adapter.send('Other', 3)
        self.assertEqual(self.adapter.result.seq, 1)

    def test_all_timeout_boundaries_no_auto_retry(self):
        for stage in ('accepting', 'sending', 'guard'):
            with self.subTest(stage=stage):
                self.setUp()
                self.ready()
                result = self.adapter.send('Hi', 1)
                if stage != 'accepting':
                    self.accepted(1.1)
                if stage == 'guard':
                    self.event('sent', 2, session='12345678', seq=0)
                boundary = 3 if stage == 'accepting' else 13
                self.adapter.tick(boundary - 0.001)
                self.assertEqual(self.adapter.state, stage)
                self.adapter.tick(boundary)
                self.assertEqual(result.status, 'uncertain')
                self.assertEqual(result.local_sent, stage == 'guard')
                self.assertEqual(len(self.writes), 2)
                with self.assertRaises(RuntimeError):
                    self.adapter.send('Hi', boundary)

    def test_event_at_accept_deadline_is_too_late(self):
        self.ready()
        self.adapter.send('Hi', 1)
        self.accepted(3)
        self.assertEqual(self.adapter.state, 'reconnect_required')

    def test_split_crlf_blank_multiple_and_overflow_recovery(self):
        data = b'\n' + line('hello', role='tx', max_text_bytes=48).replace(b'\n', b'\r\n') + line('ready')
        for byte in data:
            self.adapter.feed(bytes([byte]), 0.1)
        self.assertEqual(self.adapter.state, 'ready')
        self.adapter.feed(b'x' * 50000, 0.2)
        self.assertEqual(len(self.adapter.buffer), 0)
        self.adapter.feed(b'{"v":1,"event":"ready"}\n' + line('ready'), 0.3)
        self.assertEqual(self.adapter.state, 'ready')
        self.assertEqual(len(self.adapter.diagnostics), 1)

    def test_line_bound_excludes_optional_cr(self):
        self.adapter.feed(b' ' * (C['MAX_EVENT_LINE_BYTES'] - len(line('ready')) + 1) + line('ready')[:-1] + b'\r\n', 0.1)
        self.assertFalse(self.adapter.diagnostics)
        self.adapter.feed(b' ' * 257 + line('ready'), 0.1)
        self.assertIn('overflow', self.adapter.diagnostics[-1])

    def test_malformed_events_cannot_change_readiness(self):
        for data in (b'not json\n', b'\xff\n', b'[]\n', b'{"v":1,"event":"ready","extra":1}\n'):
            self.adapter.feed(data, 0.1)
        self.assertEqual(self.adapter.state, 'handshake')
        self.assertEqual(len(self.adapter.diagnostics), 4)

    def test_identity_mismatch_out_of_order_and_board_reset(self):
        for data in (line('sent', session='12345678', seq=0), line('accepted', session='12345678', seq=1), line('ready'), line('hello', role='tx', max_text_bytes=48)):
            self.setUp()
            self.ready()
            self.adapter.send('Hi', 1)
            self.adapter.feed(data, 1.1)
            self.assertEqual(self.adapter.state, 'reconnect_required')
            self.assertEqual(self.adapter.result.status, 'uncertain')

    def test_local_rejection_and_tx_failure_wait_for_ready(self):
        for code in CONTRACT_ERROR_CODES:
            self.setUp()
            self.ready()
            result = self.adapter.send('Hi', 1)
            self.event('error', 1.1, code=code)
            self.assertEqual(self.adapter.state, 'guard')
            self.assertEqual(result.status, 'failed')
            self.assertFalse(result.local_sent)
            self.event('ready', 2)
            self.assertEqual(self.adapter.state, 'ready')
            self.assertEqual(result.status, 'failed')

    def test_partial_write_and_disconnect_are_uncertain(self):
        self.ready()
        self.adapter.write = lambda data: 2
        with self.assertRaises(OSError):
            self.adapter.send('Hi', 1)
        self.assertEqual(self.adapter.result.status, 'uncertain')
        self.assertEqual(self.adapter.seq, 1)
        self.setUp()
        self.ready()
        self.adapter.send('Hi', 1)
        class Unplugged:
            def read(self, size):
                raise OSError('unplugged')
        poll_once(self.adapter, Unplugged(), lambda: 1.1)
        self.assertEqual(self.adapter.result.status, 'uncertain')
        self.assertEqual(self.adapter.state, 'reconnect_required')

    def test_reconnect_preserves_uncertainty_and_increments_identity(self):
        self.ready()
        prior = self.adapter.send('Hi', 1)
        self.adapter.start(2)
        self.adapter.feed(line('ready'), 2.1)
        self.assertEqual(prior.status, 'uncertain')
        self.adapter.feed(line('hello', role='tx', max_text_bytes=48) + line('ready'), 2.2)
        result = self.adapter.send('Hi', 2.3)
        self.assertEqual(result.seq, 1)

    def test_sequence_wrap_uses_new_session(self):
        self.ready()
        self.adapter.seq = 65536
        with self.assertRaises(ValueError):
            self.adapter.send('Hi', 1)
        self.adapter.session_factory = lambda: '87654321'
        result = self.adapter.send('Hi', 1)
        self.assertEqual((result.session, result.seq), ('87654321', 0))

    def test_invalid_input_does_not_consume_ready_or_identity(self):
        self.ready()
        with self.assertRaises(ValueError):
            self.adapter.send('x' * 49, 1)
        self.assertEqual((self.adapter.state, self.adapter.seq, len(self.writes)), ('ready', 0, 1))

    def test_simulated_cli_success_and_failures(self):
        for scenario in ('success', 'accept-timeout', 'send-timeout', 'ready-timeout', 'tx-failed', 'disconnect'):
            with self.subTest(scenario=scenario), contextlib.redirect_stdout(io.StringIO()) as output:
                code = serial_cli.main(['--simulate', '--text', 'Hi', '--text', 'Spirit', '--scenario', scenario])
            self.assertEqual(code, 0 if scenario == 'success' else 2)
            self.assertIn('SIMULATION ONLY', output.getvalue())
            self.assertIn('Remote delivery unknown', output.getvalue())

    def test_local_port_configuration_without_opening_hardware(self):
        factory = Mock()
        self.assertIs(open_local_port('COM3', factory), factory.return_value)
        factory.assert_called_once_with(port='COM3', baudrate=C['SERIAL_BAUD'], bytesize=8,
                                       parity='N', stopbits=1, timeout=0.05, write_timeout=0.5,
                                       xonxoff=False, rtscts=False, dsrdtr=False)
        for port in ('socket://localhost:1234', 'loop://', '', 'COM0', None):
            with self.assertRaises(ValueError):
                open_local_port(port, factory)
        factory.assert_called_once()

    def test_poll_during_silence_honors_timeout(self):
        self.ready()
        self.adapter.send('Hi', 1)
        transport = Mock()
        transport.read.return_value = b''
        poll_once(self.adapter, transport, lambda: 3)
        transport.read.assert_not_called()
        self.assertEqual(self.adapter.result.status, 'uncertain')


from shared.generated.protocol import CONTRACT
CONTRACT_ERROR_CODES = CONTRACT['error_codes']

if __name__ == '__main__':
    unittest.main()
