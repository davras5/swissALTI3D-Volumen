# Swiss Building Volume Calculator

Calculate building volumes in cubic meters using publicly available Swiss geodata. This tool combines building footprints from the Swiss official cadastral survey (Amtliche Vermessung) with height data from swissALTI3D (terrain) and swissSURFACE3D (surface) models.

## Overview

This tool:
- Loads building footprints from Amtliche Vermessung (AV) geopackage files
- Creates a 1x1m voxel grid for each building
- Samples terrain height (swissALTI3D) to determine base elevation
- Samples surface height (swissSURFACE3D) for roof elevation
- Calculates volume as: `Σ(roof_height - base_height) × 1m²`

## Requirements

### Python Dependencies
```bash
pip install geopandas rasterio numpy pandas shapely fiona
```

### Data Requirements

1. **Building footprints**: `av_2056.gpkg` from [geodienste.ch](https://www.geodienste.ch/services/av)
   - Uses layer `lcsf` with `Art = 'Gebaeude'`

2. **swissALTI3D**: Terrain model tiles from [swisstopo](https://www.swisstopo.admin.ch/de/hoehenmodell-swissalti3d)
   - 0.5m resolution GeoTIFF files
   - Represents bare earth elevation

3. **swissSURFACE3D Raster**: Surface model tiles from [swisstopo](https://www.swisstopo.admin.ch/de/hoehenmodell-swisssurface3d-raster)
   - 0.5m resolution GeoTIFF files
   - Includes buildings, vegetation, and other structures

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/swiss-building-volumes.git
cd swiss-building-volumes
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Download required geodata and organize as follows:
```
project/
├── main.py
├── data/
│   ├── av_2056.gpkg
│   ├── alti3d/
│   │   ├── swissALTI3D_2680_1235.tif
│   │   ├── swissALTI3D_2681_1235.tif
│   │   └── ...
│   └── surface3d/
│       ├── swissSURFACE3D_2680_1235.tif
│       ├── swissSURFACE3D_2681_1235.tif
│       └── ...
```

## Usage

### Basic Usage
```bash
python main.py data/av_2056.gpkg data/alti3d data/surface3d
```

### Command Line Options
```bash
# Process limited number of buildings for testing
python main.py data/av_2056.gpkg data/alti3d data/surface3d --limit 10

# Process specific area (Swiss LV95 coordinates)
python main.py data/av_2056.gpkg data/alti3d data/surface3d \
    --bbox 2680000 1235000 2681000 1236000

# Custom output files
python main.py data/av_2056.gpkg data/alti3d data/surface3d \
    -o results.csv \
    -g buildings_with_volumes.gpkg

# Combine options
python main.py data/av_2056.gpkg data/alti3d data/surface3d \
    --limit 100 \
    --bbox 2680000 1235000 2681000 1236000 \
    -o test_results.csv
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `av_gpkg` | Yes | Path to AV geopackage file |
| `alti3d_dir` | Yes | Directory containing swissALTI3D tiles |
| `surface3d_dir` | Yes | Directory containing swissSURFACE3D tiles |
| `-o, --output` | No | Output CSV file (default: building_volumes.csv) |
| `-g, --gpkg` | No | Output GeoPackage with geometries |
| `-l, --limit` | No | Limit number of buildings to process |
| `-b, --bbox` | No | Bounding box: MINX MINY MAXX MAXY |

## Output

### CSV Output
The tool generates a CSV file with the following columns:
- `EGID`: Building identifier
- `volume_m3`: Calculated volume in cubic meters
- `footprint_area_m2`: Building footprint area
- `mean_height_m`: Average building height
- `max_height_m`: Maximum building height
- `base_height_m`: Terrain elevation at building base
- `status`: Processing status (success/no_voxels/no_height_data)

### GeoPackage Output (optional)
Contains original building geometries with volume calculations as attributes.

## Technical Details

### Coordinate System
- Swiss LV95 (EPSG:2056)
- Tile naming: `XXXX_YYYY` based on SW corner in kilometers

### Methodology
1. **Voxel Grid**: Creates 1x1m points within each building polygon
2. **Base Height**: Minimum terrain elevation from swissALTI3D
3. **Roof Height**: Surface elevation from swissSURFACE3D at each voxel
4. **Volume**: Sum of (surface - base) × 1m² for all voxels

### Performance
- Processing speed: ~10-20 buildings/second (depends on building size)
- Memory usage: Minimal, processes buildings individually
- Tile caching: Currently loads tiles on demand

## Known Limitations

- Buildings spanning multiple tiles are handled correctly
- Missing height data results in `status: no_height_data`
- Negative heights (underground portions) are set to 0
- Accuracy depends on height model resolution (0.5m)

## Data Sources

- **Amtliche Vermessung**: [geodienste.ch](https://www.geodienste.ch)
- **Height Models**: [Federal Office of Topography swisstopo](https://www.swisstopo.admin.ch)
- **Coordinate System**: [Swiss coordinate system](https://www.swisstopo.admin.ch/en/knowledge-facts/surveying-geodesy/reference-systems.html)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Federal Office of Topography swisstopo for providing the height models
- Swiss cadastral surveying authorities for the building footprint data
