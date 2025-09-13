# 🥃 Congressional District 6 - Bourbon Distillery Overlay

## Branch: `feature-distillery-overlay`

This branch contains a specialized bourbon distillery mapping system for Kentucky's 6th Congressional District, showcasing the region's rich bourbon heritage.

---

## 🎯 Purpose

This branch is a **standalone feature branch** designed to:
- Map all bourbon distilleries within Congressional District 6
- Provide an interactive visualization of Kentucky's bourbon tourism assets
- Support economic development and tourism initiatives
- Demonstrate the district's cultural and economic significance in bourbon production

**Note:** This branch is maintained separately from `main` and is not intended for merging. It serves as a dedicated bourbon industry visualization tool.

---

## 🗂️ Branch Structure

```
feature-distillery-overlay/
├── scripts/
│   └── create_map.py          # Main distillery mapping script
├── cd6_distilleries_map.html  # Generated primary map (bourbon markers)
├── cd6_distilleries_iframe.html # Iframe wrapper for embedding
├── cd6_distilleries_*.html    # Alternative icon style maps
├── ky_6th_congressional_district.geojson  # District boundaries
└── README.md                   # This documentation
```

---

## 🚀 Quick Start

### Accessing This Branch

```bash
# Clone the repository if you haven't already
git clone https://github.com/YOUR_USERNAME/congressional-district-mapper.git
cd congressional-district-mapper

# Switch to the distillery branch
git checkout feature-distillery-overlay

# Pull latest changes
git pull origin feature-distillery-overlay
```

### Running the Distillery Mapper

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run the mapping script
python scripts/create_map.py
```

---

## 📊 Data Source Configuration

### Google Sheets Setup

The distillery data is sourced from a Google Sheet with the following structure:

| Column | Field | Description | Example |
|--------|-------|-------------|---------|
| A | Name | Distillery name | "Woodford Reserve" |
| B | Address | Street address | "7855 McCracken Pike" |
| C | Address2 | Suite/Unit (optional) | "Suite 100" |
| D | City | City name | "Versailles" |
| E | State | State code | "KY" |
| F | Zip | ZIP code | "40383" |

**Current Sheet URL:** 
```
https://docs.google.com/spreadsheets/d/1MpxmmbJXS5qBog5HE2lANgeeJEvY0oE3MWypKuEvjks/
```

### Updating the Data Source

1. **To use a different Google Sheet:**
   - Edit `scripts/create_map.py`
   - Update line 21: `GOOGLE_SHEET_URL = 'YOUR_NEW_SHEET_URL'`
   - Ensure the sheet is publicly accessible (view permissions)

2. **To modify the data range:**
   - Edit line 26: `'range': 'A2:F28'`
   - Adjust to match your data (e.g., `'A2:F50'` for more rows)

3. **To change column mappings:**
   - Edit the `columns` dictionary in `SHEET_CONFIG` (lines 27-33)

---

## 🗺️ Generated Maps

Running the script produces multiple map variations:

### Primary Map
- **File:** `cd6_distilleries_map.html`
- **Style:** Brown bourbon-themed markers with glass icons
- **Features:** Clustered markers, popups with distillery info, district boundaries

### Alternative Styles
- `cd6_distilleries_bourbon_emoji.html` - Custom bourbon glass emoji markers
- `cd6_distilleries_barrel.html` - Dark red barrel icons
- `cd6_distilleries_building.html` - Blue building icons
- `cd6_distilleries_star.html` - Gold star markers
- `cd6_distilleries_bottle.html` - Purple bottle icons
- `cd6_distilleries_classic.html` - Traditional brown markers

### Embedding
- **File:** `cd6_distilleries_iframe.html`
- **Usage:** For embedding the map in websites or presentations

---

## 🛠️ Development in GitHub Codespaces

### Setting Up Codespaces

1. Navigate to the repository on GitHub
2. Click the green "Code" button
3. Select "Codespaces" tab
4. Click "Create codespace on feature-distillery-overlay"

### Working in Codespaces

```bash
# The environment is pre-configured
# Navigate to the project
cd /workspaces/congressional-district-mapper

# Ensure you're on the correct branch
git checkout feature-distillery-overlay

# Install dependencies if needed
pip install -r requirements-dev.txt

# Edit the script
code scripts/create_map.py

# Run the mapper
python scripts/create_map.py

# View generated files
ls -la *.html
```

### Saving Changes from Codespaces

```bash
# Stage your changes
git add .

# Commit with descriptive message
git commit -m "Update distillery locations and add new markers"

# Push to GitHub
git push origin feature-distillery-overlay
```

---

## 🔧 Customization Options

### Adding Manual Coordinates

For distilleries that fail to geocode automatically, add manual coordinates in `create_map.py`:

```python
MANUAL_COORDINATES = {
    'Distillery Name': (latitude, longitude),
    'Buffalo Trace': (38.2189, -84.8732),
    # Add more as needed
}
```

### Modifying Map Appearance

#### Change Default Icon Style
Line 492 in `create_map.py`:
```python
primary_style = 'bourbon'  # Change to: 'barrel', 'building', 'star', etc.
```

#### Adjust Map Center
Line 358:
```python
map_center = [38.0406, -84.5037]  # [latitude, longitude]
```

#### Modify Zoom Level
Line 363:
```python
zoom_start=9  # Increase for closer view, decrease for wider view
```

---

## 📈 Geocoding Success Metrics

The script provides detailed geocoding statistics:
- Total distilleries processed
- Successfully geocoded count and percentage
- Failed geocoding attempts with specific addresses
- Suggestions for manual coordinate additions

---

## 🐛 Troubleshooting

### Common Issues

1. **404 Error Loading Sheet**
   - Verify the Google Sheet URL is correct
   - Ensure the sheet has public view permissions
   - Check that the sheet ID is properly extracted

2. **Geocoding Failures**
   - The script attempts multiple fallback strategies
   - Add problematic addresses to `MANUAL_COORDINATES`
   - Check address formatting in the source sheet

3. **Missing Dependencies**
   ```bash
   pip install folium pandas requests
   ```

4. **No District Boundaries Showing**
   - Ensure `ky_6th_congressional_district.geojson` exists
   - Check file path references in the script

---

## 📝 Maintenance Notes

### Regular Updates

1. **Monthly:** Update distillery data in Google Sheets
2. **Quarterly:** Review geocoding success rate and add manual coordinates as needed
3. **Annually:** Review and update distillery information for accuracy

### Branch Management

```bash
# Keep branch updated with security fixes from main (selective)
git checkout main
git pull origin main
git checkout feature-distillery-overlay
git cherry-pick [commit-hash]  # Only if needed for security updates

# This branch should remain independent and not be merged with main
```

---

## 🤝 Contributing

To contribute to this distillery mapping branch:

1. Always work on the `feature-distillery-overlay` branch
2. Test thoroughly before committing
3. Document any new distilleries added
4. Update this README if functionality changes

---

## 📞 Contact

For questions about this bourbon distillery mapping system:
- Create an issue on GitHub with the label `distillery-overlay`
- Reference this branch specifically in any discussions

---

## 🏛️ License & Attribution

This project maps publicly available information about licensed distilleries in Kentucky's 6th Congressional District. 

Data sources:
- Kentucky Distillers' Association
- Public business registrations
- Tourism directories

---

*Last Updated: September 2025*
*Branch Maintainer: [Your Name]*
