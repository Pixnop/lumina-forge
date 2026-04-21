---
type: formula
name: Core damage
variables:
  - weapon_damage
  - might
  - agility
  - defense
  - luck
  - crit_rate
  - crit_damage_bonus
  - picto_damage_bonus
  - lumina_damage_bonus
  - gradient_level
  - powerful_active
  - status_multiplier
  - damage_reduction
applies_to: "All offensive skills except Painted Power finishers (see painted-power.md)"
effect_structured:
  rotation_turns: 3
  might_per_point: 0.02
  agility_crit_rate: 0.004
  luck_crit_rate: 0.004
  base_crit_damage: 1.50
  damage_cap_per_hit: 9999
sources:
  - https://maxroll.gg/clair-obscur-expedition-33/mechanics/damage
  - https://expedition33.wiki.fextralife.com/Combat+Mechanics
---

# Core damage equation

$$
\text{hit} = \lfloor
  W_{\text{base}}
  \times (1 + 0.02 \cdot \text{Might})
  \times (1 + \sum_{p \in \text{pictos}} p_{\text{dmg}\%})
  \times (1 + \sum_{l \in \text{luminas}} l_{\text{dmg}\%})
  \times C_{\text{crit}}
  \times G_{\text{gradient}}
  \times S_{\text{status}}
  \times (1 - D_{\text{target}})
\rfloor
$$

Where:

| Factor | Expression | Notes |
| --- | --- | --- |
| $W_{\text{base}}$ | weapon.base_damage × skill_multiplier | skill_multiplier is in the skill's frontmatter; defaults to 1.0 for basic hits |
| Might bonus | $1 + 0.02 \cdot \text{Might}$ | +2% flat damage per Might point, uncapped |
| Picto multiplier | $\prod_{p} (1 + p_{\text{dmg}\%})$ | additive within one picto, multiplicative across the three slots |
| Lumina multiplier | $1 + \sum l_{\text{dmg}\%}$ | additive — luminas don't compound with each other |
| $C_{\text{crit}}$ | $1 + \text{crit\_rate} \cdot (\text{crit\_mult} - 1)$ | see [[critical-hits]] |
| $G_{\text{gradient}}$ | see [[gradient-bonus]] | per-character, multiplicative on final line |
| $S_{\text{status}}$ | see [[status-effects]] | Burn / Stain / Mark / Powerful multiplicatively chain |
| $D_{\text{target}}$ | target's damage reduction (0–0.85 cap) | subtracted at the very end |

## Effect structured — parser hints

```yaml
effect_structured:
  rotation_turns: 3           # how many turns an average rotation takes
  might_per_point: 0.02       # +2% per Might
  agility_crit_rate: 0.004    # +0.4% crit rate per Agility
  luck_crit_rate: 0.004       # +0.4% crit rate per Luck
  base_crit_damage: 1.50      # ×1.5 on crit before multipliers
  damage_cap_per_hit: 9999    # see cap-9999.md — relevant only outside Painted Power
```

The optimizer's `VaultFormulaModel` reads these keys and drives every number off them so changing the formula is data-only.

## Test cases

Canonical inputs for the test suite:

| Input | Expected output |
| --- | --- |
| weapon 100, might 0, pictos/luminas neutral, agility 0, luck 0, gradient 1, no status | 300 (base × 3 turns) |
| weapon 100, might 50, rest neutral | 600 (×2.0 might mult) |
| weapon 100, might 0, 3 pictos each +20% dmg | 518 (1.2³ = 1.728) |
| weapon 100, might 0, agility 50, luck 50, rest neutral | 360 (crit mult 1.2 ≈ rate 0.4 × dmg-1) |

These match `DefaultDamageModel.estimate()` in `packages/optimizer/src/optimizer/formulas.py` — the model derives its constants from this note once `VaultFormulaModel` is wired (task 58).
