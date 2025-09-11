#!/usr/bin/env python3
import geopandas as gpd
import folium
from pathlib import Path
import sys

def create_map(state, district):
    """Create mobile-first map from local GeoJSON files with custom styling"""
    
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
    
    # Create mobile-first map
    m = folium.Map(
        location=[center_lat, center_lon], 
        zoom_start=9,
        tiles='OpenStreetMap',
        width='100%',
        height='100vh',  # Full viewport height for mobile
        zoom_control=True,
        scrollWheelZoom=True,
        dragging=True
    )
    
    # Add custom mobile-optimized header
    title_html = '''
                <div style="position: fixed; 
                           top: 10px; 
                           left: 50%; 
                           transform: translateX(-50%);
                           width: 90%;
                           z-index: 9999; 
                           font-size: 18px;
                           background-color: rgba(255,255,255,0.9);
                           padding: 8px 15px;
                           border-radius: 5px;
                           box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                           text-align: center;
                           font-family: Arial, sans-serif;">
                <b>Placeholder - Placeholder</b>
                </div>
                '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add background layer for areas outside district (light grey)
    # Create a large bounding box around the district
    padding = 0.5  # degrees
    background_bounds = [
        [bounds[1] - padding, bounds[0] - padding],  # southwest
        [bounds[1] - padding, bounds[2] + padding],  # southeast  
        [bounds[3] + padding, bounds[2] + padding],  # northeast
        [bounds[3] + padding, bounds[0] - padding],  # northwest
        [bounds[1] - padding, bounds[0] - padding]   # close polygon
    ]
    
    folium.Polygon(
        locations=background_bounds,
        color='#E8E8E8',
        weight=0,
        fillColor='#F5F5F5',  # Very light grey
        fillOpacity=0.3,
        popup="Outside District Area"
    ).add_to(m)
    
    # Add counties first (so they appear under district boundary)
    if counties_gdf is not None:
        folium.GeoJson(
            counties_gdf,
            style_function=lambda x: {
                'fillColor': '#F0FFFF',      # Alice Blue fill
                'color': '#0000FF',          # Blue border
                'weight': 1,                 # Thinner lines for counties
                'fillOpacity': 0.7,
                'opacity': 0.8
            },
            tooltip=folium.Tooltip(
                fields=['NAME'], 
                aliases=['County:'],
                style="background-color: white; color: #333; font-family: arial; font-size: 14px; padding: 8px; border-radius: 3px;"
            )
        ).add_to(m)
    
    # Add district boundary on top with thicker border
    folium.GeoJson(
        district_gdf,
        style_function=lambda x: {
            'fillColor': '#F0FFFF',          # Alice Blue fill
            'color': '#0000FF',              # Blue border
            'weight': 4,                     # Thicker line for district boundary
            'fillOpacity': 0.3,              # Lower opacity so counties show through
            'opacity': 1.0
        },
        popup=folium.Popup(
            f"{state} Congressional District {district}",
            max_width=250  # Smaller for mobile
        )
    ).add_to(m)
    
    # Mobile-optimized controls
    folium.plugins.Fullscreen(
        position='topright',
        title='Fullscreen',
        title_cancel='Exit Fullscreen',
        force_separate_button=True
    ).add_to(m)
    
    # Fit bounds to district with mobile-friendly padding
    m.fit_bounds(
        [[bounds[1], bounds[0]], [bounds[3], bounds[2]]], 
        padding=[20, 20]  # Mobile-friendly padding
    )
    
    # Save map
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    map_path = output_dir / f'{state}_{district:02d}_map.html'
    m.save(str(map_path))
    
    print(f"Mobile-first map created: {map_path}")
    return True

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python scripts/create_map.py STATE DISTRICT")
        sys.exit(1)
    
    state = sys.argv[1]
    district = int(sys.argv[2])
    create_map(state, district)
