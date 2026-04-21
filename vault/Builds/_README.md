---
type: folder-readme
folder: Builds
---

# Builds

Curated and scraped builds. Each note is a **known recipe** — the optimizer uses them as score boosters (a proposed combo matching a known build gets a synergy bonus) and as a library you can browse in Obsidian.

## Filename

`<character-slug>-<archetype-slug>.md` — e.g. `verso-dualist.md`, `gustave-overcharge-dps.md`.

## Frontmatter

```yaml
---
type: build
name: Gustave — Overcharge DPS
character: Gustave
archetype: Overcharge
role: Offensive
dps_tier: S                     # S | A | B | C — tier of this build within the character's options
weapon: Weapons/overcharged-hammer
pictos:
  - Pictos/augmented-attack
  - Pictos/critical-burn
  - Pictos/second-chance
luminas:
  - Luminas/might-boost
  - Luminas/crit-rate-plus
attributes:                     # recommended stat allocation
  might: 60
  agility: 20
  defense: 10
  luck: 10
required_skills:
  - Skills/powerful-strike
  - Skills/overcharge
dependencies:                   # what you NEED unlocked for this to work
  - Skills/overcharge must be at level 3+
tags: [meta, pve, late-game]
sources:
  - https://maxroll.gg/clair-obscur-expedition-33/builds/gustave-overcharge
  - https://www.clairbuilds.com/builds/gustave-overcharge
---
```

## Body

- **Win condition** — what the build is trying to do in one paragraph.
- **Rotation** — turn-by-turn sequence of actions.
- **Scaling checkpoints** — which upgrades dramatically shift performance.
- **Why each picto / lumina / skill is in the list** — optimizer uses this as synergy evidence.
- **Variants** — swaps for specific fights or if you lack a component.
