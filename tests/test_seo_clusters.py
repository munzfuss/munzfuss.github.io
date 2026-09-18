"""`generate_seo_files` derives the sitemap from the RENDERED tree rather
than from Location objects, which makes it the one place where a site's
shape has to be re-derived from disk instead of read from the profile. Two
assumptions were baked in when there was only ever one site: that English
is the default language, and that a landing page exists at the root.

Neither holds now. danskmoent has no landing — its single location IS the
root — and both sites are due to change their default language. A sitemap
that disagrees with the pages' own canonical tags is the quiet kind of
wrong: every page renders, the build exits 0, and search engines get two
contradictory answers about which URL is canonical.

The tree here is synthetic, so these run in milliseconds; the real shapes
were confirmed against full builds of both profiles.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build as bld  # noqa: E402

THREE = ["de", "en", "uk"]


class SeoTreeCase(unittest.TestCase):
    """Points the module's output globals at a throwaway tree."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.site = Path(self._tmp.name)
        self._saved = (bld.SITE_DIR, bld.SITE_ORIGIN, bld.REPO_ROOT)
        bld.SITE_DIR = self.site
        bld.SITE_ORIGIN = "https://t.example"
        # `generate_seo_files` logs a path relative to the repo root.
        bld.REPO_ROOT = self.site.parent

    def tearDown(self):
        bld.SITE_DIR, bld.SITE_ORIGIN, bld.REPO_ROOT = self._saved
        self._tmp.cleanup()

    def page(self, *parts):
        d = self.site.joinpath(*parts)
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text("<html></html>", encoding="utf-8")

    def locs(self) -> list[str]:
        import re
        xml = (self.site / "sitemap.xml").read_text(encoding="utf-8")
        return re.findall(r"<loc>([^<]+)</loc>", xml)

    def x_defaults(self) -> set[str]:
        import re
        xml = (self.site / "sitemap.xml").read_text(encoding="utf-8")
        return set(re.findall(r'hreflang="x-default" href="([^"]+)"', xml))


class RootMountedSinglePage(SeoTreeCase):
    """danskmoent: `/`, `/de/`, `/en/`, `/uk/` and nothing else."""

    def build(self, root_lang="en"):
        for lang in THREE:
            self.page(lang)
        (self.site / "index.html").write_text("<html></html>", encoding="utf-8")
        bld.generate_seo_files(THREE, "", root_lang=root_lang)

    def test_one_cluster_and_no_location_subtree(self):
        self.build()
        self.assertEqual(len(self.locs()), 3)
        self.assertNotIn("denmark", " ".join(self.locs()))

    def test_root_language_is_listed_at_the_root_not_its_own_directory(self):
        """The root language renders twice; the sitemap must name the URL the
        pages canonicalise to, or the two contradict each other."""
        self.build(root_lang="en")
        self.assertIn("https://t.example/", self.locs())
        self.assertNotIn("https://t.example/en/", self.locs())

    def test_a_german_default_moves_the_collapse_to_german(self):
        self.build(root_lang="de")
        self.assertIn("https://t.example/", self.locs())
        self.assertNotIn("https://t.example/de/", self.locs())
        self.assertIn("https://t.example/en/", self.locs())

    def test_x_default_is_always_the_root(self):
        self.build(root_lang="de")
        self.assertEqual(self.x_defaults(), {"https://t.example/"})


class TreeMountedSite(SeoTreeCase):
    """munzfuss: a landing at the root plus locations under /<loc>/<lang>/."""

    def build(self, root_lang="en"):
        for lang in THREE:
            self.page(lang)
            self.page("lubeck", lang)
        (self.site / "index.html").write_text("<html></html>", encoding="utf-8")
        bld.generate_seo_files(THREE, "", root_lang=root_lang)

    def test_landing_and_location_are_separate_clusters(self):
        self.build()
        self.assertEqual(len(self.locs()), 6)

    def test_location_languages_all_keep_their_own_directory(self):
        """Only the landing has a root copy; a location page under a tree
        mount never collapses."""
        self.build(root_lang="de")
        for lang in THREE:
            self.assertIn(f"https://t.example/lubeck/{lang}/", self.locs())

    def test_location_x_default_follows_the_root_language(self):
        self.build(root_lang="de")
        self.assertIn("https://t.example/lubeck/de/", self.x_defaults())

    def test_assets_dir_is_not_mistaken_for_a_location(self):
        self.build()
        (self.site / "assets").mkdir(exist_ok=True)
        bld.generate_seo_files(THREE, "", root_lang="en")
        self.assertNotIn("https://t.example/assets/", self.locs())


class NoRootPage(SeoTreeCase):
    """`landing: false` with `mount: tree` — locations in their own subtrees
    and nothing at «/». Nothing ships in this shape today, which is exactly
    why it is pinned: the root cluster used to be unconditional, so such a
    site would have advertised «/» as its x-default while «/» 404s."""

    def test_no_root_cluster_when_no_root_page_was_written(self):
        for lang in THREE:
            self.page("lubeck", lang)
            self.page("denmark", lang)
        bld.generate_seo_files(THREE, "", root_lang="de")
        self.assertNotIn("https://t.example/", self.locs())
        self.assertEqual(len(self.locs()), 6)

    def test_locations_still_get_their_clusters(self):
        for lang in THREE:
            self.page("lubeck", lang)
        bld.generate_seo_files(THREE, "", root_lang="de")
        self.assertIn("https://t.example/lubeck/en/", self.locs())
        self.assertEqual(self.x_defaults(), {"https://t.example/lubeck/de/"})


class ProjectPagesPrefix(SeoTreeCase):
    def test_base_url_prefixes_every_url(self):
        """A project-pages deploy serves the site under /<repo>/."""
        for lang in THREE:
            self.page(lang)
        (self.site / "index.html").write_text("<html></html>", encoding="utf-8")
        bld.generate_seo_files(THREE, "/repo", root_lang="en")
        for url in self.locs():
            self.assertTrue(url.startswith("https://t.example/repo/"), url)

    def test_robots_points_at_this_sites_own_sitemap(self):
        for lang in THREE:
            self.page(lang)
        bld.generate_seo_files(THREE, "", root_lang="en")
        robots = (self.site / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("Sitemap: https://t.example/sitemap.xml", robots)


if __name__ == "__main__":
    unittest.main()
