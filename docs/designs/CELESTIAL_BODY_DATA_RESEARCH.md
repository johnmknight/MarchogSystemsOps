# Weather Page — Celestial Body Data Research

## Research Date: 2026-02-23

## Summary

Three data source categories identified for rendering Moon and Mars geological features:

---

## 1. MOON (Luna)

### Data Sources

**A. USGS Unified Geologic Map of the Moon (1:5M, 2020)** ⭐ PRIMARY
- URL: https://astrogeology.usgs.gov/search/map/Moon/Geology/Unified_Geologic_Map_of_the_Moon_GIS_v2
- Download: https://asc-astropedia.s3.us-west-2.amazonaws.com/Moon/Geology/Unified_Geologic_Map_of_the_Moon_GIS_v2.zip
- Format: ArcGIS geodatabase + Shapefiles (GeoUnits polygons, contacts polylines, linear features)
- Content: Globally consistent geologic unit polygons with type classifications
- Units include: Maria (mare basalt), highland terrain, crater materials, etc.
- Authors: Fortezzo, Spudis, Harrel (2020)
- License: US Government public domain

**B. LROC Mare Boundary Polygons** ⭐ BEST FOR MARIA
- URL: https://data.lroc.im-ldi.com/lroc/view_rdr/SHAPEFILE_LROC_GLOBAL_MARE
- Format: Shapefile (polygons)
- Content: Digitized mare boundaries from LROC WAC basemap
- Coordinate systems: IAU Moon 2000 (-180 to 180 AND 0 to 360)
- This is exactly what we need for drawing Maria regions

**C. IAU/USGS Nomenclature (Center Points)**
- URL: https://planetarynames.wr.usgs.gov/GIS_Downloads
- Download: https://asc-planetarynames-data.s3.us-west-2.amazonaws.com/MOON_nomenclature_center_pts.zip
- Format: Shapefile (POINTS only, not polygons)
- Content: 9,003+ named features with center lat/lon, diameter, feature type
- Feature types: Mare, Mons, Crater, Vallis, Rima, Lacus, Sinus, Palus, Oceanus, etc.
- Use for: Labels and approximate circular boundaries (center + diameter → circle)

### Lunar Feature Types for Display
| Latin Term | English | Example | Display Priority |
|------------|---------|---------|-----------------|
| Mare | Sea (dark basalt plains) | Mare Tranquillitatis | HIGH - large polygon regions |
| Oceanus | Ocean | Oceanus Procellarum | HIGH - largest mare region |
| Sinus | Bay | Sinus Iridum | MEDIUM |
| Lacus | Lake | Lacus Mortis | MEDIUM |
| Palus | Marsh | Palus Putredinis | MEDIUM |
| Mons/Montes | Mountain(s) | Mons Huygens | MEDIUM - point/area |
| Vallis | Valley | Vallis Schröteri | LOW - linear feature |
| Rima/Rimae | Rille(s) | Rima Hadley | LOW - linear feature |
| Rupes | Scarp | Rupes Recta | LOW - linear feature |
| Dorsum/Dorsa | Ridge(s) | Dorsa Smirnov | LOW - linear feature |
| Crater | Crater | Copernicus | HIGH for major craters |

### Recommended Approach for Moon
1. Download LROC mare boundary shapefiles → convert to GeoJSON → extract polygon outlines
2. Download USGS nomenclature center points → use for labels + approximate circles for craters
3. For Mons features: use center point + diameter to draw approximate circles
4. Major maria as filled polygon regions (like US states)
5. Major craters as circles (center + radius)

---

## 2. MARS

### Data Sources

