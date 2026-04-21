---
type: formula
name: Painted Power
variables:
  - painted_power_active
  - painted_power_turns
  - painted_power_damage_multiplier
applies_to: "Character-specific ultimate that temporarily removes the 9999 cap"
effect_structured:
  damage_multiplier: 2.5
  duration_turns: 1
  cooldown_turns_baseline: null     # no cooldown — gated by charge
  cap_bypass: true
sources:
  - https://expedition33.wiki.fextralife.com/Painted+Power
---

# Painted Power

Painted Power is the late-game "unlimited damage" mode that bypasses the 9999 per-hit cap. It's gated by a dedicated charge bar that fills on specific actions (mastered pictos, ability usage, successful dodges).

## Effects

- Per-hit damage cap is **removed** during the activation window (normally 1 turn, sometimes 2 with specific pictos).
- Final damage is multiplied by `×2.5` on top of the normal formula.
- Certain skills have a dedicated Painted Power animation / variant that does more (e.g. *Painted Gradient*).

## Interaction with core formula

$$
\text{hit}_{\text{PP}} = W_{\text{base}} \times \ldots \times \text{(normal factors)} \times 2.5
$$

with no `min(9999, \cdot)` clamp.

## Scorer behaviour

The optimizer does **not** assume Painted Power in the baseline scoring — it's a burst phase, and the build ranking should reflect sustained DPS. If a build includes Painted-Power-enabling pictos (e.g. *Painted Charge*), the scorer adds a bonus proportional to `damage_multiplier × pp_charge_frequency`, approximating an every-Nth-turn burst.

## Not covered here

- Exact charge-fill mechanics per character (data still sparse — needs another scraping pass on Fextralife detail pages).
- Per-character unique PP variants (Gustave Painted Overcharge vs. Verso Painted Dual Strike).

These are tracked as follow-up work; the scorer handles them with a single flat multiplier for now.
