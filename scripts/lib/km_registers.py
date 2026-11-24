"""Krause-Mishler volumes ("registers") for catalogue KM numbers.

Krause numbers each country / region in its own volume and restarts the
numbering in each, so a bare «KM 230» means nothing until the volume is
known: Denmark KM 230 is a 3 Speciedaler 1661, Norway KM 230 a 6 Mark
1732-1733. A seed records the volume as a dict key (`km: {nor: '230'}`)
when its source names it; a bare KM is read in the volume of the issuing
entity (this table). The merger uses the table to compare bare numbers, the
render uses it to label them («KM-NO#»), so both read a bare KM the same way.

Register codes are lower-case internally. «nor», never «no»: a register
written as a YAML mapping key «no:» round-trips to the boolean False.
"""
from __future__ import annotations

import re

ENTITY_TO_KM_REGISTER: dict[str, str] = {
    # Danish-realm tracks Krause's «Denmark» volume
    "danish_realm": "dk",
    # Krause has a separate Norway volume. Code is «nor», NOT «no» — a register
    # code written as a YAML mapping key («no: 260») round-trips to the BOOLEAN
    # False, silently corrupting a register-keyed km dict. Never use a YAML-bool
    # token (no/yes/true/false/on/off/n/y) as a register code.
    "danish_norway": "nor",
    # Kingdom of Norway after 1814 — the same Krause Norway volume.
    "norway": "nor",
    # Christian II after 1523 — Krause's Denmark / Norway volumes.
    "christian_ii_supporters": "dk",
    "christian_ii_reconquest": "nor",
    # Søren Norby's own Visby issues 1523-1525 — Krause's Denmark volume.
    "norby_gotland": "dk",
    # Erik VII on Gotland after his deposition (1439-1449) — Denmark volume.
    "erik_gotland": "dk",
    # Gotlandic coin struck at Visby («gullandsk mønt») — Denmark volume.
    "gotland": "dk",
    # SH territory — Krause «German States» numbers each Schleswig-Holstein
    # house in a section of its own (KRAUSE_SECTIONS below). The royal
    # duchies are the section «Schleswig-Holstein» («sh»); every other house
    # entity is read in its own section. norburg_plon_duchy holds two sections
    # (Plön and Norburg), so a bare number there has no section to be read in.
    "royal_holstein": "sh",
    "gottorp_duchy": "gott",
    "schauenburg_pinneberg": "schpin",
    "sonderburg_duchy": "sond",
    "glucksburg_duchy": "gluecksb",
    "rantzau_county": "rantz",
    "provisional_govt": "sh",
    "holstein_schauenburg_county": "sh",
    # Other German entities — each has its own Krause volume, keep
    # registers explicit so cross-entity bleed (rare) doesn't false-match
    "fuerstbisthum_luebeck": "de-fbl",
    "hanseatic_hamburg": "de-hh",
    "hanseatic_lubeck": "de-hl",
    "erzbisthum_bremen_verden": "de-bv",
    "hanseatic_bremen": "de-hb",
    "herzogtum_braunschweig_lueneburg": "de-bl",
    "herzogtum_sachsen_lauenburg": "de-sl",
    "grafschaft_oldenburg": "de-old",
    "hochstift_osnabrueck": "de-osnabr",
    "landgrafschaft_hessen_kassel": "de-hk",
    # No register — bare KM remains ambiguous within these synthetic buckets
    # "_unclassified": None,
    # "_deprecated_gesamtstaat": None,
}


# Internal code → the code the page shows after «KM-» and the `km_register`
# casing of `data/v2/locations/<loc>.yml`.
# «glu» is Krause's own «Glückstadt» section: NGC files it under Denmark
# («Denmark GLÜCKSTADT …»), NumisMaster as country GLÜCKSTADT, Numista as the
# issuer «Glückstadt, City of». Its numbers collide with Denmark main (KM 26 =
# 6 Speciedaler 1604 there, 1/16 Speciedaler 1640 here) and with the S-H
# section (Hede 120 = Glückstadt KM 73 = S-H KM 105), so it is neither «dk»
# nor «sh». No entity reads a bare number in it: only a source that names the
# section writes it.
_DISPLAY = {"dk": "DK", "nor": "NO", "sh": "SH", "glu": "GLÜ",
            "hgr": "HGR", "gott": "GOTT", "sond": "SOND", "ploen": "PLÖN",
            "norb": "NORB", "gluecksb": "GLÜCKSB", "rantz": "RANTZ",
            "schpin": "SCHPIN"}