**A. USGS Global Geologic Map of Mars (SIM 3292, 2014)** ⭐ PRIMARY
- URL: https://pubs.usgs.gov/sim/3292/
- Download: https://pubs.usgs.gov/sim/3292/pdf/sim3292_map.zip (GIS package)
- Format: ArcGIS geodatabase + Shapefiles
- Content: Global geologic unit polygons at 1:20,000,000 scale
- Authors: Tanaka, Skinner, Dohm, Irwin, Kolb, Fortezzo, et al. (2014)
- License: US Government public domain
- Contains: GeoUnits (polygons), GeoContacts (polylines), GeoLinear (structures)

**B. IAU/USGS Mars Nomenclature (Center Points)**
- URL: https://planetarynames.wr.usgs.gov/GIS_Downloads
- Download: https://asc-planetarynames-data.s3.us-west-2.amazonaws.com/MARS_nomenclature_center_pts.zip
- Format: Shapefile (POINTS only)
- Content: Named features with center lat/lon, diameter, feature type
- Feature types: Planitia, Terra, Mons, Vallis, Crater, Chasma, Fossa, etc.

### Mars Feature Types for Display
| Latin Term | English | Example | Display Priority |
|------------|---------|---------|-----------------|
| Planitia | Plain/lowland | Utopia Planitia | HIGH - large polygon regions |
| Terra | Land/highland | Terra Cimmeria | HIGH - large polygon regions |
| Planum | Plateau | Planum Australe | HIGH |
| Mons/Montes | Mountain(s) | Olympus Mons | HIGH - volcanic shields |
| Chasma | Canyon | Valles Marineris | HIGH - major canyon system |
| Vallis | Valley | Kasei Valles | MEDIUM |
| Crater | Crater | Gale Crater | MEDIUM for major ones |
| Fossa/Fossae | Ditch/trough | Cerberus Fossae | LOW - linear |
| Labyrinthus | Labyrinth | Noctis Labyrinthus | MEDIUM |

### Recommended Approach for Mars
1. Download SIM 3292 shapefile package → extract geologic unit polygons
2. Filter for major region types (volcanic, basin, highland, etc.)
3. Download nomenclature center points for labeling
4. Major regions (Planitiae, Terrae) as filled polygons
5. Volcanic shields (Mons) as approximate circles from center + diameter
6. Valles Marineris as polygon from geologic map

---

## Implementation Plan

### Data Pipeline
1. Download shapefiles for Moon (LROC mare + USGS geologic + nomenclature) and Mars (SIM 3292 + nomenclature)
2. Convert shapefiles to GeoJSON using Python (pyproj/fiona/shapely or ogr2ogr)
3. Extract major features by type, simplify coordinates (like lake data reduction)
4. Output compact JS data files: `moon_data.js`, `mars_data.js`
5. Coordinate system: lat/lon (-180 to 180 east longitude, planetocentric latitude)

### Rendering Differences from Earth
- Moon: No atmosphere data, so "weather" panel shows different data (phase, libration, distance, illumination)
- Mars: Has atmosphere — could show simulated or historical weather data (InSight data, dust storms)
- Both: Same tactical wireframe aesthetic, same globe renderer, different data overlays

### Weather API Alternatives
- **Moon**: No weather. Display orbital/phase data, Earth-Moon distance, illumination percentage
- **Mars**: Mars Climate Database (free), or simulated data based on InSight/Curiosity historical readings

---

## File Size Estimates
| Dataset | Raw Size | After Simplification |
|---------|----------|---------------------|
| Moon mare boundaries (LROC) | ~5-15 MB shapefile | ~50-100 KB JS |
| Moon nomenclature points | ~2 MB shapefile | ~20 KB JS (major features only) |
| Mars geologic polygons (SIM 3292) | ~50 MB shapefile | ~100-200 KB JS |
| Mars nomenclature points | ~3 MB shapefile | ~20 KB JS (major features only) |

## Notes
- All data is US Government public domain — no licensing concerns
- Shapefiles need conversion (ogr2ogr or Python geopandas) to get to JSON
- LROC mare boundaries are the cleanest polygon data for Moon maria
- Mars SIM 3292 is the gold standard for Mars geologic polygons
