import fs from 'node:fs';
import { validateEvent } from '../shared/js/contract.mjs';
const fixtures = JSON.parse(fs.readFileSync(new URL('../shared/fixtures/events.json', import.meta.url), 'utf8'));
for (const test of fixtures) {
  let accepted = false;
  try { validateEvent(test.value, test.role); accepted = true; } catch {}
  if (accepted !== test.valid) throw new Error(`JS event fixture disagreement: ${test.id}`);
}
console.log(`PASS: JavaScript agrees on ${fixtures.length} shared valid/invalid event fixtures`);
