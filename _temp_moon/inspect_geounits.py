"""
Inspect USGS Unified Geologic Map GeoUnits shapefile.
This has full surface coverage — highland terrains, crater fills, volcanic units, etc.
"""
import geopandas as gpd
import sys
sys.stdout.reconfigure(encoding='utf-8')

shp_dir = r'C:\Users\john_\dev\MarchogSystemsOps\_temp_moon\geologic\Unified_Geologic_Map_of_the_Moon_GIS\Lunar_GIS\Shapefiles'

# GeoUnits - the main geologic polygon layer
gdf = gpd.read_file(f'{shp_dir}\\GeoUnits.shp')
print(f"=== GeoUnits ===")
print(f"Total polygons: {len(gdf)}")
print(f"Columns: {list(gdf.columns)}")
print(f"CRS: {gdf.crs}")
print()

# Show unique unit types/codes
for col in ['UnitSymbol', 'UnitName', 'GeoUnit', 'Description', 'Age']:
    if col in gdf.columns:
        uvals = gdf[col].nunique()
        print(f"  {col}: {uvals} unique values")
        print(f"    Top 20: {gdf[col].value_counts().head(20).to_string()}")
        print()

# Total points
total_pts = 0
for g in gdf.geometry:
    if g is None:
        continue
    if g.geom_type == 'Polygon':
        total_pts += len(g.exterior.coords)
    elif g.geom_type == 'MultiPolygon':
        for p in g.geoms:
            total_pts += len(p.exterior.coords)
print(f"Total coordinate points: {total_pts:,}")

# Also read the color CSV
import csv, os
color_csv = os.path.join(shp_dir, '..', 'Symbol_LayerDefinitions', 'GeologyUnit_colors.csv')
if os.path.exists(color_csv):
    print(f"\n=== Color Reference ===")
    with open(color_csv, 'r') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i < 25:
                print(f"  {row}")
