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

# "Break damage is increased by 50%", "base damage is reduced by 20%" —
# the % comes *after* "damage" so _CONTEXT_RE (which is anchored on %-first)
# doesn't see it. Captures the modifier kind, direction and magnitude.
_DAMAGE_DELTA_RE = re.compile(
    r"(?P<kind>base|break|burn|critical|void|fire|earth|lightning|ice)?\s*"
    r"damage\s+(?:is\s+|are\s+)?"
    r"(?P<direction>increased|multiplied|boosted|amplified|reduced|decreased)"
    r"\s+by\s+(?P<pct>\d+(?:\.\d+)?)\s*%",
    re.I,
)

# "increase damage by 20%", "increases damage by 5%" — same as above but
# verb-first ordering, used in conditional phrasings ("…if successful,
# increase damage by 20%").
_DAMAGE_DELTA_VERB_FIRST_RE = re.compile(
    r"(?P<direction>increase|boost|amplify|multiply|reduce|decrease)s?\s+"
    r"(?:(?P<kind>base|break|burn|critical|void|fire|earth|lightning|ice)\s+)?"
    r"damage\s+by\s+(?P<pct>\d+(?:\.\d+)?)\s*%",
    re.I,
)

# "gives a hidden 1.1x damage buff", "hidden 2x damage".
_HIDDEN_MULTIPLIER_RE = re.compile(
    r"hidden\s+(?P<mult>\d+(?:\.\d+)?)\s*[x×]\s*damage",
    re.I,
)

# "Damage can exceed 9,999" — Painted Power's cap-bypass flag.
_CAP_BYPASS_RE = re.compile(
    r"damage\s+can\s+exceed\s+9[,]?999",
    re.I,
)

# "Apply Powerful for 3 turns on battle start" → always-on damage buff
# for the first N turns. Powerful = +50 % damage in-game.
_BATTLE_START_BUFF_RE = re.compile(
    r"apply\s+(?P<buff>powerful|rush|shell|mark|burn|stain)\s+"
    r"for\s+(?P<turns>\d+)\s+turns?\s+on\s+battle\s+start",
    re.I,
)

# "Gain Powerful for 1 turn on Base Attack", "Apply Powerful on Breaking",
# "Gain Powerful if fighting alone" — conditional buff gains. Uptime
# depends on the trigger, captured separately by _estimate_trigger_uptime
# from the text around the match.
_BUFF_APPLY_RE = re.compile(
    r"(?:apply|gain)\s+(?P<buff>powerful|mark|burn|stain)"
    r"(?:\s+for\s+\d+\s+turns?)?"
    r"\s+(?:on|when|if|upon|after|per)\b",
    re.I,
)

# "20 % chance to gain Powerful on Free Aim shot" — same buffs but gated
# on a probability. Multiply the buff bonus by the stated chance.
_CHANCE_BUFF_RE = re.compile(
    r"(?P<pct>\d+(?:\.\d+)?)\s*%\s*chance\s+to\s+"
    r"(?:apply|gain|cause|trigger)\s+"
    r"(?P<buff>powerful|mark|burn|stain|rush|shell)",
    re.I,
)

# Chance-to-status shorthand — "20% chance to Burn on Free Aim shot".
# The verb "burn" doubles as the buff name.
_CHANCE_STATUS_VERB_RE = re.compile(
    r"(?P<pct>\d+(?:\.\d+)?)\s*%\s*chance\s+to\s+(?P<buff>burn|mark|stain)\b",
    re.I,
)

# "Base Attack has N extra hit(s)" — each extra hit is a fractional damage
# bonus over the baseline. Base Attack in E33 is typically 3 hits.
_EXTRA_HITS_RE = re.compile(
    r"base\s+attack\s+has\s+(?P<extra>\d+)\s+extra\s+hits?",
    re.I,
)
_BASE_ATTACK_HITS = 3

# Damage impact of each named buff while active. Only buffs that actually
# raise outgoing damage go here; Rush/Shell affect turn order / incoming
# damage respectively and contribute nothing to damage_bonus.
_BUFF_DAMAGE_BONUS: dict[str, float] = {
    "powerful": 0.50,
    "mark": 0.30,
    "burn": 0.50,
    "stain": 0.50,
}

