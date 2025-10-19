#!/usr/bin/env python3
"""
Create accurate GeoJSON files from US Census TIGER shapefiles.
This creates the correct District 6 boundary and filtered county boundaries.
"""

import geopandas as gpd
import json

print("="*70)
print("CREATING ACCURATE GEOJSON FILES FROM TIGER SHAPEFILES")
print("="*70)

# Load Congressional Districts for Kentucky
print("\n1. Loading Congressional Districts...")
cd_file = 'tl_2024_21_cd119/tl_2024_21_cd119.shp'
cds = gpd.read_file(cd_file)

# Get District 6
district6 = cds[cds['CD119FP'] == '06']
print(f"   Found District 6: {district6['NAMELSAD'].values[0]}")

# Convert to GeoJSON and save
district6_geojson = district6.to_crs('EPSG:4326')  # Convert to WGS84 for web mapping
district6_geojson.to_file('ky_6th_congressional_district_accurate.geojson', driver='GeoJSON')
print(f"   ✓ Saved: ky_6th_congressional_district_accurate.geojson")

# Load all US counties
print("\n2. Loading Kentucky counties...")
county_file = 'tl_2024_us_county/tl_2024_us_county.shp'
counties = gpd.read_file(county_file)

# Filter to Kentucky counties only (STATEFP = '21')
ky_counties = counties[counties['STATEFP'] == '21'].copy()
print(f"   Total Kentucky counties: {len(ky_counties)}")

# Ensure same CRS for spatial analysis
if district6.crs != ky_counties.crs:
    district6_analysis = district6.to_crs(ky_counties.crs)
else:
    district6_analysis = district6

# Find counties in District 6 (≥45% overlap to catch partial counties)
print("\n3. Filtering counties in District 6...")
counties_in_district = []

for idx, county in ky_counties.iterrows():
    county_geom = county.geometry
    county_name = county['NAME']

    if district6_analysis.geometry.values[0].intersects(county_geom):
        intersection = district6_analysis.geometry.values[0].intersection(county_geom)
        county_area = county_geom.area
        intersection_area = intersection.area
        overlap_pct = (intersection_area / county_area) * 100 if county_area > 0 else 0

        # Include if ≥45% overlap (catches both full and partial counties)
        if overlap_pct >= 45.0:
            counties_in_district.append(idx)
            status = "PARTIAL" if overlap_pct < 90 else "FULL"
            print(f"   ✓ {county_name:20s} ({overlap_pct:5.1f}%) [{status}]")

# Create filtered county GeoDataFrame
filtered_counties = ky_counties.loc[counties_in_district].copy()

# Convert to WGS84 and save
filtered_counties_geojson = filtered_counties.to_crs('EPSG:4326')
filtered_counties_geojson.to_file('ky_district6_counties_accurate.geojson', driver='GeoJSON')

print(f"\n   ✓ Saved: ky_district6_counties_accurate.geojson")
print(f"   Total counties: {len(filtered_counties)}")

print("\n" + "="*70)
print("SUCCESS - Accurate GeoJSON files created!")
print("="*70)
print("\nFiles created:")
print("  - ky_6th_congressional_district_accurate.geojson")
print("  - ky_district6_counties_accurate.geojson")
