---
type: index
tags: [index, meta]
---

# Lumina Forge — Knowledge Base

Everything the optimizer needs to rank builds for **Clair Obscur: Expedition 33**.
Notes live in thematic folders; every note uses YAML frontmatter so the Python side can query structured attributes.

## Map of the vault

- [[Characters/_README|Characters]] — one note per playable character (stats, archetypes, signature skills)
- [[Pictos/_README|Pictos]] — one note per picto (effect, source, offensive/defensive/utility)
- [[Weapons/_README|Weapons]] — one note per weapon (base damage, scaling stat, boosted skills, passives)
- [[Luminas/_README|Luminas]] — one note per lumina (effect, PP cost, restrictions)
- [[Skills/_README|Skills]] — one note per skill (AP cost, damage formula, status effects, targeting)
- [[Formulas/_README|Formulas]] — damage math, status stacking, 9999 cap, Painted Power
- [[Builds/_README|Builds]] — curated / scraped builds (archetype, synergies, dependencies)
- [[Synergies/_README|Synergies]] — validated combos across pictos / weapons / luminas / skills

## Conventions

- Filenames: `kebab-case` for multi-word, e.g. `glass-cannon.md`, `verso-dualist.md`.
- Every note starts with a YAML frontmatter block. Each folder's `_README.md` documents the expected keys.
- Cross-reference with Obsidian wikilinks `[[...]]`. Prefer `[[Target|alias]]` for readability.
- Tag notes with broad categories (`#offensive`, `#defensive`, `#utility`, `#meta`). Tags are search helpers, not the source of truth — frontmatter is.
- When multiple scraped sources disagree, keep both values and record them in `sources:` (list of URLs) with a note in the body.

## Status

Phase 1 scaffold — folders and conventions are in place. Content will be populated by the scraper in Phase 2.
