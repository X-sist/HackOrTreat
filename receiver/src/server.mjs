import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { StreamParser } from './stream_parser.mjs';
import { QwenInference } from './qwen_inference.mjs';
import { AudioEngine } from './audio_engine.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PUBLIC_DIR = path.join(__dirname, '../public');

const PORT = parseInt(process.env.PORT || '3000', 10);
const sseClients = new Set();
const DEMO_MODE = process.env.DEMO_MODE === '1';
let lastHello = null;

function broadcastEvent(type, payload) {
  const message = `event: ${type}\ndata: ${JSON.stringify({ ...payload, timestamp: new Date().toISOString() })}\n\n`;
  for (const client of sseClients) {
    try {
      client.write(message);
    } catch {
      sseClients.delete(client);
    }
  }
}

// Initialize Subsystems
const qwen = new QwenInference();
const audio = new AudioEngine();

// Instantiate StreamParser wired to Qwen and Audio pipelines
const parser = new StreamParser({
  onMessage: ({ session, seq, text, raw }) => {
    broadcastEvent('input_received', { session, seq, text, raw });
    qwen.recordValidMessage(text);
    void respond({ type: 'message', text }, { session, seq, promptText: text, disturbed: false });
  },

  onDisturbance: ({ code, reason, session, seq, raw }) => {
    broadcastEvent('disturbance', { code, reason, session, seq, raw });
    void respond({ type: 'disturbance', code, reason }, { code, reason, disturbed: true });
  },

  onDuplicate: ({ session, seq, raw }) => {
    // Strictly per PROTOCOL.md: duplicate emits event without delivery, animation, or inference
    broadcastEvent('duplicate', { session, seq, raw });
  },

  onHello: ({ role, maxTextBytes, raw }) => {
    lastHello = { role, maxTextBytes, raw };
    qwen.lastValidText = null;
    qwen.lastDisturbanceTimestamp = 0;
    broadcastEvent('hello', { role, maxTextBytes, raw });
  },

  onProtocolError: ({ code, raw }) => {
    broadcastEvent('protocol_error', { code, raw });
  },

  onError: ({ code, raw }) => {
    broadcastEvent('error', { code, raw });
  },

  onStreamError: ({ type, line, error }) => {
    broadcastEvent('stream_error', { type, line, error: error.message });
  },
});

async function respond(request, metadata) {
  try {
    broadcastEvent('spirit_thinking', { stage: 'invoking_qwen' });
    const result = await qwen.generateResponse(request);
    if (result.coalesced) {
      broadcastEvent('service_notice', { message: 'Spirit request skipped while busy or during disturbance cooldown.' });
      return;
    }
    if (DEMO_MODE && result.offline) {
      broadcastEvent('service_error', { source: 'Ollama', message: result.error || 'No generated response. Check the local model service.' });
      return;
    }
    const voice = await audio.synthesize(result.text, { disturbed: metadata.disturbed });
    if (!voice.success || (DEMO_MODE && !voice.usedPiper)) {
      broadcastEvent('service_error', { source: 'Piper', message: voice.error || voice.honestNotice || 'Speech synthesis failed.' });
    }
    broadcastEvent('spirit_response', {
      ...metadata, responseText: result.text,
      audioFile: voice.success && (!DEMO_MODE || voice.usedPiper) ? voice.audioFile : undefined,
      offlineNotice: result.offline ? 'Canned diagnostic fallback; no model response was generated.' : undefined,
      audioNotice: voice.honestNotice,
    });
  } catch (error) {
    broadcastEvent('service_error', { source: 'Receiver', message: error.message });
  }
}

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.wav': 'audio/wav',
};

