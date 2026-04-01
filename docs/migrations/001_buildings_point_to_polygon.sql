-- ============================================================================
-- Migration: Convert buildings.geog from POINT to POLYGON
-- ============================================================================
--
-- Purpose: Change building geometry from point (centroid) to polygon (footprint)
--
-- Prerequisites:
--   - landcovers table has polygon geometries with building_id FK
--   - buildings table has lon/lat columns for point coordinates (kept for matching)
--
-- Steps:
--   1. Add new polygon column
--   2. Copy polygons from linked landcovers
--   3. Drop old point column
--   4. Rename new column to geog
--   5. Recreate spatial index
--
-- Note: Buildings without linked landcovers will have NULL geometry
-- and won't appear on the map until they're matched to footprints.
--
-- ============================================================================

-- Step 1: Add new polygon column (nullable initially)
ALTER TABLE public.buildings
ADD COLUMN geog_polygon geography(POLYGON, 4326);

-- Step 2: Copy polygon geometry from linked landcovers
-- Uses the building_id foreign key in landcovers to find matching footprints
UPDATE public.buildings b
SET geog_polygon = lc.geog
FROM public.landcovers lc
WHERE lc.building_id = b.id
  AND lc.type = 'building';  -- Only use building-type landcovers

-- Step 3: Check how many buildings were matched
-- Run this SELECT to verify before proceeding:
-- SELECT
--   COUNT(*) AS total_buildings,
--   COUNT(geog_polygon) AS buildings_with_polygon,
--   COUNT(*) - COUNT(geog_polygon) AS buildings_without_polygon
-- FROM public.buildings;

-- Step 4: Drop the old point geometry column
ALTER TABLE public.buildings DROP COLUMN geog;

-- Step 5: Rename the new column to geog
ALTER TABLE public.buildings RENAME COLUMN geog_polygon TO geog;

-- Step 6: Recreate spatial index for query performance
DROP INDEX IF EXISTS idx_buildings_geog_gist;
CREATE INDEX idx_buildings_geog_gist ON public.buildings USING GIST (geog);

-- Step 7: Update the updated_at timestamp for migrated records
UPDATE public.buildings
SET updated_at = NOW()
WHERE geog IS NOT NULL;

-- ============================================================================
-- Verification Queries (run after migration)
-- ============================================================================

-- Check geometry types
-- SELECT DISTINCT ST_GeometryType(geog::geometry) FROM public.buildings WHERE geog IS NOT NULL;

-- Count buildings by polygon status
-- SELECT
--   CASE WHEN geog IS NOT NULL THEN 'Has Polygon' ELSE 'No Polygon' END AS status,
--   COUNT(*)
-- FROM public.buildings
-- GROUP BY 1;

-- Test MVT generation still works
-- SELECT mvt_tile('buildings', 14, 8594, 5747, ARRAY['id', 'label', 'status']);
