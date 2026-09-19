"""The Danish page is moving to its own host, and the build grew site
profiles to do it without duplicating data. Three of the ways that can go
wrong are silent, which is why they are pinned here.

A profile that resolves to the wrong location set publishes the wrong site;
one that resolves to nothing publishes an empty site and exits 0. Neither
announces itself — the build prints its usual green lines either way. So
every scope error raises.

The URL half has its own history. `en` was hard-coded in six places across
two templates and the SEO writer, and the first root-mounted build
advertised `/denmark/en/` on a site that has no `/denmark/`. Both sites are
due to change their default language (danskmoent to Danish, munzfuss to
German), so the tests below exercise a NON-English `root_lang` — with `en`
everywhere the two bugs are invisible, since the wrong answer and the right
one coincide.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.sites import (  # noqa: E402
    SiteProfile, SiteProfileError, lang_url, load_site, page_urls,
)

THREE = ["de", "en", "uk"]
FOUR = ["da", "de", "en", "uk"]   # danskmoent, once Danish is switched on


def _profile(**over) -> SiteProfile:
    base = dict(id="t", origin="https://t.example", locations=["a"],
                languages=THREE, root_lang="en", brand="B")
    base.update(over)
    return SiteProfile(**base)


class ScopeResolution(unittest.TestCase):
    def test_allowlist_keeps_available_order(self):
        p = _profile(locations=["c", "a"])
        self.assertEqual(p.resolve_locations(["a", "b", "c"]), ["a", "c"])

    def test_denylist_is_everything_else(self):
        p = _profile(locations=None, all_except=["b"])
        self.assertEqual(p.resolve_locations(["a", "b", "c"]), ["a", "c"])

    def test_empty_denylist_is_every_location(self):
        """`all_except: []` is how munzfuss says «all of them»."""
        p = _profile(locations=None, all_except=[])
        self.assertEqual(p.resolve_locations(["a", "b"]), ["a", "b"])

    def test_unknown_id_raises_rather_than_shrinking_the_site(self):
        p = _profile(locations=["a", "typo"])
        with self.assertRaises(SiteProfileError) as cm:
            p.resolve_locations(["a", "b"])
        self.assertIn("typo", str(cm.exception))

    def test_unknown_id_in_a_denylist_also_raises(self):
        """A removed location left in `all_except` is a stale config, not a
        no-op: it silently stops excluding what it names."""
        p = _profile(locations=None, all_except=["gone"])
        with self.assertRaises(SiteProfileError):
            p.resolve_locations(["a", "b"])

    def test_zero_resolution_raises(self):
        p = _profile(locations=None, all_except=["a"])
        with self.assertRaises(SiteProfileError):
            p.resolve_locations(["a"])


class ProfileValidation(unittest.TestCase):
    def test_scope_keys_are_mutually_exclusive(self):
        for kwargs in ({"locations": None, "all_except": None},
                       {"locations": ["a"], "all_except": ["b"]}):
            with self.subTest(**kwargs), self.assertRaises(Exception):
                _profile(**kwargs)

    def test_root_lang_must_be_rendered(self):
        """`root_lang` names the version copied to the site root; a value
        outside `languages` would silently leave the root empty. (The case
        used to be spelled with «da», which now reads as a real language.)"""
        with self.assertRaises(Exception):
            _profile(root_lang="zz")          # not in `languages`

    def test_origin_must_not_end_in_a_slash(self):
        """It is concatenated with base_url + an absolute path, so a trailing
        slash yields `https://host//de/`."""
        with self.assertRaises(Exception):
            _profile(origin="https://t.example/")

    def test_unknown_field_is_rejected(self):
        """_StrictBase forbids extras: a typo'd key must not be ignored."""
        with self.assertRaises(Exception):
            _profile(langauges=THREE)


