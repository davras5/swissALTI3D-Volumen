# Style Guide

## Design Vision

### What We Stand For

This is public infrastructure, not a startup. The design should feel:

- **Trustworthy** — like a well-run public service
- **Clear** — complexity absorbed, simplicity delivered
- **Accessible** — no expertise required to navigate
- **Warm** — human, not clinical
- **Precise** — Swiss quality without Swiss coldness

### Design Principles

| Principle | Expression |
|-----------|------------|
| **Let the data speak for itself** | The map is the interface. Spatial data first. Minimal chrome. |
| **Clarity over cleverness** | Every element earns its place. No decoration for decoration's sake. |
| **Data made human** | Numbers in context. Visualizations that inform, not impress. |
| **Quiet confidence** | Professional without being corporate. Trustworthy without being boring. |
| **Inclusive by default** | Accessible contrast, readable type, intuitive patterns. |
| **Open feeling** | Generous whitespace. Breathing room. Nothing cramped. |

### What We're Not

- Not a flashy startup (no gradients, no glassmorphism, no dark mode gimmicks)
- Not enterprise software (no cluttered dashboards, no overwhelming options)
- Not a government form (no bureaucratic coldness, no dated patterns)
- Not a data visualization showpiece (no charts for the sake of charts)
- Not a spreadsheet (tables are for exports, not exploration)

---

## Interface Philosophy

### Map-Centric Design

The map is the primary interface. Everything else supports it.

```
┌─────────────────────────────────────────────────────────────┐
│  [Search]                                    [Filters] [?]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                                                             │
│                                                             │
│                         MAP                                 │
│                                                             │
│                   (full viewport)                           │
│                                                             │
│                                                             │
│                                              ┌────────────┐ │
│                                              │  Building  │ │
│                                              │  Panel     │ │
│                                              │  (on tap)  │ │
│                                              └────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Core Interaction Model

1. **Explore** — Pan and zoom the map. Buildings are visible, clickable.
2. **Select** — Tap a building. A panel slides in with key metrics.
3. **Dive deeper** — Want more? Download a detailed report.

That's it. No dashboards. No multi-step wizards. No configuration screens.

### What Lives Where

| Content | Location |
|---------|----------|
| Building exploration | Map (primary interface) |
| Key metrics | Slide-in panel on selection |
| Search | Minimal top bar |
| Filters | Collapsible, unobtrusive |
| Detailed reports | Downloadable files (PDF, CSV) |
| Documentation | Separate /docs section |

### Simplicity Rules

- **One primary action per view** — on the map, it's "explore and select"
- **Progressive disclosure** — show summary first, details on demand
- **Reports are files** — complex data belongs in exports, not the UI
- **Mobile-first** — if it works on a phone, it works everywhere

---

## Color Palette

### Philosophy

Colors should feel **grounded, natural, and trustworthy** — like public infrastructure you can rely on. The palette draws from:

- Sky and water (trust, openness, data)
- Earth and stone (stability, reliability)
- Growth and renewal (climate, sustainability)

### Primary Colors

| Name | Hex | Usage |
|------|-----|-------|
| **Deep Blue** | `#1e3a5f` | Primary text, headers, key UI elements |
| **Ocean** | `#2563eb` | Interactive elements, links, primary buttons |
| **Sky** | `#3b82f6` | Hover states, secondary actions |

### Accent Colors

| Name | Hex | Usage |
|------|-----|-------|
| **Leaf** | `#059669` | Climate/sustainability indicators, positive states, success |
| **Amber** | `#d97706` | Warnings, attention, energy-related data |
| **Coral** | `#dc2626` | Errors, critical states (use sparingly) |

### Neutral Colors

| Name | Hex | Usage |
|------|-----|-------|
| **Slate 900** | `#0f172a` | Primary text |
| **Slate 700** | `#334155` | Secondary text |
| **Slate 500** | `#64748b` | Tertiary text, captions |
| **Slate 300** | `#cbd5e1` | Borders, dividers |
| **Slate 100** | `#f1f5f9` | Backgrounds, cards |
| **White** | `#ffffff` | Page background, card backgrounds |

### Semantic Colors

| Purpose | Color | Hex |
|---------|-------|-----|
| Success / Positive | Leaf | `#059669` |
| Warning / Attention | Amber | `#d97706` |
| Error / Critical | Coral | `#dc2626` |
| Info / Neutral | Ocean | `#2563eb` |

