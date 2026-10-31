"""Shared boundary helpers; no serial I/O, hardware, models or app state."""
import json
import re
from shared.generated.protocol import CONTRACT

C = CONTRACT['constants']

def _integer(value):
    # JSON has one number type; JS cannot distinguish 1 from 1.0 after parsing.
    # Accept integral numeric values consistently, but never booleans.
    return type(value) is int or (type(value) is float and value.is_integer())

def valid_text(data):
    return 1 <= len(data) <= C['MAX_TEXT_BYTES'] and all(32 <= byte <= 126 for byte in data) and bool(data.strip(b' '))

def validate_event(value, role):
    if role not in ('tx', 'rx') or not isinstance(value, dict):
        raise ValueError('invalid role or event object')
    if not _integer(value.get('v')) or value['v'] != C['PROTOCOL_VERSION']:
        raise ValueError('unsupported version')
    name = value.get('event')
    if not isinstance(name, str) or name not in CONTRACT['event_fields']:
        raise ValueError('unknown event')
    spec = CONTRACT['event_fields'][name]
    if role not in spec['roles'] or set(value) != {'v', 'event', *spec['required']}:
        raise ValueError('wrong role or fields')
    if len(json.dumps(value, separators=(',', ':'), ensure_ascii=True).encode('ascii')) > C['MAX_EVENT_LINE_BYTES']:
        raise ValueError('oversized event')
    if name == 'hello':
        if value['role'] != role or not _integer(value['max_text_bytes']) or value['max_text_bytes'] != C['MAX_TEXT_BYTES']:
            raise ValueError('hello mismatch')
    elif name == 'disturbance':
        reasons = CONTRACT['disturbance_reasons'].get(value['code']) if isinstance(value['code'], str) else None
        if reasons is None or value['reason'] not in reasons or value['session'] is not None or value['seq'] is not None:
            raise ValueError('invalid disturbance metadata')
    elif name in ('accepted', 'sent', 'message', 'duplicate'):
        if not isinstance(value['session'], str) or re.fullmatch(r'[0-9A-F]{8}', value['session']) is None:
            raise ValueError('invalid session')
        if not _integer(value['seq']) or not 0 <= value['seq'] <= 65535:
            raise ValueError('invalid sequence')
        if name == 'message':
            payload = value['payload_hex']
            if not isinstance(payload, str) or re.fullmatch(r'(?:[0-9A-F]{2})+', payload) is None or not valid_text(bytes.fromhex(payload)):
                raise ValueError('invalid payload')
    elif name in ('error', 'protocol_error'):
        allowed = CONTRACT['error_codes' if name == 'error' else 'protocol_error_codes']
        if value['code'] not in allowed:
            raise ValueError('unknown error code')
    return value

def build_send(session, seq, text):
    if not isinstance(session, str) or re.fullmatch(r'[0-9A-F]{8}', session) is None:
        raise ValueError('invalid session')
    if type(seq) is not int or not 0 <= seq <= 65535 or not isinstance(text, str):
        raise ValueError('invalid sequence or text')
    try:
        payload = text.encode('ascii')
    except UnicodeEncodeError as error:
        raise ValueError('ASCII required') from error
    if not valid_text(payload):
        raise ValueError('invalid text')
    return f'SEND\t{session}\t{seq:04X}\t{payload.hex().upper()}\n'
