import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { Readable } from 'node:stream';
import { spawn } from 'node:child_process';
import http from 'node:http';
import { once } from 'node:events';
import { fileURLToPath } from 'node:url';
import { ReceiverLines, forwardEvents } from '../demo_receiver.mjs';
import { CONTRACT } from '../../shared/generated/protocol.mjs';

const C = CONTRACT.constants;
const hello = { v: C.PROTOCOL_VERSION, event: 'hello', role: 'rx', max_text_bytes: C.MAX_TEXT_BYTES };
const message = { v: C.PROTOCOL_VERSION, event: 'message', session: '12345678', seq: 1, payload_hex: '4869' };
const line = value => Buffer.from(JSON.stringify(value) + '\n');

test('bridge validates shared Rx fixtures, split bytes and multiple records', () => {
  const fixtures = JSON.parse(fs.readFileSync(new URL('../../shared/fixtures/events.json', import.meta.url)));
  for (const f of fixtures.filter(f => f.role === 'rx')) {
    const parser = new ReceiverLines(() => {});
    const result = [];
    for (const b of line(f.value)) result.push(...parser.push(Buffer.from([b])));
    assert.equal(result.length, f.valid ? 1 : 0, f.id);
  }
  assert.equal(new ReceiverLines().push(Buffer.concat([line(hello), line(message)])).length, 2);
});

test('bridge bounds unterminated input and recovers only after newline', () => {
  const parser = new ReceiverLines(() => {});
  parser.push(Buffer.alloc(50000, 65));
  assert.equal(parser.bytes.length, 0);
  assert.equal(parser.discard, true);
  assert.deepEqual(parser.push(Buffer.concat([line(message), line(hello)])), [hello]);
  const padded = Buffer.from(JSON.stringify(hello).padEnd(C.MAX_EVENT_LINE_BYTES, ' ') + '\r\n');
  assert.deepEqual(parser.push(padded), [hello]);
});

test('bridge refuses transmitter port and non-ASCII serial data', () => {
  assert.throws(() => new ReceiverLines().push(line({ ...hello, role: 'tx' })), /transmitter/);
  assert.deepEqual(new ReceiverLines(() => {}).push(Buffer.from([255, 10])), []);
});

test('bridge forwards no message before Rx hello and never retries failed ingest', async () => {
  const received = []; let ready = 0;
  await assert.rejects(forwardEvents(Readable.from([line(message), line(hello), line(message)]), {
    ingest: async body => received.push(JSON.parse(body)), ready: () => ready++, diagnostic: () => {},
  }), /serial reader stopped/);
  assert.deepEqual(received, [hello, message]);
  assert.equal(ready, 1);
  let attempts = 0;
  await assert.rejects(forwardEvents(Readable.from([line(hello), line(message)]), {
    ingest: async () => { attempts++; throw new Error('UI stopped'); }, ready: () => {},
  }), /UI stopped/);
  assert.equal(attempts, 1);
});

async function freePort() {
  const server = http.createServer();
  server.listen(0, '127.0.0.1'); await once(server, 'listening');
  const port = server.address().port;
  await new Promise(resolve => server.close(resolve));
  return port;
}

async function waitJson(url) {
  for (let i = 0; i < 60; i++) {
    try { return await (await fetch(url)).json(); } catch { await new Promise(r => setTimeout(r, 50)); }
  }
  throw new Error('Test receiver did not start');
}

test('real server demo endpoints distinguish generation, missing voice and model failure', { timeout: 20000 }, async () => {
  let failModel = false;
  const model = http.createServer(async (req, res) => {
    for await (const chunk of req) { }
    res.writeHead(failModel ? 503 : 200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ response: 'I AM THE TEST SPIRIT.' }));
  });
  model.listen(0, '127.0.0.1'); await once(model, 'listening');
  const port = await freePort();
  const base = `http://127.0.0.1:${port}`;
  const child = spawn(process.execPath, [fileURLToPath(new URL('../../receiver/src/server.mjs', import.meta.url))], {
    stdio: ['ignore', 'pipe', 'pipe'], windowsHide: true,
    env: { ...process.env, PORT: String(port), DEMO_MODE: '1', OLLAMA_HOST: `http://127.0.0.1:${model.address().port}`,
      PIPER_MODEL: fileURLToPath(new URL('./missing-test-voice.onnx', import.meta.url)),
      PIPER_EXE: 'missing-test-piper', QWEN_TIMEOUT_MS: '1000' },
  });
  child.stdout.resume(); child.stderr.resume();
  const controller = new AbortController();
  const received = [];
  let consume;
  try {
    const status = await waitJson(base + '/api/status');
    assert.equal(status.demoMode, true);
    assert.equal(status.serialConnected, false);
    assert.equal((await fetch(base + '/api/simulate', { method: 'POST', body: '{}' })).status, 403);
    assert.equal((await fetch(base + '/api/ingest', { method: 'POST', body: 'x'.repeat(1025) })).status, 413);
    const events = await fetch(base + '/events', { signal: controller.signal });
    consume = (async () => {
      let text = '';
      for await (const chunk of events.body) {
        text += Buffer.from(chunk).toString();
        let index;
        while ((index = text.indexOf('\n\n')) !== -1) {
          const record = text.slice(0, index); text = text.slice(index + 2);
          const name = record.match(/^event: (.*)/m)?.[1];
          const data = record.match(/^data: (.*)/m)?.[1];
          if (name && data) received.push({ name, data: JSON.parse(data) });
        }
      }
    })().catch(error => { if (error.name !== 'AbortError') throw error; });
    await fetch(base + '/api/ingest', { method: 'POST', body: line(hello) });
    await fetch(base + '/api/ingest', { method: 'POST', body: line(message) });
    for (let i = 0; i < 100 && !received.some(e => e.name === 'spirit_response'); i++) await new Promise(r => setTimeout(r, 20));
    const response = received.find(e => e.name === 'spirit_response');
    assert.equal(response?.data.responseText, 'I AM THE TEST SPIRIT.');
    assert.equal(response.data.audioFile, undefined);
    assert.ok(received.some(e => e.name === 'service_error' && e.data.source === 'Piper'));
    assert.equal((await (await fetch(base + '/api/status')).json()).serialConnected, true);
    received.length = 0;
    failModel = true;
    await fetch(base + '/api/ingest', { method: 'POST', body: line({ ...message, seq: 2 }) });
    for (let i = 0; i < 100 && !received.some(e => e.name === 'service_error'); i++) await new Promise(r => setTimeout(r, 20));
    assert.ok(received.some(e => e.name === 'service_error' && e.data.source === 'Ollama'));
    assert.equal(received.some(e => e.name === 'spirit_response'), false, 'No canned revelation after model failure');
  } finally {
    controller.abort();
    await consume;
    const exited = once(child, 'exit'); child.kill(); await exited;
    model.closeAllConnections(); await new Promise(resolve => model.close(resolve));
  }
});
