"""Bounded, memory-only mono capture. Importing this module does not open a mic."""
import time
import threading

class CaptureCancelled(Exception):
    pass

class CaptureBuffer:
    def __init__(self, sample_rate, seconds):
        import numpy as np
        if not 0.25 <= seconds <= 30 or not 8000 <= sample_rate <= 192000:
            raise ValueError('Recording must be 0.25–30 seconds at a supported input rate.')
        self.sample_rate = sample_rate
        self.capacity = int(sample_rate * seconds)
        self.data = np.empty(self.capacity, dtype=np.float32)
        self.used = 0
        self.full = threading.Event()
        self.error = None

    def append(self, audio, overflow=False):
        if overflow:
            self.error = 'Microphone input overflowed. Close other audio apps or choose another input.'
            self.full.set()
            return
        count = min(len(audio), self.capacity - self.used)
        if count:
            self.data[self.used:self.used + count] = audio[:count, 0]
            self.used += count
        if self.used >= self.capacity:
            self.full.set()

    def finish(self):
        if self.error:
            raise ValueError(self.error)
        if self.used < int(0.25 * self.sample_rate):
            raise ValueError('Recording too short. Speak for at least a quarter second.')
        return self.data[:self.used].copy(), self.sample_rate

def input_devices():
    import sounddevice as sd
    return [(index, item['name'], int(item['max_input_channels'])) for index, item in enumerate(sd.query_devices()) if item['max_input_channels'] > 0]

def enter_pressed():
    import msvcrt
    while msvcrt.kbhit():
        key = msvcrt.getwch()
        if key == '\x03':
            raise KeyboardInterrupt
        if key in ('\r', '\n'):
            return True
    return False

def record(device=None, seconds=10, stop_requested=None):
    import sounddevice as sd
    try:
        info = sd.query_devices(device, kind='input')
        rate = int(info['default_samplerate'])
        # Native device rate avoids assuming every Windows mic supports 16 kHz.
        sd.check_input_settings(device=device, channels=1, dtype='float32', samplerate=rate)
        buffer = CaptureBuffer(rate, seconds)
        def callback(audio, frames, timing, status):
            buffer.append(audio, overflow=bool(status))
            if buffer.full.is_set():
                raise sd.CallbackStop
        with sd.InputStream(device=device, channels=1, samplerate=rate, dtype='float32', blocksize=1024, callback=callback) as stream:
            deadline = time.monotonic() + seconds + 2
            while stream.active and not buffer.full.is_set():
                if stop_requested is not None and stop_requested():
                    break
                if time.monotonic() >= deadline:
                    raise ValueError('Microphone stalled. Check input permissions and device selection.')
                time.sleep(0.03)
        return buffer.finish()
    except KeyboardInterrupt as error:
        raise CaptureCancelled('Recording cancelled; nothing transcribed or saved.') from error
    except sd.PortAudioError as error:
        raise ValueError('Cannot open the microphone. Check Windows microphone privacy settings, device ID, and other apps. Details: ' + str(error)) from error
