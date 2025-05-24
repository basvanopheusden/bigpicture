import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import path from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
function resolve(relPath) {
  return path.join(__dirname, '..', relPath);
}

const src = readFileSync(resolve('src/components/TaskManager.jsx'), 'utf8');

function has(str) {
  return new RegExp(str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).test(src);
}

test('handleUndo posts to /api/undo and refreshes data', () => {
  assert.ok(has('const handleUndo'), 'handleUndo not defined');
  assert.match(src, /apiWrapper\.post\('\/api\/undo'\)/);
  assert.match(src, /refreshAll\(/);
});

test('undo button calls handleUndo on click', () => {
  assert.match(src, /<button[^>]*onClick={handleUndo}/);
  assert.ok(src.includes('↺'), 'button label missing');
});

test('Ctrl\+Z shortcut triggers handleUndo', () => {
  assert.match(src, /addEventListener\('keydown',/);
  assert.match(src, /e.key === 'z'/);
  assert.match(src, /handleUndo\(\)/);
});
