import folium
from folium import plugins
import pandas as pd
import json
import time
import requests
import re
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("CD 6 DISTILLERY MAPPING SYSTEM")
print("=" * 60)
print(f"Execution started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Configuration
GOOGLE_SHEET_URL = 'https://docs.google.com/spreadsheets/d/1g8afJBAVBJnTkNrL5tz9Pv6u4V36ZClxYmAmrnDD48k/edit?usp=sharing'
OUTPUT_HTML = 'cd6_distilleries_map.html'
OUTPUT_IFRAME_HTML = 'cd6_distilleries_iframe.html'

# Icon configuration for distilleries
BOURBON_ICON = {
    'type': 'custom_teardrop',
    'emoji': '🥃',
    'backgroundColor': '#8B4513',
    'borderColor': 'white',
    'size': [35, 42]
}

# Manual coordinates for problematic addresses (add as needed)
MANUAL_COORDINATES = {
    # Example: 'Specific Distillery Name': (latitude, longitude),
    # 'Historic Distillery': (38.2089, -84.5589),
}

def load_distillery_data():
    """Load distillery data from Google Sheets"""
    print("Loading distillery data from Google Sheets...")
    
    # Extract sheet ID from URL and create export URL
    if '/d/' in GOOGLE_SHEET_URL:
        sheet_id = GOOGLE_SHEET_URL.split('/d/')[1].split('/')[0]
        csv_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv'
    else:
        csv_url = GOOGLE_SHEET_URL  # Fallback to original URL
    
    print(f"Fetching from: {csv_url}")
    
    try:
        df = pd.read_csv(csv_url)
        print(f"✓ Loaded {len(df)} distilleries from spreadsheet")
        
        # Display first few entries
        print("\nFirst 5 distilleries:")
        for idx, row in df.head().iterrows():
            name = row.iloc[0] if not pd.isna(row.iloc[0]) else "Unknown"
            address = row.iloc[1] if not pd.isna(row.iloc[1]) else "No address"
            print(f"  {idx+1}. {name} - {address}")
        
        return df
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        return None

def format_address(address, county=""):
    """Format and clean address for better geocoding, including suite number handling"""
    # Handle empty or invalid addresses
    if pd.isna(address) or address == '' or not address:
        return None
    
    # Convert to string if not already
    address = str(address)
    
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

def geocode_address(address, original_address="", name=""):
    """Geocode an address using Nominatim with fallback strategies for suite numbers and street variations"""
    # Check manual coordinates first
    if name and name in MANUAL_COORDINATES:
        lat, lon = MANUAL_COORDINATES[name]
        print(f"      → Using manual coordinates: ({lat:.4f}, {lon:.4f})")
        return (lat, lon), None
    
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
                city_match = re.search(r'[A-Za-z\s]+,?\s*KY\s*\d{5}', after_suite)
                if city_match:
                    base_address += ", " + city_match.group().strip()
                elif "KY" in after_suite:
                    # Just append everything after suite if it contains KY
                    base_address += ", " + after_suite.strip()
            
            if base_address not in address_attempts:
                address_attempts.append(base_address)
    
    # Also try without any suite info at all - just street + city
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
        ' Cir,': ' Circle,',
        ' Ct ': ' Court ',
        ' Ct,': ' Court,',
        ' Ln ': ' Lane ',
        ' Ln,': ' Lane,',
        ' Pkwy ': ' Parkway ',
        ' Pkwy,': ' Parkway,',
        ' Pl ': ' Place ',
        ' Pl,': ' Place,'
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
    
    # Try with distillery name + city as last resort
    if name and original_address:
        city_parts = original_address.split(',')
        if len(city_parts) >= 2:
            city = city_parts[-2].strip()
            name_search = f"{name}, {city}, Kentucky"
            if name_search not in address_attempts:
                address_attempts.append(name_search)
    
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

def geocode_distilleries(df):
    """Geocode all distillery addresses"""
    print("\n" + "=" * 60)
    print("GEOCODING DISTILLERY LOCATIONS")
    print("=" * 60)
    
    locations = []
    successful = 0
    failed = 0
    failed_distilleries = []
    
    for idx, row in df.iterrows():
        # Handle both old format (name, address) and new format (with separate columns)
        if 'name' in row:
            # New multi-column format
            name = row['name']
            address = row['full_address']
            city = row.get('city', '')
        else:
            # Old two-column format (backward compatibility)
            name = row.iloc[0] if not pd.isna(row.iloc[0]) else f"Distillery {idx+1}"
            address = row.iloc[1] if not pd.isna(row.iloc[1]) else None
            city = ''
        
        print(f"\n[{idx+1}/{len(df)}] {name}")
        
        if not address or pd.isna(address):
            print(f"  ✗ No address provided")
            failed += 1
            failed_distilleries.append(f"{name} (No address)")
            continue
        
        print(f"  Address: {address}")
        
        # Format the address (pass city/county if available)
        formatted_address = format_address(address, county=city if city else "")
        
        if not formatted_address:
            print(f"  ✗ Invalid address format")
            failed += 1
            failed_distilleries.append(f"{name} ({address})")
            continue
        
        print(f"  Formatted: {formatted_address}")
        
        # Geocode the address
        coords, error = geocode_address(formatted_address, original_address=address, name=name)
        
        if coords:
            lat, lon = coords
            locations.append({
                'name': name,
                'address': address,
                'lat': lat,
                'lon': lon
            })
            print(f"  ✓ Geocoded: ({lat:.4f}, {lon:.4f})")
            successful += 1
        else:
            print(f"  ✗ Failed to geocode: {error}")
            failed += 1
            failed_distilleries.append(f"{name} ({address})")
    
    print("\n" + "=" * 60)
    print("GEOCODING SUMMARY")
    print("=" * 60)
    print(f"Total distilleries: {len(df)}")
    print(f"Successfully geocoded: {successful} ({successful/len(df)*100:.1f}%)")
    print(f"Failed: {failed}")
    
    if failed_distilleries:
        print("\nFailed to geocode:")
        for distillery in failed_distilleries:
            print(f"  - {distillery}")
        print("\nConsider adding manual coordinates for these distilleries in MANUAL_COORDINATES")
    
    return locations

def create_teardrop_icon(emoji, background_color, border_color, size):
    """Create a custom teardrop/pin shaped marker with emoji"""
    width, height = size

    icon_html = f"""
    <div style="
        position: relative;
        width: {width}px;
        height: {height}px;
        transform: translate(-50%, -100%);
    ">
        <div style="
            position: absolute;
            top: 0;
            left: 50%;
            width: {width-4}px;
            height: {width-4}px;
            background-color: {background_color};
            border: 2px solid {border_color};
            border-radius: 50%;
            transform: translateX(-50%);
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        "></div>
        <div style="
            position: absolute;
            bottom: 0;
            left: 50%;
            width: 0;
            height: 0;
            border-left: 8px solid transparent;
            border-right: 8px solid transparent;
            border-top: 12px solid {background_color};
            transform: translateX(-50%);
            filter: drop-shadow(0 2px 3px rgba(0,0,0,0.2));
        "></div>
        <div style="
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -65%);
            font-size: 16px;
            z-index: 1000;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
        ">{emoji}</div>
    </div>
    """

    return folium.DivIcon(
        html=icon_html,
        icon_size=(width, height),
        icon_anchor=(width//2, height)
    )

def load_geojson():
    """Load congressional district GeoJSON"""
    print("\nLoading Congressional District 6 boundaries...")
    
    # Try multiple possible file locations
    possible_paths = [
        'ky_6th_congressional_district.geojson',
        '../ky_6th_congressional_district.geojson',
        'data/ky_6th_congressional_district.geojson',
        '../../ky_6th_congressional_district.geojson'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                print(f"✓ Loaded GeoJSON from {path}")
                return json.load(f)
    
    print("✗ Warning: Congressional district GeoJSON not found")
    print("  Map will be created without district boundaries")
    return None

def create_map_with_distilleries(locations):
    """Create the map with distillery markers"""
    print(f"\nCreating map with {len(locations)} distilleries...")
    
    # Center map on Lexington/Central KY
    map_center = [38.0406, -84.5037]
    
    # Create base map
    m = folium.Map(
        location=map_center,
        zoom_start=9,
        tiles='OpenStreetMap',
        control_scale=True
    )
    
    # Add title
    title_html = '''
    <div style="position: fixed; 
                top: 10px; 
                left: 50px; 
                width: 300px; 
                height: 60px; 
                background-color: rgba(255, 255, 255, 0.9);
                border-radius: 10px;
                box-shadow: 2px 2px 6px rgba(0, 0, 0, 0.3);
                border: 2px solid #8B4513;
                z-index: 9999;
                font-size: 20px;
                font-weight: bold;
                color: #5D4037;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: 'Georgia', serif;">
        <div>
            🥃 CD 6 Distilleries 🥃
            <div style="font-size: 12px; font-weight: normal; color: #666; margin-top: 2px;">
                Kentucky's Bourbon Heritage
            </div>
        </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Try to add congressional district boundaries
    geojson_data = load_geojson()
    if geojson_data:
        folium.GeoJson(
            geojson_data,
            name='Congressional District 6',
            style_function=lambda feature: {
                'fillColor': 'none',
                'color': '#8B4513',
                'weight': 3,
                'opacity': 0.8,
                'dashArray': '10, 5'
            }
        ).add_to(m)
    
    # Use bourbon teardrop icon configuration
    icon_config = BOURBON_ICON
    
    # Add distillery markers
    marker_cluster = plugins.MarkerCluster(
        name='Distilleries',
        overlay=True,
        control=True,
        show=True,
        options={'showCoverageOnHover': False}
    )
    
    for loc in locations:
        popup_html = f"""
        <div style='font-family: Georgia, serif; width: 200px;'>
            <h4 style='margin: 0 0 5px 0; color: #5D4037;'>{loc['name']}</h4>
            <p style='margin: 0; font-size: 12px; color: #666;'>
                📍 {loc['address']}
            </p>
            <p style='margin: 5px 0 0 0; font-size: 11px; color: #8B4513;'>
                <i>Craft Distillery</i>
            </p>
        </div>
        """

        # Create bourbon teardrop marker
        marker_icon = create_teardrop_icon(
            emoji=icon_config['emoji'],
            background_color=icon_config['backgroundColor'],
            border_color=icon_config['borderColor'],
            size=icon_config['size']
        )

        folium.Marker(
            location=[loc['lat'], loc['lon']],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=loc['name'],
            icon=marker_icon
        ).add_to(marker_cluster)
    
    marker_cluster.add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add fullscreen plugin
    plugins.Fullscreen().add_to(m)
    
    return m

def create_iframe_wrapper(map_filename, iframe_filename):
    """Create an iframe wrapper for embedding"""
    print(f"\nCreating iframe wrapper: {iframe_filename}")
    
    iframe_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>CD 6 Distilleries Map</title>
    <style>
        body, html {{
            margin: 0;
            padding: 0;
            height: 100%;
            overflow: hidden;
        }}
        #map-container {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
        }}
        iframe {{
            width: 100%;
            height: 100%;
            border: none;
        }}
    </style>
</head>
<body>
    <div id="map-container">
        <iframe src="{map_filename}" allowfullscreen></iframe>
    </div>
</body>
</html>"""
    
    with open(iframe_filename, 'w') as f:
        f.write(iframe_html)
    print(f"✓ Iframe wrapper created: {iframe_filename}")

def main():
    """Main execution function"""
    
    # Load distillery data
    df = load_distillery_data()
    if df is None:
        print("\n✗ Failed to load distillery data. Exiting.")
        return
    
    # Geocode distilleries
    locations = geocode_distilleries(df)
    
    if not locations:
        print("\n✗ No distilleries were successfully geocoded. Exiting.")
        return
    
    # Create maps with different icon styles
    print("\n" + "=" * 60)
    print("GENERATING DISTILLERY MAPS")
    print("=" * 60)
    
    # Generate map with bourbon teardrop icons
    m = create_map_with_distilleries(locations)
    
    # Save in scripts directory
    output_path = os.path.join(os.path.dirname(__file__), OUTPUT_HTML)
    m.save(output_path)
    print(f"✓ Map saved: {output_path}")

    # Create iframe wrapper
    iframe_path = os.path.join(os.path.dirname(__file__), OUTPUT_IFRAME_HTML)
    create_iframe_wrapper(OUTPUT_HTML, iframe_path)

    # Print summary
    print("\n" + "=" * 60)
    print("DISTILLERY MAPPING COMPLETE!")
    print("=" * 60)
    print(f"✓ {len(locations)} distilleries mapped")
    print(f"✓ Map: {output_path}")
    print(f"✓ Iframe wrapper: {iframe_path}")
    print("\nFiles are ready for viewing in your browser!")
    print(f"Execution completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()