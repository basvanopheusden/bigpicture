import test from 'node:test';
import assert from 'node:assert/strict';
import { getStoredAuth, storeAuth, clearAuth } from '../src/utils/auth.js';

class MockStorage {
  constructor() { this.store = {}; }
  getItem(k) { return Object.prototype.hasOwnProperty.call(this.store, k) ? this.store[k] : null; }
  setItem(k, v) { this.store[k] = String(v); }
  removeItem(k) { delete this.store[k]; }
}

test('authentication state persists via localStorage', () => {
  const mock = new MockStorage();
  global.localStorage = mock;
  assert.equal(getStoredAuth(), false);
  storeAuth();
  assert.equal(mock.getItem('authenticated'), 'true');
  // simulate reload by calling getStoredAuth again
  assert.equal(getStoredAuth(), true);
  clearAuth();
  assert.equal(mock.getItem('authenticated'), null);
});
