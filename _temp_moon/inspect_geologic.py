"""
Inspect USGS Unified Geologic Map of the Moon for highland/terrain polygons.
This gives us the full surface coverage beyond just mare boundaries.
"""
import zipfile, os, sys
sys.stdout.reconfigure(encoding='utf-8')

zpath = r'C:\Users\john_\Downloads\Unified_Geologic_Map_of_the_Moon_GIS_v2.zip'
extract_dir = r'C:\Users\john_\dev\MarchogSystemsOps\_temp_moon\geologic'
os.makedirs(extract_dir, exist_ok=True)

with zipfile.ZipFile(zpath, 'r') as z:
    z.extractall(extract_dir)
    flist = z.namelist()
    print(f"Extracted {len(flist)} files")
    for f in flist:
        print(f"  {f}")