# Rotation assumed by the scorer. Matches ``DefaultDamageModel.rotation_turns``.
_ROTATION_TURNS = 3

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

    # Cap-bypass flag (Painted Power).
    if _CAP_BYPASS_RE.search(text):
        result["damage_cap_bypass"] = True

    # Hidden multipliers like "1.1x damage" → damage_bonus = 0.1.
    if (match := _HIDDEN_MULTIPLIER_RE.search(text)) is not None:
        mult = float(match.group("mult"))
        if mult > 0:
            result.setdefault("damage_bonus", mult - 1.0)

    # Battle-start buffs. Powerful for N turns on a 3-turn rotation scales
    # its always-on damage bonus by N/3 (clamped).
    if (match := _BATTLE_START_BUFF_RE.search(text)) is not None:
        buff = match.group("buff").lower()
        turns = int(match.group("turns"))
        buff_bonus = _BUFF_DAMAGE_BONUS.get(buff, 0.0)
        if buff_bonus > 0:
            uptime_fraction = min(turns / _ROTATION_TURNS, 1.0)
            result.setdefault("damage_bonus", buff_bonus * uptime_fraction)

    # Chance-gated buff application. The chance replaces the default
    # trigger_uptime for this clause.
    if "damage_bonus" not in result:
        for chance_re in (_CHANCE_BUFF_RE, _CHANCE_STATUS_VERB_RE):
            match = chance_re.search(text)
            if match is None:
                continue
            buff = match.group("buff").lower()
            buff_bonus = _BUFF_DAMAGE_BONUS.get(buff, 0.0)
            if buff_bonus <= 0:
                break
            chance = float(match.group("pct")) / 100.0
            # Tuck the buff's damage bonus behind the chance. The scorer
            # multiplies damage_bonus × trigger_uptime downstream, so we
            # keep the damage_bonus whole and stash the chance as uptime.
            result.setdefault("damage_bonus", buff_bonus)
            result.setdefault("trigger_uptime", chance)
            break

    # Non-chance buff applications: "Gain Powerful on <condition>".
    # The conditional trigger_uptime is filled in by _estimate_trigger_uptime
    # further down, so we only set damage_bonus here.
    if "damage_bonus" not in result and (match := _BUFF_APPLY_RE.search(text)) is not None:
        buff = match.group("buff").lower()
        buff_bonus = _BUFF_DAMAGE_BONUS.get(buff, 0.0)
        if buff_bonus > 0:
            result["damage_bonus"] = buff_bonus

    # Extra hits on Base Attack — each extra hit adds ~1/3 of base damage.
    if (match := _EXTRA_HITS_RE.search(text)) is not None:
        extra = int(match.group("extra"))
        result.setdefault("damage_bonus", extra / _BASE_ATTACK_HITS)

    _apply_context_matches(text, result)

    # Verb-first and verb-middle "damage increased/reduced by N%" clauses
    # that _CONTEXT_RE can't catch because the % sits after "damage".
    for match in _DAMAGE_DELTA_RE.finditer(text):
        _absorb_damage_delta(match, result)
    for match in _DAMAGE_DELTA_VERB_FIRST_RE.finditer(text):
        _absorb_damage_delta(match, result)

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


def _apply_context_matches(text: str, result: dict[str, Any]) -> None:
    """Kept separate so the main function reads cleanly."""
    for match in _CONTEXT_RE.finditer(text):
        pct = float(match.group("pct")) / 100.0
        kind = match.group("kind").strip().lower()
        tail = match.group("tail").lower()

        key = _classify(kind, tail)
        if key is None:
            continue
        # First hit wins — keep the most specific bucket we see per key.
        result.setdefault(key, pct)


def _absorb_damage_delta(match: re.Match[str], result: dict[str, Any]) -> None:
    pct = float(match.group("pct")) / 100.0
    direction = match.group("direction").lower()
    # Reductions map to a negative damage_bonus so the scorer subtracts
    # the penalty side of trade-off pictos (e.g. break-specialist).
    if direction.startswith(("reduc", "decrease")):
        pct = -pct
    kind = (match.group("kind") or "").lower()

    if "break" in kind:
        key = "break_damage_bonus"
    elif "critical" in kind:
        key = "crit_damage_bonus"
    else:
        key = "damage_bonus"

    # For damage_bonus we *overwrite* a previous non-penalty match with a
    # penalty one (so "+50% break, -20% base" keeps the -20% on damage_bonus
    # rather than dropping it because an earlier match set the key).
    if key == "damage_bonus" and pct < 0:
        result[key] = pct
    else:
        result.setdefault(key, pct)


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
    (re.compile(r"after\s+(?:a\s+)?(?:free\s+aim|base\s+attack)", re.I), 0.30),
    (re.compile(r"(?:on|after)\s+(?:successful\s+|a\s+)?parry", re.I), 0.35),
    (re.compile(r"if\s+fighting\s+alone", re.I), 0.50),
    (re.compile(r"for\s+\d+\s+turn", re.I), 0.40),
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
