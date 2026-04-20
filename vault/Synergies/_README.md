---
type: folder-readme
folder: Synergies
---

# Synergies

Validated multi-component combos — the atomic units the optimizer reasons about when it scores a proposed build.

A synergy is a **weighted hint**: "if this subset of components shows up in the inventory, boost the score by X because the combo is known to work". Synergies are smaller than full [[Builds/_README|Builds]] — a build bundles many synergies plus a rotation.

## Filename

`<concept-slug>.md` — e.g. `burn-stain-chain.md`, `crit-stacking.md`.

## Frontmatter

```yaml
---
type: synergy
name: Burn + Stain chain
tier: S                          # S | A | B | C (strength of the combo)
components:                      # every key is optional — list what matters
  skills:
    - Skills/ignite
    - Skills/stain-shot
  pictos:
    - Pictos/pyromaniac
  luminas:
    - Luminas/burn-amplifier
  weapons: []
  statuses_applied:
    - Burn
    - Stain
effect_summary: "Ignite applies Burn (1.5x dmg vs burning), Stain Shot consumes Burn and reapplies Stain with +30% damage."
score_bonus: 0.20                # flat multiplier the optimizer applies if all components are present
requires:                        # hard preconditions
  - character_has_skill: Skills/ignite
tags: [dot, combo, status]
sources:
  - https://maxroll.gg/clair-obscur-expedition-33/synergies/burn-stain
---
```

## Body

- **How the combo works** — 2-3 lines of plain English.
- **Why it's strong** — the specific interaction (status stacking, damage multiplier chain, AP economy).
- **Counterplay / limits** — when the synergy breaks (immune enemies, AoE fights, etc.).
- **Builds that use it** — backlinks to [[Builds/_README|Builds]] entries.
