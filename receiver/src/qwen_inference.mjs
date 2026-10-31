/**
 * QwenInference: Offline Qwen 2.5 1.5B/3B LLM router for HackOrTreat CS2 (T09).
 * Implements PROTOCOL.md v1 rules:
 * - Cap/coalesce automatic disturbance-triggered requests to max 1 outstanding and at most one trigger per 5s.
 * - Formats validated message text and disturbance context (code, reason, prior valid question).
 * - Queries local offline Ollama API with graceful atmospheric fallback if offline.
 */

import { CONTRACT } from '../../shared/generated/protocol.mjs';

export const DISTURBANCE_COOLDOWN_MS = CONTRACT.constants.DISTURBANCE_COOLDOWN_MS; // 5000 ms

export const SPIRIT_SYSTEM_PROMPT = `You are a spirit summoned through an antique Ouija board in an offline room.
Wi-Fi is severed. Communication arrives through an invisible optical infrared beam.
If the message contains corrupted text or disturbance details (<AETHER_DISTURBED>),
the receiver reported a damaged or incomplete transmission. React in character, but do not claim a physical cause or invent the lost question.
Otherwise, respond to mortal inquiries with brief, eerie, archaic prophecy.
CRITICAL CONSTRAINT: Keep your response short (10 to 18 words maximum) so the physical planchette can spell it letter by letter without stalling.`;

export class QwenInference {
  constructor(options = {}) {
    this.host = options.host || process.env.OLLAMA_HOST || 'http://127.0.0.1:11434';
    this.model = options.model || process.env.OLLAMA_MODEL || 'qwen2.5:1.5b';
    this.timeoutMs = options.timeoutMs || Number(process.env.QWEN_TIMEOUT_MS || 8000);

    this.lastValidText = null;
    this.lastDisturbanceTimestamp = 0;
    this.isGenerating = false;
  }

  /**
   * Records the last successfully verified message text.
   * @param {string} text
   */
  recordValidMessage(text) {
    if (typeof text === 'string' && text.trim().length > 0) {
      this.lastValidText = text.trim();
    }
  }

  /**
   * Formats the user prompt according to event type and context.
   * @param {Object} params
   * @param {'message'|'disturbance'} params.type
   * @param {string} [params.text]
   * @param {string} [params.code]
   * @param {string} [params.reason]
   * @returns {string}
   */
  formatPrompt({ type, text, code, reason }) {
    if (type === 'disturbance') {
      const prior = this.lastValidText ? `"${this.lastValidText}"` : 'Unknown';
      return `<AETHER_DISTURBED> Damaged or incomplete transmission. Disruption Code: ${code || 'CHECKSUM_FAILED'}, Reason: ${reason || 'CRC_MISMATCH'}. Prior mortal query was ${prior}. React to this disruption!`;
    }
    return `MORTAL QUERY: "${text || ''}"`;
  }

  /**
   * Query local Qwen model with cooldown and bounded concurrency.
   * @param {Object} params
   * @returns {Promise<{ text: string, offline: boolean, coalesced?: boolean }>}
   */
  async generateResponse(params) {
    const { type, text, code, reason } = params;

    // PROTOCOL.md rule: Coalesce disturbance requests within 5000ms
    if (type === 'disturbance') {
      const now = Date.now();
      const elapsed = now - this.lastDisturbanceTimestamp;
      if (elapsed < DISTURBANCE_COOLDOWN_MS) {
        return {
          text: 'THE LIVING DISRUPT US. I AM TRAPPED.',
          offline: true,
          coalesced: true,
          reason: `Disturbance request throttled (last disturbance ${elapsed}ms ago; cooldown is ${DISTURBANCE_COOLDOWN_MS}ms).`,
        };
      }
      this.lastDisturbanceTimestamp = now;
    }

    // PROTOCOL.md rule: Cap to 1 outstanding request
    if (this.isGenerating) {
      return {
        text: type === 'disturbance' ? 'THE BEAM IS BROKEN.' : 'THE SPIRIT SPEAKS ALREADY.',
        offline: true,
        coalesced: true,
        reason: 'Concurrent request dropped; spirit inference already in progress.',
      };
    }

    this.isGenerating = true;
    const prompt = this.formatPrompt(params);

    let timeoutId;
    try {
      const controller = new AbortController();
      timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

      const res = await fetch(`${this.host}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: this.model,
          prompt,
          system: SPIRIT_SYSTEM_PROMPT,
          stream: false,
        }),
        signal: controller.signal,
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }

      const data = await res.json();
      const cleanResponse = (data.response || '').trim();

      if (!cleanResponse) {
        throw new Error('Empty response from model');
      }

      return {
        text: cleanResponse,
        offline: false,
      };
    } catch (err) {
      // Deterministic atmospheric fallback when Ollama is offline or not started
      const fallbackText = type === 'disturbance'
        ? 'THE LIVING DISRUPT US. I AM TRAPPED.'
        : 'THE VEIL IS THIN. I HEAR THEE.';

      return {
        text: fallbackText,
        offline: true,
        error: err.message,
      };
    } finally {
      clearTimeout(timeoutId);
      this.isGenerating = false;
    }
  }
}