### Accessibility

- All text meets WCAG AA contrast requirements (4.5:1 minimum)
- Interactive elements have clear focus states
- Never rely on color alone to convey meaning

---

## Typography

### Philosophy

Typography should be **readable, professional, and unobtrusive**. Text delivers information; it shouldn't demand attention for itself.

### Font Stack

**Primary:** Inter

```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

Inter is chosen because:
- Designed for screens, excellent legibility
- Open source (aligns with project values)
- Strong support for tabular/numeric data
- Wide language support

**Monospace (for data/code):** JetBrains Mono

```css
font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
```

### Type Scale

| Name | Size | Weight | Line Height | Usage |
|------|------|--------|-------------|-------|
| **Display** | 48px / 3rem | 700 | 1.1 | Hero headlines only |
| **H1** | 36px / 2.25rem | 700 | 1.2 | Page titles |
| **H2** | 28px / 1.75rem | 600 | 1.3 | Section headers |
| **H3** | 22px / 1.375rem | 600 | 1.4 | Subsection headers |
| **H4** | 18px / 1.125rem | 600 | 1.4 | Card titles, labels |
| **Body** | 16px / 1rem | 400 | 1.6 | Default text |
| **Small** | 14px / 0.875rem | 400 | 1.5 | Captions, metadata |
| **Tiny** | 12px / 0.75rem | 500 | 1.4 | Labels, badges |

### Text Colors

| Context | Color | Usage |
|---------|-------|-------|
| Primary | Slate 900 | Headings, important text |
| Secondary | Slate 700 | Body text |
| Tertiary | Slate 500 | Captions, helper text |
| Disabled | Slate 300 | Inactive elements |
| Link | Ocean | Interactive text |
| Link Hover | Deep Blue | Hovered links |

---

## Spacing & Layout

### Spacing Scale

Base unit: 4px

| Token | Value | Usage |
|-------|-------|-------|
| `xs` | 4px | Tight gaps, icon padding |
| `sm` | 8px | Related elements |
| `md` | 16px | Default spacing |
| `lg` | 24px | Section gaps |
| `xl` | 32px | Major sections |
| `2xl` | 48px | Page sections |
| `3xl` | 64px | Hero spacing |

### Grid

- **Max width:** 1280px (content container)
- **Columns:** 12-column grid
- **Gutter:** 24px
- **Margins:** 16px (mobile), 24px (tablet), 48px (desktop)

### Breakpoints

| Name | Width | Target |
|------|-------|--------|
| `sm` | 640px | Large phones |
| `md` | 768px | Tablets |
| `lg` | 1024px | Small laptops |
| `xl` | 1280px | Desktops |

---

## Components

### Buttons

**Primary Button**
- Background: Ocean (`#2563eb`)
- Text: White
- Padding: 12px 24px
- Border radius: 6px
- Hover: Sky (`#3b82f6`)
- Focus: 2px outline, offset 2px

**Secondary Button**
- Background: White
- Border: 1px Slate 300
- Text: Slate 900
- Hover: Slate 100 background

**Text Button**
- No background
- Text: Ocean
- Hover: Underline

### Cards

- Background: White
- Border: 1px Slate 200 (`#e2e8f0`)
- Border radius: 8px
- Shadow: `0 1px 3px rgba(0,0,0,0.1)`
- Padding: 24px
- Hover (if interactive): Shadow increases, subtle lift

### Forms

Keep forms minimal. The platform is for exploration, not data entry.

**Search Input**
- Large, prominent, always accessible
- Placeholder: "Search by address, EGID, or place..."
- Instant results as you type
- Border: 1px Slate 300, radius 6px
- Focus: Ocean border, light blue ring

**Filters**
- Collapsible panel, hidden by default
- Simple toggles and ranges
- "Reset all" always visible

### Building Panel

When a building is selected, a panel slides in with key metrics.

```
┌─────────────────────────┐
│  Bundeshaus West        │  ← Name/Address (H4)
│  Bern, 3003             │  ← Location (Small, Slate 500)
├─────────────────────────┤
│                         │
│  Volume    12,450 m³    │  ← Key metrics
│  Floors    4 above      │     (clean, scannable)
│  Built     1894         │
│  Heating   District     │
│                         │
├─────────────────────────┤
│  [↓ Download Report]    │  ← Detailed data = export
└─────────────────────────┘
```

