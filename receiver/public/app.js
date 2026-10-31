/* ==========================================================================
   HACKORTREAT — RECEIVER CLIENT (app.js) [T11 Full Integration]
   Renders Ouija board, animates planchette, plays offline audio,
   and separates input question vs. spirit response with readable transport errors.
   ========================================================================== */

const LETTERS_TOP = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M'];
const LETTERS_BOTTOM = ['N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'];
const NUMBERS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'];

// DOM elements
const ouijaBoard = document.getElementById('ouijaBoard');
const planchette = document.getElementById('planchette');
const arcTop = document.getElementById('arcTop');
const arcBottom = document.getElementById('arcBottom');
const numbersRow = document.getElementById('numbersRow');
const spiritLog = document.getElementById('spiritLog');
const currentLetterDisplay = document.getElementById('currentLetterDisplay');
const glitchOverlay = document.getElementById('glitchOverlay');
const disturbanceBanner = document.getElementById('disturbanceBanner');
const disturbanceCodeText = document.getElementById('disturbanceCodeText');
const disturbanceReasonText = document.getElementById('disturbanceReasonText');
const serialStatusText = document.getElementById('serialStatusText');
const aetherStatusText = document.getElementById('aetherStatusText');

const targetElements = new Map();
let isSpelling = false;
let spellingQueue = [];
let audioContext = null;
let voiceSource = null;

function initBoard() {
  arcTop.innerHTML = '';
  LETTERS_TOP.forEach(char => {
    const el = document.createElement('span');
    el.className = 'board-letter';
    el.textContent = char;
    el.id = `char-${char}`;
    arcTop.appendChild(el);
    targetElements.set(char, el);
  });

  arcBottom.innerHTML = '';
  LETTERS_BOTTOM.forEach(char => {
    const el = document.createElement('span');
    el.className = 'board-letter';
    el.textContent = char;
    el.id = `char-${char}`;
    arcBottom.appendChild(el);
    targetElements.set(char, el);
  });

  numbersRow.innerHTML = '';
  NUMBERS.forEach(num => {
    const el = document.createElement('span');
    el.className = 'board-num';
    el.textContent = num;
    el.id = `char-${num}`;
    numbersRow.appendChild(el);
    targetElements.set(num, el);
  });

  targetElements.set('YES', document.getElementById('target-YES'));
  targetElements.set('NO', document.getElementById('target-NO'));
  targetElements.set('GOODBYE', document.getElementById('target-GOODBYE'));

  setTimeout(resetPlanchette, 200);
}

function movePlanchetteToElement(targetEl) {
  if (!targetEl || !ouijaBoard || !planchette) return;

  const boardRect = ouijaBoard.getBoundingClientRect();
  const targetRect = targetEl.getBoundingClientRect();

  const targetCenterX = (targetRect.left + targetRect.width / 2) - boardRect.left;
  const targetCenterY = (targetRect.top + targetRect.height / 2) - boardRect.top;

  const lensOffsetX = 45;
  const lensOffsetY = 38;

  const targetX = targetCenterX - lensOffsetX;
  const targetY = targetCenterY - lensOffsetY;

  const randomTilt = (Math.random() * 8 - 4).toFixed(1);
  planchette.style.transform = `translate(${targetX}px, ${targetY}px) rotate(${randomTilt}deg)`;
}

function resetPlanchette() {
  if (!ouijaBoard || !planchette) return;
  const boardRect = ouijaBoard.getBoundingClientRect();
  const centerX = (boardRect.width / 2) - 45;
  const centerY = (boardRect.height / 2) - 30;
  planchette.style.transform = `translate(${centerX}px, ${centerY}px) rotate(0deg)`;
  currentLetterDisplay.textContent = 'Planchette Resting';
  clearLetterHighlights();
}

function clearLetterHighlights() {
  document.querySelectorAll('.board-letter, .board-num, .oracle-opt, .goodbye-container')
    .forEach(el => el.classList.remove('active', 'highlight'));
}