class ShippedProfiles(unittest.TestCase):
    """The two configs that actually publish."""

    def test_munzfuss_is_a_tree_site_with_a_landing(self):
        p = load_site("munzfuss")
        self.assertEqual((p.mount, p.landing, p.out_dir),
                         ("tree", True, "site"))

    def test_the_two_sites_do_not_publish_the_same_location(self):
        """Denmark publishes as danskmoent.github.io from this same data.
        Left in both profiles it would put the identical page on two hosts,
        competing with itself in search."""
        m, d = load_site("munzfuss"), load_site("danskmoent")
        self.assertIn("denmark", m.all_except)
        self.assertEqual(d.locations, ["denmark"])
        self.assertFalse(set(m.all_except) - set(d.locations),
                         "a location munzfuss drops must be published somewhere")

    def test_only_the_danish_site_renders_danish(self):
        """Danish exists for this one page. Switching it on for munzfuss too
        would put a language with no prose behind it on twelve German pages,
        each silently falling back to English."""
        m, d = load_site("munzfuss"), load_site("danskmoent")
        self.assertEqual(d.languages, ["da", "de", "en", "uk"])
        self.assertEqual(d.root_lang, "da")
        self.assertNotIn("da", m.languages)
        self.assertEqual(m.root_lang, "en")

    def test_the_danish_site_leads_with_danish(self):
        """`languages` order is the hreflang and switcher order."""
        self.assertEqual(load_site("danskmoent").languages[0], "da")

    def test_danskmoent_is_one_page_at_its_own_root(self):
        p = load_site("danskmoent")
        self.assertEqual((p.mount, p.landing, p.locations),
                         ("root", False, ["denmark"]))

    def test_the_two_sites_do_not_share_a_static_root(self):
        """A Search Console token proves ownership of ONE host; copying
        munzfuss's into the Danish tree claims a relationship that does not
        exist."""
        self.assertNotEqual(load_site("munzfuss").static_dir,
                            load_site("danskmoent").static_dir)

    def test_each_site_brands_itself_in_its_own_language(self):
        """«Møntfod» is the Danish term for a Müntzfuß, attested on
        danskmoent.dk itself. Being a -fod standard name it is one string in
        every language (§2 tier 2), which is why the Danish site also
        overrides the localised eyebrow."""
        m, d = load_site("munzfuss"), load_site("danskmoent")
        self.assertEqual(m.brand, "Müntzfüße")
        self.assertEqual(d.brand, "Møntfod")
        self.assertIsNone(m.eyebrow)      # falls back to the localised ui.yml
        self.assertEqual(d.eyebrow, "Møntfod")

    def test_unknown_site_raises_and_names_the_ones_that_exist(self):
        with self.assertRaises(SiteProfileError) as cm:
            load_site("nope")
        self.assertIn("munzfuss", str(cm.exception))


class TreeMountedUrls(unittest.TestCase):
    """A location under /<loc>/<lang>/ — munzfuss. No page collapses into
    the site root, so every language is self-canonical."""

    def urls(self, lang, root_lang="de"):
        return page_urls("", "/lubeck", THREE, lang, root_lang, False)

    def test_every_language_is_self_canonical(self):
        for lang in THREE:
            with self.subTest(lang=lang):
                self.assertEqual(self.urls(lang)["canonical"],
                                 f"/lubeck/{lang}/")

    def test_x_default_follows_the_root_language(self):
        self.assertEqual(self.urls("en")["x_default"], "/lubeck/de/")

    def test_alternates_cover_every_language_in_render_order(self):
        self.assertEqual(self.urls("en")["alternates"],
                         [("de", "/lubeck/de/"), ("en", "/lubeck/en/"),
                          ("uk", "/lubeck/uk/")])


class RootMountedUrls(unittest.TestCase):
    """The page IS the site root — danskmoent. The root language is written
    twice (to `/` and `/<lang>/`) so it must consolidate onto `/`."""

    def urls(self, lang, root_lang="de"):
        return page_urls("", "", THREE, lang, root_lang, True)

    def test_root_language_canonicalises_to_the_bare_root(self):
        self.assertEqual(self.urls("de")["canonical"], "/")

    def test_other_languages_stay_self_canonical(self):
        self.assertEqual(self.urls("en")["canonical"], "/en/")
        self.assertEqual(self.urls("uk")["canonical"], "/uk/")

    def test_x_default_is_the_root(self):
        self.assertEqual(self.urls("uk")["x_default"], "/")

    def test_alternates_point_the_root_language_at_the_root(self):
        self.assertEqual(self.urls("en")["alternates"],
                         [("de", "/"), ("en", "/en/"), ("uk", "/uk/")])


