"""Check T02 conformance data. Not a firmware/parser implementation.

Usage: python tools/validate_protocol_vectors.py
Or:    python validate_protocol_vectors.py path/to/protocol-vectors.json
"""
import binascii
import json
import sys
from pathlib import Path

def check(condition, message):
    if not condition:
        raise ValueError(message)

def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / 'docs' / 'protocol-vectors.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    check(data['contract_version'] == 1 and data['max_text_bytes'] == 48, 'contract constants')
    check(binascii.crc_hqx(b'123456789', 0xFFFF) == 0x29B1, 'CRC known answer')
    ids = []
    cases = {case['id']: case for case in data['packet_cases']}
    for case in data['packet_cases']:
        ids.append(case['id'])
        packet = bytes.fromhex(case['packet_hex']) if 'packet_hex' in case else None
        if packet is not None:
            check(len(packet) == 11 + packet[8], f"{case['id']}: envelope length")
            crc_ok = binascii.crc_hqx(packet[:-2], 0xFFFF) == int.from_bytes(packet[-2:], 'big')
            check(crc_ok == (case['id'] != 'checksum-failure'), f"{case['id']}: CRC expectation")
            for event in case['expected_events']:
                if event['event'] in ('message', 'duplicate'):
                    check(packet[:2] == b'\x01\x01' and 1 <= packet[8] <= 48, 'valid header')
                    check(all(32 <= b <= 126 for b in packet[9:-2]) and packet[9:-2].strip(b' '), 'valid text')
                    check(event['session'] == packet[2:6].hex().upper(), 'session byte order')
                    check(event['seq'] == int.from_bytes(packet[6:8], 'big'), 'sequence byte order')
                    if event['event'] == 'message':
                        check(event['payload_hex'] == packet[9:-2].hex().upper(), 'payload hex')
        for symbol in case.get('symbols', []):
            address = int(symbol['address_hex'], 16)
            check(address >> 8 == 0xA7 and (address & 255) <= 58, 'symbol address bounds')
            check(0 <= int(symbol['command_hex'], 16) <= 255, 'symbol byte bounds')
        if packet is not None and 'symbols' in case:
            check(bytes(int(s['command_hex'], 16) for s in case['symbols']) == packet, 'symbol packet bytes')
            check([int(s['address_hex'], 16) & 255 for s in case['symbols']] == list(range(len(packet))), 'symbol indexes')
        for event in case['expected_events']:
            check(len(json.dumps(event, separators=(',', ':')).encode('ascii')) <= 256, 'event line limit')
            if event['event'] == 'disturbance':
                check(event['session'] is None and event['seq'] is None, 'untrusted metadata')
    partial = cases['partial-timeout']
    check(partial['advance_to_ms'] - partial['symbols'][-1]['at_ms'] == 500, 'partial timeout boundary')
    whole = cases['whole-packet-timeout']
    check(whole['advance_to_ms'] == 9000 and whole['advance_to_ms'] - whole['symbols'][-1]['at_ms'] < 500, 'whole-packet timer boundary')
    gap_indexes = [int(s['address_hex'], 16) & 255 for s in cases['index-gap']['symbols']]
    check(gap_indexes[:4] == [0, 1, 2, 4], 'gap fixture')
    check(cases['total-loss-silence']['expected_events'] == [] and not cases['total-loss-silence']['symbols'], 'silence is not failure')
    check(cases['duplicate']['packet_hex'] == cases['duplicate']['cache']['packet_hex'], 'identical duplicate')
    check(cases['id-conflict']['packet_hex'] != cases['id-conflict']['cache']['packet_hex'], 'conflicting payload')
    check(cases['dedup-expired']['cache']['age_ms_at_delivery'] == 60000, 'cache expiry boundary')
    check(len(bytes.fromhex(cases['valid-max48']['packet_hex'])) == 59, 'maximum packet')
    for case in data['serial_cases']:
        ids.append(case['id'])
        if 'line' in case and case['expected'] == 'accepted':
            line = case['line'].removesuffix('\n')
            fields = line.split('\t')
            check(len(line.encode('ascii')) <= 128 and len(fields) == 4, 'serial bound/fields')
            packet = bytes.fromhex(case['packet_hex'])
            check(fields[1] == packet[2:6].hex().upper() and int(fields[2], 16) == int.from_bytes(packet[6:8], 'big'), 'serial identity')
            check(fields[3] == packet[9:-2].hex().upper(), 'serial text')
        if case['id'] == 'split-and-multiple':
            check(''.join(case['chunks']).splitlines() == case['expected_lines'], 'split read reconstruction')
        if case['id'] == 'line-overflow':
            check(len(case['line'].removesuffix('\n')) == 129, 'serial overflow')
    check(len(ids) == len(set(ids)), 'unique case IDs')
    check(len(data['packet_cases']) >= 14 and len(data['serial_cases']) >= 8, 'fixture coverage count')
    print(f"PASS: {len(data['packet_cases'])} packet cases and {len(data['serial_cases'])} serial cases; CRC, bounds, identities and fixture consistency verified. State machines and hardware not tested.")

if __name__ == '__main__':
    main()
