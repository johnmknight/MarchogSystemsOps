import geopandas as gpd
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

gdf = gpd.read_file(r'C:\Users\john_\dev\MarchogSystemsOps\_temp_moon\MOON_nomenclature_center_pts.shp')

print('=== Feature Types ===')
print(gdf['type'].value_counts().to_string())
print()

# Non-crater features
major = gdf[~gdf['type'].isin(['Crater, craters', 'Satellite Feature'])]
print(f'Non-crater features: {len(major)}')
print(major['type'].value_counts().to_string())
print()

# Maria
mare = gdf[gdf['type'] == 'Mare, maria']
print(f'=== Maria ({len(mare)}) ===')
for _, r in mare.iterrows():
    n = r['name']
    print(f'  {n:30s} lat={r["center_lat"]:7.2f} lon={r["center_lon"]:7.2f} diam={r["diameter"]:8.1f}km')

# Mons
mons = gdf[gdf['type'].str.contains('Mons', na=False)]
print(f'\n=== Mons ({len(mons)}) ===')
for _, r in mons.head(15).iterrows():
    n = r['name']
    print(f'  {n:30s} lat={r["center_lat"]:7.2f} lon={r["center_lon"]:7.2f} diam={r["diameter"]:8.1f}km')

# Vallis
vallis = gdf[gdf['type'].str.contains('Vallis', na=False)]
print(f'\n=== Vallis ({len(vallis)}) ===')
for _, r in vallis.iterrows():
    n = r['name']
    print(f'  {n:30s} lat={r["center_lat"]:7.2f} lon={r["center_lon"]:7.2f} diam={r["diameter"]:8.1f}km')
