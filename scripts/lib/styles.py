"""
CSS prefix generator.

The bulk of the stylesheet lives as a real .css file at `assets/style.base.css`
(language-agnostic, references theme tokens via `var(--*)`). This module
generates the small `prefix` that:

  • Imports web fonts.
  • Defines the v3 (Noir, default) palette as CSS custom properties on
    `:root` — pulled from `config/theme.yml`.
  • Sets per-`html[lang]` `--body-line-height` overrides so the static
    base CSS can resolve them via `body { line-height: var(--body-line-height) }`.
  • Emits the per-bar timeline palette CSS from `theme.yml: timeline_bars`.

`build_css(theme)` returns `prefix + base.css` content as a single string,
ready to write to `site/assets/style.css`.
"""
from __future__ import annotations

from pathlib import Path


BASE_CSS_PATH = Path(__file__).resolve().parent / "style.base.css"


FONT_IMPORTS = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500"
    "&family=Inter:wght@400;500;600"
    "&family=JetBrains+Mono:wght@400;500"
    "&family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400;1,700"
    "&family=Spectral:ital,wght@0,400;0,500;0,700;1,400"
    "&family=Source+Serif+Pro:ital,wght@0,400;0,600;1,400"
    "&display=swap');\n"
)


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """`#abcdef` → `(171, 205, 239)`. Tolerant of leading `#` only."""
    s = hex_str.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def _timeline_bars_css(bars: dict) -> str:
    """Theme-agnostic timeline-bar palette generated from theme.yml.

    For every palette key (rt / si / sh / kr / krm / vt / rm / g / …) emits:
      • foreground / weight rules on `.tl-bar.{palette}` (no background —
        the colour comes from layered `.tl-bar-layer` siblings now).
      • flat-colour `.tl-bar-layer.{palette}` rules using the brighter
        `to` colour at 1/6 alpha (~0.1667). Combined with the layer's
        `mix-blend-mode: plus-lighter`, six overlapping layers sum to the
        original full colour, and any subset renders proportionally
        fainter — providing the visual decomposition of the period ×
        scope grid (mint / status / circulation × anywhere / holstein).
      • a kept-as-fallback gradient on `.tl-bar.{palette}:not(.tl-bar-layered)`
        so any bar that doesn't yet carry events still renders as before.
    """
    out: list[str] = []
    noir_selector = (
        ':root:not([data-theme="v1"]):not([data-theme="v2"])'
    )
    alpha = 1 / 6  # six layers stacking with plus-lighter sum to alpha=1
    for bar_id, conf in bars.items():
        extras = []
        if conf.get("fg"):
            extras.append(f"color: {conf['fg']};")
        if conf.get("weight"):
            extras.append(f"font-weight: {conf['weight']};")
        extras_str = " " + " ".join(extras) if extras else ""

        # Foreground / weight on `.tl-bar.{palette}` (no background here).
        if extras_str.strip():
            out.append(f".tl-bar.{bar_id} {{{extras_str} }}")

        # Layer-colour rule.
        r, g, b = _hex_to_rgb(conf["to"])
        out.append(
            f".tl-bar-layer.{bar_id} {{ "
            f"--layer-bg: rgba({r}, {g}, {b}, {alpha:.4f}); "
            f"background: var(--layer-bg); }}"
        )

        # Light-theme override (v1 atlas / v2 codex).
        # See the original CLAUDE.md / DECISIONS.md for the WCAG / hue
        # rationale behind the from_light field and the 0.7 darkening.
        if "from_light" in conf:
            fr_d, fg_d, fb_d = _hex_to_rgb(conf["from_light"])
        else:
            DARKEN = 0.70
            fr, fg, fb = _hex_to_rgb(conf["from"])
            fr_d, fg_d, fb_d = int(fr * DARKEN), int(fg * DARKEN), int(fb * DARKEN)
        out.append(
            f'[data-theme="v1"] .tl-bar-layer.{bar_id}, '
            f'[data-theme="v2"] .tl-bar-layer.{bar_id} {{ '
            f"--layer-bg: rgba({fr_d}, {fg_d}, {fb_d}, {alpha:.4f}); }}"
        )

        # Fallback gradient kept for bars without layers (no events data).
        out.append(
            f".tl-bar.{bar_id}:not(.tl-bar-layered) {{ "
            f"background: linear-gradient(90deg, {conf['from']}, {conf['to']}); }}"
        )
        out.append(
            f"{noir_selector} .tl-bar.{bar_id}:not(.tl-bar-layered)"
            f":not(.tl-bar-reichsdukatenfuss) {{ "
            f"background: linear-gradient(90deg, {conf['to']}, {conf['from']}); }}"
        )
        out.append(
            f'[data-theme="v1"] .tl-bar.{bar_id}:not(.tl-bar-layered), '
            f'[data-theme="v2"] .tl-bar.{bar_id}:not(.tl-bar-layered) {{ '
            f"background: linear-gradient(90deg, {conf['to']}, {conf['from']}); }}"
        )

    # Per-bar layer-visibility overrides — see the long comment in the
    # historical version of this function for the alpha-doubling rationale.
    if "rt" in bars:
        rt_r, rt_g, rt_b = _hex_to_rgb(bars["rt"]["to"])
        out.append(
            f".tl-bar.tl-bar-9_thaler .tl-bar-layer.tl-bar-layer-circulation"
            f".tl-bar-layer-holstein {{ "
            f"--layer-bg: rgba({rt_r}, {rt_g}, {rt_b}, {alpha * 2:.4f}); }}"
        )

    # Sole-kind opacity reduction (4th layer kind beyond mint/status/
    # circulation; halving its alpha keeps the additive stacking inside
    # the 100 % envelope on light themes).
    out.append(".tl-bar-layer.tl-bar-layer-sole { opacity: 0.5; }")

    return "\n".join(out)


