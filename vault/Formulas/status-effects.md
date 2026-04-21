---
type: formula
name: Status effects — Burn, Stain, Mark, Powerful, Shield
variables:
  - burn_stacks
  - stain_stacks
  - mark_active
  - powerful_active
  - shield_stacks
applies_to: "Every hit on a target carrying at least one status"
effect_structured:
  burn_damage_per_stack: 0.10
  burn_max_stacks: 10
  stain_damage_bonus: 0.50
  stain_consumes_on_elemental_hit: true
  mark_damage_bonus: 0.30
  mark_duration_turns: 3
  powerful_damage_bonus: 0.50
  powerful_next_skill_only: true
  shield_damage_block_per_stack: 1.0
sources:
  - https://maxroll.gg/clair-obscur-expedition-33/statuses
  - https://expedition33.wiki.fextralife.com/Status+Effects
---

# Status effects

Five statuses matter for DPS math. They all stack **multiplicatively** with the core damage formula (status multiplier `S_status` in [[damage-formula]]).

## Burn — damage-over-time × mild multiplier

- Target takes `base_damage × 10%` per burn stack at the start of their turn.
- A hit on a burning target gets a `×(1 + 0.05 × stacks)` bonus, capped at 10 stacks (×1.50).
- Multiple burn applications add stacks, not duration.

## Stain — elemental trigger × big multiplier

- An elemental hit on a stained target does `×1.50` damage and **consumes the stain**.
- Stain is element-specific (Fire Stain, Ice Stain, etc.). Mismatched element = no trigger, stain stays.
- Some pictos (e.g. *Pyromaniac*) auto-apply stain on hit → supports Burn+Stain rotations.

## Mark — class-wide amplifier

- Marked target takes `×1.30` damage from every source for `mark_duration_turns` turns.
- Gustave's *Marking Shot* is the canonical applier.
- Marks do **not** stack; reapplying refreshes duration.

## Powerful — next-skill amplifier

- The character's very next offensive skill does `×1.50` damage.
- Consumed on use, or expires at end of turn.
- Comes from *Overcharge*, the *Powerful Attack* picto, and *Greater Powerful*.

## Shield — defensive, but affects outbound damage

- Each stack absorbs 1 base hit before HP drops.
- Some builds use *Barrier Breaker* or *Shattering Strike* to consume shields for bonus damage — in that case `shield_damage_block_per_stack` is effectively a target debuff, not a buff.

## Combined multiplier

$$
S_{\text{status}} =
  (1 + 0.05 \cdot \text{burn\_stacks})
  \times (1.5 \text{ if stain consumed else } 1)
  \times (1.3 \text{ if marked else } 1)
  \times (1.5 \text{ if powerful active else } 1)
$$

Order of operations: burn and mark are always-on checks; stain and powerful are **one-shot triggers** that the optimizer counts at most once per rotation.

## Test cases

| Status state | S_status |
| --- | --- |
| no status | 1.00 |
| mark only | 1.30 |
| burn × 3 | 1.15 |
| stain consumed + mark | 1.95 |
| burn × 5 + stain + mark + powerful | 1.25 × 1.5 × 1.3 × 1.5 ≈ 3.66 |
