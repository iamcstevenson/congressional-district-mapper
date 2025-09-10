#!/usr/bin/env python3
"""
Interactive Congressional District Map Generator
Creates mobile-first responsive maps with clickable county boundaries
"""
import json
import requests
import geopandas as gpd
import folium
from pathlib import Path
import click
import logging

logger = logging.getLogger(__name__)

@click.command()
@click.option('--state', required=True, help='State code')
@click.option('--district', required=True, help='District number')
@click.option('--urls', required=True, help='JSON string with Google Drive URLs')
def generate_map(state, district, urls):
    """Generate interactive congressional district map"""
    # Parse URLs
    try:
        drive_urls = json.loads(urls)
    except json.JSONDecodeError:
        logger.error("Invalid JSON format for URLs")
        return

    logger.info(f"Generating map for {state} District {district}")

    # Download data from Google Drive
    district_gdf = download_geojson(drive_urls['district_boundary'])
    counties_gdf = download_geojson(drive_urls['counties'])

    # Calculate map center
    bounds = district_gdf.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    # Create base map (mobile-first)
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=9,
        tiles='OpenStreetMap',
        width='100%',
        height='100%'
    )

    # Add district boundary (primary focus)
    folium.GeoJson(
        district_gdf,
        style_function=lambda x: {
            'fillColor': '#ff6b6b',
            'color': '#c92a2a',
            'weight': 3,
            'fillOpacity': 0.3,
            'opacity': 0.8
        },
        popup=folium.Popup(
            f"<strong>{state} Congressional District {district}</strong>",
            max_width=300
        )
    ).add_to(m)

    # Add county boundaries (interactive)
    folium.GeoJson(
        counties_gdf,
        style_function=lambda x: {
            'fillColor': '#4dabf7',
            'color': '#1971c2',
            'weight': 2,
            'fillOpacity': 0.1,
            'opacity': 0.6
        },
        popup=folium.Popup(
            lambda x: f"<strong>County:</strong> {x['properties'].get('NAME', 'Unknown')}",
            max_width=200
        ),
        tooltip=folium.Tooltip(
            fields=['NAME'],
            aliases=['County:'],
            style="background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;"
        )
    ).add_to(m)

    # Add mobile-optimized controls
    folium.plugins.Fullscreen(
        position='topright',
        title='Expand map',
        title_cancel='Exit full screen',
        force_separate_button=True
    ).add_to(m)

    # Fit bounds to district
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    # Ensure output directory exists
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)

    # Save map
    map_filename = f"{state}_{district}_district_map.html"
    map_path = output_dir / map_filename
    m.save(str(map_path))

    # Create index.html for GitHub Pages
    create_index_page(output_dir, state, district, map_filename)

    logger.info(f"Map generated: {map_path}")

def download_geojson(url):
    """Download and load GeoJSON from Google Drive URL"""
    response = requests.get(url)
    response.raise_for_status()
    
    # Load as GeoDataFrame
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.geojson', delete=False) as f:
        f.write(response.text)
        temp_path = f.name
    
    gdf = gpd.read_file(temp_path)
    Path(temp_path).unlink()  # Cleanup
    return gdf

def create_index_page(output_dir, state, district, map_filename):
    """Create mobile-optimized index page"""
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{state} Congressional District {district} - Interactive Map</title>
<style>
body {{
margin: 0;
padding: 0;
font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
background-color: #f8f9fa;
}}
.header {{
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
color: white;
padding: 1rem;
text-align: center;
box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}}
.header h1 {{
margin: 0;
font-size: 1.5rem;
}}
.map-container {{
width: 100vw;
height: calc(100vh - 120px);
border: none;
}}
.footer {{
padding: 1rem;
text-align: center;
font-size: 0.9rem;
color: #666;
background: white;
border-top: 1px solid #eee;
}}
@media (max-width: 768px) {{
.header h1 {{
font-size: 1.2rem;
}}
.map-container {{
height: calc(100vh - 100px);
}}
}}
</style>
</head>
<body>
<div class="header">
<h1>{state} Congressional District {district}</h1>
<p>Interactive District and County Boundaries</p>
</div>
<iframe src="{map_filename}" class="map-container"></iframe>
<div class="footer">
<p>Data: U.S. Census Bureau | Generated: {{% now "Y-m-d" %}}</p>
</div>
</body>
</html>"""

    index_path = output_dir / 'index.html'
    with open(index_path, 'w') as f:
        f.write(html_content)

if __name__ == '__main__':
    generate_map()
