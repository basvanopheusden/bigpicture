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

function checkBalanced(src, tag) {
  const open = (src.match(new RegExp(`<${tag}\\b`, 'g')) || []).length;
  const close = (src.match(new RegExp(`</${tag}>`, 'g')) || []).length;
  assert.equal(open, close);
}

function combinedSrc() {
  const files = [
    'src/components/TaskManager.jsx',
    'src/components/AreaList.jsx',
    'src/components/ObjectiveList.jsx',
    'src/components/TaskList.jsx'
  ];
  return files.map(f => readFileSync(resolve(f), 'utf8')).join('\n');
}

test('TaskManager JSX fragments are balanced', () => {
  const src = combinedSrc();
  const opens = (src.match(/<>/g) || []).length;
  const closes = (src.match(/<\/>/g) || []).length;
  assert.equal(opens, closes);
});

test('TaskManager div tags are balanced', () => {
  const src = combinedSrc();
  const opens = (src.match(/<div[^>]*>/g) || []).length;
  const closes = (src.match(/<\/div>/g) || []).length;
  assert.equal(opens, closes);
});

test('DragDropContext tag closes properly', () => {
  const src = combinedSrc();
  checkBalanced(src, 'DragDropContext');
});

test('Droppable tags close properly', () => {
  const src = combinedSrc();
  checkBalanced(src, 'Droppable');
});

test('Draggable tags close properly', () => {
  const src = combinedSrc();
  checkBalanced(src, 'Draggable');
});

test('ReactMarkdown tags close properly', () => {
  const src = combinedSrc();
  checkBalanced(src, 'ReactMarkdown');
});
