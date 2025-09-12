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

def create_map(state, district, icon_style="coffee_emoji"):
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
                CD 6 Coffee Shops
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
    
    # Debug: Show first coffee shop structure
    if coffee_shops:
        print(f"\nDEBUG: First coffee shop keys: {list(coffee_shops[0].keys())}")
        print(f"DEBUG: First coffee shop data: {coffee_shops[0]}")
    
    if coffee_shops:
        # Add coffee shop markers to the map
        markers_added = add_coffee_shop_markers(m, coffee_shops, icon_style)
        print(f"\n🎉 Coffee shop overlay complete! Added {markers_added} markers to the map.")
    else:
        print("❌ No coffee shop data found or error occurred")
    
    # Fit bounds
    m.fit_bounds(
        [[bounds[1], bounds[0]], [bounds[3], bounds[2]]], 
        padding=[20, 20]
    )
    
    # Save main map
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    map_path = output_dir / f'cd6_map_with_coffee_shops_{icon_style}.html'
    m.save(str(map_path))
    
    # Generate iframe-friendly version
    iframe_path = output_dir / f'cd6_coffee_shops_embed_{icon_style}.html'
    generate_iframe_version(m, iframe_path)
    
    # Generate iframe code snippet
    iframe_code_path = output_dir / f'iframe_embed_code_{icon_style}.txt'
    generate_iframe_code(iframe_code_path, icon_style)
    
    print(f"Map created: {map_path}")
    print(f"Iframe version created: {iframe_path}")
    print(f"Embed code saved to: {iframe_code_path}")
    return True


def fetch_coffee_shops(csv_url):
    """Fetch coffee shop data from Google Sheets CSV with improved parsing"""
    try:
        response = requests.get(csv_url)
        response.raise_for_status()
        
        # Parse CSV
        csv_reader = csv.reader(StringIO(response.text))
        rows = list(csv_reader)
        
        if not rows:
            print("No data found in CSV")
            return []
        
        # Debug: Show CSV structure
        print(f"CSV has {len(rows)} rows")
        if len(rows) > 0:
            print(f"Headers: {rows[0]}")
        
        # Skip header row
        coffee_shops = []
        mobile_trucks = []
        
        for i, row in enumerate(rows[1:], 1):
            # Ensure we have enough columns and handle empty rows
            if len(row) < 3:
                continue
                
            name = row[0].strip() if row[0] else f"Coffee Shop {i}"
            address1 = row[1].strip() if len(row) > 1 and row[1] else ""
            address2 = row[2].strip() if len(row) > 2 and row[2] else ""
            county = row[5].strip() if len(row) > 5 and row[5] else ""
            
            # Check for mobile-only indicators
            is_mobile = any(keyword in name.lower() for keyword in ['mobile', 'truck', 'cart', 'trailer'])
            
            # Process first address
            if address1:
                formatted_address1 = format_address(address1, county)
                coffee_shops.append({
                    'name': name,
                    'address': formatted_address1,
                    'original_address': address1,
                    'county': county,
                    'location_num': 1,
                    'row_number': i + 1
                })
            elif is_mobile:
                mobile_trucks.append(name)
            else:
                # No address and not identified as mobile - still add with empty address
                coffee_shops.append({
                    'name': name,
                    'address': "",
                    'original_address': "",
                    'county': county,
                    'location_num': 1,
                    'row_number': i + 1
                })
            
            # Process second address
            if address2:
                formatted_address2 = format_address(address2, county)
                coffee_shops.append({
                    'name': f"{name} (Location 2)",
                    'address': formatted_address2,
                    'original_address': address2,
                    'county': county,
                    'location_num': 2,
                    'row_number': i + 1
                })
        
        print(f"Found {len(coffee_shops)} coffee shop locations")
        if mobile_trucks:
            print(f"Found {len(mobile_trucks)} mobile coffee trucks (no fixed address):")
            for truck in mobile_trucks:
                print(f"   - {truck}")
        
        return coffee_shops
        
    except Exception as e:
        print(f"Error fetching coffee shop data: {e}")
        return []


