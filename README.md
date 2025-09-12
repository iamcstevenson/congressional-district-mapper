# Congressional District Coffee Shop Mapper

An interactive mapping system that visualizes coffee shops within Kentucky's 6th Congressional District. This project combines census data processing with live Google Sheets integration to create embeddable maps with multiple icon styles.

## Features

- **Interactive District Maps** - Accurate congressional district boundaries with county overlays
- **Live Data Integration** - Real-time coffee shop data from Google Sheets
- **Multiple Icon Styles** - 7 different marker options including custom images
- **Robust Geocoding** - Advanced address parsing with fallback strategies
- **Iframe Embedding** - Ready-to-use embed codes for websites
- **Manual Override System** - Handle addresses that can't be automatically geocoded

## Project Structure

```
congressional-district-mapper/
├── scripts/
│   └── create_map.py           # Main mapping script
├── data/
│   └── processed/
│       └── KY_06/              # Processed geospatial data
│           ├── district_boundary.geojson
│           └── counties.geojson
└── output/                     # Generated map files
    ├── cd6_map_with_coffee_shops_*.html
    ├── cd6_coffee_shops_embed_*.html
    └── iframe_embed_code_*.txt
```

## Installation

### Prerequisites
- Python 3.8+
- Required packages:
```bash
pip install geopandas folium requests pandas shapely
```

### Setup
1. Clone the repository
2. Process your census data into the `data/processed/` structure
3. Update the Google Sheets CSV URL in the script (if using different data)

## Usage

### Basic Usage
```bash
# Generate map with default coffee emoji icons
python scripts/create_map.py KY 6

# Generate map with star icons
python scripts/create_map.py KY 6 star
```

### Available Icon Styles
- `coffee_emoji` - ☕ (default)
- `coffee_bean` - 🫘
- `hot_beverage` - 🍵
- `brown_circle` - 🟤
- `location_pin` - 📍
- `star` - ⭐
- `dot` - ● (simple brown dot)
- `custom_image` - Custom image (requires `coffee_bean_icon.png` in output folder)

### Output Files
Each run generates three files:
1. **Main Map** - `cd6_map_with_coffee_shops_{icon_style}.html`
2. **Iframe Version** - `cd6_coffee_shops_embed_{icon_style}.html` (no banner)
3. **Embed Code** - `iframe_embed_code_{icon_style}.txt` (ready-to-use HTML)

## Data Sources

### Google Sheets Integration
The script pulls coffee shop data from a published Google Sheets CSV with the following structure:
- Column A: Name
- Column B: Address 1
- Column C: Address 2 (for multiple locations)
- Column F: County

### Geographic Data
- Congressional district boundaries from US Census TIGER/Line shapefiles
- County boundaries processed through local ETL pipeline

## Advanced Features

### Geocoding System
The script uses a sophisticated multi-step geocoding process:
1. **Suite Number Handling** - Automatically formats addresses with suite/unit numbers
2. **Fallback Strategies** - Tries multiple address variations if initial geocoding fails
3. **Street Abbreviations** - Handles Dr/Drive, St/Street, etc.
4. **Manual Overrides** - Coordinates can be manually specified for problem addresses

### Address Processing Examples
```
Original: "101 W Loudon Ave Suite 160 Lexington, KY 40508"
Formatted: "101 W Loudon Ave, Suite 160, Lexington, KY 40508"
Fallback: "101 W Loudon Ave, Lexington, KY 40508"
```

### Mobile Coffee Trucks
The system automatically identifies and skips mobile coffee services (no fixed address) by detecting keywords: mobile, truck, cart, trailer.

## Website Embedding

### Basic Iframe
```html
<iframe 
    src="cd6_coffee_shops_embed_star.html" 
    width="100%" 
    height="600" 
    frameborder="0">
</iframe>
```

### Responsive Iframe
```html
<div style="position: relative; width: 100%; height: 0; padding-bottom: 60%;">
    <iframe 
        src="cd6_coffee_shops_embed_star.html" 
        style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
    </iframe>
</div>
```

## Custom Image Icons

To use custom coffee bean images:
1. Save your image as `coffee_bean_icon.png` in the `output/` folder
2. Recommended size: 30x30 or 50x50 pixels
3. PNG format with transparent background works best
4. Run: `python scripts/create_map.py KY 6 custom_image`

## Performance & Results

### Geocoding Success Rate
- **98%+ success rate** with fallback strategies
- Handles suite numbers, street abbreviations, and address formatting issues
- Manual override system for remaining edge cases

### Current Dataset
- **52 coffee shop locations** in Kentucky's 6th Congressional District
- **16 counties** (14 full + 2 partial)
- **Real-time data** updates from Google Sheets

## Development Notes

### Architecture
This is a **two-workflow system**:
1. **Local ETL Process** - Python scripts process Census Bureau ZIP files into web-optimized GeoJSON
2. **GitHub Mapping Workspace** - Repository with map generation scripts

### Key Technical Solutions
- **Geometric intersection fix** - Resolved complex boundary rendering issues
- **Suite number geocoding** - Custom address formatting for commercial addresses
- **Iframe compatibility** - Clean embeddable versions without banner elements

## Contributing

### Adding New Locations
Update the Google Sheets with new coffee shop information - changes will be reflected automatically on the next map generation.

### Adding New Icon Styles
Add new entries to the `icon_styles` dictionary in `create_map.py`:
```python
"new_style": {
    "html": "🆕",
    "size": 24,
    "description": "New style description"
}
```

### Manual Address Overrides
Add problematic addresses to the `manual_coordinates` dictionary:
```python
manual_coordinates = {
    "Full Address Here": (latitude, longitude),
}
```

## Version History

- **v8.0** - Added multiple icon styles and custom image support
- **v7.0** - Implemented manual coordinate override system
- **v6.0** - Advanced geocoding with fallback strategies
- **v5.0** - Suite number handling and address formatting
- **v4.0** - Google Sheets integration
- **v3.0** - Iframe embedding functionality
- **v2.0** - Coffee shop overlay system
- **v1.0** - Basic district mapping with county boundaries

## License

This project processes public census data and creates maps for civic/political purposes.

## Support

For issues with geocoding specific addresses, add them to the manual override system or update the address formatting in your Google Sheets data.
