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

test('TaskManager JSX fragments are balanced', () => {
  const src = readFileSync(resolve('src/components/TaskManager.jsx'), 'utf8');
  const opens = (src.match(/<>/g) || []).length;
  const closes = (src.match(/<\/>/g) || []).length;
  assert.equal(opens, closes);
});
