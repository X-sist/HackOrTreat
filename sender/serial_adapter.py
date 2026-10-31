"""Bounded Tx serial state machine. No microphone, model, or hardware imports."""
import json
import secrets
import re
from collections import deque
from dataclasses import dataclass

from shared.generated.protocol import CONTRACT
from shared.python.contract import build_send, validate_event

C = CONTRACT['constants']


def open_local_port(port, serial_factory=None):
    """Explicit hardware seam, not used by the simulator. Never accepts URL ports."""
    if not isinstance(port, str) or re.fullmatch(r'COM[1-9][0-9]*', port, re.IGNORECASE) is None:
        raise ValueError('Choose an explicit local Windows COM port, such as COM3.')
    if serial_factory is None:
        from serial import Serial
        serial_factory = Serial
    return serial_factory(port=port, baudrate=C['SERIAL_BAUD'], bytesize=8,
                          parity='N', stopbits=1, timeout=0.05, write_timeout=0.5,
                          xonxoff=False, rtscts=False, dsrdtr=False)


def clean_text(text):
    """Normalize ASCII whitespace only; never strip Unicode or truncate."""
    if not isinstance(text, str):
        raise ValueError('Text must be a string.')
    if len(text) > 4096:
        raise ValueError('Input exceeds 4096 characters; edit it explicitly.')
    if not text.isascii():
        raise ValueError('ASCII required; edit non-ASCII characters explicitly.')
    text = re.sub(r'[ \t\r\n\v\f]+', ' ', text).strip(' ')
    # Shared builder enforces printable, nonblank, and byte bounds.
    build_send('00000000', 0, text)
    return text


@dataclass
class Result:
    session: str
    seq: int
    text: str
    status: str = 'awaiting_acceptance'
    local_sent: bool = False
    detail: str = ''


