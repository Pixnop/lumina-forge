---
type: formula
name: Gradient bonus
variables:
  - gradient_level
  - gradient_generation_per_action
applies_to: "Every offensive skill once a character has Gradient stacks"
effect_structured:
  gradient_max_level: 3
  gradient_multiplier_per_level: 0.25
  gradient_gain_per_turn_baseline: 1
  gradient_consume_reset: true
sources:
  - https://expedition33.wiki.fextralife.com/Gradient+Attack
---

# Gradient

Gradient is a per-character resource displayed as a tricolor bar. Each turn action generates Gradient (1 stack baseline, more with specific pictos / skills). At max level the bar can be spent on a **Gradient Attack** that roughly doubles the skill's damage and resets the bar.

## Multiplier

$$
G_{\text{gradient}} = 1 + 0.25 \cdot \text{gradient\_level}
$$

So:

| Gradient level | Multiplier |
| --- | --- |
| 0 | ×1.00 |
| 1 | ×1.25 |
| 2 | ×1.50 |
| 3 (max) | ×1.75 — or ×2.0 if spent as a Gradient Attack |

Gradient Attacks reset the bar to 0. Non-attack uses (buffs, defensive) don't consume it.

## Interactions

- **Pictos that grant Gradient on hit** (e.g. *Gradient Parry*, *Gradient Overcharge*) compound with base generation and are the bread and butter of Overcharge-style Gustave builds.
- **Gustave's Overcharge** is a unique skill that reads as *Powerful + Gradient 3 next turn*, stacking with this formula multiplicatively.
- **Maelle's stances** can generate Gradient on the stance-change turn.

## Optimizer behaviour

The optimizer evaluates a "steady-state" assumption: over a 3-turn rotation, Gradient hovers near level 1-2 for most builds and level 3 for Overcharge-stacking builds. The scorer reads `gradient_generation_per_action` from the build's picto effect_structured fields and averages.
