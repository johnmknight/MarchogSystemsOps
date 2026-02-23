"""
Build moon_regions.js — geologic terrain regions for Moon globe rendering.
Groups 49 USGS unit codes into ~8 high-level terrain types, dissolves + simplifies.
This is the 2nd-level detail: full surface coverage showing terrain classification.
"""
import geopandas as gpd
import json, os, sys
from shapely.ops import unary_union
sys.stdout.reconfigure(encoding='utf-8')

shp_dir = r'C:\Users\john_\dev\MarchogSystemsOps\_temp_moon\geologic\Unified_Geologic_Map_of_the_Moon_GIS\Lunar_GIS\Shapefiles'
gdf = gpd.read_file(f'{shp_dir}\\GeoUnits.shp')

print(f"Input: {len(gdf)} polygons")

# === TERRAIN CLASSIFICATION ===
# Group 49 USGS unit codes into high-level terrain types
# Based on Fortezzo et al. 2020 geologic map legend

TERRAIN_MAP = {
    # MARE (dark basalt volcanic plains) — render as filled regions
    'Em':   'mare',        # Eratosthenian Mare
    'Im1':  'mare',        # Imbrian Mare, Lower
    'Im2':  'mare',        # Imbrian Mare, Upper
    'Imd':  'mare',        # Imbrian Mare, Dome
    'Id':   'mare',        # Imbrian Dark Mantle (pyroclastic)

    # HIGHLAND TERRA (ancient anorthositic crust)
    'It':   'terra',       # Imbrian Terra
    'Itd':  'terra',       # Imbrian Terra, Dome
    'INt':  'terra',       # Imbrian-Nectarian Terra
    'Nt':   'terra',       # Nectarian Terra
    'Ntp':  'terra',       # Nectarian Terra, Plains mantling
    'pNt':  'terra',       # Pre-Nectarian Terra

    # PLAINS (smooth, intermediate albedo)
    'Ip':   'plains',      # Imbrian Plains
    'INp':  'plains',      # Imbrian-Nectarian Plains
    'Np':   'plains',      # Nectarian Plains
    'EIp':  'plains',      # Eratosthenian-Imbrian Plateau
    'Ig':   'plains',      # Imbrian Grooved terrain

    # BASIN (large impact basin materials)
    'Ib':   'basin',       # Imbrian Basin
    'Ibm':  'basin',       # Imbrian Basin, Massif
    'Nb':   'basin',       # Nectarian Basin
    'Nbl':  'basin',       # Nectarian Basin, Lineated
    'Nbm':  'basin',       # Nectarian Basin, Massif
    'Nbsc': 'basin',       # Nectarian Basin, Secondary Crater
    'pNb':  'basin',       # Pre-Nectarian Basin
    'pNbm': 'basin',       # Pre-Nectarian Basin, Massif

    # CRATER (impact craters — all ages)
    'Cc':   'crater',      # Copernican Crater
    'Ccc':  'crater',      # Copernican Crater, Catena
    'Csc':  'crater',      # Copernican Secondary
    'Ec':   'crater',      # Eratosthenian Crater
    'Ecc':  'crater',      # Eratosthenian Crater, Catena
    'Esc':  'crater',      # Eratosthenian Secondary
    'Ic':   'crater',      # Imbrian Crater
    'Ic1':  'crater',      # Imbrian Crater, Lower
    'Ic2':  'crater',      # Imbrian Crater, Upper
    'Icc':  'crater',      # Imbrian Crater, Catena
    'Icf':  'crater',      # Imbrian Crater, Fracture Floor
    'Isc':  'crater',      # Imbrian Secondary
    'Nc':   'crater',      # Nectarian Crater
    'pNc':  'crater',      # Pre-Nectarian Crater

    # IMBRIUM BASIN (specific to Mare Imbrium impact)
    'Iia':  'imbrium',     # Imbrium Alpes Formation
    'Iiap': 'imbrium',     # Imbrium Apenninus Formation
    'Iic':  'imbrium',     # Imbrium Crater
    'Iif':  'imbrium',     # Imbrium Fra Mauro Formation

    # ORIENTALE BASIN (specific to Mare Orientale impact)
    'Iohi': 'orientale',   # Orientale Hevelius, Inner
    'Ioho': 'orientale',   # Orientale Hevelius, Outer
    'Iohs': 'orientale',   # Orientale Hevelius, Secondary  (mapped from 'Iohs' in data)
    'Ios':  'orientale',   # Orientale Secondary
    'Iom':  'orientale',   # Orientale Maunder Formation
    'Iork': 'orientale',   # Orientale Rook, Knobby
    'Iorm': 'orientale',   # Orientale Rook, Massif
}

