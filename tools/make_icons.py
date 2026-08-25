"""Generate Pass Chart app icons. Run: python tools/make_icons.py"""
import os
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons")
os.makedirs(OUT, exist_ok=True)

BG = (16, 20, 38)
RAMP = [(61, 220, 151), (245, 192, 68), (240, 132, 75), (234, 76, 96)]


def icon(size, maskable=False):
    """A stack of four bars in the grade ramp - the ribbon, which is the
    app's one visual signature. Maskable keeps everything inside the safe
    circle Android crops to."""
    img = Image.new("RGBA", (size, size), BG + (255,))
    d = ImageDraw.Draw(img)

    pad = size * (0.26 if maskable else 0.17)
    w = size - 2 * pad
    gap = size * 0.035
    bar_h = (w - 3 * gap) / 4.0
    radius = max(2, int(bar_h * 0.42))

    # widths echo a real passing distribution: lots of 2s, few 0s
    fracs = [0.62, 1.00, 0.46, 0.24]
    for i, (col, f) in enumerate(zip(RAMP, fracs)):
        y0 = pad + i * (bar_h + gap)
        d.rounded_rectangle(
            [pad, y0, pad + w * f, y0 + bar_h],
            radius=radius, fill=col + (255,),
        )
    return img


for size in (192, 512):
    icon(size).save(os.path.join(OUT, "icon-%d.png" % size))
icon(512, maskable=True).save(os.path.join(OUT, "maskable-512.png"))

# iOS does not honour transparency or maskable; give it its own opaque square
ios = icon(180).convert("RGB")
ios.save(os.path.join(OUT, "apple-touch-icon.png"))

for f in sorted(os.listdir(OUT)):
    p = os.path.join(OUT, f)
    print("%-24s %6d bytes  %s" % (f, os.path.getsize(p), Image.open(p).size))
