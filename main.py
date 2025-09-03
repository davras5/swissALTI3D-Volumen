#!/usr/bin/env python3
"""
Building Volume Calculator for Swiss Buildings
Uses swissALTI3D and swissSURFACE3D to calculate building volumes from AV data
"""

import argparse
import sys
from pathlib import Path
import geopandas as gpd
import rasterio
import numpy as np
from shapely.geometry import Point
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

class BuildingVolumeCalculator:
    def __init__(self, alti3d_dir, surface3d_dir):
        self.alti3d_dir = Path(alti3d_dir)
        self.surface3d_dir = Path(surface3d_dir)
        self.tile_size = 1000
        self.voxel_size = 1.0
        
    def load_buildings_from_av(self, av_gpkg_path):
        print(f"Loading buildings from {av_gpkg_path}...")
        lcsf = gpd.read_file(av_gpkg_path, layer='lcsf')
        buildings = lcsf[lcsf['Art'] == 'Gebaeude'].copy()
        print(f"Found {len(buildings)} buildings")
        
        if 'EGID' not in buildings.columns:
            buildings['EGID'] = [f"building_{i}" for i in range(len(buildings))]
            
        if buildings.crs != 'EPSG:2056':
            buildings = buildings.to_crs('EPSG:2056')
            
        return buildings
    
    def get_required_tiles(self, bounds):
        minx, miny, maxx, maxy = bounds
        min_tile_x = int(minx / 1000)
        min_tile_y = int(miny / 1000)
        max_tile_x = int(maxx / 1000)
        max_tile_y = int(maxy / 1000)
        
        tiles = []
        for x in range(min_tile_x, max_tile_x + 1):
            for y in range(min_tile_y, max_tile_y + 1):
                tiles.append(f"{x:04d}_{y:04d}")
        return tiles
    
    def create_voxel_points(self, polygon):
        bounds = polygon.bounds
        x_min = np.floor(bounds[0] / self.voxel_size) * self.voxel_size
        y_min = np.floor(bounds[1] / self.voxel_size) * self.voxel_size
        x_max = np.ceil(bounds[2] / self.voxel_size) * self.voxel_size
        y_max = np.ceil(bounds[3] / self.voxel_size) * self.voxel_size
        
        x_coords = np.arange(x_min + self.voxel_size/2, x_max, self.voxel_size)
        y_coords = np.arange(y_min + self.voxel_size/2, y_max, self.voxel_size)
        
        points = []
        for x in x_coords:
            for y in y_coords:
                point = Point(x, y)
                if polygon.contains(point) or polygon.touches(point):
                    points.append((x, y))
        return points
    
    def sample_heights_from_tiles(self, points, tiles, model_type):
        heights = np.full(len(points), np.nan)
        
        for tile_name in tiles:
            if model_type == 'alti3d':
                possible_names = [
                    f"swissalti3d_2019_{tile_name}_0.5_2056_5728.tif",
                    f"swissALTI3D_{tile_name}.tif"
                ]
                base_dir = self.alti3d_dir
            else:
                possible_names = [
                    f"swisssurface3d_raster_2019_{tile_name}_0.5_2056_5728.tif",
                    f"swissSURFACE3D_{tile_name}.tif"
                ]
                base_dir = self.surface3d_dir
                
            filename = None
            for name in possible_names:
                test_path = base_dir / name
                if test_path.exists():
                    filename = test_path
                    break
            
            if filename is None:
                continue
                
            try:
                with rasterio.open(filename) as src:
                    sampled = list(src.sample(points, indexes=1))
                    for i, value in enumerate(sampled):
                        if not np.isnan(value[0]) and value[0] != src.nodata:
                            heights[i] = value[0]
            except Exception as e:
                print(f"Error reading {filename}: {e}", file=sys.stderr)
                
        return heights
    
    def calculate_building_volume(self, polygon, egid=None):
        voxel_points = self.create_voxel_points(polygon)
        
        if len(voxel_points) == 0:
            return {
                'EGID': egid,
                'volume_m3': 0,
                'footprint_area_m2': polygon.area,
                'mean_height_m': 0,
                'base_height_m': np.nan,
                'status': 'no_voxels'
            }
        
        tiles = self.get_required_tiles(polygon.bounds)
        terrain_heights = self.sample_heights_from_tiles(voxel_points, tiles, 'alti3d')
        surface_heights = self.sample_heights_from_tiles(voxel_points, tiles, 'surface3d')
        
        valid_mask = ~(np.isnan(terrain_heights) | np.isnan(surface_heights))
        valid_terrain = terrain_heights[valid_mask]
        valid_surface = surface_heights[valid_mask]
        
        if len(valid_terrain) == 0:
            return {
                'EGID': egid,
                'volume_m3': 0,
                'footprint_area_m2': polygon.area,
                'mean_height_m': 0,
                'base_height_m': np.nan,
                'status': 'no_height_data'
            }
        
        base_height = np.min(valid_terrain)
        building_heights = np.maximum(valid_surface - base_height, 0)
        volume = np.sum(building_heights) * (self.voxel_size ** 2)
        
        return {
            'EGID': egid,
            'volume_m3': round(volume, 2),
            'footprint_area_m2': round(polygon.area, 2),
            'mean_height_m': round(np.mean(building_heights), 2),
            'max_height_m': round(np.max(building_heights), 2),
            'base_height_m': round(base_height, 2),
            'status': 'success'
        }
    
    def process_buildings(self, buildings_gdf, limit=None):
        if limit:
            buildings_gdf = buildings_gdf.head(limit)
            
        results = []
        total = len(buildings_gdf)
        
        for idx, row in buildings_gdf.iterrows():
            print(f"Processing building {idx + 1}/{total}", end='\r')
            egid = row.get('EGID', f"building_{idx}")
            result = self.calculate_building_volume(row.geometry, egid)
            results.append(result)
        
        print(f"\nProcessed {total} buildings")
        return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(description='Calculate building volumes from Swiss geodata')
    parser.add_argument('av_gpkg', help='Path to av_2056.gpkg file')
    parser.add_argument('alti3d_dir', help='Directory containing swissALTI3D tiles')
    parser.add_argument('surface3d_dir', help='Directory containing swissSURFACE3D tiles')
    parser.add_argument('-o', '--output', default='building_volumes.csv', 
                       help='Output CSV file (default: building_volumes.csv)')
    parser.add_argument('-g', '--gpkg', help='Output GeoPackage file with geometries')
    parser.add_argument('-l', '--limit', type=int, help='Limit number of buildings to process')
    parser.add_argument('-b', '--bbox', nargs=4, type=float, metavar=('MINX', 'MINY', 'MAXX', 'MAXY'),
                       help='Process only buildings within bounding box')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not Path(args.av_gpkg).exists():
        print(f"Error: AV file not found: {args.av_gpkg}", file=sys.stderr)
        return 1
        
    if not Path(args.alti3d_dir).is_dir():
        print(f"Error: ALTI3D directory not found: {args.alti3d_dir}", file=sys.stderr)
        return 1
        
    if not Path(args.surface3d_dir).is_dir():
        print(f"Error: SURFACE3D directory not found: {args.surface3d_dir}", file=sys.stderr)
        return 1
    
    # Initialize calculator
    calc = BuildingVolumeCalculator(args.alti3d_dir, args.surface3d_dir)
    
    # Load buildings
    try:
        buildings = calc.load_buildings_from_av(args.av_gpkg)
    except Exception as e:
        print(f"Error loading AV data: {e}", file=sys.stderr)
        return 1
    
    # Apply bounding box filter if specified
    if args.bbox:
        minx, miny, maxx, maxy = args.bbox
        buildings = buildings.cx[minx:maxx, miny:maxy]
        print(f"Filtered to {len(buildings)} buildings within bounding box")
    
    # Process buildings
    results = calc.process_buildings(buildings, limit=args.limit)
    
    # Save results
    results.to_csv(args.output, index=False)
    print(f"\nResults saved to: {args.output}")
    
    # Save GeoPackage if requested
    if args.gpkg:
        buildings_with_volumes = buildings.merge(results, on='EGID', how='left')
        buildings_with_volumes.to_file(args.gpkg, driver="GPKG")
        print(f"GeoPackage saved to: {args.gpkg}")
    
    # Print summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    successful = results[results['status'] == 'success']
    print(f"Successful: {len(successful)}/{len(results)}")
    if len(successful) > 0:
        print(f"Total volume: {successful['volume_m3'].sum():,.0f} m³")
        print(f"Avg volume: {successful['volume_m3'].mean():,.0f} m³")
        print(f"Avg height: {successful['mean_height_m'].mean():.1f} m")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())