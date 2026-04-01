# MapLibre GL JS Frontend

This document covers the map frontend architecture in the OpenBuildings application.

## Overview

**MapLibre GL JS Version:** 4.7.1

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  User Click     │────▶│  Layer Query    │────▶│  Supabase API   │
│                 │     │  (Vector Tile)  │     │  (Detail Fetch) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │                        │
                              ▼                        ▼
                        Feature ID              Full Record
                        from MVT tile           for Panel Display
```

## Module Architecture

The application uses code-splitting for performance:

| Module | Path | Load Strategy |
|--------|------|---------------|
| Main App | `js/app.js` | Immediate |
| 3D Mode | `js/modules/3d-mode.js` | Lazy (dynamic import) |
| Search | `js/modules/search.js` | Lazy (dynamic import) |

```javascript
// Example lazy loading pattern
const { setup3DMode, teardown3DMode } = await import('./modules/3d-mode.js');
```

---

## Map Initialization

```javascript
const map = new maplibregl.Map({
  container: 'map',
  style: `https://api.protomaps.com/styles/v2/white.json?key=${PROTOMAPS_KEY}`,
  center: [8.2275, 46.8182], // Switzerland center
  zoom: 7,
  maxBounds: [[5.5, 45.5], [11.0, 48.0]] // Restrict to Switzerland
});
```

---

## Layer Architecture

### Sources

All data layers use vector tile sources from Supabase Edge Functions:

| Source | Type | Zoom Range | Geometry |
|--------|------|------------|----------|
| `buildings` | vector | 0-14 | Polygon |
| `parcels` | vector | 10-14 | Polygon |
| `landcovers` | vector | 10-14 | Polygon |
| `terrain-dem` | raster-dem | 0-15 | Elevation (lazy) |
| `switzerland-border` | geojson | 0-14 | LineString |

### Layers (render order, bottom to top)

| Layer ID | Source | Type | Visibility |
|----------|--------|------|------------|
| `switzerland-border-line` | GeoJSON | line | Always |
| `parcels-fill` | parcels | fill | zoom ≥ 12 |
| `parcels-outline` | parcels | line | zoom ≥ 12 |
| `landcovers-fill` | landcovers | fill / fill-extrusion | zoom ≥ 12 |
| `landcovers-outline` | landcovers | line | zoom ≥ 12 |
| `buildings-heat` | buildings | heatmap | zoom < 12 |
| `buildings-fill` | buildings | fill | zoom ≥ 10 |
| `buildings-outline` | buildings | line | zoom ≥ 10 |
| `sky` | none | sky | 3D mode only |

### Layer Colors

| Layer | Default | Selected | Opacity |
|-------|---------|----------|---------|
| Buildings | Status-based (see below) | `#059669` (green) | 0.3 → 1.0 by zoom |
| Parcels | `#1e3a5f` (deep blue) | `#059669` (green) | 0.1 / 0.25 |
| Landcovers | `#8b5cf6` (purple) | `#059669` (green) | 0.2 / 0.4 |

### Building Status Colors

Buildings are colored by construction status using a match expression:

| Status Code | Label | Color |
|-------------|-------|-------|
| `1004` | Bestehend (Existing) | `#059669` (emerald) |
| `1003` | Im Bau (Under construction) | `#eab308` (yellow) |
| `1002` | Bewilligt (Approved) | `#0891b2` (cyan) |
| `1001` | Projektiert (Planned) | `#6366f1` (indigo) |
| `1005` | Nicht nutzbar (Unusable) | `#9ca3af` (gray) |
| `1007` | Abgebrochen (Demolished) | `#dc2626` (red) |
| `1008` | Nicht realisiert (Not realized) | `#6b7280` (dark gray) |

```javascript
// Color expression builder
const matchExpression = ['match', ['get', 'status'],
  '1004', '#059669',
  '1003', '#eab308',
  // ... etc
  '#475569' // fallback
];
```

---

## State Management

### Application State

```javascript
const state = {
  selectedBuilding: null,    // Building ID or null
  selectedParcel: null,      // Parcel ID or null
  selectedLandcover: null,   // Landcover ID or null
  is3DMode: false,           // Terrain enabled
  searchMarker: null,        // MapLibre Marker instance
  markerClickHandled: false  // Click debounce flag
};
```

### Selection Tracking (Paint Optimization)

```javascript
let lastRenderedBuildingSelection = undefined;
let lastRenderedBuildingColorScheme = undefined;
const lastRenderedPolygonSelection = { parcels: undefined, landcovers: undefined };
```

### URL Parameters (Deep Linking)

| Parameter | Type | Description |
|-----------|------|-------------|
| `zoom` | float | Map zoom level |
| `lon` | float | Center longitude |
| `lat` | float | Center latitude |
| `building` | int | Selected building ID |
| `parcel` | int | Selected parcel ID |
| `landcover` | int | Selected landcover ID |
| `3d` | bool | Enable 3D terrain |
| `marker` | bool | Show search marker at lon/lat |

