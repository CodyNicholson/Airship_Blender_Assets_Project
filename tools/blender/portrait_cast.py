"""Who everybody is. One function per character, plus the colours and pose that go with them.

The rule for every entry: squint at it at 108 px, the size of the comms bar, and it should still be
that person. Each character owns one big silhouette idea, one striking colour, and one expression.
Traits that the 3D model has (Krag's eyepatch, Lyra's braid) are kept, so the face on the comms bar
and the figure on the deck are plainly the same person.
"""
import math

import numpy as np

from portrait_kit import _spline, plate_mesh, rgb

INK = (0.07, 0.04, 0.05)

SKIN_TAN = rgb(205, 146, 104)
SKIN_TAN_S = rgb(150, 92, 72)
SKIN_TAN_B = rgb(204, 108, 84)


def shoulders(p, width, color, neck=0.5, top=-1.28, depth=0.74, gloss=0.0, slope=0.0):
    """The bust everything hangs on. slope>0 drops the image-left shoulder, for a bit of swagger."""
    rings = []
    for z, f in ((-7.0, 1.0), (-5.5, 1.0), (-4.0, 1.0), (-3.0, 1.0), (-2.5, 1.0), (-2.05, 0.97), (-1.82, 0.84), (-1.62, 0.56), (-1.46, 0.36), (top, neck / width)):
        ring = []
        for a in np.linspace(0, 2 * math.pi, 64, endpoint=False):
            cx, cy = math.cos(a), math.sin(a)
            # Squared-off cross-section: shoulders are boxes, not cylinders.
            r = (abs(cx) ** 3 + abs(cy) ** 3) ** (-1 / 3)
            x = r * cx * width * f
            y = 0.2 + r * cy * depth * max(f, 0.55)
            ring.append((x, y, z + slope * x * (f ** 2)))
        rings.append(ring)
    dense = _resample(rings, 6)
    p.loft(dense, color, gloss=gloss, root=p.body_root, cap=True)
    return p


def _resample(rings, per):
    """Splines down the rings. Blending ring to ring would stop dead at each one and leave steps."""
    rings = np.asarray(rings, dtype=float)
    n, m = rings.shape[:2]
    return _spline(rings.reshape(n, m * 3), per).reshape(-1, m, 3)


def goggles(p, z=0.62, y=-0.86, spread=0.3, r=0.2, lens=rgb(90, 220, 220), frame=rgb(186, 142, 62), strap=rgb(70, 44, 32), tilt=0.0):
    """Sky-crew goggles pushed up on the forehead."""
    for sign in (-1, 1):
        centre = (sign * spread, y - 0.03 + abs(sign * spread) * 0.34, z + sign * tilt)
        normal = (sign * 0.3, -1, 0.55)
        p.ball(centre, (r * 1.05, 0.11, r), frame, gloss=0.8)
        offset = (centre[0] + sign * 0.03, centre[1] - 0.075, centre[2] + 0.04)
        p.disc(offset, r * 0.72, lens, normal=normal, gloss=0.9, outline=0.0)
        p.ring(offset, r * 0.76, 0.028, rgb(90, 66, 34), gloss=0.9, normal=normal, outline=0.0)
    p.sweep([(-spread * 0.45, y - 0.05, z), (spread * 0.45, y - 0.05, z)], 0.035, frame, gloss=0.8)
    for sign in (-1, 1):
        p.sweep([(sign * (spread + r * 0.8), y + 0.15, z + 0.02), (sign * 0.8, -0.3, z + 0.06), (sign * 0.78, 0.2, z + 0.1), (sign * 0.55, 0.75, z + 0.1)], 0.075, strap, depth=0.28)
    return p


# ---- crew -------------------------------------------------------------------------------------------

def _vane_face(p, act):
    """Vane's face and hair, from the newVane reference: warm tan skin, hazel-green eyes under thick dark brows,
    a straight nose, a squarish jaw with light stubble, a small scar through the right brow and a crooked
    half-smile pulled up on the left. Golden-brown hair swept up and back with real volume, wavy over the ears
    to the jaw (longer from Act 2), under the red bandana knotted on the right."""
    skin, shade, blush = rgb(212, 158, 116), rgb(146, 92, 78), rgb(204, 112, 88)
    p.skull()
    p.base_skin(shade, blush)
    # Light stubble along the jaw, chin and upper lip.
    stubble = rgb(150, 112, 92)
    p.paint.blob(0, -0.78, 0.6, 0.3, stubble, 0.28, soft=0.7)
    rng = np.random.default_rng(7)
    for x, z in rng.uniform((-0.6, -1.02), (0.6, -0.5), (160, 2)):
        if (x / 0.6) ** 2 + ((z + 0.78) / 0.3) ** 2 < 1.0:
            p.paint.blob(x, z, 0.006, 0.006, rgb(110, 76, 64), 0.5, soft=0.3)
    hazel = rgb(116, 104, 50)
    p.eye(-1, hazel, up=0.072, low=0.034, tilt=0.008, gaze=(0.034, 0.004), lid=0.14)
    p.eye(1, hazel, up=0.072, low=0.034, tilt=0.008, gaze=(0.04, 0.004), lid=0.14)
    brow = rgb(40, 28, 24)
    p.brow(-1, brow, inner=0.1, outer=0.13, thick=0.042, arch=0.018)
    p.brow(1, brow, inner=0.1, outer=0.12, thick=0.042, arch=0.012)
    # The small scar through the right brow.
    p.paint.line([(-0.4, 0.36), (-0.37, 0.2), (-0.35, 0.1)], [0.004, 0.012, 0.004], rgb(236, 188, 156))
    p.nostrils(rgb(96, 52, 44))
    p.nose_line(shade, 1)
    p.mouth(INK, lip=rgb(170, 100, 84), lip_alpha=0.5, line=0.012)
    p.under_lip(shade)
    p.finish_skull()
    p.ear(-1, skin, shade)
    p.ear(1, skin, shade)
    p.neck(skin, width=0.36, depth=0.34)

    # Golden-brown hair: a cap over the crown and back, then volume swept up and back, then the side locks.
    base_, mid, light, dark = rgb(112, 74, 38), rgb(146, 102, 52), rgb(214, 166, 92), rgb(70, 44, 26)
    nape = -0.95 if act >= 2 else -0.75
    p.cap(base_, lambda x, y, z: (z > 0.5 - 0.1 * x * x) | ((y > 0.15) & (z > nape)), inflate=0.06)
    if act < 3:
        # Thick waves swept up off the brow and back towards his right, highest over the left of the brow.
        for k, x0 in enumerate(np.linspace(0.58, -0.6, 6)):
            top = 1.16 + 0.1 * x0 + 0.04 * math.sin(k * 2.1)
            pts = [(x0, -0.64, 0.72), (x0 - 0.1, -0.46, top), (x0 - 0.36, -0.06, top + 0.06), (x0 - 0.62, 0.42, 0.86)]
            p.sweep(pts, [0.2, 0.26, 0.22, 0.03], mid if k in (1, 4) else base_, depth=0.6)
            # A highlight riding the crest of each wave.
            p.sweep([(x0 - 0.04, -0.6, 0.86), (x0 - 0.12, -0.5, top + 0.08), (x0 - 0.34, -0.14, top + 0.12)], [0.02, 0.035, 0.005], light, depth=0.3, outline=0.0)
        # One wave curls forward over the bandana, on the left.
        p.sweep([(0.12, -0.72, 0.78), (0.3, -0.98, 0.6), (0.36, -1.02, 0.42), (0.28, -1.0, 0.34)], [0.1, 0.1, 0.07, 0.01], base_, depth=0.5)
        p.sweep([(0.16, -0.76, 0.76), (0.31, -1.0, 0.58)], [0.03, 0.01], light, depth=0.3, outline=0.0)
    # Wavy locks over the ears to the jaw, flicking out at the ends.
    drop = 0.2 if act >= 2 else 0.0
    for sign in (-1, 1):
        p.sweep([(sign * 0.78, -0.2, 0.42), (sign * 0.92, -0.12, 0.06), (sign * 0.82, -0.14, -0.28 - drop), (sign * 0.96, -0.2, -0.56 - drop)], [0.16, 0.2, 0.15, 0.02], base_, depth=0.5)
        p.sweep([(sign * 0.84, -0.3, 0.3), (sign * 0.94, -0.26, -0.1), (sign * 0.9, -0.26, -0.4 - drop)], [0.04, 0.05, 0.01], light, depth=0.3, outline=0.0)
        p.sweep([(sign * 0.74, -0.3, 0.2), (sign * 0.82, -0.3, -0.24 - drop)], [0.05, 0.01], dark, depth=0.3, outline=0.0)

    # The red bandana: a flat band across the forehead, the knot on the right, tails streaming.
    red, darkred = rgb(212, 30, 44), rgb(132, 16, 32)
    band = []
    for z in (0.46, 0.7):
        ring = []
        for a in np.linspace(0, 2 * math.pi, 64, endpoint=False):
            ring.append((math.cos(a) * 0.88, 0.03 + math.sin(a) * 1.04, z + 0.05 * max(0.0, math.sin(a))))
        band.append(ring)
    p.loft(band, red, cap=False, halftone=0.3)
    if act >= 2:
        gold = rgb(236, 186, 80)
        for z in (0.465, 0.695):
            edge = [(math.cos(a) * 0.885, 0.03 + math.sin(a) * 1.045 - 0.004, z) for a in np.linspace(math.pi * 1.1, math.pi * 1.9, 16)]
            p.sweep(edge, 0.012, gold, gloss=0.8, outline=0.0)
    p.ball((-0.88, 0.32, 0.58), (0.1, 0.12, 0.12), darkred)
    ends = 0.0 if act >= 2 else 0.04
    p.sweep([(-0.92, 0.34, 0.6), (-1.32, 0.48, 0.46), (-1.66, 0.58, 0.56)], [0.11, 0.14, ends + 0.01], red, depth=0.3)
    p.sweep([(-0.92, 0.36, 0.55), (-1.26, 0.55, 0.18), (-1.66, 0.62, 0.1)], [0.1, 0.13, ends + 0.01], darkred, depth=0.3)
    return skin, shade


def vane(p):
    """Act 1, the cast-off deckhand: thrown off the Sovereign Gale with nothing. A torn linen shirt ripped open
    at the collar, smudged with grease and tar, under a scavenged sleeveless leather jerkin with a ghost of
    darker leather and raw stitch holes where the First Mate insignia was ripped off the left breast."""
    skin, shade = _vane_face(p, 1)
    linen, grime = rgb(226, 216, 194), rgb(92, 78, 70)
    shoulders(p, 1.44, linen, neck=0.42, slope=-0.04)
    # The ripped-open collar: a deep V of bare chest, one flap torn and hanging.
    p.plate([(-0.3, -0.6, -1.36), (0.3, -0.6, -1.36), (0.04, -0.8, -2.3), (-0.04, -0.8, -2.3)], 0.03, skin, root=p.body_root)
    p.plate([(0.3, -0.62, -1.34), (0.5, -0.64, -1.5), (0.22, -0.78, -1.86)], 0.03, linen, root=p.body_root)
    p.plate([(-0.3, -0.62, -1.34), (-0.42, -0.7, -1.62), (-0.36, -0.74, -1.58), (-0.2, -0.8, -1.9)], 0.03, linen, root=p.body_root)
    p.ball((-0.12, -0.8, -2.05), (0.07, 0.015, 0.04), grime, root=p.body_root, outline=0.0)
    # The scavenged leather jerkin, open over the shirt.
    leather, leather_dark = rgb(108, 68, 42), rgb(64, 40, 28)
    for sign in (-1, 1):
        p.plate([(sign * 0.42, -0.58, -1.3), (sign * 1.0, -0.42, -1.4), (sign * 1.08, -0.6, -2.95), (sign * 0.36, -0.78, -2.95)], 0.06, leather, root=p.body_root)
    # Where the insignia was: unfaded leather, ringed with raw stitch holes.
    p.plate([(0.56, -0.8, -1.82), (0.84, -0.76, -1.82), (0.84, -0.78, -2.12), (0.56, -0.82, -2.12)], 0.02, leather_dark, root=p.body_root)
    for k in range(10):
        a = 2 * math.pi * k / 10
        p.ball((0.7 + 0.18 * math.cos(a), -0.84, -1.97 + 0.19 * math.sin(a)), (0.016, 0.01, 0.016), rgb(36, 24, 20), root=p.body_root, outline=0.0)


def vane_captain(p):
    """Act 2, the rising captain: earned authority, battle-worn. A storm-navy captain's coat with dark leather
    lapels and silver buttons over a charcoal brocade waistcoat and an open cream shirt, and a tooled leather
    baldric studded in brass across the chest."""
    skin, shade = _vane_face(p, 2)
    navy, navy_dark, leather = rgb(40, 46, 82), rgb(28, 32, 60), rgb(52, 36, 30)
    shoulders(p, 1.5, navy, neck=0.44, slope=-0.04)
    # A stand collar behind the neck, then the open shirt and the waistcoat.
    p.plate([(-0.5, -0.1, -1.0), (0.5, -0.1, -1.0), (0.56, -0.3, -1.4), (-0.56, -0.3, -1.4)], 0.05, navy_dark, root=p.body_root)
    p.plate([(-0.3, -0.62, -1.36), (0.3, -0.62, -1.36), (0.04, -0.82, -2.4), (-0.04, -0.82, -2.4)], 0.03, rgb(232, 222, 200), root=p.body_root)
    p.plate([(-0.14, -0.66, -1.42), (0.14, -0.66, -1.42), (0.0, -0.84, -2.0)], 0.03, skin, root=p.body_root)
    for sign in (-1, 1):
        p.plate([(sign * 0.3, -0.64, -1.6), (sign * 0.56, -0.62, -1.6), (sign * 0.5, -0.78, -2.9), (sign * 0.08, -0.84, -2.9)], 0.04, rgb(54, 54, 62), root=p.body_root)
        p.plate([(sign * 0.3, -0.58, -1.25), (sign * 0.72, -0.5, -1.25), (sign * 0.8, -0.64, -1.82), (sign * 0.1, -0.86, -2.45)], 0.06, leather, root=p.body_root)
        for z in (-2.05, -2.45, -2.85):
            p.ball((sign * 0.66, -0.86, z), (0.045, 0.03, 0.045), rgb(196, 202, 212), gloss=0.9, root=p.body_root, outline=0.006)
    # The baldric, left shoulder to right hip, studded in brass, the pocket watch's chain at its edge.
    p.sweep([(1.05, -0.72, -1.6), (0.3, -0.94, -2.0), (-0.75, -0.86, -2.65)], 0.13, rgb(112, 70, 42), depth=0.3, root=p.body_root)
    for k in np.linspace(0.08, 0.92, 7):
        x, z = 1.05 - 1.8 * k, -1.6 - 1.05 * k
        p.ball((x, -1.0 + 0.1 * abs(k - 0.5), z + 0.04), (0.05, 0.035, 0.05), rgb(226, 178, 74), gloss=0.9, root=p.body_root, outline=0.008)
    p.sweep([(-0.3, -0.94, -2.3), (-0.12, -0.98, -2.55), (0.1, -0.96, -2.62)], 0.012, rgb(214, 170, 70), gloss=0.9, root=p.body_root, outline=0.0)


def vane_king(p):
    """Act 3, the King of All Pirates. The red bandana still under a grand black tricorn-cavalier hat edged in
    gold, pinned up on the left with a fleet crest and a storm-petrel plume. A black greatcoat with a high flared
    collar, crimson silk lapels, a gold-trimmed storm-cape mantle and braided epaulets, over a gold-studded
    brigandine, with the ivory grips of twin pistols crossing the chest."""
    skin, shade = _vane_face(p, 3)
    black, gold, crimson = rgb(30, 28, 36), rgb(236, 186, 80), rgb(176, 22, 40)
    # The hat: crown, a wide brim pinned up on the left, braided gold edging, the crest and the plume.
    p.loft([_ellipse(0.9, 1.0, 0.8), _ellipse(0.84, 0.94, 1.22), _ellipse(0.58, 0.64, 1.46), _ellipse(0.2, 0.22, 1.52)], black)

    def brim_ring(r_out, dz):
        ring = []
        for a in np.linspace(0, 2 * math.pi, 96, endpoint=False):
            r = 0.9 + (r_out - 0.9) * 1.0
            r *= 1.0 + 0.16 * math.cos(3 * (a + math.pi / 2)) if r_out > 0.9 else 1.0
            t = (r - 0.9) / 0.85
            up = (0.5 * max(0.0, math.cos(a)) ** 2 + 0.22 * max(0.0, -math.sin(a)) ** 3) * max(0.0, t)
            ring.append((r * math.cos(a), 0.03 + r * 1.05 * math.sin(a), 0.8 + dz + up))
        return ring

    brim = [brim_ring(0.9, 0.0), brim_ring(1.75, 0.0), brim_ring(1.75, 0.07), brim_ring(0.9, 0.07)]
    p.loft(brim, black, cap=False)
    edge = np.array(brim[2])
    p.sweep(np.vstack([edge, edge[:1]]), 0.035, gold, gloss=0.85, seg=1, sides=6, outline=0.006)
    p.ball((0.98, -0.42, 1.12), (0.05, 0.16, 0.16), rgb(206, 212, 222), gloss=0.9, outline=0.006)
    p.ball((1.02, -0.44, 1.12), (0.04, 0.09, 0.09), gold, gloss=0.9, outline=0.004)
    p.sweep([(1.0, -0.38, 1.18), (1.16, -0.1, 1.62), (0.6, 0.3, 1.9), (-0.3, 0.6, 1.62)], [0.06, 0.16, 0.12, 0.01], rgb(36, 40, 70), depth=0.4)
    p.sweep([(1.12, -0.16, 1.58), (0.62, 0.22, 1.84), (-0.2, 0.52, 1.6)], [0.04, 0.04, 0.005], rgb(70, 120, 220), depth=0.3, outline=0.0)

    # The greatcoat: a high flared collar, crimson lapels edged in gold, the mantle and epaulets.
    shoulders(p, 1.62, black, neck=0.46, slope=-0.04)
    for sign in (-1, 1):
        p.plate([(sign * 0.36, -0.2, -0.95), (sign * 0.62, 0.0, -0.7), (sign * 0.8, -0.1, -1.3), (sign * 0.5, -0.4, -1.45)], 0.05, black, root=p.body_root)
        p.sweep([(sign * 0.62, -0.02, -0.7), (sign * 0.8, -0.12, -1.3)], 0.025, gold, gloss=0.8, root=p.body_root, outline=0.004)
    p.plate([(-0.26, -0.62, -1.36), (0.26, -0.62, -1.36), (0.02, -0.8, -2.2), (-0.02, -0.8, -2.2)], 0.03, rgb(40, 34, 44), root=p.body_root)
    p.plate([(-0.13, -0.66, -1.42), (0.13, -0.66, -1.42), (0.0, -0.84, -1.95)], 0.03, skin, root=p.body_root)
    for sign in (-1, 1):
        lapel = [(sign * 0.3, -0.58, -1.25), (sign * 0.74, -0.5, -1.25), (sign * 0.82, -0.64, -1.86), (sign * 0.1, -0.86, -2.5)]
        p.plate(lapel, 0.06, crimson, root=p.body_root)
        p.sweep([lapel[1], lapel[2], lapel[3]], 0.02, gold, gloss=0.8, root=p.body_root, outline=0.004)
        # The storm-cape mantle over the shoulder, its hem in gold waves, and braided epaulets.
        p.ball((sign * 1.3, -0.2, -1.62), (0.6, 0.66, 0.24), black, root=p.body_root, rot=(0, sign * 0.3, 0))
        hem = [(sign * (0.84 + 0.14 * k), -0.62 + 0.04 * k, -1.84 - 0.05 * math.sin(k * 2.2)) for k in range(6)]
        p.sweep(hem, 0.022, gold, gloss=0.8, root=p.body_root, outline=0.004)
        for k in range(6):
            x = sign * (1.3 + 0.08 * k)
            p.sweep([(x, -0.42, -1.6), (x + sign * 0.02, -0.46, -1.98)], [0.03, 0.022], gold, gloss=0.8, root=p.body_root, outline=0.005)
    # Gold studs on the brigandine, and the ivory grips of the twin pistols crossing the chest.
    for x in (-0.18, 0.18):
        for z in (-2.1, -2.35, -2.6):
            p.ball((x, -0.86, z), (0.03, 0.02, 0.03), gold, gloss=0.9, root=p.body_root, outline=0.004)
    for sign in (-1, 1):
        p.sweep([(sign * 0.95, -0.6, -1.5), (-sign * 0.5, -0.92, -2.7)], 0.08, rgb(48, 34, 30), depth=0.3, root=p.body_root)
        p.sweep([(sign * 0.6, -1.02, -2.0), (sign * 0.78, -1.04, -1.8)], [0.07, 0.08], rgb(236, 228, 206), gloss=0.6, root=p.body_root, outline=0.008)
        p.ball((sign * 0.8, -1.05, -1.78), (0.07, 0.05, 0.07), gold, gloss=0.9, root=p.body_root, outline=0.006)


