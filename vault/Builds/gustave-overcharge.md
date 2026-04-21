---
type: build
name: Gustave — Overcharge DPS
character: Gustave
archetype: Overcharge
role: Offensive
dps_tier: S
weapon: Weapons/blodam
pictos:
  - Pictos/gradient-overcharge
  - Pictos/empowering-jumps
  - Pictos/rush-on-powerful
luminas:
  - Luminas/critical-burn
  - Luminas/augmented-attack
attributes:
  might: 40
  agility: 15
  defense: 10
  luck: 15
  vitality: 10
required_skills:
  - Skills/overcharge
  - Skills/lumiere-assault
  - Skills/marking-shot
dependencies:
  - Overcharge skill unlocked (level 15 story gate)
tags: [meta, burst, late-game]
sources:
  - https://maxroll.gg/clair-obscur-expedition-33/builds/gustave-overcharge
---

# Gustave — Overcharge DPS

## Win condition

Turn 2 nukes. Use Overcharge on turn 1 to bank Powerful + Gradient 3, then unload *Lumiere Assault* on turn 2 for a 3-hit burst that routinely caps at 9999 per hit.

## Rotation

| Turn | Skill | Rationale |
| --- | --- | --- |
| 1 | *Marking Shot* + *Overcharge* | Mark target (×1.30), bank Powerful + Gradient 3 |
| 2 | *Lumiere Assault* | ×1.50 Powerful × ×1.75 Gradient × ×1.30 Mark ≈ ×3.4 over base |
| 3 | *From Fire* or basic | Refill Gradient, reapply Mark if expired |
| loop | back to turn 1 if boss survives | |

## Scaling checkpoints

- **Might 40** is the sweet spot — beyond that, the 9999 cap eats the marginal gain.
- **Crit rate 15-20%** via Agility+Luck + Augmented Critical lumina is enough to trigger Critical Burn stacks regularly.

## Synergies

- [[Synergies/overcharge-burst]] — the archetypal combo this build is built around
- [[Synergies/crit-stacking]] — secondary; Critical Burn lumina covers the Burn angle

## Variants

- Swap *Powerful Attack* for *Greater Powerful* if you already run *Auto-Powerful* from another slot
- Swap *Blodam* for *Abysseram* on bosses with high Agility resistance (Blodam scales Agility, Abysseram scales Vitality)
