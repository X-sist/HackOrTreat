import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Optional dotenv loader
try {
  const dotenv = await import('dotenv');
  dotenv.config();
} catch (e) {
  // dotenv not installed yet, use defaults
}

const PORT = process.env.PORT || 3000;
const SERIAL_PORT_PATH = process.env.SERIAL_PORT || 'COM3';
const BAUD_RATE = parseInt(process.env.BAUD_RATE || '115200', 10);
const OLLAMA_HOST = process.env.OLLAMA_HOST || 'http://127.0.0.1:11434';
const OLLAMA_MODEL = process.env.OLLAMA_MODEL || 'qwen2.5:1.5b';

// Keep track of connected SSE clients
const sseClients = new Set();

function broadcastEvent(type, data) {
  const payload = JSON.stringify({ type, data, timestamp: new Date().toISOString() });
  const message = `event: ${type}\ndata: ${payload}\n\n`;
  for (const client of sseClients) {
    try {
      client.write(message);
    } catch (err) {
      sseClients.delete(client);
    }
  }
}

// MIME types for static assets
const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.mp3': 'audio/mpeg',
  '.wav': 'audio/wav',
};

// System prompt for Qwen (Spirit Plane persona & aether disturbance handler)
const SPIRIT_SYSTEM_PROMPT = `You are a spirit speaking through an antique Ouija board in an offline room. 
Wi-Fi is severed. Communication arrives through an invisible optical infrared beam.
If the message contains corrupted text (e.g. asterisks, missing letters) or mentions <AETHER_DISTURBED>,
the physical IR beam has been broken by a mortal! React with supernatural distress, declaring that the living have disrupted the link.
Otherwise, respond to questions with brief, eerie, archaic prophecy.
CRITICAL CONSTRAINT: Keep your response short (10 to 20 words maximum) so the planchette can spell it letter by letter without stalling.`;

