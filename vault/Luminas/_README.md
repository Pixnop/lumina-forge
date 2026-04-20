---
type: folder-readme
folder: Luminas
---

# Luminas

One note per lumina. Luminas are drawn from a **shared pool** across characters and cost **Lumina Points (PP)** to equip, so the optimizer has to satisfy a budget constraint and track which builds compete for the same PP pool.

## Filename

`<lumina-slug>.md` — e.g. `second-chance.md`.

## Frontmatter

```yaml
---
type: lumina
name: Second Chance
pp_cost: 8
category: Defensive               # Offensive | Defensive | Utility
effect: "Revive with 50% HP once per battle"
effect_structured:
  on_death_revive_pct: 0.50
  uses_per_battle: 1
restrictions:                     # empty list if none
  - "Only one reviving lumina active per party"
source_picto: glass-cannon        # which picto mastery unlocks this lumina (optional)
sources:
  - https://expedition33.wiki.fextralife.com/Second+Chance
---
```

## Body

- **Effect** — full in-game text.
- **When it shines** — build archetypes or encounters where this lumina is worth the PP.
- **Conflicts** — luminas that share a bucket (e.g. only one revive allowed).
- **Notes** — caps, exceptions.
