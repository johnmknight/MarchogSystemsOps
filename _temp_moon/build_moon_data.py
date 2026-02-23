"""
Generate moon_data.js for MarchogSystemsOps weather page.
Extracts major geological features from USGS nomenclature shapefile.
Creates fake weather/environment data based on real lunar science.
"""
import geopandas as gpd
import json, os, sys, math, random
sys.stdout.reconfigure(encoding='utf-8')

gdf = gpd.read_file(r'C:\Users\john_\dev\MarchogSystemsOps\_temp_moon\MOON_nomenclature_center_pts.shp')

# === FEATURE EXTRACTION ===
# We want: Maria, Oceanus, Lacus, Sinus, Palus, Mons/Montes, Vallis, major craters, Rima, Rupes
features = []

# Priority feature types (like "states" on Earth)
region_types = [
    'Mare, maria', 'Oceanus, oceani', 'Lacus, lacūs', 'Sinus, sinūs',
    'Palus, paludes', 'Planitia, planitiae'
]

landmark_types = [
    'Mons, montes', 'Vallis, valles', 'Rupes, rupēs',
    'Promontorium, promontoria', 'Dorsum, dorsa', 'Rima, rimae',
    'Catena, catenae', 'Statio'
]

# Extract regions (maria, lacus, etc) - these are selectable like states
for _, r in gdf[gdf['type'].isin(region_types)].iterrows():
    features.append({
        'name': r['name'],
        'type': r['type'].split(',')[0].strip(),
        'lat': round(r['center_lat'], 2),
        'lon': round(r['center_lon'], 2),
        'diameter': round(r['diameter'], 1),
        'category': 'region'
    })

# Extract landmarks (mons, vallis, etc) - displayed as markers
for _, r in gdf[gdf['type'].isin(landmark_types)].iterrows():
    features.append({
        'name': r['name'],
        'type': r['type'].split(',')[0].strip(),
        'lat': round(r['center_lat'], 2),
        'lon': round(r['center_lon'], 2),
        'diameter': round(r['diameter'], 1),
        'category': 'landmark'
    })

# Major craters only (diameter > 100km)
big_craters = gdf[(gdf['type'] == 'Crater, craters') & (gdf['diameter'] > 100)]
for _, r in big_craters.iterrows():
    features.append({
        'name': r['name'],
        'type': 'Crater',
        'lat': round(r['center_lat'], 2),
        'lon': round(r['center_lon'], 2),
        'diameter': round(r['diameter'], 1),
        'category': 'crater'
    })

print(f"Total features: {len(features)}")
print(f"  Regions: {sum(1 for f in features if f['category']=='region')}")
print(f"  Landmarks: {sum(1 for f in features if f['category']=='landmark')}")
print(f"  Major craters: {sum(1 for f in features if f['category']=='crater')}")

# === FAKE WEATHER DATA GENERATION ===
# Based on real lunar science:
# - Equatorial day: ~127°C (400K), night: ~-173°C (100K)
# - Polar: ~-30°C to -238°C
# - PSR (permanently shadowed): -238°C to -248°C
# - Lunar day/night cycle: ~29.5 Earth days
# - No atmosphere: 3×10^-15 atm
# - Solar wind: ~400 km/s
# - Micrometeorite flux, radiation, regolith charge

