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

const src = readFileSync(resolve('src/components/AreaList.jsx'), 'utf8');

test('shows add area button at the end of the list', () => {
  assert.match(src, /<PlusIcon[^>]*onClick={handleAddArea}/);
});