# Map terrain types to display properties
TERRAIN_STYLES = {
    'mare':      {'label': 'Maria (Volcanic)',   'color': '#1a3a5c', 'opacity': 0.6},
    'terra':     {'label': 'Highland Terra',     'color': '#5a4a3a', 'opacity': 0.3},
    'plains':    {'label': 'Plains',             'color': '#4a5a4a', 'opacity': 0.35},
    'basin':     {'label': 'Impact Basin',       'color': '#3a3a5a', 'opacity': 0.4},
    'crater':    {'label': 'Crater Material',    'color': '#6a6a6a', 'opacity': 0.2},
    'imbrium':   {'label': 'Imbrium Basin',      'color': '#2a4a6a', 'opacity': 0.45},
    'orientale': {'label': 'Orientale Basin',    'color': '#3a2a5a', 'opacity': 0.45},
}

# Classify each polygon
gdf['terrain'] = gdf['FIRST_Unit'].map(TERRAIN_MAP)
unmapped = gdf[gdf['terrain'].isna()]['FIRST_Unit'].unique()
if len(unmapped) > 0:
    print(f"WARNING: Unmapped units: {unmapped}")
    # Map anything unmapped to 'crater' as fallback
    gdf.loc[gdf['terrain'].isna(), 'terrain'] = 'crater'

print(f"\n=== Terrain Classification ===")
for t, count in gdf['terrain'].value_counts().items():
    print(f"  {t:12s}: {count:5d} polygons")

# === DISSOLVE BY TERRAIN TYPE + SIMPLIFY ===
# For each terrain type, we dissolve all polygons into one MultiPolygon,
# then simplify heavily for globe rendering

TOLERANCE = 30000  # meters in the projected CRS (30km tolerance)

regions = []
total_pts = 0

for terrain_type in sorted(TERRAIN_STYLES.keys()):
    subset = gdf[gdf['terrain'] == terrain_type]
    if len(subset) == 0:
        continue

    print(f"\nProcessing {terrain_type}: {len(subset)} polygons...", end='', flush=True)

    # Fix invalid geometries
    valid = [g.buffer(0) if (g is not None and not g.is_valid) else g
             for g in subset.geometry if g is not None]

    # Union all
    try:
        merged = unary_union(valid)
    except Exception as e:
        print(f" UNION ERROR: {e}")
        continue

    # Simplify
    simplified = merged.simplify(TOLERANCE, preserve_topology=True)

    # Convert to geographic coords (the CRS is equirectangular meters)
    # In this projection: x = lon * (pi/180) * R, y = lat * (pi/180) * R
    # R = 1737400m, so lon = x / (1737400 * pi/180) = x / 30319.4
    R_FACTOR = 1737400.0 * 3.14159265358979 / 180.0  # ~30319.4 m per degree

    # Extract coordinate rings and convert to lon/lat
    polys = []
    pts_count = [0]

    def extract_polys(geom):
        if geom.geom_type == 'Polygon':
            # Skip tiny polygons (< 1.0 sq degrees after conversion)
            if geom.area < (R_FACTOR * R_FACTOR * 1.0):
                return
            coords = list(geom.exterior.coords)
            if len(coords) >= 4:
                ring = [[round(c[0] / R_FACTOR, 1), round(c[1] / R_FACTOR, 1)] for c in coords]
                polys.append(ring)
                pts_count[0] += len(ring)
        elif geom.geom_type == 'MultiPolygon':
            for p in geom.geoms:
                extract_polys(p)

    extract_polys(simplified)
    pts_count = pts_count[0]

    total_pts += pts_count
    print(f" {len(polys)} polys, {pts_count:,} pts")

    regions.append({
        'type': terrain_type,
        'label': TERRAIN_STYLES[terrain_type]['label'],
        'color': TERRAIN_STYLES[terrain_type]['color'],
        'opacity': TERRAIN_STYLES[terrain_type]['opacity'],
        'polys': polys
    })

print(f"\n=== OUTPUT ===")
print(f"Total regions: {len(regions)}")
print(f"Total points: {total_pts:,}")

# Write JS
outpath = r'C:\Users\john_\dev\MarchogSystemsOps\client\pages\data\moon\moon_regions.js'
js = '// USGS Unified Geologic Map of the Moon — terrain regions for globe rendering\n'
js += '// Source: Fortezzo, Spudis & Harrel (2020) USGS SIM 3316 — Public Domain\n'
js += f'// {len(regions)} terrain types, {total_pts:,} coordinate points\n'
js += '// Coordinate system: IAU Moon 2000, lon -180..180, lat -90..90\n\n'
js += 'const LUNA_TERRAIN_STYLES = ' + json.dumps(TERRAIN_STYLES, indent=2) + ';\n\n'
js += 'const LUNA_REGIONS = ' + json.dumps(regions, separators=(',', ':')) + ';\n'

with open(outpath, 'w', encoding='utf-8') as f:
    f.write(js)

fsize = os.path.getsize(outpath)
print(f"File: {outpath}")
print(f"Size: {fsize:,} bytes ({fsize/1024:.1f} KB)")
