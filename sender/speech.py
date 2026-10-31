"""Offline file/PCM transcription, shared by the CLI; no microphone or serial I/O."""
import io
import os
import socket
import wave
from contextlib import ExitStack, contextmanager
from pathlib import Path
from unittest.mock import patch

from offline_check import SENDER, deny_network, verify_model_files

@contextmanager
def offline_mode():
    settings = {'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1', 'HF_HUB_DISABLE_TELEMETRY': '1', 'DO_NOT_TRACK': '1'}
    previous = {key: os.environ.get(key) for key in settings}
    os.environ.update(settings)
    try:
        with ExitStack() as guard:
            for owner, name in ((socket, 'create_connection'), (socket, 'getaddrinfo'), (socket.socket, 'connect'), (socket.socket, 'connect_ex')):
                guard.enter_context(patch.object(owner, name, deny_network))
            yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

def pcm_wave(samples, sample_rate):
    import numpy as np
    audio = np.asarray(samples, dtype=np.float32).reshape(-1)
    if audio.size == 0 or not np.isfinite(audio).all():
        raise ValueError('The microphone returned empty or invalid audio.')
    if not 8000 <= sample_rate <= 192000:
        raise ValueError('Unsupported microphone sample rate.')
    stream = io.BytesIO()
    with wave.open(stream, 'wb') as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(sample_rate)
        writer.writeframes((np.clip(audio, -1, 1) * 32767).astype('<i2').tobytes())
    stream.seek(0)
    return stream

class Transcriber:
    def __init__(self, model_path=None):
        self.path = Path(model_path) if model_path else SENDER / 'models/tiny.en'
        self._model = None

    def transcribe(self, source):
        if isinstance(source, (str, Path)):
            source = Path(source)
            if not source.is_file():
                raise ValueError('Audio file not found. Use an existing local file, not a URL.')
            source = str(source)
        with offline_mode():
            if self._model is None:
                model_path = verify_model_files(self.path)
                from faster_whisper import WhisperModel
                self._model = WhisperModel(str(model_path), device='cpu', compute_type='int8', cpu_threads=4, local_files_only=True)
            segments, _ = self._model.transcribe(source, language='en', beam_size=1, temperature=0, vad_filter=False, condition_on_previous_text=False)
            return ' '.join(segment.text.strip() for segment in segments).strip()
