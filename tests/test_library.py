"""The research library keeps originals outside git, so its manifest is the
only record of what exists and where its other copies are.

Introduced 2026-11-25 (docs/plans/research_library_split.md). Before it, the
six Secher PDFs sat gitignored in the harvest cache with no second copy and no
record outside one json per volume; nothing would have noticed their loss.
These tests pin the behaviour that makes a lost or altered file visible:
a missing origin URL is not an error, a changed byte is, fetch tries the
release before the origin and never silently accepts bytes that differ, and
a bundle's hash does not depend on how its tar was packed.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "library"))

import library as L  # noqa: E402


class FakeBackend:
    """Release assets in memory; digests computed like GitHub's."""

    def __init__(self):
        self.store: dict[str, dict[str, bytes]] = {}
        self.uploads = 0

    def assets(self, tag):
        if tag not in self.store:
            return None
        import hashlib
        return {k: hashlib.sha256(v).hexdigest() for k, v in self.store[tag].items()}

    def ensure_release(self, tag):
        self.store.setdefault(tag, {})

    def upload(self, tag, asset, src):
        self.uploads += 1
        self.store[tag][asset] = Path(src).read_bytes()
        return self.assets(tag)[asset]

    def download(self, tag, asset, dest):
        Path(dest).write_bytes(self.store[tag][asset])


def quiet(fn, *a, **kw):
    buf = StringIO()
    with redirect_stdout(buf):
        rc = fn(*a, **kw)
    return rc, buf.getvalue()


