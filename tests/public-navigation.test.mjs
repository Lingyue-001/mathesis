import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const root = fileURLToPath(new URL('..', import.meta.url));
const eleventy = join(root, 'node_modules', '@11ty', 'eleventy', 'cmd.js');

test('public navigation exposes Inspector and keeps the intentional Workbench removal', () => {
  const output = join(root, 'dist');
  rmSync(output, { recursive: true, force: true });
  execFileSync(process.execPath, [eleventy], {
    cwd: root,
    env: { ...process.env, NETLIFY: 'true' },
    stdio: 'pipe',
  });
  const home = readFileSync(join(output, 'index.html'), 'utf8');
  const pattern = readFileSync(join(output, 'patterns', 'index.html'), 'utf8');
  const grammar = readFileSync(join(output, 'relation-atlas', 'index.html'), 'utf8');

  assert.match(home, /Pattern Lab \(experimental\)/);
  assert.match(home, /href="(?:\/mathesis)?\/inspector\/">Inspector<\/a>/);
  assert.match(home, /Visual Grammar \(experimental\)/);
  assert.doesNotMatch(home, /href="\/adjudication\//);
  assert.match(pattern, /<h1 class="page-kicker">Pattern Lab \(experimental\)<\/h1>/);
  assert.match(grammar, /<h1>Visual Grammar \(experimental\)<\/h1>/);
  assert.equal(existsSync(join(output, 'adjudication', 'index.html')), false);
  assert.equal(existsSync(join(output, 'inspector', 'index.html')), true);
});