const server = http.createServer((req, res) => {
  const parsedUrl = new URL(req.url, `http://${req.headers.host}`);
  const pathname = parsedUrl.pathname;

  // SSE Stream
  if (pathname === '/events') {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Access-Control-Allow-Origin': '*',
    });
    res.write(`event: connected\ndata: ${JSON.stringify({ status: 'ok', role: 'rx' })}\n\n`);
    sseClients.add(res);
    if (lastHello) res.write(`event: hello\ndata: ${JSON.stringify(lastHello)}\n\n`);

    req.on('close', () => {
      sseClients.delete(res);
    });
    return;
  }

  // API: Ingest raw NDJSON bytes from external stream or serial forwarder
  if (pathname === '/api/ingest' && req.method === 'POST') {
    let body = '';
    let overflow = false;
    req.on('data', chunk => {
      if (overflow) return;
      if (Buffer.byteLength(body) + chunk.length > 1024) {
        overflow = true; body = ''; res.writeHead(413); res.end('Event batch too large'); return;
      }
      body += chunk;
    });
    req.on('end', () => {
      if (overflow) return;
      parser.push(body);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: true, bytesReceived: body.length }));
    });
    return;
  }

  // API: Simulate demo events
  if (pathname === '/api/simulate' && req.method === 'POST') {
    if (DEMO_MODE) { res.writeHead(403); res.end('Simulation disabled for the real demo'); return; }
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const payload = JSON.parse(body || '{}');
        const type = payload.type || 'message';

        if (type === 'message') {
          const text = payload.text || 'Spirit, what is your name?';
          const hex = Buffer.from(text, 'ascii').toString('hex').toUpperCase();
          const line = JSON.stringify({
            v: 1,
            event: 'message',
            session: 'CAFE0001',
            seq: 1,
            payload_hex: hex,
          }) + '\n';
          parser.push(line);
        } else if (type === 'disturbance_checksum') {
          const line = JSON.stringify({
            v: 1,
            event: 'disturbance',
            code: 'CHECKSUM_FAILED',
            reason: 'CRC_MISMATCH',
            session: null,
            seq: null,
          }) + '\n';
          parser.push(line);
        } else if (type === 'disturbance_gap') {
          const line = JSON.stringify({
            v: 1,
            event: 'disturbance',
            code: 'INCOMPLETE_PACKET',
            reason: 'INDEX_GAP',
            session: null,
            seq: null,
          }) + '\n';
          parser.push(line);
        } else if (type === 'duplicate') {
          const line = JSON.stringify({
            v: 1,
            event: 'duplicate',
            session: 'CAFE0001',
            seq: 1,
          }) + '\n';
          parser.push(line);
        }

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, type }));
      } catch (err) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: err.message }));
      }
    });
    return;
  }

  // API: Status
  if (pathname === '/api/status' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'active',
      demoMode: DEMO_MODE,
      serialConnected: Boolean(lastHello),
      role: 'rx',
      connectedClients: sseClients.size,
      qwen: {
        host: qwen.host,
        model: qwen.model,
        lastValidText: qwen.lastValidText,
      },
    }));
    return;
  }

  // Static files from receiver/public
  const filePath = path.join(PUBLIC_DIR, pathname === '/' ? 'index.html' : pathname);
  const normalized = path.normalize(filePath);
  if (!normalized.startsWith(PUBLIC_DIR)) {
    res.writeHead(403, { 'Content-Type': 'text/plain' });
    res.end('Forbidden');
    return;
  }

  fs.stat(normalized, (err, stats) => {
    if (err || !stats.isFile()) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('404 Not Found');
      return;
    }
    const ext = path.extname(normalized).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': contentType });
    fs.createReadStream(normalized).pipe(res);
  });
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`=======================================================`);
  console.log(`  HACKORTREAT RECEIVER — OUIJA SPIRIT PLANE (CS2)      `);
  console.log(`  Web Display: http://localhost:${PORT}               `);
  console.log(`  SSE Stream:  http://localhost:${PORT}/events        `);
  console.log(`  NDJSON API:  POST http://localhost:${PORT}/api/ingest`);
  console.log(`=======================================================`);
});

export { server, parser, qwen, audio };
