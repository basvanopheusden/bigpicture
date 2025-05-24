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

test('handleUndo clears editing state for blank additions', () => {
  assert.match(src, /editingArea && !editingArea\.text\.trim\(\)/);
  assert.ok(has('setEditingArea(null)'), 'setEditingArea(null) missing');
  assert.match(src, /editingObjective && !editingObjective\.text\.trim\(\)/);
  assert.ok(has('setEditingObjective(null)'), 'setEditingObjective(null) missing');
  assert.match(src, /editingTask && !editingTask\.text\.trim\(\)/);
  assert.ok(has('setEditingTask(null)'), 'setEditingTask(null) missing');
});
