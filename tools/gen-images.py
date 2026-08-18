#!/usr/bin/env python3
"""Генерация WebP-версий изображений для sintegra-additive.ru.

Запуск:  python3 tools/gen-images.py
Перезапустите после замены исходных фото на оригиналы высокого качества.
"""
import os
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(HERE, "img")

JOBS = [
    ("hbd-p400.jpg", (768,), 82),
    ("korpus-kompressora.jpg", (960, 480), 80),
    ("photo_2026-06-23_15-00-04.jpg", (960, 480), 80),
    ("photo_2026-06-24_14-54-05.jpg", (960, 480), 80),
]

for src, widths, q in JOBS:
    path = os.path.join(IMG, src)
    if not os.path.exists(path):
        print("skip (no source):", src)
        continue
    im = Image.open(path)
    base, _ = os.path.splitext(src)
    for w in widths:
        h = round(im.height * w / im.width)
        out = im.resize((w, h), Image.LANCZOS)
        dst = os.path.join(IMG, f"{base}-{w}w.webp" if w != im.width else f"{base}.webp")
        out.save(dst, "WEBP", quality=q, method=6)
        print(f"{src} -> {os.path.basename(dst)} ({w}x{h}, q{q})")