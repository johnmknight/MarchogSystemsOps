"""
Build mars_data.js — geological features + simulated environmental data for Mars.
"""
import geopandas as gpd
import zipfile, json, os, sys, random
sys.stdout.reconfigure(encoding='utf-8')

zpath = r'C:\Users\john_\Downloads\MARS_nomenclature_center_pts.zip'
extract_dir = r'C:\Users\john_\dev\MarchogSystemsOps\_temp_mars\raw'
os.makedirs(extract_dir, exist_ok=True)
with zipfile.ZipFile(zpath, 'r') as z:
    z.extractall(extract_dir)
shps = [os.path.join(extract_dir, f) for f in os.listdir(extract_dir) if f.lower().endswith('.shp')]
gdf = gpd.read_file(shps[0])

features = []
region_types = [
    'Planitia, planitiae', 'Terra, terrae', 'Planum, plana',
    'Vastitas, vastitates', 'Palus, paludes',
]
landmark_types = [
    'Mons, montes', 'Tholus, tholi', 'Patera, paterae',
    'Chasma, chasmata', 'Vallis, valles', 'Fossa, fossae',
    'Labyrinthus, labyrinthi', 'Chaos, chaoses',
    'Rupes, rupēs', 'Dorsum, dorsa', 'Mensa, mensae',
    'Sulcus, sulci', 'Catena, catenae', 'Collis, colles',
    'Fluctus, fluctūs', 'Scopulus, scopuli', 'Cavus, cavi',
]

for _, r in gdf[gdf['type'].isin(region_types)].iterrows():
    features.append({
        'name': r['name'], 'type': r['type'].split(',')[0].strip(),
        'lat': round(r['center_lat'], 2), 'lon': round(r['center_lon'], 2),
        'diameter': round(r['diameter'], 1), 'category': 'region'
    })
for _, r in gdf[gdf['type'].isin(landmark_types)].iterrows():
    features.append({
        'name': r['name'], 'type': r['type'].split(',')[0].strip(),
        'lat': round(r['center_lat'], 2), 'lon': round(r['center_lon'], 2),
        'diameter': round(r['diameter'], 1), 'category': 'landmark'
    })
big_craters = gdf[(gdf['type'] == 'Crater, craters') & (gdf['diameter'] > 100)]
for _, r in big_craters.iterrows():
    features.append({
        'name': r['name'], 'type': 'Crater',
        'lat': round(r['center_lat'], 2), 'lon': round(r['center_lon'], 2),
        'diameter': round(r['diameter'], 1), 'category': 'crater'
    })

print(f"Features: {len(features)}")
print(f"  Regions: {sum(1 for f in features if f['category']=='region')}")
print(f"  Landmarks: {sum(1 for f in features if f['category']=='landmark')}")
print(f"  Craters >100km: {sum(1 for f in features if f['category']=='crater')}")

# === MARS ENVIRONMENT GENERATOR ===
def gen_mars_env(lat, lon, name, ftype, diam):
    random.seed(hash(name))
    abs_lat = abs(lat)
    is_low = ftype in ['Planitia', 'Vastitas'] or 'Hellas' in name
    solar_angle = ((lon + 180) % 360) / 360
    is_day = 0.25 < solar_angle < 0.75

    # Temperature
    if abs_lat > 60:
        t = -100 + random.uniform(-25, 15)
    elif is_day:
        eq = 1.0 - (abs_lat / 90)
        t = -30 + (50 * eq) + (10 if is_low else 0) + random.uniform(-15, 10)
    else:
        t = -80 + (20 * (1.0 - abs_lat/90)) + random.uniform(-15, 5)

    # Pressure (mbar)
    if is_low: p = 8.0 + random.uniform(0, 4)
    elif ftype in ['Mons', 'Tholus']: p = 0.5 + random.uniform(0, 2)
    elif ftype in ['Planum', 'Terra']: p = 4.0 + random.uniform(0, 3)
    else: p = 5.0 + random.uniform(0, 3)

    wind = round(5 + random.uniform(0, 20), 1)
    wind_dir = random.choice(['N','NE','E','SE','S','SW','W','NW'])
    dust = round(0.2 + random.uniform(0, 0.8), 2)
    uv = round(10 + random.uniform(0, 8), 1) if is_day else 0
    rad = round(0.5 + random.uniform(0, 0.4), 2)
    pwv = round(5 + random.uniform(0, 30), 1)
    ls = round(random.uniform(0, 360), 1)
    seasons = ['Spring','Summer','Autumn','Winter']
    season = seasons[int(ls / 90)]

    return {
        'surface_temp_c': round(t, 1), 'pressure_mbar': round(p, 2),
        'wind_speed_ms': wind, 'wind_direction': wind_dir,
        'dust_opacity_tau': dust, 'uv_index': uv,
        'radiation_msv_day': rad, 'precip_water_um': pwv,
        'sky_color': 'butterscotch' if dust > 0.5 else 'salmon-pink',
        'solar_longitude_ls': ls, 'season_nh': season,
        'co2_frost': abs_lat > 50 and season in ['Autumn','Winter'],
        'is_dayside': is_day
    }

for f in features:
    f['env'] = gen_mars_env(f['lat'], f['lon'], f['name'], f['type'], f['diameter'])

# === REFERENCE + OUTPUT ===
mars_ref = {
    'body': 'Mars', 'body_code': 'mars', 'radius_km': 3389.5,
    'gravity_ms2': 3.721,
    'atmosphere': '6.1 mbar avg (95.3% CO2, 2.7% N2, 1.6% Ar)',
    'axial_tilt_deg': 25.19, 'year_earth_days': 687, 'sol_hours': 24.66,
    'magnetic_field': 'None (localized crustal remnants)',
    'temp_range_c': [-153, 20], 'temp_avg_c': -60,
    'data_sources': [
        'NASA InSight Lander meteorology',
        'MSL Curiosity REMS weather station',
        'Mars Climate Database (LMD)',
        'USGS Gazetteer of Planetary Nomenclature'
    ]
}

outdir = r'C:\Users\john_\dev\MarchogSystemsOps\client\pages\data\mars'
os.makedirs(outdir, exist_ok=True)

js = '// Mars geological features + simulated environmental data\n'
js += '// Source: USGS/IAU Gazetteer of Planetary Nomenclature (public domain)\n'
js += '// Environmental data is SIMULATED based on real Mars science parameters\n'
js += f'// Generated: 2026-02-23 | Features: {len(features)}\n\n'
js += 'const MARS_REFERENCE = ' + json.dumps(mars_ref, indent=2) + ';\n\n'
js += 'const MARS_FEATURES = ' + json.dumps(features, separators=(',', ':')) + ';\n'

outpath = os.path.join(outdir, 'mars_data.js')
with open(outpath, 'w', encoding='utf-8') as f:
    f.write(js)

fsize = os.path.getsize(outpath)
print(f"\nOutput: {outpath}")
print(f"Size: {fsize:,} bytes ({fsize/1024:.1f} KB)")

print(f"\nSample regions:")
for f in sorted([x for x in features if x['category']=='region'], key=lambda x: -x['diameter'])[:10]:
    e = f['env']
    t, p, w = e['surface_temp_c'], e['pressure_mbar'], e['wind_speed_ms']
    print(f"  {f['name']:30s} {t:6.1f}C {p:5.2f}mbar wind={w}m/s dust={e['dust_opacity_tau']}")
