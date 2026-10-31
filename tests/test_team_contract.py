import json
import tempfile
import unittest
from pathlib import Path
from shared.python.contract import build_send, validate_event
from tools.check_repo import ROOT, check_scope, check_repo, requirement_pins, check_python_environment, check_node_environment
from tools.generate_contract import outputs
from shared.generated.protocol import CONTRACT
TEMP_ROOT = ROOT / '.local' / 'test-tmp'

class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    def test_runtime_contract_is_immutable(self):
        with self.assertRaises(TypeError):
            CONTRACT['constants']['MAX_TEXT_BYTES'] = 64
    def test_existing_send_vectors(self):
        cases = json.loads((ROOT / 'docs/protocol-vectors.json').read_text())['serial_cases']
        for case in cases:
            if case.get('expected') == 'accepted':
                packet = bytes.fromhex(case['packet_hex'])
                self.assertEqual(build_send(packet[2:6].hex().upper(), int.from_bytes(packet[6:8], 'big'), packet[9:-2].decode('ascii')), case['line'])

    def test_sender_rejects_bad_identity_and_text(self):
        for session, seq, text in [('abcd1234', 1, 'Hi'), ('12345678', True, 'Hi'), ('12345678', 65536, 'Hi'), ('12345678', 0, 'A'*49), ('12345678', 0, '\n'), ('12345678', 0, 'é'), ('12345678', 0, '   ')]:
            with self.subTest(session=session, seq=seq, text=text), self.assertRaises(ValueError):
                build_send(session, seq, text)

    def test_shared_valid_and_invalid_event_cases(self):
        for case in json.loads((ROOT / 'shared/fixtures/events.json').read_text()):
            with self.subTest(case=case['id']):
                if case['valid']:
                    validate_event(case['value'], case['role'])
                else:
                    with self.assertRaises(ValueError):
                        validate_event(case['value'], case['role'])

    def test_component_scope(self):
        for role in ('firmware', 'sender', 'receiver'):
            check_scope(role, [f'{role}/README.md', f'{role}/tests/test_example.py'])
            for illegal in ('shared/contract.json', 'TASKS.md', f'{role}/contract.lock.json', '../sender/secret'):
                with self.subTest(role=role, path=illegal), self.assertRaises(ValueError):
                    check_scope(role, [illegal])

    def test_cross_owner_rename_is_not_allowed(self):
        with self.assertRaises(ValueError):
            check_scope('sender', ['sender/old.py', 'receiver/new.py'])
        check_scope('integration', ['sender/old.py', 'receiver/new.py', 'shared/contract.json'])

    def test_unpinned_and_unhashed_dependencies_fail(self):
        for line in ['x>=1.0', 'x==latest', '-r other.txt', 'x @ https://example.test/file.whl', 'x==1.0']:
            with self.subTest(line=line), self.assertRaises(ValueError):
                requirement_pins(line, hashed=True)
        self.assertEqual(requirement_pins('x==1.0 --hash=sha256:' + 'a'*64, hashed=True), {'x': '1.0'})

    def test_python_manifest_lock_disagreement_fails(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp:
            root = Path(temp)
            (root / 'requirements.in').write_text('x==1.0\n')
            (root / 'requirements.lock').write_text('x==2.0 --hash=sha256:' + 'a'*64)
            (root / 'runtime.json').write_text('{"status":"configured","python":"3.11.9"}')
            with self.assertRaisesRegex(ValueError, 'manifest/lock mismatch'):
                check_python_environment(root)

    def test_node_manifest_lock_disagreement_fails(self):
        with tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp:
            root = Path(temp)
            (root / 'package.json').write_text(json.dumps({'engines': {'node': '24.15.0'}, 'packageManager': 'npm@11.12.1', 'dependencies': {'x': '1.0.0'}}))
            (root / 'package-lock.json').write_text(json.dumps({'packages': {'': {'dependencies': {'x': '2.0.0'}}}}))
            with self.assertRaisesRegex(ValueError, 'manifest/lock mismatch'):
                check_node_environment(root)

    def test_stale_contract_and_consumer_pin_fail(self):
        for target in ('shared/generated/protocol.py', 'sender/contract.lock.json'):
            with self.subTest(target=target), tempfile.TemporaryDirectory(dir=TEMP_ROOT) as temp:
                root = Path(temp)
                (root / 'shared').mkdir()
                (root / 'shared/contract.json').write_text((ROOT / 'shared/contract.json').read_text())
                for name, expected in outputs(root).items():
                    path = root / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(expected)
                (root / target).write_text('stale')
                with self.assertRaisesRegex(ValueError, 'stale shared output or consumer pin'):
                    check_repo(root)

if __name__ == '__main__':
    unittest.main()