def format_address(address, county=""):
    """Format and clean address for better geocoding, including suite number handling"""
    if not address:
        return ""
    
    # Clean up the address
    formatted = address.strip()
    
    # Handle suite numbers - add commas where needed for better geocoding
    suite_patterns = [
        ('Suite ', ', Suite '),
        ('Ste ', ', Ste '),
        ('STE ', ', STE '),
        ('Unit ', ', Unit '),
        ('UNIT ', ', UNIT '),
        ('#', ', #')
    ]
    
    for pattern, replacement in suite_patterns:
        # Only add comma if there isn't already one before the suite
        if pattern in formatted and f", {pattern}" not in formatted and f",{pattern}" not in formatted:
            # Find the position and check if there's already a comma nearby
            pos = formatted.find(pattern)
            if pos > 0:
                # Look at the character before the suite pattern
                char_before = formatted[pos-1]
                if char_before not in [',', ' ']:
                    # Add a space before the comma if the previous char isn't a space
                    formatted = formatted[:pos] + replacement + formatted[pos + len(pattern):]
                elif char_before == ' ':
                    # Replace the space with comma + space
                    formatted = formatted[:pos-1] + replacement + formatted[pos + len(pattern):]
    
    # Add Kentucky if not present
    if "KY" not in formatted.upper() and "KENTUCKY" not in formatted.upper():
        formatted += ", KY"
    
    # If no ZIP code and we have county info, try to add it
    if not any(char.isdigit() for char in formatted[-10:]) and county:
        # Insert county before state
        if ", KY" in formatted:
            formatted = formatted.replace(", KY", f", {county} County, KY")
    
    return formatted


def geocode_address(address, original_address=""):
    """Geocode an address using Nominatim with fallback strategies for suite numbers and street variations"""
    if not address:
        return None, "No address provided"
    
    base_url = "https://nominatim.openstreetmap.org/search"
    
    # Try multiple address variations
    address_attempts = [address]
    
    # Create fallback versions by removing suite information
    suite_patterns = [', Suite ', ', Ste ', ', STE ', ', Unit ', ', UNIT ', ', #', ' Suite ', ' Ste ', ' STE ', ' Unit ', ' UNIT ', ' #']
    
    for pattern in suite_patterns:
        if pattern in address:
            # Remove everything from the suite pattern onwards, but keep the rest
            base_address = address.split(pattern)[0]
            # Add back the city, state, zip if they exist after the suite
            parts = address.split(pattern)
            if len(parts) > 1:
                # Look for city, state, zip after the suite number
                after_suite = parts[1]
                # Find where the city starts (usually after the suite number)
                import re
                city_match = re.search(r'[A-Za-z\s]+,?\s*KY\s*\d{5}', after_suite)
                if city_match:
                    base_address += ", " + city_match.group().strip()
                elif "KY" in after_suite:
                    # Just append everything after suite if it contains KY
                    base_address += ", " + after_suite.strip()
            
            if base_address not in address_attempts:
                address_attempts.append(base_address)
    
    # Also try without any suite info at all - just street + city
    import re
    no_suite = re.sub(r',?\s*(Suite|Ste|STE|Unit|UNIT|#)\s*[A-Za-z0-9\-]+', '', address)
    if no_suite != address and no_suite not in address_attempts:
        address_attempts.append(no_suite)
    
    # Try street abbreviation variations
    street_abbrev_variations = {
        ' Dr ': ' Drive ',
        ' Dr,': ' Drive,',
        ' St ': ' Street ',
        ' St,': ' Street,',
        ' Ave ': ' Avenue ',
        ' Ave,': ' Avenue,',
        ' Rd ': ' Road ',
        ' Rd,': ' Road,',
        ' Blvd ': ' Boulevard ',
        ' Blvd,': ' Boulevard,',
        ' Cir ': ' Circle ',
        ' Cir,': ' Circle,'
    }
    
    for abbrev, full_word in street_abbrev_variations.items():
        if abbrev in address:
            variation = address.replace(abbrev, full_word)
            if variation not in address_attempts:
                address_attempts.append(variation)
        elif full_word in address:
            variation = address.replace(full_word, abbrev)
            if variation not in address_attempts:
                address_attempts.append(variation)
    
    print(f"      Trying {len(address_attempts)} address variations...")
    
    for i, attempt_address in enumerate(address_attempts, 1):
        print(f"      Attempt {i}: {attempt_address}")
        
        params = {
            'q': attempt_address,
            'format': 'json',
            'limit': 3,
            'countrycodes': 'us',
            'addressdetails': 1
        }
        
        try:
            # Add a small delay to be respectful to the free service
            time.sleep(1)
            
            response = requests.get(base_url, params=params, 
                                  headers={'User-Agent': 'Congressional District Mapper'})
            response.raise_for_status()
            
            results = response.json()
            if results:
                # Try to find Kentucky results first
                ky_results = [r for r in results if 'kentucky' in r.get('display_name', '').lower()]
                best_result = ky_results[0] if ky_results else results[0]
                
                lat = float(best_result['lat'])
                lon = float(best_result['lon'])
                
                if i > 1:
                    print(f"      ✅ Success with fallback address!")
                
                return (lat, lon), None
            else:
                print(f"      No results for attempt {i}")
                
        except requests.RequestException as e:
            print(f"      Network error on attempt {i}: {e}")
            continue
        except (ValueError, KeyError) as e:
            print(f"      Data parsing error on attempt {i}: {e}")
            continue
        except Exception as e:
            print(f"      Unexpected error on attempt {i}: {e}")
            continue
    
    return None, f"All {len(address_attempts)} geocoding attempts failed for: {original_address or address}"