**Example:** `?zoom=14.50&lon=8.54170&lat=47.37690&building=123&3d=true`

---

## Event Handlers

### Map Events

| Event | Purpose |
|-------|---------|
| `load` | Add layers and set initial view |
| `mousemove` | Display mouse coordinates (throttled via RAF) |
| `mouseout` | Clear coordinate display |
| `click` | Query rendered features (parcels/landcover) |
| `contextmenu` | Open right-click context menu |
| `movestart` | Close context menu on map movement |
| `moveend` | Update URL parameters |
| `rotate` | Rotate compass indicator (throttled via RAF) |
| `idle` | Re-add layers after style change |

### Layer Event Management

```javascript
const layerHandlers = {
  buildings: {
    click: (e) => {
      // Use click location for polygon features
      const coords = [e.lngLat.lng, e.lngLat.lat];
      selectBuilding(e.features[0].properties.id, coords);
    },
    mouseenter: () => { map.getCanvas().style.cursor = 'pointer'; },
    mouseleave: () => { map.getCanvas().style.cursor = ''; }
  },
  parcels: cursorHandlers,
  landcovers: cursorHandlers
};

function manageLayerHandlers(action, layerName, layerId) {
  const handlers = layerHandlers[layerName];
  const method = action === 'add' ? 'on' : 'off';
  Object.entries(handlers).forEach(([event, handler]) => {
    map[method](event, layerId, handler);
  });
}
```

---

## Feature Selection

### Click Priority (highest to lowest)

1. **Buildings** - Direct layer click handler on `buildings-fill`
2. **Landcovers** - Query `landcovers-fill` at click point
3. **Parcels** - Query `parcels-fill` at click point

### Selection Flow

```
Click Event
    │
    ├─▶ Building layer? ──▶ selectBuilding(id, coords)
    │                            │
    │                            ▼
    │                      Show panel immediately
    │                      (coords from tile)
    │
    └─▶ Query rendered features
            │
            ├─▶ Landcover hit? ──▶ selectLandcover(id)
            │                            │
            └─▶ Parcel hit? ────▶ selectParcel(id)
                                         │
                                         ▼
                                   Fetch from Supabase
                                   Show panel with details
```

### Data Fetched per Feature Type

| Type | Columns from Supabase |
|------|----------------------|
| Building | `id, label, egid, lon, lat` (+ address, dimensions, features) |
| Parcel | `id, label, egrid, type` (+ area, zone) |
| Landcover | `id, label, type, egid` (+ dimensions) |

---

## Performance Optimizations

### Caching

| Cache | Max Size | Purpose |
|-------|----------|---------|
| `wkbCache` | 100 | Parsed WKB geometries (LRU) |
| `featureCache.building` | 50 | Fetched building records (LRU) |
| `featureCache.parcel` | 50 | Fetched parcel records (LRU) |
| `featureCache.landcovers` | 50 | Fetched landcover records (LRU) |

### Throttling & Debouncing

| Operation | Strategy | Delay |
|-----------|----------|-------|
| Mouse coordinates | requestAnimationFrame | ~16ms |
| Compass rotation | requestAnimationFrame | ~16ms |
| Search input | Debounce | 300ms |
| Building click | Timeout flag | 100ms |

### Code Splitting

Modules are loaded on-demand to reduce initial bundle size:

```javascript
// 3D mode loaded only when user enables it
if (enable3D) {
  const { setup3DMode } = await import('./modules/3d-mode.js');
  await setup3DMode();
}

// Search module loaded when search panel opens
const { initSearch } = await import('./modules/search.js');
```

### Paint Property Optimization

Selection changes track previous state to skip unnecessary repaints:

```javascript
// Skip if selection hasn't changed
if (lastRenderedBuildingSelection === currentSelection) return;
```

### Style Change Handling

Uses `idle` event (more reliable than `load`) for re-adding layers:

```javascript
map.setStyle(newStyleUrl);
map.once('idle', async () => {
  await addSwitzerlandBorder();
  addParcelsLayer();
  addLandcoverLayer();
  addBuildingsLayer();
});
```

---

## 3D Mode

### Module Location

`js/modules/3d-mode.js` - Lazy-loaded on first 3D toggle

### Terrain Source

```javascript
{
  type: 'raster-dem',
  tiles: ['https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'],
  encoding: 'terrarium',
  tileSize: 256,
  maxzoom: 15
}
```

### Landcover Extrusion

In 3D mode, `landcovers-fill` converts from `fill` to `fill-extrusion`:

| Property | Value |
|----------|-------|
| `fill-extrusion-height` | 10m |
| `fill-extrusion-base` | 0m |
| `fill-extrusion-opacity` | 0.8 (default) / 0.6 (selected) |

### Sky Layer

