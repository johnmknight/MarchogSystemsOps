// mso-base.js — Reverse proxy subpath detection for MarchogSystemsOps
// Include this script BEFORE any fetch calls in every page.
const MSO_BASE = (() => {
  let path;
  try { path = window.parent.location.pathname; } catch(e) { path = window.location.pathname; }
  const seg = path.split('/')[1] || '';
  const excluded = ['api','static','client','pages','ws','js','css','assets','themes','media','config','icons','fonts','thumbnails'];
  if (!seg || seg.includes('.') || excluded.includes(seg)) return '';
  return '/' + seg;
})();

// Monkey-patch fetch to auto-prepend MSO_BASE to root-relative URLs
const _origFetch = window.fetch;
window.fetch = function(url, opts) {
  if (typeof url === 'string' && url.startsWith('/') && !url.startsWith('//') && MSO_BASE) {
    url = MSO_BASE + url;
  }
  return _origFetch.call(this, url, opts);
};
