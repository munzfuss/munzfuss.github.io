#!/usr/bin/env python3
"""Generate the project's favicon family from a single source image.

Input  : SOURCE_PATH (a JPG/PNG with a SOLID near-white background and
         the subject — a Christian-IV gold coin in the canonical case —
         clearly contrasting against it).

Output (written to `assets/`):
  • `favicon.ico`           — 16+32+48 multi-resolution ICO
  • `favicon-16.png`        — small browser tab variant
  • `favicon-32.png`        — high-DPI browser tab
  • `favicon-192.png`       — Android home-screen
  • `favicon-512.png`       — high-res / OpenGraph share-card upgrade
  • `apple-touch-icon.png`  — 180×180 iOS / iPadOS home-screen

(The transparent master can always be re-derived by re-running this
script against the source JPG; we don't ship a 2 MB intermediate to
the live site.)

Pipeline:
  1. Load source as RGBA.
  2. White-background removal via per-pixel «whiteness» threshold with a
     smooth alpha transition in the 220-245 brightness band (preserves
     anti-aliased coin edge instead of producing a hard-cut silhouette).
  3. Auto-crop to the subject's alpha-bounding-box plus a 2 % padding.
  4. Center on a square canvas so resizing doesn't distort the coin's
     round shape.
  5. Resize via Lanczos (high-quality downsample) for each output size.
  6. Save PNGs + multi-resolution ICO.

The CLAUDE.md «scripts directory layout» rule places this under
`scripts/maintenance/` because it's a one-shot-per-source-image
re-runnable utility, not part of the build flow.
"""
from pathlib import Path
import sys

try:
    import numpy as np
    from PIL import Image
except ImportError as e:
    print(f"❌ Missing dependency: {e}. Run `pip install Pillow numpy`.")
    sys.exit(1)


REPO_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = REPO_ROOT / "assets"

SOURCE_PATH = Path.home() / "Downloads" / "66a6741ea191a9.68097845-original.jpg"

# Output sizes for browser / OS variants
PNG_SIZES = {
    "favicon-16.png":         16,
    "favicon-32.png":         32,
    "favicon-192.png":       192,
    "favicon-512.png":       512,
    "apple-touch-icon.png":  180,
}
ICO_SIZES = [16, 32, 48]  # multi-resolution favicon.ico

# Whiteness threshold band for background removal:
#   pixels with min(R,G,B) >= UPPER → fully transparent (background)
#   pixels with min(R,G,B) <= LOWER → fully opaque (subject)
#   between → linear alpha (smooth anti-aliased edge)
THRESH_UPPER = 245
THRESH_LOWER = 220


def remove_white_background(img: Image.Image) -> Image.Image:
    """Return an RGBA copy of `img` with near-white pixels turned
    transparent. Uses min-channel «whiteness» (sensitive to colour cast,
    so a gold pixel with R=240 G=240 B=200 stays opaque because its
    min-channel is 200 — well below the LOWER band).
    """
    rgba = img.convert("RGBA")
    arr = np.array(rgba)               # shape (H, W, 4)
    rgb = arr[:, :, :3]
    mn = rgb.min(axis=2)               # whiteness per pixel
    # Linear alpha ramp in the threshold band.
    alpha = np.full(mn.shape, 255, dtype=np.uint8)
    # Above UPPER → 0; below LOWER → 255; in-between linear.
    band = (mn > THRESH_LOWER) & (mn < THRESH_UPPER)
    alpha[mn >= THRESH_UPPER] = 0
    # In-band: interpolate from 255 at LOWER → 0 at UPPER.
    band_vals = ((THRESH_UPPER - mn[band]) * 255 / (THRESH_UPPER - THRESH_LOWER))
    alpha[band] = np.clip(band_vals, 0, 255).astype(np.uint8)
    arr[:, :, 3] = alpha
    return Image.fromarray(arr, "RGBA")


def autocrop_to_subject(img: Image.Image, pad_pct: float = 0.02) -> Image.Image:
    """Crop `img` (RGBA) to its alpha-bounding-box with `pad_pct` padding."""
    bbox = img.getbbox()
    if not bbox:
        return img
    x0, y0, x1, y1 = bbox
    w = x1 - x0
    h = y1 - y0
    pad = int(max(w, h) * pad_pct)
    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(img.width, x1 + pad)
    y1 = min(img.height, y1 + pad)
    return img.crop((x0, y0, x1, y1))


def center_on_square(img: Image.Image) -> Image.Image:
    """Place `img` (RGBA) centred on a transparent square canvas whose
    side = max(w, h). Keeps round subjects round after resize."""
    w, h = img.size
    side = max(w, h)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - w) // 2, (side - h) // 2), img)
    return canvas


def main():
    if not SOURCE_PATH.exists():
        print(f"❌ Source not found: {SOURCE_PATH}")
        sys.exit(1)

    print(f"📷 Loading {SOURCE_PATH.name} ...")
    src = Image.open(SOURCE_PATH)
    print(f"   original: {src.size[0]}×{src.size[1]} px, mode={src.mode}")

    print("🧹 Removing white background ...")
    transparent = remove_white_background(src)

    print("✂️  Auto-cropping to subject ...")
    cropped = autocrop_to_subject(transparent, pad_pct=0.02)
    print(f"   cropped: {cropped.size[0]}×{cropped.size[1]} px")

    print("⏹  Centering on square canvas ...")
    square = center_on_square(cropped)
    print(f"   square : {square.size[0]}×{square.size[1]} px")

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    # PNG variants
    print("\n💾 Writing PNG variants:")
    for filename, size in PNG_SIZES.items():
        resized = square.resize((size, size), Image.LANCZOS)
        out = ASSETS_DIR / filename
        resized.save(out, format="PNG", optimize=True)
        print(f"   → {out.relative_to(REPO_ROOT)}  ({size}×{size}, {out.stat().st_size:,} bytes)")

    # Multi-resolution favicon.ico
    print("\n💾 Writing favicon.ico (multi-resolution):")
    ico_sources = [square.resize((s, s), Image.LANCZOS) for s in ICO_SIZES]
    ico_out = ASSETS_DIR / "favicon.ico"
    ico_sources[0].save(
        ico_out,
        format="ICO",
        sizes=[(s, s) for s in ICO_SIZES],
        # Pillow's ICO writer accepts an `append_images` for multi-res
        append_images=ico_sources[1:],
    )
    print(f"   → {ico_out.relative_to(REPO_ROOT)}  "
          f"(sizes: {', '.join(str(s) for s in ICO_SIZES)}, "
          f"{ico_out.stat().st_size:,} bytes)")

    print("\n✅ Done. Re-run any time the source image changes.")


if __name__ == "__main__":
    main()
