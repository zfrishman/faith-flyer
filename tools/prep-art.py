#!/usr/bin/env python3
"""Prepare Faith Flyer art: compress backgrounds and crop transparent plane sprites.

Reads originals from art/src and writes the files the game loads:
  art/bg-eden.webp, art/bg-noah.webp, art/end-tree.webp, art/end-ark.webp
  art/plane-1.png ... art/plane-4.png
"""
from pathlib import Path
import math
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "art" / "src"
OUT = ROOT / "art"

SCENES = {
    "bg-eden.jpg": "bg-eden.webp",
    "bg-noah.jpg": "bg-noah.webp",
    "end-tree-of-life.jpg": "end-tree.webp",
    "end-ark.jpg": "end-ark.webp",
}


def save_scene(src_name, dest_name, target=200_000):
    im = Image.open(SRC / src_name).convert("RGB")
    # Sources are already near 1280px. Keep that width (about 1600, not upscaled).
    if im.width > 1600:
        h = round(im.height * 1600 / im.width)
        im = im.resize((1600, h), Image.Resampling.LANCZOS)
    dest = OUT / dest_name
    best = None
    for q in (78, 72, 66, 60, 54, 48):
        im.save(dest, "WEBP", quality=q, method=6)
        size = dest.stat().st_size
        best = (q, size)
        if size <= target:
            break
    print(f"{dest_name}: {im.size} q={best[0]} {best[1]} bytes")


def is_paper(r, g, b):
    # Off-white paper. Colored paint (even pale wood) stays opaque.
    return r >= 236 and g >= 234 and b >= 228 and (max(r, g, b) - min(r, g, b)) < 18


def key_white(im):
    im = im.convert("RGBA")
    pix = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pix[x, y]
            if is_paper(r, g, b):
                # Soft edge: how far the pixel is from pure paper.
                dist = math.sqrt((255 - r) ** 2 + (255 - g) ** 2 + (255 - b) ** 2)
                if dist < 14:
                    pix[x, y] = (r, g, b, 0)
                elif dist < 32:
                    pix[x, y] = (r, g, b, int(255 * (dist - 14) / 18))
            # else keep
    return im


def crop_planes():
    im = Image.open(SRC / "planes-right.jpg").convert("RGB")
    w, h = im.size
    px = im.load()
    cols = []
    for x in range(w):
        ink = 0
        for y in range(0, h, 2):
            r, g, b = px[x, y]
            if not is_paper(r, g, b):
                ink += 1
        cols.append(ink)
    runs = []
    on = None
    for x, ink in enumerate(cols):
        if ink > 6 and on is None:
            on = x
        elif ink <= 6 and on is not None:
            if x - on > 30:
                runs.append((on, x - 1))
            on = None
    if on is not None and w - on > 30:
        runs.append((on, w - 1))
    if len(runs) != 4:
        raise SystemExit(f"expected 4 planes, found {len(runs)}: {runs}")
    for i, (x0, x1) in enumerate(runs, start=1):
        top, bot = h, 0
        for x in range(x0, x1 + 1):
            for y in range(h):
                r, g, b = px[x, y]
                if not is_paper(r, g, b):
                    if y < top:
                        top = y
                    if y > bot:
                        bot = y
        pad = 10
        box = (max(0, x0 - pad), max(0, top - pad), min(w, x1 + pad + 1), min(h, bot + pad + 1))
        crop = key_white(im.crop(box))
        # Trim fully transparent borders but keep a hair of padding.
        bbox = crop.getbbox()
        if bbox:
            crop = crop.crop(bbox)
        # Cap width so the PNGs stay light for an iPad.
        if crop.width > 480:
            nh = round(crop.height * 480 / crop.width)
            crop = crop.resize((480, nh), Image.Resampling.LANCZOS)
        dest = OUT / f"plane-{i}.png"
        crop.save(dest, "PNG", optimize=True)
        print(f"plane-{i}.png {crop.size} {dest.stat().st_size} bytes from {box}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for src, dest in SCENES.items():
        save_scene(src, dest)
    crop_planes()


if __name__ == "__main__":
    main()