// Call Ollama local offline LLM
async function queryOllama(promptText, isDisturbed = false) {
  const effectivePrompt = isDisturbed
    ? `<AETHER_DISTURBED> Incoming corrupted packet: "${promptText}". A mortal broke the infrared beam.`
    : promptText;

  broadcastEvent('status', {
    stage: 'thinking',
    message: isDisturbed ? 'Disturbance detected! Channeling disrupted spirit...' : 'Channeling spirit response...'
  });

  try {
    const res = await fetch(`${OLLAMA_HOST}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: OLLAMA_MODEL,
        prompt: effectivePrompt,
        system: SPIRIT_SYSTEM_PROMPT,
        stream: false,
      }),
    });

    if (!res.ok) {
      throw new Error(`Ollama returned status ${res.status}: ${res.statusText}`);
    }

    const data = await res.json();
    const cleanResponse = (data.response || '').trim();

    broadcastEvent('spirit_response', {
      prompt: promptText,
      response: cleanResponse,
      disturbed: isDisturbed,
    });

    return cleanResponse;
  } catch (error) {
    const fallbackMessage = isDisturbed
      ? 'THE LIVING DISRUPT US. I AM TRAPPED.'
      : 'THE VEIL IS THIN. I HEAR THEE.';

    broadcastEvent('spirit_response', {
      prompt: promptText,
      response: fallbackMessage,
      disturbed: isDisturbed,
      offlineNotice: `Ollama not reachable (${error.message}). Using atmospheric fallback response.`,
    });

    return fallbackMessage;
  }
}

// SerialPort setup (graceful fallback if package is missing or hardware is not attached)
let serialPortInstance = null;
let serialStatus = 'SIMULATION_MODE';

async function initSerial() {
  try {
    const { SerialPort } = await import('serialport');
    const { ReadlineParser } = await import('@serialport/parser-readline');

    serialPortInstance = new SerialPort({
      path: SERIAL_PORT_PATH,
      baudRate: BAUD_RATE,
      autoOpen: false,
    });

    const parser = serialPortInstance.pipe(new ReadlineParser({ delimiter: '\n' }));

    serialPortInstance.open((err) => {
      if (err) {
        serialStatus = `PORT_ERROR: ${err.message}`;
        console.log(`[SerialPort] Could not open ${SERIAL_PORT_PATH}: ${err.message}`);
        console.log(`[SerialPort] Running in Simulation Mode.`);
        broadcastEvent('hardware_status', { serial: 'disconnected', port: SERIAL_PORT_PATH, error: err.message });
      } else {
        serialStatus = `CONNECTED: ${SERIAL_PORT_PATH} @ ${BAUD_RATE}`;
        console.log(`[SerialPort] Successfully listening on ${SERIAL_PORT_PATH} @ ${BAUD_RATE}`);
        broadcastEvent('hardware_status', { serial: 'connected', port: SERIAL_PORT_PATH });
      }
    });

    parser.on('data', async (line) => {
      const cleanLine = line.toString().trim();
      if (!cleanLine) return;
      console.log(`[Serial IN] ${cleanLine}`);

      const isDisturbed = cleanLine.includes('AETHER_DISTURBED') || cleanLine.includes('CHECKSUM_FAILED');
      broadcastEvent('raw_serial', { raw: cleanLine, isDisturbed });

      if (isDisturbed) {
        broadcastEvent('aether_disturbed', { text: cleanLine });
      }

      await queryOllama(cleanLine, isDisturbed);
    });

    serialPortInstance.on('error', (err) => {
      console.error(`[Serial Error] ${err.message}`);
      broadcastEvent('hardware_status', { serial: 'error', error: err.message });
    });
  } catch (err) {
    serialStatus = 'SIMULATION_MODE (serialport package not installed)';
    console.log(`[SerialPort] SerialPort package is not installed yet.`);
    console.log(`[SerialPort] Ready in Simulation Mode (use web UI test triggers).`);
  }
}

// HTTP Server
const server = http.createServer(async (req, res) => {
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
    res.write(`event: connected\ndata: ${JSON.stringify({ serialStatus, ollamaModel: OLLAMA_MODEL })}\n\n`);
    sseClients.add(res);

    req.on('close', () => {
      sseClients.delete(res);
    });
    return;
  }

  // API: Simulate incoming Arduino text or beam break
  if (pathname === '/api/simulate' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', async () => {
      try {
        const payload = JSON.parse(body || '{}');
        const text = payload.text || 'Spirit, what is your name?';
        const isDisturbed = Boolean(payload.disturbed);

        broadcastEvent('raw_serial', {
          raw: isDisturbed ? `[ERR] CHECKSUM_FAILED: AETHER_DISTURBED -> ${text}` : `[OK] ${text}`,
          isDisturbed,
        });

        if (isDisturbed) {
          broadcastEvent('aether_disturbed', { text });
        }

        const answer = await queryOllama(text, isDisturbed);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, text, isDisturbed, answer }));
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
      serialStatus,
      port: SERIAL_PORT_PATH,
      baudRate: BAUD_RATE,
      ollamaHost: OLLAMA_HOST,
      ollamaModel: OLLAMA_MODEL,
      clientsConnected: sseClients.size,
    }));
    return;
  }

  // Static file serving from ./public
  let filePath = path.join(__dirname, 'public', pathname === '/' ? 'index.html' : pathname);
  
  // Security guard against directory traversal
  const normalizedPath = path.normalize(filePath);
  if (!normalizedPath.startsWith(path.join(__dirname, 'public'))) {
    res.writeHead(403, { 'Content-Type': 'text/plain' });
    res.end('Access Denied');
    return;
  }

  fs.stat(normalizedPath, (err, stats) => {
    if (err || !stats.isFile()) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('404 Not Found');
      return;
    }

    const ext = path.extname(normalizedPath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';

    res.writeHead(200, { 'Content-Type': contentType });
    fs.createReadStream(normalizedPath).pipe(res);
  });
});

// Start server
server.listen(PORT, () => {
  console.log(`=======================================================`);
  console.log(`  BEYOND THE GRAVE - SPIRIT PLANE (Laptop 2 Output)    `);
  console.log(`  Web Interface: http://localhost:${PORT}             `);
  console.log(`  Serial Port:   ${SERIAL_PORT_PATH} (${BAUD_RATE} baud) `);
  console.log(`  Ollama Target: ${OLLAMA_HOST} [${OLLAMA_MODEL}]     `);
  console.log(`=======================================================`);
  initSerial();
});
