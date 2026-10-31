/** Local receiver launcher: COM -> validated NDJSON -> same-laptop UI. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { spawn, execFile } from 'node:child_process';
import { CONTRACT } from '../shared/generated/protocol.mjs';
import { validateEvent } from '../shared/js/contract.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SERIAL_SCRIPT = path.join(ROOT, 'tools/read_receiver_serial.ps1');
const C = CONTRACT.constants;

export class ReceiverLines {
  constructor(diagnostic = console.error) {
    this.bytes = []; this.discard = false; this.diagnostic = diagnostic;
  }
  push(chunk) {
    const events = [];
    for (const byte of chunk) {
      if (byte === 10) {
        if (!this.discard && this.bytes.length) {
          if (this.bytes.at(-1) === 13) this.bytes.pop();
          if (this.bytes.length) {
            try {
              if (this.bytes.some(b => b > 127)) throw new Error('Non-ASCII event');
              const value = JSON.parse(Buffer.from(this.bytes).toString('ascii'));
              if (value?.event === 'hello' && value.role !== 'rx') {
                throw new WrongBoard('This is the transmitter. Choose the receiver Arduino port.');
              }
              validateEvent(value, 'rx');
              events.push(value);
            } catch (error) {
              if (error instanceof WrongBoard) throw error;
              this.diagnostic(`Ignored invalid serial event: ${error.message}`);
            }
          }
        }
        this.bytes = []; this.discard = false;
      } else if (!this.discard) {
        this.bytes.push(byte);
        if (this.bytes.length > C.MAX_EVENT_LINE_BYTES &&
            !(this.bytes.length === C.MAX_EVENT_LINE_BYTES + 1 && byte === 13)) {
          this.bytes = []; this.discard = true;
          this.diagnostic('Serial line overflow; discarding through the next newline.');
        }
      }
    }
    return events;
  }
}
class WrongBoard extends Error {}

export async function forwardEvents(readable, { ingest, ready, diagnostic = console.error }) {
  const lines = new ReceiverLines(diagnostic);
  let identified = false;
  for await (const chunk of readable) {
    for (const event of lines.push(chunk)) {
      if (!identified && event.event !== 'hello') {
        diagnostic('Ignoring serial event until a valid receiver hello.');
        continue;
      }
      await ingest(JSON.stringify(event) + '\n');
      if (event.event === 'hello' && !identified) {
        identified = true;
        ready();
      }
      if (event.event === 'message') {
        console.log(`[REAL IR INPUT] ${Buffer.from(event.payload_hex, 'hex').toString('ascii')}`);
      }
    }
  }
  throw new Error('Receiver serial reader stopped. Reconnect explicitly; nothing was retried.');
}

function options(argv) {
  const result = { model: 'qwen2.5:1.5b', webPort: 3000 };
  const names = { '--port': 'port', '--piper': 'piper', '--voice': 'voice', '--model': 'model', '--web-port': 'webPort' };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--list-ports') result.list = true;
    else if (argv[i] === '--check') result.check = true;
    else if (names[argv[i]] && argv[i + 1] && !argv[i + 1].startsWith('--')) result[names[argv[i]]] = argv[++i];
    else throw new Error(`Unknown or incomplete option: ${argv[i]}`);
  }
  result.webPort = Number(result.webPort);
  if (!Number.isInteger(result.webPort) || result.webPort < 1024 || result.webPort > 65535) throw new Error('Choose a web port from 1024 to 65535.');
  if (!result.list && !result.check && !/^COM[1-9][0-9]*$/i.test(result.port || '')) {
    throw new Error('Usage: node tools/demo_receiver.mjs --port COMx [--piper path] [--voice path]\nUse --list-ports to find ports or --check to test Ollama/Piper only.');
  }
  return result;
}

async function localJson(url, init = {}, timeout = 5000) {
  const response = await fetch(url, { ...init, signal: AbortSignal.timeout(timeout) });
  if (!response.ok) throw new Error(`${url}: HTTP ${response.status}`);
  return response.json();
}

async function services(args) {
  const host = 'http://127.0.0.1:11434';
  const tags = await localJson(host + '/api/tags');
  if (!tags.models?.some(m => m.name === args.model || m.model === args.model)) {
    throw new Error(`Ollama model ${args.model} is not installed. Prepare it while online before the demo.`);
  }
  console.log(`Warming local ${args.model}; no cloud service is used...`);
  const model = await localJson(host + '/api/generate', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model: args.model, prompt: 'Reply with READY.', stream: false, keep_alive: '30m', options: { num_predict: 12 } }),
  }, 120000);
  if (!model.response?.trim()) throw new Error('Ollama returned no generated text.');
  const candidates = ['receiver/audio/.venv/Scripts/piper.exe', 'receiver/.venv/Scripts/piper.exe'].map(p => path.join(ROOT, p));
  const piper = args.piper || process.env.PIPER_EXE || candidates.find(p => fs.existsSync(p)) || 'piper';
  const voice = path.resolve(ROOT, args.voice || process.env.PIPER_MODEL || 'receiver/models/piper/en_US-lessac-medium.onnx');
  if (!fs.existsSync(voice) || !fs.existsSync(voice + '.json')) {
    throw new Error('Piper voice and matching .onnx.json are missing. Supply --voice with the installed .onnx path.');
  }
  const directory = path.join(ROOT, 'receiver/.local/demo');
  fs.mkdirSync(directory, { recursive: true });
  const output = path.join(directory, 'voice-check.wav');
  if (fs.existsSync(output)) fs.unlinkSync(output); // Only our disposable preflight file.
  await new Promise((resolve, reject) => {
    const child = execFile(piper, ['-m', voice, '-f', output],
      { cwd: ROOT, timeout: 30000, windowsHide: true, maxBuffer: 1024 * 1024 },
      error => error ? reject(new Error(`Piper voice check failed: ${error.message}. Use --piper with the installed executable path.`)) : resolve());
    child.stdin.on('error', () => {});
    child.stdin.end('The spirit is ready.\n');
  });
  const wav = fs.readFileSync(output);
  if (wav.length <= 44 || wav.toString('ascii', 0, 4) !== 'RIFF' || wav.toString('ascii', 8, 12) !== 'WAVE') {
    throw new Error('Piper did not produce a valid speech WAV.');
  }
  console.log('Local Qwen generation and Piper speech synthesis passed.');
  return { host, piper, voice };
}

export async function main(argv = process.argv.slice(2)) {
  const args = options(argv);
  if (args.list) {
    const child = spawn('powershell.exe', ['-NoLogo', '-NoProfile', '-File', SERIAL_SCRIPT, '-ListPorts'], { stdio: 'inherit', windowsHide: true });
    await new Promise((resolve, reject) => {
      child.on('error', reject);
      child.on('exit', code => code === 0 ? resolve() : reject(new Error('Serial port listing failed.')));
    });
    return;
  }
  const readyServices = await services(args);
  if (args.check) return;
  const base = `http://127.0.0.1:${args.webPort}`;
  let occupied = false;
  try { await fetch(base + '/api/status', { signal: AbortSignal.timeout(1000) }); occupied = true; } catch {}
  if (occupied) throw new Error('A web server is already running on this port. Close it or choose --web-port.');
  let web, reader, bootTimer;
  const close = () => { clearTimeout(bootTimer); reader?.kill(); web?.kill(); };
  let stopping = false;
  const stop = () => { stopping = true; close(); };
  process.once('SIGINT', stop);
  process.once('SIGTERM', stop);
  try {
    web = spawn(process.execPath, [path.join(ROOT, 'receiver/src/server.mjs')], {
      cwd: ROOT, stdio: ['ignore', 'inherit', 'inherit'], windowsHide: true,
      env: { ...process.env, PORT: String(args.webPort), OLLAMA_HOST: readyServices.host,
        OLLAMA_MODEL: args.model, QWEN_TIMEOUT_MS: '30000', PIPER_EXE: readyServices.piper, PIPER_MODEL: readyServices.voice, DEMO_MODE: '1' },
    });
    let webError;
    web.on('error', error => { webError = error; });
    for (let attempt = 0; ; attempt++) {
      if (webError || web.exitCode !== null) throw webError || new Error('Receiver web server exited.');
      try {
        const status = await localJson(base + '/api/status');
        if (status.demoMode !== true) throw new Error('Unexpected receiver server; restart with the integrated launcher.');
        break;
      } catch (error) {
        if (attempt >= 40) throw error;
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    }
    reader = spawn('powershell.exe', ['-NoLogo', '-NoProfile', '-File', SERIAL_SCRIPT, '-Port', args.port],
      { cwd: ROOT, stdio: ['ignore', 'pipe', 'inherit'], windowsHide: true });
    const failure = new Promise((_, reject) => {
      reader.once('error', reject);
      web.once('exit', () => reject(new Error('Receiver web server stopped.')));
      bootTimer = setTimeout(() => reject(new Error('No valid Rx hello within the shared boot timeout. Check port, firmware and Serial Monitor.')), C.HOST_BOOT_TIMEOUT_MS);
    });
    const bridge = forwardEvents(reader.stdout, {
      ingest: body => localJson(base + '/api/ingest', { method: 'POST', headers: { 'Content-Type': 'application/x-ndjson' }, body }),
      ready: () => {
        clearTimeout(bootTimer);
        console.log(`RECEIVER READY on ${args.port}. Open ${base}, click Enable sound, then send from Laptop 1.`);
      },
    });
    try { await Promise.race([bridge, failure]); }
    catch (error) { if (!stopping) throw error; }
  } finally {
    process.removeListener('SIGINT', stop); process.removeListener('SIGTERM', stop);
    close();
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  main().catch(error => { console.error(`Demo stopped: ${error.message}`); process.exitCode = 1; });
}