def generate_lunar_env(lat, lon, name, feature_type):
    """Generate realistic fake environmental data for a lunar location."""
    abs_lat = abs(lat)
    random.seed(hash(name))  # Deterministic per feature

    # Temperature model based on latitude and time
    # Assume current solar angle based on longitude
    solar_angle = (lon % 360) / 360  # 0-1 around the moon
    is_dayside = 0.25 < solar_angle < 0.75

    if abs_lat > 80:
        # Polar regions
        base_temp = -50
        if feature_type == 'Crater' and abs_lat > 85:
            # PSR candidate
            base_temp = -238 + random.uniform(0, 20)
            is_dayside = False
        else:
            base_temp = -30 + random.uniform(-40, 10)
    elif is_dayside:
        # Dayside temperature varies with latitude
        equator_factor = 1.0 - (abs_lat / 90)
        base_temp = -20 + (147 * equator_factor)  # up to 127°C at equator
        base_temp += random.uniform(-15, 15)
    else:
        # Nightside
        equator_factor = 1.0 - (abs_lat / 90)
        base_temp = -173 + (30 * equator_factor)
        base_temp += random.uniform(-10, 10)

    surface_temp = round(base_temp, 1)

    # Subsurface temp (35cm depth): ~40-45K warmer than surface
    subsurface_temp = round(surface_temp + random.uniform(35, 50), 1)

    # Solar wind speed (always present, varies with solar activity)
    solar_wind = round(350 + random.uniform(0, 150), 0)

    # Radiation (mSv/day) - no atmosphere protection
    # ~1.37 mSv/day average from GCR, spikes during solar events
    radiation = round(1.0 + random.uniform(0, 0.8), 2)

    # Regolith electrostatic charge (from UV/solar wind)
    if is_dayside:
        static_charge = round(random.uniform(5, 20), 1)  # +V dayside
    else:
        static_charge = round(random.uniform(-100, -500), 0)  # -V nightside (electron buildup)

    # Micrometeorite flux (impacts/m2/year) - background rate
    micro_flux = round(random.uniform(0.001, 0.005), 4)

    # Exosphere density (particles/cm3) - varies by species
    exo_density = round(random.uniform(20000, 100000), 0)

    # Illumination percentage
    if abs_lat > 85:
        illumination = round(random.uniform(0, 40), 0)
    elif is_dayside:
        illumination = round(70 + random.uniform(0, 30), 0)
    else:
        illumination = 0

    # Lunar phase day (0-29.5 day cycle)
    phase_day = round(random.uniform(0, 29.5), 1)

    return {
        'surface_temp_c': surface_temp,
        'subsurface_temp_c': subsurface_temp,
        'solar_wind_kms': int(solar_wind),
        'radiation_msv_day': radiation,
        'static_charge_v': static_charge,
        'micrometeorite_flux': micro_flux,
        'exosphere_density': int(exo_density),
        'illumination_pct': int(illumination),
        'phase_day': phase_day,
        'is_dayside': is_dayside,
        'regolith_depth_m': round(random.uniform(2, 15), 1)
    }

# Generate env data for all features
for f in features:
    f['env'] = generate_lunar_env(f['lat'], f['lon'], f['name'], f['type'])

# === OUTPUT JS FILE ===
outdir = r'C:\Users\john_\dev\MarchogSystemsOps\client\pages\data\moon'
os.makedirs(outdir, exist_ok=True)

# Lunar temperature reference data
temp_reference = {
    'equatorial_day_max_c': 127,
    'equatorial_night_min_c': -173,
    'polar_avg_c': -30,
    'psr_min_c': -248,
    'subsurface_offset_c': 42,
    'day_night_cycle_earth_days': 29.53,
    'body': 'Moon',
    'body_code': 'luna',
    'radius_km': 1737.4,
    'gravity_ms2': 1.625,
    'atmosphere': '3e-15 atm (virtual vacuum)',
    'magnetic_field': 'None (localized anomalies only)',
    'data_sources': [
        'NASA LRO Diviner Lunar Radiometer',
        'USGS Gazetteer of Planetary Nomenclature',
        'Apollo 15/17 heat flow measurements'
    ]
}

js_content = '// Moon geological features + simulated environmental data\n'
js_content += '// Source: USGS/IAU Gazetteer of Planetary Nomenclature (public domain)\n'
js_content += '// Environmental data is SIMULATED based on real lunar science parameters\n'
js_content += f'// Generated: 2026-02-23 | Features: {len(features)}\n\n'
js_content += 'const LUNA_REFERENCE = ' + json.dumps(temp_reference, indent=2) + ';\n\n'
js_content += 'const LUNA_FEATURES = ' + json.dumps(features, separators=(',', ':')) + ';\n'

outpath = os.path.join(outdir, 'moon_data.js')
with open(outpath, 'w', encoding='utf-8') as f:
    f.write(js_content)

fsize = os.path.getsize(outpath)
print(f"\nOutput: {outpath}")
print(f"File size: {fsize:,} bytes ({fsize/1024:.1f} KB)")
print(f"\nRegion examples:")
for f in [x for x in features if x['category']=='region'][:5]:
    e = f['env']
    print(f"  {f['name']:30s} {e['surface_temp_c']:7.1f}°C  illum={e['illumination_pct']}%  solar_wind={e['solar_wind_kms']}km/s")
