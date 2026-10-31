// Shared boundary validator. No serial, audio, filesystem or model access.
import { CONTRACT } from '../generated/protocol.mjs';
const c = CONTRACT.constants;
export function validateEvent(value, role) {
  const fail = () => { throw new Error('Invalid HackOrTreat event'); };
  if (!['tx', 'rx'].includes(role) || value === null || typeof value !== 'object' || Array.isArray(value)) fail();
  if (!Number.isInteger(value.v) || value.v !== c.PROTOCOL_VERSION) fail();
  if (typeof value.event !== 'string') fail();
  const spec = Object.hasOwn(CONTRACT.event_fields, value.event) ? CONTRACT.event_fields[value.event] : undefined;
  if (!spec || !spec.roles.includes(role)) fail();
  const fields = ['v', 'event', ...spec.required];
  if (Object.keys(value).length !== fields.length || !fields.every(key => Object.hasOwn(value, key))) fail();
  if (Buffer.byteLength(JSON.stringify(value), 'utf8') > c.MAX_EVENT_LINE_BYTES) fail();
  if (value.event === 'hello') {
    if (value.role !== role || value.max_text_bytes !== c.MAX_TEXT_BYTES) fail();
  } else if (value.event === 'disturbance') {
    if (typeof value.code !== 'string' || typeof value.reason !== 'string') fail();
    const reasons = Object.hasOwn(CONTRACT.disturbance_reasons, value.code) ? CONTRACT.disturbance_reasons[value.code] : undefined;
    if (!reasons || !reasons.includes(value.reason) || value.session !== null || value.seq !== null) fail();
  } else if (['accepted', 'sent', 'message', 'duplicate'].includes(value.event)) {
    if (typeof value.session !== 'string' || !/^[0-9A-F]{8}$/.test(value.session)) fail();
    if (!Number.isInteger(value.seq) || value.seq < 0 || value.seq > 65535) fail();
    if (value.event === 'message') {
      if (typeof value.payload_hex !== 'string' || !/^(?:[0-9A-F]{2})+$/.test(value.payload_hex)) fail();
      const bytes = Buffer.from(value.payload_hex, 'hex');
      if (bytes.length > c.MAX_TEXT_BYTES || !bytes.every(byte => byte >= 32 && byte <= 126) || !bytes.some(byte => byte !== 32)) fail();
    }
  } else if (['error', 'protocol_error'].includes(value.event)) {
    if (!(value.event === 'error' ? CONTRACT.error_codes : CONTRACT.protocol_error_codes).includes(value.code)) fail();
  }
  return value;
}
