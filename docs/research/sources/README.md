# docs/research/sources/

Raw external source captures — full-text preservations of external
articles, monographs, and online publications that the project's
research dossiers (in the parent `docs/research/` directory) cite
frequently or substantively.

## What lives here

Each file is a **literal markdown transcript** of an external source,
captured to local storage so future sessions can read the source
without re-fetching (which may fail if the source moves, the site
goes offline, or the original is paywall-restricted).

Files in this directory are **NOT our analysis**. They are
preserved-as-is external content. Our analysis of the captured
content lives in the parent `docs/research/<topic>.md` dossiers.

## How it differs from related surfaces

| Surface | Purpose | Content type |
|---|---|---|
| `docs/research/sources/<source>.md` | **Raw external capture** | Verbatim transcript of external article |
| `docs/research/<topic>.md` | Topical research dossier (our analysis) | Our findings, computed metrics, cross-source synthesis |
| `docs/SOURCES.md` §13 | Per-source quirks log | Short notes on source behaviour / parsing quirks |
| `scripts/cache/hede/*.json` | Per-coin Hede catalogue pages | Structured JSON parsed from danskmoent.dk |

A source preserved here may be cited from multiple research
dossiers. The capture is the canonical local reference; the
dossiers cite it and quote verbatim passages as needed.

## Capture metadata

Every file begins with a metadata header:

```markdown
# <Source title>

> **Source capture** — full markdown transcript of an external source.
>
> - **Original URL**: <https://example.com/path>
> - **Fetched**: YYYY-MM-DD via WebFetch
> - **Author / publisher**: ...
> - **Original publication**: ... (year, journal, monograph, etc.)
> - **License / public domain status**: ... (if known)
> - **Captured by**: claude / human

This is a verbatim local copy of the external source. The original
remains the authoritative version; this file exists only as
preservation against link rot and to allow future sessions to
consult the source without re-fetching.

---

[full content below]
```

## File naming

`<source_slug>.md` — descriptive snake_case identifier prefixed with
the publisher / author identifier where appropriate. Examples:

- `galster_galshist.md` — Galster's *Danske mønter* historical
  overview (danskmoent.dk/galster/galshist.htm).
- `galster_galsfre2.md` — Galster's *Danske efterligninger af
  fremmed mønt fra nyere tid* (danskmoent.dk/galster/galsfre2.htm).
- `wilcke_w6a.md` — Wilcke's *Kong Hans' rhinske Guldgylden*
  (danskmoent.dk/wilcke/w6a.htm).

When a publisher's site uses opaque file names, prefer descriptive
slugs over verbatim paths (e.g. `wilcke_hans_rhinske_guldgylden.md`
rather than `wilcke_w6a.md`) — but keep the original URL in the
metadata header so the source is locatable.

## When to capture

Capture an external source when:

- The source is cited substantively (>1 quote, or extensive
  paraphrase) by 2+ research dossiers.
- The source is non-trivial to re-fetch (auth-walled, slow site,
  region-restricted).
- The source could plausibly disappear (small personal site, blog
  post, anonymous transcript).
- The source contains data we want to grep / cross-reference
  programmatically (URLs, dates, coin specs, mintage figures).

Do NOT capture:

- Live numismatic databases (Numista, ucoin, IKMK) — their content
  is dynamic and structured; cache those via `scripts/cache/` not
  here.
- Sources cited only once with a short scope-note (just the URL +
  page hint in the references-file ref entry is enough).
- Copyrighted / proprietary material where the licence prohibits
  redistribution. Public-domain or freely-licensed material only.

## Closure / lifecycle

Captures stay in this directory indefinitely. They are immutable
preservation artefacts — never deleted (would defeat the «against
link rot» purpose), occasionally updated if the source publishes a
revised version (with the prior capture preserved as
`<slug>_YYYY-MM-DD.md` archive).
