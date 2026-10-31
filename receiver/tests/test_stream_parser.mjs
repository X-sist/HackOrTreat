import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { StreamParser, decodePayloadHex } from '../src/stream_parser.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, '../../');

let totalTests = 0;
let passedTests = 0;

function assert(condition, message) {
  totalTests++;
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
  passedTests++;
}

console.log('--- Running StreamParser Unit Tests ---');

// Test 1: Single valid message line
{
  const received = [];
  const parser = new StreamParser({
    onMessage: (msg) => received.push(msg),
  });

  parser.push('{"v":1,"event":"message","session":"12345678","seq":1,"payload_hex":"4869"}\n');
  assert(received.length === 1, 'Test 1: exactly one message received');
  assert(received[0].session === '12345678', 'Test 1: session matches');
  assert(received[0].seq === 1, 'Test 1: seq matches');
  assert(received[0].text === 'Hi', 'Test 1: payload_hex decoded to "Hi"');
}

// Test 2: Split reads across multiple push calls
{
  const received = [];
  const parser = new StreamParser({
    onMessage: (msg) => received.push(msg),
  });

  parser.push('{"v":1,"event":"mes');
  parser.push('sage","session":"ABCDEF01","seq":42,"payload_hex":"53706972');
  parser.push('6974"}\n');

  assert(received.length === 1, 'Test 2: message assembled across 3 chunks');
  assert(received[0].session === 'ABCDEF01', 'Test 2: session matches');
  assert(received[0].seq === 42, 'Test 2: seq matches');
  assert(received[0].text === 'Spirit', 'Test 2: payload decoded to "Spirit"');
}

// Test 3: Multiple events in single chunk, with \r\n and blank lines
{
  const hellos = [];
  const messages = [];
  const parser = new StreamParser({
    onHello: (h) => hellos.push(h),
    onMessage: (m) => messages.push(m),
  });

  const payload = '\r\n\n{"v":1,"event":"hello","role":"rx","max_text_bytes":48}\r\n\r\n{"v":1,"event":"message","session":"11223344","seq":0,"payload_hex":"4F6B"}\n';
  parser.push(payload);

  assert(hellos.length === 1, 'Test 3: hello received');
  assert(hellos[0].maxTextBytes === 48, 'Test 3: maxTextBytes 48');
  assert(messages.length === 1, 'Test 3: message received');
  assert(messages[0].text === 'Ok', 'Test 3: text is "Ok"');
}

// Test 4: Disturbance events
{
  const disturbances = [];
  const parser = new StreamParser({
    onDisturbance: (d) => disturbances.push(d),
  });

  parser.push('{"v":1,"event":"disturbance","code":"CHECKSUM_FAILED","reason":"CRC_MISMATCH","session":null,"seq":null}\n');
  parser.push('{"v":1,"event":"disturbance","code":"INCOMPLETE_PACKET","reason":"INDEX_GAP","session":null,"seq":null}\n');

  assert(disturbances.length === 2, 'Test 4: 2 disturbances parsed');
  assert(disturbances[0].code === 'CHECKSUM_FAILED', 'Test 4: CHECKSUM_FAILED code');
  assert(disturbances[0].reason === 'CRC_MISMATCH', 'Test 4: CRC_MISMATCH reason');
  assert(disturbances[1].reason === 'INDEX_GAP', 'Test 4: INDEX_GAP reason');
}

// Test 5: Duplicate and protocol error events
{
  const duplicates = [];
  const protoErrors = [];
  const parser = new StreamParser({
    onDuplicate: (d) => duplicates.push(d),
    onProtocolError: (p) => protoErrors.push(p),
  });

  parser.push('{"v":1,"event":"duplicate","session":"DEADBEEF","seq":5}\n');
  parser.push('{"v":1,"event":"protocol_error","code":"UNSUPPORTED_TYPE"}\n');

  assert(duplicates.length === 1, 'Test 5: duplicate parsed');
  assert(duplicates[0].session === 'DEADBEEF', 'Test 5: duplicate session');
  assert(protoErrors.length === 1, 'Test 5: protocol error parsed');
  assert(protoErrors[0].code === 'UNSUPPORTED_TYPE', 'Test 5: protocol error code');
}

// Test 6: Bounded read overflow - discarding line exceeding 256 bytes
{
  const streamErrors = [];
  const messages = [];
  const parser = new StreamParser({
    onMessage: (m) => messages.push(m),
    onStreamError: (e) => streamErrors.push(e),
  });

  // Create an oversized line (300 chars) followed by a valid message
  const oversized = 'A'.repeat(300) + '\n';
  const valid = '{"v":1,"event":"message","session":"AABBCCDD","seq":2,"payload_hex":"41"}\n';

  parser.push(oversized + valid);

  assert(streamErrors.length >= 1, 'Test 6: stream error emitted for oversized line');
  assert(streamErrors[0].type === 'LINE_TOO_LONG', 'Test 6: error type LINE_TOO_LONG');
  assert(messages.length === 1, 'Test 6: valid message after oversized line was cleanly parsed');
  assert(messages[0].text === 'A', 'Test 6: message payload is "A"');
}

// Test 7: Malformed JSON handling
{
  const streamErrors = [];
  const parser = new StreamParser({
    onStreamError: (e) => streamErrors.push(e),
  });

  parser.push('{ not valid json }\n');
  assert(streamErrors.length === 1, 'Test 7: malformed JSON error emitted');
  assert(streamErrors[0].type === 'MALFORMED_JSON', 'Test 7: error type is MALFORMED_JSON');
}

// Test 8: Replay all rx fixtures from shared/fixtures/events.json
{
  const fixturesPath = path.join(ROOT, 'shared/fixtures/events.json');
  const fixtures = JSON.parse(fs.readFileSync(fixturesPath, 'utf8'));

  let rxCount = 0;
  for (const item of fixtures) {
    if (item.role !== 'rx') continue;
    rxCount++;

    let callbackCalled = false;
    let streamErrorCalled = false;

    const parser = new StreamParser({
      onMessage: () => { callbackCalled = true; },
      onDisturbance: () => { callbackCalled = true; },
      onDuplicate: () => { callbackCalled = true; },
      onHello: () => { callbackCalled = true; },
      onProtocolError: () => { callbackCalled = true; },
      onError: () => { callbackCalled = true; },
      onStreamError: () => { streamErrorCalled = true; },
    });

    const line = JSON.stringify(item.value) + '\n';
    parser.push(line);

    if (item.valid) {
      assert(callbackCalled && !streamErrorCalled, `Fixture ${item.id} should be accepted`);
    } else {
      assert(streamErrorCalled && !callbackCalled, `Fixture ${item.id} should be rejected`);
    }
  }
  console.log(`Replayed ${rxCount} rx fixtures from shared/fixtures/events.json`);
}

// Test 9: decodePayloadHex helper
{
  assert(decodePayloadHex('48656C6C6F') === 'Hello', 'Test 9: Hello');
  assert(decodePayloadHex('5370697269742C207768617420697320796F7572206E616D653F') === 'Spirit, what is your name?', 'Test 9: Demo phrase');
}

console.log(`\nPASS: ${passedTests}/${totalTests} assertions passed cleanly.`);
