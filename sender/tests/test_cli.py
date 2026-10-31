import contextlib
import io
import os
import socket
import sys
import types
import unittest
import wave
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cli
import microphone
import speech
import numpy as np

class CliChecks(unittest.TestCase):
    def test_manual_mode_never_opens_mic_or_model(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), patch.object(cli, 'record', side_effect=AssertionError('mic opened')), patch.object(cli.Transcriber, 'transcribe', side_effect=AssertionError('model loaded')):
            self.assertEqual(cli.main(['--text', 'Hello spirit']), 0)
        self.assertIn('Manual text: Hello spirit', output.getvalue())

    def test_missing_local_audio_is_actionable(self):
        with contextlib.redirect_stderr(io.StringIO()) as error, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['--audio', 'https://example.invalid/audio.wav']), 2)
        self.assertIn('existing local file', error.getvalue())

    def test_capture_limit_rejects_unbounded_input(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            cli.main(['--record', '--seconds', '31'])
        self.assertEqual(error.exception.code, 2)

    def test_blank_transcript_is_not_displayed_as_speech(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertFalse(cli.show_text('  '))
        self.assertNotIn('Recognized:', output.getvalue())

    def test_native_rate_pcm_is_wav_and_clips_safely(self):
        stream = speech.pcm_wave(np.array([-2, -0.5, 0.5, 2]), 48000)
        with wave.open(stream, 'rb') as audio:
            self.assertEqual((audio.getframerate(), audio.getnchannels(), audio.getsampwidth()), (48000, 1, 2))
            values = np.frombuffer(audio.readframes(4), dtype='<i2')
        self.assertEqual(values.tolist(), [-32767, -16383, 16383, 32767])

    def test_invalid_pcm_rejected_before_model(self):
        for data in ([], [float('nan')], [float('inf')]):
            with self.subTest(data=data), self.assertRaises(ValueError):
                speech.pcm_wave(data, 16000)

    def test_memory_wav_decodes_at_whisper_sample_rate(self):
        from faster_whisper.audio import decode_audio
        signal = (0.2 * np.sin(2 * np.pi * 100 * np.arange(48000) / 48000)).astype(np.float32)
        decoded = decode_audio(speech.pcm_wave(signal, 48000), sampling_rate=16000)
        self.assertEqual(decoded.shape, (16000,))
        self.assertGreater(float(np.max(np.abs(decoded))), 0.1)

    def test_capture_stays_bounded(self):
        buffer = microphone.CaptureBuffer(16000, 0.25)
        buffer.append(np.ones((5000, 1), dtype=np.float32))
        samples, rate = buffer.finish()
        self.assertEqual((len(samples), rate), (4000, 16000))
        self.assertTrue(buffer.full.is_set())

    def test_overflow_is_rejected_not_silently_transcribed(self):
        buffer = microphone.CaptureBuffer(16000, 1)
        buffer.append(np.ones((1000, 1), dtype=np.float32), overflow=True)
        with self.assertRaisesRegex(ValueError, 'overflowed'):
            buffer.finish()

    def test_short_capture_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'too short'):
            microphone.CaptureBuffer(16000, 1).finish()

    def test_capture_uses_device_native_rate_without_opening_hardware(self):
        class Stop(Exception):
            pass
        class Stream:
            active = False
            def __init__(self, **kwargs):
                self.callback = kwargs['callback']
                self.rate = kwargs['samplerate']
            def __enter__(self):
                try:
                    self.callback(np.ones((13000, 1), dtype=np.float32), 13000, None, False)
                except Stop:
                    pass
                return self
            def __exit__(self, *args):
                pass
        fake = types.SimpleNamespace(query_devices=Mock(return_value={'default_samplerate': 48000}), check_input_settings=Mock(), InputStream=Stream, CallbackStop=Stop, PortAudioError=type('PortAudioError', (Exception,), {}))
        with patch.dict(sys.modules, {'sounddevice': fake}):
            samples, rate = microphone.record(device=3, seconds=0.25)
        self.assertEqual((len(samples), rate), (12000, 48000))
        fake.check_input_settings.assert_called_once_with(device=3, channels=1, dtype='float32', samplerate=48000)

    def test_model_is_reused_and_network_is_denied_during_lazy_iteration(self):
        original_connect = socket.create_connection
        original_env = os.environ.get('HF_HUB_OFFLINE')
        constructed = []
        class Model:
            def __init__(self, path, **kwargs):
                constructed.append(kwargs)
            def transcribe(self, source, **kwargs):
                def segments():
                    with self_case.assertRaisesRegex(OSError, 'disabled for offline'):
                        socket.create_connection(('example.invalid', 443))
                    yield types.SimpleNamespace(text=' Hello ')
                return segments(), None
        self_case = self
        with patch.object(speech, 'verify_model_files', return_value=Path('fixture-model')), patch.dict(sys.modules, {'faster_whisper': types.SimpleNamespace(WhisperModel=Model)}):
            transcriber = speech.Transcriber()
            self.assertEqual(transcriber.transcribe(io.BytesIO()), 'Hello')
            self.assertEqual(transcriber.transcribe(io.BytesIO()), 'Hello')
        self.assertEqual(len(constructed), 1)
        self.assertTrue(constructed[0]['local_files_only'])
        self.assertIs(socket.create_connection, original_connect)
        self.assertEqual(os.environ.get('HF_HUB_OFFLINE'), original_env)

    def test_manual_stop_closes_stream_and_keeps_only_captured_frames(self):
        closed = []
        class Stream:
            active = True
            def __init__(self, **kwargs):
                self.callback = kwargs['callback']
            def __enter__(self):
                self.callback(np.ones((13000, 1), dtype=np.float32), 13000, None, False)
                return self
            def __exit__(self, *args):
                closed.append(True)
        fake = types.SimpleNamespace(query_devices=Mock(return_value={'default_samplerate': 48000}), check_input_settings=Mock(), InputStream=Stream, CallbackStop=type('Stop', (Exception,), {}), PortAudioError=type('AudioError', (Exception,), {}))
        with patch.dict(sys.modules, {'sounddevice': fake}):
            samples, rate = microphone.record(seconds=1, stop_requested=lambda: True)
        self.assertEqual((len(samples), rate), (13000, 48000))
        self.assertEqual(closed, [True])

    def test_cancel_closes_stream_and_discards_recording(self):
        closed = []
        class Stream:
            active = True
            def __init__(self, **kwargs):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                closed.append(True)
        def cancelled():
            raise KeyboardInterrupt
        fake = types.SimpleNamespace(query_devices=Mock(return_value={'default_samplerate': 48000}), check_input_settings=Mock(), InputStream=Stream, CallbackStop=type('Stop', (Exception,), {}), PortAudioError=type('AudioError', (Exception,), {}))
        with patch.dict(sys.modules, {'sounddevice': fake}), self.assertRaises(microphone.CaptureCancelled):
            microphone.record(seconds=1, stop_requested=cancelled)
        self.assertEqual(closed, [True])

if __name__ == '__main__':
    unittest.main()