async function spellText(text) {
  if (isSpelling) {
    spellingQueue.push(text);
    return;
  }

  isSpelling = true;
  const clean = text.toUpperCase().replace(/[^A-Z0-9\s]/g, '');
  const tokens = clean.split('');

  logMessage(`[SPIRIT SPELLS] "${clean}"`, 'spirit');

  for (let i = 0; i < tokens.length; i++) {
    const char = tokens[i];
    clearLetterHighlights();

    if (char === ' ') {
      currentLetterDisplay.textContent = '— [Space] —';
      await new Promise(r => setTimeout(r, 380));
      continue;
    }

    const targetEl = targetElements.get(char);
    if (targetEl) {
      currentLetterDisplay.textContent = `Pointing to: "${char}"`;
      movePlanchetteToElement(targetEl);
      targetEl.classList.add('active');
      await new Promise(r => setTimeout(r, 620));
    }
  }

  clearLetterHighlights();
  currentLetterDisplay.textContent = 'Spelling Complete';
  await new Promise(r => setTimeout(r, 1000));
  resetPlanchette();

  isSpelling = false;
  if (spellingQueue.length > 0) {
    const nextText = spellingQueue.shift();
    spellText(nextText);
  }
}

function logMessage(text, type = 'system') {
  const entry = document.createElement('div');
  entry.className = `log-entry ${type}`;
  const timestamp = new Date().toLocaleTimeString();
  entry.textContent = `[${timestamp}] ${text}`;
  spiritLog.appendChild(entry);
  spiritLog.scrollTop = spiritLog.scrollHeight;
}

function triggerDisturbanceVisuals(code, reason) {
  glitchOverlay.classList.add('disturbed');
  disturbanceBanner.classList.add('active');
  disturbanceCodeText.textContent = `${code}: ${reason}`;
  disturbanceReasonText.textContent = `The receiver reported a damaged or incomplete transmission.`;

  aetherStatusText.textContent = 'Aether: DISTURBED';
  const aetherPill = document.getElementById('aetherPill');
  const dot = aetherPill.querySelector('.indicator-dot');
  dot.className = 'indicator-dot dot-red';

  playDisturbanceTone();
  logMessage(`[TRANSPORT ERROR] ${code} (${reason}) — Transmission disturbed!`, 'disturbed');

  setTimeout(() => {
    glitchOverlay.classList.remove('disturbed');
  }, 1200);

  setTimeout(() => {
    disturbanceBanner.classList.remove('active');
    aetherStatusText.textContent = 'Aether: Re-stabilizing';
    dot.className = 'indicator-dot dot-yellow';
    setTimeout(() => {
      aetherStatusText.textContent = 'Aether: Stable';
      dot.className = 'indicator-dot dot-green';
    }, 3000);
  }, 4000);
}

function playDisturbanceTone() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(70, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(32, ctx.currentTime + 0.8);

    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.8);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start();
    osc.stop(ctx.currentTime + 0.8);
  } catch {}
}

async function enableSound() {
  try {
    audioContext ||= new (window.AudioContext || window.webkitAudioContext)();
    await audioContext.resume();
    document.getElementById('enableSound').textContent = 'Sound enabled';
    logMessage('Sound enabled. Keep speakers on for the spirit response.', 'system');
  } catch (error) { logMessage(`Sound error: ${error.message}`, 'disturbed'); }
}

async function playAudioFile(url) {
  if (!url) return;
  if (!audioContext || audioContext.state !== 'running') {
    logMessage('Click Enable sound before sending the next question.', 'system');
    return;
  }
  try {
    const response = await fetch(url + '?t=' + Date.now());
    if (!response.ok) throw new Error('Speech audio could not be loaded.');
    const buffer = await audioContext.decodeAudioData(await response.arrayBuffer());
    voiceSource?.stop();
    voiceSource = audioContext.createBufferSource();
    voiceSource.buffer = buffer;
    voiceSource.connect(audioContext.destination);
    voiceSource.start();
  } catch (error) { logMessage(`Speech playback error: ${error.message}`, 'disturbed'); }
}

