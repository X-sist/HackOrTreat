"""Living Plane: offline transcript CLI with explicit local Arduino sending."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from serial_adapter import clean_text, validate_local_port
from serial_connection import SenderConnection, list_ports, send_once
from microphone import CaptureCancelled, enter_pressed, input_devices, record
from speech import Transcriber, pcm_wave

def show_text(text, manual=False, sender=None):
    if not text.strip():
        print('No recognizable speech/text. Try again.')
        return False
    if manual and len(text) > 4096:
        raise ValueError('Manual text is too long (maximum 4096 characters).')
    # Show original speech/text separately from the exact outgoing normalized bytes.
    print(('Manual text: ' if manual else 'Recognized: ') + text)
    if sender is None:
        print('Text only -- nothing sent. Use --send --port COMx with an explicit input mode.')
    else:
        sender(clean_text(text))
    return True

def devices():
    available = input_devices()
    if not available:
        raise ValueError('No microphone inputs found. Connect/enable an input in Windows Sound settings.')
    for index, name, channels in available:
        print(f'{index}: {name} ({channels} input channel(s))')

def capture_once(transcriber, device, seconds, interactive=False, sender=None):
    print(f'Recording (maximum {seconds:g}s). ' + ('Press Enter to stop; ' if interactive else '') + 'Ctrl+C cancels.', flush=True)
    samples, rate = record(device, seconds, stop_requested=enter_pressed if interactive else None)
    print('Transcribing locally...', flush=True)
    return show_text(transcriber.transcribe(pcm_wave(samples, rate)), sender=sender)

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--list-devices', action='store_true')
    mode.add_argument('--list-ports', action='store_true', help='List serial devices without opening them')
    mode.add_argument('--check-serial', action='store_true', help='Check Tx hello/ready only; no text is sent')
    mode.add_argument('--text', help='Display manual text without loading a model or opening a mic')
    mode.add_argument('--audio', type=Path, help='Transcribe an existing local audio file')
    mode.add_argument('--record', action='store_true', help='Record one timed utterance and exit')
    parser.add_argument('--send', action='store_true', help='Explicitly send one text/audio/record result to the local Tx board')
    parser.add_argument('--port', help='Explicit local Windows COM port, e.g. COM8')
    parser.add_argument('--device', type=int, help='Input ID from --list-devices; otherwise use Windows default')
    parser.add_argument('--seconds', type=float, default=10, help='Capture limit, 0.25–30 seconds (default 10)')
    parser.add_argument('--model', type=Path, help='Prepared sender-local model directory')
    args = parser.parse_args(argv)
    if not 0.25 <= args.seconds <= 30:
        parser.error('--seconds must be between 0.25 and 30')
    if args.send and (not args.port or not (args.text is not None or args.audio or args.record)):
        parser.error('--send requires --port and one of --text, --audio or --record')
    if args.check_serial and not args.port:
        parser.error('--check-serial requires --port')
    if args.port and not (args.send or args.check_serial):
        parser.error('--port requires --send or --check-serial')
    if args.port:
        try:
            validate_local_port(args.port)
        except ValueError as error:
            parser.error(str(error))
    sender = (lambda text: send_once(args.port, text)) if args.send else None
    transcriber = Transcriber(args.model)
    try:
        if args.list_ports:
            ports = list_ports()
            for port, description in ports:
                print(f'{port}: {description}')
            if not ports:
                print('No serial devices found. Check USB data cable and driver.')
        elif args.check_serial:
            with SenderConnection(args.port):
                print('Connection check passed; no text sent.')
        elif args.list_devices:
            devices()
        elif args.text is not None:
            if not show_text(args.text, manual=True, sender=sender):
                return 2
        elif args.audio:
            print('Transcribing local file...', flush=True)
            if not show_text(transcriber.transcribe(args.audio), sender=sender):
                return 2
        elif args.record:
            if not capture_once(transcriber, args.device, args.seconds, sender=sender):
                return 2
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
                    print(f'Input/model/serial error: {error}', file=sys.stderr)
    except (KeyboardInterrupt, EOFError):
        print('\nCancelled.')
        return 130
    except (CaptureCancelled, ValueError, OSError, RuntimeError, ImportError) as error:
        print(f'Input/model/serial error: {error}', file=sys.stderr)
        return 2
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
