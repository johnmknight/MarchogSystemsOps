import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'C:\Users\john_\dev\MarchogSystemsOps\client\pages\data\moon\moon_regions.js', 'r') as f:
    text = f.read()
idx = text.index('const LUNA_REGIONS = ')
data = json.loads(text[idx+20:].rstrip().rstrip(';'))
for r in data:
    all_lons = [c[0] for p in r['polys'] for c in p]
    all_lats = [c[1] for p in r['polys'] for c in p]
    t = r['type']
    lb = r['label']
    np = len(r['polys'])
    lo_min, lo_max = min(all_lons), max(all_lons)
    la_min, la_max = min(all_lats), max(all_lats)
    print(f"  {t:12s} {lb:25s} {np:4d} polys  lon=[{lo_min:7.1f},{lo_max:6.1f}]  lat=[{la_min:7.1f},{la_max:6.1f}]")
