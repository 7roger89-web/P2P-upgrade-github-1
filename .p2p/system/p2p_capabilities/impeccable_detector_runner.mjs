#!/usr/bin/env node
// P2P host runner for the pinned Impeccable deterministic design detector.
//
// This file is P2P host code. It is NOT a second router, orchestrator, design
// system or skill loader: it only invokes the two offline detector engines of
// the pinned local vendor snapshot and prints a normalized, stable JSON report.
//
// Boundaries enforced here:
//   - no network, no install, no browser, no model
//   - no DESIGN.md / project config discovery (no cross-project contamination)
//   - no upstream CLI, no upstream live/browser/cache surface
//   - deterministic ordering so repeat runs are byte-comparable
//
// Vendor snapshot: .p2p/vendor/skill/pbakaus-impeccable-94b7f34
// Upstream: https://github.com/pbakaus/impeccable @ 94b7f34 (Apache-2.0)

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const VENDOR_DETECTOR = path.resolve(
  HERE,
  '..',
  '..',
  'vendor',
  'skill',
  'pbakaus-impeccable-94b7f34',
  'skills',
  'impeccable',
  'scripts',
  'detector',
);

const SCHEMA = 'p2p-impeccable-deterministic-check/1';
const HTML_EXTENSIONS = new Set(['.html', '.htm']);

// Enhanced static-HTML parsing is OPTIONAL. When the four upstream parser
// modules are absent the vendored engine degrades to its regex engine. Both
// modes are deterministic and model-free; the mode is always reported so that
// evidence is never read as a clean bill of health when it is an undercount.
async function probeEngineMode() {
  try {
    await Promise.all([
      import('htmlparser2'),
      import('css-select'),
      import('css-tree'),
      import('domutils'),
    ]);
    return 'STATIC_HTML_FULL';
  } catch {
    return 'REGEX_DEGRADED';
  }
}

function normalize(finding, root) {
  const file = finding.file ? path.relative(root, path.resolve(finding.file)).split(path.sep).join('/') : null;
  return {
    antipattern: finding.antipattern,
    name: finding.name,
    category: finding.category,
    severity: finding.severity,
    advisory: finding.advisory === true,
    file,
    line: typeof finding.line === 'number' ? finding.line : null,
    snippet: typeof finding.snippet === 'string' ? finding.snippet : String(finding.snippet ?? ''),
  };
}

function stableKey(item) {
  return [item.file, String(item.line ?? ''), item.antipattern, item.snippet].join('\u0000');
}

async function main() {
  const args = process.argv.slice(2);
  let root = process.cwd();
  const targets = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--root') { root = path.resolve(args[i + 1]); i += 1; continue; }
    targets.push(args[i]);
  }
  if (targets.length === 0) {
    process.stderr.write('P2P_IMPECCABLE_RUNNER: no target files supplied\n');
    process.exit(2);
  }

  const engineMode = await probeEngineMode();
  const { detectText } = await import(path.join(VENDOR_DETECTOR, 'engines', 'regex', 'detect-text.mjs'));
  const { detectHtml } = await import(path.join(VENDOR_DETECTOR, 'engines', 'static-html', 'detect-html.mjs'));

  const findings = [];
  const scanned = [];
  for (const target of targets) {
    const resolved = path.resolve(target);
    if (!fs.existsSync(resolved) || !fs.statSync(resolved).isFile()) {
      process.stderr.write(`P2P_IMPECCABLE_RUNNER: not a file: ${target}\n`);
      process.exit(2);
    }
    scanned.push(path.relative(root, resolved).split(path.sep).join('/'));
    const extension = path.extname(resolved).toLowerCase();
    const raw = HTML_EXTENSIONS.has(extension)
      ? await detectHtml(resolved, {})
      : detectText(fs.readFileSync(resolved, 'utf-8'), resolved, {});
    for (const item of raw) findings.push(normalize(item, root));
  }

  const seen = new Set();
  const unique = [];
  for (const item of findings) {
    const key = stableKey(item);
    if (seen.has(key)) continue;
    seen.add(key);
    unique.push(item);
  }
  unique.sort((a, b) => (stableKey(a) < stableKey(b) ? -1 : stableKey(a) > stableKey(b) ? 1 : 0));

  const categories = {};
  for (const item of unique) categories[item.antipattern] = (categories[item.antipattern] || 0) + 1;

  process.stdout.write(
    JSON.stringify(
      {
        schema: SCHEMA,
        engine_mode: engineMode,
        model_used: false,
        network_used: false,
        browser_used: false,
        scanned,
        finding_count: unique.length,
        antipattern_counts: Object.fromEntries(Object.entries(categories).sort()),
        findings: unique,
      },
      null,
      2,
    ) + '\n',
  );
}

await main();
