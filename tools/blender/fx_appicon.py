"""The app icon: a glowing blue anchor on the night sky, in the same comic ink style as the UI icons.

Android wants three pictures:
  * T_AppIcon.png             1024 px, the whole icon on its background, for legacy and round icons.
  * T_AppIcon_Background.png  432 px, the night sky alone, the adaptive icon's back layer.
  * T_AppIcon_Foreground.png  432 px, the anchor alone on transparency, the adaptive icon's front layer.
    Launchers crop adaptive icons to any shape and show only the middle 66/108 safely, so the anchor
    is drawn small enough to sit inside that circle.

    fx_appicon.generate(out_dir)   # inside Blender, or any Python with numpy
"""
from pathlib import Path

import numpy as np

from fx_image import smoothstep, write_png

SAMPLES = 2  # Supersampling, for clean edges at every launcher size.

NIGHT_CENTRE = (0.11, 0.19, 0.42)
NIGHT_EDGE = (0.02, 0.04, 0.12)
INK = (0.02, 0.04, 0.12)
GLOW = (0.25, 0.68, 1.0)
CORE_EDGE = (0.32, 0.74, 1.0)
CORE_MIDDLE = (0.86, 0.97, 1.0)

FULL_SCALE = 0.78  # The anchor's share of the square icon.
FOREGROUND_SCALE = 0.6  # Inside the adaptive icon's safe circle, with room for the glow.


class _Grid:
    """Signed-distance shapes in units where the icon spans -1..1, y up. Matches fx_icons.G."""

    def __init__(self, x, y):
        self.x, self.y = x, y

    def circle(self, cx, cy, r):
        return np.hypot(self.x - cx, self.y - cy) - r

    def ring(self, cx, cy, r, t):
        return np.abs(self.circle(cx, cy, r)) - t

    def box(self, cx, cy, hx, hy, rnd=0.0):
        qx, qy = np.abs(self.x - cx) - hx + rnd, np.abs(self.y - cy) - hy + rnd
        return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - rnd

    def line(self, ax, ay, bx, by, r):
        dx, dy = bx - ax, by - ay
        h = np.clip(((self.x - ax) * dx + (self.y - ay) * dy) / (dx * dx + dy * dy), 0, 1)
        return np.hypot(self.x - ax - dx * h, self.y - ay - dy * h) - r

    def poly(self, *points):
        pts = np.array(points, dtype=np.float32)
        d = np.full_like(self.x, 1e9)
        inside = np.zeros_like(self.x, dtype=bool)
        j = len(pts) - 1
        for i in range(len(pts)):
            ex, ey = pts[j] - pts[i]
            wx, wy = self.x - pts[i][0], self.y - pts[i][1]
            h = np.clip((wx * ex + wy * ey) / (ex * ex + ey * ey), 0, 1)
            d = np.minimum(d, (wx - ex * h) ** 2 + (wy - ey * h) ** 2)
            crosses = (self.y >= pts[i][1]) != (self.y >= pts[j][1])
            at_x = (pts[j][0] - pts[i][0]) * (self.y - pts[i][1]) / (pts[j][1] - pts[i][1] + 1e-9) + pts[i][0]
            inside ^= crosses & (self.x < at_x)
            j = i
        return np.sqrt(d) * np.where(inside, -1, 1)


def anchor(g):
    """An anchor: ring, stock, shank, and two curved arms ending in flukes."""
    ring = g.ring(0.0, 0.7, 0.15, 0.06)
    stock = g.box(0.0, 0.42, 0.42, 0.06, rnd=0.05)
    stock_ends = np.minimum(g.circle(-0.44, 0.42, 0.085), g.circle(0.44, 0.42, 0.085))
    shank = g.line(0.0, 0.55, 0.0, -0.66, 0.08)
    arms = np.maximum(g.ring(0.0, -0.08, 0.62, 0.075), g.box(0.0, -0.57, 0.9, 0.45))
    flukes = np.minimum(
        g.poly((-0.68, 0.1), (-0.84, -0.22), (-0.5, -0.17)),
        g.poly((0.68, 0.1), (0.84, -0.22), (0.5, -0.17)),
    )
    crown = g.circle(0.0, -0.68, 0.11)
    return np.minimum.reduce([ring, stock, stock_ends, shank, arms, flukes, crown])