def lyra(p):
    """Nomad wind mage and musician, mid-song on a windswept cliff. Bronze skin, bright eyes and an open, spirited
    smile. Wind-swirl markings trace her cheekbones and temples. Dark brown hair streams in the wind, threaded
    with thin braids, turquoise beads, metal rings and feathers. A ribbed emerald scarf runs back into a patchwork
    cloak. Cream blouse, green waistcoat edged in gold, and a driftwood-and-bone lyre hung with feathers and chimes."""
    skin, shade, blush = rgb(178, 118, 78), rgb(116, 72, 62), rgb(196, 112, 84)
    hair, hair2 = rgb(70, 44, 28), rgb(98, 64, 40)
    mark = rgb(46, 128, 118)
    turquoise, metal, gold = rgb(64, 208, 196), rgb(184, 188, 196), rgb(232, 182, 62)
    emerald, emerald2, sage, olive = rgb(26, 122, 82), rgb(14, 82, 56), rgb(140, 166, 120), rgb(110, 118, 60)
    cream, bone, wood, wood2 = rgb(238, 228, 204), rgb(232, 222, 196), rgb(150, 122, 92), rgb(104, 82, 62)

    # The patchwork cloak trails behind her, so it's drawn first.
    patches = (emerald, olive, sage, rgb(120, 92, 58), emerald2, rgb(150, 132, 84))
    for k in range(6):
        x0, z0 = 1.05 + (k % 3) * 0.42, -1.25 - (k // 3) * 0.42 + 0.12 * (k % 3)
        p.plate([(x0, 0.5, z0), (x0 + 0.44, 0.5, z0 + 0.12), (x0 + 0.44, 0.5, z0 - 0.32), (x0, 0.5, z0 - 0.44)], 0.03, patches[k], root=p.body_root)
    for x in np.linspace(1.1, 2.2, 9):
        p.sweep([(x, 0.48, -2.08 + 0.12 * (x - 1.1)), (x + 0.03, 0.48, -2.22 + 0.12 * (x - 1.1))], 0.012, olive, outline=0.0, root=p.body_root, seg=3)

    p.skull()
    p.base_skin(shade, blush)
    iris = rgb(176, 214, 92)
    p.eye(-1, iris, up=0.098, low=0.046, tilt=0.03, gaze=(0.0, 0.01), lid=0.04, iris_r=0.074, lash=0.02)
    p.eye(1, iris, up=0.098, low=0.046, tilt=0.03, gaze=(0.005, 0.01), lid=0.04, iris_r=0.074, lash=0.02)
    p.brow(-1, hair, inner=0.12, outer=0.12, thick=0.03, arch=0.05)
    p.brow(1, hair, inner=0.12, outer=0.12, thick=0.03, arch=0.05)
    p.nostrils(rgb(90, 52, 44))
    # An open, confident smile.
    p.mouth(INK, lip=rgb(166, 82, 70), lip_alpha=0.8, open_amt=0.06, teeth=True, line=0.01)
    p.under_lip(shade)
    # Wind-swirl markings across both cheekbones and up the temples.
    for sign in (-1, 1):
        for k, (r, z0) in enumerate(((0.07, -0.26), (0.045, -0.2))):
            pts = [(sign * (0.46 + r * math.cos(t)), z0 + r * math.sin(t)) for t in np.linspace(0, 1.7 * math.pi, 7)]
            p.paint.line(pts, [0.003, 0.007, 0.007, 0.006, 0.005, 0.004, 0.002], mark)
        p.paint.line([(sign * 0.4, -0.3), (sign * 0.56, -0.16), (sign * 0.6, 0.1), (sign * 0.55, 0.34)], [0.002, 0.006, 0.006, 0.002], mark)
        p.paint.line([(sign * 0.55, 0.2), (sign * 0.48, 0.28), (sign * 0.5, 0.36)], [0.002, 0.005, 0.002], mark)
    p.finish_skull()
    p.ear(1, skin, shade)
    p.neck(skin, width=0.27, depth=0.27)

    # Thick dark-brown hair in loose waves, streaming out on the wind.
    p.cap(hair, lambda x, y, z: (z > 0.6 - 0.7 * x * x) | ((y > 0.1) & (z > -0.9)), inflate=0.06)
    for k, (z0, reach, drop) in enumerate(((0.6, 2.1, 0.3), (0.35, 2.3, 0.0), (0.1, 2.2, -0.3), (-0.2, 2.0, -0.6), (-0.5, 1.8, -0.9))):
        p.sweep([(0.55, 0.15, z0), (1.1, 0.25, z0 + 0.15), (1.6, 0.3, z0 - 0.05 + 0.1 * math.sin(k)), (reach, 0.35, drop)], [0.16, 0.18, 0.12, 0.01], hair if k % 2 else hair2, depth=0.4)
    # Thin nomad braids with turquoise beads and metal rings, framing her face.
    for side, x in ((-1, -0.66), (1, 0.7)):
        path = [(x, -0.62, 0.15), (x + side * 0.06, -0.7, -0.35), (x + side * 0.02, -0.74, -0.85)]
        p.sweep(path, 0.035, hair, depth=0.6, outline=0.008)
        for k, (bx, bz) in enumerate(((x + side * 0.05, -0.25), (x + side * 0.04, -0.55), (x + side * 0.02, -0.9))):
            if k == 1:
                p.ring((bx, -0.74, bz), 0.05, 0.016, metal, gloss=0.9, normal=(0, 0, 1))
            else:
                p.ball((bx, -0.75, bz), (0.05, 0.05, 0.06), turquoise, gloss=0.8, outline=0.006)
    # Long brown-and-white feathers pinned near the crown.
    for k, (x0, lean) in enumerate(((0.32, 0.5), (0.45, 0.75))):
        p.plate([(x0, -0.3, 0.92), (x0 + 0.08, -0.3, 0.95), (x0 + lean + 0.06, -0.2, 1.6), (x0 + lean, -0.2, 1.62)], 0.02, bone, outline=0.006)
        for t in (0.35, 0.6, 0.85):
            p.sweep([(x0 + lean * t - 0.02, -0.33, 0.92 + 0.68 * t), (x0 + lean * t + 0.1, -0.33, 0.92 + 0.68 * t - 0.03)], 0.02, rgb(110, 76, 50), depth=0.2, outline=0.0, seg=3)
    p.ball((0.36, -0.42, 0.9), (0.06, 0.05, 0.06), turquoise, gloss=0.8, outline=0.006)

    # Cream linen blouse, with a fitted green waistcoat bordered in gold geometric embroidery.
    shoulders(p, 1.24, cream, neck=0.34, slope=0.08)
    for sign in (-1, 1):
        p.plate([(sign * 0.26, -0.62, -1.45), (sign * 1.02, -0.46, -1.6), (sign * 1.02, -0.6, -2.9), (sign * 0.22, -0.8, -2.9)], 0.04, emerald, root=p.body_root)
        edge = [(sign * 0.26, -0.84, -1.45), (sign * 0.22, -0.86, -2.9)]
        p.sweep(edge, 0.026, gold, root=p.body_root, outline=0.004)
        for k in range(7):
            z = -1.6 - k * 0.18
            p.sweep([(sign * 0.33, -0.86, z), (sign * 0.41, -0.86, z - 0.09), (sign * 0.33, -0.86, z - 0.18)], 0.01, gold, root=p.body_root, outline=0.0, seg=3)
    # A thick ribbed emerald scarf wound tight round the neck, its tail flying back into the cloak.
    for k, (z, f) in enumerate(((-1.72, 1.3), (-1.58, 1.2), (-1.44, 1.1), (-1.3, 1.0), (-1.16, 0.92))):
        ring = [[(math.cos(a) * 0.6 * f, 0.1 + math.sin(a) * 0.72 * f, zz + 0.08 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 64, endpoint=False)] for zz in (z, z + 0.12)]
        p.loft(ring, emerald if k % 2 else emerald2, root=p.body_root)
    p.sweep([(0.55, -0.35, -1.42), (1.05, 0.05, -1.36), (1.55, 0.3, -1.3)], [0.18, 0.2, 0.18], emerald, depth=0.3, root=p.body_root)

    # The lyre: driftwood arms, a bone crossbar and horn tips, gold strings, feathers and hanging chimes.
    lx, ly, lz = 1.02, -1.5, 0.3
    p.ball((lx, ly, lz - 2.2), (0.42, 0.15, 0.27), wood2, root=p.body_root)
    for sign in (-1, 1):
        p.sweep([(lx + sign * 0.28, ly, lz - 2.1), (lx + sign * 0.5, ly, lz - 1.72), (lx + sign * 0.36, ly, lz - 1.36), (lx + sign * 0.5, ly, lz - 1.1)], [0.075, 0.07, 0.055, 0.015], wood if sign > 0 else wood2, depth=0.6, root=p.body_root)
    p.sweep([(lx - 0.42, ly, lz - 1.4), (lx + 0.42, ly, lz - 1.4)], 0.038, bone, root=p.body_root)
    for off in np.linspace(-0.2, 0.2, 5):
        p.sweep([(lx + off, ly - 0.05, lz - 1.4), (lx + off * 0.8, ly - 0.05, lz - 2.06)], 0.012, gold, root=p.body_root, outline=0.0, seg=4)
    for k, x in enumerate((lx - 0.38, lx + 0.4)):
        p.sweep([(x, ly - 0.04, lz - 1.42), (x + 0.02, ly - 0.04, lz - 1.66)], 0.008, rgb(90, 70, 52), root=p.body_root, outline=0.0, seg=3)
        p.plate([(x - 0.03, ly - 0.06, lz - 1.64), (x + 0.04, ly - 0.06, lz - 1.64), (x + 0.02, ly - 0.06, lz - 1.98), (x - 0.01, ly - 0.06, lz - 1.98)], 0.015, bone if k else rgb(120, 86, 58), root=p.body_root, outline=0.005)
    for k, off in enumerate((-0.12, 0.0, 0.12)):
        p.sweep([(lx + off, ly - 0.08, lz - 1.42), (lx + off, ly - 0.08, lz - 1.52 - 0.06 * k)], 0.005, metal, root=p.body_root, outline=0.0, seg=3)
        p.sweep([(lx + off, ly - 0.08, lz - 1.52 - 0.06 * k), (lx + off, ly - 0.08, lz - 1.7 - 0.06 * k)], 0.02, metal, gloss=0.9, root=p.body_root, outline=0.004, seg=3)
    p.ball((lx - 0.12, ly - 0.14, lz - 1.8), (0.13, 0.1, 0.1), skin, root=p.body_root)

    # The wind she's calling, curling round her and through the strings.
    gust, gust2 = rgb(226, 250, 240), rgb(170, 232, 214)
    p.sweep([(-2.2, -1.5, -1.7), (-1.1, -1.55, -2.2), (0.3, -1.6, -2.05), (0.95, -1.6, -1.55), (0.6, -1.6, -1.2)], [0.008, 0.05, 0.06, 0.04, 0.006], gust, depth=0.3, root=p.body_root, outline=0.0)
    p.sweep([(-2.1, -0.9, 0.8), (-1.45, -0.95, 0.3), (-1.6, -1.0, -0.15), (-1.95, -1.0, 0.0)], [0.006, 0.035, 0.035, 0.005], gust2, depth=0.3, root=p.body_root, outline=0.0)


def thorne(p):
    """Sorcerer. Says little and gives away less: a gaunt grey face deep in a black hood, purple
    under the robe, and green eyes that are the only warm thing about him, and they aren't warm."""
    skin, shade, blush = rgb(176, 172, 176), rgb(70, 62, 92), rgb(120, 104, 138)
    p.skull()
    p.base_skin(shade, blush)
    # Sunken sockets and hollow cheeks. A faint green glow leaks out of the eyes.
    for sign in (-1, 1):
        p.paint.blob(sign * 0.31, 0.03, 0.27, 0.17, rgb(30, 22, 44), 0.8, soft=0.75)
        p.paint.blob(sign * 0.31, 0.03, 0.2, 0.12, rgb(50, 190, 96), 0.3, soft=0.9)
        p.paint.blob(sign * 0.42, -0.36, 0.13, 0.25, rgb(58, 50, 80), 0.6, soft=0.9)
    green = rgb(90, 255, 130)
    for side in (-1, 1):
        p.eye(side, green, ink=(0.02, 0.01, 0.03), w=0.15, up=0.055, low=0.035, tilt=0.03, gaze=(0.02, 0.0), iris_r=0.06, lash=0.007, lid=0.3, crease=False)
    brow = rgb(22, 18, 28)
    p.brow(-1, brow, inner=0.06, outer=0.14, thick=0.062, arch=0.0, thin_end=False)
    p.brow(1, brow, inner=0.06, outer=0.14, thick=0.062, arch=0.0, thin_end=False)
    # Age and hard years: creases beside the nose and mouth, a line between the brows, a short dark beard.
    for sign in (-1, 1):
        p.paint.line([(sign * 0.13, -0.26), (sign * 0.27, -0.46), (sign * 0.3, -0.72)], [0.003, 0.012, 0.003], shade)
        p.paint.line([(sign * 0.47, -0.02), (sign * 0.58, -0.08)], [0.003, 0.007, 0.002], shade)
        p.paint.line([(sign * 0.04, 0.14), (sign * 0.03, 0.3)], [0.002, 0.008], shade)
    p.paint.blob(0, -0.88, 0.2, 0.24, rgb(24, 20, 30), 0.95, soft=0.3)
    p.paint.line([(-0.2, -0.52), (0, -0.48), (0.2, -0.52)], [0.008, 0.02, 0.008], rgb(24, 20, 30))
    p.nostrils(rgb(38, 30, 50))
    p.nose_line(shade)
    # A flat, closed mouth. He isn't going to explain.
    p.mouth(rgb(34, 26, 44), lip=rgb(92, 76, 104), lip_alpha=0.5, line=0.01)
    p.under_lip(shade)
    p.finish_skull()

    black, deep = rgb(26, 22, 34), rgb(12, 10, 18)
    purple, violet = rgb(94, 42, 152), rgb(58, 26, 100)
    p.neck(deep, width=0.3, depth=0.3)

    # The hood: open only at the face, with its point falling forward to shade the brow.
    def hood(x, y, z):
        return ~((y < -0.1) & (np.abs(x) < 0.6 - 0.24 * np.abs(z + 0.1) ** 2) & (z > -1.25) & (z < 0.42))
    p.cap(black, hood, inflate=0.15)
    p.sweep([(0, 0.0, 0.92), (0, -0.62, 1.04), (0, -1.02, 0.64)], [0.52, 0.36, 0.03], black, depth=0.5)
    # A thin purple lining shows around the edge of the opening.
    for sign in (-1, 1):
        p.sweep([(sign * 0.53, -0.72, 0.48), (sign * 0.68, -0.72, -0.2), (sign * 0.5, -0.66, -0.95), (sign * 0.14, -0.7, -1.32)], [0.03, 0.045, 0.045, 0.02], purple, depth=0.4, seg=8)
        p.sweep([(sign * 0.76, 0.1, 0.5), (sign * 0.9, 0.1, -0.5), (sign * 0.9, 0.1, -1.45)], [0.22, 0.28, 0.46], deep, depth=0.8)

    # A black robe open over purple, and one green stone on a cord.
    coat(p, 1.42, black, deep, purple, gap=0.34, neck=0.46)
    for sign in (-1, 1):
        p.plate([(sign * 0.36, -0.68, -1.3), (sign * 0.46, -0.66, -1.3), (sign * 0.14, -0.86, -2.9), (sign * 0.06, -0.86, -2.9)], 0.03, violet, root=p.body_root)
        p.sweep([(sign * 0.3, -0.62, -1.28), (sign * 0.1, -0.86, -1.95), (0, -0.9, -2.08)], 0.016, deep, root=p.body_root, seg=8)
    p.ball((0, -0.94, -2.16), (0.1, 0.05, 0.14), green, gloss=0.9, root=p.body_root)


def _vial(c):
    rings = []
    for z, r in ((-0.2, 0.05), (-0.16, 0.085), (0.12, 0.085), (0.18, 0.04)):
        rings.append([(c[0] + r * math.cos(a), c[1] + r * math.sin(a), c[2] + z) for a in np.linspace(0, 2 * math.pi, 18, endpoint=False)])
    return rings


# ---- rivals ------------------------------------------------------------------------------------------

def krag(p):
    """Scrap-Winds warlord. All jaw, no neck: the head is a slab of beef set straight into the shoulders.
    Red beard shot through with iron, one eye, gold teeth, and a grin that enjoys the drop."""
    skin, shade, blush = rgb(190, 126, 88), rgb(120, 66, 56), rgb(196, 86, 66)
    p.skull()
    p.base_skin(shade, blush)
    beard = rgb(190, 72, 30)
    p.paint.blob(0, 0.0, 0.8, 0.5, blush, 0.12)
    p.eye(-1, rgb(170, 216, 90), w=0.115, up=0.052, low=0.03, tilt=-0.015, gaze=(-0.024, 0.0), iris_r=0.052, lash=0.018, bags=0.8, skin_shade=shade)
    p.brow(-1, beard, inner=0.05, outer=0.16, thick=0.06, arch=0.0, thin_end=False, length=0.28)
    p.brow(1, beard, inner=0.05, outer=0.18, thick=0.055, arch=0.0, thin_end=False, length=0.26)
    p.nostrils(rgb(60, 26, 26))
    p.nose_line(shade, -1)
    # Scars and pitted skin, plus the deep frown lines between the brows.
    p.paint.line([(-0.06, 0.16), (-0.03, 0.08)], [0.004, 0.009, 0.003], shade)
    p.paint.line([(0.06, 0.16), (0.03, 0.08)], [0.004, 0.009, 0.003], shade)
    p.paint.line([(-0.5, 0.62), (-0.32, 0.48), (-0.34, 0.3)], [0.004, 0.012, 0.004], rgb(228, 174, 146))
    p.paint.line([(-0.2, 0.48), (0.24, 0.44)], 0.004, shade, 0.6)
    p.paint.line([(-0.24, 0.38), (0.22, 0.36)], 0.004, shade, 0.5)
    # Snarl: the open mouth is dark, with gold on the bottom row.
    m = p.s["mouth_z"]
    p.mouth(INK, open_amt=0.17, teeth=True, line=0.013, width=p.s["mouth_w"])
    p.paint.line([(-0.1, m - 0.012), (-0.1, m - 0.075)], 0.004, INK, 0.5)
    p.paint.line([(0.02, m - 0.012), (0.02, m - 0.075)], 0.004, INK, 0.5)
    p.paint.blob(0.13, m - 0.045, 0.05, 0.035, rgb(244, 190, 58), 1.0, soft=0.2)
    p.finish_skull()
    p.neck(skin, width=0.56, depth=0.5, bottom=-1.6)
    p.ear(-1, skin, shade, size=0.85)

    # Bandana, tied hard to the skull and knotted at the side.
    rust = rgb(142, 58, 30)
    p.cap(rust, lambda x, y, z: z > 0.34 + 0.05 * np.abs(x), inflate=0.05)
    p.ball((-0.8, 0.25, 0.5), (0.1, 0.14, 0.13), rgb(104, 40, 22))
    p.sweep([(-0.84, 0.28, 0.5), (-1.14, 0.42, 0.28), (-1.3, 0.5, -0.12)], [0.09, 0.11, 0.01], rust, depth=0.3)
    # The eyepatch: a riveted iron plate, not a bit of cloth.
    iron = rgb(70, 74, 84)
    p.plate([(0.14, -1.0, 0.2), (0.58, -0.82, 0.22), (0.62, -0.72, -0.14), (0.2, -0.96, -0.2)], 0.06, iron, gloss=0.75)
    for x, z in ((0.2, 0.14), (0.54, 0.16), (0.56, -0.1), (0.24, -0.14)):
        p.ball((x, -0.99 + abs(x) * 0.24, z), 0.024, rgb(170, 176, 186), gloss=0.9, outline=0.006)
    p.sweep([(0.6, -0.74, 0.14), (0.86, -0.3, 0.26), (0.86, 0.2, 0.36)], 0.04, rgb(40, 28, 26), depth=0.3)

    # The beard is the character: one great wedge from ear to ear, split at the end, ringed with iron.
    dark = rgb(138, 44, 22)
    rings = []
    for z, f in ((-0.84, 1.05), (-1.1, 1.08), (-1.45, 0.92), (-1.85, 0.62), (-2.2, 0.3)):
        ring = []
        for a in np.linspace(0, 2 * math.pi, 64, endpoint=False):
            ca, sa = math.cos(a), math.sin(a)
            lift = 0.52 * ca * ca * (1 if z > -1.2 else 0.4)
            ring.append((ca * 0.98 * f, -0.48 + sa * 0.5 * f, z + lift))
        rings.append(ring)
    p.loft(_resample(rings, 6), beard, halftone=0.3)
    # Heavy locks over the mass give it weight, and the two tips break its outline.
    for sign in (-1, 1):
        for x, top, tip_x, tip_z, w, color in ((0.86, -0.42, 0.96, -1.5, 0.15, dark), (0.58, -0.92, 0.64, -1.94, 0.15, dark), (0.26, -0.95, 0.34, -2.46, 0.2, beard)):
            p.sweep([(sign * x, -0.84, top), (sign * (x + 0.05), -1.0, (top + tip_z) / 2), (sign * tip_x, -1.0, tip_z)], [w, w, 0.01], color, depth=0.55)
        # Moustache sits above the snarl and drags down outside the mouth, so the teeth stay visible.
        p.sweep([(sign * 0.03, -1.05, -0.43), (sign * 0.3, -1.03, -0.5), (sign * 0.52, -0.94, -0.72), (sign * 0.56, -0.94, -1.02)], [0.04, 0.07, 0.075, 0.015], beard, depth=0.55)
        p.ring((sign * 0.31, -1.0, -2.06), 0.13, 0.04, iron, gloss=0.85, normal=(0, 0, 1))

    # Plates of scrap for shoulders.
    leather = rgb(56, 40, 36)
    shoulders(p, 2.05, leather, neck=0.72, top=-1.18, depth=0.95, slope=0.03)
    for sign in (-1, 1):
        p.ball((sign * 1.62, 0.0, -1.66), (0.62, 0.72, 0.42), rgb(110, 58, 36), root=p.body_root, rot=(0, sign * 0.3, 0))
        for angle, length, x in ((-0.2, 0.75, 1.3), (0.35, 0.92, 1.72), (0.85, 0.72, 2.0)):
            base = np.array((sign * x, -0.05, -1.34 - (x - 1.3) * 0.28))
            tip = base + np.array((sign * math.sin(angle) * length, 0, math.cos(angle) * length))
            p.sweep([base, tip], [0.15, 0.005], rgb(90, 94, 104), gloss=0.8, sides=8, root=p.body_root)
    # Chains across the chest.
    for k in range(13):
        t = k / 12
        x = -1.5 + 3.0 * t
        p.ring((x, -0.98 + 0.25 * abs(x), -1.95 - 0.5 * (1 - (2 * t - 1) ** 2)), 0.1, 0.03, rgb(120, 124, 134), gloss=0.85, normal=(0.7, 0, 0.7) if k % 2 else (-0.7, 0, 0.7), root=p.body_root, outline=0.008)


CAST = {
    # shadow is multiplied into every colour, rim is the edge light, turn>0 looks towards image right.
    "Vane": dict(build=vane, dark=rgb(150, 26, 38), light=rgb(246, 170, 72), shadow=rgb(112, 86, 146), rim=rgb(255, 196, 96), key_side=1,
                 turn=0.3, tilt=-0.07, pitch=-0.03, body_turn=0.12, motif="wind", span=4.1, target=(0, 0, -0.5)),
    "Lyra": dict(build=lyra, dark=rgb(30, 84, 104), light=rgb(176, 226, 212), shadow=rgb(92, 104, 130), rim=rgb(230, 255, 236), key_side=1,
                 turn=0.38, tilt=0.08, pitch=-0.13, body_turn=0.1, motif="cliffwind", span=4.5, target=(0, 0, -0.55)),
    "Thorne": dict(build=thorne, skin=(0.56, 0.54, 0.58), dark=rgb(14, 8, 26), light=rgb(84, 42, 132), shadow=rgb(46, 30, 76), rim=rgb(110, 240, 150), key_side=1,
                   turn=0.16, tilt=0.0, pitch=0.07, body_turn=0.05, motif="sigils", span=4.1, target=(0, 0, -0.45)),
    "Krag": dict(build=krag, dark=rgb(84, 40, 24), light=rgb(216, 144, 60), shadow=rgb(112, 80, 112), rim=rgb(255, 170, 80), key_side=-1,
                 turn=-0.3, tilt=-0.06, pitch=0.06, body_turn=-0.15, motif="rust",
                 span=5.0, target=(0, 0, -0.68),
                 shape=dict(crown=0.74, temple=0.8, cheek=0.92, jaw=0.98, chin=0.6, chin_z=-1.26, depth=1.0, brow_ridge=0.11, socket=0.07,
                            cheekbone=0.03, nose_len=0.4, nose_bridge=0.14, nose_tip=0.21, nose_width=0.18, nose_skew=-0.05,
                            mouth_w=0.32, mouth_z=-0.62, smile=0.1, smirk=-0.06, lip_top=0.03, lip_low=0.03, eye_x=0.36, eye_z=0.05, chin_jut=0.12)),
}
# From the newVane reference: a squarish jaw and solid chin, a long straight nose, a crooked half-smile.
CAST["Vane"]["shape"] = dict(crown=0.7, temple=0.74, cheek=0.76, jaw=0.7, chin=0.42, chin_z=-1.1, depth=0.9, cheekbone=0.06, hollow=0.03,
                             nose_len=0.43, nose_bridge=0.2, nose_tip=0.14, nose_width=0.11, nose_skew=0.0, nose_hook=0.0,
                             mouth_w=0.28, mouth_z=-0.62, smile=0.08, smirk=0.22, eye_x=0.31)
CAST["Lyra"]["shape"] = dict(crown=0.7, temple=0.72, cheek=0.7, jaw=0.58, chin=0.33, chin_z=-1.04, depth=0.86, cheekbone=0.07, hollow=0.02,
                             nose_len=0.37, nose_bridge=0.12, nose_tip=0.12, nose_width=0.09, nose_snub=0.02, brow_ridge=0.02,
                             mouth_w=0.21, mouth_z=-0.58, smile=0.05, lip_top=0.03, lip_low=0.04, eye_x=0.31, forehead=0.05)
CAST["Thorne"]["shape"] = dict(crown=0.76, temple=0.74, cheek=0.66, jaw=0.62, chin=0.38, chin_z=-1.14, top_z=1.06, depth=0.92, forehead=0.05, cheekbone=0.12,
                               nose_len=0.44, nose_bridge=0.17, nose_tip=0.12, nose_width=0.1, nose_hook=0.03, mouth_w=0.22, mouth_z=-0.62, smile=-0.04, lip_top=0.014, lip_low=0.02, eye_x=0.31, brow_ridge=0.05)


# ---- shared wardrobe ---------------------------------------------------------------------------------

def face(p, skin, shade, blush, iris, brow, inner=0.12, outer=0.12, thick=0.03, lip=None, lip_alpha=0.55, gaze=0.035, nose_side=0, **eye):
    """The standard sitting: under-paint, two eyes, brows, nose and mouth. Extras go on before finish_skull."""
    p.skull()
    p.base_skin(shade, blush)
    for side in (-1, 1):
        p.eye(side, iris, gaze=eye.get("gaze_xy", (gaze, 0.0)), **{k: v for k, v in eye.items() if k != "gaze_xy"})
    p.brow(-1, brow, inner=inner, outer=outer, thick=thick)
    p.brow(1, brow, inner=inner, outer=outer, thick=thick)
    p.nostrils(tuple(c * 0.45 for c in shade))
    if nose_side:
        p.nose_line(shade, nose_side)
    p.mouth(INK, lip=lip or tuple(c * 0.85 for c in blush), lip_alpha=lip_alpha)
    p.under_lip(shade)
    return p


def finish(p, skin, shade, neck=0.33, ears=(-1, 1)):
    p.finish_skull()
    for side in ears:
        p.ear(side, skin, shade)
    p.neck(skin, width=neck, depth=neck)
    return p


def hair_cap(p, color, line=0.5, curve=0.12, nape=-0.7, inflate=0.05, side=0.0):
    p.cap(color, lambda x, y, z: (z > line - curve * x * x + side * x) | ((y > 0.15) & (z > nape)), inflate=inflate)
    return p


def coat(p, width, color, lapel, shirt=None, gap=0.3, neck=0.42, slope=0.0, gloss=0.0, depth=0.74):
    """Shoulders, a shirt panel and lapels: most of the costume in this cast."""
    shoulders(p, width, color, neck=neck, slope=slope, gloss=gloss, depth=depth)
    if shirt:
        p.plate([(-gap, -0.6, -1.3), (gap, -0.6, -1.3), (gap * 0.25, -0.83, -2.9), (-gap * 0.25, -0.83, -2.9)], 0.04, shirt, root=p.body_root)
    for sign in (-1, 1):
        p.plate([(sign * gap, -0.56, -1.22), (sign * (gap + 0.42), -0.48, -1.22), (sign * (gap + 0.5), -0.64, -1.82), (sign * gap * 0.25, -0.86, -2.6)], 0.06, lapel, root=p.body_root)
    return p


def epaulettes(p, width, gold):
    for sign in (-1, 1):
        p.ball((sign * width * 0.8, -0.05, -1.62), (0.4, 0.42, 0.1), gold, gloss=0.8, root=p.body_root, rot=(0, sign * 0.25, 0))
        for k in range(7):
            x = sign * width * (0.58 + 0.07 * k)
            p.sweep([(x, -0.32, -1.68 - 0.02 * k), (x + sign * 0.02, -0.38, -1.95)], [0.035, 0.025], gold, gloss=0.8, root=p.body_root, outline=0.007)
    return p


def _ellipse(rx, ry, z, cy=0.03, n=64, wobble=None):
    out = []
    for a in np.linspace(0, 2 * math.pi, n, endpoint=False):
        out.append((rx * math.cos(a), cy + ry * math.sin(a), z + (wobble(a) if wobble else 0.0)))
    return out


def tricorn(p, color, trim):
    def brim_r(a):
        return 1.2 + 0.3 * math.cos(3 * (a + math.pi / 2))
    rings = [_ellipse(0.8, 0.96, z) for z in (0.42, 0.9)] + [_ellipse(0.66, 0.82, 1.18), _ellipse(0.25, 0.3, 1.26)]
    p.loft(_resample(rings, 4), color)
    brim = []
    for f, base, up in ((0.62, 0.44, 0.0), (0.82, 0.44, 0.12), (1.0, 0.44, 0.62)):
        ring = []
        for a in np.linspace(0, 2 * math.pi, 96, endpoint=False):
            r = 0.8 + (brim_r(a) - 0.8) * (f - 0.62) / 0.38 if f > 0.62 else 0.78
            corner = 0.5 + 0.5 * math.cos(3 * (a + math.pi / 2))
            ring.append((r * math.cos(a), 0.03 + r * 1.08 * math.sin(a), base + up * (1 - corner * 0.8)))
        brim.append(ring)
    p.loft(brim, color, cap=False)
    edge = np.array(brim[-1])
    p.sweep(np.vstack([edge, edge[:1]]), 0.025, trim, gloss=0.85, seg=1, sides=6, outline=0.005)
    return p


def bicorne(p, color, trim, plume=None):
    for y, peak in ((-0.3, 1.5), (0.22, 1.42)):
        outline = [(x, y - 0.02 * abs(x), 0.62 + (peak - 0.62) * (1 - (abs(x) / 1.75) ** 1.7)) for x in np.linspace(-1.75, 1.75, 40)]
        bottom = [(x, y, 0.5 + 0.28 * (abs(x) / 1.75) ** 3) for x in np.linspace(1.75, -1.75, 40)]
        p.plate(outline + bottom, 0.12, color)
        p.sweep(outline, 0.028, trim, gloss=0.85, seg=2, sides=6, outline=0.005)
    p.ball((0.0, -0.42, 0.98), (0.17, 0.05, 0.17), trim, gloss=0.85)
    p.ball((0.0, -0.46, 0.98), (0.08, 0.04, 0.08), rgb(196, 36, 60), gloss=0.5)
    if plume:
        p.sweep([(0.0, -0.3, 1.1), (0.03, -0.25, 1.65), (-0.1, -0.1, 2.0)], [0.09, 0.1, 0.005], plume)
    return p


def peaked_cap(p, color, band, visor=rgb(22, 20, 30), badge=None):
    rings = [_ellipse(0.82, 0.98, 0.5), _ellipse(0.84, 1.0, 0.66), _ellipse(1.04, 1.16, 0.96, cy=-0.04), _ellipse(0.98, 1.1, 1.08, cy=-0.04), _ellipse(0.4, 0.45, 1.12, cy=-0.04)]
    p.loft(_resample(rings, 3), color)
    p.loft([_ellipse(0.85, 1.01, 0.5), _ellipse(0.86, 1.02, 0.64)], band, gloss=0.8, cap=False)
    p.plate([(-0.66, -0.8, 0.5), (0.66, -0.8, 0.5), (0.5, -1.32, 0.38), (-0.5, -1.32, 0.38)], 0.04, visor, gloss=0.8)
    if badge:
        p.plate([(-0.14, -1.08, 0.74), (0.14, -1.08, 0.74), (0.17, -1.04, 1.0), (0, -1.08, 1.12), (-0.17, -1.04, 1.0)], 0.04, badge, gloss=0.9)
    return p


def wide_hat(p, color, band, r=1.5, sag=0.2):
    rings = [_ellipse(0.82, 0.96, 0.46), _ellipse(0.76, 0.9, 0.9), _ellipse(0.6, 0.72, 1.3), _ellipse(0.2, 0.25, 1.38)]
    p.loft(_resample(rings, 4), color)
    brim = [_ellipse(0.8, 0.95, 0.46), _ellipse(r * 0.8, r * 0.85, 0.46, wobble=lambda a: -sag * 0.4 * math.cos(a) ** 2), _ellipse(r, r, 0.42, wobble=lambda a: -sag * math.cos(a) ** 2 + 0.1 * math.sin(a))]
    p.loft(brim, color)
    p.loft([_ellipse(0.84, 0.97, 0.5), _ellipse(0.82, 0.95, 0.68)], band, cap=False)
    return p


def _motif_coat_buttons(p, x, gold, count=4, top=-1.75):
    for k in range(count):
        p.ball((x, -0.86, top - k * 0.28), (0.05, 0.03, 0.05), gold, gloss=0.9, root=p.body_root, outline=0.006)


# ---- crew, continued ---------------------------------------------------------------------------------

def rook(p):
    """Disgraced Armada cannoneer, built like the guns he hauls. A flat, unimpressed stare and a heavy moustache,
    half the face tattooed by powder burns, on a neck as wide as his head and shoulders that fill the frame."""
    skin, shade, blush = rgb(120, 76, 54), rgb(66, 36, 42), rgb(136, 68, 50)
    black = rgb(30, 26, 30)
    face(p, skin, shade, blush, rgb(150, 208, 240), black, inner=0.075, outer=0.1, thick=0.042, lid=0.36, up=0.078, low=0.034, gaze=0.03, bags=0.8, skin_shade=shade, nose_side=-1)
    rng = np.random.default_rng(5)
    for x, z in rng.uniform((0.28, -0.42), (0.78, 0.34), (70, 2)):
        p.paint.blob(x, z, 0.012, 0.012, rgb(26, 18, 24), 0.85, soft=0.3)
    p.paint.line([(0.38, 0.34), (0.47, 0.17), (0.43, -0.04)], [0.004, 0.015, 0.004], rgb(178, 132, 110))
    for sign in (-1, 1):
        p.paint.line([(sign * 0.24, -0.32), (sign * 0.34, -0.48), (sign * 0.36, -0.62)], [0.003, 0.008, 0.002], shade)
    finish(p, skin, shade, neck=0.66, ears=())
    # Close-cropped hair, and goggles pushed up with one lens cracked.
    hair_cap(p, black, line=0.52, curve=0.1, nape=-0.45, inflate=0.025)
    goggles(p, z=0.72, y=-0.82, spread=0.3, r=0.2, lens=rgb(236, 158, 70), strap=rgb(60, 46, 40))
    # Moustache: broad, combed flat, military. The one bit of regulation left.
    for sign in (-1, 1):
        p.sweep([(sign * 0.02, -1.03, -0.45), (sign * 0.22, -1.0, -0.5), (sign * 0.42, -0.9, -0.68)], [0.055, 0.085, 0.01], black, depth=0.6)
    # Copper ear guards, from a life beside guns.
    for sign in (-1, 1):
        p.ball((sign * 0.78, 0.08, -0.05), (0.08, 0.2, 0.25), rgb(178, 106, 58), gloss=0.8)
    coat(p, 1.5, rgb(42, 58, 100), rgb(30, 40, 74), rgb(170, 154, 126), gap=0.42, neck=0.66, depth=0.95)
    canvas_shade = rgb(120, 104, 88)
    for sign in (-1, 1):
        # Traps climbing to the ears, then bare shoulders and arms bursting out of a sleeveless coat.
        p.sweep([(sign * 0.45, -0.1, -0.85), (sign * 0.85, -0.1, -1.28), (sign * 1.45, -0.1, -1.62)], [0.22, 0.34, 0.3], skin, depth=0.9, root=p.body_root)
        p.ball((sign * 1.92, -0.1, -1.95), (0.68, 0.7, 0.62), skin, root=p.body_root)
        p.ball((sign * 2.1, -0.45, -2.85), (0.62, 0.55, 0.72), skin, root=p.body_root)
        # The crease between shoulder and arm, and the pec line under the shirt.
        p.sweep([(sign * 1.42, -0.72, -1.72), (sign * 1.56, -0.86, -2.3), (sign * 1.72, -0.84, -2.7)], [0.012, 0.028, 0.012], shade, depth=0.3, root=p.body_root, outline=0.0)
        p.sweep([(sign * 0.04, -1.0, -2.22), (sign * 0.3, -1.0, -2.5), (sign * 0.72, -0.96, -2.36)], [0.008, 0.024, 0.008], canvas_shade, depth=0.3, root=p.body_root, outline=0.0)
    # The torn shoulder: rank ripped off, thread still hanging.
    for k, x in enumerate(np.linspace(-1.42, -0.96, 6)):
        p.sweep([(x, -0.5, -1.62), (x + 0.03, -0.62, -1.82 - 0.1 * (k % 2))], 0.018, rgb(226, 186, 90), root=p.body_root, outline=0.005)
    p.sweep([(1.25, -0.72, -1.6), (0.35, -1.02, -2.05), (-0.7, -0.98, -2.7)], 0.12, rgb(70, 46, 34), depth=0.3, root=p.body_root)
    for k in np.linspace(0.08, 0.95, 7):
        p.ball((1.25 - 1.95 * k, -1.08 + 0.1 * abs(k - 0.5), -1.6 - 1.1 * k + 0.05), (0.05, 0.035, 0.1), rgb(150, 156, 166), gloss=0.9, root=p.body_root, outline=0.008)

    # Cinder, his robot hound, at his shoulder: one ember eye and a fire cannon for a mouth, lit and ready.
    steel, dark, brass, ember = rgb(112, 118, 128), rgb(60, 64, 72), rgb(214, 164, 62), rgb(255, 120, 36)
    hx, hy, hz = 1.2, -1.75, -1.86
    p.ball((hx, hy, hz), (0.58, 0.5, 0.48), steel, gloss=0.5, root=p.body_root)  # Skull.
    p.sweep([(hx - 0.42, hy - 0.05, hz + 0.3), (hx - 0.62, hy + 0.05, hz + 0.86)], [0.2, 0.03], dark, depth=0.3, root=p.body_root)  # Ears.
    p.sweep([(hx + 0.42, hy - 0.05, hz + 0.3), (hx + 0.62, hy + 0.05, hz + 0.86)], [0.2, 0.03], dark, depth=0.3, root=p.body_root)
    for sign, y in ((-1, -0.42), (1, -0.42)):
        p.ball((hx + sign * 0.24, hy + y, hz + 0.16), (0.09, 0.05, 0.08), ember, root=p.body_root, outline=0.006)  # Eyes.
    # Sharp steel jaws around the barrel, top and bottom, with fangs.
    silver = rgb(206, 212, 220)
    p.plate([(hx + 0.34, hy - 0.42, hz - 0.08), (hx - 0.3, hy - 0.6, hz - 0.02), (hx - 0.56, hy - 0.86, hz - 0.08), (hx - 0.1, hy - 0.72, hz - 0.2)], 0.05, silver, gloss=0.8, root=p.body_root)
    p.plate([(hx + 0.3, hy - 0.42, hz - 0.46), (hx - 0.2, hy - 0.62, hz - 0.54), (hx - 0.52, hy - 0.86, hz - 0.5), (hx - 0.06, hy - 0.72, hz - 0.4)], 0.05, silver, gloss=0.8, root=p.body_root)
    for k, u in enumerate((0.0, 0.2, 0.4)):
        x, y = hx - 0.06 - u, hy - 0.68 - u * 0.4
        p.plate([(x - 0.045, y, hz - 0.1), (x + 0.045, y, hz - 0.12), (x, y, hz - 0.28)], 0.02, rgb(240, 242, 246), root=p.body_root)
        p.plate([(x - 0.04, y, hz - 0.47), (x + 0.04, y, hz - 0.48), (x, y, hz - 0.34)], 0.02, rgb(240, 242, 246), root=p.body_root)
    # The muzzle is a brass cannon barrel, with flame coming out of it.
    p.sweep([(hx - 0.02, hy - 0.4, hz - 0.2), (hx - 0.3, hy - 0.72, hz - 0.3)], [0.27, 0.22], dark, root=p.body_root)
    p.ring((hx - 0.32, hy - 0.76, hz - 0.31), 0.21, 0.05, brass, gloss=0.9, normal=(-0.5, -1, 0), root=p.body_root)
    p.disc((hx - 0.33, hy - 0.77, hz - 0.31), 0.17, rgb(30, 18, 16), normal=(-0.5, -1, 0), root=p.body_root)
    p.sweep([(hx - 0.34, hy - 0.8, hz - 0.31), (hx - 0.72, hy - 0.92, hz - 0.14), (hx - 1.15, hy - 0.98, hz - 0.3), (hx - 1.62, hy - 1.0, hz - 0.05)], [0.16, 0.25, 0.16, 0.01], ember, depth=0.4, root=p.body_root, outline=0.008)
    p.sweep([(hx - 0.36, hy - 0.98, hz - 0.31), (hx - 0.78, hy - 1.1, hz - 0.2), (hx - 1.15, hy - 1.16, hz - 0.27)], [0.07, 0.11, 0.01], rgb(255, 224, 110), depth=0.3, root=p.body_root, outline=0.0)


def sable(p):
    """Assassin, crouched in the moonlit rigging. Lean and angular, pale weathered skin, light eyes in heavy black
    kohl, a jagged crimson scar on her left cheekbone, and a cold unblinking stare. Salt-matted hair and thin
    beaded braids escape a frayed grey cowl worn over a black bandana. A dark grey double-breasted coat with
    pewter buttons, brown leather bandoliers and a bone-handled dagger across her chest. A blood-tipped
    stiletto in one hand, a venom-soaked rag and an uncorked bottle of glowing green poison in the other, and
    a steel-bracketed recurve bow and green-fletched arrows on her back."""
    skin, shade, blush = rgb(214, 204, 198), rgb(150, 136, 140), rgb(196, 168, 168)
    kohl, hair, scar = rgb(14, 10, 16), rgb(30, 26, 32), rgb(176, 28, 40)
    grey, grey2, vest = rgb(70, 72, 80), rgb(46, 48, 56), rgb(26, 24, 30)
    leather, pewter, bone, steel = rgb(100, 66, 42), rgb(150, 154, 160), rgb(226, 216, 190), rgb(176, 186, 200)
    poison, glow = rgb(96, 230, 90), rgb(190, 255, 150)

    # Bow and quiver behind her shoulders, drawn first.
    wood = rgb(120, 84, 54)
    p.sweep([(-1.5, 0.45, 1.3), (-1.78, 0.45, 1.0), (-2.05, 0.45, 0.2), (-2.05, 0.45, -0.9), (-1.6, 0.45, -2.2), (-1.36, 0.45, -2.45)], [0.025, 0.06, 0.08, 0.08, 0.06, 0.025], wood, depth=0.6)
    p.sweep([(-1.5, 0.42, 1.3), (-1.36, 0.42, -2.45)], 0.012, rgb(196, 190, 172), outline=0.0, seg=4)
    for z in (0.6, -0.4):
        p.sweep([(-2.08, 0.4, z), (-2.08, 0.4, z - 0.16)], 0.1, steel, gloss=0.9, depth=0.3, outline=0.005, seg=3)
    p.sweep([(-1.66, 0.4, 1.12), (-1.62, 0.4, 0.98), (-1.6, 0.4, 0.9)], [0.015, 0.04, 0.01], poison, outline=0.004)
    p.sweep([(0.92, 0.4, -1.5), (1.14, 0.4, -0.15)], [0.17, 0.2], leather, depth=0.7)
    for dx, h in ((0.0, 0.5), (0.11, 0.4), (-0.1, 0.34)):
        x0, z0 = 1.14 + dx, -0.15
        p.sweep([(x0, 0.38, z0), (x0 + 0.04, 0.38, z0 + h)], 0.016, rgb(150, 132, 108), outline=0.005, seg=4)
        p.plate([(x0 + 0.02, 0.36, z0 + h - 0.18), (x0 + 0.1, 0.36, z0 + h - 0.24), (x0 + 0.06, 0.36, z0 + h)], 0.01, poison, outline=0.004)

    p.skull()
    p.base_skin(shade, blush)
    # Heavy kohl round light eyes, and a cold, level stare.
    for sign in (-1, 1):
        p.paint.blob(sign * 0.31, 0.02, 0.22, 0.12, kohl, 0.85, soft=0.35)
    iris = rgb(196, 224, 232)
    p.eye(-1, iris, up=0.08, low=0.04, tilt=0.08, gaze=(0.0, 0.0), lash=0.03, lid=0.18, iris_r=0.062)
    p.eye(1, iris, up=0.08, low=0.04, tilt=0.08, gaze=(0.0, 0.0), lash=0.03, lid=0.18, iris_r=0.062)
    p.brow(-1, hair, inner=0.06, outer=0.15, thick=0.026, arch=0.02)
    p.brow(1, hair, inner=0.06, outer=0.15, thick=0.026, arch=0.02)
    p.nostrils(rgb(110, 90, 96))
    p.mouth(INK, lip=rgb(150, 110, 118), lip_alpha=0.6, line=0.009)
    p.under_lip(shade)
    for sign in (-1, 1):
        p.paint.line([(sign * 0.36, -0.32), (sign * 0.48, -0.5)], [0.003, 0.008], shade)
    # A jagged crimson scar across her left cheekbone.
    p.paint.line([(0.3, -0.06), (0.4, -0.16), (0.36, -0.22), (0.5, -0.36)], [0.006, 0.014, 0.012, 0.004], scar)
    p.finish_skull()
    p.ear(-1, skin, shade)
    p.neck(skin, width=0.27, depth=0.27)
    # A tight black bandana, then the cowl over it: frayed dark grey, pulled low.
    p.cap(vest, lambda x, y, z: (z > 0.42 - 0.2 * x * x) & (y < 0.2), inflate=0.05)
    def hood(x, y, z):
        return ~((y < -0.1) & (np.abs(x) < 0.66 - 0.24 * np.abs(z + 0.1) ** 2) & (z > -1.2) & (z < 0.52))
    p.cap(grey2, hood, inflate=0.15)
    p.sweep([(0, 0.0, 0.92), (0, -0.62, 1.04), (0, -1.06, 0.68)], [0.5, 0.34, 0.03], grey2, depth=0.5)
    for x, z in ((-0.7, 0.3), (0.74, -0.1), (-0.62, -0.6), (0.2, 0.98)):
        p.ball((x, -0.6, z), (0.04, 0.02, 0.035), rgb(16, 16, 22), outline=0.0)
    for sign in (-1, 1):
        p.sweep([(sign * 0.7, -0.6, 0.52), (sign * 0.8, -0.56, -0.4), (sign * 0.64, -0.54, -1.25)], [0.02, 0.05, 0.02], rgb(60, 62, 70), depth=0.4, seg=8)
        # Salt-matted strands and thin beaded braids along her jaw.
        p.sweep([(sign * 0.6, -0.66, 0.4), (sign * 0.68, -0.72, -0.2), (sign * 0.6, -0.74, -0.8)], [0.035, 0.05, 0.01], hair, depth=0.5)
        p.sweep([(sign * 0.58, -0.74, -0.25), (sign * 0.6, -0.78, -0.7), (sign * 0.55, -0.8, -1.05)], 0.022, hair, outline=0.006, seg=6)
        for bz in (-0.75, -0.98):
            p.ball((sign * 0.58, -0.82, bz), (0.035, 0.03, 0.04), bone if bz < -0.9 else pewter, gloss=0.6, outline=0.005)

    # Dark grey double-breasted coat with dull pewter buttons, over a dark vest.
    coat(p, 1.3, grey, grey2, vest, gap=0.24, neck=0.42, depth=0.72)
    for sign in (-1, 1):
        for k in range(3):
            p.ball((sign * 0.4, -0.86, -1.85 - k * 0.3), (0.045, 0.025, 0.045), pewter, gloss=0.6, root=p.body_root, outline=0.005)
    # Brown bandoliers across her chest, and a bone-handled dagger sheathed diagonally across them.
    p.sweep([(1.08, -0.62, -1.6), (0.2, -0.88, -2.05), (-0.75, -0.8, -2.75)], 0.11, leather, depth=0.3, root=p.body_root)
    p.sweep([(-1.02, -0.6, -1.66), (-0.1, -0.9, -2.2), (0.8, -0.82, -2.85)], 0.09, rgb(82, 54, 36), depth=0.3, root=p.body_root)
    p.sweep([(-0.75, -0.92, -1.95), (0.25, -0.98, -2.55)], [0.07, 0.05], rgb(40, 32, 30), depth=0.4, root=p.body_root)
    p.sweep([(-0.98, -0.9, -1.8), (-0.75, -0.94, -1.95)], 0.065, bone, root=p.body_root)
    p.sweep([(-0.82, -0.95, -1.8), (-0.68, -0.97, -2.08)], 0.04, steel, gloss=0.9, root=p.body_root)

    # A blood-tipped stiletto held up in her left hand.
    sx, sy = 1.55, -1.15
    p.plate([(sx - 0.04, sy, -1.38), (sx + 0.04, sy, -1.38), (sx, sy, 0.02)], 0.016, steel, gloss=1.0, root=p.body_root)
    p.plate([(sx - 0.014, sy - 0.012, -0.22), (sx + 0.014, sy - 0.012, -0.22), (sx, sy - 0.012, 0.02)], 0.01, scar, root=p.body_root, outline=0.0)
    p.sweep([(sx - 0.2, sy, -1.4), (sx + 0.2, sy, -1.4)], 0.04, pewter, gloss=0.8, root=p.body_root)
    p.sweep([(sx, sy, -1.42), (sx, sy, -1.9)], 0.06, rgb(40, 30, 28), root=p.body_root)
    p.ball((sx, sy - 0.03, -1.82), (0.15, 0.11, 0.14), rgb(36, 34, 40), root=p.body_root)
    for k in range(3):
        p.ball((sx - 0.1, sy - 0.12, -1.74 - 0.07 * k), (0.045, 0.04, 0.035), skin, root=p.body_root, outline=0.004)
    # In the other hand, a rag drawing glowing green poison from an uncorked bottle.
    bx, by = -1.28, -1.5
    p.ball((bx, by, -2.35), (0.24, 0.18, 0.3), rgb(70, 190, 86), gloss=0.9, root=p.body_root)
    p.ball((bx - 0.06, by - 0.12, -2.25), (0.05, 0.02, 0.09), glow, root=p.body_root, outline=0.0)
    p.sweep([(bx, by, -2.06), (bx, by, -1.86)], 0.07, rgb(46, 110, 62), gloss=0.7, root=p.body_root)
    p.sweep([(bx, by - 0.05, -1.84), (bx + 0.14, by - 0.12, -1.62), (bx + 0.2, by - 0.1, -1.38)], [0.06, 0.09, 0.05], rgb(150, 160, 120), depth=0.4, root=p.body_root)
    p.sweep([(bx + 0.05, by - 0.14, -1.7), (bx + 0.1, by - 0.16, -1.48)], [0.03, 0.01], glow, depth=0.3, root=p.body_root, outline=0.0)
    p.ball((bx + 0.24, by - 0.08, -1.32), (0.14, 0.1, 0.12), rgb(36, 34, 40), root=p.body_root)
    for k in range(3):
        p.ball((bx + 0.16 + 0.06 * k, by - 0.17, -1.38), (0.035, 0.04, 0.045), skin, root=p.body_root, outline=0.004)


def morrow(p):
    """The navigator who sold you out. Immaculate, and the only clean thing on any ship: emerald velvet, gold
    filigree, white lace and a black tricorn. Dark lenses in brass cages hide his eyes completely, so all you
    get is a square jaw and a tight smirk that's warm on the surface and calculating underneath."""
    skin, shade, blush = rgb(214, 170, 130), rgb(132, 92, 90), rgb(198, 128, 104)
    hair = rgb(44, 30, 26)
    # The eyes are drawn, but only the lenses over them are ever seen.
    face(p, skin, shade, blush, rgb(120, 170, 90), hair, inner=0.13, outer=0.11, thick=0.03, up=0.06, low=0.03, gaze=0.04, lid=0.2)
    rng = np.random.default_rng(11)
    for x, z in rng.uniform((-0.5, -1.02), (0.5, -0.66), (150, 2)):
        if abs(x) < 0.26 and -0.8 < z:
            continue
        p.paint.blob(x, z, 0.008, 0.008, rgb(92, 68, 62), 0.5, soft=0.3)
    finish(p, skin, shade, neck=0.3)
    p.cap(hair, lambda x, y, z: (z > 0.34) | ((y > 0.1) & (z > -0.75)), inflate=0.04, gloss=0.4)

    # Brass-framed spectacles: thick, dark, round lenses with caged sides.
    brass, dark = rgb(214, 170, 72), rgb(18, 20, 26)
    for sign, x in ((-1, -0.31), (1, 0.31)):
        p.disc((x, -1.02, 0.03), 0.2, dark, gloss=0.9)
        p.ring((x, -1.03, 0.03), 0.2, 0.036, brass, gloss=0.9)
        p.sweep([(x - 0.1, -1.05, 0.0), (x - 0.02, -1.055, 0.13)], 0.012, rgb(110, 124, 130), depth=0.2, outline=0.0)
        for z in (-0.1, 0.03, 0.16):
            p.sweep([(sign * 0.5, -0.98, z), (sign * 0.72, -0.62, z)], 0.014, brass, gloss=0.8, outline=0.004, seg=4)
        p.sweep([(sign * 0.72, -0.62, 0.2), (sign * 0.72, -0.62, -0.14)], 0.016, brass, gloss=0.8, outline=0.004, seg=4)
        p.sweep([(sign * 0.72, -0.62, 0.05), (sign * 0.8, -0.2, 0.06), (sign * 0.8, 0.1, 0.02)], 0.016, brass, gloss=0.8)
    p.sweep([(-0.115, -1.03, 0.05), (0, -1.07, 0.09), (0.115, -1.03, 0.05)], 0.02, brass, gloss=0.9)

    tricorn(p, rgb(20, 18, 22), rgb(226, 178, 66))

    # Emerald velvet over a gold brocade waistcoat, wide lapels edged in filigree.
    velvet, velvet2, gold, lace = rgb(18, 118, 80), rgb(10, 76, 54), rgb(232, 184, 70), rgb(244, 242, 234)
    coat(p, 1.34, velvet, velvet2, rgb(176, 130, 50), gap=0.3, neck=0.38)
    for sign in (-1, 1):
        p.sweep([(sign * 0.31, -0.62, -1.24), (sign * 0.8, -0.56, -1.3), (sign * 0.86, -0.68, -1.86), (sign * 0.28, -0.84, -2.5)], 0.016, gold, gloss=0.8, root=p.body_root, outline=0.004)
        p.sweep([(sign * 0.55, -0.68, -1.5), (sign * 0.68, -0.7, -1.56), (sign * 0.62, -0.74, -1.72), (sign * 0.5, -0.76, -1.66)], 0.008, gold, root=p.body_root, outline=0.0)
        p.sweep([(sign * 0.5, -0.76, -1.92), (sign * 0.62, -0.76, -1.98), (sign * 0.56, -0.8, -2.14), (sign * 0.46, -0.8, -2.08)], 0.008, gold, root=p.body_root, outline=0.0)
        for k in range(3):
            p.ball((sign * 0.46, -0.9, -2.2 - k * 0.3), (0.05, 0.03, 0.05), gold, gloss=0.9, root=p.body_root, outline=0.006)
    # A white silk cravat with lace edging, tied neatly at the throat.
    p.sweep([(-0.26, -0.72, -1.3), (0, -0.84, -1.42), (0.26, -0.72, -1.3)], 0.11, lace, root=p.body_root)
    p.plate([(-0.17, -0.86, -1.46), (0.17, -0.86, -1.46), (0.25, -0.88, -2.06), (0, -0.92, -2.2), (-0.25, -0.88, -2.06)], 0.03, lace, root=p.body_root)
    p.ball((0, -0.94, -1.46), (0.1, 0.06, 0.085), lace, root=p.body_root)
    for x in np.linspace(-0.22, 0.22, 7):
        p.ball((x, -0.93, -2.1 - 0.1 * (1 - abs(x) / 0.25)), (0.038, 0.016, 0.034), lace, root=p.body_root, outline=0.004)


def _cassian_face(p, warm):
    skin, shade, blush = rgb(226, 178, 142), rgb(140, 100, 104), rgb(208, 118, 96)
    silver = rgb(214, 216, 222)
    face(p, skin, shade, blush, rgb(70, 142, 212), silver,
         inner=0.14 if warm else 0.07, outer=0.15 if warm else 0.17, thick=0.042,
         up=0.075 if warm else 0.056, low=0.036 if warm else 0.028, lid=0.08 if warm else 0.32,
         tilt=0.004 if warm else 0.02, gaze=-0.035, bags=0.6, skin_shade=shade, nose_side=1)
    # The same scar in both portraits, which is how you know it's the same man.
    p.paint.line([(-0.5, 0.42), (-0.4, 0.16), (-0.33, -0.08), (-0.36, -0.34)], [0.004, 0.015, 0.012, 0.003], rgb(158, 56, 58))
    for sign in (-1, 1):
        p.paint.line([(sign * 0.54, 0.02), (sign * 0.66, -0.02)], [0.002, 0.005, 0.001], shade)
        p.paint.line([(sign * 0.54, -0.05), (sign * 0.65, -0.1)], [0.002, 0.005, 0.001], shade)
    if not warm:
        p.paint.line([(-0.2, 0.46), (0.2, 0.46)], 0.003, shade, 0.5)
    finish(p, skin, shade, neck=0.38)
    hair_cap(p, silver, line=0.5, curve=0.2, nape=-0.55, inflate=0.04)
    return silver


def _beard(p, color, dark, length, width=0.72):
    rings = []
    for z, f in ((-0.8, 1.02), (-1.05, 1.04), (-1.05 - length * 0.5, 0.74), (-1.05 - length, 0.3)):
        ring = []
        for a in np.linspace(0, 2 * math.pi, 56, endpoint=False):
            ca, sa = math.cos(a), math.sin(a)
            ring.append((ca * width * f, -0.48 + sa * 0.5 * f, z + 0.42 * ca * ca * (1 if z > -1.1 else 0.3)))
        rings.append(ring)
    p.loft(_resample(rings, 6), color, halftone=0.3)
    for sign in (-1, 1):
        p.sweep([(sign * 0.3, -0.96, -0.82), (sign * 0.35, -1.0, -1.05 - length * 0.4), (sign * 0.14, -0.96, -1.05 - length * 0.95)], [0.09, 0.09, 0.01], dark, depth=0.5)
        p.sweep([(sign * 0.03, -1.03, -0.44), (sign * 0.22, -1.0, -0.49), (sign * 0.42, -0.9, -0.72)], [0.04, 0.07, 0.01], color, depth=0.6)


def cassian_pirate(p):
    """The father-figure, in his glory. Red coat and silver beard and a grin you'd follow off a cliff."""
    p.s["smile"] = 0.15
    silver = _cassian_face(p, True)
    _beard(p, silver, rgb(170, 172, 182), 0.42)
    p.ball((-0.84, -0.1, -0.32), 0.05, rgb(244, 190, 58), gloss=0.9)
    tricorn(p, rgb(96, 28, 36), rgb(232, 186, 76))
    p.sweep([(0.72, -0.35, 1.02), (1.02, -0.05, 1.55), (1.6, 0.25, 1.82)], [0.12, 0.15, 0.005], rgb(238, 238, 232))
    coat(p, 1.72, rgb(176, 34, 44), rgb(128, 22, 36), rgb(236, 228, 208), gap=0.32, neck=0.46)
    epaulettes(p, 1.72, rgb(240, 192, 80))
    _motif_coat_buttons(p, 0.44, rgb(240, 192, 80))


def cassian_admiral(p):
    """The same man after the betrayal. Same scar, same beard cut short: the warmth has been removed and
    replaced with medals. Set beside his pirate portrait, the difference is the whole plot."""
    p.s["smile"] = -0.03
    silver = _cassian_face(p, False)
    _beard(p, silver, rgb(170, 172, 182), 0.18, width=0.68)
    bicorne(p, rgb(26, 34, 76), rgb(240, 196, 84))
    coat(p, 1.72, rgb(230, 230, 234), rgb(28, 38, 84), rgb(26, 34, 76), gap=0.28, neck=0.5)
    # High gold collar, right up under the beard: he is now held in place by his own uniform.
    for sign in (-1, 1):
        p.plate([(sign * 0.08, -0.72, -1.28), (sign * 0.64, -0.36, -1.16), (sign * 0.68, -0.4, -1.58), (sign * 0.1, -0.76, -1.66)], 0.06, rgb(240, 196, 84), gloss=0.8, root=p.body_root)
    epaulettes(p, 1.72, rgb(240, 196, 84))
    for k, c in enumerate((rgb(196, 36, 60), rgb(48, 96, 196), rgb(236, 196, 80), rgb(40, 150, 120))):
        x = -1.0 + k * 0.17
        p.plate([(x, -0.84, -2.0), (x + 0.14, -0.84, -2.0), (x + 0.14, -0.84, -2.25), (x, -0.84, -2.25)], 0.03, c, gloss=0.5, root=p.body_root, outline=0.006)
    for x in (-0.85, -0.5):
        p.ball((x, -0.88, -2.4), 0.08, rgb(240, 196, 84), gloss=0.9, root=p.body_root, outline=0.006)


def _twin(p, mirror, hair, accent, deep, iris, sneer):
    """Vex and Vesper, drawn from one set of bones and mirrored, with their temperament the only difference."""
    skin, shade, blush = rgb(232, 196, 172), rgb(138, 100, 132), rgb(214, 128, 132)
    p.s["smirk"] = 0.2 * mirror if sneer else 0.0
    p.s["smile"] = 0.08 if sneer else -0.01
    face(p, skin, shade, blush, iris, tuple(c * 0.7 for c in hair), inner=0.075, outer=0.17, thick=0.024, lid=0.1 if sneer else 0.42, tilt=0.03, up=0.075, low=0.032, gaze=-0.045, lash=0.022, lip=tuple(c * 0.6 for c in accent), lip_alpha=0.8)
    # A sliver mark under one eye, on opposite sides: each one's the other's reflection.
    p.paint.line([(mirror * -0.3, -0.13), (mirror * -0.36, -0.28)], [0.012, 0.002], accent)
    p.paint.line([(mirror * -0.22, -0.13), (mirror * -0.27, -0.23)], [0.01, 0.002], accent)
    finish(p, skin, shade, neck=0.28)
    # Shaved on one side, a long blade of hair on the other.
    p.cap(hair, lambda x, y, z: ((x * mirror > -0.12) & (z > 0.34)) | ((y > 0.05) & (z > 0.1) & (x * mirror > -0.2)), inflate=0.05, gloss=0.3)
    p.cap(tuple(c * 0.68 + 0.08 for c in hair), lambda x, y, z: (x * mirror <= -0.08) & (z > 0.52 - 0.15 * x * x), inflate=0.012)
    m = mirror
    p.sweep([(m * 0.05, -0.8, 0.82), (m * 0.68, -0.72, 0.56), (m * 0.98, -0.55, -0.15), (m * 1.02, -0.62, -0.95), (m * 0.9, -0.75, -1.5)], [0.2, 0.32, 0.27, 0.16, 0.005], hair, depth=0.45, gloss=0.3)
    p.sweep([(m * 0.3, 0.1, 1.0), (m * 0.86, 0.15, 0.6), (m * 1.14, 0.2, -0.3)], [0.2, 0.25, 0.005], tuple(c * 0.85 for c in hair), depth=0.5)
    for k in range(3):
        p.ball((m * -0.82, -0.2 - 0.03 * k, -0.08 - 0.13 * k), (0.03, 0.03, 0.03), rgb(240, 196, 84), gloss=0.9, outline=0.006)
    coat(p, 1.3, deep, accent, tuple(c * 0.5 for c in accent), gap=0.2, neck=0.36)
    for sign in (-1, 1):
        p.plate([(sign * 0.06, -0.74, -1.3), (sign * 0.6, -0.4, -1.14), (sign * 0.66, -0.4, -1.55), (sign * 0.08, -0.78, -1.62)], 0.05, accent, gloss=0.6, root=p.body_root)
    p.sweep([(-0.26, -0.82, -1.6), (0, -0.86, -1.68), (0.26, -0.82, -1.6)], 0.022, rgb(240, 196, 84), gloss=0.9, root=p.body_root, outline=0.005)
    # Scimitar hilts rising behind the same shoulder they'd draw from.
    p.sweep([(m * -0.85, 0.3, -2.0), (m * -1.5, 0.3, -0.3)], [0.055, 0.05], rgb(210, 214, 222), gloss=0.9, root=p.body_root)
    p.sweep([(m * -1.0, 0.3, -1.05), (m * -1.42, 0.3, -1.24)], 0.04, rgb(240, 196, 84), gloss=0.9, root=p.body_root)


def vex(p):
    """The loud twin: silver hair and a curling lip. "Round and round we go, little brig." """
    _twin(p, 1, rgb(232, 232, 242), rgb(166, 76, 240), rgb(52, 26, 92), rgb(214, 120, 252), True)


def vesper(p):
    """The quiet twin: black hair, half-lidded and flat. The one you should have worried about."""
    _twin(p, -1, rgb(34, 36, 56), rgb(40, 204, 190), rgb(14, 58, 64), rgb(70, 232, 212), False)


def malakor(p):
    """The Warden. No face at all, only a furnace behind a slit. Keys rattling at the collar."""
    p.skull()
    p.finish_skull()
    iron, light, glow = rgb(60, 64, 76), rgb(112, 118, 130), rgb(255, 126, 40)
    p.neck(iron, width=0.5, depth=0.5)
    # Great helm: a riveted box tapering to a point at the top.
    rings = []
    for z, rx, ry in ((-1.25, 0.9, 1.0), (-0.5, 1.0, 1.1), (0.25, 1.02, 1.12), (0.82, 0.86, 0.96), (1.25, 0.4, 0.5), (1.5, 0.05, 0.06)):
        ring = []
        for a in np.linspace(0, 2 * math.pi, 72, endpoint=False):
            ca, sa = math.cos(a), math.sin(a)
            k = (abs(ca) ** 3.4 + abs(sa) ** 3.4) ** (-1 / 3.4)
            ring.append((k * rx * ca, 0.05 + k * ry * sa, z))
        rings.append(ring)
    p.loft(_resample(rings, 4), iron, gloss=0.5, halftone=0.3)
    front = -1.06
    p._add(plate_mesh([(-0.72, front - 0.03, 0.13), (0.72, front - 0.03, 0.13), (0.68, front - 0.03, -0.03), (-0.68, front - 0.03, -0.03)], 0.02), p.mat(glow, flat=True), outline=0.0)
    p.plate([(-0.84, front - 0.05, 0.3), (0.84, front - 0.05, 0.3), (0.82, front - 0.05, 0.15), (-0.82, front - 0.05, 0.15)], 0.05, light, gloss=0.8)
    p.plate([(-0.84, front - 0.05, -0.05), (0.84, front - 0.05, -0.05), (0.8, front - 0.05, -0.18), (-0.8, front - 0.05, -0.18)], 0.05, light, gloss=0.8)
    p.plate([(-0.07, front - 0.06, 1.0), (0.07, front - 0.06, 1.0), (0.1, front - 0.06, -1.2), (-0.1, front - 0.06, -1.2)], 0.05, light, gloss=0.8)
    for x in (-0.62, -0.3, 0.3, 0.62):
        for z in (-0.45, -0.75, -1.05):
            p.ball((x, front - 0.04, z), 0.045, light, gloss=0.9, outline=0.006)
    for sign in (-1, 1):
        p.sweep([(sign * 0.9, 0.0, 0.62), (sign * 1.42, -0.05, 1.05), (sign * 1.66, -0.08, 1.85)], [0.24, 0.14, 0.005], light, gloss=0.8, sides=10)
    shoulders(p, 2.05, iron, neck=0.9, depth=1.0, top=-1.1, gloss=0.4)
    for sign in (-1, 1):
        p.ball((sign * 1.65, 0.0, -1.68), (0.66, 0.78, 0.46), light, gloss=0.7, root=p.body_root, rot=(0, sign * 0.3, 0))
        for x in (1.3, 1.72):
            b = np.array((sign * x, -0.05, -1.34 - (x - 1.3) * 0.22))
            p.sweep([b, b + (sign * 0.25, 0, 0.8)], [0.15, 0.004], iron, gloss=0.8, sides=8, root=p.body_root)
    p.plate([(-0.26, -1.0, -1.6), (0.26, -1.0, -1.6), (0.3, -1.0, -3.0), (-0.3, -1.0, -3.0)], 0.04, rgb(120, 32, 34), root=p.body_root)
    # The keys.
    p.ring((0.82, -1.08, -2.2), 0.22, 0.04, rgb(226, 178, 74), gloss=0.9, root=p.body_root, normal=(0, -1, 0.2))
    for k, off in enumerate((-0.14, 0, 0.14)):
        x = 0.82 + off
        p.sweep([(x, -1.1, -2.34), (x + off * 0.5, -1.14, -2.72)], 0.028, rgb(226, 178, 74), gloss=0.9, root=p.body_root, outline=0.006)


def armada_soldier(p):
    """A line trooper, and barely shaved. Oversized shako and scared eyes: a kid in someone else's war."""
    skin, shade, blush = rgb(232, 190, 158), rgb(150, 116, 126), rgb(226, 136, 122)
    p.s["smile"] = -0.06
    face(p, skin, shade, blush, rgb(100, 140, 170), rgb(92, 62, 38), inner=0.17, outer=0.1, thick=0.022, up=0.09, low=0.05, gaze=-0.03, iris_r=0.055)
    for x, z in ((0.17, -0.2), (0.28, -0.19), (0.22, -0.3), (-0.16, -0.21), (-0.26, -0.2), (-0.2, -0.29)):
        p.paint.blob(x, z, 0.012, 0.012, rgb(176, 110, 84), 0.8, soft=0.5)
    finish(p, skin, shade, neck=0.26)
    navy = rgb(36, 50, 104)
    rings = [_ellipse(0.8, 0.94, 0.42), _ellipse(0.88, 1.02, 1.1), _ellipse(0.98, 1.1, 1.72), _ellipse(0.98, 1.1, 1.78), _ellipse(0.2, 0.2, 1.8)]
    p.loft(rings, navy)
    p.loft([_ellipse(1.0, 1.12, 1.72), _ellipse(1.0, 1.12, 1.82)], rgb(240, 196, 84), gloss=0.8, cap=False)
    p.plate([(-0.62, -0.84, 0.44), (0.62, -0.84, 0.44), (0.42, -1.25, 0.34), (-0.42, -1.25, 0.34)], 0.04, rgb(22, 20, 30), gloss=0.8)
    p.plate([(-0.2, -1.1, 0.72), (0.2, -1.1, 0.72), (0.15, -1.17, 1.28), (0, -1.18, 1.42), (-0.15, -1.17, 1.28)], 0.04, rgb(240, 196, 84), gloss=0.9)
    p.sweep([(0, -1.0, 1.75), (0.02, -0.98, 2.2), (0.0, -0.9, 2.66)], [0.12, 0.13, 0.005], rgb(236, 236, 240))
    coat(p, 1.3, navy, navy, None, gap=0.3, neck=0.36)
    p.sweep([(-1.05, -0.7, -1.6), (1.0, -0.88, -2.9)], 0.11, rgb(238, 238, 234), depth=0.3, root=p.body_root)
    p.sweep([(1.05, -0.7, -1.6), (-1.0, -0.88, -2.9)], 0.11, rgb(238, 238, 234), depth=0.3, root=p.body_root)
    p.plate([(-0.24, -0.76, -1.36), (0.24, -0.76, -1.36), (0.3, -0.72, -1.72), (-0.3, -0.72, -1.72)], 0.05, rgb(236, 236, 240), root=p.body_root)


def armada_officer(p):
    """Career officer. Pompous waxed moustache, chin up, looking down at you along his nose."""
    skin, shade, blush = rgb(230, 186, 152), rgb(146, 106, 116), rgb(226, 124, 104)
    blond = rgb(226, 182, 92)
    face(p, skin, shade, blush, rgb(120, 170, 200), blond, inner=0.2, outer=0.17, thick=0.03, lid=0.46, up=0.075, low=0.03, gaze=-0.03, lip_alpha=0.3)
    finish(p, skin, shade, neck=0.34)
    # Waxed to points that break the outline of the face.
    for sign in (-1, 1):
        p.sweep([(sign * 0.03, -1.03, -0.45), (sign * 0.3, -1.02, -0.5), (sign * 0.68, -0.72, -0.38), (sign * 0.86, -0.55, -0.16)], [0.04, 0.075, 0.03, 0.003], blond, depth=0.6)
    peaked_cap(p, rgb(30, 42, 92), rgb(240, 196, 84), badge=rgb(240, 196, 84))
    coat(p, 1.52, rgb(32, 44, 96), rgb(232, 232, 236), rgb(236, 236, 240), gap=0.26, neck=0.44)
    epaulettes(p, 1.52, rgb(240, 196, 84))
    p.sweep([(-1.2, -0.68, -1.62), (0.3, -0.92, -2.6), (0.9, -0.76, -3)], 0.1, rgb(240, 196, 84), depth=0.3, root=p.body_root)
    for k in range(3):
        x = -1.12 + 0.2 * k
        p.plate([(x, -0.82, -1.96), (x + 0.15, -0.82, -1.96), (x + 0.15, -0.82, -2.08), (x, -0.82, -2.08)], 0.03, (rgb(196, 36, 60), rgb(238, 238, 234), rgb(60, 90, 170))[k], root=p.body_root, outline=0.005)


def royal_guard(p):
    """The finale's elite. Silver morion with a crimson comb, dark skin, a calm, dangerous, level stare."""
    skin, shade, blush = rgb(146, 96, 68), rgb(78, 44, 54), rgb(156, 80, 60)
    p.s["smile"] = -0.02
    face(p, skin, shade, blush, rgb(236, 190, 86), rgb(28, 24, 26), inner=0.07, outer=0.12, thick=0.038, lid=0.3, up=0.066, low=0.03, gaze=-0.036)
    p.paint.line([(0.44, -0.3), (0.5, -0.5)], 0.004, shade, 0.7)
    p.paint.line([(-0.44, -0.3), (-0.5, -0.5)], 0.004, shade, 0.7)
    finish(p, skin, shade, neck=0.38, ears=())
    silver, red = rgb(206, 212, 222), rgb(190, 34, 50)
    p.cap(silver, lambda x, y, z: z > 0.3, inflate=0.1, gloss=0.8)
    for sign in (-1, 1):
        p.plate([(sign * 0.3, -0.88, 0.32), (sign * 0.9, -0.34, 0.34), (sign * 0.86, -0.3, -0.4), (sign * 0.64, -0.68, -0.72), (sign * 0.55, -0.76, -0.18)], 0.06, silver, gloss=0.8)
    # Boat-shaped brim, pointed and up-swept front and back.
    brim = []
    for f, lift in ((0.7, 0.0), (1.0, 0.0), (1.2, 0.38)):
        ring = []
        for a in np.linspace(0, 2 * math.pi, 72, endpoint=False):
            ca, sa = math.cos(a), math.sin(a)
            ring.append((ca * 0.96 * f, sa * 1.42 * f, 0.34 + lift * sa * sa + 0.5 * (f - 0.7) * sa * sa))
        brim.append(ring)
    p.loft(brim, silver, gloss=0.8, cap=False)
    outline = [(0, y, 1.38 + 0.42 * (1 - (y / 0.9) ** 2)) for y in np.linspace(-0.92, 0.92, 24)] + [(0, 0.92, 0.75), (0, -0.92, 0.75)]
    p.plate(outline, 0.16, rgb(230, 186, 84), gloss=0.8)
    p.sweep([(0, -0.7, 1.86), (0, -0.05, 2.5), (0, 0.8, 2.15), (0, 1.5, 1.45)], [0.09, 0.22, 0.17, 0.005], red, depth=0.75)
    coat(p, 1.68, silver, rgb(226, 186, 88), rgb(150, 26, 44), gap=0.18, neck=0.46, gloss=0.75)
    for sign in (-1, 1):
        p.ball((sign * 1.42, 0, -1.64), (0.56, 0.72, 0.36), rgb(226, 186, 88), gloss=0.85, root=p.body_root, rot=(0, sign * 0.3, 0))


# ---- the rest of the people you talk to ----------------------------------------------------------------

def tobin(p):
    """Tobin, the Sovereign Gale's old helmsman, who teaches you to fly and never, ever trusts luck. A kind, deeply
    weathered face, worry lines across the brow and crow's feet from squinting into storms, brows knotted in mild
    suspicion of good weather, gentle grey-blue eyes half on the horizon, and a magnificent drooping grey walrus
    moustache. A battered oilskin storm-hat tied under the chin, its brim weighed with fishing-weight beads; a navy
    greatcoat with a turned-up storm collar over a cream cable-knit sweater, a knitted scarf wrapped twice round the
    neck, a brass barometer whose needle always points to "Change", and the weather-staff's vane at his shoulder."""
    skin, shade, blush = rgb(206, 150, 110), rgb(136, 92, 88), rgb(212, 112, 92)
    grey = rgb(198, 200, 206)
    p.s["smile"] = 0.02
    face(p, skin, shade, blush, rgb(120, 156, 180), grey, inner=0.22, outer=0.08, thick=0.046, up=0.066, low=0.036, gaze=(0.0), bags=1.0, skin_shade=shade, gaze_xy=(0.05, 0.025))
    for z in (0.3, 0.38, 0.46):
        p.paint.line([(-0.28, z), (0, z - 0.02), (0.28, z)], 0.0045, shade, 0.65)
    for sign in (-1, 1):
        for k in range(3):
            p.paint.line([(sign * 0.54, 0.04 - 0.05 * k), (sign * 0.68, 0.05 - 0.08 * k)], [0.002, 0.005, 0.001], shade)
    finish(p, skin, shade, neck=0.32)
    # The magnificent drooping walrus moustache.
    for sign in (-1, 1):
        p.sweep([(sign * 0.03, -1.03, -0.42), (sign * 0.28, -1.03, -0.5), (sign * 0.46, -0.9, -0.8), (sign * 0.46, -0.86, -1.02)], [0.05, 0.11, 0.09, 0.005], grey, depth=0.6)
    # The battered oilskin storm-hat, its brim weighed with fishing-weight beads, tied under the chin.
    oilskin = rgb(64, 80, 100)
    wide_hat(p, oilskin, rgb(46, 58, 74), r=1.42, sag=0.28)
    for k in range(7):
        a = math.pi * (0.1 + 0.8 * k / 6)
        p.ball((1.4 * math.cos(a) * -1, -1.4 * math.sin(a) * 0.55 - 0.1, 0.32 - 0.1 * math.sin(a)), 0.05, rgb(120, 124, 132), gloss=0.7, outline=0.005)
    for sign in (-1, 1):
        p.sweep([(sign * 0.82, -0.2, 0.3), (sign * 0.76, -0.4, -0.6), (sign * 0.3, -0.7, -1.05)], 0.018, rgb(176, 146, 98), outline=0.003)

    # The navy greatcoat with its storm collar turned up, over the cream cable-knit sweater and the scarf.
    navy, navy_dark, cream, cable, scarf = rgb(40, 52, 84), rgb(28, 36, 62), rgb(228, 216, 188), rgb(196, 182, 150), rgb(176, 84, 44)
    coat(p, 1.36, navy, navy_dark, cream, gap=0.34, neck=0.4)
    for x in (-0.12, 0.12):
        p.sweep([(x + 0.03 * math.sin(k * 1.7), -0.84, -1.6 - 0.3 * k) for k in range(5)], 0.03, cable, root=p.body_root, outline=0.0)
    for sign in (-1, 1):
        p.plate([(sign * 0.3, -0.3, -1.05), (sign * 0.72, -0.12, -0.55), (sign * 0.86, -0.06, -0.15), (sign * 0.62, -0.3, -1.4)], 0.05, navy, root=p.body_root)
    for k, z in enumerate((-1.18, -1.36)):
        p.sweep([(-0.42, -0.52 + 0.02 * k, z), (0.0, -0.68, z - 0.04), (0.42, -0.52 + 0.02 * k, z)], 0.1, scarf, root=p.body_root)
    p.sweep([(0.26, -0.7, -1.4), (0.32, -0.88, -1.9), (0.3, -0.9, -2.5)], [0.1, 0.1, 0.09], scarf, root=p.body_root)
    # The brass barometer on its chain, needle on "Change".
    bx, bz = -0.62, -2.2
    p.sweep([(-0.5, -0.82, -1.7), (bx, -0.86, bz + 0.12)], 0.008, rgb(186, 142, 62), root=p.body_root, outline=0.0)
    p.ring((bx, -0.9, bz), 0.13, 0.03, rgb(206, 160, 70), gloss=0.9, root=p.body_root)
    p.disc((bx, -0.91, bz), 0.11, rgb(232, 220, 190), root=p.body_root)
    p.sweep([(bx, -0.93, bz), (bx + 0.05, -0.93, bz + 0.07)], 0.01, rgb(30, 24, 26), root=p.body_root, outline=0.0, seg=2)
    # The weather-staff at his shoulder: a brass wind vane and anemometer cups.
    brass = rgb(206, 160, 70)
    p.sweep([(1.4, -0.4, -3.2), (1.3, -0.4, -0.2)], 0.05, rgb(110, 72, 44), root=p.body_root)
    p.sweep([(1.3, -0.4, -0.2), (1.3, -0.4, 0.3)], 0.018, brass, root=p.body_root, outline=0.004)
    p.sweep([(1.06, -0.4, 0.26), (1.56, -0.4, 0.26)], 0.016, brass, root=p.body_root, outline=0.004)
    p.plate([(1.56, -0.4, 0.26), (1.46, -0.4, 0.32), (1.46, -0.4, 0.2)], 0.02, brass, root=p.body_root)
    p.plate([(1.1, -0.4, 0.26), (1.0, -0.4, 0.38), (0.98, -0.4, 0.14)], 0.02, brass, root=p.body_root)
    for a in (0.0, 2.1, 4.2):
        cx, cz = 1.3 + 0.2 * math.cos(a), -0.02
        p.sweep([(1.3, -0.4, cz), (cx, -0.4 - 0.2 * math.sin(a) * 0.4, cz)], 0.01, brass, root=p.body_root, outline=0.0)
        p.ball((cx, -0.4 - 0.08 * math.sin(a), cz), 0.05, brass, gloss=0.8, root=p.body_root, outline=0.004)


def mirren(p):
    """Mirren, the laughing master gunner of the old crew, and the loudest person on any deck: "I'll put a hole in
    the moon." A round, rosy, freckled face dusted with black powder across the nose and cheeks like soot-coloured
    blush, bright green eyes crinkled almost shut over a huge open laugh, a wild riot of copper curls exploding from
    under a knotted green-and-gold headscarf. A short open crimson waistcoat, half its brass buttons gone, over a
    billowing cream shirt; padded brass ear-cups round the neck; the bell-mouthed blunderbuss slung over a shoulder."""
    skin, shade, blush = rgb(238, 192, 158), rgb(158, 106, 108), rgb(232, 120, 104)
    p.s["smile"] = 0.22
    face(p, skin, shade, blush, rgb(96, 190, 90), rgb(176, 70, 26), inner=0.16, outer=0.18, thick=0.034, up=0.07, low=0.044, gaze=0.03, tilt=-0.004, lid=0.55)
    p.mouth(INK, lip=rgb(198, 86, 80), lip_alpha=0.8, open_amt=0.18, teeth=True, line=0.012)
    # Laugh lines crinkling the eyes almost shut.
    for sign in (-1, 1):
        for k in range(3):
            p.paint.line([(sign * 0.5, 0.06 - 0.05 * k), (sign * 0.62, 0.1 - 0.08 * k)], [0.006, 0.002], shade)
    # Freckles, and black powder dusted across the nose and cheeks like soot-coloured blush.
    for x, z in ((0.14, -0.14), (0.25, -0.2), (0.35, -0.14), (0.44, -0.24), (-0.14, -0.15), (-0.24, -0.2), (-0.34, -0.16), (-0.42, -0.25), (0.05, -0.1), (-0.05, -0.11), (0.31, -0.28), (-0.3, -0.29)):
        p.paint.blob(x, z, 0.014, 0.014, rgb(176, 90, 58), 0.85, soft=0.5)
    for x, z, rx, rz in ((0.02, -0.3, 0.12, 0.08), (0.4, -0.24, 0.16, 0.08), (-0.38, -0.26, 0.15, 0.08)):
        p.paint.blob(x, z, rx, rz, rgb(48, 38, 42), 0.42, soft=0.8)
    finish(p, skin, shade, neck=0.34)
    # A wild riot of copper curls, exploding from under the headscarf.
    hair, hair2 = rgb(208, 86, 30), rgb(164, 58, 24)
    hair_cap(p, hair2, line=0.6, curve=0.2)
    rng = np.random.default_rng(3)
    for k in range(40):
        a = rng.uniform(-0.6, math.pi + 0.6)
        r = rng.uniform(0.78, 1.1)
        x, z = math.cos(a) * r * 1.0, 0.3 + math.sin(a) * r * 0.86
        p.ball((x, rng.uniform(-0.45, 0.25), z), rng.uniform(0.17, 0.26), hair if k % 3 else hair2)
    # The knotted green-and-gold headscarf.
    green, gold = rgb(46, 120, 70), rgb(230, 182, 70)
    p.loft([_ellipse(0.9, 1.02, 0.46), _ellipse(0.84, 0.96, 0.78)], green, cap=False)
    p.sweep([(-0.6, -0.72, 0.5), (0.0, -0.98, 0.5), (0.6, -0.72, 0.5)], 0.022, gold, gloss=0.6, outline=0.004)
    p.ball((0.82, 0.2, 0.66), (0.12, 0.12, 0.12), green)
    p.sweep([(0.88, 0.22, 0.62), (1.18, 0.3, 0.36)], [0.1, 0.03], green, depth=0.3)

    # The billowing shirt, the short open waistcoat with half its buttons gone, the ear-cups round the neck.
    cream, crimson = rgb(236, 226, 204), rgb(176, 36, 44)
    shoulders(p, 1.52, cream, neck=0.4)
    for sign in (-1, 1):
        p.plate([(sign * 0.3, -0.6, -1.3), (sign * 1.0, -0.46, -1.4), (sign * 1.04, -0.62, -2.95), (sign * 0.34, -0.8, -2.95)], 0.06, crimson, root=p.body_root)
        p.ball((sign * 0.44, -0.18, -1.12), (0.14, 0.16, 0.2), rgb(214, 166, 70), gloss=0.8, root=p.body_root, outline=0.008)
        p.ball((sign * 0.44, -0.3, -1.12), (0.09, 0.05, 0.12), rgb(120, 76, 52), root=p.body_root, outline=0.004)
    p.sweep([(-0.44, -0.12, -0.96), (0.0, -0.36, -0.92), (0.44, -0.12, -0.96)], 0.03, rgb(70, 46, 34), root=p.body_root, outline=0.004)
    for z, there in ((-1.75, True), (-2.05, False), (-2.35, True), (-2.65, False)):
        if there:
            p.ball((0.4, -0.86, z), (0.055, 0.04, 0.055), rgb(214, 170, 70), gloss=0.9, root=p.body_root, outline=0.006)
        else:
            p.sweep([(0.4, -0.86, z), (0.42, -0.88, z - 0.06)], 0.006, rgb(150, 120, 90), root=p.body_root, outline=0.0, seg=2)
    # The blunderbuss slung over the right shoulder, its brass bell flaring behind the head.
    brass, wood = rgb(206, 156, 64), rgb(110, 70, 40)
    p.sweep([(-1.1, -0.5, -2.8), (-0.95, -0.3, -1.6)], 0.09, wood, root=p.body_root)
    p.sweep([(-0.95, -0.3, -1.6), (-1.15, 0.1, -0.1)], 0.07, brass, gloss=0.8, root=p.body_root)
    p.sweep([(-1.15, 0.1, -0.1), (-1.22, 0.16, 0.3)], [0.07, 0.24], brass, gloss=0.8, root=p.body_root)
    p.ring((-1.22, 0.16, 0.32), 0.22, 0.03, brass, gloss=0.8, normal=(-0.2, 0.15, 1), root=p.body_root)


def odessa(p):
    """Odessa, the Gale's surgeon and keeper of its Lift-Core, and the most tired face in the sky: "Keep your limbs
    attached and my Lift-Core cool. That's all I've ever asked of you lot." Warm brown skin lined round the eyes,
    heavy drooping lids and deep bags over steady brown eyes, a mouth in a flat line of infinite patience, grey hair
    in a tight bun skewered with two steel probes, and a polished head-mirror on a leather band. A slate-grey
    surgeon's coat buttoned to the throat under a quilted vest with scorch-marked shoulder pads, a stethoscope
    with a flared brass bell, and bandage rolls bulging from the pockets."""
    skin, shade, blush = rgb(162, 110, 80), rgb(92, 56, 62), rgb(168, 86, 68)
    grey, steel = rgb(186, 186, 192), rgb(196, 204, 212)
    p.s["smile"] = -0.06
    face(p, skin, shade, blush, rgb(120, 86, 56), grey, inner=0.13, outer=0.1, thick=0.024, lid=0.56, up=0.076, low=0.034, gaze=0.03, bags=1.3, skin_shade=shade, lip_alpha=0.6)
    for sign in (-1, 1):
        p.paint.line([(sign * 0.22, -0.32), (sign * 0.33, -0.5), (sign * 0.34, -0.64)], [0.003, 0.008, 0.002], shade)
        # Lines worn in round the eyes.
        for k in range(3):
            p.paint.line([(sign * 0.5, 0.04 - 0.05 * k), (sign * 0.62, 0.06 - 0.07 * k)], [0.005, 0.002], shade, 0.8)
    finish(p, skin, shade, neck=0.3)
    # The tight grey bun, skewered with two steel probes.
    hair_cap(p, grey, line=0.46, curve=0.25, nape=-0.45, inflate=0.04)
    p.ball((0.0, 0.62, 0.66), (0.42, 0.34, 0.42), grey)
    for sign in (-1, 1):
        p.sweep([(sign * -0.5, 0.5, 0.5), (sign * 0.55, 0.72, 0.92)], [0.025, 0.012], steel, gloss=0.9, outline=0.004)
    # The head-mirror: a polished disc strapped across the brow, flashing.
    p.loft([_ellipse(0.8, 0.96, 0.46), _ellipse(0.8, 0.96, 0.6)], rgb(60, 44, 40), cap=False)
    p.ring((0.0, -1.0, 0.9), 0.24, 0.03, rgb(186, 142, 62), gloss=0.9, normal=(0, -1, -0.2))
    p.disc((0.0, -1.0, 0.9), 0.23, rgb(236, 246, 246), normal=(0, -1, -0.2), gloss=0.9)

    # The slate-grey surgeon's coat, buttoned to the throat, under the quilted vest and its scorched pads.
    slate, slate_dark, quilt, quilt_line = rgb(78, 88, 112), rgb(56, 64, 86), rgb(150, 136, 104), rgb(112, 100, 76)
    shoulders(p, 1.4, slate, neck=0.38)
    p.sweep([(-0.36, -0.36, -1.12), (0.0, -0.46, -1.18), (0.36, -0.36, -1.12)], 0.08, slate_dark, root=p.body_root)
    for z in (-1.45, -1.8, -2.15, -2.5, -2.85):
        p.ball((0.0, -0.84, z), (0.05, 0.035, 0.05), rgb(70, 74, 84), gloss=0.6, root=p.body_root, outline=0.006)
    for sign in (-1, 1):
        p.plate([(sign * 0.32, -0.68, -1.35), (sign * 1.02, -0.5, -1.45), (sign * 1.06, -0.64, -2.95), (sign * 0.36, -0.84, -2.95)], 0.07, quilt, root=p.body_root)
        for z in (-1.75, -2.1, -2.45, -2.8):
            p.sweep([(sign * 0.38, -0.86, z), (sign * 1.02, -0.68, z + 0.04)], 0.01, quilt_line, root=p.body_root, outline=0.0)
        pad = (sign * 1.15, -0.3, -1.45)
        p.ball(pad, (0.42, 0.44, 0.2), rgb(110, 72, 46), root=p.body_root, rot=(0, sign * 0.3, 0))
        p.ball((pad[0] - sign * 0.06, -0.62, pad[2] + 0.1), (0.16, 0.06, 0.08), rgb(48, 40, 38), root=p.body_root, outline=0.0)
    # The stethoscope round the neck, its flared brass bell hanging, and bandage rolls bulging from a pocket.
    p.sweep([(-0.42, -0.45, -1.2), (-0.36, -0.86, -1.8), (-0.18, -0.92, -2.25)], 0.025, rgb(40, 34, 32), root=p.body_root, outline=0.004)
    p.sweep([(0.42, -0.45, -1.2), (0.3, -0.88, -1.9)], 0.025, rgb(40, 34, 32), root=p.body_root, outline=0.004)
    p.ring((-0.18, -0.96, -2.32), 0.1, 0.03, rgb(206, 160, 70), gloss=0.9, root=p.body_root)
    p.disc((-0.18, -0.97, -2.32), 0.08, rgb(176, 132, 56), gloss=0.8, root=p.body_root)
    for k, x in enumerate((0.58, 0.74)):
        p.sweep([(x, -0.9, -2.55), (x, -0.9, -2.28 - 0.06 * k)], 0.08, rgb(240, 236, 226), root=p.body_root, outline=0.006)


def ashgrave(p):
    """Lord Ashgrave, the pinched Syndicate toll-lord, eyes already sliding towards the lifeboats. A long, pinched
    face powdered chalk-white, pale violet eyes in shadowed, sleepless sockets, a gold monocle on a fine chain,
    thin pursed lips, a beauty mark high on the left cheek, and a tight grey-powdered queue tied in black ribbon.
    A towering starched collar past the jaw, a lace jabot, and a plum frock coat frogged in tarnished silver,
    the Syndicate cipher-case bulging from its inner pocket: "The cipher's in my coat. Please." """
    skin, shade, blush = rgb(238, 232, 230), rgb(150, 128, 150), rgb(220, 160, 176)
    black = rgb(40, 28, 40)
    p.s["smile"] = -0.03
    face(p, skin, shade, blush, rgb(186, 150, 236), black, inner=0.18, outer=0.1, thick=0.014, up=0.08, low=0.036, gaze=-0.06, lip_alpha=0.85, bags=0.9, skin_shade=shade)
    # Shadowed, sleepless sockets.
    for sign in (-1, 1):
        p.paint.blob(sign * p.s["eye_x"], p.s["eye_z"] - 0.02, 0.2, 0.12, rgb(150, 120, 160), 0.35, soft=0.9)
    # Thin, pursed lips, and the beauty mark high on the left cheek.
    p.paint.blob(0.0, p.s["mouth_z"], 0.06, 0.02, rgb(150, 70, 96), 0.7, soft=0.5)
    p.paint.blob(0.44, -0.14, 0.014, 0.014, rgb(30, 20, 30), 1.0, soft=0.2)
    finish(p, skin, shade, neck=0.22)
    # The tight grey-powdered queue: hair combed hard back, one roll above each ear, a black ribbon behind.
    wig, wig_shade = rgb(200, 198, 208), rgb(150, 148, 162)
    hair_cap(p, wig, line=0.58, curve=0.1, nape=-0.45, inflate=0.04)
    for sign in (-1, 1):
        p.sweep([(sign * 0.8, -0.26, 0.24), (sign * 0.88, 0.05, 0.24), (sign * 0.8, 0.32, 0.24)], 0.13, wig, sides=14)
        p.sweep([(sign * 0.45, -0.66, 0.9), (sign * 0.62, -0.2, 1.0)], [0.01, 0.004], wig_shade, depth=0.3, outline=0.0)
    p.ball((0.0, 0.92, -0.2), (0.22, 0.08, 0.14), black)
    for sign in (-1, 1):
        p.sweep([(sign * 0.08, 0.95, -0.2), (sign * 0.42, 1.0, -0.02)], [0.12, 0.03], black, depth=0.2)
    # The gold-rimmed monocle and its fine chain.
    gold = rgb(230, 186, 84)
    p.ring((-0.31, -1.0, 0.03), 0.2, 0.024, gold, gloss=0.9)
    p.sweep([(-0.31, -1.0, -0.18), (-0.42, -0.96, -0.62), (-0.55, -0.9, -1.2)], 0.008, gold, outline=0.0)
    p.sweep([(-0.42, -1.015, -0.09), (-0.24, -1.015, 0.13)], 0.024, rgb(255, 255, 255), depth=0.2, outline=0.0)

    # The plum frock coat, frogged in tarnished silver, the cipher-case peeking from the inner pocket.
    plum, plum_dark, silver = rgb(70, 30, 96), rgb(46, 18, 70), rgb(176, 180, 196)
    coat(p, 1.22, plum, plum_dark, rgb(236, 230, 240), gap=0.16, neck=0.32)
    for z in (-1.75, -2.05, -2.35, -2.65):
        for sign in (-1, 1):
            p.sweep([(sign * 0.2, -0.86, z), (sign * 0.52, -0.8, z)], 0.02, silver, gloss=0.7, root=p.body_root, outline=0.004)
            p.ball((sign * 0.53, -0.82, z), 0.035, silver, gloss=0.8, root=p.body_root, outline=0.004)
    p.sweep([(0.36, -0.84, -2.05), (0.4, -0.86, -1.7)], 0.07, rgb(196, 152, 66), gloss=0.8, root=p.body_root)
    p.ball((0.4, -0.87, -1.66), (0.075, 0.05, 0.05), rgb(60, 196, 190), gloss=0.9, root=p.body_root, outline=0.006)
    # The towering starched collar, rising past the jaw, and the lace jabot spilling from the throat.
    starch = rgb(244, 240, 246)
    for sign in (-1, 1):
        p.plate([(sign * 0.12, -0.66, -1.3), (sign * 0.84, -0.26, -0.8), (sign * 0.92, -0.1, -0.1), (sign * 0.6, -0.28, -1.5)], 0.04, starch, root=p.body_root)
    for k, z in enumerate((-1.38, -1.55, -1.72)):
        half = 0.16 + 0.05 * k
        p.sweep([(-half, -0.86 - 0.02 * k, z), (0, -0.94 - 0.02 * k, z - 0.1), (half, -0.86 - 0.02 * k, z)], 0.07, starch, root=p.body_root)
    p.ball((0, -1.0, -1.5), 0.06, rgb(60, 196, 190), gloss=0.9, root=p.body_root)


def thrace(p):
    """Lady Thrace, the untouchable sky-lounge duelist, unimpressed by everything including you. A fine-boned face,
    high cheekbones, a hooded green stare, deep crimson lips in a half-smirk, and a towering swept-up coiffure the
    colour of old wine pinned with jewelled combs, one stray lock curling over her right eye. A wine-and-black
    duelling coat with a high split collar over a corseted silver waistcoat, strands of pearls at the throat, a
    black silk half-cape clasped with a garnet brooch, and a black lace fan snapped open beside her chin."""
    skin, shade, blush = rgb(220, 178, 146), rgb(136, 98, 112), rgb(208, 112, 110)
    wine, wine_light = rgb(112, 26, 56), rgb(150, 40, 76)
    pearl, gold, black = rgb(240, 240, 232), rgb(226, 182, 84), rgb(26, 20, 28)
    p.s["smile"] = 0.05
    p.s["smirk"] = -0.12
    face(p, skin, shade, blush, rgb(70, 196, 120), rgb(58, 16, 34), inner=0.11, outer=0.18, thick=0.016, lid=0.52, up=0.08, low=0.03, tilt=0.03, gaze=-0.05, lash=0.024, lip=rgb(162, 22, 50), lip_alpha=1.0)
    # High cheekbones.
    for sign in (-1, 1):
        p.paint.line([(sign * 0.26, -0.2), (sign * 0.5, -0.22), (sign * 0.64, -0.12)], [0.003, 0.01, 0.003], shade, 0.7)
    p.finish_skull()
    p.ear(1, skin, shade)
    p.ear(-1, skin, shade)
    p.neck(skin, width=0.25, depth=0.25)
    # The towering coiffure, pinned with jewelled combs.
    hair_cap(p, wine, line=0.56, curve=0.2, nape=-0.2, inflate=0.05)
    for k, (x, z, w) in enumerate(((-0.42, 1.02, 0.42), (0.38, 1.1, 0.44), (-0.15, 1.46, 0.42), (0.26, 1.72, 0.32), (-0.1, 1.98, 0.22))):
        p.ball((x, 0.12, z), (w, w * 0.86, w), wine if k % 2 else wine_light)
    for x, z, gem in ((0.62, 1.2, rgb(60, 196, 190)), (-0.5, 1.52, rgb(200, 30, 50)), (0.4, 1.84, rgb(60, 196, 190))):
        p.sweep([(x - 0.16, -0.32, z), (x + 0.16, -0.36, z + 0.04)], 0.035, gold, gloss=0.8, outline=0.005)
        p.ball((x, -0.4, z + 0.03), 0.055, gem, gloss=0.9, outline=0.005)
    # The one deliberate stray lock, curling down over her right eye.
    p.sweep([(-0.18, -0.8, 0.62), (-0.3, -0.92, 0.3), (-0.36, -0.95, 0.04), (-0.28, -0.94, -0.14)], [0.06, 0.06, 0.04, 0.003], wine, depth=0.5)
    for sign in (-1, 1):
        p.sweep([(sign * 0.82, 0.05, -0.28), (sign * 0.82, 0.05, -0.56)], 0.015, pearl, outline=0.0)
        p.ball((sign * 0.82, 0.05, -0.62), 0.05, pearl, gloss=0.9, outline=0.006)

    # The duelling coat, its high split collar, the corseted silver waistcoat.
    coat(p, 1.2, wine, black, rgb(196, 200, 212), gap=0.3, neck=0.3)
    for sign in (-1, 1):
        p.plate([(sign * 0.14, -0.3, -1.05), (sign * 0.62, -0.1, -0.6), (sign * 0.76, -0.05, -0.05), (sign * 0.5, -0.24, -1.3)], 0.04, wine, root=p.body_root)
        p.sweep([(sign * 0.62, -0.12, -0.6), (sign * 0.76, -0.07, -0.05)], 0.02, black, root=p.body_root, outline=0.004)
    for k in range(4):
        z = -1.85 - 0.22 * k
        for sign in (-1, 1):
            p.sweep([(sign * 0.12, -0.86, z), (-sign * 0.12, -0.86, z - 0.18)], 0.012, black, root=p.body_root, outline=0.0)
    # Strands of pearls at the throat.
    for strand, (depth, sag) in enumerate(((0.65, 0.3), (0.7, 0.48), (0.74, 0.66))):
        for k in np.linspace(0, 1, 15 + 2 * strand):
            x = -0.5 + 1.0 * k
            bow = 1 - (2 * k - 1) ** 2
            p.ball((x, -depth - 0.2 * bow, -1.4 - sag * bow), 0.045, pearl, gloss=0.9, root=p.body_root, outline=0.005)
    # The black silk half-cape over her left shoulder, clasped with a garnet brooch.
    p.sweep([(0.5, -0.5, -1.35), (1.1, -0.35, -1.55), (1.45, -0.2, -2.6)], [0.18, 0.3, 0.32], black, depth=0.4, root=p.body_root)
    p.ball((0.56, -0.86, -1.55), (0.1, 0.05, 0.1), rgb(150, 18, 40), gloss=0.9, root=p.body_root, outline=0.006)
    p.ring((0.56, -0.86, -1.55), 0.11, 0.022, gold, gloss=0.9, root=p.body_root)
    # The black lace fan, snapped open beside her chin, gold ribs fanning from the pivot.
    pivot = (1.18, -1.2, -1.6)
    tips = [(pivot[0] + 0.9 * math.sin(a), pivot[1] - 0.1, pivot[2] + 0.9 * math.cos(a)) for a in np.linspace(-1.15, 0.25, 9)]
    p.plate([pivot] + tips, 0.02, black, root=p.body_root)
    for tip in tips[::2]:
        p.sweep([pivot, (pivot[0] + (tip[0] - pivot[0]) * 0.96, pivot[1] - 0.12, pivot[2] + (tip[2] - pivot[2]) * 0.96)], 0.012, gold, gloss=0.8, root=p.body_root, outline=0.0, seg=2)
    p.sweep(tips, 0.02, rgb(60, 50, 64), root=p.body_root, outline=0.004)
    p.ball(pivot, 0.05, gold, gloss=0.9, root=p.body_root, outline=0.005)


def gorse(p):
    """Captain Gorse, the bellowing Scrap-brig rival, mid-bluster. A ruddy, sunburnt face framed by enormous
    ginger-brown mutton chops bristling outward, a wide gap-toothed grin with a gold tooth, amber eyes darting
    for the exit, a bulbous much-broken nose and flushed cheeks. An oversized tricorn with a singed, snapped
    plume; a patchwork sailcloth coat riveted with scrap plates across the shoulders over a gaudy plum
    waistcoat straining at its brass buttons."""
    skin, shade, blush = rgb(212, 140, 100), rgb(136, 78, 76), rgb(222, 86, 70)
    ginger, ginger_light = rgb(168, 86, 40), rgb(214, 128, 64)
    p.s["smile"] = 0.13
    p.s["smirk"] = -0.08
    face(p, skin, shade, blush, rgb(226, 150, 40), rgb(140, 66, 30), inner=0.1, outer=0.21, thick=0.05, up=0.075, low=0.04, gaze=-0.045)
    p.mouth(INK, lip=rgb(166, 76, 70), lip_alpha=0.7, open_amt=0.11, teeth=True, line=0.012)
    # The gap where a front tooth was, and the gold one beside it.
    p.paint.line([(-0.09, -0.61), (-0.09, -0.69)], 0.018, rgb(40, 14, 18))
    p.paint.blob(0.11, -0.65, 0.03, 0.024, rgb(244, 190, 58), 1.0, soft=0.2)
    p.paint.blob(0.105, -0.64, 0.01, 0.008, rgb(255, 244, 200), 1.0, soft=0.3)
    # A bulbous, much-broken nose, and cheeks flushed with rum and shouting.
    p.paint.blob(0.02, -0.4, 0.13, 0.1, rgb(218, 76, 62), 0.65)
    p.paint.line([(-0.03, -0.12), (0.04, -0.22), (0.0, -0.3)], [0.004, 0.01, 0.004], shade, 0.7)
    for sign in (-1, 1):
        p.paint.blob(sign * 0.42, -0.3, 0.17, 0.1, rgb(222, 80, 66), 0.45)
    finish(p, skin, shade, neck=0.4)
    # Enormous mutton chops, bristling out like a startled cat.
    for sign in (-1, 1):
        p.sweep([(sign * 0.7, -0.5, -0.05), (sign * 0.88, -0.6, -0.48), (sign * 0.6, -0.8, -0.86)], [0.06, 0.18, 0.02], ginger, depth=0.55)
        for k, (z, dz) in enumerate(((-0.25, 0.08), (-0.45, 0.0), (-0.62, -0.1))):
            p.sweep([(sign * 0.86, -0.55, z), (sign * 1.06, -0.5, z + dz)], [0.06, 0.004], ginger if k % 2 else ginger_light, depth=0.4)
    # The oversized tricorn, and its plume snapped halfway and burnt at the tip.
    tricorn(p, rgb(92, 54, 30), rgb(204, 156, 62))
    plume = [(-0.6, -0.2, 0.96), (-0.9, -0.1, 1.52), (-1.22, 0.0, 1.66), (-1.6, 0.2, 1.36)]
    p.sweep(plume, [0.08, 0.16, 0.14, 0.03], rgb(226, 206, 160), depth=0.5)
    p.sweep(plume[1:], [0.06, 0.06, 0.01], rgb(196, 66, 40), depth=0.4, outline=0.0)
    p.ball((-1.62, 0.21, 1.34), (0.07, 0.07, 0.07), rgb(48, 40, 40))

    # The patchwork coat, scrap plates riveted across the shoulders, over the straining plum waistcoat.
    coat(p, 1.62, rgb(170, 152, 120), rgb(120, 104, 82), rgb(110, 26, 52), gap=0.3, neck=0.46)
    for x, z, c in ((-1.05, -1.95, rgb(108, 80, 54)), (0.95, -2.35, rgb(64, 98, 62)), (-0.7, -2.6, rgb(52, 62, 96)), (1.15, -1.75, rgb(226, 212, 180))):
        p.plate([(x - 0.17, -0.66, z + 0.14), (x + 0.17, -0.66, z + 0.14), (x + 0.15, -0.68, z - 0.15), (x - 0.16, -0.68, z - 0.14)], 0.02, c, root=p.body_root)
        for k in range(4):
            p.sweep([(x - 0.18 + 0.1 * k, -0.7, z + 0.15), (x - 0.15 + 0.1 * k, -0.7, z + 0.11)], 0.008, rgb(40, 30, 28), root=p.body_root, outline=0.0, seg=2)
    for sign in (-1, 1):
        for dx, dz, c in ((0.0, 0.0, rgb(150, 156, 166)), (0.32, -0.22, rgb(158, 84, 48))):
            cx, cz = sign * (1.15 + dx), -1.55 + dz
            p.plate([(cx - 0.26, -0.3, cz + 0.1), (cx + 0.26, -0.3, cz + 0.06), (cx + 0.24, -0.42, cz - 0.2), (cx - 0.24, -0.44, cz - 0.16)], 0.05, c, gloss=0.5, root=p.body_root)
            for rx in (-0.16, 0.16):
                p.ball((cx + rx, -0.46, cz - 0.05), (0.035, 0.03, 0.035), rgb(60, 60, 68), gloss=0.6, root=p.body_root, outline=0.004)
    for z in (-1.75, -2.1, -2.45):
        p.ball((0.0, -0.98, z), (0.055, 0.04, 0.055), rgb(214, 170, 70), gloss=0.9, root=p.body_root, outline=0.006)
        for sign in (-1, 1):
            p.sweep([(sign * 0.03, -0.96, z), (sign * 0.16, -0.94, z + 0.06)], 0.008, rgb(76, 16, 36), root=p.body_root, outline=0.0, seg=2)


def captain_ria(p):
    """Captain Ria, the joyful free-fleet wingmate: the first captain who ever chose to fly at Vane's wing, and
    their whole face shows it. Sun-browned and freckled, dark hair cropped short and wind-tousled with the sides
    shaved close, bright amber eyes, an enormous open grin, a burst of gold earrings climbing the right ear and a
    thin white scar on the chin. Brass flight goggles with amber lenses pushed up into the hair, a faded sky-blue
    sleeveless flight jacket with a sheepskin collar over a rust-orange shirt, signal-flag tubes over the shoulders."""
    skin, shade, blush = rgb(176, 120, 82), rgb(100, 60, 58), rgb(190, 90, 66)
    black = rgb(34, 26, 34)
    p.s["smile"] = 0.2
    face(p, skin, shade, blush, rgb(240, 172, 52), black, inner=0.14, outer=0.17, thick=0.03, up=0.082, low=0.042, gaze=0.03)
    p.mouth(INK, lip=rgb(152, 70, 62), lip_alpha=0.8, open_amt=0.12, teeth=True, line=0.011)
    # Freckles from open-air flying, laugh lines, and the thin white scar nicking the chin.
    rng = np.random.default_rng(3)
    for x, z in rng.uniform((-0.5, -0.36), (0.5, -0.08), (34, 2)):
        if abs(x) > 0.1 or z < -0.2:
            p.paint.blob(x, z, 0.012, 0.012, rgb(122, 72, 50), 0.75, soft=0.4)
    for sign in (-1, 1):
        p.paint.line([(sign * 0.25, -0.3), (sign * 0.33, -0.48), (sign * 0.32, -0.6)], [0.003, 0.008, 0.002], shade)
    p.paint.line([(0.1, -0.86), (0.12, -0.98)], [0.004, 0.012], rgb(232, 200, 176))
    finish(p, skin, shade, neck=0.3)
    # Cropped short and tousled on top, the sides shaved close (just a shadow of stubble).
    hair_cap(p, black, line=0.62, curve=0.32, nape=-0.3, inflate=0.04)
    for x, z, dx, dz in ((-0.42, 0.84, -0.2, 0.22), (-0.18, 0.98, -0.1, 0.28), (0.06, 1.02, 0.05, 0.3), (0.3, 0.96, 0.16, 0.26), (0.5, 0.82, 0.24, 0.2)):
        p.sweep([(x, -0.3, z), (x + dx, -0.3, z + dz)], [0.15, 0.004], black, depth=0.6)
    goggles(p, z=0.68, y=-0.84, spread=0.3, r=0.18, lens=rgb(244, 170, 60), frame=rgb(196, 150, 62), strap=rgb(70, 46, 34), tilt=0.1)
    # A burst of gold earrings climbing the right ear.
    for k in range(4):
        p.ring((-0.82, -0.08, -0.32 + k * 0.1), 0.045, 0.012, rgb(244, 190, 58), gloss=0.9, normal=(1, 0, 0), outline=0.003)

    # The faded sky-blue flight jacket, sleeveless, its sheepskin collar turned out, over the rust-orange shirt.
    sky, sky_dark, fleece, orange = rgb(150, 186, 214), rgb(110, 142, 170), rgb(236, 226, 204), rgb(196, 98, 44)
    shoulders(p, 1.36, orange, neck=0.38)
    for sign in (-1, 1):
        p.plate([(sign * 0.3, -0.62, -1.3), (sign * 0.98, -0.44, -1.36), (sign * 1.06, -0.6, -2.95), (sign * 0.34, -0.8, -2.95)], 0.06, sky, root=p.body_root)
        p.sweep([(sign * 0.98, -0.5, -1.45), (sign * 1.06, -0.62, -2.9)], 0.03, sky_dark, root=p.body_root, outline=0.0)
        p.sweep([(sign * 0.12, -0.7, -1.2), (sign * 0.5, -0.6, -1.32), (sign * 0.62, -0.7, -1.9)], [0.16, 0.18, 0.06], fleece, depth=0.5, root=p.body_root)
    for x, z in ((0.72, -2.2), (-0.62, -2.6)):
        p.plate([(x - 0.12, -0.8, z + 0.1), (x + 0.12, -0.8, z + 0.1), (x + 0.12, -0.82, z - 0.1), (x - 0.12, -0.82, z - 0.1)], 0.02, rgb(120, 156, 186), root=p.body_root)
    # Signal-flag tubes over the shoulders, the flags poking out.
    for sign, flag in ((-1, rgb(214, 46, 52)), (1, rgb(244, 178, 52))):
        p.sweep([(sign * 1.0, 0.3, -1.6), (sign * 1.28, 0.25, -0.75)], 0.08, rgb(120, 78, 46), root=p.body_root)
        p.plate([(sign * 1.28, 0.2, -0.72), (sign * 1.6, 0.2, -0.6), (sign * 1.32, 0.2, -0.4)], 0.02, flag, root=p.body_root)


def scrapper(p):
    """Scrap-Winds rank and file. A welding mask flipped up, one tooth, soot everywhere, delighted."""
    skin, shade, blush = rgb(186, 128, 88), rgb(92, 56, 54), rgb(174, 88, 66)
    p.s["smile"] = 0.1
    face(p, skin, shade, blush, rgb(230, 212, 90), rgb(36, 28, 26), inner=0.08, outer=0.16, thick=0.04, up=0.09, low=0.05, gaze=-0.03, iris_r=0.048)
    p.mouth(INK, open_amt=0.1, line=0.012)
    p.paint.blob(0.05, p.s["mouth_z"] - 0.035, 0.028, 0.03, rgb(236, 218, 150), 1.0, soft=0.2)
    rng = np.random.default_rng(7)
    # Soot in broad wipes, clear around the eyes: goggle marks, from a life behind a welding mask.
    p.paint.blob(0.3, -0.42, 0.3, 0.18, rgb(38, 30, 32), 0.55)
    p.paint.blob(-0.42, -0.5, 0.24, 0.18, rgb(38, 30, 32), 0.5)
    p.paint.blob(0.0, 0.34, 0.4, 0.12, rgb(38, 30, 32), 0.45)
    finish(p, skin, shade, neck=0.26)
    iron = rgb(84, 88, 96)
    rings = [_ellipse(0.8, 0.94, 0.46), _ellipse(0.88, 1.02, 1.1), _ellipse(0.6, 0.7, 1.35), _ellipse(0.2, 0.2, 1.42)]
    p.loft(_resample(rings, 4), rgb(106, 66, 40))
    p.plate([(-0.82, -0.8, 0.5), (0.82, -0.8, 0.5), (0.72, -1.02, 1.56), (-0.72, -1.02, 1.56)], 0.08, iron, gloss=0.5)
    p.plate([(-0.52, -0.97, 0.92), (0.52, -0.97, 0.92), (0.47, -1.05, 1.24), (-0.47, -1.05, 1.24)], 0.03, rgb(78, 228, 180), gloss=0.6)
    for x in (-0.8, 0.8):
        p.ball((x, -0.82, 0.58), 0.07, rgb(186, 142, 62), gloss=0.9)
    coat(p, 1.25, rgb(96, 70, 48), rgb(70, 50, 36), rgb(160, 90, 44), gap=0.2, neck=0.36)
    for k in range(9):
        t = k / 8
        p.ring((-0.9 + 1.8 * t, -0.86, -1.72 - 0.34 * (1 - (2 * t - 1) ** 2)), 0.08, 0.024, rgb(130, 134, 144), gloss=0.85, normal=(0.7, 0, 0.7) if k % 2 else (-0.7, 0, 0.7), root=p.body_root, outline=0.006)


def runner(p):
    """Haven runner, one step ahead of everyone. Wide-eyed, sweat on the brow, a wind-whipped headwrap."""
    skin, shade, blush = rgb(144, 98, 74), rgb(80, 48, 56), rgb(162, 84, 68)
    p.s["smile"] = -0.06
    face(p, skin, shade, blush, rgb(110, 230, 170), rgb(28, 22, 26), inner=0.2, outer=0.12, thick=0.03, up=0.09, low=0.054, gaze=0.045, iris_r=0.052)
    finish(p, skin, shade, neck=0.25, ears=())
    wrap, wrap2 = rgb(50, 186, 150), rgb(30, 120, 112)
    p.cap(wrap, lambda x, y, z: (z > 0.34 + 0.06 * np.abs(x)) | ((y > 0.1) & (z > -0.45)), inflate=0.08)
    for z in (0.5, 0.74):
        p.sweep([(-0.8, -0.3, z - 0.12), (0, -1.0, z), (0.8, -0.3, z + 0.1)], 0.04, wrap2, seg=8, outline=0.004)
    p.sweep([(-0.8, 0.3, 0.42), (-1.34, 0.45, 0.5), (-1.92, 0.5, 0.18)], [0.12, 0.17, 0.01], wrap, depth=0.3)
    p.sweep([(-0.8, 0.3, 0.36), (-1.28, 0.45, 0.05), (-1.76, 0.5, -0.38)], [0.1, 0.13, 0.01], wrap2, depth=0.3)
    for x, z in ((0.25, 0.48), (-0.22, 0.42), (0.47, 0.36)):
        p.sweep([(x, -0.97, z), (x, -0.97, z - 0.1)], [0.012, 0.025], rgb(226, 246, 255), outline=0.003)
    coat(p, 1.14, rgb(50, 62, 80), rgb(36, 44, 60), rgb(190, 176, 144), gap=0.22, neck=0.32)


def hask(p):
    """The pressed master gunner, giving you his one good stare. A shaved, soot-weathered skull ruled with black
    tally-mark tattoos from his right temple down the side of his neck. An angular, grim face speckled with
    black-powder stippling and an old flash burn, a jaw set in a tight line under salt-and-ash stubble, and a
    vertical scar through his left brow over a milky, blind eye; the right eye a sharp steel grey. A sleeveless
    linen shirt under a scorched bull-hide apron on brass buckles, a cracked bandolier of brass powder flasks,
    and the linstock in his fist, its slow-match smouldering orange."""
    skin, shade, blush = rgb(196, 146, 108), rgb(112, 80, 78), rgb(178, 106, 84)
    ink, stubble = rgb(24, 22, 28), rgb(92, 86, 84)
    ex, ez = p.s["eye_x"], p.s["eye_z"]
    p.s["smile"] = -0.03
    p.skull()
    p.base_skin(shade, blush)
    # Weathered scalp, and salt-and-ash stubble over the jaw, cheeks and upper lip.
    p.paint.blob(0, 0.74, 0.7, 0.34, rgb(170, 128, 100), 0.45, soft=0.7)
    p.paint.blob(0, -0.76, 0.66, 0.34, stubble, 0.42, soft=0.6)
    p.paint.blob(0, -0.5, 0.2, 0.06, stubble, 0.35, soft=0.7)
    rng = np.random.default_rng(11)
    for x, z in rng.uniform((-0.66, -1.02), (0.66, -0.44), (220, 2)):
        if (x / 0.66) ** 2 + ((z + 0.76) / 0.34) ** 2 < 1.1:
            p.paint.blob(x, z, 0.008, 0.008, rgb(60, 56, 58), 0.6, soft=0.3)
    # Black-powder stippling across both cheeks and the brow, and an old flash burn under the blind eye.
    for x, z in rng.uniform((-0.7, -0.4), (0.7, 0.45), (60, 2)):
        if abs(x) > 0.18 or z > 0.25:
            p.paint.blob(x, z, 0.01, 0.01, ink, 0.8, soft=0.3)
    p.paint.blob(0.5, -0.24, 0.12, 0.08, rgb(206, 120, 104), 0.55)
    p.paint.blob(0.53, -0.22, 0.06, 0.04, rgb(226, 160, 140), 0.5)

    # His right eye (image left): steel grey and locked on. His left: a milky, sightless film.
    p.eye(-1, rgb(132, 150, 166), lid=0.36, up=0.064, low=0.03, gaze=(0.03, 0.0), bags=0.6, skin_shade=shade)
    p.eye(1, rgb(196, 204, 206), lid=0.48, up=0.064, low=0.03, gaze=(-0.01, -0.012), bags=0.6, skin_shade=shade)
    k = 1.22
    p.paint.blob(ex - 0.01, ez + 0.0, 0.07 * k, 0.03 * k, rgb(232, 236, 234), 0.95, soft=0.4)
    p.paint.blob(ex - 0.01, ez + 0.0, 0.035 * k, 0.02 * k, rgb(206, 216, 222), 0.6, soft=0.8)
    p.brow(-1, rgb(64, 58, 56), inner=0.07, outer=0.11, thick=0.034)
    p.brow(1, rgb(64, 58, 56), inner=0.07, outer=0.11, thick=0.034)
    # The scar: a pale seam straight down through the left brow, across the lids, onto the cheek.
    scar = rgb(236, 190, 172)
    seam = [(ex + 0.035, ez + 0.4), (ex + 0.012, ez + 0.16), (ex - 0.005, ez - 0.06), (ex - 0.025, ez - 0.28)]
    p.paint.line([(x + 0.02, z) for x, z in seam], [0.003, 0.01, 0.008, 0.002], shade, 0.8)
    p.paint.line(seam, [0.008, 0.028, 0.024, 0.005], scar)
    p.nostrils(tuple(c * 0.45 for c in shade))
    p.nose_line(shade, -1)
    # The jaw set in a permanent tight line.
    p.mouth(INK, lip=tuple(c * 0.8 for c in blush), lip_alpha=0.3, line=0.013)
    p.under_lip(shade)
    for sign in (-1, 1):
        p.paint.line([(sign * 0.2, -0.36), (sign * 0.28, -0.5), (sign * 0.27, -0.62)], [0.003, 0.009, 0.002], shade)

    # Tally marks: four strokes struck through by a fifth, in rows from the right temple back over the skull.
    def tallies(x0, z0, step, height, groups, lean=0.0):
        for g in range(groups):
            gx = x0 + g * step * 5.6
            for j in range(4):
                x = gx + j * step
                p.paint.line([(x, z0), (x + lean, z0 + height)], 0.012, ink)
            p.paint.line([(gx - step * 0.5, z0 + height * 0.2), (gx + step * 3.5 + lean, z0 + height * 0.8)], 0.01, ink)

    tallies(-0.36, 0.66, -0.05, 0.13, 2, lean=-0.01)
    tallies(-0.56, 0.4, -0.045, 0.13, 2, lean=-0.01)
    tallies(-0.74, 0.12, -0.035, 0.12, 1)
    finish(p, skin, shade, neck=0.62)

    # ...and down the side of his neck.
    def on_neck(x, z):
        # In front of the neck and the traps that climb it.
        return (x, min(0.2 - 0.62 * math.sqrt(max(0.0, 1 - (x / 0.62) ** 2)), -0.3) - 0.04, z)

    for row, z in enumerate((-0.86, -1.08)):
        x0 = -0.32 - 0.04 * row
        for j in range(4):
            x = x0 - 0.05 * j
            p.sweep([on_neck(x, z), on_neck(x - 0.01, z - 0.13)], 0.012, ink, root=p.body_root, outline=0.0, seg=2)
        p.sweep([on_neck(x0 + 0.03, z - 0.03), on_neck(x0 - 0.19, z - 0.1)], 0.01, ink, root=p.body_root, outline=0.0, seg=2)

    # The bust: bare, heavy shoulders bursting out of a sleeveless linen shirt.
    linen, linen_shade = rgb(222, 212, 186), rgb(160, 148, 124)
    shoulders(p, 1.36, linen, neck=0.62, depth=0.9)
    for sign in (-1, 1):
        p.sweep([(sign * 0.45, -0.1, -0.85), (sign * 0.85, -0.1, -1.28), (sign * 1.4, -0.1, -1.6)], [0.22, 0.32, 0.3], skin, depth=0.9, root=p.body_root)
        p.ball((sign * 1.86, -0.1, -1.98), (0.64, 0.68, 0.6), skin, root=p.body_root)
        p.sweep([(sign * 1.36, -0.7, -1.7), (sign * 1.5, -0.84, -2.3), (sign * 1.66, -0.82, -2.7)], [0.012, 0.028, 0.012], shade, depth=0.3, root=p.body_root, outline=0.0)
    # Grime on the linen at the armholes.
    for sign in (-1, 1):
        p.sweep([(sign * 1.18, -0.6, -1.5), (sign * 1.28, -0.74, -2.1)], 0.06, linen_shade, depth=0.3, root=p.body_root, outline=0.0)

    # The scorched bull-hide apron: a bib on heavy straps and tarnished brass buckles.
    hide, hide_dark, brass = rgb(116, 72, 44), rgb(58, 38, 30), rgb(170, 132, 62)
    p.plate([(-0.6, -0.8, -1.72), (0.6, -0.8, -1.72), (0.78, -0.88, -2.95), (-0.78, -0.88, -2.95)], 0.06, hide, root=p.body_root)
    for sign in (-1, 1):
        p.sweep([(sign * 0.54, -0.82, -1.72), (sign * 0.56, -0.56, -1.36), (sign * 0.5, -0.2, -1.16)], 0.06, hide_dark, root=p.body_root)
        p.ball((sign * 0.54, -0.88, -1.76), (0.09, 0.03, 0.08), brass, gloss=0.7, root=p.body_root, outline=0.006)
    for x, z, rx, rz in ((0.28, -2.1, 0.16, 0.1), (-0.36, -2.55, 0.12, 0.14), (0.1, -1.86, 0.07, 0.05)):
        p.ball((x, -0.88, z), (rx, 0.02, rz), hide_dark, root=p.body_root, outline=0.0)

    # A cracked bandolier from his left shoulder across to his right hip: brass powder flasks and iron spikes.
    p.sweep([(1.28, -0.62, -1.42), (0.4, -0.98, -1.92), (-0.9, -1.0, -2.6)], 0.12, rgb(54, 38, 32), depth=0.3, root=p.body_root)
    for u in (0.3, 0.44, 0.58):
        x, z = 1.28 - 2.18 * u, -1.42 - 1.18 * u
        p.ball((x, -1.1, z - 0.04), (0.07, 0.05, 0.13), brass, gloss=0.85, root=p.body_root, outline=0.006)
        p.sweep([(x, -1.1, z + 0.08), (x, -1.1, z + 0.16)], 0.02, rgb(150, 156, 166), root=p.body_root, outline=0.004, seg=2)
    for k in range(3):
        x, z = 1.02 - 0.09 * k, -1.56 - 0.05 * k
        p.sweep([(x, -1.08, z + 0.14), (x + 0.03, -1.08, z - 0.2)], [0.022, 0.004], rgb(150, 156, 166), gloss=0.8, root=p.body_root, outline=0.004, seg=2)

    # The linstock, held upright in his right fist: an iron fork with the slow-match smouldering in it.
    wood, iron, ember, hot = rgb(96, 62, 38), rgb(64, 66, 74), rgb(255, 120, 36), rgb(255, 214, 120)
    x, top = -1.32, -0.74
    p.sweep([(x - 0.1, -1.25, -3.5), (x, -1.3, top)], 0.06, wood, root=p.body_root)
    for sign in (-1, 1):
        p.sweep([(x, -1.3, top - 0.02), (x + sign * 0.14, -1.3, top + 0.16), (x + sign * 0.12, -1.3, top + 0.34)], [0.035, 0.03, 0.02], iron, gloss=0.6, root=p.body_root)
    p.sweep([(x, -1.3, top), (x, -1.3, top + 0.38)], [0.03, 0.002], iron, gloss=0.6, root=p.body_root)
    p.sweep([(x, -1.32, top - 0.2), (x - 0.16, -1.34, top + 0.02), (x - 0.12, -1.34, top + 0.32)], 0.025, rgb(176, 146, 98), root=p.body_root)
    p.ball((x - 0.12, -1.36, top + 0.36), (0.07, 0.07, 0.07), ember, root=p.body_root, outline=0.006)
    p.ball((x - 0.125, -1.42, top + 0.365), (0.035, 0.035, 0.035), hot, root=p.body_root, outline=0.0)
    p.ball((x - 0.08, -1.28, -2.75), (0.26, 0.24, 0.34), skin, root=p.body_root)  # His fist round the shaft.


def brill(p):
    """Bosun Brill, a barrel of a man, inspecting a rigging block on deck. A weathered, ruddy face with a
    bulbous sea-worn nose, a rugged squint, and a faded indigo anchor on his right cheek. A bushy grizzled
    beard with beaded braids down his chest, a tarnished gold hoop, and a charcoal watch cap stuck with pins.
    A brass bosun's call on a hemp cord over an indigo-and-cream striped shirt, an open tar-stained navy
    waistcoat, and a coil of Manila rope over his right shoulder."""
    skin, shade, blush = rgb(222, 160, 122), rgb(150, 92, 84), rgb(226, 92, 72)
    p.s["smile"] = 0.05
    face(p, skin, shade, blush, rgb(70, 118, 170), rgb(120, 104, 90), inner=0.1, outer=0.14, thick=0.055, up=0.04, low=0.024, gaze=0.028, iris_r=0.048, lid=0.4, bags=0.8, skin_shade=shade)
    # Ruddy cheeks and nose, crow's feet from squinting into the wind, and the faded anchor tattoo.
    p.paint.blob(0, -0.33, 0.2, 0.13, rgb(214, 70, 58), 0.55)
    for sign in (-1, 1):
        p.paint.blob(sign * 0.42, -0.3, 0.16, 0.1, rgb(214, 96, 76), 0.35)
        for k in range(3):
            p.paint.line([(sign * 0.48, 0.02 + 0.03 * (k - 1)), (sign * 0.6, 0.04 + 0.07 * (k - 1))], [0.006, 0.002], shade)
    for x, z in ((0.06, -0.26), (-0.05, -0.31), (0.03, -0.36)):
        p.paint.blob(x, z, 0.035, 0.03, rgb(196, 64, 56), 0.5)
    tat = rgb(70, 90, 136)
    p.paint.line([(-0.5, -0.1), (-0.5, -0.36)], 0.009, tat)
    p.paint.line([(-0.56, -0.15), (-0.44, -0.15)], 0.008, tat)
    p.paint.line([(-0.6, -0.27), (-0.56, -0.36), (-0.5, -0.38), (-0.44, -0.36), (-0.4, -0.27)], 0.008, tat)
    p.paint.blob(-0.5, -0.09, 0.025, 0.025, tat, 0.8)
    finish(p, skin, shade, neck=0.56)
    gold_dark = rgb(178, 140, 64)
    p.ring((0.97, -0.12, -0.34), 0.085, 0.022, gold_dark, gloss=0.7, normal=(1, 0, 0))

    # A charcoal knitted watch cap with a turned-up cuff, ribbed, with a few rusted pins stuck in it.
    knit, cuff = rgb(62, 62, 70), rgb(44, 44, 52)
    rings = [_ellipse(0.84, 0.98, 0.42), _ellipse(0.86, 1.0, 0.7), _ellipse(0.76, 0.88, 0.98), _ellipse(0.4, 0.48, 1.12)]
    p.loft(_resample(rings, 4), knit)
    p.loft([_ellipse(0.89, 1.04, 0.36), _ellipse(0.89, 1.04, 0.64)], cuff, cap=False)
    for x in np.linspace(-0.7, 0.7, 11):
        p.sweep([(x, -0.97 * math.sqrt(max(0.05, 1 - (x / 0.9) ** 2)) - 0.02, 0.38), (x, -0.97 * math.sqrt(max(0.05, 1 - (x / 0.9) ** 2)) - 0.02, 0.62)], 0.01, rgb(34, 34, 40), outline=0.0, seg=3)
    rust_pin = rgb(150, 90, 58)
    for x, z, lean in ((0.5, 0.86, 0.12), (0.62, 0.74, 0.18), (-0.56, 0.8, -0.14)):
        p.sweep([(x, -0.72, z), (x + lean, -0.86, z + 0.22)], 0.012, rust_pin, outline=0.004, seg=3)
        p.ball((x + lean, -0.86, z + 0.22), 0.03, rgb(196, 188, 170), outline=0.004)

    # The bust: an open navy waistcoat over the striped shirt.
    navy, navy2, cream, indigo = rgb(40, 50, 84), rgb(28, 36, 62), rgb(232, 224, 202), rgb(58, 70, 128)
    shoulders(p, 1.92, navy, neck=0.66, depth=0.92)
    # The striped shirt in the open front, laid in front of the bust so it shows either side of the beard.
    p.plate([(-1.0, -0.8, -1.3), (1.0, -0.8, -1.3), (0.85, -0.98, -2.95), (-0.85, -0.98, -2.95)], 0.04, cream, root=p.body_root)
    for z in np.arange(-1.42, -2.95, -0.19):
        t = (-1.3 - z) / 1.65
        hw, y = 1.0 - 0.15 * t, -0.8 - 0.18 * t
        p.sweep([(-hw, y - 0.035, z), (hw, y - 0.035, z)], 0.055, indigo, root=p.body_root, outline=0.0, seg=4)
    # The waistcoat's open fronts, worn and stained.
    for sign in (-1, 1):
        p.plate([(sign * 0.95, -0.86, -1.26), (sign * 1.5, -0.72, -1.3), (sign * 1.55, -0.86, -2.95), (sign * 0.78, -1.06, -2.95)], 0.06, navy2, root=p.body_root)
    for k, (x, z) in enumerate(((0.98, -2.0), (0.93, -2.35), (0.88, -2.7))):
        p.ball((x, -1.06, z), (0.06, 0.03, 0.06), rgb(190, 150, 70) if k != 1 else rgb(160, 164, 170), gloss=0.7, root=p.body_root, outline=0.005)
    for x, z, r in ((-1.0, -2.3, 0.12), (1.2, -1.9, 0.09), (-0.84, -2.7, 0.08)):
        p.ball((x * 1.25, -1.02, z), (r, 0.02, r * 0.7), rgb(20, 22, 30), root=p.body_root, outline=0.0)  # Tar stains.

    # A coil of Manila rope over his right shoulder.
    rope, rope2 = rgb(200, 164, 104), rgb(160, 126, 76)
    for k in range(5):
        p.ring((-1.25 - 0.04 * k, -0.3 - 0.07 * k, -1.66 + 0.035 * k), 0.46, 0.055, rope if k % 2 else rope2, normal=(0.3, -0.85, 0.42), root=p.body_root, outline=0.006)

    # The bosun's call on a knotted hemp cord, left of the beard.
    cord = rgb(176, 150, 104)
    for sign in (-1, 1):
        p.sweep([(sign * 0.42, -0.62, -1.3), (0.62 if sign > 0 else 0.2, -0.86, -2.0), (0.62, -0.94, -2.3)], 0.016, cord, root=p.body_root, outline=0.004)
    brass = rgb(200, 158, 70)
    p.sweep([(0.62, -0.96, -2.3), (0.98, -1.0, -2.2)], [0.05, 0.035], brass, gloss=0.9, root=p.body_root)
    p.ball((1.02, -1.0, -2.24), 0.09, brass, gloss=0.9, root=p.body_root)

    # A bushy grizzled beard cascading down his chest, with beaded braids.
    grey, grey2, brown = rgb(172, 168, 160), rgb(136, 130, 124), rgb(112, 84, 62)
    # Many wavy locks of different lengths, grey with brown through it, so it reads bushy rather than striped.
    locks = []
    for k in range(13):
        x0 = -0.7 + 1.4 * k / 12
        drop = 1.9 + 0.45 * math.sin(k * 1.7) - 0.5 * abs(x0)
        locks.append((x0, drop, (grey, grey2, brown, grey, grey2, grey, brown, grey, grey2, grey, brown, grey2, grey)[k]))
    for k, (x0, drop, color) in enumerate(sorted(locks, key=lambda l: -abs(l[0]))):
        wave = 0.08 * math.sin(k * 2.3)
        p.sweep([(x0 * 1.05, -0.84, -0.42), (x0 * 1.1 + wave, -1.0, -0.42 - drop * 0.35), (x0 * 0.9 - wave, -1.1, -0.42 - drop * 0.7), (x0 * 0.7 + wave, -1.08, -0.42 - drop)],
                [0.14, 0.2, 0.15, 0.02], color, depth=0.55, outline=0.008)
    p.sweep([(-0.46, -1.04, -0.52), (-0.12, -1.1, -0.56), (0.0, -1.08, -0.6), (0.12, -1.1, -0.56), (0.46, -1.04, -0.52)], [0.04, 0.09, 0.07, 0.09, 0.04], brown, depth=0.5)
    # The bulbous, bumpy sea-worn nose.
    nose = rgb(222, 146, 116)
    p.ball((0, -0.98, -0.32), (0.15, 0.11, 0.13), nose)
    for x, z in ((0.08, -0.27), (-0.07, -0.36), (0.04, -0.39)):
        p.ball((x, -1.07, z), 0.045, rgb(214, 128, 102), outline=0.0)
    for x in (-0.18, 0.2):
        p.sweep([(x, -1.08, -1.7), (x * 1.1, -1.1, -2.2), (x * 1.2, -1.1, -2.55)], 0.04, grey2, outline=0.006, seg=6)
        p.ball((x * 1.1, -1.13, -2.25), 0.05, rgb(130, 136, 140), gloss=0.5, outline=0.005)
        p.sweep([(x * 1.2 - 0.05, -1.14, -2.42), (x * 1.2 + 0.05, -1.14, -2.44)], 0.018, cord, outline=0.0, seg=3)

    # In his huge hands, a heavy weathered rigging block he's turning over to inspect.
    wood, wood2, iron = rgb(128, 92, 60), rgb(92, 64, 44), rgb(96, 98, 104)
    bx, by, bz = -0.95, -1.55, -2.55
    p.ball((bx, by, bz), (0.3, 0.18, 0.4), wood, root=p.body_root)
    p.ball((bx, by - 0.12, bz - 0.02), (0.07, 0.05, 0.26), wood2, root=p.body_root, outline=0.0)
    p.ring((bx, by, bz + 0.44), 0.1, 0.03, iron, gloss=0.6, normal=(1, 0, 0), root=p.body_root)
    p.sweep([(bx - 0.06, by - 0.16, bz + 0.2), (bx - 0.4, by - 0.1, bz + 0.6), (bx - 0.9, by + 0.2, bz + 0.5)], 0.035, rope2, root=p.body_root, outline=0.005)
    for sign in (-1, 1):
        hx = bx + sign * 0.3
        p.ball((hx, by - 0.08, bz - 0.12), (0.2, 0.17, 0.2), skin, root=p.body_root)
        for k in range(3):
            p.ball((hx - sign * 0.08, by - 0.24, bz - 0.04 - 0.08 * k), (0.06, 0.05, 0.045), skin, root=p.body_root, outline=0.004)
        p.sweep([(hx + sign * 0.06, by - 0.24, bz - 0.22), (hx + sign * 0.02, by - 0.25, bz - 0.12)], 0.012, rgb(80, 100, 140), root=p.body_root, outline=0.0, seg=3)


def wren(p):
    """Sawbones, examining you like a specimen. A gaunt, hollow face on a shaved skull: razor cheekbones,
    sunken temples and pallid, parchment skin. Fine tally marks in neat rows across his right temple and down
    his corded neck. Black catgut sutures across his lower face and left jaw, hauling the corner of his mouth
    into a thin, calm smile. His left eye milky and scarred over, his right dark and unblinking. A leather
    headband with a flip-up brass loupe, a collarless linen shirt under a stained leather apron on brass rings,
    an apothecary bandolier of instruments and glowing vials, and a curved suture needle pinched in his
    left hand, trailing catgut."""
    skin, shade, blush = rgb(224, 204, 178), rgb(120, 102, 116), rgb(186, 140, 136)
    ink = rgb(22, 20, 26)
    ex, ez = p.s["eye_x"], p.s["eye_z"]
    p.s["smile"] = 0.0
    p.skull()
    p.base_skin(shade, blush)
    # Sunken temples and hollow cheeks under blade-sharp cheekbones; a grey shadow of shaved scalp.
    for sign in (-1, 1):
        p.paint.blob(sign * 0.66, 0.36, 0.16, 0.2, shade, 0.4, soft=0.8)
        p.paint.blob(sign * 0.46, -0.42, 0.16, 0.2, shade, 0.5, soft=0.7)
        p.paint.line([(sign * 0.24, -0.18), (sign * 0.48, -0.2), (sign * 0.64, -0.12)], [0.004, 0.012, 0.003], shade, 0.8)
        p.paint.blob(sign * 0.44, -0.12, 0.14, 0.05, rgb(240, 226, 204), 0.6, soft=0.6)
    p.paint.blob(0, 0.78, 0.66, 0.3, rgb(190, 180, 170), 0.35, soft=0.7)

    # His right eye (image left) dark and unblinking; his left a milky, scarred-over film.
    p.eye(-1, rgb(40, 30, 30), lid=0.1, up=0.072, low=0.034, gaze=(0.03, 0.0), bags=1.0, skin_shade=shade)
    p.eye(1, rgb(200, 204, 200), lid=0.42, up=0.07, low=0.034, gaze=(-0.01, -0.01), bags=1.0, skin_shade=shade)
    k = 1.22
    p.paint.blob(ex - 0.01, ez, 0.07 * k, 0.03 * k, rgb(230, 232, 226), 0.95, soft=0.4)
    p.paint.blob(ex - 0.01, ez, 0.035 * k, 0.02 * k, rgb(206, 210, 206), 0.6, soft=0.8)
    scar = rgb(206, 150, 146)
    p.paint.line([(ex + 0.1, ez + 0.2), (ex + 0.02, ez + 0.02), (ex - 0.06, ez - 0.16)], [0.004, 0.016, 0.004], scar)
    p.brow(-1, ink, inner=0.13, outer=0.12, thick=0.02)
    p.brow(1, ink, inner=0.13, outer=0.12, thick=0.02)
    p.nostrils(tuple(c * 0.45 for c in shade))
    p.nose_line(shade, -1)
    # A razor-thin mouth, its left corner hauled up by the sutures.
    mz = p.s["mouth_z"]
    p.paint.line([(-0.17, mz + 0.01), (0.0, mz - 0.005), (0.13, mz + 0.02), (0.2, mz + 0.07)], [0.006, 0.011, 0.01, 0.004], ink)
    p.paint.line([(-0.1, mz - 0.035), (0.1, mz - 0.03)], [0.002, 0.006, 0.002], rgb(150, 100, 104), 0.6)
    # The wound and its black catgut stitches, from the mouth's corner across the left jaw.
    wound = [(0.2, mz + 0.07), (0.3, mz - 0.01), (0.4, mz + 0.03), (0.5, mz - 0.07), (0.58, mz - 0.02)]
    p.paint.line(wound, [0.014, 0.018, 0.016, 0.014, 0.006], rgb(150, 66, 72))
    for (x0, z0), (x1, z1) in zip(wound, wound[1:]):
        for f in (0.3, 0.75):
            x, z = x0 + (x1 - x0) * f, z0 + (z1 - z0) * f
            dx, dz = z1 - z0, -(x1 - x0)
            n = math.hypot(dx, dz) / 0.05
            p.paint.line([(x - dx / n, z - dz / n), (x + dx / n, z + dz / n)], 0.009, ink)

    # Fine, clinical tally marks in neat rows across the right temple.
    def tallies(x0, z0, step, height, groups):
        for g in range(groups):
            gx = x0 + g * step * 5.6
            for j in range(4):
                p.paint.line([(gx + j * step, z0), (gx + j * step, z0 + height)], 0.007, ink)
            p.paint.line([(gx - step * 0.5, z0 + height * 0.2), (gx + step * 3.5, z0 + height * 0.8)], 0.006, ink)

    tallies(-0.24, 0.38, -0.032, 0.08, 2)
    tallies(-0.44, 0.26, -0.03, 0.08, 1)
    tallies(-0.58, 0.12, -0.028, 0.08, 1)
    finish(p, skin, shade, neck=0.3)

    # ...and down the corded neck.
    def on_neck(x, z):
        return (x, 0.2 - 0.3 * math.sqrt(max(0.0, 1 - (x / 0.3) ** 2)) - 0.02, z)

    for sign in (-1, 1):
        p.sweep([on_neck(sign * 0.2, -0.8), on_neck(sign * 0.06, -1.5)], [0.035, 0.03], skin, root=p.body_root, outline=0.004)
    for z in (-1.0, -1.2):
        for j in range(4):
            x = -0.14 - 0.03 * j
            p.sweep([on_neck(x, z), on_neck(x, z - 0.1)], 0.008, ink, root=p.body_root, outline=0.0, seg=2)
        p.sweep([on_neck(-0.12, z - 0.02), on_neck(-0.25, z - 0.08)], 0.007, ink, root=p.body_root, outline=0.0, seg=2)

    # A worn leather headband round the brow, the brass loupe flipped up on it.
    leather, brass = rgb(104, 66, 42), rgb(196, 152, 70)
    p.loft([_ellipse(0.71, 0.84, 0.52), _ellipse(0.65, 0.78, 0.7)], leather, cap=False)
    p.sweep([(-0.3, -0.8, 0.64), (-0.3, -1.0, 0.8)], [0.12, 0.13], brass, gloss=0.85, outline=0.008)
    p.ball((-0.3, -1.02, 0.82), (0.1, 0.03, 0.1), rgb(170, 210, 220), gloss=1.0, rot=(0.6, 0, 0))

    # The bust: a gaunt frame in a collarless linen shirt, the dark leather apron on brass rings.
    linen, apron = rgb(226, 218, 196), rgb(56, 38, 32)
    shoulders(p, 1.08, linen, neck=0.3, depth=0.68, slope=0.04)
    p.plate([(-0.46, -0.66, -1.62), (0.46, -0.66, -1.62), (0.58, -0.74, -2.95), (-0.58, -0.74, -2.95)], 0.05, apron, root=p.body_root)
    for sign in (-1, 1):
        p.ring((sign * 0.42, -0.74, -1.64), 0.07, 0.02, brass, gloss=0.8, root=p.body_root, outline=0.004)
        p.sweep([(sign * 0.42, -0.7, -1.58), (sign * 0.36, -0.4, -1.3), (sign * 0.26, -0.1, -1.12)], 0.045, apron, root=p.body_root)
    for x, z, rx, rz in ((0.2, -2.1, 0.14, 0.09), (-0.24, -2.5, 0.1, 0.12)):
        p.ball((x, -0.78, z), (rx, 0.02, rz), rgb(96, 30, 36), root=p.body_root, outline=0.0)
    # The apothecary bandolier, right shoulder to left hip: a scalpel, forceps and glowing vials.
    p.sweep([(-1.0, -0.5, -1.4), (-0.2, -0.86, -1.9), (0.9, -0.84, -2.6)], 0.1, rgb(130, 84, 52), depth=0.3, root=p.body_root)
    steel = rgb(196, 204, 212)
    p.sweep([(-0.68, -0.98, -1.5), (-0.7, -0.98, -1.78)], [0.02, 0.02], steel, gloss=0.9, root=p.body_root, outline=0.004, seg=2)
    p.sweep([(-0.68, -0.98, -1.5), (-0.66, -0.98, -1.4)], [0.025, 0.002], steel, gloss=0.9, root=p.body_root, outline=0.004, seg=2)
    for dx in (-0.025, 0.025):
        p.sweep([(-0.48 + dx, -0.98, -1.56), (-0.48, -0.98, -1.86)], 0.012, steel, gloss=0.9, root=p.body_root, outline=0.004, seg=2)
    for x, c in ((-0.18, rgb(110, 255, 150)), (0.06, rgb(214, 140, 50)), (0.3, rgb(110, 255, 150))):
        z = -1.9 - 0.55 * (x + 0.2)
        p.loft(_vial((x, -0.96, z)), c, gloss=0.9, root=p.body_root)

    # The curved suture needle, pinched up in his left hand, trailing black catgut.
    hand = rgb(214, 192, 168)
    p.ball((1.0, -1.1, -1.62), (0.2, 0.16, 0.24), hand, root=p.body_root)
    for k in range(3):
        p.sweep([(0.9 + 0.06 * k, -1.2, -1.5), (0.84 + 0.05 * k, -1.26, -1.2 - 0.04 * k)], [0.05, 0.04], hand, root=p.body_root, outline=0.006)
        p.sweep([(0.84 + 0.05 * k, -1.26, -1.2 - 0.04 * k), (0.835 + 0.05 * k, -1.27, -1.14 - 0.04 * k)], [0.04, 0.035], rgb(150, 76, 54), root=p.body_root, outline=0.006)
    arc = [(0.86 + 0.13 * math.cos(a), -1.3, -1.06 + 0.13 * math.sin(a)) for a in np.linspace(-0.4, 2.6, 6)]
    p.sweep(arc, [0.012, 0.014, 0.014, 0.012, 0.008, 0.002], steel, gloss=1.0, root=p.body_root, outline=0.004)
    p.sweep([arc[0], (1.06, -1.32, -1.4), (0.98, -1.34, -1.9), (1.1, -1.34, -2.5)], 0.008, ink, root=p.body_root, outline=0.0)


def ivo(p):
    """The jittery trainee stormcaller. Huge glassy eyes, a static-charged bush of dark frizz with a burnt-white
    streak down his right side, one brow half singed away, soot and a branching Lichtenberg scar on his right
    cheek, a slack, breathless mouth. A singed linen high collar under an oilskin coat far too big for him,
    a patchwork vest laced with copper mesh, and harness straps hung with a jar of trapped lightning."""
    skin, shade, blush = rgb(214, 166, 132), rgb(128, 92, 110), rgb(226, 120, 112)
    p.s["smile"] = -0.02
    face(p, skin, shade, blush, rgb(150, 214, 255), rgb(46, 32, 26), inner=0.25, outer=0.19, thick=0.022, up=0.12, low=0.075, iris_r=0.064, gaze=0.02)
    p.mouth(INK, open_amt=0.09, line=0.009)
    # His right brow (the viewer's left), burnt away at the outer end, with a few charred flecks.
    p.paint.blob(-0.46, 0.2, 0.075, 0.05, skin, 1.0, soft=0.5)
    for x, z in ((-0.42, 0.205), (-0.45, 0.19), (-0.44, 0.215)):
        p.paint.blob(x, z, 0.008, 0.008, rgb(40, 28, 26), 0.8, soft=0.3)
    # Soot smudges, and a Lichtenberg scar branching down his right cheek to the jaw.
    for x, z, rx, rz, a in ((0.4, -0.24, 0.12, 0.06, 0.3), (0.12, 0.38, 0.1, 0.04, 0.22), (-0.06, -0.62, 0.08, 0.04, 0.25)):
        p.paint.blob(x, z, rx, rz, rgb(70, 58, 64), a)
    scar = rgb(206, 92, 92)
    p.paint.line([(-0.34, -0.06), (-0.4, -0.22), (-0.38, -0.4), (-0.42, -0.6)], [0.013, 0.011, 0.009, 0.004], scar, 0.95)
    for start, end in (((-0.4, -0.22), (-0.5, -0.3)), ((-0.39, -0.32), (-0.3, -0.42)), ((-0.38, -0.4), (-0.48, -0.5)), ((-0.4, -0.5), (-0.33, -0.6))):
        mid = ((start[0] + end[0]) / 2 + 0.015, (start[1] + end[1]) / 2)
        p.paint.line([start, mid, end], [0.008, 0.006, 0.002], scar, 0.9)
    finish(p, skin, shade, neck=0.22)

    dark, bolt, singed = rgb(54, 38, 30), rgb(236, 246, 255), rgb(190, 196, 204)
    hair_cap(p, dark, line=0.55, curve=0.14, nape=-0.3, inflate=0.06)
    for k, a in enumerate(np.linspace(0.3, math.pi - 0.3, 15)):
        x, z = math.cos(a) * 0.68, 0.48 + math.sin(a) * 0.52
        L = 0.85 + 0.25 * math.sin(k * 2.3)
        color = bolt if k in (10, 11) else dark
        p.sweep([(x, 0.0, z), (x * 1.46 + 0.04 * math.sin(k * 7.0), 0.06, z + 0.5 * L), (x * 1.86, 0.1, z + 0.9 * L)], [0.15, 0.1, 0.004], color, depth=0.6)
    # The streak cascades down his right temple, its ends frayed and singed.
    p.sweep([(-0.6, -0.12, 0.5), (-0.74, -0.14, 0.22), (-0.8, -0.1, -0.06)], [0.11, 0.08, 0.01], bolt, depth=0.5)
    for dz, dx in ((0.0, -0.04), (0.06, 0.03)):
        p.sweep([(-0.8, -0.1, -0.02 + dz), (-0.88 + dx, -0.1, -0.12 + dz)], [0.02, 0.003], singed, depth=0.4)

    # An oilskin coat cut for someone twice his size, worn open over the vest.
    oilskin, oilskin_light = rgb(58, 72, 94), rgb(96, 114, 140)
    coat(p, 1.34, oilskin, oilskin_light, rgb(118, 76, 46), gap=0.3, neck=0.32)
    for x, z in ((-0.86, -1.9), (0.92, -2.2)):
        p.plate([(x - 0.12, -0.56, z + 0.1), (x + 0.12, -0.56, z + 0.1), (x + 0.12, -0.6, z - 0.12), (x - 0.12, -0.6, z - 0.12)], 0.02, rgb(150, 132, 106), root=p.body_root)
    # Copper mesh woven through the patchwork vest.
    for z in (-1.7, -1.95, -2.2):
        p.sweep([(-0.24, -0.84, z), (0.0, -0.88, z - 0.02), (0.24, -0.84, z)], 0.028, rgb(190, 102, 54), gloss=0.6, root=p.body_root)
    # A singed linen high collar standing up round his thin neck.
    p.sweep([(-0.3, -0.3, -1.2), (-0.22, -0.46, -1.3), (0.0, -0.52, -1.33), (0.22, -0.46, -1.3), (0.3, -0.3, -1.2)], [0.05, 0.06, 0.06, 0.06, 0.05], rgb(226, 212, 176), root=p.body_root)
    # Harness straps crossing his chest, one hung with a jar of trapped lightning.
    for sign in (1, -1):
        p.sweep([(sign * 0.62, -0.7, -1.4), (0.0, -0.94, -1.95), (-sign * 0.5, -0.86, -2.5)], 0.055, rgb(46, 32, 28), root=p.body_root)
    p.ball((0.36, -1.0, -2.16), (0.09, 0.07, 0.13), rgb(214, 236, 255), gloss=0.9, root=p.body_root)
    p.ball((0.36, -1.0, -2.0), (0.08, 0.06, 0.04), rgb(186, 142, 62), gloss=0.7, root=p.body_root)


def hale(p):
    """Commodore Hale, who wrote the Armada's gun drills and signed Rook's court-martial. A long, pinched old face
    held perfectly still, chin up, looking down the nose at you as if you were a misfiled form. Thin lips pressed
    flat, steel-grey eyes under heavy disapproving brows, grey mutton-chop sideburns and a clipped moustache. A
    peaked cap with a mirror-polished badge, a gilded-navy greatcoat with gold epaulettes, and the red leather drill
    book clamped against his chest, its ribbon marking page forty."""
    skin, shade, blush = rgb(226, 184, 156), rgb(140, 104, 112), rgb(214, 128, 112)
    grey = rgb(196, 198, 204)
    face(p, skin, shade, blush, rgb(130, 146, 162), grey, inner=0.24, outer=0.06, thick=0.05, lid=0.5, up=0.06, low=0.03, gaze=-0.04, lip_alpha=0.25, bags=0.8, skin_shade=shade)
    for z in (0.32, 0.4):
        p.paint.line([(-0.24, z), (0, z - 0.015), (0.24, z)], 0.004, shade, 0.6)
    for sign in (-1, 1):
        p.paint.line([(sign * 0.2, -0.36), (sign * 0.3, -0.62)], [0.002, 0.005, 0.001], shade)
    finish(p, skin, shade, neck=0.32)
    # Mutton chops: down each cheek from the temple to the jaw, stopping short of the chin.
    for sign in (-1, 1):
        p.sweep([(sign * 0.64, -0.74, 0.12), (sign * 0.66, -0.82, -0.3), (sign * 0.54, -0.92, -0.66), (sign * 0.36, -0.99, -0.74)], [0.07, 0.12, 0.11, 0.035], grey, depth=0.6)
    # A clipped moustache, trimmed to regulation.
    for sign in (-1, 1):
        p.sweep([(sign * 0.03, -1.03, -0.43), (sign * 0.22, -1.02, -0.47), (sign * 0.34, -0.96, -0.5)], [0.04, 0.06, 0.02], grey, depth=0.6)
    gold = rgb(240, 196, 84)
    peaked_cap(p, rgb(30, 42, 92), gold, badge=gold)
    coat(p, 1.4, rgb(32, 44, 96), rgb(232, 232, 236), rgb(236, 236, 240), gap=0.24, neck=0.44)
    epaulettes(p, 1.4, gold)
    # The red drill book, held flat against his chest, page forty marked.
    red, page = rgb(160, 30, 40), rgb(236, 224, 196)
    p.plate([(-0.98, -0.98, -1.62), (-0.18, -0.98, -1.52), (-0.15, -0.98, -2.6), (-0.95, -0.98, -2.7)], 0.08, red, root=p.body_root, outline=0.008)
    p.plate([(-0.93, -1.0, -1.65), (-0.23, -1.0, -1.57), (-0.2, -1.0, -1.67), (-0.91, -1.0, -1.75)], 0.02, page, root=p.body_root, outline=0.0)
    p.sweep([(-0.52, -1.04, -1.58), (-0.49, -1.04, -2.0), (-0.54, -1.04, -2.2)], 0.025, gold, root=p.body_root, outline=0.0)


def _spec(build, dark, light, rim, rival=False, motif="rays", turn=0.28, tilt=0.03, pitch=0.0, body_turn=0.1, span=4.2, target=-0.42, shadow=rgb(108, 94, 148), **shape):
    side = -1 if rival else 1
    return dict(build=build, dark=dark, light=light, rim=rim, shadow=shadow, key_side=side, turn=turn * side, tilt=tilt, pitch=pitch,
                body_turn=body_turn * side, motif=motif, span=span, target=(0, 0, target), shape=shape)


CAST["Vane"].update(span=4.6, target=(0, 0, -0.32))
CAST["VaneCaptain"] = dict(CAST["Vane"], build=vane_captain)
CAST["VaneKing"] = dict(CAST["Vane"], build=vane_king, span=5.2, target=(0, 0, -0.05))
CAST["Lyra"].update(span=5.1, target=(0, 0, -0.7))
CAST["Thorne"].update(span=4.7, target=(0, 0, -0.4))
CAST["Krag"].update(span=5.4, target=(0, 0, -0.75))
CAST.update({
    "Rook": _spec(rook, rgb(38, 56, 104), rgb(216, 148, 66), rgb(255, 180, 92), motif="flak", turn=0.2, tilt=-0.02, pitch=0.02, span=5.4, target=-0.72,
                  crown=0.76, temple=0.8, cheek=0.82, jaw=0.86, chin=0.5, depth=0.94, brow_ridge=0.08, socket=0.07, nose_len=0.4, nose_bridge=0.15, nose_tip=0.19, nose_width=0.15, mouth_w=0.28, mouth_z=-0.62, chin_jut=0.07, eye_x=0.33),
    "Sable": _spec(sable, rgb(10, 16, 36), rgb(120, 150, 196), rgb(170, 210, 240), motif="moonharbor", turn=0.3, tilt=0.03, pitch=0.08, span=5.2, target=-0.68,
                   crown=0.68, temple=0.68, cheek=0.66, jaw=0.56, chin=0.32, depth=0.84, nose_len=0.3, nose_bridge=0.03, nose_tip=0.03, nose_width=0.08, eye_x=0.3, eye_bulge=0.02, socket=0.03, lip_top=0.0, lip_low=0.0, chin_jut=0.0, cheekbone=0.02),
    "Morrow": _spec(morrow, rgb(22, 62, 50), rgb(214, 196, 130), rgb(236, 220, 150), motif="chart", turn=0.24, tilt=0.05, pitch=-0.05, span=5.0, target=-0.12,
                    crown=0.74, temple=0.76, cheek=0.76, jaw=0.76, chin=0.46, chin_z=-1.1, depth=0.88, cheekbone=0.05, nose_len=0.46, nose_bridge=0.18, nose_tip=0.11, nose_width=0.09, mouth_w=0.2, mouth_z=-0.66, smile=0.06, smirk=0.16, lip_top=0.01, lip_low=0.014, eye_x=0.31),
    "CassianPirate": _spec(cassian_pirate, rgb(140, 26, 34), rgb(240, 194, 104), rgb(255, 214, 120), rival=False, motif="rays", turn=-0.16, tilt=-0.04, pitch=-0.03, body_turn=-0.06, span=5.0, target=-0.32,
                           crown=0.76, temple=0.8, cheek=0.8, jaw=0.76, chin=0.46, depth=0.94, brow_ridge=0.08, socket=0.06, nose_len=0.42, nose_bridge=0.22, nose_tip=0.18, nose_width=0.12, nose_hook=0.03, mouth_w=0.27, mouth_z=-0.6, eye_x=0.33),
    "CassianAdmiral": _spec(cassian_admiral, rgb(24, 36, 84), rgb(226, 186, 90), rgb(255, 224, 150), rival=True, motif="rays", turn=0.12, tilt=0.0, pitch=-0.09, body_turn=0.05, span=5.2, target=-0.2,
                            crown=0.76, temple=0.8, cheek=0.78, jaw=0.76, chin=0.46, depth=0.94, brow_ridge=0.08, socket=0.08, nose_len=0.42, nose_bridge=0.22, nose_tip=0.18, nose_width=0.12, nose_hook=0.03, mouth_w=0.24, mouth_z=-0.6, eye_x=0.33),
    "Vex": _spec(vex, rgb(62, 24, 104), rgb(196, 120, 250), rgb(226, 170, 255), rival=True, motif="slash_l", turn=0.26, tilt=-0.09, pitch=-0.06, span=4.6, target=-0.36,
                 crown=0.68, temple=0.7, cheek=0.7, jaw=0.54, chin=0.28, depth=0.86, cheekbone=0.1, hollow=0.05, nose_len=0.4, nose_bridge=0.18, nose_tip=0.1, nose_width=0.08, mouth_w=0.22, mouth_z=-0.6, lip_low=0.035, eye_x=0.3),
    "Vesper": _spec(vesper, rgb(14, 76, 82), rgb(70, 206, 196), rgb(120, 255, 236), rival=True, motif="slash_r", turn=0.26, tilt=0.09, pitch=0.03, span=4.6, target=-0.36,
                    crown=0.68, temple=0.7, cheek=0.7, jaw=0.54, chin=0.28, depth=0.86, cheekbone=0.1, hollow=0.05, nose_len=0.4, nose_bridge=0.18, nose_tip=0.1, nose_width=0.08, mouth_w=0.22, mouth_z=-0.6, lip_low=0.035, eye_x=0.3),
    "Malakor": _spec(malakor, rgb(36, 34, 46), rgb(236, 106, 38), rgb(255, 140, 60), rival=True, motif="bars", turn=0.2, tilt=0.0, pitch=0.06, body_turn=0.08, span=5.7, target=-0.55),
    "ArmadaSoldier": _spec(armada_soldier, rgb(30, 46, 96), rgb(160, 176, 214), rgb(200, 216, 255), rival=True, motif="rays", turn=0.2, tilt=0.02, span=5.5, target=0.0,
                           crown=0.68, temple=0.7, cheek=0.7, jaw=0.58, chin=0.32, chin_z=-1.02, depth=0.84, brow_ridge=0.02, nose_len=0.32, nose_bridge=0.1, nose_tip=0.12, nose_width=0.1, nose_snub=0.02, mouth_w=0.17, mouth_z=-0.56, eye_x=0.31),
    "ArmadaOfficer": _spec(armada_officer, rgb(30, 46, 96), rgb(226, 186, 90), rgb(255, 224, 150), rival=True, motif="rays", turn=0.2, tilt=0.03, pitch=-0.13, span=4.7, target=-0.24,
                           crown=0.74, temple=0.76, cheek=0.76, jaw=0.68, chin=0.36, depth=0.92, nose_len=0.45, nose_bridge=0.24, nose_tip=0.15, nose_width=0.11, nose_hook=0.03, mouth_w=0.2, mouth_z=-0.63, smile=-0.03, eye_x=0.32),
    "Hale": _spec(hale, rgb(30, 46, 96), rgb(196, 70, 70), rgb(255, 200, 170), rival=True, motif="bars", turn=0.18, tilt=0.02, pitch=-0.14, span=4.8, target=-0.3,
                  crown=0.72, temple=0.72, cheek=0.7, jaw=0.62, chin=0.38, chin_z=-1.14, depth=0.9, hollow=0.06, cheekbone=0.1, nose_len=0.48, nose_bridge=0.24, nose_tip=0.12, nose_width=0.1, nose_hook=0.04, mouth_w=0.2, mouth_z=-0.66, smile=-0.06, eye_x=0.31),
    "RoyalGuard": _spec(royal_guard, rgb(120, 26, 40), rgb(226, 186, 90), rgb(255, 214, 130), rival=True, motif="rays", turn=0.16, tilt=0.0, pitch=0.0, span=5.8, target=0.0,
                        crown=0.74, temple=0.74, cheek=0.74, jaw=0.68, chin=0.4, depth=0.92, brow_ridge=0.08, socket=0.07, nose_len=0.4, nose_bridge=0.14, nose_tip=0.15, nose_width=0.13, mouth_w=0.24, mouth_z=-0.6, eye_x=0.32),
    "Tobin": _spec(tobin, rgb(32, 78, 120), rgb(208, 196, 150), rgb(240, 226, 160), motif="clouds", turn=0.24, tilt=-0.05, span=4.7, target=-0.26,
                   crown=0.74, temple=0.76, cheek=0.76, jaw=0.68, chin=0.4, depth=0.9, nose_len=0.42, nose_bridge=0.16, nose_tip=0.2, nose_width=0.15, mouth_w=0.25, mouth_z=-0.62, eye_x=0.32),
    "Mirren": _spec(mirren, rgb(150, 30, 40), rgb(248, 190, 74), rgb(255, 214, 110), motif="flak", turn=0.2, tilt=0.16, pitch=-0.09, span=5.0, target=-0.3,
                    crown=0.72, temple=0.74, cheek=0.78, jaw=0.66, chin=0.4, depth=0.88, cheekbone=0.09, nose_len=0.34, nose_bridge=0.1, nose_tip=0.14, nose_width=0.11, nose_snub=0.02, mouth_w=0.31, mouth_z=-0.58, eye_x=0.32),
    "Odessa": _spec(odessa, rgb(36, 84, 66), rgb(150, 216, 170), rgb(190, 255, 200), motif="gears", turn=0.22, tilt=-0.05, span=4.7, target=-0.3,
                    crown=0.7, temple=0.74, cheek=0.76, jaw=0.66, chin=0.4, depth=0.9, nose_len=0.38, nose_bridge=0.13, nose_tip=0.16, nose_width=0.14, mouth_w=0.22, mouth_z=-0.61, eye_x=0.32),
    "Ashgrave": _spec(ashgrave, rgb(52, 26, 92), rgb(186, 126, 240), rgb(216, 180, 255), rival=True, motif="current", turn=0.24, tilt=0.06, pitch=-0.05, span=4.8, target=-0.32,
                      crown=0.66, temple=0.68, cheek=0.62, jaw=0.5, chin=0.26, chin_z=-1.18, depth=0.82, hollow=0.06, cheekbone=0.05, nose_len=0.48, nose_bridge=0.22, nose_tip=0.1, nose_width=0.08, mouth_w=0.14, mouth_z=-0.7, eye_x=0.3),
    "Thrace": _spec(thrace, rgb(22, 90, 76), rgb(120, 220, 170), rgb(190, 255, 216), rival=True, motif="current", turn=0.3, tilt=0.07, pitch=-0.09, span=5.4, target=0.0,
                    crown=0.68, temple=0.7, cheek=0.7, jaw=0.54, chin=0.28, depth=0.86, cheekbone=0.11, hollow=0.05, nose_len=0.38, nose_bridge=0.14, nose_tip=0.1, nose_width=0.08, mouth_w=0.2, mouth_z=-0.6, lip_top=0.032, lip_low=0.04, eye_x=0.31),
    "Gorse": _spec(gorse, rgb(104, 60, 28), rgb(232, 178, 80), rgb(255, 204, 110), rival=True, motif="rust", turn=0.24, tilt=-0.1, pitch=-0.08, span=5.3, target=-0.18,
                   crown=0.74, temple=0.78, cheek=0.84, jaw=0.8, chin=0.48, depth=0.94, cheekbone=0.05, nose_len=0.4, nose_bridge=0.14, nose_tip=0.25, nose_width=0.17, mouth_w=0.33, mouth_z=-0.6, eye_x=0.33),
    "CaptainRia": _spec(captain_ria, rgb(24, 96, 136), rgb(246, 204, 100), rgb(255, 228, 140), motif="clouds", turn=0.22, tilt=-0.09, pitch=-0.05, span=4.4, target=-0.36,
                        crown=0.7, temple=0.72, cheek=0.72, jaw=0.62, chin=0.36, depth=0.88, cheekbone=0.08, nose_len=0.36, nose_bridge=0.14, nose_tip=0.13, nose_width=0.1, mouth_w=0.27, mouth_z=-0.58, eye_x=0.31),
    "Scrapper": _spec(scrapper, rgb(90, 52, 28), rgb(190, 150, 60), rgb(226, 190, 90), rival=True, motif="rust", turn=0.2, tilt=0.09, span=5.2, target=-0.14,
                      crown=0.68, temple=0.72, cheek=0.68, jaw=0.6, chin=0.3, depth=0.86, hollow=0.06, nose_len=0.36, nose_bridge=0.1, nose_tip=0.2, nose_width=0.15, nose_skew=0.04, mouth_w=0.26, mouth_z=-0.58, smirk=0.12, eye_x=0.32),
    "Runner": _spec(runner, rgb(16, 92, 86), rgb(90, 216, 180), rgb(150, 255, 216), motif="wind", turn=0.38, tilt=0.02, span=4.8, target=-0.34,
                    crown=0.68, temple=0.7, cheek=0.68, jaw=0.56, chin=0.3, depth=0.84, nose_len=0.36, nose_bridge=0.14, nose_tip=0.1, nose_width=0.09, mouth_w=0.19, mouth_z=-0.58, eye_x=0.31),
    "Hask": _spec(hask, rgb(110, 26, 34), rgb(180, 120, 100), rgb(230, 170, 150), motif="flak", turn=0.16, tilt=0.0, pitch=0.08, span=4.4, target=-0.42,
                  crown=0.72, temple=0.74, cheek=0.74, jaw=0.72, chin=0.44, depth=0.9, brow_ridge=0.09, socket=0.07, nose_len=0.38, nose_bridge=0.13, nose_tip=0.14, nose_width=0.12, nose_skew=-0.05, mouth_w=0.24, mouth_z=-0.61, eye_x=0.32),
    "Brill": _spec(brill, rgb(40, 56, 94), rgb(200, 184, 130), rgb(236, 220, 160), motif="deck", turn=0.2, tilt=-0.05, span=6.2, target=-1.15,
                   crown=0.72, temple=0.8, cheek=0.92, jaw=0.94, chin=0.52, depth=0.96, cheekbone=0.03, nose_len=0.4, nose_bridge=0.1, nose_tip=0.36, nose_width=0.25, mouth_w=0.27, mouth_z=-0.61, eye_x=0.33),
    "Wren": _spec(wren, rgb(32, 72, 58), rgb(150, 216, 170), rgb(190, 255, 210), motif="gears", turn=-0.18, tilt=0.08, pitch=-0.03, span=4.5, target=-0.36,
                  crown=0.66, temple=0.64, cheek=0.64, jaw=0.48, chin=0.26, chin_z=-1.14, depth=0.84, hollow=0.12, cheekbone=0.14, nose_len=0.42, nose_bridge=0.18, nose_tip=0.1, nose_width=0.08, mouth_w=0.2, mouth_z=-0.66, eye_x=0.3),
    "Ivo": _spec(ivo, rgb(24, 66, 136), rgb(170, 216, 255), rgb(214, 240, 255), motif="storm", turn=0.2, tilt=-0.06, pitch=-0.05, span=5.2, target=-0.2,
                 crown=0.7, temple=0.72, cheek=0.68, jaw=0.54, chin=0.3, chin_z=-1.02, depth=0.84, nose_len=0.3, nose_bridge=0.08, nose_tip=0.1, nose_width=0.09, nose_snub=0.02, mouth_w=0.15, mouth_z=-0.57, eye_x=0.32),
})

CAST["Sable"]["skin"] = (0.66, 0.62, 0.6)
CAST["Ashgrave"]["skin"] = (0.9, 0.88, 0.9)  # Powdered chalk-white.
CAST["Lyra"]["skin"] = (0.7, 0.47, 0.32)
