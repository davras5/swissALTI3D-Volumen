# Supabase Infrastructure

This document covers the Supabase components that power the vector tile system for map rendering.

## Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Mapbox GL JS   │────▶│  Edge Function  │────▶│  PostGIS (DB)   │
│  (Frontend)     │◀────│  (tiles)        │◀────│  mvt_tile()     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
       Requests              Serves               Generates
     /tiles/{z}/{x}/{y}    MVT binary            Vector tiles
```

## Components

### 1. tiles (Edge Function)

**Purpose:** HTTP endpoint that serves Mapbox Vector Tiles.

**Endpoint:** `/tiles/{table}/{z}/{x}/{y}.pbf`

**Supported tables:**
- `buildings` - Building points (columns: `id`, `label`)
- `parcels` - Property boundary polygons (columns: `id`, `label`, `type`)
- `landcovers` - Land cover polygons (columns: `id`, `label`, `type`)
- `projects` - Construction project polygons (columns: `id`, `label`)

**Caching strategy:**
| Zoom Level | Cache Duration | Use Case |
|------------|----------------|----------|
| < 10 | 24 hours | Country/region view |
| 10-13 | 1 hour | City view |
| 14+ | 5 minutes | Street/building view |

**CORS:** Allows all origins (`*`), `GET` and `OPTIONS` methods.

---

### 2. MVT Tile Generator (Database Function)

**Function:** `mvt_tile(table_name, z, x, y, columns)`

**Purpose:** Generates Mapbox Vector Tiles from PostGIS geometries.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `table_name` | text | Table to query (buildings, parcels, landcovers, projects) |
| `z` | integer | Zoom level |
| `x` | integer | Tile column |
| `y` | integer | Tile row |
| `columns` | text[] | Array of column names to include (default: `['id', 'label']`) |

**Features:**
- Converts geometries to MVT binary format
- Dynamic column selection for minimal tile size
- Returns base64-encoded data (decoded by edge function)
- Marked `STABLE PARALLEL SAFE` for concurrent query optimization
- Uses `geography` type for bounds to ensure GIST index usage

**Security:**
- Table name whitelist validation (only allowed tables)
- Column name sanitization (regex: `^[a-z_][a-z0-9_]*$`)
- Prevents SQL injection via parameterized queries

**Permissions:**
```sql
GRANT EXECUTE ON FUNCTION mvt_tile(...) TO authenticated;
GRANT EXECUTE ON FUNCTION mvt_tile(...) TO anon;
```

**Technical parameters:**
| Parameter | Value | Description |
|-----------|-------|-------------|
| Extent | 4096 | Tile coordinate space (Mapbox standard) |
| Buffer | 256 | Pixel buffer for label/symbol overlap |
| Clip | true | Clips geometries to tile bounds |

**Example:**
```sql
-- Buildings with default columns
SELECT mvt_tile('buildings', 14, 8594, 5747);

-- Parcels with type for styling
SELECT mvt_tile('parcels', 14, 8594, 5747, ARRAY['id', 'label', 'type']);
```

---

### 3. Create Spatial Indexes (SQL Query)

**Purpose:** Creates GIST indexes for fast spatial queries.

**When to run:**
- After initial table creation
- After bulk data imports
- If tile queries become slow

**Indexes created:**
| Table | Index | Type |
|-------|-------|------|
| buildings | `idx_buildings_geog_gist` | GIST (spatial) |
| buildings | `idx_buildings_egid` | BTREE |
| parcels | `idx_parcels_geog_gist` | GIST (spatial) |
| parcels | `idx_parcels_egrid` | BTREE |
| landcovers | `idx_landcovers_geog_gist` | GIST (spatial) |
| landcovers | `idx_landcovers_egid` | BTREE |
| projects | `idx_projects_geog_gist` | GIST (spatial) |
| projects | `idx_projects_eproid` | BTREE |

**Performance impact:** Reduces query time from ~500-2000ms to ~5-50ms.

---

## Layer Hierarchy

Layers are rendered in this order (bottom to top):

1. **Parcels** - Property boundaries (deep blue)
2. **Landcovers** - Land cover polygons (purple)
3. **Buildings** - Building points (slate/green when selected)
4. **Projects** - Construction projects (when enabled)

---

## Environment Variables

Required for the edge function:

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Project URL (auto-set) |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (auto-set) |

---

## Troubleshooting

**Tiles not loading:**
1. Check edge function logs in Supabase dashboard
2. Verify table exists and has data
3. Ensure spatial indexes are created

**Slow tile loading:**
1. Run the Create Spatial Indexes SQL below
2. Run `ANALYZE` on tables
3. Check edge function logs for query times

**Empty tiles:**
1. Verify data exists in the requested tile bounds
2. Check that `geog` column has valid geometries
3. Test with: `SELECT COUNT(*) FROM {table} WHERE geog IS NOT NULL`

**Verifying index usage:**
```sql
-- Should show "Index Scan using idx_buildings_geog_gist"
-- If it shows "Seq Scan", the index is missing or not being used
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM buildings
WHERE geog && ST_Transform(ST_TileEnvelope(14, 8594, 5747), 4326)::geography
LIMIT 1000;
```

---

## Edge Function

```ts
/**
 * ============================================================================
 * VECTOR TILE SERVER - Supabase Edge Function
 * ============================================================================
 * 
 * Serves Mapbox Vector Tiles (MVT) for map layers from PostGIS.
 * 
 * Endpoint: /tiles/{table}/{z}/{x}/{y}.pbf
 * 
 * Supported tables:
 *   - buildings  : Building points (id, label)
 *   - parcels    : Property boundary polygons (id, label, type)
 *   - landcovers : Land cover polygons (id, label, type)
 *   - projects   : Construction project polygons (id, label)
 * 
 * ============================================================================
 */