# Krause's own sections for the Schleswig-Holstein houses, by the heading the
# sources print (NumisMaster country, NGC «German States <SECTION>» /
# «Denmark <SECTION>»). Each numbers from 1 on its own, and the numbers collide
# (KM 5: Plön Thaler 1625, Norburg Thaler 1676, Gottorp 1/16 Thaler 1594-1605,
# Sonderburg 2 Schilling 1618, Glückstadt Denning 1619, Rendsborg Skilling
# 1719-1720). Curator 2026-11-23: a register per section.
KRAUSE_SECTIONS: dict[str, str] = {
    "SCHLESWIG-HOLSTEIN": "sh",
    "GLÜCKSTADT": "glu",
    "GLUCKSTADT": "glu",
    "HOLSTEIN-GOTTORP-RENDSBORG": "hgr",
    "SCHLESWIG-HOLSTEIN-GOTTORP": "gott",
    "SCHLESWIG-HOLSTEIN-SONDERBURG": "sond",
    "SCHLESWIG-HOLSTEIN-PLOEN": "ploen",
    "SCHLESWIG-HOLSTEIN-NORBURG": "norb",
    "SCHLESWIG-HOLSTEIN-GLUCKSBURG": "gluecksb",
    "RANTZAU": "rantz",
    "SCHAUMBURG-PINNEBERG": "schpin",
}

# Matching group of a register. The merger compares every number of the
# group under one scope key («km/sh»), so a bare number whose section the
# source does not name (ucoin, Bruun, Hede, KMM) still meets the same number
# written in a named section; two NAMED sections that differ never match
# (merge_seeds_cross_source._km_section_conflict).
KM_MATCH_GROUP: dict[str, str] = {code: "sh" for code in set(KRAUSE_SECTIONS.values())}

# Entities in the group with no section of their own (several sections).
_ENTITY_GROUP_ONLY: dict[str, str] = {"norburg_plon_duchy": "sh"}


def match_group(register: str | None) -> str | None:
    """The scope a register is compared under: «gott» → «sh», «dk» → «dk»."""
    if not register:
        return None
    r = str(register).strip().lower()
    return KM_MATCH_GROUP.get(r, r)


def entity_match_scope(entity) -> str | None:
    """The scope a BARE KM of this entity is compared under."""
    ent = entity[0] if isinstance(entity, list) else entity
    reg = ENTITY_TO_KM_REGISTER.get(ent or "")
    if reg:
        return match_group(reg)
    return _ENTITY_GROUP_ONLY.get(ent or "")


def is_named_section(register: str | None) -> bool:
    """True for a register that is one of Krause's S-H sections."""
    return bool(register) and str(register).strip().lower() in KM_MATCH_GROUP


def display_register(code: str | None) -> str | None:
    """«nor» → «NO», «dk» → «DK», «de-hh» → «DE-HH»; None stays None."""
    if not code:
        return None
    c = str(code).strip().lower()
    if c in ("no", "false"):          # a «no:» key that survived as text
        c = "nor"
    return _DISPLAY.get(c, c.upper())


def entity_register(issuing_entity) -> str | None:
    """The internal register of a coin's issuing entity, or None.

    A list-form entity resolves only when every entity maps to the same
    volume; a joint coin of two volumes has no single default."""
    ents = issuing_entity if isinstance(issuing_entity, list) else [issuing_entity]
    regs = {ENTITY_TO_KM_REGISTER.get(e) for e in ents if e}
    regs.discard(None)
    return regs.pop() if len(regs) == 1 else None


_SPLIT = re.compile(r"\s*[,/]\s*")


def split_km(value) -> list[str]:
    """A scalar or list KM value → its individual numbers, in order."""
    out: list[str] = []
    for v in (value if isinstance(value, list) else [value]):
        if v in (None, "", []):
            continue
        for p in _SPLIT.split(str(v)):
            p = p.strip()
            if p and p not in out:
                out.append(p)
    return out