def _axes(size):
    px = size * SAMPLES
    axis = (np.arange(px, dtype=np.float32) + 0.5) / px * 2 - 1
    x, y = np.meshgrid(axis, -axis)
    return x, y, px


def _downsample(image):
    h, w = image.shape[:2]
    return image.reshape(h // SAMPLES, SAMPLES, w // SAMPLES, SAMPLES, -1).mean(axis=(1, 3))


def _sky(x, y):
    """Deep night blue, lighter behind the anchor, with a scatter of small stars."""
    r = np.clip(np.hypot(x, y * 1.05) / 1.25, 0, 1)
    t = smoothstep(0.0, 1.0, r)[..., None]
    image = np.array(NIGHT_CENTRE, dtype=np.float32) * (1 - t) + np.array(NIGHT_EDGE, dtype=np.float32) * t
    rng = np.random.default_rng(7)
    stars = np.zeros_like(x)
    for sx, sy, size in zip(rng.uniform(-0.95, 0.95, 26), rng.uniform(-0.95, 0.95, 26), rng.uniform(0.006, 0.016, 26)):
        if np.hypot(sx, sy) < 0.55:
            continue  # Keep the middle clear for the anchor.
        stars = np.maximum(stars, smoothstep(size, 0.0, np.hypot(x - sx, y - sy)))
    return image + stars[..., None] * np.array((0.75, 0.85, 1.0), dtype=np.float32) * 0.8


def _anchor_layer(x, y, px, scale):
    """The glowing anchor as colour plus coverage: a soft blue halo, an ink line, and a bright core."""
    g = _Grid(x / scale, y / scale)
    d = anchor(g) * scale
    aa = 2.0 / px * 1.2
    ink_width = 0.03 * scale / FULL_SCALE

    halo = np.exp(-np.maximum(d, 0) / (0.09 * scale / FULL_SCALE)) * 0.85
    ink = smoothstep(aa, -aa, d - ink_width)
    fill = smoothstep(aa, -aa, d)

    # Hotter toward the middle of each stroke, like a glowing tube.
    depth = np.clip(-d / (0.06 * scale), 0, 1)
    core = np.array(CORE_EDGE, dtype=np.float32) * (1 - depth[..., None]) + np.array(CORE_MIDDLE, dtype=np.float32) * depth[..., None]

    colour = np.broadcast_to(np.array(GLOW, dtype=np.float32), x.shape + (3,)).copy()
    alpha = halo.copy()
    colour = colour * (1 - ink[..., None]) + np.array(INK, dtype=np.float32) * ink[..., None]
    alpha = np.maximum(alpha, ink)
    colour = colour * (1 - fill[..., None]) + core * fill[..., None]
    return colour, alpha


def _over(base, colour, alpha):
    return base * (1 - alpha[..., None]) + colour * alpha[..., None]


def full_icon(size=1024):
    x, y, px = _axes(size)
    colour, alpha = _anchor_layer(x, y, px, FULL_SCALE)
    image = _over(_sky(x, y), colour, alpha)
    return _downsample(np.dstack((image, np.ones_like(x))))


def background(size=432):
    x, y, _ = _axes(size)
    return _downsample(np.dstack((_sky(x, y), np.ones_like(x))))


def foreground(size=432):
    x, y, px = _axes(size)
    colour, alpha = _anchor_layer(x, y, px, FOREGROUND_SCALE)
    return _downsample(np.dstack((colour, alpha)))


def generate(out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for name, image in (("T_AppIcon.png", full_icon()), ("T_AppIcon_Background.png", background()), ("T_AppIcon_Foreground.png", foreground())):
        path = out / name
        write_png(path, np.clip(image, 0, 1))
        written.append(str(path))
    return written


if __name__ == "__main__":
    import sys
    for path in generate(sys.argv[1] if len(sys.argv) > 1 else "."):
        print(path)
