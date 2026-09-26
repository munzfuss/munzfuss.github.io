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

# libyaml-backed loader when available. It composes the SAME node tree
# (MappingNode/SequenceNode/ScalarNode with start_mark) that the pure-Python
# SafeLoader does, so the dup-key walk below is unchanged — but ~4× faster,
# and this scan over every data/ file is the dominant cost of a full
# `build.py --validate-only`.
_FastLoader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


def find_duplicate_keys(yaml_path: Path) -> list[tuple[str, str | int, int, int]]:
    """Return a list of (path, key, first_line, dup_line) for every
    duplicate key found anywhere in the YAML document tree.

    `path` is a dotted accessor like `9_25_thaler.events.first_mint`.
    Empty list = clean.
    """
    with open(yaml_path) as fp:
        loader = _FastLoader(fp)
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


def check_data_directory(root: Path = Path("data"),
                         files: list[Path] | None = None) -> int:
    """Report duplicate keys across a set of YAML files.

    Default: walk every *.yml under `root`. If `files` is given, scan only
    those (a pre-commit hook passes the STAGED data yamls — a new duplicate
    key can only appear in a file the commit changed, and CI keeps the full
    `root` scan as the backstop). A path in `files` that does not exist or is
    not under `root` is skipped.

    Returns the number of issues found. Prints a clear error for each issue.
    Use the return value as a process exit code: zero = clean, non-zero =
    at least one duplicate detected.
    """
    if files is None:
        scan = sorted(root.rglob("*.yml"))
    else:
        scan = sorted(f for f in files if f.suffix == ".yml" and f.is_file())
    total = 0
    for f in scan:
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
