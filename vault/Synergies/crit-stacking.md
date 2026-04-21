---
type: synergy
name: Crit stacking
tier: S
components:
  pictos:
    - Pictos/augmented-attack
    - Pictos/alternating-critical
    - Pictos/critical-burn
effect_summary: "Three crit pictos push Augmented Critical (+crit dmg) × Alternating Critical (guaranteed crit every 2nd hit) × Critical Burn (crit procs Burn) into a loop where every other hit is a guaranteed ×1.80+ crit applying Burn stacks."
score_bonus: 0.25
tags: [crit, core, works-on-everyone]
sources:
  - https://maxroll.gg/clair-obscur-expedition-33/builds/crit-core
---

# Crit stacking

## How the combo works

- **Alternating Critical** makes every 2nd hit an auto-crit, so multi-hit skills see 50% of their hits crit regardless of rate.
- **Augmented Critical** adds +0.30 crit damage, moving the crit multiplier from ×1.50 to ×1.80.
- **Critical Burn** applies a Burn stack on each crit, so the 50% auto-crits double as Burn spreaders.

## Expected multiplier

For a 4-hit weapon: `(2 guaranteed crits × 1.80) + (2 normal hits × crit_rate × (1.80 - 1) + base)`. Even at 0% underlying crit rate, the expected multiplier is ~×1.40 just from Alternating Critical, and closer to ×1.55 once rate is 30%+.

## Best characters

- **Sciel** — built-in crit rate from Agility, naturally aligns with this combo
- **Gustave** — works but competes with Overcharge-stacking pictos for slots
- **Verso** — multi-hit dualist weapons love Alternating Critical

## Builds

- [[Builds/sciel-crit-sniper]] — canonical home for this synergy
- [[Builds/verso-dualist]] — uses a subset (Augmented + Alternating without Critical Burn)
