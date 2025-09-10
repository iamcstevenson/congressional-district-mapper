#!/usr/bin/env python3
"""Development testing utilities"""
import subprocess
import sys
from pathlib import Path
import requests
import json

def test_environment():
    """Test development environment setup"""
    print("Testing development environment...")
    
    # Test Python imports
    try:
        import geopandas
        import folium
        import pandas
        print("✓ All required packages imported successfully")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    # Test GDAL
    try:
        result = subprocess.run(['gdalinfo', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ GDAL available")
        else:
            print("✗ GDAL not available")
            return False
    except FileNotFoundError:
        print("✗ GDAL command not found")
        return False
    
    print("✓ Development environment ready")
    return True

def test_sample_map():
    """Generate a sample map with mock data"""
    print("Testing map generation with sample data...")
    
    # Create sample GeoJSON data
    sample_district = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"NAME": "Sample District"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-85.5, 38.1], [-85.3, 38.1],
                    [-85.3, 38.3], [-85.5, 38.3],
                    [-85.5, 38.1]
                ]]
            }
        }]
    }
    
    # Save sample data
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    sample_file = output_dir / 'sample_district.geojson'
    with open(sample_file, 'w') as f:
        json.dump(sample_district, f)
    
    # Test basic map creation
    import folium
    m = folium.Map(location=[38.2, -85.4], zoom_start=10)
    folium.GeoJson(sample_district).add_to(m)
    
    test_map = output_dir / 'test_map.html'
    m.save(str(test_map))
    
    print(f"✓ Sample map generated: {test_map}")
    return True

if __name__ == '__main__':
    success = test_environment() and test_sample_map()
    sys.exit(0 if success else 1)