class DanishDefaultAtTheRoot(unittest.TestCase):
    """The shape danskmoent takes once Danish is its default: four languages,
    root-mounted, and the default one collapsing onto «/».

    Exercised separately from RootMountedUrls because both bugs this whole
    extraction exists to stop are invisible when the default is English — the
    wrong answer and the right one coincide at `/en/`.
    """

    def urls(self, lang):
        return page_urls("", "", FOUR, lang, "da", True)

    def test_danish_is_the_root_and_has_no_directory_of_its_own(self):
        self.assertEqual(self.urls("da")["canonical"], "/")

    def test_german_no_longer_collapses_just_because_it_is_first_alphabetically(self):
        """`da` sorts before `de`; the collapse follows root_lang, not order."""
        self.assertEqual(self.urls("de")["canonical"], "/de/")

    def test_every_language_agrees_on_one_x_default(self):
        self.assertEqual({self.urls(l)["x_default"] for l in FOUR}, {"/"})

    def test_the_hreflang_cluster_covers_all_four(self):
        self.assertEqual(self.urls("en")["alternates"],
                         [("da", "/"), ("de", "/de/"), ("en", "/en/"),
                          ("uk", "/uk/")])

    def test_a_fourth_language_does_not_disturb_a_tree_mount(self):
        """munzfuss keeps three; nothing here is global state."""
        u = page_urls("", "/lubeck", THREE, "en", "de", False)
        self.assertEqual(u["canonical"], "/lubeck/en/")


class BaseUrlPrefix(unittest.TestCase):
    """A project-pages deploy serves the whole site under /<repo>/."""

    def test_base_url_prefixes_every_shape(self):
        u = page_urls("/repo", "/lubeck", THREE, "en", "de", False)
        self.assertEqual(u["canonical"], "/repo/lubeck/en/")
        self.assertEqual(u["x_default"], "/repo/lubeck/de/")

    def test_base_url_survives_the_root_collapse(self):
        u = page_urls("/repo", "", THREE, "de", "de", True)
        self.assertEqual(u["canonical"], "/repo/")


class NoDoubleSlashes(unittest.TestCase):
    def test_no_url_ever_doubles_a_slash(self):
        """`/lubeck` + `/` + `de/` is easy to write as `//de/` — and a
        canonical that 404s is worse than none."""
        for prefix in ("", "/lubeck"):
            for collapses in (False, True):
                for lang in THREE:
                    url = lang_url("", prefix, lang, "de", collapses)
                    with self.subTest(prefix=prefix, collapses=collapses,
                                      lang=lang):
                        self.assertNotIn("//", url)
                        self.assertTrue(url.startswith("/"))
                        self.assertTrue(url.endswith("/"))


class TemplatesHoldNoUrlLogic(unittest.TestCase):
    """The regression this whole extraction exists to stop.

    The URL shapes lived inline in both templates, which is how `en` came to
    be hard-coded in six of them. They now render precomputed values; a new
    hand-built link in a template would drift from `page_urls` without any
    build failing.
    """

    TEMPLATES = ROOT / "templates"

    def test_no_template_hardcodes_the_site_brand(self):
        """The brand is per-site: the Danish site calls itself «Møntfod», not
        «Müntzfüße». A literal in a template would silently re-brand it."""
        for name in ("location.html.j2", "landing.html.j2"):
            text = (self.TEMPLATES / name).read_text(encoding="utf-8")
            for i, line in enumerate(text.splitlines(), 1):
                if line.lstrip().startswith("{#") or "Müntzfüße" not in line:
                    continue
                with self.subTest(template=name, line=i):
                    self.fail(f"{name}:{i} hardcodes the brand: {line.strip()}")

    def test_no_template_builds_a_canonical_or_hreflang_href_by_hand(self):
        for name in ("location.html.j2", "landing.html.j2"):
            text = (self.TEMPLATES / name).read_text(encoding="utf-8")
            for line in text.splitlines():
                if 'rel="canonical"' not in line and "hreflang=" not in line:
                    continue
                if "href=" not in line:
                    continue
                with self.subTest(template=name, line=line.strip()[:60]):
                    self.assertNotIn("base_url", line)
                    self.assertNotIn("'en'", line)


if __name__ == "__main__":
    unittest.main()
