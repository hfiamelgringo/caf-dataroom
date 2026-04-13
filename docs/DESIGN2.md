# Design System v2: PFA Enterprise

Derived from the PFA Dataroom Explorer reference site. Modern enterprise aesthetic — professional, data-driven, trustworthy.

## 1. Color Palette

### Primary
- **PFA Blue**: `#00517b` — primary brand, nav, headings
- **PFA Blue Dark**: `#003a57` — hover states, deeper accents
- **PFA Blue Light**: `#bbe1f8` — highlights, selected states
- **Cover Blue**: `#1a6a8a` — hero backgrounds
- **Section Blue**: `#0c5b82` — section accents

### Accent
- **PFA Orange**: `#df7f43` — CTAs, dividers, active indicators
- **PFA Orange Light**: `#f5d4b8` — light accent backgrounds
- **Section Green**: `#9aae6b` — positive indicators, secondary accent

### Neutrals
- **White**: `#ffffff` — card backgrounds, primary surface
- **Light Gray**: `#f4f7fa` — page background, section alternation
- **Border**: `#e0e6ed` — card borders, separators
- **Dark Text**: `#333333` — primary body text
- **Gray Text**: `#666666` — secondary/muted text
- **Callout BG**: `#edf6f9` — highlighted content areas

## 2. Typography

**Single font family**: `'Segoe UI', system-ui, -apple-system, sans-serif`

No custom fonts. System stack for speed and native feel.

### Scale
| Role | Size | Weight | Spacing |
|------|------|--------|---------|
| Hero H1 | `clamp(32px, 5vw, 52px)` | 800 | -1px |
| Section H2 | 28px | 700 | 0 |
| Card Title | 16px | 600 | 0 |
| Body | 15px | 400 | 0, line-height 1.6 |
| Label | 12px | 700 | 2px, uppercase |
| Small | 11px | 700 | 0 |

## 3. Layout

- **Max-width**: 1280px, centered
- **Section padding**: 60px vertical, 24px horizontal
- **Card padding**: 22px
- **Grid gaps**: 14px-32px
- **Grid pattern**: `repeat(auto-fit, minmax(280px, 1fr))`

## 4. Components

### Cards
- White background, `1px solid #e0e6ed`
- `border-radius: 12px`
- Shadow: `0 4px 12px rgba(0,0,0,0.1)`
- Hover: shadow `0 8px 30px rgba(0,0,0,0.12)`, translateY(-2px)
- Optional 4px colored top bar

### Buttons
- Primary: `#00517b` bg, white text, `border-radius: 6px`, padding `14px 20px`
- Hover: darken to `#003a57`
- Pills/chips: `border-radius: 20px`

### Hero
- Gradient: `135deg, #00517b 0%, #1a6a8a 55%, #0c5b82 100%`
- Decorative circles with low-opacity white/orange
- Orange divider bar: `80px × 4px`
- White text, muted white for subtitle

### Navigation
- Sticky, 64px height
- Items: `padding: 8px 14px`, `border-radius: 6px`
- Hover: `rgba(255,255,255,0.12)` overlay

## 5. Visual Effects

### Shadows
- Rest: `0 4px 12px rgba(0,0,0,0.1)`
- Hover: `0 8px 30px rgba(0,0,0,0.12)`
- Subtle: `0 1px 3px rgba(0,0,0,0.08)`

### Animations
- Fade-in: `fadeInUp 0.5s ease`, staggered 0.05s
- Hover transitions: `0.15s-0.25s ease`
- Card top bar: `scaleX(0.3) → scaleX(1)` on hover

### Border Radius
- Standard: 8px
- Cards: 12px
- Pills: 20px+

## 6. Design Philosophy

- **Enterprise modern** — not SaaS playful, not government stiff
- **Data-driven**: grids, charts, structured information
- **Subtle depth**: shadows for layering, not flat
- **Warm professional**: blue + orange palette feels approachable but serious
- **System fonts**: fast, native, no loading delay
- **Responsive-native**: clamp values, auto-fit grids
