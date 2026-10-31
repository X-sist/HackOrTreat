/* ==========================================================================
   BEYOND THE GRAVE — SPIRIT PLANE CLIENT (app.js)
   Handles Planchette movement, SSE telemetry, and Aether Disturbance effects
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
const serialStatusText = document.getElementById('serialStatusText');
const aetherStatusText = document.getElementById('aetherStatusText');

// Target positions cache
const targetElements = new Map();
let isSpelling = false;
let spellingQueue = [];

// Initialize Board Elements
function initBoard() {
  // Build top arc (A-M)
  arcTop.innerHTML = '';
  LETTERS_TOP.forEach(char => {
    const el = document.createElement('span');
    el.className = 'board-letter';
    el.textContent = char;
    el.id = `char-${char}`;
    arcTop.appendChild(el);
    targetElements.set(char, el);
  });

  // Build bottom arc (N-Z)
  arcBottom.innerHTML = '';
  LETTERS_BOTTOM.forEach(char => {
    const el = document.createElement('span');
    el.className = 'board-letter';
    el.textContent = char;
    el.id = `char-${char}`;
    arcBottom.appendChild(el);
    targetElements.set(char, el);
  });

  // Build numbers (1-0)
  numbersRow.innerHTML = '';
  NUMBERS.forEach(num => {
    const el = document.createElement('span');
    el.className = 'board-num';
    el.textContent = num;
    el.id = `char-${num}`;
    numbersRow.appendChild(el);
    targetElements.set(num, el);
  });

  // Special targets
  targetElements.set('YES', document.getElementById('target-YES'));
  targetElements.set('NO', document.getElementById('target-NO'));
  targetElements.set('GOODBYE', document.getElementById('target-GOODBYE'));

  // Initial center position
  setTimeout(resetPlanchette, 200);
}

// Move Planchette lens directly over a DOM target
function movePlanchetteToElement(targetEl) {
  if (!targetEl || !ouijaBoard || !planchette) return;

  const boardRect = ouijaBoard.getBoundingClientRect();
  const targetRect = targetEl.getBoundingClientRect();

  // Target center relative to board
  const targetCenterX = (targetRect.left + targetRect.width / 2) - boardRect.left;
  const targetCenterY = (targetRect.top + targetRect.height / 2) - boardRect.top;

  // Planchette lens center offset (lens is centered horizontally, ~35px down in 110px body)
  const lensOffsetX = 45; // 90px width / 2
  const lensOffsetY = 38;

  const targetX = targetCenterX - lensOffsetX;
  const targetY = targetCenterY - lensOffsetY;

  // Slight spooky tilt variation (-4 to +4 deg)
  const randomTilt = (Math.random() * 8 - 4).toFixed(1);

  planchette.style.transform = `translate(${targetX}px, ${targetY}px) rotate(${randomTilt}deg)`;
}

// Center resting position
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

// Theatrical planchette spelling routine
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
      await new Promise(r => setTimeout(r, 450));
      continue;
    }

    const targetEl = targetElements.get(char);
    if (targetEl) {
      currentLetterDisplay.textContent = `Pointing to: "${char}"`;
      movePlanchetteToElement(targetEl);
      targetEl.classList.add('active');

      // Theatrical hover delay for audience reading
      await new Promise(r => setTimeout(r, 680));
    }
  }

  clearLetterHighlights();
  currentLetterDisplay.textContent = 'Prophecy Complete';
  await new Promise(r => setTimeout(r, 1000));
  resetPlanchette();

  isSpelling = false;
  if (spellingQueue.length > 0) {
    const nextText = spellingQueue.shift();
    spellText(nextText);
  }
}

// Add formatted entry to transcription log
function logMessage(text, type = 'system') {
  const entry = document.createElement('div');
  entry.className = `log-entry ${type}`;
  const timestamp = new Date().toLocaleTimeString();
  entry.textContent = `[${timestamp}] ${text}`;
  spiritLog.appendChild(entry);
  spiritLog.scrollTop = spiritLog.scrollHeight;
}

// Handle Aether Disturbance (IR Beam Broken)
function triggerDisturbanceVisuals() {
  glitchOverlay.classList.add('disturbed');
  disturbanceBanner.classList.add('active');
  aetherStatusText.textContent = 'Aether: DISTURBED';
  const aetherPill = document.getElementById('aetherPill');
  const dot = aetherPill.querySelector('.indicator-dot');
  dot.className = 'indicator-dot dot-red';

  // Play a brief synthesized audio glitch using Web Audio API
  playSpookyDisturbanceTone();

  logMessage('ALERT: Optical IR beam broken! Trapped spirit agitated!', 'disturbed');

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

// Offline spooky low-frequency disturbance synthesizer
function playSpookyDisturbanceTone() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(65, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(35, ctx.currentTime + 0.8);

    gain.gain.setValueAtTime(0.35, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.8);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start();
    osc.stop(ctx.currentTime + 0.8);
  } catch (e) {
    // AudioContext blocked until user interaction
  }
}

// Simulation trigger for testing without hardware
async function triggerSimulation(promptText, disturbed = false) {
  logMessage(`[SIMULATE] Laptop 1 Input: "${promptText}" (Disturbed: ${disturbed})`, 'incoming');

  try {
    const res = await fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: promptText, disturbed }),
    });
    const data = await res.json();
    console.log('Simulate response:', data);
  } catch (err) {
    logMessage(`Simulation error: ${err.message}`, 'disturbed');
  }
}

// Server-Sent Events (SSE) Listener
function connectSSE() {
  const eventSource = new EventSource('/events');

  eventSource.addEventListener('connected', (e) => {
    const data = JSON.parse(e.data);
    logMessage(`[SSE] Linked to Spirit Plane Server. Serial status: ${data.serialStatus}`, 'system');
  });

  eventSource.addEventListener('raw_serial', (e) => {
    const { data } = JSON.parse(e.data);
    logMessage(`[IR-RX] Packet: "${data.raw}"`, data.isDisturbed ? 'disturbed' : 'incoming');
  });

  eventSource.addEventListener('aether_disturbed', (e) => {
    triggerDisturbanceVisuals();
  });

  eventSource.addEventListener('spirit_response', (e) => {
    const { data } = JSON.parse(e.data);
    logMessage(`[SPIRIT REVELATION] ${data.response}`, 'spirit');
    if (data.offlineNotice) {
      logMessage(`[NOTICE] ${data.offlineNotice}`, 'system');
    }
    spellText(data.response);
  });

  eventSource.addEventListener('hardware_status', (e) => {
    const { data } = JSON.parse(e.data);
    if (data.serial === 'connected') {
      serialStatusText.textContent = `Arduino: ${data.port}`;
      document.querySelector('#serialPill .indicator-dot').className = 'indicator-dot dot-green';
    } else {
      serialStatusText.textContent = `Arduino: Simulation`;
      document.querySelector('#serialPill .indicator-dot').className = 'indicator-dot dot-yellow';
    }
  });

  eventSource.onerror = () => {
    // Reconnection is automatic in SSE
  };
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
  initBoard();
  connectSSE();
});

window.addEventListener('resize', () => {
  if (!isSpelling) {
    resetPlanchette();
  }
});

// Expose globals for simulation buttons
window.triggerSimulation = triggerSimulation;
window.resetPlanchette = resetPlanchette;
