"""Living Plane: offline microphone -> visible transcript. No serial output yet."""
import argparse
import sys
from pathlib import Path

from microphone import CaptureCancelled, enter_pressed, input_devices, record
from speech import Transcriber, pcm_wave

def show_text(text, manual=False):
    if not text.strip():
        print('No recognizable speech/text. Try again.')
        return False
    if manual and len(text) > 4096:
        raise ValueError('Manual text is too long (maximum 4096 characters).')
    # Preserve the recognized text; transport cleanup/limits are a later task.
    print(('Manual text: ' if manual else 'Recognized: ') + text)
    print('Text only -- no Arduino transmission in C1-02.')
    return True

def devices():
    available = input_devices()
    if not available:
        raise ValueError('No microphone inputs found. Connect/enable an input in Windows Sound settings.')
    for index, name, channels in available:
        print(f'{index}: {name} ({channels} input channel(s))')

def capture_once(transcriber, device, seconds, interactive=False):
    print(f'Recording (maximum {seconds:g}s). ' + ('Press Enter to stop; ' if interactive else '') + 'Ctrl+C cancels.', flush=True)
    samples, rate = record(device, seconds, stop_requested=enter_pressed if interactive else None)
    print('Transcribing locally...', flush=True)
    return show_text(transcriber.transcribe(pcm_wave(samples, rate)))

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--list-devices', action='store_true')
    mode.add_argument('--text', help='Display manual text without loading a model or opening a mic')
    mode.add_argument('--audio', type=Path, help='Transcribe an existing local audio file')
    mode.add_argument('--record', action='store_true', help='Record one timed utterance and exit')
    parser.add_argument('--device', type=int, help='Input ID from --list-devices; otherwise use Windows default')
    parser.add_argument('--seconds', type=float, default=10, help='Capture limit, 0.25–30 seconds (default 10)')
    parser.add_argument('--model', type=Path, help='Prepared sender-local model directory')
    args = parser.parse_args(argv)
    if not 0.25 <= args.seconds <= 30:
        parser.error('--seconds must be between 0.25 and 30')
    transcriber = Transcriber(args.model)
    try:
        if args.list_devices:
            devices()
        elif args.text is not None:
            show_text(args.text, manual=True)
        elif args.audio:
            print('Transcribing local file...', flush=True)
            show_text(transcriber.transcribe(args.audio))
        elif args.record:
            capture_once(transcriber, args.device, args.seconds)
        else:
            if not sys.stdin.isatty():
                raise ValueError('Interactive mode needs a terminal. Use --text, --audio, --list-devices or --record.')
            print('Living Plane -- offline Whisper. Audio stays in memory; nothing is sent.')
            while True:
                command = input('\nEnter=record | t=manual text | d=devices | q=quit: ').strip().lower()
                if command == 'q':
                    break
                try:
                    if command == 't':
                        show_text(input('Text: '), manual=True)
                    elif command == 'd':
                        devices()
                    elif command == '':
                        capture_once(transcriber, args.device, args.seconds, interactive=True)
                    else:
                        print('Use Enter, t, d or q.')
                except (CaptureCancelled, ValueError, OSError, RuntimeError) as error:
                    print(f'Input/model error: {error}', file=sys.stderr)
    except (KeyboardInterrupt, EOFError):
        print('\nCancelled.')
        return 130
    except (CaptureCancelled, ValueError, OSError, RuntimeError, ImportError) as error:
        print(f'Input/model error: {error}', file=sys.stderr)
        return 2
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