```javascript
{
  id: 'sky',
  type: 'sky',
  paint: {
    'sky-type': 'atmosphere',
    'sky-atmosphere-sun': [0.0, 90.0],
    'sky-atmosphere-sun-intensity': 15
  }
}
```

### Camera Animation

```javascript
// Synchronized terrain and camera animation
// Easing: ease-out cubic
const easing = 1 - Math.pow(1 - progress, 3);
```

### Camera Settings

| Setting | Value |
|---------|-------|
| Pitch (3D) | 60° |
| Pitch (2D) | 0° |
| Terrain exaggeration | 1.5x |
| Animation duration | 1000ms |

---

## Search

### Module Location

`js/modules/search.js` - Lazy-loaded when search panel opens

### API Endpoint (Swisstopo)

```
https://api3.geo.admin.ch/rest/services/ech/SearchServer
  ?searchText={query}
  &type=locations
  &type=layers
  &lang=de
  &sr=4326
```

### Result Types

| Origin | Action |
|--------|--------|
| `address`, `zipcode`, `sn25`, `gg25`, `district`, `canton`, `gazetteer` | Fly to location, add marker |
| `layer` | Displayed but disabled |

### Search Marker

```javascript
state.searchMarker = new maplibregl.Marker({
  element: createSearchMarkerElement()
})
  .setLngLat([lon, lat])
  .addTo(map);
```

---

## Basemap

### Provider

[Protomaps](https://protomaps.com/) vector tiles with multiple styles:

| Style | Key | Description |
|-------|-----|-------------|
| Light (default) | `white` | Clean, minimal |
| Streets | `light` | Road emphasis |
| Outdoors | `outdoors` | Terrain-friendly |
| Satellite | `satellite` | Aerial imagery |

### Style Change Handling

When basemap changes, layers are re-added in order:
1. Switzerland border
2. Parcels
3. Landcovers
4. Buildings
5. Re-apply color scheme
6. Re-apply 3D terrain if active

---

## Configuration Constants

### Map Settings (`MAP_CONFIG`)

| Constant | Value | Description |
|----------|-------|-------------|
| `defaultZoom` | 7 | Initial zoom (Switzerland overview) |
| `detailZoom` | 14 | Zoom for feature selection |
| `searchZoom` | 17 | Zoom for search results |
| `quickDuration` | 300ms | Zoom button animation |
| `standardDuration` | 1000ms | Fit bounds / 3D animation |
| `flyDuration` | 1500ms | Fly-to animation |
| `pitch3D` | 60° | 3D mode camera pitch |
| `terrainExaggeration` | 1.5 | Terrain height multiplier |
| `boundsPadding` | 40px | Fit bounds padding |

### UI Timing (`UI_TIMING`)

| Constant | Value | Description |
|----------|-------|-------------|
| `clickDebounce` | 100ms | Prevent double-click handling |
| `searchDebounce` | 300ms | Search input delay |
| `toastDuration` | 4000ms | Toast display time |
| `toastFadeOut` | 300ms | Toast fade animation |

### Geographic Bounds

```javascript
const SWITZERLAND_BOUNDS = [5.9559, 45.818, 10.4921, 47.8084];
```

---

## Custom Controls

### Zoom Controls

```javascript
document.getElementById('zoomInBtn').addEventListener('click', () => {
  map.zoomIn({ duration: MAP_CONFIG.quickDuration });
});
```

### Scale Control

```javascript
const scaleControl = new maplibregl.ScaleControl({ unit: 'metric' });
map.on('load', () => {
  scaleControl.onAdd(map);
  scaleContainer.appendChild(scaleControl._container);
});
```

### Compass Control

- Reset north/pitch with `map.easeTo({ bearing: 0, pitch: 0 })`
- Rotates compass icon with `map.on('rotate')` event
- Uses `requestAnimationFrame` for throttling

### Home Button

```javascript
map.fitBounds(SWITZERLAND_BOUNDS, {
  padding: MAP_CONFIG.boundsPadding,
  duration: MAP_CONFIG.standardDuration
});
```

### Context Menu

- Right-click handler for coordinates, share, print options
- Custom positioning with viewport bounds checking

---

## Error Handling

### Fatal Errors (Initialization)

Displayed in loading overlay:
- MapLibre GL not loaded
- Supabase client not loaded

```javascript
if (typeof maplibregl === 'undefined') {
  showFatalError('Map library failed to load...');
  return;
}
```

### Runtime Errors

Displayed as toast notifications:
- Feature fetch failures
- Search API failures
- Navigation failures

### Toast Types

| Type | Color | Icon |
|------|-------|------|
| `error` | Red | X circle |
| `success` | Green | Check circle |
| `info` | Blue | Info circle |

---

## File Structure

| File | Purpose |
|------|---------|
| `index.html` | MapLibre library loading (CDN) |
| `js/app.js` | Main map initialization, layers, events |
| `js/modules/3d-mode.js` | 3D terrain and camera management |
| `js/modules/search.js` | Search and marker placement |
| `css/styles.css` | Map container and control styling |
