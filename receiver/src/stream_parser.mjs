/**
 * StreamParser: Bounded serial stream parser and contract event validator for HackOrTreat Receiver.
 * Implements PROTOCOL.md v1 host-board NDJSON parser rules:
 * - 115200 baud, 8N1, LF-terminated (optional preceding CR accepted).
 * - Bounded reads: discards lines exceeding MAX_EVENT_LINE_BYTES (256 bytes) until next LF.
 * - Never executes a truncated prefix.
 * - Validates parsed objects with shared/js/contract.mjs validateEvent(obj, 'rx').
 * - Decodes message payload_hex into verified printable ASCII plain text.
 */

import { validateEvent } from '../../shared/js/contract.mjs';
import { CONTRACT } from '../../shared/generated/protocol.mjs';

export const MAX_EVENT_LINE_BYTES = CONTRACT.constants.MAX_EVENT_LINE_BYTES; // 256
export const MAX_TEXT_BYTES = CONTRACT.constants.MAX_TEXT_BYTES; // 48

export class StreamParser {
  /**
   * @param {Object} options
   * @param {Function} [options.onMessage] - Callback for validated text message ({ session, seq, text, raw })
   * @param {Function} [options.onDisturbance] - Callback for disturbance ({ code, reason, raw })
   * @param {Function} [options.onDuplicate] - Callback for duplicate event ({ session, seq, raw })
   * @param {Function} [options.onHello] - Callback for board hello ({ role, maxTextBytes, raw })
   * @param {Function} [options.onProtocolError] - Callback for protocol error ({ code, raw })
   * @param {Function} [options.onError] - Callback for board error ({ code, raw })
   * @param {Function} [options.onStreamError] - Callback for stream parser errors ({ type, line, error })
   */
  constructor(options = {}) {
    this.options = options;
    this.buffer = '';
    this.isDiscarding = false;
  }

  /**
   * Ingest a chunk of incoming serial data (string or Buffer).
   * @param {string|Buffer} chunk
   */
  push(chunk) {
    const text = typeof chunk === 'string' ? chunk : chunk.toString('utf8');
    this.buffer += text;

    let newlineIndex;
    while ((newlineIndex = this.buffer.indexOf('\n')) !== -1) {
      const lineSegment = this.buffer.slice(0, newlineIndex);
      this.buffer = this.buffer.slice(newlineIndex + 1);

      if (this.isDiscarding) {
        // Discarded until next LF after overflow
        this.isDiscarding = false;
        continue;
      }

      // Check byte length of line
      const byteLength = Buffer.byteLength(lineSegment, 'utf8');
      if (byteLength > MAX_EVENT_LINE_BYTES) {
        this._emitStreamError('LINE_TOO_LONG', lineSegment, new Error(`Line length ${byteLength} exceeds limit ${MAX_EVENT_LINE_BYTES}`));
        continue;
      }

      // Strip optional trailing \r
      const cleanLine = lineSegment.endsWith('\r') ? lineSegment.slice(0, -1) : lineSegment;
      const trimmed = cleanLine.trim();

      // Blank lines are ignored per PROTOCOL.md
      if (!trimmed) {
        continue;
      }

      this._parseLine(cleanLine);
    }

    // Check if remaining buffer exceeds limit without seeing newline
    const remainingBytes = Buffer.byteLength(this.buffer, 'utf8');
    if (remainingBytes > MAX_EVENT_LINE_BYTES) {
      this.isDiscarding = true;
      const discardedPrefix = this.buffer;
      this.buffer = '';
      this._emitStreamError('LINE_TOO_LONG', discardedPrefix, new Error(`Buffer exceeded ${MAX_EVENT_LINE_BYTES} bytes without LF; discarding`));
    }
  }

  /**
   * Reset parser internal buffer state.
   */
  reset() {
    this.buffer = '';
    this.isDiscarding = false;
  }

  /**
   * Flush any remaining content (useful on stream end).
   */
  flush() {
    if (this.buffer.trim().length > 0 && !this.isDiscarding) {
      // Incomplete trailing data without LF is discarded
      this._emitStreamError('INCOMPLETE_LINE', this.buffer, new Error('Trailing data without trailing LF at stream end'));
    }
    this.reset();
  }

  /**
   * Process a single complete line.
   * @private
   */
  _parseLine(line) {
    let parsed;
    try {
      parsed = JSON.parse(line);
    } catch (err) {
      this._emitStreamError('MALFORMED_JSON', line, err);
      return;
    }

    // Validate event using shared contract
    let validated;
    try {
      validated = validateEvent(parsed, 'rx');
    } catch (err) {
      this._emitStreamError('CONTRACT_VALIDATION_FAILED', line, err);
      return;
    }

    // Dispatch according to validated event schema
    switch (validated.event) {
      case 'message': {
        const text = decodePayloadHex(validated.payload_hex);
        if (this.options.onMessage) {
          this.options.onMessage({
            session: validated.session,
            seq: validated.seq,
            text,
            raw: validated,
          });
        }
        break;
      }

      case 'disturbance': {
        if (this.options.onDisturbance) {
          this.options.onDisturbance({
            code: validated.code,
            reason: validated.reason,
            session: validated.session,
            seq: validated.seq,
            raw: validated,
          });
        }
        break;
      }

      case 'duplicate': {
        if (this.options.onDuplicate) {
          this.options.onDuplicate({
            session: validated.session,
            seq: validated.seq,
            raw: validated,
          });
        }
        break;
      }

      case 'hello': {
        if (this.options.onHello) {
          this.options.onHello({
            role: validated.role,
            maxTextBytes: validated.max_text_bytes,
            raw: validated,
          });
        }
        break;
      }

      case 'protocol_error': {
        if (this.options.onProtocolError) {
          this.options.onProtocolError({
            code: validated.code,
            raw: validated,
          });
        }
        break;
      }

      case 'error': {
        if (this.options.onError) {
          this.options.onError({
            code: validated.code,
            raw: validated,
          });
        }
        break;
      }

      default: {
        this._emitStreamError('UNHANDLED_EVENT', line, new Error(`Unhandled event type: ${validated.event}`));
      }
    }
  }

  /**
   * @private
   */
  _emitStreamError(type, line, error) {
    if (this.options.onStreamError) {
      this.options.onStreamError({ type, line, error });
    }
  }
}

/**
 * Decodes uppercase hex payload into verified ASCII string.
 * @param {string} hex
 * @returns {string}
 */
export function decodePayloadHex(hex) {
  const bytes = Buffer.from(hex, 'hex');
  const text = bytes.toString('ascii');
  return text;
}
