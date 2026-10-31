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


def runs_of(im):
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
    found = []
    on = None
    for x, ink in enumerate(cols):
        if ink > 6 and on is None:
            on = x
        elif ink <= 6 and on is not None:
            if x - on > 30:
                found.append((on, x - 1))
            on = None
    if on is not None and w - on > 30:
        found.append((on, w - 1))
    return found


def save_sprite(im, box, dest, max_w=520):
    crop = key_white(im.crop(box))
    bbox = crop.getbbox()
    if bbox:
        crop = crop.crop(bbox)
    if crop.width > max_w:
        nh = round(crop.height * max_w / crop.width)
        crop = crop.resize((max_w, nh), Image.Resampling.LANCZOS)
    dest = OUT / dest
    crop.save(dest, "PNG", optimize=True)
    print(f"{dest.name}: {crop.size} {dest.stat().st_size} bytes")
    return dest


def crop_row(src_name, names):
    im = Image.open(SRC / src_name).convert("RGB")
    found = runs_of(im)
    if len(found) != len(names):
        raise SystemExit(f"{src_name}: expected {len(names)} sprites, found {len(found)} {found}")
    w, h = im.size
    px = im.load()
    for (x0, x1), name in zip(found, names):
        if not name:
            continue
        top, bot = h, 0
        for x in range(x0, x1 + 1):
            for y in range(h):
                r, g, b = px[x, y]
                if not is_paper(r, g, b):
                    top = min(top, y)
                    bot = max(bot, y)
        pad = 8
        box = (max(0, x0 - pad), max(0, top - pad), min(w, x1 + pad + 1), min(h, bot + pad + 1))
        save_sprite(im, box, name)


def crop_grid(src_name, names, cols, rows):
    im = Image.open(SRC / src_name).convert("RGB")
    w, h = im.size
    cw, ch = w / cols, h / rows
    if len(names) != cols * rows:
        raise SystemExit(f"{src_name}: name count {len(names)}")
    for i, name in enumerate(names):
        if not name:
            continue
        c, r = i % cols, i // cols
        box = (int(c * cw), int(r * ch), int((c + 1) * cw), int((r + 1) * ch))
        save_sprite(im, box, name, max_w=360)


def crop_planes():
    im = Image.open(SRC / "planes-right.jpg").convert("RGB")
    w, h = im.size
    px = im.load()
    runs = runs_of(im)
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
        save_sprite(im, box, f"plane-{i}.png")


ANIMALS = [
    "animal-lion.png", "animal-zebra.png", "animal-elephant.png", "animal-giraffe.png",
    "animal-sheep.png", "animal-bear.png", "animal-camel.png", "animal-kangaroo.png",
    "animal-penguin.png", "animal-rabbit.png", "animal-owl.png", "animal-turtle.png",
]
TROPHIES = [
    "trophy-fruit.png", "trophy-lily.png", "trophy-leaf.png", "trophy-butterfly.png",
    "trophy-feather.png", "trophy-stone.png", "trophy-nest.png", "trophy-sunflower.png",
    "trophy-olive.png", "trophy-dove.png", "trophy-rainbow.png", "trophy-hammer.png",
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for src, dest in SCENES.items():
        save_scene(src, dest)
    crop_planes()
    crop_row("planes-eden-early.jpg", [f"eden-{i}.png" for i in range(1, 5)])
    # Image 2 of the Noah sheet looks like a car, so it is skipped.
    crop_row("planes-noah-early.jpg", ["noah-1.png", None, "noah-3.png", "noah-4.png"])
    crop_grid("animals.jpg", ANIMALS, 4, 3)
    crop_grid("trophies.jpg", TROPHIES, 4, 3)


if __name__ == "__main__":
    main()
