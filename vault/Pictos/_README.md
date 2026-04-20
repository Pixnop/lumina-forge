---
type: folder-readme
folder: Pictos
---

# Pictos

One note per picto. Only **3 pictos can be equipped per character at once**, so the optimizer has to enumerate combinations — keep this folder's data clean and exhaustive.

## Filename

`<picto-slug>.md` — e.g. `augmented-critical.md`.

## Frontmatter

```yaml
---
type: picto
name: Augmented Critical
category: Offensive            # Offensive | Defensive | Utility
tier: S                        # optional — S | A | B | C | F (meta placement)
effect: "+30% critical damage"
effect_structured:             # machine-readable — used by the optimizer
  crit_damage_bonus: 0.30
stats_granted:
  might: 8
  luck: 4
lumina_after_mastery: augmented-critical-lumina  # link to Luminas/ entry (optional)
source_locations:              # how to obtain it
  - chest: Lumiere, East Gate
  - enemy: Grandfather
sources:
  - https://expedition33.wiki.fextralife.com/Augmented+Critical
  - https://maxroll.gg/clair-obscur-expedition-33/picto/augmented-critical
---
```

## Body

- **Effect** — full text of the in-game description.
- **Interactions** — interplay with skills / statuses / other pictos.
- **Typical builds** — link to [[Builds/_README|Builds]] entries that use it.
- **Notes** — edge cases, caps, hidden math.
