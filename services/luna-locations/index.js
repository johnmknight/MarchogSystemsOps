const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(cors());

// ── Load moon data ──────────────────────────────────────
const dataPath = path.join(__dirname, '..', '..', 'client', 'pages', 'data', 'moon', 'moon_data.js');
const src = fs.readFileSync(dataPath, 'utf8');

// Extract LUNA_FEATURES array from the JS file
let FEATURES = [];
try {
  // The file defines: const LUNA_REFERENCE = {...}; const LUNA_FEATURES = [...];
  const match = src.match(/LUNA_FEATURES\s*=\s*(\[[\s\S]*\]);/);
  if (match) FEATURES = JSON.parse(match[1]);
} catch (e) {
  console.error('Failed to parse moon_data.js:', e.message);
}
console.log(`Loaded ${FEATURES.length} Luna features`);

// ── Normalize for search ────────────────────────────────
function normalize(s) { return s.toLowerCase().replace(/['']/g, '').replace(/[^a-z0-9]/g, ' ').trim(); }

// Pre-index for fast search
const indexed = FEATURES.map(f => ({
  ...f,
  _search: normalize(f.name),
  _tokens: normalize(f.name).split(/\s+/)
}));

// ── GET /api/search?q=... ───────────────────────────────
app.get('/api/search', (req, res) => {
  const q = normalize(req.query.q || '');
  if (!q || q.length < 2) return res.json([]);

  const tokens = q.split(/\s+/);
  const results = indexed
    .filter(f => tokens.every(t => f._search.includes(t)))
    .slice(0, 20)
    .map(f => ({
      name: f.name,
      type: f.type,
      category: f.category,
      lat: f.lat,
      lon: f.lon > 180 ? f.lon - 360 : f.lon,
      diameter: f.diameter
    }));

  res.json(results);
});

// ── GET /api/features?category=region ────────────────────
app.get('/api/features', (req, res) => {
  const cat = req.query.category;
  let list = FEATURES;
  if (cat) list = list.filter(f => f.category === cat);

  res.json(list.map(f => ({
    name: f.name,
    type: f.type,
    category: f.category,
    lat: f.lat,
    lon: f.lon > 180 ? f.lon - 360 : f.lon,
    diameter: f.diameter
  })));
});

// ── Start ───────────────────────────────────────────────
const PORT = process.env.PORT || 8091;
app.listen(PORT, () => console.log(`Luna locations service on :${PORT}`));
