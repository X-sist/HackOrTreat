import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { StreamParser } from './stream_parser.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PUBLIC_DIR = path.join(__dirname, '../public');

const PORT = parseInt(process.env.PORT || '3000', 10);
const sseClients = new Set();

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

// Instantiate StreamParser wired to SSE broadcast
const parser = new StreamParser({
  onMessage: ({ session, seq, text, raw }) => {
    broadcastEvent('message', { session, seq, text, raw });
  },
  onDisturbance: ({ code, reason, raw }) => {
    broadcastEvent('disturbance', { code, reason, raw });
  },
  onDuplicate: ({ session, seq, raw }) => {
    broadcastEvent('duplicate', { session, seq, raw });
  },
  onHello: ({ role, maxTextBytes, raw }) => {
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

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
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

    req.on('close', () => {
      sseClients.delete(res);
    });
    return;
  }

  // API: Ingest raw NDJSON bytes from external stream or serial forwarder
  if (pathname === '/api/ingest' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      parser.push(body);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: true, bytesReceived: body.length }));
    });
    return;
  }

  // API: Simulate demo events
  if (pathname === '/api/simulate' && req.method === 'POST') {
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
      role: 'rx',
      connectedClients: sseClients.size,
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

server.listen(PORT, () => {
  console.log(`=======================================================`);
  console.log(`  HACKORTREAT RECEIVER — OUIJA SPIRIT PLANE (CS2)      `);
  console.log(`  Web Display: http://localhost:${PORT}               `);
  console.log(`  SSE Stream:  http://localhost:${PORT}/events        `);
  console.log(`  NDJSON API:  POST http://localhost:${PORT}/api/ingest`);
  console.log(`=======================================================`);
});

export { server, parser };
