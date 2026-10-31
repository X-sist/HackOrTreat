#!/usr/bin/env node
/**
 * HackOrTreat Receiver CLI — Plain-text stream parser and inspector.
 * Supports:
 *   node src/cli.mjs --stdin
 *   node src/cli.mjs --replay <file.ndjson>
 *   node src/cli.mjs --fixtures
 *   node src/cli.mjs --simulate
 */

import fs from 'node:fs';
import readline from 'node:readline';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { StreamParser } from './stream_parser.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, '../../');

function printBanner() {
  console.log('=====================================================');
  console.log('  HACKORTREAT RECEIVER — THE SPIRIT PLANE (CS2)      ');
  console.log('  Contract: Revision 1.0.0 (v1 NDJSON)               ');
  console.log('=====================================================');
}

function createFormattedParser() {
  return new StreamParser({
    onMessage: ({ session, seq, text }) => {
      const ts = new Date().toLocaleTimeString();
      console.log(`[${ts}] [MESSAGE] session=${session} seq=${seq}`);
      console.log(`  => PLAIN TEXT: "${text}"`);
    },
    onDisturbance: ({ code, reason }) => {
      const ts = new Date().toLocaleTimeString();
      console.log(`[${ts}] [DISTURBANCE] \x1b[31m${code}: ${reason}\x1b[0m (Optical beam broken!)`);
    },
    onDuplicate: ({ session, seq }) => {
      const ts = new Date().toLocaleTimeString();
      console.log(`[${ts}] [DUPLICATE] session=${session} seq=${seq} (dropped per deduplication policy)`);
    },
    onHello: ({ role, maxTextBytes }) => {
      const ts = new Date().toLocaleTimeString();
      console.log(`[${ts}] [HELLO] Board connection established (role=${role}, max_text_bytes=${maxTextBytes})`);
    },
    onProtocolError: ({ code }) => {
      const ts = new Date().toLocaleTimeString();
      console.log(`[${ts}] [PROTOCOL_ERROR] code=${code}`);
    },
    onError: ({ code }) => {
      const ts = new Date().toLocaleTimeString();
      console.log(`[${ts}] [BOARD_ERROR] code=${code}`);
    },
    onStreamError: ({ type, line, error }) => {
      const ts = new Date().toLocaleTimeString();
      console.error(`[${ts}] [STREAM_ERROR] type=${type}: ${error.message}`);
    },
  });
}

async function runStdin() {
  printBanner();
  console.log('Listening on STDIN for NDJSON events (Ctrl+C to stop)...');
  const parser = createFormattedParser();
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', (chunk) => parser.push(chunk));
  process.stdin.on('end', () => parser.flush());
}

async function runReplay(filePath) {
  printBanner();
  const resolved = path.resolve(process.cwd(), filePath);
  if (!fs.existsSync(resolved)) {
    console.error(`File not found: ${resolved}`);
    process.exit(1);
  }
  console.log(`Replaying NDJSON events from: ${resolved}`);
  const parser = createFormattedParser();
  const content = fs.readFileSync(resolved, 'utf8');
  parser.push(content);
  parser.flush();
}

async function runFixtures() {
  printBanner();
  const fixturePath = path.join(ROOT, 'shared/fixtures/events.json');
  console.log(`Replaying valid rx events from shared fixtures: ${fixturePath}`);
  const fixtures = JSON.parse(fs.readFileSync(fixturePath, 'utf8'));
  const parser = createFormattedParser();

  let count = 0;
  for (const item of fixtures) {
    if (item.role === 'rx' && item.valid) {
      parser.push(JSON.stringify(item.value) + '\n');
      count++;
    }
  }
  parser.flush();
  console.log(`Completed replay of ${count} valid shared rx fixtures.`);
}

async function runSimulate() {
  printBanner();
  console.log('Simulating typical demo sequence...');
  const parser = createFormattedParser();

  console.log('\n--- 1. Board Boot Hello ---');
  parser.push('{"v":1,"event":"hello","role":"rx","max_text_bytes":48}\n');

  console.log('\n--- 2. Valid Incoming Speech Transcript ---');
  // "Spirit, what is your name?" -> 5370697269742C207768617420697320796F7572206E616D653F
  parser.push('{"v":1,"event":"message","session":"B007CAFE","seq":0,"payload_hex":"5370697269742C207768617420697320796F7572206E616D653F"}\n');

  console.log('\n--- 3. Optical Beam Interruption (Disturbance) ---');
  parser.push('{"v":1,"event":"disturbance","code":"CHECKSUM_FAILED","reason":"CRC_MISMATCH","session":null,"seq":null}\n');

  console.log('\n--- 4. Incomplete Packet Interruption ---');
  parser.push('{"v":1,"event":"disturbance","code":"INCOMPLETE_PACKET","reason":"INDEX_GAP","session":null,"seq":null}\n');

  console.log('\n--- 5. Duplicate Packet Drop ---');
  parser.push('{"v":1,"event":"duplicate","session":"B007CAFE","seq":0}\n');

  parser.flush();
  console.log('\nSimulation complete.');
}

const args = process.argv.slice(2);
if (args.includes('--stdin')) {
  runStdin();
} else if (args.includes('--fixtures')) {
  runFixtures();
} else if (args.includes('--simulate')) {
  runSimulate();
} else if (args.includes('--replay') && args[args.indexOf('--replay') + 1]) {
  runReplay(args[args.indexOf('--replay') + 1]);
} else {
  printBanner();
  console.log('Usage:');
  console.log('  node src/cli.mjs --stdin              Read and parse NDJSON lines from STDIN');
  console.log('  node src/cli.mjs --replay <file>      Replay an NDJSON event file');
  console.log('  node src/cli.mjs --fixtures           Replay valid events from shared fixtures');
  console.log('  node src/cli.mjs --simulate           Simulate demo sequence (message, disturbance, dup)');
}
