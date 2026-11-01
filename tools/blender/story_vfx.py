"""Alpha-free mesh effects. Emissive and opaque, so they cost no transparent overdraw on weak GPUs,
and they match the low-poly art. Animate them by scaling and rotating about the `origin` socket;
they take the place of flipbooks where a preset names a fallback_mesh."""
import math
import random

from mathutils import Matrix


def _q(hq, high, low):
    return high if hq else low


def flame(mb, hq):
    """A 1.8 m flame on the deck. Spin about Z and jitter its height for a cheap flicker."""
    sides = _q(hq, 7, 4)
    outer = [(0.32, 0.0), (0.52, 0.34), (0.42, 0.84), (0.22, 1.32), (0.03, 1.8)]
    mb.lathe(outer if hq else [outer[0], outer[1], outer[3], outer[4]], sides, lambda i, _j: "ember" if i < 3 else "lamp", smooth=False)
    if hq:
        for sign, h, x in ((1, 0.9, 0.42), (-1, 0.72, 0.38)):
            with mb.xf(Matrix.Translation((sign * x, 0.05, 0.08))):
                mb.lathe([(0.15, 0.0), (0.17, h * 0.34), (0.02, h)], 5, "ember", smooth=False)
    mb.socket("origin", (0, 0, 0))


def fireball(mb, hq):
    """Unit-ish lumpy fireball, 2 m across. Scale up over about half a second, then remove."""
    rng = random.Random(5)
    lobes = _q(hq, 5, 2)
    mb.sphere((0, 0, 1.0), 1.0, _q(hq, 10, 6), _q(hq, 6, 4), lambda i, j: "lamp" if (i + j) % 3 == 0 else "ember", smooth=False)
    for _ in range(lobes):
        a, b = rng.uniform(0, 6.28), rng.uniform(-0.6, 0.8)
        x, y, z = 0.72 * math.cos(a) * math.cos(b), 0.72 * math.sin(a) * math.cos(b), 1.0 + 0.72 * math.sin(b)
        mb.sphere((x, y, z), rng.uniform(0.3, 0.5), _q(hq, 6, 4), _q(hq, 4, 2), "ember", smooth=False)
    mb.socket("origin", (0, 0, 1.0))


def smoke_puff(mb, hq):
    """Three overlapping soft lumps, 2 m across, for damage smoke on low-end devices. Solid, so
    keep a few and grow and sink them instead of fading them."""
    parts = ((0, 0, 0.8, 0.8), (0.55, 0.1, 0.62, 0.6), (-0.5, -0.1, 0.66, 0.62)) if hq else ((0, 0, 0.8, 0.8), (0.45, 0, 0.64, 0.56))
    for x, y, z, r in parts:
        mb.sphere((x, y, z), r, _q(hq, 8, 5), _q(hq, 5, 3), lambda i, _j: "storm_dark" if i <= 1 else "storm", smooth=True)
    mb.socket("origin", (0, 0, 0.8))


def shock_ring(mb, hq):
    """A flat ring, radius 1 m. Scale up fast and hide. Lies flat; rotate it to face the camera."""
    mb.lathe([(0.84, 0.0), (1.0, 0.02), (0.84, 0.04), (0.84, 0.0)], _q(hq, 32, 14), "lightning", smooth=False, caps=(False, False))
    mb.socket("origin", (0, 0, 0.02))


def plume(mb, hq):
    """Afterburner flame, 3 m long, along +Z from the socket. Rotate it to the exhaust's axis."""
    sides = _q(hq, 8, 5)
    mb.lathe([(0.42, 0.0), (0.46, 0.5), (0.26, 1.6), (0.03, 3.0)], sides, lambda i, _j: "plasma" if i < 2 else "lightning", smooth=hq)
    mb.socket("origin", (0, 0, 0))
