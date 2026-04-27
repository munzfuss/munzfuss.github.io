#!/usr/bin/env python3
"""One-off: strip stale TODO markers from schleswig.yml.

All `# TODO: translate` and `# TODO: expand note from original HTML if needed`
comments are stale — translations have been completed in a subsequent pass, but
the markers were never cleaned up.

Run once:
    python scripts/strip_stale_todos.py
"""
import pathlib
import re

p = pathlib.Path("data/locations/schleswig.yml")
text = p.read_text()
before = text

# Strip trailing "# TODO: translate" comments (with optional whitespace before)
text = re.sub(r"\s*#\s*TODO:\s*translate\s*$", "", text, flags=re.MULTILINE)

# Remove standalone "# TODO: expand note from original HTML if needed" lines
# (they are on their own line, possibly with indentation)
text = re.sub(
    r"^[ \t]*#\s*TODO:\s*expand note from original HTML if needed\s*\n",
    "",
    text,
    flags=re.MULTILINE,
)

# Clean up accidental double blank lines that can result
text = re.sub(r"\n{3,}", "\n\n", text)

if text == before:
    print("Nothing to change.")
else:
    p.write_text(text)
    removed_translate = before.count("TODO: translate") - text.count("TODO: translate")
    removed_expand = before.count("TODO: expand note") - text.count("TODO: expand note")
    print(f"Removed {removed_translate} 'TODO: translate' markers")
    print(f"Removed {removed_expand} 'TODO: expand note' markers")
