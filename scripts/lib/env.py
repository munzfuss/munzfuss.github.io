"""Tiny dotenv-style loader for `local.env` (gitignored).

We avoid the `python-dotenv` dependency: a 20-line parser handles our needs.
"""
from __future__ import annotations
import os
import pathlib

ENV_FILE = pathlib.Path(__file__).resolve().parents[2] / "local.env"


def load_local_env(path: pathlib.Path = ENV_FILE) -> dict[str, str]:
    """Read KEY=VALUE pairs from `path` and merge into os.environ.

    Returns the dict that was loaded. Empty values are skipped (so a stub
    `NUMISTA_API_KEY=` line doesn't clobber a real env var).
    Existing os.environ entries take precedence.
    """
    loaded: dict[str, str] = {}
    if not path.exists():
        return loaded
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if not v:
            continue
        loaded[k] = v
        os.environ.setdefault(k, v)
    return loaded


def require(name: str) -> str:
    """Get an env var or raise if missing/empty."""
    val = os.environ.get(name) or ""
    if not val:
        raise RuntimeError(
            f"Missing required env var {name!r}. "
            f"Set it in local.env (see local.env in project root)."
        )
    return val
