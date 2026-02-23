const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(cors());

// ── Load mars data ──────────────────────────────────────
const dataPath = path.join(__dirname, '..', '..', 'client', 'pages', 'data', 'mars', 'mars_data.js');
const src = fs.readFileSync(dataPath, 'utf8');

let FEATURES = [];
try {
  const match = src.match(/MARS_FEATURES\s*=\s*(\[[\s\S]*\]);/);
  if (match) FEATURES = JSON.parse(match[1]);
} catch (e) {
  console.error('Failed to parse mars_data.js:', e.message);
}
console.log(`Loaded ${FEATURES.length} Mars features`);

// ── Normalize for search ────────────────────────────────
function normalize(s) { return s.toLowerCase().replace(/[''ē]/g, '').replace(/[^a-z0-9]/g, ' ').trim(); }

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
      lon: f.lon,
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
    lon: f.lon,
    diameter: f.diameter
  })));
});

// ── Start ───────────────────────────────────────────────
const PORT = process.env.PORT || 8092;
app.listen(PORT, () => console.log(`Mars locations service on :${PORT}`));
