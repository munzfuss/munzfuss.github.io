"""
YAML integrity checks that run BEFORE Pydantic schema validation.

Pydantic catches schema violations (missing required fields, wrong types,
unknown fields when `extra='forbid'`), but it operates on the parsed dict —
which has already lost the duplicate-key information. PyYAML resolves
duplicate mapping keys silently with last-wins semantics, so a botched
text-substitution edit that duplicates a key (e.g. two `metal:` lines
under the same record) survives validation and ships broken data.

This module walks the YAML AST directly and fails the build if any
mapping has two children with the same key, at any depth, in any of the
project's data files. Errors include file path, the offending key, and
both line numbers — so the user can fix the source by hand.
"""

from __future__ import annotations

from pathlib import Path
import sys

import yaml


def find_duplicate_keys(yaml_path: Path) -> list[tuple[str, str | int, int, int]]:
    """Return a list of (path, key, first_line, dup_line) for every
    duplicate key found anywhere in the YAML document tree.

    `path` is a dotted accessor like `9_25_thaler.events.first_mint`.
    Empty list = clean.
    """
    with open(yaml_path) as fp:
        loader = yaml.SafeLoader(fp)
        try:
            node = loader.get_single_node()
        finally:
            loader.dispose()

    if node is None:
        return []

    issues: list[tuple[str, str | int, int, int]] = []

    def walk(n, path: str = "") -> None:
        if isinstance(n, yaml.MappingNode):
            seen: dict = {}
            for k_node, v_node in n.value:
                k = loader.construct_object(k_node, deep=False)
                line = k_node.start_mark.line + 1
                if k in seen:
                    issues.append((path, k, seen[k], line))
                else:
                    seen[k] = line
                walk(v_node, f"{path}.{k}" if path else str(k))
        elif isinstance(n, yaml.SequenceNode):
            for i, item in enumerate(n.value):
                walk(item, f"{path}[{i}]")

    walk(node)
    return issues


def check_data_directory(root: Path = Path("data")) -> int:
    """Walk every *.yml under `root` and report duplicate keys.

    Returns the number of issues found across all files. Prints a clear
    error for each issue. Use the return value as a process exit code:
    zero = clean, non-zero = at least one duplicate detected.
    """
    total = 0
    for f in sorted(root.rglob("*.yml")):
        issues = find_duplicate_keys(f)
        for path, key, first_line, dup_line in issues:
            rel = f.relative_to(Path.cwd()) if f.is_absolute() else f
            print(
                f"❌ {rel}: duplicate key '{key}' "
                f"at path '{path}' — first declared L{first_line}, "
                f"redeclared L{dup_line}",
                file=sys.stderr,
            )
            total += 1
    return total
