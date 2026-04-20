---
type: folder-readme
folder: Skills
---

# Skills

One note per skill. Skills have an **AP cost**, a **damage formula**, optional **status application**, and are tied to a character.

## Filename

`<skill-slug>.md` — e.g. `powerful-strike.md`.

## Frontmatter

```yaml
---
type: skill
name: Powerful Strike
character: Gustave
ap_cost: 2                       # Action Points to cast
ap_generated: 0                  # some skills generate AP instead
category: Offensive              # Offensive | Defensive | Utility | Buff | Debuff
targeting: SingleEnemy           # SingleEnemy | AllEnemies | Self | Ally | AllAllies
element: Neutral                 # Neutral | Fire | Ice | Lightning | Dark | Light
damage:
  formula: base * might_multiplier * (1 + gradient_bonus)
  base: 120
  multiplier_stat: Might
  hits: 1
  scaling_notes: "Gains +30% damage while Gradient 3"
status_applied:
  - name: Stain
    chance: 0.25
    duration: 3
cooldown: 0
sources:
  - https://expedition33.wiki.fextralife.com/Powerful+Strike
---
```

## Body

- **Description** — in-game text.
- **Ideal conditions** — when the skill shines (status on target, specific stance, buff up).
- **Combo potential** — which pictos / weapons / luminas amplify it.
- **Notes** — hidden interactions, bug workarounds.

## Formula grammar

Formulas in `damage.formula` use plain variable names that the optimizer resolves from:

- Character stats (`might`, `agility`, …)
- Weapon stats (`base_damage`, `scaling_stat_value`)
- Situational buffs (`gradient_bonus`, `powerful_bonus`, `burn_multiplier`)

See [[Formulas/_README|Formulas]] for the canonical list of variables and their sources.
