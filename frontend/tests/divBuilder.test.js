import test from 'node:test';
import assert from 'node:assert/strict';
import { divSpec, specToHtml, isValidDivString, nestedDivSpec, branchingDivSpec } from '../src/utils/divBuilder.js';

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

test('nestedDivSpec generates balanced HTML', () => {
  const html = specToHtml(nestedDivSpec(5));
  assert.ok(isValidDivString(html));
});

test('branchingDivSpec generates balanced HTML', () => {
  const html = specToHtml(branchingDivSpec(3, 2));
  const opens = (html.match(/<div/g) || []).length;
  const closes = (html.match(/<\/div>/g) || []).length;
  assert.ok(isValidDivString(html));
  assert.equal(opens, closes);
});

test('isValidDivString detects imbalance', () => {
  assert.equal(isValidDivString('<div><div></div>'), false);
});