class LibraryTest(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        base = Path(self.td.name)
        self.root = base / "lib"
        (self.root / "work" / "d1" / "alto").mkdir(parents=True)
        (self.root / "work" / "a.pdf").write_bytes(b"%PDF original")
        (self.root / "work" / "d1" / "alto" / "p1.xml").write_text("<a/>")
        (self.root / "work" / "d1" / "alto" / "p2.xml").write_text("<b/>")
        self.lib = L.Library(self.root, base / "corpus" / "library_manifest.yml")
        self.be = FakeBackend()

    def tearDown(self):
        self.td.cleanup()

    def rec(self, path):
        return {r["path"]: r for r in self.lib.load()}[path]

    def test_add_without_url_is_not_an_error(self):
        rc, out = quiet(L.cmd_add, self.lib, ["work/a.pdf"], None, None, False, False)
        self.assertEqual(rc, 0)
        self.assertIn("url: unknown", out)
        self.assertNotIn("source_url", self.rec("work/a.pdf"))
        rc, out = quiet(L.cmd_status, self.lib, True)
        self.assertIn("single copy (no backup, no URL): 1", out)

    def test_verify_catches_a_changed_byte(self):
        quiet(L.cmd_add, self.lib, ["work/a.pdf"], "http://x/a.pdf", None, False, False)
        self.assertEqual(quiet(L.cmd_verify, self.lib, [])[0], 0)
        (self.root / "work" / "a.pdf").write_bytes(b"%PDF originaL")
        rc, out = quiet(L.cmd_verify, self.lib, [])
        self.assertEqual(rc, 1)
        self.assertIn("1 differ", out)

    def test_re_add_of_changed_file_needs_force(self):
        quiet(L.cmd_add, self.lib, ["work/a.pdf"], None, None, False, False)
        (self.root / "work" / "a.pdf").write_bytes(b"other")
        self.assertEqual(quiet(L.cmd_add, self.lib, ["work/a.pdf"], None, None, False, False)[0], 1)

    def test_backup_then_fetch_from_release(self):
        quiet(L.cmd_add, self.lib, ["work/a.pdf"], None, None, False, False)
        self.assertEqual(quiet(L.cmd_backup, self.lib, self.be, [], False)[0], 0)
        self.assertEqual(self.rec("work/a.pdf")["backup"],
                         {"release": "work", "asset": "a.pdf"})
        # a second backup run uploads nothing
        quiet(L.cmd_backup, self.lib, self.be, [], False)
        self.assertEqual(self.be.uploads, 1)
        (self.root / "work" / "a.pdf").unlink()
        calls = []
        rc, out = quiet(L.cmd_fetch, self.lib, self.be, ["work/a.pdf"], False, None,
                        fetch_url=lambda u, d: calls.append(u))
        self.assertEqual(rc, 0)
        self.assertIn("(release)", out)
        self.assertEqual(calls, [])  # origin not touched when the release works
        self.assertEqual((self.root / "work" / "a.pdf").read_bytes(), b"%PDF original")

    def test_origin_serving_other_bytes_is_flagged_not_accepted(self):
        quiet(L.cmd_add, self.lib, ["work/a.pdf"], "http://x/a.pdf", None, False, False)
        (self.root / "work" / "a.pdf").unlink()
        rc, out = quiet(L.cmd_fetch, self.lib, self.be, ["work/a.pdf"], False, None,
                        fetch_url=lambda u, d: Path(d).write_bytes(b"new edition"))
        self.assertEqual(rc, 1)
        self.assertIn("different bytes", out)
        self.assertFalse((self.root / "work" / "a.pdf").exists())
        self.assertTrue((self.root / "work" / "a.pdf.origin-mismatch").exists())

    def test_origin_used_when_no_release(self):
        quiet(L.cmd_add, self.lib, ["work/a.pdf"], "http://x/a.pdf", None, False, False)
        (self.root / "work" / "a.pdf").unlink()
        rc, out = quiet(L.cmd_fetch, self.lib, self.be, ["work/a.pdf"], False, None,
                        fetch_url=lambda u, d: Path(d).write_bytes(b"%PDF original"))
        self.assertEqual(rc, 0)
        self.assertIn("(origin)", out)

    def test_bundle_roundtrip(self):
        quiet(L.cmd_add, self.lib, ["work/d1/alto"], None, None, True, False)
        r = self.rec("work/d1/alto")
        self.assertEqual((r["kind"], r["files"]), ("bundle", 2))
        quiet(L.cmd_backup, self.lib, self.be, [], False)
        b = self.rec("work/d1/alto")["backup"]
        self.assertEqual(b["asset"], "d1--alto.tar.gz")
        import shutil
        shutil.rmtree(self.root / "work" / "d1" / "alto")
        rc, out = quiet(L.cmd_fetch, self.lib, self.be, [], True, None)
        self.assertEqual(rc, 0, out)
        self.assertEqual((self.root / "work" / "d1" / "alto" / "p2.xml").read_text(), "<b/>")
        # status: alto files are covered by the bundle record, not «unrecorded»
        quiet(L.cmd_add, self.lib, ["work/a.pdf"], None, None, False, False)
        self.assertIn("unrecorded files: 0", quiet(L.cmd_status, self.lib, False)[1])

    def test_tar_is_deterministic(self):
        d = self.root / "work" / "d1" / "alto"
        a, b = Path(self.td.name) / "a.tgz", Path(self.td.name) / "b.tgz"
        L.make_tar(d, a)
        (d / "p1.xml").touch()  # new mtime, same bytes
        L.make_tar(d, b)
        self.assertEqual(L.sha256_file(a), L.sha256_file(b))

    def test_asset_name_is_github_safe(self):
        # «Jesse side 99-104.pdf»: GitHub stored it as «Jesse.side.99-104.pdf»
        # and the digest lookup by the original name found nothing.
        self.assertEqual(L.asset_location({"path": "danskmoent/jesse_1927/Jesse side 99-104.pdf"}),
                         ("danskmoent", "jesse_1927--Jesse_side_99-104.pdf"))

    def test_top_level_file_has_no_release(self):
        (self.root / "loose.pdf").write_bytes(b"x")
        quiet(L.cmd_add, self.lib, ["loose.pdf"], None, None, False, False)
        with self.assertRaises(SystemExit):
            quiet(L.cmd_backup, self.lib, self.be, [], False)



class OriginalsResolutionTest(unittest.TestCase):
    """lib.originals: during the move the library wins, the cache is the
    fallback, and a missing file names the command that restores it."""

    def setUp(self):
        from lib import paths
        self.paths = paths
        self.saved = (paths.LIBRARY_ROOT, paths.HARVEST_ROOT)
        self.td = tempfile.TemporaryDirectory()
        b = Path(self.td.name)
        paths.LIBRARY_ROOT, paths.HARVEST_ROOT = b / "lib", b / "cache"
        for r, body in ((b / "lib", b"L"), (b / "cache", b"C")):
            (r / "w").mkdir(parents=True)
            (r / "w" / "both.pdf").write_bytes(body)
        (b / "cache" / "w" / "cache_only.pdf").write_bytes(b"C")

    def tearDown(self):
        self.paths.LIBRARY_ROOT, self.paths.HARVEST_ROOT = self.saved
        self.td.cleanup()

    def test_resolution(self):
        from lib.originals import MissingOriginal, iter_originals, original
        self.assertEqual(original("w/both.pdf").read_bytes(), b"L")
        self.assertEqual(original("w/cache_only.pdf").read_bytes(), b"C")
        # the repo-relative spelling used before the library existed
        self.assertEqual(original(self.paths.LEGACY_CACHE_PREFIX + "w/both.pdf").read_bytes(), b"L")
        with self.assertRaises(MissingOriginal) as cm:
            original("w/none.pdf")
        self.assertIn("library.py fetch w/none.pdf", str(cm.exception))
        got = {r: f.read_bytes() for r, f in iter_originals(".pdf")}
        self.assertEqual(got, {"w/both.pdf": b"L", "w/cache_only.pdf": b"C"})


if __name__ == "__main__":
    unittest.main()
