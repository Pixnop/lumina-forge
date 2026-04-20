---
type: folder-readme
folder: Characters
---

# Characters

One note per playable character — currently Gustave, Lune, Maelle, Sciel, Monoco, Verso.

## Filename

`<character-slug>.md` — e.g. `gustave.md`, `verso.md`.

## Frontmatter

```yaml
---
type: character
name: Gustave
role: Offensive            # Offensive | Defensive | Support | Hybrid
primary_stat: Might        # scaling stat that matters most
signature_skills:          # wikilinks without the [[ ]]
  - Skills/prosthetic-strike
archetypes:                # build families the character excels at
  - Overcharge
  - Paint-Stacker
base_stats:
  hp: 450
  vitality: 10
  might: 14
  agility: 9
  defense: 8
  luck: 6
sources:
  - https://expedition33.wiki.fextralife.com/Gustave
---
```

## Body

- **Overview** — 1-2 lines: role, what makes them unique.
- **Scaling** — which stats boost what.
- **Signature mechanic** — the thing only this character does (Gustave's Overcharge, Maelle's stances, etc.).
- **Typical builds** — link to [[Builds/_README|Builds]] entries.
- **Notes / quirks** — hidden interactions, buffs, bugs.