class SerialAdapter:
    """Single-threaded adapter; caller supplies monotonic seconds and a write(bytes).

    start() is an explicit reconnect on a fresh transport. feed() consumes arbitrary
    byte chunks; tick() must also run during silence. No queue and no auto retry.
    """
    def __init__(self, write, session_factory=lambda: secrets.token_hex(4).upper()):
        self.write = write
        self.session_factory = session_factory
        self.session = session_factory()
        build_send(self.session, 0, 'x')
        self.seq = 0
        self.state = 'disconnected'
        self.result = None
        self.diagnostics = deque(maxlen=32)
        self.buffer = bytearray()
        self.discard = False
        self.hello = False

    def _fail(self, detail):
        if self.state in ('accepting', 'sending', 'guard') and self.result:
            self.result.status = 'uncertain'
            self.result.detail = detail
        self.state = 'reconnect_required'
        self.hello = False
        self.buffer.clear()
        self.discard = False
        self.diagnostics.append(detail)

    def disconnect(self, detail='Serial disconnected; reconnect explicitly.'):
        self._fail(detail)

    def _write(self, data):
        try:
            if self.write(data) != len(data):
                raise OSError('Incomplete serial write')
        except OSError as error:
            self._fail(str(error))
            raise OSError('Serial write failed; reconnect, do not automatically resend.') from error

    def start(self, now):
        if self.state != 'disconnected':
            self._fail('Connection replaced; prior operation may have transmitted.')
        self.buffer.clear()
        self.discard = False
        self.hello = False
        self.state = 'handshake'
        self.deadline = now + C['HOST_BOOT_TIMEOUT_MS'] / 1000
        self._write(b'HELLO\n')

    def tick(self, now):
        if self.state in ('handshake', 'accepting', 'sending', 'guard') and now >= self.deadline:
            self._fail('Local serial timeout; reconnect explicitly. Remote delivery unknown.')

    def send(self, text, now):
        self.tick(now)
        if self.state != 'ready':
            raise RuntimeError('BUSY or disconnected: wait for local ready or reconnect.')
        text = clean_text(text)
        if self.seq > 65535:
            previous = self.session
            self.session = self.session_factory()
            if self.session == previous:
                raise ValueError('Session factory reused session at sequence wrap.')
            self.seq = 0
        command = build_send(self.session, self.seq, text).encode('ascii')
        if len(command) - 1 > C['MAX_HOST_LINE_BYTES']:
            raise ValueError('Host command exceeds shared line bound.')
        self.result = Result(self.session, self.seq, text)
        self.seq += 1  # Even a failed/partial write consumes the identity.
        self.state = 'accepting'
        self.deadline = now + C['HOST_ACCEPT_TIMEOUT_MS'] / 1000
        self.send_deadline = now + C['HOST_SEND_TIMEOUT_MS'] / 1000
        self._write(command)
        return self.result

    def feed(self, data, now):
        self.tick(now)  # Deadlines take precedence over events at the boundary.
        if self.state in ('disconnected', 'reconnect_required'):
            return
        for byte in data:
            if byte == 10:
                if not self.discard:
                    line = bytes(self.buffer)
                    if line.endswith(b'\r'):
                        line = line[:-1]
                    if line:
                        self._line(line)
                self.buffer.clear()
                self.discard = False
                if self.state == 'reconnect_required':
                    break
            elif not self.discard:
                self.buffer.append(byte)
                # One extra byte is allowed only for optional CR before LF.
                limit = C['MAX_EVENT_LINE_BYTES']
                if len(self.buffer) > limit and not (len(self.buffer) == limit + 1 and byte == 13):
                    self.buffer.clear()
                    self.discard = True
                    self.diagnostics.append('Local event line overflow; discarded through LF.')

    def _line(self, line):
        try:
            event = json.loads(line.decode('ascii'))
            validate_event(event, 'tx')
        except (UnicodeError, ValueError, TypeError, KeyError, RecursionError):
            self.diagnostics.append('Invalid/unknown local serial event ignored.')
            return
        name = event['event']
        if name == 'hello':
            if self.state == 'handshake':
                self.hello = True
            else:
                self._fail('Board hello/reset invalidated local state; reconnect explicitly.')
        elif self.state == 'handshake':
            if name == 'ready' and self.hello:
                self.state = 'ready'
        elif name == 'error':
            if self.state in ('accepting', 'sending'):
                self.result.status = 'failed'
                self.result.detail = 'Local board error: ' + event['code']
                self.state = 'guard'
                self.deadline = self.send_deadline
            else:
                self._fail('Unexpected local board error: ' + event['code'])
        elif name in ('accepted', 'sent'):
            if not self.result or (event['session'], event['seq']) != (self.result.session, self.result.seq):
                self._fail('Unexpected message identity; reconnect explicitly.')
            elif name == 'accepted' and self.state == 'accepting':
                self.result.status = 'accepted'
                self.state = 'sending'
                self.deadline = self.send_deadline
            elif name == 'sent' and self.state == 'sending':
                self.result.local_sent = True
                self.result.status = 'local_sent_waiting_ready'
                self.state = 'guard'
            else:
                self._fail('Out-of-order local send event; reconnect explicitly.')
        elif name == 'ready':
            if self.state == 'guard':
                if self.result.local_sent:
                    self.result.status = 'local_sent'
                self.state = 'ready'
            elif self.state != 'ready':
                self._fail('Ready arrived before local send outcome; reconnect explicitly.')


def poll_once(adapter, transport, clock):
    """transport.read(256) must be bounded/nonblocking; b'' means no data.

    EOF/unplug must raise OSError (or be reported via disconnect), not b''.
    The transport owner closes/reopens it explicitly after reconnect_required.
    """
    adapter.tick(clock())
    if adapter.state in ('disconnected', 'reconnect_required'):
        return
    try:
        data = transport.read(C['MAX_EVENT_LINE_BYTES'])
    except OSError as error:
        adapter.disconnect(str(error))
        return
    adapter.feed(data, clock())
