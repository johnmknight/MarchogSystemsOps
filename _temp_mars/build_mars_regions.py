"""
Build mars_regions.js — synthetic region boundaries from nomenclature center points.
Since we don't have the 790MB USGS geologic shapefile, we generate approximate
circular/elliptical boundaries from the named regions' center coords + diameters.
These serve as selectable regions on the globe until real polygon data is available.
"""
import json, os, sys, math
sys.stdout.reconfigure(encoding='utf-8')

# Load the features we already extracted
with open(r'C:\Users\john_\dev\MarchogSystemsOps\client\pages\data\mars\mars_data.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.index('const MARS_FEATURES = ')
data = json.loads(text[idx + 22:].rstrip().rstrip(';'))

# Get all regions
regions = [f for f in data if f['category'] == 'region']
print(f"Regions to process: {len(regions)}")

# Generate approximate polygon boundaries as circles (in lat/lon)
# For each region, create a polygon with N vertices approximating the area
def make_region_poly(lat, lon, diameter_km, n_points=32):
    """Generate approximate circular boundary in lat/lon degrees."""
    # Mars radius: 3389.5 km
    R = 3389.5
    radius_deg_lat = (diameter_km / 2) / (R * math.pi / 180)
    # Longitude degrees vary with latitude
    cos_lat = math.cos(math.radians(lat)) if abs(lat) < 89 else 0.02
    radius_deg_lon = radius_deg_lat / cos_lat

    # Clamp to reasonable bounds
    radius_deg_lon = min(radius_deg_lon, 90)

    coords = []
    for i in range(n_points):
        angle = 2 * math.pi * i / n_points
        dlat = radius_deg_lat * math.sin(angle)
        dlon = radius_deg_lon * math.cos(angle)
        plat = round(max(-90, min(90, lat + dlat)), 1)
        plon = round(lon + dlon, 1)
        # Wrap longitude to -180..180
        if plon > 180: plon -= 360
        if plon < -180: plon += 360
        coords.append([plon, plat])
    coords.append(coords[0])  # close ring
    return coords

# Terrain type classification based on feature type
TERRAIN_MAP = {
    'Planitia': {'label': 'Lowland Plains', 'color': '#1a3a2a', 'opacity': 0.5},
    'Vastitas': {'label': 'Vast Lowland', 'color': '#1a4a2a', 'opacity': 0.5},
    'Terra':    {'label': 'Highland Terra', 'color': '#5a3a2a', 'opacity': 0.4},
    'Planum':   {'label': 'Plateau', 'color': '#4a4a3a', 'opacity': 0.35},
    'Palus':    {'label': 'Swamp/Marsh', 'color': '#3a4a3a', 'opacity': 0.3},
}

mars_regions = []
total_pts = 0

for r in sorted(regions, key=lambda x: -x['diameter']):
    ftype = r['type']
    style = TERRAIN_MAP.get(ftype, {'label': ftype, 'color': '#4a4a4a', 'opacity': 0.3})

    # Vary polygon detail by size
    if r['diameter'] > 3000:
        n = 48
    elif r['diameter'] > 1000:
        n = 36
    else:
        n = 24

    poly = make_region_poly(r['lat'], r['lon'], r['diameter'], n)
    total_pts += len(poly)

    mars_regions.append({
        'name': r['name'],
        'type': ftype,
        'label': style['label'],
        'color': style['color'],
        'opacity': style['opacity'],
        'lat': r['lat'],
        'lon': r['lon'],
        'diameter': r['diameter'],
        'polys': [poly]
    })

print(f"Output: {len(mars_regions)} regions, {total_pts:,} pts")

# Write
outpath = r'C:\Users\john_\dev\MarchogSystemsOps\client\pages\data\mars\mars_regions.js'
js = '// Mars region boundaries (synthetic from nomenclature center pts + diameters)\n'
js += '// Source: USGS/IAU Gazetteer — approximated as circular boundaries\n'
js += '// Will be replaced with real USGS SIM 3292 polygons when available\n'
js += f'// {len(mars_regions)} regions, {total_pts:,} pts\n\n'

styles = {k: v for k, v in TERRAIN_MAP.items()}
js += 'const MARS_TERRAIN_STYLES = ' + json.dumps(styles, indent=2) + ';\n\n'
js += 'const MARS_REGIONS = ' + json.dumps(mars_regions, separators=(',', ':')) + ';\n'

with open(outpath, 'w', encoding='utf-8') as f:
    f.write(js)

fsize = os.path.getsize(outpath)
print(f"File: {outpath}")
print(f"Size: {fsize:,} bytes ({fsize/1024:.1f} KB)")

print(f"\nLargest regions:")
for r in mars_regions[:12]:
    print(f"  {r['name']:30s} {r['type']:10s} diam={r['diameter']:8.1f}km  lat={r['lat']:7.2f} lon={r['lon']:7.2f}")
