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

test('bottom section defines droppable area list', () => {
  assert.match(src, /droppableId=\"areas-list-bottom\"/);
});

test('bottom areas and objectives use Draggable', () => {
  assert.match(src, /<Draggable key={`bottom-\$\{area.key\}`}/);
  assert.match(src, /<Draggable key={`bottom-\$\{objective.key\}`}/);
});
