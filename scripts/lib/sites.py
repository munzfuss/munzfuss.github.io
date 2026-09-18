"""Site profiles — one build tree, several published sites.

A **site profile** names which locations a build renders, where it mounts
them, and under which origin. The repository holds one set of data and
one set of templates; each profile is a different published view of it.

Why this exists. The project began as a survey of the German lands, but
the Danish-German dual sovereignty over Schleswig-Holstein made Denmark
unavoidable, and Denmark became the main line of work — while rendering
as one tab among thirteen, twelve of which are German. The Danish page
deserves its own host. It cannot get one by splitting the repository,
because `schleswig_holstein` carries dual jurisdiction and the Danish
entities (`royal_slesvig`, `royal_holstein`, `gottorp_duchy`) render on
both sides: any data split would duplicate either a location yaml or
half of `data/v2/final/`. So the data stays in one place and the SITE
becomes configuration.

munzfuss is itself a profile (`config/sites/munzfuss.yml`), not a
hard-coded default with exceptions bolted on.

Profile fields:

    id            profile name; must equal the config file's stem
    origin        absolute origin for canonical / hreflang / sitemap
    out_dir       build output tree, relative to the repo root
    locations     explicit allowlist of location ids            ┐ exactly
    all_except    every location EXCEPT these ids               ┘ one of
    languages     languages to render (the one place `da` is switched on);
                  required — a site's language set is explicit, never inherited
    root_lang     the language additionally copied to `<out>/index.html`
    landing       whether to render the landing grid at all
    mount         `tree` → /<loc>/<lang>/ ; `root` → /<lang>/
    static_dir    directory copied verbatim to the site root (search-engine
                  verification tokens, CNAME, .well-known) — per site, because
                  such a token proves ownership of ONE host
    brand         the site's own name, in the <title> and the footer. A proper
                  noun, so it is one string across all languages (§2 tier 2:
                  -Fuß / -fod standard names never translate)
    eyebrow       optional override for the kicker above the <h1>; when unset
                  the localised `hero.eyebrow` from data/i18n/ui.yml is used,
                  which on the German site is a generic descriptor and IS
                  translated

Fields are consumed progressively by `scripts/build.py` as the site
plumbing lands; the model validates all of them from the first commit so
a config can never carry a field the loader does not understand.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import ValidationError, model_validator

from lib.schema import _StrictBase

# Repo root: this file is <repo>/scripts/lib/sites.py.
_REPO_ROOT = Path(__file__).resolve().parents[2]
SITES_DIR = _REPO_ROOT / "config" / "sites"

DEFAULT_SITE = "munzfuss"


class SiteProfileError(ValueError):
    """A profile is missing, malformed, or names a location that does not exist.

    Raised rather than warned: a profile that silently resolves to the
    wrong location set publishes the wrong site, and an empty resolution
    publishes nothing at all while exiting 0.
    """


class SiteProfile(_StrictBase):
    """One published site's shape. See the module docstring for the fields."""

    id: str
    origin: str
    out_dir: str = "site"
    locations: list[str] | None = None
    all_except: list[str] | None = None
    languages: list[str]
    root_lang: str = "en"
    landing: bool = True
    mount: Literal["tree", "root"] = "tree"
    static_dir: str = "static"
    brand: str
    eyebrow: str | None = None

    @model_validator(mode="after")
    def _check_scope_and_langs(self) -> "SiteProfile":
        if (self.locations is None) == (self.all_except is None):
            raise SiteProfileError(
                f"site '{self.id}': set exactly one of `locations` "
                f"(allowlist) or `all_except` (denylist)"
            )
        if not self.languages:
            raise SiteProfileError(f"site '{self.id}': `languages` is empty")
        if self.root_lang not in self.languages:
            raise SiteProfileError(
                f"site '{self.id}': root_lang '{self.root_lang}' is not in "
                f"languages {self.languages}"
            )
        if self.origin.endswith("/"):
            raise SiteProfileError(
                f"site '{self.id}': origin must not end in '/' "
                f"(it is concatenated with base_url + path)"
            )
        return self

    @property
    def out_path(self) -> Path:
        return _REPO_ROOT / self.out_dir

    @property
    def static_path(self) -> Path:
        return _REPO_ROOT / self.static_dir

    def resolve_locations(self, available: list[str]) -> list[str]:
        """Return this profile's location ids, in `available` order.

        `available` is the set of location ids that actually exist on disk
        (the stems of `data/v2/locations/*.yml`). Every id named by the
        profile must appear in it — a typo'd or removed location is an
        error, never a quietly smaller site.
        """
        named = self.locations if self.locations is not None else self.all_except
        unknown = [lid for lid in (named or []) if lid not in available]
        if unknown:
            raise SiteProfileError(
                f"site '{self.id}': unknown location id(s) "
                f"{', '.join(sorted(unknown))} — available: "
                f"{', '.join(sorted(available))}"
            )
        if self.locations is not None:
            keep = set(self.locations)
        else:
            keep = set(available) - set(self.all_except or [])
        resolved = [lid for lid in available if lid in keep]
        if not resolved:
            raise SiteProfileError(
                f"site '{self.id}': resolves to zero locations"
            )
        return resolved


