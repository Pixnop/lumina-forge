---
type: folder-readme
folder: Weapons
---

# Weapons

One note per weapon. Weapons are character-specific and define passives that can massively reshape a build (multi-hit, on-burn bonus, etc.).

## Filename

`<weapon-slug>.md` — e.g. `verso-s-rapier.md`.

## Frontmatter

```yaml
---
type: weapon
name: Verso's Rapier
character: Verso                 # owner
base_damage: 85
scaling_stat: Agility            # Might | Agility | Defense | Luck
boosted_skills:                  # skill slugs that get a boost from this weapon
  - Skills/riposte
passives:
  - name: Bleeding Edge
    effect: "Applies bleed on critical hit"
    effect_structured:
      on_crit_status: Bleed
      status_chance: 1.0
upgrade_tree:
  max_level: 20
  costs_per_level: "see in-game blacksmith"
source_locations:
  - quest: Prologue — Gustave's workshop
sources:
  - https://expedition33.wiki.fextralife.com/Verso%27s+Rapier
---
```

## Body

- **Passives** — full text.
- **Scaling curve** — what happens with upgrades (damage growth, extra procs at milestones).
- **Best pairings** — link to [[Pictos/_README|Pictos]] / [[Skills/_README|Skills]] that synergize.
- **Notes** — hidden multipliers, caps.
