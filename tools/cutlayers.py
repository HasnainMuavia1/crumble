"""Cut ChatGPT transparent PNGs into scroll-film layers.

usage: python3 tools/cutlayers.py <cup.png> <halves.png> <goo.png> <crumbs.png> <swirl.png>
Writes assets/film/{cup,half-l,half-r,goo,swirl,crumb-N}.webp and assets/film/meta.json.
"""
import json
import sys
from collections import deque

import numpy as np
from PIL import Image, ImageFilter

ROOT = __file__.rsplit("/tools/", 1)[0] + "/assets/film/"


def trim(im):
    return im.crop(im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox())


def components(im, f=4, thr=20, minarea=12):
    a = np.array(im.getchannel("A"))
    small = np.array(Image.fromarray(a).resize((a.shape[1] // f, a.shape[0] // f), Image.BILINEAR)) > thr
    lab = np.zeros(small.shape, np.int32)
    n = 0
    H, W = small.shape
    for y in range(H):
        for x in np.nonzero(small[y] & (lab[y] == 0))[0]:
            if lab[y, x]:
                continue
            n += 1
            q = deque([(y, x)])
            lab[y, x] = n
            while q:
                cy, cx = q.popleft()
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < H and 0 <= nx < W and small[ny, nx] and not lab[ny, nx]:
                        lab[ny, nx] = n
                        q.append((ny, nx))
    out = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if len(ys) < minarea:
            continue
        out.append({"i": i, "area": len(ys), "box": (xs.min() * f, ys.min() * f, (xs.max() + 1) * f, (ys.max() + 1) * f)})
    return out, lab, f


def cut(im, c, lab, f, pad=6):
    m = Image.fromarray(((lab == c["i"]) * 255).astype(np.uint8)).resize(im.size, Image.NEAREST).filter(ImageFilter.MaxFilter(9))
    arr = np.array(im)
    arr[..., 3] = np.minimum(arr[..., 3], np.array(m))
    x0, y0, x1, y1 = c["box"]
    return trim(Image.fromarray(arr).crop((max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), min(im.height, y1 + pad))))


def save(im, name, maxside=900, q=86):
    t = im.copy()
    t.thumbnail((maxside, maxside))
    t.save(ROOT + name, "WEBP", quality=q, method=6)
    return t


cup_p, halves_p, goo_p, crumbs_p, swirl_p = sys.argv[1:6]
save(trim(Image.open(cup_p).convert("RGBA")), "cup.webp")
save(trim(Image.open(swirl_p).convert("RGBA")), "swirl.webp")
g = trim(Image.open(goo_p).convert("RGBA"))
g.thumbnail((1400, 600))
g.save(ROOT + "goo.webp", "WEBP", quality=84, method=6)

h = Image.open(halves_p).convert("RGBA")
cs, lab, f = components(h)
L, R = sorted(sorted(cs, key=lambda c: -c["area"])[:2], key=lambda c: c["box"][0])
hl, hr = cut(h, L, lab, f), cut(h, R, lab, f)
save(hl, "half-l.webp", 800)
save(hr, "half-r.webp", 800)
cy = lambda c: (c["box"][1] + c["box"][3]) / 2
mid = (cy(L) + cy(R)) / 2
meta = {"halves": {"joinedW": hl.width + hr.width, "l": {"w": hl.width, "dy": cy(L) - mid}, "r": {"w": hr.width, "dy": cy(R) - mid}}}

c = Image.open(crumbs_p).convert("RGBA")
cs, lab, f = components(c, f=2)
crumbs = []
for k, comp in enumerate(sorted(cs, key=lambda x: -x["area"])[:9]):
    im = cut(c, comp, lab, f, pad=3)
    t = save(im, f"crumb-{k + 1}.webp", 260, 88)
    # width relative to the halves source scale
    crumbs.append({"file": f"crumb-{k + 1}.webp", "w": im.width, "h": im.height})
meta["crumbs"] = crumbs
json.dump(meta, open(ROOT + "meta.json", "w"), indent=1)
print(json.dumps(meta))
