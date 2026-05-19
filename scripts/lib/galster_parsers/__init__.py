"""Per-page-shape parsers for danskmoent.dk Galster pages.

The Galster cache at ``scripts/cache/danskmoent/galster/`` mixes five
distinct page shapes that share a folder but require different parsing
strategies. Rather than branching inside a monolithic parser, each
shape gets its own module + a dispatcher (`classify.detect_page_shape`)
routes incoming pages to the right module.

Page shapes (see ``classify.py`` for detection rules):

  1. ``standard``     — typical coin page (`chr/c2g37`, `fr/f1g46`,
                       `norge/nc2g164`). H1 carries ruler+denom+year.
                       Implementation: ``standard.py``.

  2. ``grevenfejde``  — possessive-H1 coin page from the Grevens Fejde
                       (Count's Feud, 1534-1536) series. H1 reads
                       «Christian 2.s tilhængere under Grevens Fejde»;
                       the actual coin descriptor sits in body-H2.
                       7 known pages (chr_c2g80…91).
                       Implementation: ``grevenfejde.py``.

  3. ``reign_index``  — reign-overview tables (`c2galst.htm`,
                       `f1galst.htm`). Not a coin — a table-of-contents
                       summarising all coins for that reign.
                       Implementation: ``reign_index.py`` (skip).

  4. ``article``      — danskmoent.dk blog articles (`artikler_*`,
                       `ernst_*` without a Galster-number filename
                       component). Not coin data.
                       Implementation: ``article.py`` (skip).

  5. (future)         — extension slot for new shapes; add module +
                       extend ``classify.detect_page_shape``.

A per-shape parser's `parse_page(html_path, normalised_text)` returns
either a sidecar dict ready to be JSON-serialised, or a sentinel
``{"skip": True, "reason": <shape>, "source_file": <name>}`` that
tells the entry-builder to drop the page from the seed.
"""

from . import article, classify, grevenfejde, reign_index, standard

__all__ = ["article", "classify", "grevenfejde", "reign_index", "standard"]