def load_site(site_id: str = DEFAULT_SITE) -> SiteProfile:
    """Load and validate `config/sites/<site_id>.yml`."""
    path = SITES_DIR / f"{site_id}.yml"
    if not path.is_file():
        existing = sorted(p.stem for p in SITES_DIR.glob("*.yml")) \
            if SITES_DIR.is_dir() else []
        raise SiteProfileError(
            f"no site profile '{site_id}' at {path.relative_to(_REPO_ROOT)}"
            + (f" — available: {', '.join(existing)}" if existing else "")
        )
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    if not isinstance(raw, dict):
        raise SiteProfileError(f"{path.relative_to(_REPO_ROOT)}: not a mapping")
    try:
        profile = SiteProfile(**raw)
    except ValidationError as exc:
        # Pydantic wraps whatever a validator raises, including our own
        # SiteProfileError — unwrap so callers see one exception type.
        raise SiteProfileError(
            f"{path.relative_to(_REPO_ROOT)}: {exc}"
        ) from exc
    if profile.id != site_id:
        raise SiteProfileError(
            f"{path.relative_to(_REPO_ROOT)}: `id: {profile.id}` does not "
            f"match the file name '{site_id}'"
        )
    return profile


# ---------------------------------------------------------------------------
# URL shapes
# ---------------------------------------------------------------------------

def lang_url(base_url: str, page_prefix: str, lang: str, root_lang: str,
             collapses_root: bool) -> str:
    """The URL of one language version of a page.

    `page_prefix` is the page's own segment (`/denmark`, or empty when the
    page IS the site root — the landing, or a root-mounted location).
    `collapses_root` says whether this page has a root copy: when it does,
    the site's default language is served at the prefix itself rather than
    under its own language directory, because that render is written twice
    (to `/` and to `/<root_lang>/`) and the two must consolidate onto one
    canonical URL.

    This is the single place a page URL is spelled. It used to be written
    inline in both templates, which is how `en` ended up hard-coded in six
    of them and how the location page came to advertise `/denmark/en/` on a
    site that has no `/denmark/`.
    """
    if collapses_root and lang == root_lang:
        return f"{base_url}{page_prefix}/"
    return f"{base_url}{page_prefix}/{lang}/"


def page_urls(base_url: str, page_prefix: str, languages: list[str],
              lang: str, root_lang: str, collapses_root: bool) -> dict:
    """Every URL the `<head>` of one rendered page needs.

    - `canonical`   — this language version's own canonical URL
    - `x_default`   — the default language's URL, for `hreflang="x-default"`
    - `alternates`  — `[(lang, url), …]` for the hreflang cluster, in the
                      order the languages are rendered

    x-default is simply the root language's URL, which is why it needs no
    rule of its own.
    """
    return {
        "canonical": lang_url(base_url, page_prefix, lang, root_lang,
                              collapses_root),
        "x_default": lang_url(base_url, page_prefix, root_lang, root_lang,
                              collapses_root),
        "alternates": [
            (l, lang_url(base_url, page_prefix, l, root_lang, collapses_root))
            for l in languages
        ],
    }
