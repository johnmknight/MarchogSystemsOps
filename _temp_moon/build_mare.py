"""
Convert LROC mare boundary polygons to compact JS for Three.js globe rendering.
Simplifies geometry and groups by mare name for efficient rendering.
"""
import geopandas as gpd
import json, os, sys
from shapely.geometry import mapping
from shapely.ops import unary_union
sys.stdout.reconfigure(encoding='utf-8')

shp = r'C:\Users\john_\dev\MarchogSystemsOps\_temp_moon\mare\LROC_GLOBAL_MARE_180.SHP'
gdf = gpd.read_file(shp)

print(f"Input: {len(gdf)} polygons, ", end='')
total_in = sum(
    len(g.exterior.coords) if g.geom_type == 'Polygon' 
    else sum(len(p.exterior.coords) for p in g.geoms)
    for g in gdf.geometry
)
print(f"{total_in:,} points")

# Unique mare names
names = gdf['MARE_NAME'].unique()
print(f"Unique mare names: {len(names)}")

# Simplify tolerance (in degrees on Moon ~1737km radius)
# 0.05° ≈ 1.5km on Moon surface — good for globe view
TOLERANCE = 0.18

mare_polygons = []
total_out = 0

for name in sorted(names):
    subset = gdf[gdf['MARE_NAME'] == name]
    
    # Fix invalid geometries then union
    valid_geoms = [g.buffer(0) if not g.is_valid else g for g in subset.geometry]
    merged = unary_union(valid_geoms)
    
    # Simplify
    simplified = merged.simplify(TOLERANCE, preserve_topology=True)
    
    # Extract coordinate rings
    polys = []
    if simplified.geom_type == 'Polygon':
        geoms = [simplified]
    elif simplified.geom_type == 'MultiPolygon':
        geoms = list(simplified.geoms)
    else:
        continue
    
    for poly in geoms:
        coords = list(poly.exterior.coords)
        if len(coords) < 4:
            continue
        # Round to 2 decimal places (good enough for globe)
        ring = [[round(c[0], 2), round(c[1], 2)] for c in coords]
        polys.append(ring)
        total_out += len(ring)
    
    if polys:
        mare_polygons.append({
            'name': name,
            'polys': polys
        })

print(f"\nOutput: {len(mare_polygons)} named mare regions")
print(f"Total output points: {total_out:,}")
print(f"Reduction: {total_in:,} → {total_out:,} ({100*(1-total_out/total_in):.1f}%)")

# Show largest by point count
by_size = sorted(mare_polygons, key=lambda m: sum(len(p) for p in m['polys']), reverse=True)
print(f"\nLargest regions:")
for m in by_size[:15]:
    npts = sum(len(p) for p in m['polys'])
    npoly = len(m['polys'])
    print(f"  {m['name']:35s} {npoly:3d} polys  {npts:5d} pts")

# Write JS
outpath = r'C:\Users\john_\dev\MarchogSystemsOps\client\pages\data\moon\mare_boundaries.js'
js = '// LROC lunar mare boundary polygons (simplified for globe rendering)\n'
js += '// Source: LROC WAC basemap digitization (Nelson et al. 2014) - Public Domain\n'
js += f'// {len(mare_polygons)} named regions, {total_out:,} coordinate points\n'
js += f'// Simplified from {total_in:,} pts (tolerance={TOLERANCE}° ≈ {TOLERANCE*30:.1f}km)\n'
js += '// Coordinate system: IAU Moon 2000, lon -180..180, lat\n\n'

# Compact JSON - arrays of [lon, lat] per polygon ring
js += 'const LUNA_MARE_BOUNDARIES = ' + json.dumps(mare_polygons, separators=(',', ':')) + ';\n'

with open(outpath, 'w', encoding='utf-8') as f:
    f.write(js)

fsize = os.path.getsize(outpath)
print(f"\nFile: {outpath}")
print(f"Size: {fsize:,} bytes ({fsize/1024:.1f} KB)")
