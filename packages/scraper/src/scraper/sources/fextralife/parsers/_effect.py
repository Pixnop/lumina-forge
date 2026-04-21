"""Extract structured numeric data from Fextralife effect text.

The index pages give us one plain-english sentence per picto/lumina
("50% increased Critical Rate on Burning enemies"). The optimizer wants
numbers it can multiply. This module bridges the gap with a handful
of forgiving regex patterns — whatever we recognise lands in
``effect_structured``, whatever we don't is left to the keyword
heuristic in the scorer.
"""

from __future__ import annotations

import re
from typing import Any

# "25% increased Critical Damage", "50% increased Base Attack damage",
# "50% increased Burn damage", "25% increased Critical Chance", "20% healing"…
# We capture the percentage, the ~3 filler words before it, and a tail
# keyword that tells us what bucket the bonus belongs to.
_CONTEXT_RE = re.compile(
    r"(?P<pct>\d+(?:\.\d+)?)\s*%\s*"
    r"(?:increased\s+)?"
    r"(?P<kind>(?:[\w']+\s+){0,4}?)"
    r"(?P<tail>damage|chance|rate|healing|recovery|resistance)",
    re.I,
)

_UTILITY_KEYWORDS: dict[str, tuple[str, bool]] = {
    "revive": ("has_revive", True),
    "resurrect": ("has_revive", True),
    "second chance": ("has_revive", True),
    "heal": ("has_heal", True),
    "healing": ("has_heal", True),
    "regen": ("has_heal", True),
    "shield": ("has_defense_buff", True),
    "barrier": ("has_defense_buff", True),
    "damage reduction": ("has_defense_buff", True),
    "invulner": ("has_defense_buff", True),
}


def parse_effect_structured(text: str) -> dict[str, Any]:
    """Return numeric + flag fields extracted from a free-form effect sentence.

    >>> parse_effect_structured("50% increased Base Attack damage")
    {'damage_bonus': 0.5}
    >>> parse_effect_structured("25% increased Critical Damage")
    {'crit_damage_bonus': 0.25}
    >>> parse_effect_structured("25% increased Critical Chance on Burning enemies")
    {'crit_rate_bonus': 0.25}
    >>> parse_effect_structured("50% increased Burn damage")
    {'damage_bonus': 0.5}
    >>> parse_effect_structured("Every third hit deals double damage.")
    {'damage_bonus': 0.33}
    >>> parse_effect_structured("Revive with 50% HP once per battle")
    {'has_revive': True}
    """
    result: dict[str, Any] = {}
    if not text:
        return result

    # Special shorthand patterns first — they don't carry a % literal.
    if re.search(r"every\s+third\s+hit.+double\s+damage", text, re.I):
        result["damage_bonus"] = 0.33
    elif re.search(r"double\s+damage", text, re.I):
        result["damage_bonus"] = 0.50

    for match in _CONTEXT_RE.finditer(text):
        pct = float(match.group("pct")) / 100.0
        kind = match.group("kind").strip().lower()
        tail = match.group("tail").lower()

        key = _classify(kind, tail)
        if key is None:
            continue
        # First hit wins — keep the most specific bucket we see per key.
        result.setdefault(key, pct)

    low = text.lower()
    for keyword, (key, flag) in _UTILITY_KEYWORDS.items():
        if keyword in low:
            result[key] = flag

    # Estimate how often the damage clause actually fires. Multiplied onto
    # damage_bonus by the scorer so Alternating Critical (≈50% uptime) no
    # longer ranks the same as a flat +100% damage picto.
    uptime = _estimate_trigger_uptime(text)
    if uptime < 1.0 and "damage_bonus" in result:
        result["trigger_uptime"] = uptime

    return result


# Common trigger phrasings → how often they're up in a typical rotation.
# Numbers are pragmatic averages, not exact: the goal is to break ties
# between "always on" and "conditional" pictos, not to be a simulator.
_UPTIME_PATTERNS: list[tuple[re.Pattern[str], float]] = [
    (re.compile(r"every\s+third\s+(?:hit|attack)", re.I), 0.33),
    (re.compile(r"every\s+(?:second|2nd|other)\s+(?:hit|attack)", re.I), 0.50),
    (re.compile(r"on\s+(?:a\s+)?critical\s+(?:hit|strike)", re.I), 0.30),
    (re.compile(r"after\s+(?:a\s+)?critical", re.I), 0.30),
    (re.compile(r"on\s+burning\s+enemies", re.I), 0.70),
    (re.compile(r"on\s+stained\s+enemies", re.I), 0.45),
    (re.compile(r"on\s+marked\s+enemies", re.I), 0.55),
    (re.compile(r"on\s+powerful\s+(?:skills?|attacks?)", re.I), 0.40),
    (
        re.compile(
            r"(?:gradient\s+3"
            r"|when\s+gradient\s+(?:is\s+)?(?:full|max)"
            r"|consume\s+\d+\s+gradient)",
            re.I,
        ),
        0.33,
    ),
    (re.compile(r"at\s+low\s+hp|when\s+hp\s+below", re.I), 0.25),
    (re.compile(r"first\s+(?:hit|attack|turn)", re.I), 0.20),
    (re.compile(r"when\s+shield(?:ed)?", re.I), 0.35),
    (re.compile(r"once\s+per\s+(?:battle|turn)", re.I), 0.15),
]


def _estimate_trigger_uptime(text: str) -> float:
    """Return uptime in [0, 1]. Defaults to 1.0 (always on) when no
    conditional phrasing is recognised."""
    low = text.lower()
    for pattern, uptime in _UPTIME_PATTERNS:
        if pattern.search(low):
            return uptime
    return 1.0


def _classify(kind: str, tail: str) -> str | None:
    """Map ``<kind> <tail>`` → effect_structured key, or None to skip."""
    has_crit = "critical" in kind or "crit" in kind
    if tail == "damage":
        if has_crit:
            return "crit_damage_bonus"
        if "break" in kind:
            return "break_damage_bonus"
        # base attack, burn, stain, elemental, etc. — treat all as flat damage
        return "damage_bonus"
    if tail in ("chance", "rate"):
        if has_crit:
            return "crit_rate_bonus"
        return None
    if tail in ("healing", "recovery"):
        return "healing_bonus"
    if tail == "resistance":
        return "damage_resistance_bonus"
    return None