import "jsr:@supabase/functions-js/edge-runtime.d.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

/**
 * Column configuration per table.
 * Only these columns are included in vector tiles to minimize tile size.
 * Additional data is fetched on-demand via detail API.
 */
const TABLE_CONFIG: Record<string, { columns: string[] }> = {
  buildings:  { columns: ['id', 'label', 'status'] },
  parcels:    { columns: ['id', 'label', 'type'] },
  landcovers: { columns: ['id', 'label', 'type', 'building_category', 'building_construction_period'] },
  projects:   { columns: ['id', 'label'] },
}

const VALID_TABLES = Object.keys(TABLE_CONFIG)

/**
 * CORS headers for cross-origin requests from map clients.
 */
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
}

Deno.serve(async (req) => {
  // CORS Preflight
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders })
  }

  try {
    const url = new URL(req.url)
    
    // Parse: /tiles/{table}/{z}/{x}/{y}.pbf
    const match = url.pathname.match(/\/tiles\/(\w+)\/(\d+)\/(\d+)\/(\d+)\.pbf/)
    
    if (!match) {
      return new Response(
        JSON.stringify({ 
          error: 'Invalid path',
          usage: '/tiles/{table}/{z}/{x}/{y}.pbf',
          tables: VALID_TABLES
        }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const [, table, z, x, y] = match

    // Validate table name
    if (!VALID_TABLES.includes(table)) {
      return new Response(
        JSON.stringify({ 
          error: `Invalid table. Must be one of: ${VALID_TABLES.join(', ')}` 
        }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Initialize Supabase client
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    )

    // Get columns for this table
    const { columns } = TABLE_CONFIG[table]

    // Generate vector tile
    const { data, error } = await supabase.rpc('mvt_tile', {
      table_name: table,
      z: parseInt(z),
      x: parseInt(x),
      y: parseInt(y),
      columns: columns
    })

    if (error) throw error

    // Decode base64 to binary
    const binaryString = atob(data || '')
    const bytes = new Uint8Array(binaryString.length)
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i)
    }

    // Cache duration by zoom level
    const zoomLevel = parseInt(z)
    const maxAge = zoomLevel < 10 ? 86400 : zoomLevel < 14 ? 3600 : 300

    return new Response(bytes, {
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/vnd.mapbox-vector-tile',
        'Cache-Control': `public, max-age=${maxAge}`,
      }
    })

  } catch (err) {
    console.error(err)
    return new Response(
      JSON.stringify({ error: err.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})
```

---

## SQL

### MVT_TILE

```sql
-- =============================================================================
-- MVT_TILE - Generate Mapbox Vector Tiles (Optimized for 1M+ records)
-- =============================================================================
-- 
-- OPTIMIZATIONS:
--   1. Uses && operator for fast bounding box check (O(log n) with GIST index)
--   2. Pre-computes tile bounds outside query to avoid repeated transforms
--   3. Adds feature LIMIT to prevent tile explosion at low zoom levels
--   4. Uses geography type for bounds_4326 to ensure GIST index usage
--
-- PERFORMANCE CHARACTERISTICS:
--   - 500 records:    ~5-20ms per tile
--   - 100K records:   ~10-50ms per tile  
--   - 1M+ records:    ~20-100ms per tile (with proper GIST indexes)
--
-- PREREQUISITES:
--   - GIST spatial index on geog column for each table
--   - Example: CREATE INDEX idx_buildings_geog_gist ON buildings USING GIST (geog);
--
-- =============================================================================

DROP FUNCTION IF EXISTS public.mvt_tile(text, integer, integer, integer, text[]);

CREATE OR REPLACE FUNCTION public.mvt_tile(
  table_name text,
  z integer,
  x integer,
  y integer,
  columns text[] DEFAULT ARRAY['id', 'label']
)
RETURNS text
LANGUAGE plpgsql
STABLE
PARALLEL SAFE
SET search_path = pg_catalog, public, extensions
AS $$
DECLARE
  bounds_3857 geometry;
  bounds_4326 geography;
  mvt bytea;
  col_list text;
  sql text;
  max_features int;
BEGIN
  -- Validate table name (security)
  IF table_name NOT IN ('buildings', 'parcels', 'landcovers', 'projects') THEN
    RAISE EXCEPTION 'Invalid table name: %. Allowed: buildings, parcels, landcovers, projects', table_name;
  END IF;

  -- Pre-compute tile bounds
  bounds_3857 := ST_TileEnvelope(z, x, y);
  bounds_4326 := ST_Transform(bounds_3857, 4326)::geography;

  -- Feature limit by zoom level
  max_features := CASE
    WHEN z < 10 THEN 10000
    WHEN z < 14 THEN 50000
    ELSE 100000
  END;

  -- Build safe column list
  SELECT string_agg(quote_ident(col), ', ')
  INTO col_list
  FROM unnest(columns) AS col
  WHERE col ~ '^[a-z_][a-z0-9_]*$';

  IF col_list IS NULL OR col_list = '' THEN
    col_list := 'id';
  END IF;

  -- Build and execute query
  sql := format(
    $SQL$
    SELECT ST_AsMVT(tile, $2) FROM (
      SELECT
        %s,
        ST_AsMVTGeom(
          ST_Transform(t.geog::geometry, 3857),
          $1,
          4096,
          256,
          true
        ) AS geom
      FROM public.%I t
      WHERE t.geog && $3
        AND ST_Intersects(t.geog, $3)
      LIMIT $4
    ) tile
    $SQL$,
    col_list,
    table_name
  );

  EXECUTE sql INTO mvt USING bounds_3857, table_name, bounds_4326, max_features;

  RETURN encode(COALESCE(mvt, ''), 'base64');
END;
$$;

-- Permissions
GRANT EXECUTE ON FUNCTION public.mvt_tile(text, integer, integer, integer, text[]) TO authenticated;
GRANT EXECUTE ON FUNCTION public.mvt_tile(text, integer, integer, integer, text[]) TO anon;
```

### Create Indexes

```sql
-- =============================================================================
-- SPATIAL INDEXES - Required for vector tile performance
-- =============================================================================
-- Run this after initial table creation or if tile queries become slow.
-- Without these indexes, queries will use slow sequential scans.
-- =============================================================================

-- Buildings
CREATE INDEX IF NOT EXISTS idx_buildings_geog_gist 
ON buildings USING GIST (geog);

CREATE INDEX IF NOT EXISTS idx_buildings_egid 
ON buildings (egid);

-- Parcels
CREATE INDEX IF NOT EXISTS idx_parcels_geog_gist 
ON parcels USING GIST (geog);

CREATE INDEX IF NOT EXISTS idx_parcels_egrid 
ON parcels (egrid);

-- Landcovers
CREATE INDEX IF NOT EXISTS idx_landcovers_geog_gist 
ON landcovers USING GIST (geog);

CREATE INDEX IF NOT EXISTS idx_landcovers_egid 
ON landcovers (egid);

-- Projects
CREATE INDEX IF NOT EXISTS idx_projects_geog_gist 
ON projects USING GIST (geog);

CREATE INDEX IF NOT EXISTS idx_projects_eproid 
ON projects (eproid);

-- Update query planner statistics
ANALYZE buildings, parcels, landcovers, projects;
```
