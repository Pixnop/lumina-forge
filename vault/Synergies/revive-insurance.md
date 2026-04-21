---
type: synergy
name: Revive insurance
tier: B
components:
  pictos:
    - Pictos/aegis-revival
    - Pictos/sos-healing-tint
  luminas:
    - Luminas/aegis-revival
effect_summary: "Safety-net build for the blind first attempt at a new boss: Aegis Revival brings a fallen ally back with shields, SOS Healing Tint auto-heals the team at low HP. Not a DPS synergy — a consistency synergy."
score_bonus: 0.10
tags: [defensive, learning-fight, utility]
sources:
  - https://expedition33.wiki.fextralife.com/Aegis+Revival
---

# Revive insurance

## How it works

- **Aegis Revival** — on KO, character revives with 40% HP and a 1-hit shield. Once per battle per character.
- **SOS Healing Tint** — when any ally drops below 30% HP, they auto-use a Healing Tint. Costs one inventory tint.
- Paired, the team can survive most unexpected 1-shot combos and learn the fight over multiple attempts.

## Why B-tier

This is a **utility synergy**, not a damage one. The optimizer's `utility_weight` mode picks it up when `--mode utility` or `--weight-utility 0.3+` is set. In pure DPS mode it's a small score contribution.

## Best for

- **First attempt at a new boss** where you don't yet know the attack patterns
- **Solo content** where there's no party-wide revive
- Any character, but especially **fragile hybrid builds** (Lune, Sciel when built for crit)
