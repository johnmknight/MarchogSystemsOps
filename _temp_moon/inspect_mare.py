"""
Process LROC mare boundary polygons into compact JS for globe rendering.
"""
import geopandas as gpd
import zipfile, os, json, sys
sys.stdout.reconfigure(encoding='utf-8')

zpath = r'C:\Users\john_\Downloads\LROC_GLOBAL_MARE_180.ZIP'
extract_dir = r'C:\Users\john_\dev\MarchogSystemsOps\_temp_moon\mare'
os.makedirs(extract_dir, exist_ok=True)

with zipfile.ZipFile(zpath, 'r') as z:
    z.extractall(extract_dir)
    print("Extracted:", z.namelist())

# Find the shapefile
shps = []
for root, dirs, files in os.walk(extract_dir):
    for f in files:
        if f.lower().endswith('.shp'):
            shps.append(os.path.join(root, f))
print("Shapefiles:", shps)

gdf = gpd.read_file(shps[0])
print(f"\nTotal polygons: {len(gdf)}")
print(f"Columns: {list(gdf.columns)}")
print(f"CRS: {gdf.crs}")
print(f"\nSample rows:")
for _, r in gdf.head(10).iterrows():
    name = r.get('MARE_NAME', r.get('NAME', 'unnamed'))
    area = r.get('AREA_KM2', r.get('AREA', '?'))
    geom_type = r.geometry.geom_type
    if hasattr(r.geometry, 'exterior'):
        npts = len(r.geometry.exterior.coords)
    elif geom_type == 'MultiPolygon':
        npts = sum(len(p.exterior.coords) for p in r.geometry.geoms)
    else:
        npts = 0
    print(f"  {name:35s} area={str(area):>12s}  type={geom_type:15s}  pts={npts}")

# Total points
total_pts = 0
for _, r in gdf.iterrows():
    g = r.geometry
    if g.geom_type == 'Polygon':
        total_pts += len(g.exterior.coords)
    elif g.geom_type == 'MultiPolygon':
        for p in g.geoms:
            total_pts += len(p.exterior.coords)
print(f"\nTotal coordinate points: {total_pts:,}")
