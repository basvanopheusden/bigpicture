import test from 'node:test';
import assert from 'node:assert/strict';
import { divSpec, specToHtml, isValidDivString } from '../src/utils/divBuilder.js';

const spec = divSpec({
  className: 'outer',
  children: [
    divSpec({ className: 'inner' }),
    divSpec({ className: 'second', children: [divSpec({ className: 'deep' })] })
  ]
});

test('buildDiv produces balanced div structure', () => {
  const html = specToHtml(spec);
  assert.ok(isValidDivString(html));
  const opens = (html.match(/<div/g) || []).length;
  const closes = (html.match(/<\/div>/g) || []).length;
  assert.equal(opens, closes);
});
