#!/usr/bin/env python3
import geopandas as gpd
import folium
from pathlib import Path
import sys

def create_map(state, district):
    """Create map from local GeoJSON files"""
    
    # Load data
    data_dir = Path(f'data/processed/{state}_{district:02d}')
    district_file = data_dir / 'district_boundary.geojson'
    counties_file = data_dir / 'counties.geojson'
    
    if not district_file.exists():
        print(f"Error: {district_file} not found")
        return False
        
    district_gdf = gpd.read_file(district_file)
    counties_gdf = gpd.read_file(counties_file) if counties_file.exists() else None
    
    # Calculate center
    bounds = district_gdf.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    
    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=9)
    
    # Add district
    folium.GeoJson(
        district_gdf,
        style_function=lambda x: {
            'fillColor': '#ff6b6b', 'color': '#c92a2a',
            'weight': 3, 'fillOpacity': 0.3
        }
    ).add_to(m)
    
    # Add counties if available
    if counties_gdf is not None:
        folium.GeoJson(
            counties_gdf,
            style_function=lambda x: {
                'fillColor': '#4dabf7', 'color': '#1971c2',
                'weight': 1, 'fillOpacity': 0.1
            }
        ).add_to(m)
    
    # Save map
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    map_path = output_dir / f'{state}_{district:02d}_map.html'
    m.save(str(map_path))
    
    print(f"Map created: {map_path}")
    return True

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python scripts/create_map.py STATE DISTRICT")
        sys.exit(1)
    
    state = sys.argv[1]
    district = int(sys.argv[2])
    create_map(state, district)
