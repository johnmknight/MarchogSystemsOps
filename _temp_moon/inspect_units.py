"""
Decode the USGS geologic unit symbols and group by terrain type.
"""
import geopandas as gpd
import csv, sys
sys.stdout.reconfigure(encoding='utf-8')

shp_dir = r'C:\Users\john_\dev\MarchogSystemsOps\_temp_moon\geologic\Unified_Geologic_Map_of_the_Moon_GIS\Lunar_GIS\Shapefiles'
gdf = gpd.read_file(f'{shp_dir}\\GeoUnits.shp')

# Read descriptions CSV
desc_csv = shp_dir + r'\..\Symbol_LayerDefinitions\Unified_Geologic_Map_of_the_Moon_DOMU_descriptions.csv'
try:
    import pandas as pd
    desc = pd.read_csv(desc_csv, encoding='utf-8-sig')
    print("=== Description columns ===")
    print(list(desc.columns))
    print(f"Rows: {len(desc)}")
    print()
    for _, r in desc.head(40).iterrows():
        print(f"  {str(r.iloc[0]):8s} | {str(r.iloc[1])[:80]}")
except Exception as e:
    print(f"Error reading descriptions: {e}")

print()
print("=== Unit symbols in shapefile ===")
print(gdf['FIRST_Unit'].value_counts().head(40).to_string())
print()
print(f"Total unique units: {gdf['FIRST_Unit'].nunique()}")

# Check FIRST_Un_1 and FIRST_Un_2
print(f"\nFIRST_Un_1 sample: {gdf['FIRST_Un_1'].dropna().unique()[:10]}")
print(f"FIRST_Un_2 sample: {gdf['FIRST_Un_2'].dropna().unique()[:10]}")
