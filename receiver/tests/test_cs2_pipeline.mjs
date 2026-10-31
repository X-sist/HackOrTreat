import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { QwenInference, DISTURBANCE_COOLDOWN_MS } from '../src/qwen_inference.mjs';
import { AudioEngine } from '../src/audio_engine.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let total = 0;
let passed = 0;

function assert(cond, msg) {
  total++;
  if (!cond) throw new Error(`Assertion failed: ${msg}`);
  passed++;
}

console.log('--- Running CS2 Full Pipeline Tests (T09, T10, T11) ---');

// =========================================================================
// T09: Qwen Offline Inference Tests
// =========================================================================
{
  const qwen = new QwenInference({ host: 'http://127.0.0.1:1' }); // Deliberately unavailable; never depends on a running local model.

  // Test 1: Record valid message
  qwen.recordValidMessage('Spirit, what is your name?');
  assert(qwen.lastValidText === 'Spirit, what is your name?', 'T09.1: valid message recorded');

  // Test 2: Message prompt format
  const msgPrompt = qwen.formatPrompt({ type: 'message', text: 'Who walks here?' });
  assert(msgPrompt.includes('MORTAL QUERY: "Who walks here?"'), 'T09.2: message prompt formatted correctly');

  // Test 3: Disturbance prompt format includes prior message context
  const distPrompt = qwen.formatPrompt({
    type: 'disturbance',
    code: 'CHECKSUM_FAILED',
    reason: 'CRC_MISMATCH',
  });
  assert(distPrompt.includes('<AETHER_DISTURBED>'), 'T09.3a: contains AETHER_DISTURBED tag');
  assert(distPrompt.includes('CHECKSUM_FAILED'), 'T09.3b: contains code');
  assert(distPrompt.includes('CRC_MISMATCH'), 'T09.3c: contains reason');
  assert(distPrompt.includes('Spirit, what is your name?'), 'T09.3d: contains prior valid question context');

  // Test 4: Offline fallback response (when Ollama is offline)
  const res = await qwen.generateResponse({ type: 'message', text: 'Speak to me' });
  assert(res.offline === true, 'T09.4a: detects offline/fallback mode');
  assert(typeof res.text === 'string' && res.text.length > 0, 'T09.4b: produces non-empty fallback text');

  // Test 5: Disturbance cooldown / coalescing (5000ms per PROTOCOL.md)
  const distRes1 = await qwen.generateResponse({ type: 'disturbance', code: 'CHECKSUM_FAILED', reason: 'CRC_MISMATCH' });
  assert(distRes1.text === 'THE LIVING DISRUPT US. I AM TRAPPED.', 'T09.5a: disturbance returns distressed response');

  const distRes2 = await qwen.generateResponse({ type: 'disturbance', code: 'INCOMPLETE_PACKET', reason: 'INDEX_GAP' });
  assert(distRes2.coalesced === true, 'T09.5b: second disturbance within 5s was throttled/coalesced');
}

// =========================================================================
// T10: Audio Synthesis & Bounded Queue Tests
// =========================================================================
{
  const audio = new AudioEngine({ maxQueueSize: 1 });

  // Test 6: Offline PCM RIFF .wav generation
  const synthRes = await audio.synthesize('I AM TRAPPED IN THE VEIL', { disturbed: true });
  assert(synthRes.success === true, 'T10.6a: synthesis completed successfully');
  assert(synthRes.audioFile === '/audio/spirit_voice.wav', 'T10.6b: audio path returned');

  // Verify file was written to disk and has valid RIFF header
  const wavPath = path.resolve(__dirname, '../public/audio/spirit_voice.wav');
  assert(fs.existsSync(wavPath), 'T10.6c: WAV file exists on disk');
  const wavHeader = fs.readFileSync(wavPath).subarray(0, 12).toString('ascii');
  assert(wavHeader.startsWith('RIFF') && wavHeader.endsWith('WAVE'), 'T10.6d: valid RIFF WAVE header verified');

  // Test 7: Bounded audio queue prevents overflow
  audio.isProcessing = true; // simulate busy worker
  audio.queue.push({ text: 'pending 1' }); // fill the 1-item queue

  const droppedRes = await audio.synthesize('pending 2');
  assert(droppedRes.queueDropped === true, 'T10.7a: 2nd pending request was dropped to enforce bounded queue');
  assert(droppedRes.error.includes('AUDIO_QUEUE_OVERFLOW'), 'T10.7b: honest queue overflow error returned');
  audio.isProcessing = false;
  audio.queue = [];
}

// =========================================================================
// T11: Separation of Input vs. Output & Offline Assets
// =========================================================================
{
  // Test 8: Verify offline assets integrity in public/
  const htmlPath = path.resolve(__dirname, '../public/index.html');
  const htmlContent = fs.readFileSync(htmlPath, 'utf8');
  assert(!htmlContent.includes('http://') && !htmlContent.includes('https://'), 'T11.8: zero external CDN links in index.html (100% offline)');

  // Test 9: Verify artifacts provenance configuration
  const artifactsPath = path.resolve(__dirname, '../artifacts.json');
  const artifactsData = JSON.parse(fs.readFileSync(artifactsPath, 'utf8'));
  assert(artifactsData.status === 'configured', 'T11.9a: artifacts status configured');
  assert(artifactsData.artifacts.length >= 2, 'T11.9b: Qwen and Piper model provenance registered');
  const qwenArtifact = artifactsData.artifacts.find(a => a.id.includes('qwen'));
  assert(qwenArtifact && qwenArtifact.license === 'Apache-2.0', 'T11.9c: Qwen license declared');
}

console.log(`\nPASS: ${passed}/${total} assertions passed cleanly.`);