- Slides in from right (desktop) or bottom (mobile)
- Dismissable with X or clicking elsewhere
- Key metrics only — details in downloadable report

### Map

The map is the product. Treat it accordingly.

**Basemap**
- Clean, minimal, muted
- Labels readable but not dominant
- Consider: Mapbox Light, CartoDB Positron, or custom
- Terrain context where useful (Switzerland has mountains)

**Building Layer**
- Default: Subtle fill, visible but not overwhelming
- Hover: Slight highlight, cursor change
- Selected: Leaf fill with stronger stroke, panel opens

**Visual Hierarchy on Map**
```
1. Selected building     — Leaf green, strong presence
2. Hovered building      — Ocean blue highlight  
3. Buildings in view     — Subtle gray fill, light stroke
4. Basemap              — Muted, supportive, never competing
```

**Map Controls**
- Zoom: Bottom right, minimal buttons
- Geolocation: Optional, near zoom
- Layers: Only if multiple views exist — keep hidden otherwise
- Scale bar: Small, unobtrusive, bottom left

**Performance**
- Vector tiles for buildings (scalable, fast)
- Clustering at low zoom levels
- Progressive loading — don't block the map

---

## Iconography

### Style

- **Library:** Lucide Icons (open source, consistent, clean)
- **Size:** 20px default, 16px small, 24px large
- **Stroke:** 1.5px
- **Color:** Inherit from text color

### Common Icons

| Concept | Icon |
|---------|------|
| Building | `building-2` |
| Location | `map-pin` |
| Energy | `zap` |
| Climate | `leaf` |
| Data | `database` |
| Search | `search` |
| Filter | `sliders-horizontal` |
| Download | `download` |
| External link | `external-link` |
| Info | `info` |
| Success | `check-circle` |
| Warning | `alert-triangle` |
| Error | `x-circle` |

---

## Imagery

### Photography

When using photography:
- Authentic, documentary style
- Natural lighting
- Real buildings, real places (prefer Swiss/European context)
- Avoid: stock photo feel, overly staged, people pointing at screens

### Illustrations

When using illustrations:
- Clean, geometric, modern
- Limited color palette (2-3 colors max)
- Editorial style, not cartoony
- Avoid: generic tech illustrations, isometric clichés

### Data Visualization

- Simple, purposeful charts
- Clear labels, no chartjunk
- Color used meaningfully, not decoratively
- Always provide context (what does this number mean?)

---

## Voice & Tone

### Writing Principles

| Principle | Do | Don't |
|-----------|-----|-------|
| **Clear** | "This building was constructed in 1985" | "Construction epoch: 1985" |
| **Human** | "We couldn't find that building" | "Error 404: Resource not found" |
| **Honest** | "Volume is estimated (±10%)" | "Volume: 12,450 m³" (without context) |
| **Concise** | "3 floors above ground" | "The building consists of 3 floors above ground level" |

### Labels & UI Text

- Use sentence case ("Building details" not "Building Details")
- Be specific ("Download CSV" not "Download")
- Avoid jargon where possible ("Area" not "GF" unless technical context)

---

## Accessibility

### Requirements

- WCAG 2.1 AA compliance minimum
- Keyboard navigation for all interactions
- Screen reader support
- Reduced motion support
- High contrast mode support

### Checklist

- [ ] Color contrast meets 4.5:1 for text
- [ ] Interactive elements have visible focus states
- [ ] Images have alt text
- [ ] Form fields have associated labels
- [ ] Error messages are clear and helpful
- [ ] No information conveyed by color alone

---

## File Naming

### Assets

```
icon-building.svg
illustration-hero.png
photo-zurich-buildings.jpg
```

### Components

```
Button.tsx
BuildingCard.tsx
MetricDisplay.tsx
```

### Pages

```
/buildings
/buildings/[egid]
/map
/about
/docs
```

---

## Summary

This design system serves the mission: **making public building data truly public.**

The map is the interface. Let the data speak for itself.

Every choice — from the trustworthy blue palette to the minimal chrome to the slide-in building panels — should make users feel:

> "I can understand this. I can use this. This was made for me."

Not for experts. Not for insiders. For everyone.

**Remember:**
- Map first, everything else supports it
- Show summary, export details
- Simple enough for a phone
- Complex data goes in reports, not the UI

---

*Last updated: December 2024*
