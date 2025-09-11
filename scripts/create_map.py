#!/usr/bin/env python3
import geopandas as gpd
import folium
from pathlib import Path
import sys
from shapely.geometry import Polygon, MultiPolygon

def create_map(state, district):
    """Create map with seamless county name labels"""
    
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
    
    # Add banner
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
                           font-family: Arial, sans-serif;
                           font-weight: bold;">
                Placeholder - Placeholder
                </div>
                '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    district_geom = district_gdf.geometry.iloc[0]
    
    # Process counties with geometry cleaning
    if counties_gdf is not None:
        for idx, county_row in counties_gdf.iterrows():
            county_geom = county_row['geometry']
            intersection = county_geom.intersection(district_geom)
            
            if not intersection.is_empty and intersection.area > 0.0001:
                # Clean geometry to prevent markers
                clean_geom = None
                if intersection.geom_type == 'Polygon':
                    clean_geom = intersection
                elif intersection.geom_type == 'MultiPolygon':
                    clean_geom = intersection
                elif intersection.geom_type == 'GeometryCollection':
                    polygons = [geom for geom in intersection.geoms 
                               if geom.geom_type in ['Polygon', 'MultiPolygon']]
                    if polygons:
                        clean_geom = polygons[0] if len(polygons) == 1 else MultiPolygon(polygons)
                
                if clean_geom and not clean_geom.is_empty:
                    # Add county with lighter blue shade
                    folium.GeoJson(
                        clean_geom,
                        style_function=lambda x: {
                            'fillColor': '#F8FFFF',
                            'color': '#0000FF',
                            'weight': 1,
                            'fillOpacity': 0.7,
                            'opacity': 0.8
                        }
                    ).add_to(m)
                    
                    # Add county name label with seamless styling
                    county_name = county_row.get('NAME', 'Unknown')
                    
                    # Special positioning for Bath county - move to red circle area
                    if county_name == 'Bath':
                        label_lat = 38.125  # Moved south into the red circle area
                        label_lon = -83.68
                    else:
                        # Use centroid for other counties
                        county_centroid = clean_geom.centroid
                        label_lat = county_centroid.y
                        label_lon = county_centroid.x
                    
                    folium.Marker(
                        location=[label_lat, label_lon],
                        icon=folium.DivIcon(
                            html=f'<div style="font-size: 10px; color: #000080; font-weight: bold; text-align: center; background: none; padding: 0; border: none; text-shadow: 1px 1px 2px rgba(255,255,255,0.7);">{county_name}</div>',
                            class_name='county-label',
                            icon_size=(len(county_name) * 6, 16),
                            icon_anchor=(len(county_name) * 3, 8)
                        )
                    ).add_to(m)
    
    # Add district boundary on top
    folium.GeoJson(
        district_gdf,
        style_function=lambda x: {
            'fillColor': 'transparent',
            'color': '#0000FF',
            'weight': 4,
            'fillOpacity': 0,
            'opacity': 1.0
        }
    ).add_to(m)
    
    # Fit bounds
    m.fit_bounds(
        [[bounds[1], bounds[0]], [bounds[3], bounds[2]]], 
        padding=[20, 20]
    )
    
    # Save
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    map_path = output_dir / 'cd6_map_base.html'
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
