/**
 * Build a specification object representing a <div> with optional className and children.
 * Children may be strings or other spec objects.
 */
export function divSpec({ className = '', children = [] } = {}) {
  return { className, children };
}

/** Convert a spec object into an HTML string. */
export function specToHtml(spec) {
  if (!spec) return '';
  const { className, children } = spec;
  const attr = className ? ` class="${className}"` : '';
  const inner = Array.isArray(children)
    ? children.map(specToHtml).join('')
    : (children || '');
  return `<div${attr}>${inner}</div>`;
}

/** Convert a spec into React elements using the provided React implementation. */
export function specToReact(spec, ReactLib) {
  if (!spec) return null;
  const { createElement, isValidElement } = ReactLib;
  const { className, children } = spec;
  const mapped = Array.isArray(children)
    ? children.map(child => (typeof child === 'object' && child && !isValidElement(child)
        ? specToReact(child, ReactLib)
        : child))
    : children;
  return createElement('div', { className }, mapped);
}

/** Validate that opening and closing <div> tags match. */
export function isValidDivString(html) {
  const open = (html.match(/<div/g) || []).length;
  const close = (html.match(/<\/div>/g) || []).length;
  return open === close;
}
