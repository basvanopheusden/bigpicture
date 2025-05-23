import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import path from 'path';

// Helper to resolve paths relative to this file
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function resolve(relPath) {
  return path.join(__dirname, '..', relPath);
}

test('index.html has root div and script tag', () => {
  const html = readFileSync(resolve('index.html'), 'utf8');
  assert.match(html, /<div id="root"><\/div>/);
  assert.match(html, /<script type="module" src="\/src\/main.jsx"><\/script>/);
});

test('package.json defines expected npm scripts', () => {
  const pkg = JSON.parse(readFileSync(resolve('package.json'), 'utf8'));
  assert.ok(pkg.scripts && pkg.scripts.dev, 'dev script missing');
  assert.ok(pkg.scripts && pkg.scripts.build, 'build script missing');
  assert.ok(pkg.scripts && pkg.scripts.preview, 'preview script missing');
});

import tailwindConfig from '../tailwind.config.js';

test('tailwind config includes index.html', () => {
  assert.ok(tailwindConfig.content.includes('./index.html'));
});

test('main.jsx renders App inside StrictMode', () => {
  const src = readFileSync(resolve('src/main.jsx'), 'utf8');
  assert.match(src, /<StrictMode>/);
  assert.match(src, /<App \/>/);
});

test('TaskItem component is imported and defined', () => {
  const taskListSrc = readFileSync(resolve('src/components/TaskList.jsx'), 'utf8');
  assert.match(taskListSrc, /from '.\/TaskItem'/);

  const itemSrc = readFileSync(resolve('src/components/TaskItem.jsx'), 'utf8');
  assert.match(itemSrc, /const TaskItem/);
  assert.match(itemSrc, /export default TaskItem/);
});
