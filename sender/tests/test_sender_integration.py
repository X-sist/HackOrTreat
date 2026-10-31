import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cli
import serial_connection
from serial_adapter import C


def event(name, **fields):
    return json.dumps({'v': C['PROTOCOL_VERSION'], 'event': name, **fields}).encode() + b'\n'


class FakePort:
    def __init__(self, scenario='success', boot=True):
        self.scenario, self.now = scenario, 0.0
        self.writes, self.responses = [], []
        self.closed = False
        if boot:
            self.identity()

    def identity(self):
        self.responses.extend([event('hello', role='tx', max_text_bytes=C['MAX_TEXT_BYTES']), event('ready')])

    def write(self, data):
        self.writes.append(data)
        if data == b'HELLO\n':
            if self.scenario != 'no-firmware':
                self.identity()
        else:
            if self.scenario == 'partial-write':
                return 3
            if self.scenario == 'cancel':
                raise KeyboardInterrupt
            _, session, seq, _ = data.decode().strip().split('\t')
            fields = {'session': session, 'seq': int(seq, 16)}
            if self.scenario == 'wrong-id':
                fields['seq'] += 1
            if self.scenario != 'accept-timeout':
                self.responses.append(event('accepted', **fields))
            if self.scenario == 'tx-failed':
                self.responses.extend([event('error', code='TX_FAILED'), event('ready')])
            elif self.scenario not in ('send-timeout', 'accept-timeout', 'disconnect', 'wrong-id'):
                self.responses.append(event('sent', **fields))
                if self.scenario != 'ready-timeout':
                    self.responses.append(event('ready'))
        return len(data)

    def read(self, size):
        self.now += 0.01
        if self.scenario == 'disconnect' and any(x.startswith(b'SEND') for x in self.writes):
            raise OSError('USB unplugged')
        if self.responses:
            # Exercise the actual incremental adapter, including boot split reads.
            chunk = self.responses[0][:7]
            self.responses[0] = self.responses[0][7:]
            if not self.responses[0]:
                self.responses.pop(0)
            return chunk
        return b''

    def close(self):
        self.closed = True


class SenderIntegrationChecks(unittest.TestCase):
    def connection(self, port):
        return serial_connection.SenderConnection('COM8', opener=lambda name: port,
            clock=lambda: port.now, pause=lambda seconds: None, report=lambda message: None)

    def test_boot_handshake_sends_no_redundant_hello_and_paces_messages(self):
        port = FakePort()
        with self.connection(port) as connection:
            first = connection.send('Hi')
            second = connection.send(' Spirit ')
            self.assertEqual(first.status, 'local_sent')
            self.assertEqual(second.seq, 1)
            self.assertEqual(first.session, second.session)
        self.assertEqual(len(port.writes), 2)
        self.assertTrue(all(x.startswith(b'SEND') for x in port.writes))
        self.assertTrue(port.closed)

    def test_missed_boot_requests_identity_once(self):
        port = FakePort(boot=False)
        with self.connection(port) as connection:
            self.assertEqual(connection.adapter.state, 'ready')
        self.assertEqual(port.writes, [b'HELLO\n'])

    def test_no_firmware_never_sends_payload_and_closes(self):
        port = FakePort('no-firmware', boot=False)
        with self.assertRaisesRegex(RuntimeError, 'CE Tx firmware'):
            self.connection(port).connect()
        self.assertEqual(port.writes, [b'HELLO\n'])
        self.assertTrue(port.closed)

    def test_connection_faults_never_reconnect_or_retry(self):
        for scenario in ('accept-timeout', 'send-timeout', 'ready-timeout', 'tx-failed', 'disconnect', 'wrong-id', 'partial-write'):
            with self.subTest(scenario=scenario):
                port = FakePort(scenario)
                with self.connection(port) as connection:
                    with self.assertRaises((RuntimeError, OSError)):
                        connection.send('Hi')
                    result = connection.adapter.result
                    self.assertEqual(result.local_sent, scenario == 'ready-timeout')
                    self.assertEqual(result.status, 'failed' if scenario == 'tx-failed' else 'uncertain')
                self.assertEqual(len(port.writes), 1)
                self.assertTrue(port.closed)

    def test_cancel_during_send_preserves_uncertainty_and_closes(self):
        port = FakePort('cancel')
        connection = self.connection(port)
        with self.assertRaises(KeyboardInterrupt):
            with connection:
                connection.send('Hi')
        self.assertEqual(connection.adapter.result.status, 'uncertain')
        self.assertTrue(port.closed)

    def test_invalid_payload_rejected_before_port_open(self):
        with patch.object(serial_connection, 'SenderConnection') as constructor:
            for text in ('', 'x' * 49, 'é'):
                with self.assertRaises(ValueError):
                    serial_connection.send_once('COM8', text)
            constructor.assert_not_called()

    def test_cli_manual_sends_normalized_text_without_mic_or_model(self):
        with patch.object(cli, 'send_once') as send, patch.object(cli, 'record', side_effect=AssertionError), patch.object(cli.Transcriber, 'transcribe', side_effect=AssertionError), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['--send', '--port', 'COM8', '--text', ' Hi\n Spirit ']), 0)
            send.assert_called_once_with('COM8', 'Hi Spirit')

    def test_cli_record_passes_transcription_to_sender(self):
        with patch.object(cli, 'record', return_value=('samples', 48000)), patch.object(cli, 'pcm_wave', return_value='pcm'), patch.object(cli.Transcriber, 'transcribe', return_value='Spirit, what is your name?') as transcribe, patch.object(cli, 'send_once') as send, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['--send', '--port', 'COM8', '--record', '--seconds', '3']), 0)
            transcribe.assert_called_once_with('pcm')
            send.assert_called_once_with('COM8', 'Spirit, what is your name?')

    def test_cli_cancel_blank_and_oversize_never_open_serial(self):
        with patch.object(cli, 'send_once') as send, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with patch.object(cli, 'record', side_effect=cli.CaptureCancelled('cancelled')):
                self.assertEqual(cli.main(['--send', '--port', 'COM8', '--record']), 2)
            self.assertEqual(cli.main(['--send', '--port', 'COM8', '--text', ' ']), 2)
            self.assertEqual(cli.main(['--send', '--port', 'COM8', '--text', 'x' * 49]), 2)
            send.assert_not_called()

    def test_cli_requires_explicit_send_and_port(self):
        with patch.object(cli, 'send_once') as send, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(['--text', 'Hi']), 0)
            send.assert_not_called()
            for args in (['--send', '--text', 'Hi'], ['--send', '--port', 'COM8'], ['--check-serial'], ['--port', 'COM8', '--text', 'Hi'], ['--send', '--port', 'socket://localhost:1234', '--record']):
                with self.assertRaises(SystemExit) as error:
                    cli.main(args)
                self.assertEqual(error.exception.code, 2)

    def test_connection_check_never_sends_payload_or_loads_speech(self):
        port = FakePort()
        with patch.object(cli, 'SenderConnection', return_value=self.connection(port)), patch.object(cli, 'record', side_effect=AssertionError), patch.object(cli.Transcriber, 'transcribe', side_effect=AssertionError), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['--check-serial', '--port', 'COM8']), 0)
        self.assertEqual(port.writes, [])
        self.assertTrue(port.closed)

    def test_port_open_failure_is_actionable(self):
        with patch.object(serial_connection, 'open_local_port'):
            connection = serial_connection.SenderConnection('COM8', opener=Mock(side_effect=OSError('Access denied')))
            with self.assertRaisesRegex(OSError, 'Access denied'):
                connection.connect()


if __name__ == '__main__':
    unittest.main()
