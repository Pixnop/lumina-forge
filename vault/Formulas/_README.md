---
type: folder-readme
folder: Formulas
---

# Formulas

Damage math, status stacking, caps. The optimizer **reads these notes at runtime** to score builds — treat them as code written in markdown.

## Filename convention

One concept per note:

- `damage-formula.md` — the core damage equation.
- `gradient-bonus.md` — how Gradient scaling works.
- `status-effects.md` — burn / stain / powerful / bleed / mark stacking rules.
- `cap-9999.md` — the 9999-per-hit cap and how Painted Power bypasses it.
- `painted-power.md` — the Painted Power mechanic end-to-end.
- `critical-hits.md` — crit rate / crit damage formula.

## Frontmatter

```yaml
---
type: formula
name: Core damage
variables:                      # canonical variables referenced in Skills/
  - base
  - might
  - weapon_damage
  - gradient_bonus
  - crit_multiplier
  - damage_reduction
applies_to: "All offensive skills except Painted Power finishers"
sources:
  - https://maxroll.gg/clair-obscur-expedition-33/mechanics/damage
---
```

## Body

- **Equation** — render the formula in a fenced block, ideally both as an inline LaTeX/maths representation and as pseudo-Python the optimizer can lift.
- **Derivation** — how the formula was reverse-engineered, which sources agree/disagree.
- **Edge cases** — interactions (e.g. status multipliers stack multiplicatively; crits apply before reductions).
- **Test cases** — concrete `input → expected output` examples the optimizer test suite can use as fixtures.