def add_coffee_shop_markers(folium_map, coffee_shops, icon_style="coffee_emoji"):
    """Add coffee shop markers to the map with detailed failure reporting and manual overrides"""
    
    # Define different icon styles
    icon_styles = {
        "coffee_emoji": {
            "html": "☕",
            "size": 24,
            "description": "Coffee emoji"
        },
        "coffee_bean": {
            "html": "🫘",
            "size": 24,
            "description": "Coffee bean emoji"
        },
        "hot_beverage": {
            "html": "🍵",
            "size": 24,
            "description": "Hot beverage emoji"
        },
        "brown_circle": {
            "html": "🟤",
            "size": 20,
            "description": "Brown circle"
        },
        "location_pin": {
            "html": "📍",
            "size": 24,
            "description": "Location pin"
        },
        "star": {
            "html": "⭐",
            "size": 24,
            "description": "Star"
        },
        "dot": {
            "html": "●",
            "size": 16,
            "description": "Simple dot",
            "color": "#8B4513"
        },
        "custom_image": {
            "type": "image",
            "image_url": "coffee_bean_icon.png",  # Place your image in the output folder
            "size": 30,
            "description": "Custom coffee bean image"
        }
    }
    
    # Get the selected icon style
    selected_icon = icon_styles.get(icon_style, icon_styles["coffee_emoji"])
    
    print(f"Using icon style: {selected_icon['description']}")
    
    # Manual coordinate overrides for addresses that can't be geocoded
    manual_coordinates = {
        "121 Bethel Harvest Dr Nicholasville, KY 40356": (37.8814, -84.5730),  # Approximate coordinates for this area
        # Add more manual overrides here if needed in format:
        # "full address": (latitude, longitude),
    }
    
    successful_markers = 0
    failed_geocoding = []
    manual_overrides_used = 0
    
    print(f"\nProcessing {len(coffee_shops)} coffee shop addresses...\n")
    
    for i, shop in enumerate(coffee_shops, 1):
        # Handle missing keys gracefully - works with both old and new data formats
        shop_name = shop.get('name', f'Coffee Shop {i}')
        original_address = shop.get('original_address', shop.get('address', ''))
        formatted_address = shop.get('address', '')
        county = shop.get('county', '')
        row_number = shop.get('row_number', i)
        
        print(f"[{i}/{len(coffee_shops)}] {shop_name}")
        print(f"   Original: {original_address}")
        print(f"   Formatted: {formatted_address}")
        
        # Skip if no address (mobile trucks)
        if not formatted_address:
            print(f"   ⚠️  Skipping - no address (mobile only)")
            print()
            continue
        
        # Check for manual override first
        coordinates = None
        error = None
        
        if formatted_address in manual_coordinates:
            coordinates = manual_coordinates[formatted_address]
            manual_overrides_used += 1
            print(f"   🎯 Using manual override coordinates")
        else:
            # Try geocoding
            coordinates, error = geocode_address(formatted_address, original_address)
        
        if coordinates:
            lat, lon = coordinates
            print(f"   ✅ Success: {lat:.4f}, {lon:.4f}")
            
            # Create popup content
            popup_html = f"""
            <div style="font-family: Arial, sans-serif; min-width: 200px;">
                <h4 style="margin: 0 0 10px 0; color: #8B4513;">☕ {shop_name}</h4>
                <p style="margin: 0; font-size: 12px; color: #666;">
                    <strong>Address:</strong><br>{original_address}
                </p>
                {f"<p style='margin: 5px 0 0 0; font-size: 11px; color: #888;'><strong>County:</strong> {county}</p>" if county else ""}
            </div>
            """
            
            # Create icon based on selected style
            if selected_icon.get("type") == "image":
                # Use custom image icon
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=shop_name,
                    icon=folium.CustomIcon(
                        icon_image=selected_icon["image_url"],
                        icon_size=(selected_icon["size"], selected_icon["size"])
                    )
                ).add_to(folium_map)
            else:
                # Use HTML/emoji icon
                if icon_style == "dot":
                    icon_html = f"""
                    <div style="
                        font-size: {selected_icon['size']}px; 
                        text-align: center; 
                        line-height: {selected_icon['size']}px;
                        color: {selected_icon.get('color', '#000')};
                        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
                    ">{selected_icon['html']}</div>
                    """
                else:
                    icon_html = f"""
                    <div style="
                        font-size: {selected_icon['size']}px; 
                        text-align: center; 
                        line-height: {selected_icon['size']}px;
                        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
                    ">{selected_icon['html']}</div>
                    """
                
                # Add marker with HTML icon
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=shop_name,
                    icon=folium.DivIcon(
                        html=icon_html,
                        icon_size=(30, 30),
                        icon_anchor=(15, 15)
                    )
                ).add_to(folium_map)
            
            successful_markers += 1
            
        else:
            print(f"   ❌ Failed: {error}")
            failed_geocoding.append({
                'name': shop_name,
                'original_address': original_address,
                'formatted_address': formatted_address,
                'error': error,
                'row': row_number
            })
        
        print()  # Add blank line for readability
    
    # Detailed summary
    print("="*60)
    print("GEOCODING SUMMARY")
    print("="*60)
    print(f"✅ Successfully geocoded: {successful_markers} addresses")
    if manual_overrides_used > 0:
        print(f"🎯 Manual overrides used: {manual_overrides_used} addresses")
    print(f"❌ Failed to geocode: {len(failed_geocoding)} addresses")
    
    if failed_geocoding:
        print(f"\nDETAILED FAILURE ANALYSIS:")
        print("-" * 40)
        
        # Group failures by error type
        error_types = {}
        for failure in failed_geocoding:
            error_key = failure['error'].split(':')[0] if ':' in failure['error'] else failure['error']
            if error_key not in error_types:
                error_types[error_key] = []
            error_types[error_key].append(failure)
        
        for error_type, failures in error_types.items():
            print(f"\n{error_type.upper()} ({len(failures)} addresses):")
            for failure in failures:
                print(f"   Row {failure['row']}: {failure['name']}")
                print(f"      Original: {failure['original_address']}")
                print(f"      Formatted: {failure['formatted_address']}")
                print(f"      💡 Consider adding to manual_coordinates in the script")
    
    return successful_markers


