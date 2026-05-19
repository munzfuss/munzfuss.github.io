"""Shared constants used by multiple Galster parser shapes.

These are deliberately kept tiny — most parsing logic stays inside
each shape's own module. Anything that grows to >10 LOC and is used
by ≥2 shapes belongs here.
"""
from __future__ import annotations

# Sentinel emitted by `parse_galster._normalise_text` to mark <HR>
# section boundaries in the flattened plain text. Used by spec-block /
# description / litteratur parsers to delimit semantic regions.
HR_SENTINEL = "§§HR§§"

# Spec-block regex patterns. Each tuple is (pattern, output_key).
# Value normalisation (comma→dot, float-cast) is per-module since
# field-name post-processing varies slightly across shapes.
SPEC_PATTERNS: list[tuple[str, str]] = [
    (r"Bruttov[æe]gt:\s*([\d.,]+)\s*g", "bruttovaegt_g"),
    (r"Finhed:\s*([\d.,]+|\d+\s*[KkLl]od|\d+\s*K(?:arat)?(?:\s*\d+\s*[Gg]r[äa]n)?)", "finhed"),
    (r"Finv[æe]gt:\s*([\d.,]+)\s*g", "finvaegt_g"),
    (r"Diameter:\s*([\d.,]+)\s*mm", "diameter_mm"),
]
