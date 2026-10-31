"""One explicit local serial connection, continuously polled until completion."""
import time

from serial_adapter import C, SerialAdapter, clean_text, open_local_port, poll_once


class SenderConnection:
    def __init__(self, port, opener=open_local_port, clock=time.monotonic, pause=time.sleep, report=print):
        self.port_name = port
        self.opener, self.clock, self.pause, self.report = opener, clock, pause, report
        self.transport = None
        self.adapter = None

    def _poll(self):
        poll_once(self.adapter, self.transport, self.clock)
        while self.adapter.diagnostics:
            self.report('Local serial diagnostic: ' + self.adapter.diagnostics.popleft())
        # Avoid spinning if an injected/nonblocking transport has no data.
        self.pause(0.005)

    def _wait(self):
        previous = None
        while self.adapter.state not in ('ready', 'reconnect_required'):
            self._poll()
            if self.adapter.state != previous:
                self.report('Local serial state: ' + self.adapter.state)
                previous = self.adapter.state

    def connect(self):
        if self.transport is not None:
            raise RuntimeError('Connection already open; close it explicitly first.')
        self.report(f'Connecting to {self.port_name}; waiting for compatible Tx hello/ready...')
        self.transport = self.opener(self.port_name)
        self.adapter = SerialAdapter(self.transport.write)
        try:
            started = self.clock()
            self.adapter.start(started, request_hello=False)
            # Opening an Uno can reset it. Read its boot events before sending
            # a single fallback HELLO, so queued HELLO cannot duplicate boot hello.
            while self.adapter.state == 'handshake':
                self._poll()
                if (self.adapter.state == 'handshake' and not self.adapter.hello
                        and not self.adapter.hello_requested and self.clock() - started >= 2):
                    self.adapter.request_identity()
            if self.adapter.state != 'ready':
                raise RuntimeError('No compatible Tx hello/ready within the boot timeout. Check port and CE Tx firmware; no text was sent.')
            self.report('Local Tx ready. Remote delivery cannot be acknowledged.')
        except BaseException:
            self.close()
            raise
        return self

    def send(self, text):
        text = clean_text(text)
        if self.transport is None or self.adapter is None or self.adapter.state != 'ready':
            raise RuntimeError('No ready connection. Reconnect explicitly; nothing was resent.')
        self.report(f'Outgoing ({len(text.encode("ascii"))} bytes): {text}')
        prior = self.adapter.result
        try:
            self.adapter.send(text, self.clock())
            self._wait()
        except BaseException:
            self.adapter.disconnect('Serial operation interrupted/failed; remote delivery unknown. Reconnect explicitly.')
            raise
        finally:
            result = self.adapter.result
            if result is not None and result is not prior:
                self.report(f'Local result: {result.status}; local_sent={result.local_sent}; connection={self.adapter.state}')
                self.report('Remote delivery unknown. ' + result.detail)
        if result.status != 'local_sent':
            raise RuntimeError('Local send did not complete successfully. Reconnect explicitly; no automatic resend.')
        return result

    def close(self):
        if self.adapter:
            self.adapter.disconnect('Local serial connection closed.')
        if self.transport is not None:
            transport, self.transport = self.transport, None
            try:
                transport.close()
            except OSError as error:
                self.report('Local serial close error: ' + str(error))

    def __enter__(self):
        return self.connect()

    def __exit__(self, kind, error, traceback):
        self.close()


def send_once(port, text):
    text = clean_text(text)  # Reject before touching a real port.
    with SenderConnection(port) as connection:
        return connection.send(text)


def list_ports():
    from serial.tools.list_ports import comports
    return sorted((item.device, item.description) for item in comports())
