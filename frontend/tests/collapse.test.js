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

test('TaskManager supports collapsing areas', () => {
  const src = readFileSync(resolve('src/components/TaskManager.jsx'), 'utf8');
  assert.match(src, /collapsedAreas/);
  assert.match(src, /useState\(/);
  assert.match(src, /new Set/);
  assert.match(src, /toggleAreaCollapse/);
  assert.match(src, /collapsedAreas\.has\(area.key\)/);
});
