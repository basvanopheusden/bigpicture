export function getStoredAuth() {
  return typeof localStorage !== 'undefined' && localStorage.getItem('authenticated') === 'true';
}

export function storeAuth() {
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem('authenticated', 'true');
  }
}

export function clearAuth() {
  if (typeof localStorage !== 'undefined') {
    localStorage.removeItem('authenticated');
  }
}
