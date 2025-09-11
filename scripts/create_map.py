#!/usr/bin/env python3
import requests
import csv
from io import StringIO
import time
import geopandas as gpd
import folium
from pathlib import Path
import sys
from shapely.geometry import Polygon, MultiPolygon

def create_map(state, district):
    """Create map with seamless county name labels and coffee shop overlay"""
    
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
    
    # ADD COFFEE SHOP OVERLAY
    print("\n" + "="*50)
    print("ADDING COFFEE SHOP OVERLAY")
    print("="*50)
    
    # CSV URL for coffee shop data
    coffee_csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgl9hpVPQCUYunDuY2KGEI6yaZSCtGkGHo0Srn3PJ87gGCYikH1_OKuf2y6TXM6iXMj61edVmICkBu/pub?output=csv"
    
    # Fetch coffee shop data
    coffee_shops = fetch_coffee_shops(coffee_csv_url)
    
    if coffee_shops:
        # Add coffee shop markers to the map
        markers_added = add_coffee_shop_markers(m, coffee_shops)
        print(f"\n🎉 Coffee shop overlay complete! Added {markers_added} markers to the map.")
    else:
        print("❌ No coffee shop data found or error occurred")
    
    # Fit bounds
    m.fit_bounds(
        [[bounds[1], bounds[0]], [bounds[3], bounds[2]]], 
        padding=[20, 20]
    )
    
    # Save
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    map_path = output_dir / 'cd6_map_with_coffee_shops.html'
    m.save(str(map_path))
    
    print(f"Map created: {map_path}")
    return True


def fetch_coffee_shops(csv_url):
    """Fetch coffee shop data from Google Sheets CSV"""
    try:
        response = requests.get(csv_url)
        response.raise_for_status()
        
        # Parse CSV
        csv_reader = csv.reader(StringIO(response.text))
        rows = list(csv_reader)
        
        if not rows:
            print("No data found in CSV")
            return []
        
        # Skip header row
        coffee_shops = []
        for i, row in enumerate(rows[1:], 1):
            if len(row) >= 4:  # Ensure we have enough columns
                name = row[0].strip() if row[0] else f"Coffee Shop {i}"
                address1 = row[1].strip() if row[1] else ""
                address2 = row[2].strip() if row[2] else ""
                county = row[5].strip() if len(row) > 5 and row[5] else ""
                
                # Add first address if it exists
                if address1:
                    coffee_shops.append({
                        'name': name,
                        'address': address1,
                        'county': county,
                        'location_num': 1
                    })
                
                # Add second address if it exists (for shops with multiple locations)
                if address2:
                    coffee_shops.append({
                        'name': f"{name} (Location 2)",
                        'address': address2,
                        'county': county,
                        'location_num': 2
                    })
        
        print(f"Found {len(coffee_shops)} coffee shop locations")
        return coffee_shops
        
    except Exception as e:
        print(f"Error fetching coffee shop data: {e}")
        return []


def geocode_address(address):
    """Geocode an address using Nominatim (free OpenStreetMap service)"""
    if not address:
        return None
    
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': address,
        'format': 'json',
        'limit': 1,
        'countrycodes': 'us'  # Restrict to US addresses
    }
    
    try:
        # Add a small delay to be respectful to the free service
        time.sleep(1)
        
        response = requests.get(base_url, params=params, 
                              headers={'User-Agent': 'Congressional District Mapper'})
        response.raise_for_status()
        
        results = response.json()
        if results:
            lat = float(results[0]['lat'])
            lon = float(results[0]['lon'])
            return (lat, lon)
        else:
            print(f"Could not geocode address: {address}")
            return None
            
    except Exception as e:
        print(f"Geocoding error for '{address}': {e}")
        return None


def add_coffee_shop_markers(folium_map, coffee_shops):
    """Add coffee shop markers to the map"""
    successful_markers = 0
    failed_geocoding = []
    
    for shop in coffee_shops:
        print(f"Processing: {shop['name']} - {shop['address']}")
        
        # Skip if no address (mobile trucks)
        if not shop['address']:
            print(f"Skipping {shop['name']} - no address (mobile only)")
            continue
        
        # Geocode the address
        coordinates = geocode_address(shop['address'])
        
        if coordinates:
            lat, lon = coordinates
            
            # Create popup content
            popup_html = f"""
            <div style="font-family: Arial, sans-serif; min-width: 200px;">
                <h4 style="margin: 0 0 10px 0; color: #8B4513;">☕ {shop['name']}</h4>
                <p style="margin: 0; font-size: 12px; color: #666;">
                    <strong>Address:</strong><br>{shop['address']}
                </p>
                {f"<p style='margin: 5px 0 0 0; font-size: 11px; color: #888;'><strong>County:</strong> {shop['county']}</p>" if shop['county'] else ""}
            </div>
            """
            
            # Add marker with coffee emoji
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=shop['name'],
                icon=folium.DivIcon(
                    html=f"""
                    <div style="
                        font-size: 24px; 
                        text-align: center; 
                        line-height: 20px;
                        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
                    ">☕</div>
                    """,
                    icon_size=(30, 30),
                    icon_anchor=(15, 15)
                )
            ).add_to(folium_map)
            
            successful_markers += 1
            
        else:
            failed_geocoding.append(f"{shop['name']} - {shop['address']}")
    
    print(f"\nCoffee shop overlay complete:")
    print(f"✅ Successfully added {successful_markers} markers")
    
    if failed_geocoding:
        print(f"❌ Failed to geocode {len(failed_geocoding)} addresses:")
        for failed in failed_geocoding:
            print(f"   - {failed}")
    
    return successful_markers


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python scripts/create_map.py STATE DISTRICT")
        sys.exit(1)
    
    state = sys.argv[1]
    district = int(sys.argv[2])
    create_map(state, district)