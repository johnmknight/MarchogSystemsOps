const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());

// Open-Meteo Geocoding API (free, no key required)
const GEO_BASE = 'https://geocoding-api.open-meteo.com/v1/search';

// ── GET /api/search?q=... ───────────────────────────────
// Handles city names, ZIP codes, or partial text
app.get('/api/search', async (req, res) => {
  const q = (req.query.q || '').trim();
  if (!q || q.length < 2) return res.json([]);

  try {
    // Open-Meteo handles ZIP codes and city names
    const url = `${GEO_BASE}?name=${encodeURIComponent(q)}&count=20&language=en&format=json`;
    const resp = await fetch(url);
    const data = await resp.json();

    if (!data.results) return res.json([]);

    const results = data.results.map(r => ({
      name: r.name,
      type: 'city',
      category: 'populated',
      lat: r.latitude,
      lon: r.longitude,
      country: r.country || '',
      country_code: r.country_code || '',
      admin1: r.admin1 || '',       // state/province
      admin2: r.admin2 || '',       // county
      population: r.population || 0,
      elevation: r.elevation || null,
      timezone: r.timezone || '',
      // Build display name: "City, State, Country"
      display: [r.name, r.admin1, r.country].filter(Boolean).join(', ')
    }));

    res.json(results);
  } catch (e) {
    console.error('Geocoding error:', e.message);
    res.status(502).json({ error: 'Geocoding service unavailable' });
  }
});

// ── GET /api/features (not applicable for Earth, returns empty) ──
app.get('/api/features', (req, res) => {
  res.json([]);
});

// ── Start ───────────────────────────────────────────────
const PORT = process.env.PORT || 8090;
app.listen(PORT, () => console.log(`Earth locations service on :${PORT}`));