def build_prefix(theme: dict) -> str:
    """Generate the dynamic CSS prefix from theme.yml.

    Contents (in order):
      1. Font imports
      2. `:root` block — every palette token referenced by var(--*) in
         `assets/style.base.css`. v3 (Noir) is the default; v1 / v2 are
         hardcoded inside base.css since those palettes are static.
      3. `html[lang="en"]` / `html[lang="uk"]` overrides for
         `--body-line-height`. The default value lives in `:root` above.
      4. Per-bar timeline palette block.
    """
    c = theme.get("colors", {})
    a = theme.get("accents", {})

    # Default body line-height (DE) and per-language overrides.
    overrides = theme.get("language_overrides", {}) or {}
    default_lh = "1.55"
    en_lh = (overrides.get("en") or {}).get("line_height", default_lh)
    uk_lh = (overrides.get("uk") or {}).get("line_height", default_lh)

    root = f"""\
:root, :root[data-theme="v3"] {{
  --bg-page:        {c.get("bg_page", "#14110d")};
  --bg-card:        {c.get("bg_card", "#1c1813")};
  --bg-subcard:     {c.get("bg_subcard", "#241f18")};
  --bg-elev:        #241f18;

  --text-primary:   {c.get("text_primary", "#ece4d2")};
  --text-secondary: {c.get("text_secondary", "#b8ad96")};
  --text-muted:     {c.get("text_muted", "#7a7060")};
  --text-faint:     {c.get("text_dim", "#666")};

  --border:         {c.get("border", "#2e2820")};
  --border-soft:    {c.get("border_subtle", "#3a3530")};
  --border-light:   {c.get("border_light", "#3e372c")};

  --accent:         {a.get("gold_deep", "#d4a85a")};
  --accent-deep:    {a.get("gold_border", "#5a4a38")};
  --accent-glow:    #f0c878;
  --accent-muted:   {a.get("gold_muted", "#c0a680")};
  --accent-bg:      {a.get("pill_active_bg", "#2a2320")};
  --accent-bg-strong: rgba(212, 168, 90, 0.12);

  --purple:         {c.get("accent_purple", "#b5a0d0")};
  --cite:           {c.get("cite_color", "#e3c789")};

  --font-display:   'Cormorant Garamond', 'EB Garamond', Georgia, serif;
  --font-body:      'Spectral', 'Source Serif Pro', Georgia, serif;
  --font-sans:      'Inter', system-ui, -apple-system, sans-serif;
  --font-mono:      'JetBrains Mono', 'SF Mono', Consolas, monospace;

  --radius-card:    6px;
  --radius-pill:    999px;
  --radius-block:   4px;

  --page-pad-x:     64px;
  --page-pad-y:     56px;

  --bg-grad:        radial-gradient(ellipse at top, #1c1813, var(--bg-page) 60%);
  --hairline:       0.5px;

  /* Δ-deviation palette */
  --sd-under-deep-fg:   {c.get("under_deep", "#c97a3d")};
  --sd-under-deep-bg:   {c.get("under_deep_bg", "#2a1e14")};
  --sd-under-mild-fg:   {c.get("under_mild", "#a08966")};
  --sd-under-mild-bg:   {c.get("under_mild_bg", "#221a13")};
  --sd-over-mild-fg:    {c.get("over_mild", "#68a257")};
  --sd-over-mild-bg:    {c.get("over_mild_bg", "#1a2a1a")};
  --sd-over-strong-fg:  {c.get("over_strong", "#92d24c")};
  --sd-over-strong-bg:  {c.get("over_strong_bg", "#1f3017")};

  /* Metal-indicator badge palette (.bx / .bx.gold inside .gw-head) */
  --badge-silver-bg:    {c.get("badge_silver_bg", "#555")};
  --badge-silver-fg:    {c.get("badge_silver_fg", "#ddd")};
  --badge-gold-bg:      {c.get("badge_gold_bg", "#5c3d00")};
  --badge-gold-fg:      {c.get("badge_gold_fg", "#fcd34d")};

  /* Subcat divider tokens (.mt-subcat.kurant / .scheide / .copper) */
  --subcat-kurant-bg:      {c.get("subcat_kurant_bg", "#1f2d1a")};
  --subcat-kurant-border:  {c.get("subcat_kurant_border", "#6b8e4e")};
  --subcat-kurant-fg:      {c.get("subcat_kurant_fg", "#c4d9a6")};
  --subcat-scheide-bg:     {c.get("subcat_scheide_bg", "#2d231a")};
  --subcat-scheide-border: {c.get("subcat_scheide_border", "#c28b4b")};
  --subcat-scheide-fg:     {c.get("subcat_scheide_fg", "#e6c590")};
  --subcat-copper-bg:      {c.get("subcat_copper_bg", "#2a1f19")};
  --subcat-copper-border:  {c.get("subcat_copper_border", "#a8673c")};
  --subcat-copper-fg:      {c.get("subcat_copper_fg", "#d69a6e")};

  /* Default body line-height — DE. html[lang=en|uk] override below. */
  --body-line-height:   {default_lh};
}}

html[lang="en"] {{ --body-line-height: {en_lh}; }}
html[lang="uk"] {{ --body-line-height: {uk_lh}; }}
"""

    bar_block = _timeline_bars_css(theme.get("timeline_bars", {}) or {})

    return (
        FONT_IMPORTS
        + "\n"
        + root
        + "\n/* --- Per-bar gradients (from theme.yml) --- */\n"
        + bar_block
        + "\n"
    )


def build_css(theme: dict) -> str:
    """Return the full stylesheet — `prefix` (theme-driven) + `style.base.css`
    (static).

    Output is language-agnostic; per-language line-height is selected via
    `html[lang=…] { --body-line-height: … }` rules emitted in the prefix.
    """
    prefix = build_prefix(theme)
    base = BASE_CSS_PATH.read_text(encoding="utf-8")
    return prefix + base