def generate_iframe_version(folium_map, output_path):
    """Generate an iframe-friendly version of the map without the banner"""
    
    # Create a copy of the map for iframe use
    iframe_map = folium.Map(
        location=folium_map.location,
        zoom_start=9,  # Use the same zoom level as the original map
        tiles='OpenStreetMap'
    )
    
    # Copy all layers except the banner (Element type)
    for child_key, child in folium_map._children.items():
        if not isinstance(child, folium.Element):  # Skip the banner element
            iframe_map.add_child(child)
    
    # Save the iframe version
    iframe_map.save(str(output_path))


def generate_iframe_code(output_path, icon_style):
    """Generate HTML iframe embed code for easy website integration"""
    
    iframe_code = f'''<!-- CD 6 Coffee Shops Map Embed Code ({icon_style} icons) -->
<!-- Copy and paste this code into your website where you want the map to appear -->

<iframe 
    src="cd6_coffee_shops_embed_{icon_style}.html" 
    width="100%" 
    height="600" 
    frameborder="0" 
    style="border: 1px solid #ccc; border-radius: 8px;"
    title="Kentucky District 6 Coffee Shops Map">
    <p>Your browser does not support iframes. 
       <a href="cd6_coffee_shops_embed_{icon_style}.html" target="_blank">View the map in a new window</a>
    </p>
</iframe>

<!-- Alternative responsive iframe (adjusts to container width) -->
<div style="position: relative; width: 100%; height: 0; padding-bottom: 60%;">
    <iframe 
        src="cd6_coffee_shops_embed_{icon_style}.html" 
        style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 1px solid #ccc; border-radius: 8px;"
        frameborder="0"
        title="Kentucky District 6 Coffee Shops Map">
        <p>Your browser does not support iframes. 
           <a href="cd6_coffee_shops_embed_{icon_style}.html" target="_blank">View the map in a new window</a>
        </p>
    </iframe>
</div>

<!-- Instructions for use: -->
<!--
1. Upload both files to your web server:
   - cd6_coffee_shops_embed_{icon_style}.html
   - cd6_map_with_coffee_shops_{icon_style}.html (backup/full version)

2. Update the src="cd6_coffee_shops_embed_{icon_style}.html" path to match your server structure
   Example: src="/maps/cd6_coffee_shops_embed_{icon_style}.html"

3. Adjust width and height as needed for your website layout

4. The responsive version will automatically adjust to fit the container width
-->'''
    
    with open(output_path, 'w') as f:
        f.write(iframe_code)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python scripts/create_map.py STATE DISTRICT [ICON_STYLE]")
        print("\nAvailable icon styles:")
        print("  coffee_emoji  - ☕ (default)")
        print("  coffee_bean   - 🫘")
        print("  hot_beverage  - 🍵")
        print("  brown_circle  - 🟤")
        print("  location_pin  - 📍")
        print("  star          - ⭐")
        print("  custom_image  - Custom coffee bean image (requires coffee_bean_icon.png in output folder)")
        print("  dot           - ● (simple brown dot)")
        print("\nExamples:")
        print("  python scripts/create_map.py KY 6")
        print("  python scripts/create_map.py KY 6 star")
        print("  python scripts/create_map.py KY 6 dot")
        sys.exit(1)
    
    state = sys.argv[1]
    district = int(sys.argv[2])
    icon_style = sys.argv[3] if len(sys.argv) > 3 else "coffee_emoji"
    
    create_map(state, district, icon_style)