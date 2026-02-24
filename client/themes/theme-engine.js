/**
 * MarchogSystemsOps — Theme Engine
 * 
 * Shared module for template pages to load and apply themes.
 * Each theme defines colors, fonts, border styles, and optional FX.
 * 
 * Usage in a template page:
 *   <script src="../themes/theme-engine.js"></script>
 *   <script>
 *     MarchogTheme.init('imperial');          // apply by ID
 *     MarchogTheme.init();                    // reads ?theme= from URL, falls back to 'marchog'
 *   </script>
 * 
 * The engine:
 *   1. Loads themes.json (once, cached)
 *   2. Injects @font-face / Google Fonts <link>
 *   3. Sets CSS custom properties on :root
 *   4. Injects optional scanlines / vignette / CRT glow overlays
 *   5. Injects border frame CSS based on border_style
 */

const MarchogTheme = (() => {
  let _themes = null;
  let _activeTheme = null;

  // ── Load themes.json ──────────────────────────────
  async function _loadThemes() {
    if (_themes) return _themes;
    const base = _resolveBase();
    const resp = await fetch(`${base}/themes/themes.json`);
    _themes = await resp.json();
    return _themes;
  }

  function _resolveBase() {
    // Works from /client/pages/, /client/themes/, or /client/
    const path = window.location.pathname;
    if (path.includes('/pages/')) return '..';
    if (path.includes('/themes/')) return '..';
    return '.';
  }

  // ── Apply theme ───────────────────────────────────
  async function init(themeId) {
    const themes = await _loadThemes();

    // Resolve theme ID: explicit > URL param > default
    if (!themeId) {
      const params = new URLSearchParams(window.location.search);
      themeId = params.get('theme') || 'marchog';
    }

    const theme = themes.find(t => t.id === themeId);
    if (!theme) {
      console.warn(`[MarchogTheme] Theme "${themeId}" not found, falling back to marchog`);
      _activeTheme = themes.find(t => t.id === 'marchog') || themes[0];
    } else {
      _activeTheme = theme;
    }

    _applyFonts(_activeTheme);
    _applyCSSVars(_activeTheme);
    _applyOverlays(_activeTheme);
    _applyBorderStyle(_activeTheme);

    document.body.dataset.theme = _activeTheme.id;
    document.body.dataset.themeGroup = _activeTheme.group;
    console.log(`[MarchogTheme] Applied: ${_activeTheme.name} (${_activeTheme.id})`);
    return _activeTheme;
  }

  // ── Font injection ────────────────────────────────
  function _applyFonts(theme) {
    const f = theme.fonts;
    const base = _resolveBase();

    // Google Fonts
    if (f.google_import) {
      const existing = document.querySelector('link[data-marchog-gfonts]');
      if (existing) existing.remove();
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.dataset.marchogGfonts = '1';
      link.href = `https://fonts.googleapis.com/css2?${f.google_import.split('|').map(f => `family=${f}`).join('&')}&display=swap`;
      document.head.appendChild(link);
    }

    // Local @font-face
    if (f.local_faces) {
      const existing = document.querySelector('style[data-marchog-faces]');
      if (existing) existing.remove();
      const style = document.createElement('style');
      style.dataset.marchogFaces = '1';
      style.textContent = f.local_faces.map(face =>
        `@font-face { font-family: '${face.family}'; src: url('${base}/${face.src.replace(/^\.\.\//, '')}') format('opentype'); ${face.weight ? `font-weight: ${face.weight};` : ''} }`
      ).join('\n');
      document.head.appendChild(style);
    }
  }

  // ── CSS custom properties ─────────────────────────
  function _applyCSSVars(theme) {
    const root = document.documentElement;
    const c = theme.colors;
    const f = theme.fonts;

    // Colors
    root.style.setProperty('--theme-bg', c.bg);
    root.style.setProperty('--theme-bg-panel', c.bg_panel);
    root.style.setProperty('--theme-primary', c.primary);
    root.style.setProperty('--theme-primary-dim', c.primary_dim);
    root.style.setProperty('--theme-secondary', c.secondary);
    root.style.setProperty('--theme-accent', c.accent);
    root.style.setProperty('--theme-danger', c.danger);
    root.style.setProperty('--theme-warning', c.warning);
    root.style.setProperty('--theme-success', c.success);
    root.style.setProperty('--theme-text', c.text);
    root.style.setProperty('--theme-text-dim', c.text_dim);
    root.style.setProperty('--theme-border', c.border);

    // Fonts
    root.style.setProperty('--theme-font-heading', `'${f.heading}', 'Courier New', monospace`);
    root.style.setProperty('--theme-font-body', `'${f.body}', 'Courier New', monospace`);
    root.style.setProperty('--theme-font-accent', `'${f.accent}', 'Courier New', monospace`);
  }

  // ── Overlay FX (scanlines, vignette, CRT glow) ───
  function _applyOverlays(theme) {
    // Remove existing overlays
    document.querySelectorAll('[data-marchog-overlay]').forEach(el => el.remove());

    if (theme.scanlines) {
      const el = document.createElement('div');
      el.dataset.marchogOverlay = 'scanlines';
      Object.assign(el.style, {
        position: 'fixed', inset: '0', zIndex: '9990', pointerEvents: 'none',
        background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.04) 2px, rgba(0,0,0,0.04) 4px)'
      });
      document.body.appendChild(el);
    }

    if (theme.vignette) {
      const el = document.createElement('div');
      el.dataset.marchogOverlay = 'vignette';
      Object.assign(el.style, {
        position: 'fixed', inset: '0', zIndex: '9991', pointerEvents: 'none',
        background: 'radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.55) 100%)'
      });
      document.body.appendChild(el);
    }

    if (theme.crt_glow) {
      // Subtle text-shadow glow via a CSS class on body
      const style = document.createElement('style');
      style.dataset.marchogOverlay = 'crt-glow-style';
      style.textContent = `
        body[data-theme] * {
          text-shadow: 0 0 6px ${theme.colors.primary_dim}, 0 0 12px ${theme.colors.primary_dim};
        }
      `;
      document.head.appendChild(style);
    }
  }

  // ── Border frame styles ───────────────────────────
  function _applyBorderStyle(theme) {
    const existing = document.querySelector('style[data-marchog-borders]');
    if (existing) existing.remove();

    const bs = theme.border_style;
    if (bs === 'none') return;

    const c = theme.colors;
    let css = '';

    if (bs === 'marchog' || bs === 'angular') {
      // Angular cut-corner frame
      css = `
        .theme-frame {
          position: relative;
          border: 1px solid ${c.border};
          clip-path: polygon(0 12px, 12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%);
          padding: 16px;
        }
        .theme-frame::before {
          content: '';
          position: absolute; inset: 0;
          border: 1px solid ${c.border};
          clip-path: polygon(0 12px, 12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%);
          pointer-events: none;
        }
        .theme-panel {
          background: ${c.bg_panel};
          border: 1px solid ${c.border};
          clip-path: polygon(0 8px, 8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%);
          padding: 12px;
        }
      `;
    } else if (bs === 'lcars') {
      // LCARS rounded panel
      css = `
        .theme-frame {
          position: relative;
          border: 3px solid ${c.primary};
          border-radius: 0 24px 24px 0;
          padding: 16px 16px 16px 28px;
        }
        .theme-frame::before {
          content: '';
          position: absolute; left: 0; top: 0; bottom: 0; width: 20px;
          background: ${c.primary};
          border-radius: 0 0 0 12px;
        }
        .theme-panel {
          background: ${c.bg_panel};
          border: 2px solid ${c.secondary};
          border-radius: 0 16px 16px 0;
          padding: 12px 12px 12px 20px;
        }
      `;
    } else if (bs === 'thin') {
      // Clean thin border
      css = `
        .theme-frame {
          border: 1px solid ${c.border};
          padding: 16px;
        }
        .theme-panel {
          background: ${c.bg_panel};
          border: 1px solid ${c.border};
          padding: 12px;
        }
      `;
    } else if (bs === 'thick') {
      // Military thick border
      css = `
        .theme-frame {
          border: 2px solid ${c.primary_dim};
          padding: 16px;
        }
        .theme-frame::before {
          content: '';
          position: absolute; inset: 3px;
          border: 1px solid ${c.border};
          pointer-events: none;
        }
        .theme-panel {
          background: ${c.bg_panel};
          border: 2px solid ${c.primary_dim};
          padding: 12px;
        }
      `;
    }

    // Common utility classes for all border styles
    css += `
      .theme-heading {
        font-family: var(--theme-font-heading);
        color: var(--theme-primary);
        text-transform: uppercase;
        letter-spacing: 0.15em;
      }
      .theme-subheading {
        font-family: var(--theme-font-accent);
        color: var(--theme-secondary);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-size: 0.85em;
      }
      .theme-body {
        font-family: var(--theme-font-body);
        color: var(--theme-text);
        line-height: 1.5;
      }
      .theme-dim {
        color: var(--theme-text-dim);
      }
      .theme-accent {
        color: var(--theme-accent);
      }
      .theme-divider {
        border: none;
        border-top: 1px solid var(--theme-border);
        margin: 12px 0;
      }
      .theme-badge {
        display: inline-block;
        font-family: var(--theme-font-accent);
        font-size: 0.7em;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        padding: 2px 8px;
        border: 1px solid var(--theme-border);
        color: var(--theme-primary);
      }
      .theme-page-bg {
        background: var(--theme-bg);
        color: var(--theme-text);
        min-height: 100vh;
        font-family: var(--theme-font-body);
      }
    `;

    const style = document.createElement('style');
    style.dataset.marchogBorders = '1';
    style.textContent = css;
    document.head.appendChild(style);
  }

  // ── Public API ────────────────────────────────────
  return {
    init,
    getTheme: () => _activeTheme,
    getThemes: () => _loadThemes(),
    getThemeById: async (id) => {
      const themes = await _loadThemes();
      return themes.find(t => t.id === id);
    }
  };
})();
