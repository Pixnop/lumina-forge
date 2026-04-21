---
type: formula
name: Critical hits
variables:
  - crit_rate
  - crit_damage_bonus
  - agility
  - luck
  - base_crit_damage
applies_to: "Every offensive hit that rolls to crit"
effect_structured:
  base_crit_damage: 1.50
  agility_crit_rate_per_point: 0.004
  luck_crit_rate_per_point: 0.004
  crit_rate_cap: 1.00
  crit_damage_cap: 5.00
sources:
  - https://maxroll.gg/clair-obscur-expedition-33/stats
---

# Critical hit math

Crits are rolled per-hit independently. Each hit a skill deals can crit separately, so multi-hit skills benefit disproportionately from crit-rate scaling.

## Crit rate

$$
\text{crit\_rate} = \min\big(1.00,\ 0.004 \cdot \text{Agility} + 0.004 \cdot \text{Luck} + \sum \text{picto crit rate}\big)
$$

0.4% per Agility or Luck point means reaching 50% crit requires ~125 points split between the two stats, or heavy picto support.

## Crit damage

Base crit multiplier is **×1.50**. Pictos (Augmented Critical, Alternating Critical, etc.) and luminas add to `crit_damage_bonus`:

$$
\text{crit\_mult} = 1.50 + \sum \text{picto crit\_damage\_bonus}
$$

Capped at ×5.00 — reaching the cap requires Critical Burn + Augmented Critical + similar stacking.

## Expected crit multiplier (what the scorer uses)

$$
C_{\text{crit}} = 1 + \text{crit\_rate} \cdot (\text{crit\_mult} - 1)
$$

This is the expected-value formulation: it averages crit and non-crit hits weighted by rate.

## Test cases

| Agility | Luck | Picto crit rate | Picto crit dmg | crit_rate | crit_mult | C_crit |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 0 | 0 | 1.50 | 1.00 |
| 25 | 25 | 0 | 0 | 0.20 | 1.50 | 1.10 |
| 0 | 0 | 0 | +0.30 | 0 | 1.80 | 1.00 |
| 50 | 50 | 0 | +0.30 | 0.40 | 1.80 | 1.32 |
| 125 | 125 | +0.20 | +1.00 | 1.00 | 2.50 | 2.50 |

The optimizer reads `agility_crit_rate_per_point` and `luck_crit_rate_per_point` from this note; pictos contribute `crit_rate` and `crit_damage_bonus` via their own `effect_structured`.
