---
type: build
name: Lune — Elemental burst
character: Lune
archetype: Elemental
role: Offensive
dps_tier: S
weapon: Weapons/angerim
pictos:
  - Pictos/critical-burn
  - Pictos/alternating-critical
  - Pictos/gradient-parry
luminas:
  - Luminas/augmented-attack
  - Luminas/critical-burn
attributes:
  might: 25
  agility: 30
  defense: 10
  luck: 25
  vitality: 10
required_skills:
  - Skills/from-fire
  - Skills/strike-storm
dependencies:
  - Fire and Storm skills unlocked
tags: [meta, elemental, sustained]
sources:
  - https://maxroll.gg/clair-obscur-expedition-33/builds/lune-caster
---

# Lune — Elemental burst

## Win condition

Rotate Fire ↔ Storm to keep Stain active every turn, while Critical Burn adds Burn stacks and Gradient Parry maintains Gradient 2-3 for the multiplier chain.

## Rotation

| Turn | Action |
| --- | --- |
| 1 | *From Fire* — applies Fire Stain |
| 2 | *Strike Storm* — consumes Fire Stain (×1.50), applies Storm Stain |
| 3 | *From Fire* again — consumes Storm Stain, applies Fire Stain |
| … | cycle |

Parry the enemy's turn between casts to keep Gradient topped up.

## Scaling

- **Agility 30** for crit rate + skill speed. Lune is naturally nimble.
- **Luck 25** for crit+Burn consistency. Critical Burn gates everything else.

## Synergies

- [[Synergies/elemental-stain-chain]] — the core of the rotation
- [[Synergies/burn-stain-chain]] — layered bonus once Burn caps
- [[Synergies/gradient-economy]] — Gradient Parry keeps the bar full

## Variants

- If you can't parry reliably, swap Gradient Parry for Augmented Critical picto
- On AoE fights, Strike Storm is already multi-target — just keep cycling

## Dependencies

- **Angerim** (fire weapon) is ideal; if unavailable, any elemental-scaling Lune weapon works. The build is locked to Lune by skillset.
