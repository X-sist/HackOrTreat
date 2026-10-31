"""Manual-text C1-03 simulator. Never opens a serial port or microphone."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sender.serial_adapter import C, SerialAdapter, clean_text, poll_once


class SimulatedArduino:
    """Virtual clock/byte transport, explicitly not firmware or physical evidence."""
    def __init__(self, scenario='success'):
        self.scenario = scenario
        self.now = 0.0
        self.events = []
        self.writes = []
        fixtures = json.loads((Path(__file__).resolve().parents[1] / 'shared/fixtures/events.json').read_text())
        self.fixtures = {f['id']: f['value'] for f in fixtures}

    def schedule(self, delay, event):
        self.events.append((self.now + delay, json.dumps(event, separators=(',', ':')).encode('ascii') + b'\r\n'))

    def write(self, data):
        self.writes.append(data)
        if data == b'HELLO\n':
            self.schedule(0.01, self.fixtures['hello-tx'])
            self.schedule(0.02, self.fixtures['valid-ready'])
        else:
            _, session, seq, payload = data.decode('ascii').strip().split('\t')
            identity = {'v': C['PROTOCOL_VERSION'], 'session': session, 'seq': int(seq, 16)}
            if self.scenario == 'accept-timeout':
                return len(data)
            self.schedule(0.01, {**identity, 'event': 'accepted'})
            duration = (C['PACKET_OVERHEAD_BYTES'] + len(bytes.fromhex(payload)) - 1) * C['SYMBOL_PERIOD_MS'] / 1000
            if self.scenario == 'tx-failed':
                self.schedule(0.1, {'v': C['PROTOCOL_VERSION'], 'event': 'error', 'code': 'TX_FAILED'})
                self.schedule(0.1 + C['PACKET_GUARD_MS'] / 1000, self.fixtures['valid-ready'])
            elif self.scenario not in ('send-timeout', 'disconnect'):
                self.schedule(duration, {**identity, 'event': 'sent'})
                if self.scenario != 'ready-timeout':
                    self.schedule(duration + C['PACKET_GUARD_MS'] / 1000, self.fixtures['valid-ready'])
        return len(data)

    def read(self, size):
        self.now += 0.01
        if self.scenario == 'disconnect' and len(self.writes) > 1:
            raise OSError('Simulated USB disconnect')
        if self.events and self.events[0][0] <= self.now:
            when, data = self.events[0]
            chunk = data[:min(size, 7)]  # Deliberately split JSON records.
            if len(chunk) == len(data):
                self.events.pop(0)
            else:
                self.events[0] = (when, data[len(chunk):])
            return chunk
        return b''


def wait(adapter, board):
    while adapter.state not in ('ready', 'reconnect_required'):
        poll_once(adapter, board, lambda: board.now)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--simulate', required=True, action='store_true', help='Required: no physical port is opened')
    parser.add_argument('--text', action='append', required=True, help='Repeat for paced manual messages')
    parser.add_argument('--scenario', choices=['success', 'accept-timeout', 'send-timeout', 'ready-timeout', 'tx-failed', 'disconnect'], default='success')
    args = parser.parse_args(argv)
    try:
        texts = [clean_text(text) for text in args.text]
        print('SIMULATION ONLY: no Arduino, IR, microphone, or model is used.')
        board = SimulatedArduino(args.scenario)
        adapter = SerialAdapter(board.write)
        adapter.start(board.now)
        wait(adapter, board)
        for text in texts:
            print(f'Outgoing ({len(text.encode("ascii"))} bytes): {text}')
            result = adapter.send(text, board.now)
            wait(adapter, board)
            print(f'Local result: {result.status}; local_sent={result.local_sent}; connection={adapter.state}')
            print('Remote delivery unknown. ' + result.detail)
            if result.status != 'local_sent':
                return 2
    except (ValueError, RuntimeError, OSError) as error:
        print(f'Local serial/input error: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
