"""Turn a Build into a 3-step rotation hint.

Placeholder for Phase 3: we don't run a combat simulator, we just order
the character's available skills by role so the user has a starting point.
The rotation typically goes **buff → main offensive → finisher**.
"""

from __future__ import annotations

from optimizer.models import Build, SkillItem

_BUFF_KEYWORDS = ("buff", "empower", "stance", "prepare", "focus", "mark")
_FINISHER_KEYWORDS = ("finish", "execute", "ultimate", "burst", "blast", "overload", "overcharge")


def suggest(build: Build) -> list[str]:
    """Return up to three lines describing a reasonable opening rotation."""
    char_slug = build.character.slug.lower()
    skills = [s for s in build.skills_used if (s.character or "").lower() == char_slug]
    if not skills:
        skills = list(build.skills_used)
    if not skills:
        return ["Use your character's basic attack — no skills known yet."]

    by_role = _group_by_role(skills)

    hints: list[str] = []
    if by_role["buff"]:
        hints.append(f"Turn 1 — open with **{by_role['buff'][0].name}** to set up.")
    if by_role["offensive"]:
        hints.append(f"Turn 2 — main damage: **{by_role['offensive'][0].name}**.")
    if by_role["finisher"]:
        hints.append(f"Turn 3 — close with **{by_role['finisher'][0].name}**.")

    # fill any gaps with the remaining cheapest skills
    while len(hints) < 3 and skills:
        next_skill = skills.pop(0)
        if any(next_skill.name in h for h in hints):
            continue
        hints.append(f"Follow-up: **{next_skill.name}**.")
    return hints


def _group_by_role(skills: list[SkillItem]) -> dict[str, list[SkillItem]]:
    buffs: list[SkillItem] = []
    offensives: list[SkillItem] = []
    finishers: list[SkillItem] = []
    others: list[SkillItem] = []
    for skill in sorted(skills, key=lambda s: s.ap_cost or 0):
        name_low = skill.name.lower()
        effect_low = (skill.body or "").lower()
        haystack = f"{name_low} {effect_low}"
        if any(kw in haystack for kw in _FINISHER_KEYWORDS):
            finishers.append(skill)
        elif skill.category == "Buff" or any(kw in haystack for kw in _BUFF_KEYWORDS):
            buffs.append(skill)
        elif skill.category == "Offensive" or "damage" in haystack:
            offensives.append(skill)
        else:
            others.append(skill)
    # Finishers often also hit hard — they belong to both "offensive" and "finisher";
    # keep them in finisher bucket for the rotation hint.
    return {
        "buff": buffs,
        "offensive": offensives or others,
        "finisher": finishers,
    }