async function triggerSimulate(type, text = '') {
  try {
    const res = await fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type, text }),
    });
    await res.json();
  } catch (err) {
    logMessage(`Simulation error: ${err.message}`, 'disturbed');
  }
}

function connectSSE() {
  const eventSource = new EventSource('/events');

  eventSource.addEventListener('connected', () => {
    logMessage('[SSE] Linked to Receiver Stream Server.', 'system');
  });

  eventSource.onerror = () => {
    serialStatusText.textContent = 'Receiver connection unavailable';
    document.querySelector('#serialPill .indicator-dot').className = 'indicator-dot dot-red';
  };

  eventSource.addEventListener('service_error', e => {
    const data = JSON.parse(e.data);
    logMessage(`${data.source} error: ${data.message}`, 'disturbed');
    currentLetterDisplay.textContent = 'Response unavailable: check receiver terminal';
  });
  eventSource.addEventListener('service_notice', e => {
    logMessage(JSON.parse(e.data).message, 'system');
  });

  eventSource.addEventListener('hello', (e) => {
    const data = JSON.parse(e.data);
    serialStatusText.textContent = `Rx Board: Online (${data.role})`;
    document.querySelector('#serialPill .indicator-dot').className = 'indicator-dot dot-green';
    logMessage(`[HELLO] Board boot recognized. Max text: ${data.maxTextBytes} bytes.`, 'system');
  });

  // T11: Strict separation of Input Status vs. Spirit Response
  eventSource.addEventListener('input_received', (e) => {
    const data = JSON.parse(e.data);
    logMessage(`[INPUT FROM LIVING] session=${data.session} seq=${data.seq}: "${data.text}"`, 'incoming');
    currentLetterDisplay.textContent = 'Mortal speaks... summoning spirit';
  });

  eventSource.addEventListener('spirit_thinking', (e) => {
    const data = JSON.parse(e.data);
    logMessage(`[ORACLE] Channeling through local Qwen LLM (${data.stage})...`, 'system');
  });

  eventSource.addEventListener('spirit_response', (e) => {
    const data = JSON.parse(e.data);
    logMessage(`[SPIRIT REVELATION] "${data.responseText}"`, 'spirit');
    if (data.offlineNotice) {
      logMessage(`[NOTE] ${data.offlineNotice}`, 'system');
    }
    if (data.audioNotice) logMessage(data.audioNotice, 'system');
    // Play voice audio
    if (data.audioFile) {
      playAudioFile(data.audioFile);
    }
    // Animate planchette
    spellText(data.responseText);
  });

  eventSource.addEventListener('disturbance', (e) => {
    const data = JSON.parse(e.data);
    triggerDisturbanceVisuals(data.code, data.reason);
  });

  eventSource.addEventListener('duplicate', (e) => {
    const data = JSON.parse(e.data);
    logMessage(`[DUPLICATE DROP] session=${data.session} seq=${data.seq} ignored (deduplicated)`, 'duplicate');
  });

  eventSource.addEventListener('protocol_error', (e) => {
    const data = JSON.parse(e.data);
    logMessage(`[PROTOCOL ERROR] code=${data.code}`, 'disturbed');
  });

  eventSource.addEventListener('stream_error', (e) => {
    const data = JSON.parse(e.data);
    logMessage(`[STREAM ERROR] ${data.type}: ${data.error}`, 'disturbed');
  });
}

window.addEventListener('DOMContentLoaded', () => {
  initBoard();
  document.getElementById('enableSound').addEventListener('click', enableSound);
  fetch('/api/status').then(r => r.json()).then(status => {
    if (status.demoMode) document.querySelector('.simulation-controls').style.display = 'none';
  }).catch(() => {});
  connectSSE();
});

window.addEventListener('resize', () => {
  if (!isSpelling) {
    resetPlanchette();
  }
});

window.triggerSimulate = triggerSimulate;
window.resetPlanchette = resetPlanchette;
