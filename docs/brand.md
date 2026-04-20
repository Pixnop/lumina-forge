# Brand — lumina-forge

A local tool for a painterly JRPG (Clair Obscur: Expedition 33). The visual identity should feel **crafted, not corporate**: a small atelier forging glowing things, not a SaaS dashboard. Colour comes from the game's gouache palette; shapes stay geometric and readable at 16×16 px.

## Logo

**Concept.** A stylised blacksmith hammer, tilted 45°, with a single crystalline gem embedded in the head. The gem emits a warm golden glow; a teal rim-light on the opposite edge introduces the secondary accent. Painterly brush-stroke particles drift around the hammer.

**Primary artwork** ships as three SVG variants in `app/public/`:

| File | Background | When to use |
| --- | --- | --- |
| `logo.svg` | navy (`#0B1025`) | dark mode, packaged icons (Tauri, installer), external assets |
| `logo-light.svg` | paper (`#FAF8F3`) | light mode header, on-brand light backgrounds |
| `logo-mark.svg` | transparent, hammer uses `currentColor` | inline in React components — colour follows the parent |

Use the mark over an arbitrary background only when it's inlined as an `<svg>` tag (CSS `color` cannot reach an SVG loaded via `<img>`).

### Recraft prompts

Paste verbatim into Recraft, pick style **Vector / Icon**, aspect **1:1**, generate 4 variants and keep the cleanest.

**Dark version** — goes into `logo.svg`:

```
A minimalist modern app icon on a deep navy background (#0B1025).
At the center, a stylized blacksmith hammer tilted 45°, sculpted from
dark obsidian with sharp bevels. A single crystalline gemstone embedded
in the hammer head emits a warm golden glow (#F4C269) with soft rays
spreading outward as painterly gouache brush strokes. A few floating
geometric particles drift around the hammer, suggesting fragments of
magical paint. Subtle teal rim light (#2CC4B4) on the left edge of the
hammer for color contrast. Flat vector style, clean geometric shapes,
gentle inner glow, no text, square composition, centered subject,
rounded-square icon silhouette with slight padding. Feels like a JRPG
crafting tool rendered in Studio Ghibli x Monument Valley art direction.
```

**Light version** — goes into `logo-light.svg`:

```
A minimalist modern app icon on a warm gouache paper background (#FAF8F3)
with a very subtle warm haze in the upper left and a cool teal haze in
the lower right. At the center, a stylized blacksmith hammer tilted 45°
sculpted from dark ink blue (#1A1F3A) with sharp bevels. A single
crystalline gemstone embedded in the hammer head emits a warm golden
glow (#F4C269) with soft rays spreading outward as painterly gouache
brush strokes. A few floating geometric particles drift around the
hammer — darker ochre (#C98F3A) and teal (#2CC4B4). Subtle teal rim
light on the left edge of the hammer. Flat vector style, clean
geometric shapes, no text, square composition, centered subject,
rounded-square icon silhouette with slight padding. Hand-painted
children's book meets modern UI icon.
```

## Palette

| Role | Hex | Usage |
| --- | --- | --- |
| Background / navy | `#0B1025` | dark-mode background, logo background |
| Background / paper | `#FAF8F3` | light-mode background (gouache paper) |
| Primary / Lumina Gold | `#F4C269` | CTAs, active highlights, gem in the logo |
| Secondary / Forge Teal | `#2CC4B4` | links, secondary accents, rim light |
| Ink | `#1A1F3A` | headings, primary text on light backgrounds |
| Muted | `#8A8FA3` | secondary text, hints |
| Destructive | `#E84B6A` | errors, dangerous actions |
| Success | `#6DC28A` | API-live badge, confirmations |

Contrast ratios: Lumina Gold on Navy passes AA (7.1:1). Ink on Paper passes AAA. Muted on Paper passes AA large text.

## Typography

| Slot | Family | Fallback |
| --- | --- | --- |
| Display / headings | Bricolage Grotesque | Inter, system-ui |
| UI / body | Inter | Segoe UI, system-ui |
| Monospace (JSON, code) | JetBrains Mono | Consolas, Menlo, monospace |

## Voice & tone

- **Direct, a little workshop-built.** "Enumerating combinations…" beats "Loading…". Empty states describe what's missing and how to fix it.
- **Help the user without apologising.** Error messages include the next step: "Start the API with `just api`, then retry."
- **English in code, French anywhere the user can see it** — except for in-game terminology (picto, lumina, Gustave) which stays as-is.

## Generating icon assets

Once the Recraft export is in hand (a 1024×1024 PNG called, say, `logo-source.png`):

```bash
# From the repo root, drop the Recraft export somewhere temporary
pnpm --dir app tauri icon /path/to/logo-source.png
# This regenerates app/src-tauri/icons/*.png, icon.ico and icon.icns.
```

Then refresh the SVG in `app/public/logo.svg` by exporting an optimised version (SVGO) from the Recraft vector, or by tracing the PNG with an online tool. Keep the SVG under 4 KB — the header renders it inline.
