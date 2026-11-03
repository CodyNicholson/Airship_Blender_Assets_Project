"""Shattered Skies cast. Same skeleton and clips as the base crew, so every character can use every
animation, but each one is built to be recognised by silhouette alone at phone size.

A character is a Hero: body proportions plus an ordered list of (feature, *args) entries. Features
are small mesh functions bound to the bone they should follow.
"""
import dataclasses
import math
from dataclasses import dataclass, field

from mathutils import Matrix, Vector

import characters as base


@dataclass
class Hero:
    scale: float = 1.0
    width: float = 1.0
    girth: float = 1.0
    skin: str = "skin_mid"
    hair: str = "hair_brown"
    top: str = "cloth_white"
    legs: str = "cloth_brown"
    boots: str = "leather_dark"
    belt: str = "leather"
    sleeve: str = None  # Upper arm; None uses top.
    forearm: str = None  # None uses sleeve.
    glove: str = None  # None shows bare hands.
    brow: int = 0  # >0 angry, <0 worried.
    arm_bulk: float = 1.0  # Thicker arms than the body's girth alone gives.
    leg_bulk: float = 1.0
    mouth: bool = True  # False when a mask covers it.
    iris: str = None  # A coloured iris for characters whose eyes are the point. None uses plain dark pupils.
    sclera: str = "eye_white"
    features: list = field(default_factory=list)


class Ctx:
    def __init__(self, mb, hero, joints, hq, q):
        self.mb, self.hero, self.joints, self.hq, self.q = mb, hero, joints, hq, q
        self.s, self.w, self.g = hero.scale, hero.width, hero.girth
        self.centre = Vector((0, 0, 1.56 * self.s))


def _at(ctx, x, y, z):
    return ctx.centre + Vector((x, y, z)) * ctx.s


def _body_ring(ctx, rx, ry, z, sides):
    s, w, g = ctx.s, ctx.w, ctx.g
    ring = []
    for j in range(sides):
        a = 2 * math.pi * (j + 0.5) / sides
        ring.append((rx * w * s * math.cos(a), ry * g * s * math.sin(a), z * s))
    return ring


# ---- face and hair --------------------------------------------------------------------------

def hair_cap(ctx, _color=None):
    h = ctx.hq
    with ctx.mb.bound_to("head"):
        ctx.mb.sphere(_at(ctx, 0, 0.04, 0.06), 0.208 * ctx.s, ctx.q["head_s"], ctx.q["head_r"], ctx.hero.hair, smooth=h)


def hair_wild(ctx):
    """Vane: swept-back shards, the shape of someone always in the wind."""
    hair_cap(ctx)
    n = 7 if ctx.hq else 3
    with ctx.mb.bound_to("head"):
        for i in range(n):
            a = -1.15 + 2.3 * (i / max(1, n - 1))
            x, z = 0.17 * math.sin(a), 0.17 * math.cos(a) + 0.1
            ctx.mb.plate([_at(ctx, x - 0.06, -0.02, z), _at(ctx, x + 0.06, -0.02, z), _at(ctx, x * 1.35, 0.34, z + 0.09)], 0.05 * ctx.s, ctx.hero.hair)


def hair_long(ctx, length=0.42):
    hair_cap(ctx)
    with ctx.mb.bound_to("chest"):
        rows = [(0.17, 0.0), (0.2, -0.2), (0.17, -length)]
        sides = 8 if ctx.hq else 4
        rings = []
        for rx, dz in rows:
            ring = []
            for j in range(sides):
                a = math.pi * j / (sides - 1)
                ring.append(_at(ctx, rx * math.cos(a), 0.11 + 0.1 * math.sin(a), dz))
            rings.append(ring)
        ctx.mb.loft(rings, ctx.hero.hair, smooth=ctx.hq)


def hair_braid(ctx):
    """Lyra: one long braid over the shoulder. Bound to the chest, so it doesn't clip when she turns."""
    hair_cap(ctx)
    points = [_at(ctx, 0.16, 0.06, -0.02), _at(ctx, 0.21, 0.02, -0.13), _at(ctx, 0.25, -0.03, -0.26), _at(ctx, 0.27, -0.08, -0.38), _at(ctx, 0.27, -0.11, -0.5), _at(ctx, 0.26, -0.13, -0.6)]
    with ctx.mb.bound_to("chest"):
        # Separate plaits, so it reads as a braid and not as one long blade.
        charm = _at(ctx, 0.26, -0.135, -0.68)
        ctx.mb.path(points + [charm], [0.026 * ctx.s] * (len(points) + 1), 4, ctx.hero.hair)  # The core that holds it together.
        for k, at in enumerate(points if ctx.hq else points[::2]):
            size = (0.058 - 0.005 * k * (1 if ctx.hq else 2)) * ctx.s
            ctx.mb.sphere(at, (size, size, size * 1.35), 6 if ctx.hq else 4, 3, ctx.hero.hair, smooth=False)
        ctx.mb.sphere(charm, 0.03 * ctx.s, 6 if ctx.hq else 4, 3, "gold", smooth=False)


def hair_ponytail(ctx):
    hair_cap(ctx)
    with ctx.mb.bound_to("head"):
        ctx.mb.path([_at(ctx, 0, 0.2, 0.09), _at(ctx, 0, 0.33, 0.05), _at(ctx, 0, 0.34, -0.2), _at(ctx, 0, 0.3, -0.34)], [0.05 * ctx.s, 0.06 * ctx.s, 0.05 * ctx.s, 0.012 * ctx.s], 6 if ctx.hq else 3, ctx.hero.hair)


def hair_slick(ctx):
    """Morrow: neat and combed back, with a sharp widow's peak."""
    hair_cap(ctx)
    with ctx.mb.bound_to("head"):
        ctx.mb.plate([_at(ctx, -0.1, -0.164, 0.12), _at(ctx, 0.1, -0.164, 0.12), _at(ctx, 0, -0.186, 0.05)], 0.025 * ctx.s, ctx.hero.hair)


def hair_side_shave(ctx, mirrored=False):
    """Vex & Vesper: mirrored undercuts so the twins read as a pair but never as one."""
    sign = -1 if mirrored else 1
    hair_cap(ctx)
    with ctx.mb.bound_to("head"):
        ctx.mb.path([_at(ctx, sign * 0.1, 0.0, 0.2), _at(ctx, sign * 0.23, 0.02, 0.1), _at(ctx, sign * 0.27, -0.02, -0.13), _at(ctx, sign * 0.24, -0.04, -0.32)], [0.06 * ctx.s, 0.08 * ctx.s, 0.06 * ctx.s, 0.012 * ctx.s], 6 if ctx.hq else 3, ctx.hero.hair)


def hair_gray_sides(ctx):
    """Thorne: wispy mad-scientist tufts around a bald crown."""
    with ctx.mb.bound_to("head"):
        for sign in (1, -1):
            ctx.mb.sphere(_at(ctx, sign * 0.2, 0.04, 0.03), (0.07 * ctx.s, 0.1 * ctx.s, 0.09 * ctx.s), 6 if ctx.hq else 4, 3, ctx.hero.hair, smooth=False)
        if ctx.hq:
            for sign in (1, -1):
                ctx.mb.plate([_at(ctx, sign * 0.21, 0.08, 0.1), _at(ctx, sign * 0.3, 0.1, 0.19), _at(ctx, sign * 0.24, 0.0, 0.12)], 0.03 * ctx.s, ctx.hero.hair)


def beard_full(ctx, length=0.33):
    with ctx.mb.bound_to("head"):
        pts = [(-0.14, -0.1, -0.06), (0.14, -0.1, -0.06), (0.11, -0.16, -length * 0.72), (0, -0.19, -length), (-0.11, -0.16, -length * 0.72)]
        ctx.mb.plate([_at(ctx, *p) for p in pts], 0.09 * ctx.s, ctx.hero.hair)


def goatee(ctx):
    with ctx.mb.bound_to("head"):
        ctx.mb.plate([_at(ctx, -0.04, -0.17, -0.13), _at(ctx, 0.04, -0.17, -0.13), _at(ctx, 0, -0.17, -0.27)], 0.04 * ctx.s, ctx.hero.hair)


def moustache(ctx):
    with ctx.mb.bound_to("head"):
        for sign in (1, -1):
            ctx.mb.plate([_at(ctx, 0.0, -0.21, -0.07), _at(ctx, sign * 0.1, -0.2, -0.1), _at(ctx, sign * 0.04, -0.21, -0.11)], 0.024 * ctx.s, ctx.hero.hair)


def eyepatch(ctx, side=1):
    with ctx.mb.bound_to("head"):
        ctx.mb.sphere(_at(ctx, side * 0.075, -0.195, 0.03), (0.055 * ctx.s, 0.022 * ctx.s, 0.05 * ctx.s), 6 if ctx.hq else 4, 2, "cloth_black", smooth=False)
        if ctx.hq:
            ctx.mb.tube(_at(ctx, side * 0.11, -0.17, 0.07), _at(ctx, -side * 0.19, -0.06, 0.09), 0.008, sides=3, color="cloth_black")


def scar(ctx, side=-1):
    if not ctx.hq:
        return
    with ctx.mb.bound_to("head"):
        ctx.mb.tube(_at(ctx, side * 0.085, -0.19, 0.09), _at(ctx, side * 0.1, -0.175, -0.05), 0.007, sides=3, color="gem_red")


def spectacles(ctx):
    with ctx.mb.bound_to("head"):
        for sign in (1, -1):
            place = Matrix.Translation(_at(ctx, sign * 0.075, -0.205, 0.03)) @ Matrix.Rotation(math.pi / 2, 4, "X")
            with ctx.mb.xf(place):
                ctx.mb.lathe([(0.046 * ctx.s, -0.008), (0.046 * ctx.s, 0.008)], 8 if ctx.hq else 4, "brass", smooth=False)
        if ctx.hq:
            ctx.mb.tube(_at(ctx, -0.03, -0.205, 0.03), _at(ctx, 0.03, -0.205, 0.03), 0.006, sides=3, color="brass")


def goggles_up(ctx, lens="brass"):
    """Pushed up on the forehead: the sky-crew look."""
    with ctx.mb.bound_to("head"):
        for sign in (1, -1):
            place = Matrix.Translation(_at(ctx, sign * 0.075, -0.15, 0.16)) @ Matrix.Rotation(math.radians(66), 4, "X")
            with ctx.mb.xf(place):
                ctx.mb.lathe([(0.052 * ctx.s, -0.022), (0.052 * ctx.s, 0.022)], 6 if ctx.hq else 4, "leather_dark", smooth=False)
                if ctx.hq:
                    ctx.mb.lathe([(0.036 * ctx.s, -0.026), (0.036 * ctx.s, -0.02)], 6, lens, smooth=False)


def face_mask(ctx, color="cloth_black"):
    """Sable: wrapped to the eyes."""
    with ctx.mb.bound_to("head"):
        ctx.mb.sphere(_at(ctx, 0, -0.012, -0.075), (0.185 * ctx.s, 0.195 * ctx.s, 0.13 * ctx.s), ctx.q["head_s"], 4 if ctx.hq else 3, color, smooth=ctx.hq)


def hood(ctx, color="cloth_black"):
    with ctx.mb.bound_to("head"):
        ctx.mb.sphere(_at(ctx, 0, 0.055, 0.03), (0.245 * ctx.s, 0.245 * ctx.s, 0.26 * ctx.s), ctx.q["head_s"], ctx.q["head_r"], color, smooth=ctx.hq)
        ctx.mb.plate([_at(ctx, -0.1, 0.2, 0.1), _at(ctx, 0.1, 0.2, 0.1), _at(ctx, 0, 0.38, -0.17)], 0.05 * ctx.s, color)
    with ctx.mb.bound_to("chest"):
        ctx.mb.lathe([(0.22 * ctx.s, 1.24 * ctx.s), (0.17 * ctx.s, 1.4 * ctx.s)], ctx.q["torso"], color, smooth=False)


def sorcerer_amulet(ctx):
    """Thorne: one green stone on a black cord, the only bright thing he wears."""
    s, g = ctx.s, ctx.g
    stone = (0, -0.195 * g * s, 1.15 * s)
    with ctx.mb.bound_to("chest"):
        for sign in (1, -1):
            ctx.mb.tube((sign * 0.09 * s, -0.135 * g * s, 1.36 * s), stone, 0.007 * s, sides=4, color="faction_c")
        ctx.mb.sphere(stone, (0.04 * s, 0.024 * s, 0.055 * s), 6 if ctx.hq else 4, 3, "faction_b")


def sorcerer_hood(ctx, lining="faction_a"):
    """Thorne: a deep cowl, open at the face. A thick shell, so the opening has a purple-lined edge."""
    s, mb = ctx.s, ctx.mb
    # Height from the head's centre, half-width, half-depth, and half-angle of the opening at that height.
    rows = [(-0.34, 0.2, 0.21, 6), (-0.27, 0.215, 0.225, 18), (-0.2, 0.24, 0.25, 40), (-0.08, 0.255, 0.265, 46), (0.04, 0.26, 0.27, 46),
            (0.13, 0.25, 0.26, 38), (0.2, 0.22, 0.235, 16), (0.27, 0.16, 0.175, 8), (0.31, 0.06, 0.08, 6)]
    if not ctx.hq:
        rows = [rows[i] for i in (0, 2, 3, 5, 6, 8)]
    points = 11 if ctx.hq else 7
    wall = 0.022
    centre_y = 0.03

    def arc(rx, ry, z, opening, backward):
        out = []
        for k in range(points):
            u = k / (points - 1)
            a = math.radians(270 + opening + (360 - 2 * opening) * u)
            out.append(_at(ctx, rx * math.cos(a), centre_y + ry * math.sin(a), z))
        return out[::-1] if backward else out

    rings = []
    for z, rx, ry, opening in rows:
        ring = arc(rx, ry, z, opening, False) + arc(max(0.02, rx - wall), max(0.02, ry - wall), z, opening, True)
        rings.append([tuple(p) for p in ring])
    outer_faces = points - 1

    with mb.bound_to("head"):
        mb.loft(rings, lambda _i, j: "cloth_black" if j < outer_faces else lining, smooth=False)
    with mb.bound_to("chest"):
        # A mantle where the cowl falls onto the shoulders, following the body rather than a circle.
        sides = ctx.q["torso"]
        mb.loft([_body_ring(ctx, rx, ry, z, sides) for rx, ry, z in ((0.335, 0.205, 1.25), (0.25, 0.175, 1.36), (0.15, 0.135, 1.46))], "cloth_black", smooth=ctx.hq)


def sorcerer_robe(ctx):
    """Thorne: a black robe to the floor over purple. Above the knee it's one piece. Below that it's a
    panel on each leg, so it parts when he walks rather than the legs cutting through it."""
    mb, q, s, g = ctx.mb, ctx.q, ctx.s, ctx.g
    sides = q["torso"]

    def shell(bone, rows, color="cloth_black"):
        with mb.bound_to(bone):
            mb.loft([_body_ring(ctx, rx, ry, z, sides) for rx, ry, z in rows], color, smooth=ctx.hq)

    def panel(bone, top_half, bottom_half, top_z, bottom_z, top_ry, bottom_ry):
        # A narrow purple strip laid into the front of the robe. Works at any polygon count.
        with mb.bound_to(bone):
            mb.plate([(-top_half * s, -top_ry * g * s, top_z * s), (top_half * s, -top_ry * g * s, top_z * s),
                      (bottom_half * s, -bottom_ry * g * s, bottom_z * s), (-bottom_half * s, -bottom_ry * g * s, bottom_z * s)], 0.05 * s, "faction_a")

    shell("chest", [(0.25, 0.175, 1.06), (0.315, 0.185, 1.28), (0.15, 0.11, 1.38)])
    shell("spine", [(0.22, 0.165, 0.9), (0.25, 0.175, 1.1)])
    shell("hips", [(0.235, 0.17, 0.95), (0.29, 0.22, 0.62)])
    shell("hips", [(0.25, 0.185, 0.84), (0.255, 0.19, 0.93)], "faction_a")  # The sash, the shape of the body.
    panel("chest", 0.05, 0.06, 1.35, 1.06, 0.155, 0.175)
    panel("spine", 0.06, 0.06, 1.1, 0.92, 0.175, 0.165)
    panel("hips", 0.06, 0.07, 0.84, 0.62, 0.19, 0.22)

    # A purple underskirt that doesn't move, so nothing shows through when the leg panels part.
    shell("hips", [(0.14, 0.13, 0.05), (0.16, 0.14, 0.72)], "faction_a")

    columns = 7 if ctx.hq else 4
    for side, sign in (("L", 1), ("R", -1)):
        rings = []
        for rx, ry, z in ((0.27, 0.205, 0.7), (0.3, 0.235, 0.5), (0.34, 0.275, 0.27), (0.4, 0.32, 0.05)):
            ring = []
            for k in range(columns):
                a = math.radians(-93 + 186 * k / (columns - 1))  # Just past the centre line, so the panels overlap.
                ring.append((sign * rx * ctx.w * s * math.cos(a), ry * g * s * math.sin(a), z * s))
            rings.append(ring if sign > 0 else ring[::-1])
        with mb.bound_to(f"thigh.{side}"):
            mb.loft(rings, "cloth_black", smooth=False)
            mb.plate([(-sign * 0.012 * s, -0.215 * g * s, 0.68 * s), (sign * 0.07 * s, -0.215 * g * s, 0.68 * s),
                      (sign * 0.11 * s, -0.31 * g * s, 0.06 * s), (-sign * 0.012 * s, -0.31 * g * s, 0.06 * s)], 0.05 * s, "faction_a")


def sorcerer_sleeves(ctx):
    """Thorne: wide sleeves with purple cuffs, flaring from the elbow."""
    s, mb = ctx.s, ctx.mb
    sides = 8 if ctx.hq else 4
    for side in ("L", "R"):
        elbow, wrist = (Vector(p) for p in ctx.joints[f"lower_arm.{side}"][:2])
        with mb.bound_to(f"lower_arm.{side}"):
            mb.tube(elbow, wrist, 0.07 * s, 0.11 * s, sides=sides, color="cloth_black")
            mb.tube(wrist - (wrist - elbow) * 0.12, wrist, 0.113 * s, 0.118 * s, sides=sides, color="faction_a")


def bandana(ctx, color="gem_red", tails=True):
    with ctx.mb.bound_to("head"):
        ctx.mb.sphere(_at(ctx, 0, 0.03, 0.09), (0.213 * ctx.s, 0.215 * ctx.s, 0.17 * ctx.s), ctx.q["head_s"], 5 if ctx.hq else 3, color, smooth=ctx.hq)
        if tails:
            y = 0.23
            ctx.mb.plate([_at(ctx, 0, y, 0.06), _at(ctx, 0.1, y + 0.2, -0.14), _at(ctx, -0.02, y + 0.13, -0.17)], 0.025, color)


def tricorn(ctx):
    with ctx.mb.bound_to("head"):
        base._tricorn(ctx.mb, ctx.centre, ctx.s, ctx.hq)


def bicorne(ctx, color="navy", trim="gold"):
    """The Admiralty hat, worn fore-and-aft. Instantly different from the pirate tricorn."""
    z = 0.15
    with ctx.mb.bound_to("head"):
        ctx.mb.sphere(_at(ctx, 0, 0.0, z), (0.2 * ctx.s, 0.21 * ctx.s, 0.1 * ctx.s), ctx.q["head_s"], 3 if ctx.hq else 2, color, smooth=False)
        for side in (1, -1):
            outline = [_at(ctx, -0.17, side * 0.02, z), _at(ctx, -0.46, side * 0.03, z + 0.05), _at(ctx, -0.36, side * 0.04, z + 0.18), _at(ctx, 0, side * 0.05, z + 0.3), _at(ctx, 0.36, side * 0.04, z + 0.18), _at(ctx, 0.46, side * 0.03, z + 0.05), _at(ctx, 0.17, side * 0.02, z)]
            ctx.mb.plate(outline, 0.022 * ctx.s, color)
        if ctx.hq:
            ctx.mb.box(tuple(_at(ctx, 0, -0.07, z + 0.15)), (0.68 * ctx.s, 0.01, 0.012), trim)
            ctx.mb.sphere(_at(ctx, 0.0, -0.075, z + 0.2), 0.04 * ctx.s, 6, 3, trim, smooth=False)
        ctx.mb.plate([_at(ctx, 0.0, -0.08, z + 0.26), _at(ctx, 0.05, -0.08, z + 0.5), _at(ctx, -0.05, -0.08, z + 0.42)], 0.015, "enamel")


def shako(ctx, color="navy", plume="enamel"):
    """Armada infantry: a tall hard cap that makes them read as one disciplined line."""
    with ctx.mb.bound_to("head"):
        place = Matrix.Translation(_at(ctx, 0, 0.0, 0.08))
        with ctx.mb.xf(place):
            ctx.mb.lathe([(0.21 * ctx.s, 0.0), (0.21 * ctx.s, 0.08 * ctx.s), (0.24 * ctx.s, 0.3 * ctx.s)], ctx.q["head_s"], color, smooth=False)
        ctx.mb.box(tuple(_at(ctx, 0, -0.17, 0.11)), (0.26 * ctx.s, 0.09 * ctx.s, 0.018), "leather_dark")
        ctx.mb.plate([_at(ctx, -0.055, -0.235, 0.24), _at(ctx, 0.055, -0.235, 0.24), _at(ctx, 0.04, -0.235, 0.34), _at(ctx, -0.04, -0.235, 0.34)], 0.012, "gold")
        ctx.mb.path([_at(ctx, 0, -0.17, 0.37), _at(ctx, 0, -0.17, 0.53), _at(ctx, 0, -0.1, 0.68)], [0.03 * ctx.s, 0.05 * ctx.s, 0.008], 5 if ctx.hq else 3, plume)


def morion(ctx, color="silver", crest="gem_red"):
    """Royal Guard: a crested helm with a boat-shaped brim. Instantly elite in silhouette."""
    with ctx.mb.bound_to("head"):
        ctx.mb.sphere(_at(ctx, 0, 0, 0.08), (0.225 * ctx.s, 0.225 * ctx.s, 0.2 * ctx.s), ctx.q["head_s"], 5 if ctx.hq else 3, color, smooth=ctx.hq)
        for sign in (1, -1):
            ctx.mb.plate([_at(ctx, -0.23, sign * 0.03, 0.08), _at(ctx, 0.23, sign * 0.03, 0.08), _at(ctx, 0.0, sign * 0.5, 0.2)], 0.018 * ctx.s, color)
        ctx.mb.plate([_at(ctx, 0, -0.3, 0.14), _at(ctx, 0, -0.14, 0.42), _at(ctx, 0, 0.15, 0.43), _at(ctx, 0, 0.33, 0.14)], 0.02 * ctx.s, crest)


def warden_helm(ctx):
    """Malakor: a riveted barrel helm with one glowing eye-slit. No face, on purpose."""
    with ctx.mb.bound_to("head"):
        place = Matrix.Translation(_at(ctx, 0, 0, -0.2))
        with ctx.mb.xf(place):
            ctx.mb.lathe([(0.26 * ctx.s, 0.0), (0.27 * ctx.s, 0.32 * ctx.s), (0.25 * ctx.s, 0.47 * ctx.s), (0.06 * ctx.s, 0.53 * ctx.s)], 10 if ctx.hq else 6, "iron", smooth=False)
        ctx.mb.box(tuple(_at(ctx, 0, -0.265, 0.05)), (0.34 * ctx.s, 0.03, 0.04 * ctx.s), "ember")
        ctx.mb.box(tuple(_at(ctx, 0, -0.27, 0.0)), (0.05 * ctx.s, 0.03, 0.26 * ctx.s), "iron_light")
        for sign in (1, -1):
            ctx.mb.tube(_at(ctx, sign * 0.21, 0.02, 0.18), _at(ctx, sign * 0.5, 0.06, 0.42), 0.055 * ctx.s, 0.004, sides=6 if ctx.hq else 3, color="iron_light")


def hat_officer(ctx, color="navy"):
    with ctx.mb.bound_to("head"):
        place = Matrix.Translation(_at(ctx, 0, 0.0, 0.1))
        with ctx.mb.xf(place):
            ctx.mb.lathe([(0.215 * ctx.s, 0.0), (0.215 * ctx.s, 0.04 * ctx.s), (0.27 * ctx.s, 0.13 * ctx.s), (0.2 * ctx.s, 0.16 * ctx.s)], ctx.q["head_s"], color, smooth=False)
        ctx.mb.box(tuple(_at(ctx, 0, -0.205, 0.11)), (0.25 * ctx.s, 0.1 * ctx.s, 0.018), "leather_dark")
        ctx.mb.box(tuple(_at(ctx, 0, -0.232, 0.16)), (0.07 * ctx.s, 0.012, 0.07 * ctx.s), "gold")


# ---- clothes --------------------------------------------------------------------------------

def long_coat(ctx, color, inner=None, tail_len=0.42):
    """Long coat with back tails. Lapels stay open at the front, showing the top underneath."""
    inner = inner or ctx.hero.top
    mb, q, s, w, g = ctx.mb, ctx.q, ctx.s, ctx.w, ctx.g
    sides = q["torso"]
    open_front = {j for j in range(sides) if math.sin(2 * math.pi * (j + 0.5) / sides) < -0.85}

    def shell(bone, rows):
        with mb.bound_to(bone):
            rings = [_body_ring(ctx, rx, ry, z, sides) for rx, ry, z in rows]
            mb.loft(rings, lambda _i, j: inner if j in open_front else color, smooth=ctx.hq)

    shell("chest", [(0.25, 0.175, 1.06), (0.315, 0.185, 1.28), (0.15, 0.11, 1.38)])
    shell("spine", [(0.22, 0.165, 0.9), (0.25, 0.175, 1.1)])
    with mb.bound_to("hips"):
        arc = 8 if ctx.hq else 4
        rows = [(0.235, 0.17, 0.95), (0.27, 0.2, 0.74), (0.3, 0.23, tail_len)]
        rings = []
        for rx, ry, z in rows:
            outer, in_ = [], []
            for j in range(arc + 1):
                a = math.radians(-10 + 200 * j / arc)
                outer.append((rx * s * w * math.cos(a), ry * g * s * math.sin(a), z * s))
                in_.append((rx * 0.9 * s * w * math.cos(a), ry * 0.9 * g * s * math.sin(a), z * s))
            rings.append(outer + list(reversed(in_)))
        mb.loft(rings, color, smooth=False)


def short_jacket(ctx, color, inner=None):
    """Cropped at the waist: for characters who need their legs free."""
    inner = inner or ctx.hero.top
    mb, q = ctx.mb, ctx.q
    sides = q["torso"]
    open_front = {j for j in range(sides) if math.sin(2 * math.pi * (j + 0.5) / sides) < -0.85}
    with mb.bound_to("chest"):
        rings = [_body_ring(ctx, rx, ry, z, sides) for rx, ry, z in ((0.245, 0.17, 1.06), (0.31, 0.18, 1.28), (0.15, 0.11, 1.38))]
        mb.loft(rings, lambda _i, j: inner if j in open_front else color, smooth=ctx.hq)
    with mb.bound_to("spine"):
        rings = [_body_ring(ctx, rx, ry, z, sides) for rx, ry, z in ((0.225, 0.165, 0.97), (0.245, 0.172, 1.1))]
        mb.loft(rings, lambda _i, j: inner if j in open_front else color, smooth=ctx.hq)


def cuirass(ctx, color="silver", trim="gold"):
    mb, q = ctx.mb, ctx.q
    sides = q["torso"]
    with mb.bound_to("chest"):
        rings = [_body_ring(ctx, rx, ry, z, sides) for rx, ry, z in ((0.26, 0.2, 1.06), (0.33, 0.21, 1.29), (0.16, 0.13, 1.38))]
        mb.loft(rings, color, smooth=ctx.hq)
        if ctx.hq:
            mb.box((0, -0.205 * ctx.g * ctx.s, 1.2 * ctx.s), (0.035 * ctx.s, 0.02, 0.28 * ctx.s), trim)
    with mb.bound_to("spine"):
        rings = [_body_ring(ctx, rx, ry, z, sides) for rx, ry, z in ((0.235, 0.18, 0.93), (0.265, 0.2, 1.08))]
        mb.loft(rings, color, smooth=ctx.hq)


def pauldrons(ctx, color="iron_light", spiked=False, trim=None):
    s, w = ctx.s, ctx.w
    with ctx.mb.bound_to("chest"):
        for sign in (1, -1):
            ctx.mb.sphere((sign * 0.3 * w * s, 0, 1.3 * s), (0.17 * s, 0.17 * s, 0.11 * s), 8 if ctx.hq else 4, 4 if ctx.hq else 2, color, smooth=ctx.hq)
            if spiked:
                ctx.mb.tube((sign * 0.34 * w * s, 0, 1.38 * s), (sign * 0.5 * w * s, 0, 1.62 * s), 0.055 * s, 0.004, sides=6 if ctx.hq else 3, color="iron")
            if trim and ctx.hq:
                ctx.mb.box((sign * 0.3 * w * s, -0.14 * s, 1.26 * s), (0.2 * s, 0.03, 0.03), trim)


def epaulettes(ctx, color="gold"):
    s, w = ctx.s, ctx.w
    with ctx.mb.bound_to("chest"):
        for sign in (1, -1):
            ctx.mb.box((sign * 0.28 * w * s, 0, 1.33 * s), (0.2 * s, 0.17 * s, 0.05 * s), color, top_scale=0.8)
            if ctx.hq:
                for k in (-0.05, 0.0, 0.05):
                    ctx.mb.tube((sign * 0.38 * w * s, k * s, 1.32 * s), (sign * 0.4 * w * s, k * s, 1.24 * s), 0.012, sides=3, color=color)


def cape(ctx, color, length=0.34, lining=None):
    """Back-mounted. Bound to the chest: it follows the torso and doesn't cut through the legs."""
    s, w = ctx.s, ctx.w
    with ctx.mb.bound_to("chest"):
        rows = 3 if ctx.hq else 2
        cols = 6 if ctx.hq else 3
        rings = []
        for r in range(rows + 1):
            k = r / rows
            z = (1.36 - (1.36 - length) * k) * s
            half = (0.26 + 0.18 * k) * w * s
            back = (0.17 + 0.16 * k) * s
            front, rear = [], []
            for c in range(cols + 1):
                u = c / cols
                x = -half + 2 * half * u
                wave = 0.04 * s * math.sin(u * math.pi * 3) * k
                front.append((x, back + wave, z))
                rear.append((x, back + wave + 0.025, z))
            rings.append(front + list(reversed(rear)))
        mb_color = (lambda _i, j: lining if lining and j < cols else color) if lining else color
        ctx.mb.loft(rings, mb_color)
    with ctx.mb.bound_to("chest"):
        ctx.mb.tube((-0.17 * w * s, -0.1 * s, 1.36 * s), (0.17 * w * s, -0.1 * s, 1.36 * s), 0.018 * s, sides=4 if ctx.hq else 3, color="gold" if ctx.hq else color)


def sash(ctx, color, tail=True):
    s, w = ctx.s, ctx.w
    with ctx.mb.bound_to("hips"):
        ctx.mb.lathe([(0.215 * w * s * ctx.g ** 0.3, 0.84 * s), (0.215 * w * s * ctx.g ** 0.3, 0.93 * s)], ctx.q["torso"], color, smooth=False)
        if tail:
            ctx.mb.plate([(0.14 * s, -0.17 * ctx.g * s, 0.86 * s), (0.22 * s, -0.18 * ctx.g * s, 0.56 * s), (0.08 * s, -0.18 * ctx.g * s, 0.6 * s)], 0.02, color)


def cross_belt(ctx, color="enamel"):
    s, g = ctx.s, ctx.g
    with ctx.mb.bound_to("chest"):
        for sign in (1, -1):
            ctx.mb.tube((sign * -0.24 * s, -0.135 * g * s, 1.32 * s), (sign * 0.22 * s, -0.19 * g * s, 1.09 * s), 0.02 * s, sides=4, color=color, flat=1.4)


def bandolier(ctx, shells="brass"):
    s, g = ctx.s, ctx.g
    with ctx.mb.bound_to("chest"):
        ctx.mb.tube((-0.27 * s, -0.13 * g * s, 1.32 * s), (0.2 * s, -0.19 * g * s, 1.08 * s), 0.026 * s, sides=4, color="leather_dark", flat=1.4)
        if ctx.hq:
            for i in range(5):
                k = (i + 0.5) / 5
                ctx.mb.box(((-0.27 + 0.47 * k) * s, (-0.15 - 0.05 * k) * g * s, (1.32 - 0.24 * k) * s), (0.03, 0.03, 0.07), shells)


def apron(ctx, color="leather"):
    s, g = ctx.s, ctx.g
    with ctx.mb.bound_to("chest"):
        ctx.mb.plate([(-0.18 * s, -0.18 * g * s, 1.28 * s), (0.18 * s, -0.18 * g * s, 1.28 * s), (0.22 * s, -0.19 * g * s, 1.08 * s), (-0.22 * s, -0.19 * g * s, 1.08 * s)], 0.025, color)
    with ctx.mb.bound_to("hips"):
        ctx.mb.plate([(-0.22 * s, -0.17 * g * s, 0.98 * s), (0.22 * s, -0.17 * g * s, 0.98 * s), (0.25 * s, -0.19 * g * s, 0.5 * s), (-0.25 * s, -0.19 * g * s, 0.5 * s)], 0.025, color)


def tool_belt(ctx):
    s, w = ctx.s, ctx.w
    with ctx.mb.bound_to("hips"):
        for x, h, c in ((0.22, 0.14, "leather"), (-0.2, 0.12, "brass"), (0.06, 0.09, "iron_light")) if ctx.hq else ((0.22, 0.14, "leather"),):
            ctx.mb.box((x * w * s, -0.13 * ctx.g * s, (0.85 - h / 2) * s), (0.1 * s, 0.07 * s, h * s), c)


def tabard(ctx, color, trim=None, length=0.36):
    s, g = ctx.s, ctx.g
    with ctx.mb.bound_to("hips"):
        for side in (1, -1):
            ctx.mb.plate([(-0.18 * s, side * 0.19 * g * s, 0.97 * s), (0.18 * s, side * 0.19 * g * s, 0.97 * s), (0.2 * s, side * 0.2 * g * s, length * s), (0, side * 0.2 * g * s, (length - 0.08) * s), (-0.2 * s, side * 0.2 * g * s, length * s)], 0.025, color)
        if trim and ctx.hq:
            ctx.mb.box((0, -0.22 * g * s, 0.65 * s), (0.08 * s, 0.015, 0.45 * s), trim)


def keyring(ctx):
    s = ctx.s
    with ctx.mb.bound_to("hips"):
        place = Matrix.Translation((-0.24 * s * ctx.w, -0.05 * s, 0.76 * s)) @ Matrix.Rotation(math.pi / 2, 4, "Y")
        with ctx.mb.xf(place):
            ctx.mb.lathe([(0.075, -0.012), (0.075, 0.012)], 8 if ctx.hq else 4, "brass", smooth=False)
        if ctx.hq:
            for i, dz in enumerate((-0.08, -0.1, -0.09)):
                ctx.mb.box(((-0.24 + 0.015 * i) * s * ctx.w, (-0.09 + i * 0.05) * s, (0.76 + dz) * s), (0.015, 0.02, 0.1), "brass")


def medals(ctx):
    s, g = ctx.s, ctx.g
    with ctx.mb.bound_to("chest"):
        for x, c in ((0.08, "gold"), (0.14, "gem_red"), (0.2, "gem_blue")) if ctx.hq else ((0.12, "gold"),):
            ctx.mb.box((x * s, -0.205 * g * s, 1.23 * s), (0.04 * s, 0.015, 0.06 * s), c)


def gold_buttons(ctx):
    if not ctx.hq:
        return
    with ctx.mb.bound_to("spine"):
        for sign in (1, -1):
            for z in (0.97, 1.05):
                ctx.mb.box((sign * 0.07 * ctx.s, -0.18 * ctx.g * ctx.s, z * ctx.s), (0.03, 0.02, 0.03), "gold")


def high_collar(ctx, color):
    s = ctx.s
    with ctx.mb.bound_to("chest"):
        ctx.mb.lathe([(0.15 * s, 1.33 * s), (0.17 * s, 1.47 * s)], ctx.q["limb"], color, smooth=False, caps=(False, False))


def scarf(ctx, color="faction_b"):
    """Long streaming scarf behind the neck: Lyra's and the wind's silhouette."""
    s = ctx.s
    with ctx.mb.bound_to("chest"):
        ctx.mb.lathe([(0.17 * s, 1.28 * s), (0.18 * s, 1.36 * s), (0.13 * s, 1.42 * s)], ctx.q["limb"], color, smooth=False)
        ctx.mb.plate([(0.08 * s, 0.16 * s, 1.36 * s), (-0.04 * s, 0.17 * s, 1.36 * s), (0.34 * s, 0.56 * s, 0.86 * s), (0.42 * s, 0.5 * s, 0.84 * s)], 0.02, color)


def grapple_gauntlet(ctx):
    """Vane's left arm: the launcher behind every boarding in the game. Always in view."""
    s = ctx.s
    head, tail = (Vector(p) for p in ctx.joints["lower_arm.L"])
    with ctx.mb.bound_to("lower_arm.L"):
        ctx.mb.tube(head.lerp(tail, 0.25), head.lerp(tail, 0.95), 0.08 * s, 0.075 * s, sides=8 if ctx.hq else 4, color="iron_light")
        tip = head.lerp(tail, 0.72)
        ctx.mb.tube(tip + Vector((0.05, -0.06, 0)) * s, tip + Vector((0.09, -0.23, -0.02)) * s, 0.032 * s, 0.024 * s, sides=6 if ctx.hq else 3, color="brass")
        if ctx.hq:
            for a in (0, 2.1, 4.2):
                base_ = tip + Vector((0.09, -0.23, -0.02)) * s
                ctx.mb.tube(base_, base_ + Vector((0.05 * math.cos(a), -0.05, 0.05 * math.sin(a))) * s, 0.012, 0.004, sides=3, color="iron")
            ctx.mb.box(tuple(head.lerp(tail, 0.5) + Vector((-0.07, 0, 0)) * s), (0.03, 0.06, 0.1), "lamp")


def iron_arm(ctx, side="L"):
    """Krag's prosthetic: a salvaged crane arm in place of a left hand. Ends in a three-fingered claw."""
    s = ctx.s
    head, tail = (Vector(p) for p in ctx.joints[f"lower_arm.{side}"])
    hand_head, hand_tail = (Vector(p) for p in ctx.joints[f"hand.{side}"])
    with ctx.mb.bound_to(f"lower_arm.{side}"):
        ctx.mb.tube(head, tail, 0.098 * s, 0.09 * s, sides=8 if ctx.hq else 4, color="iron_light")
        if ctx.hq:
            for k in (0.25, 0.6):
                centre = head.lerp(tail, k)
                ctx.mb.tube(centre - Vector((0, 0, 0.02)), centre + Vector((0, 0, 0.02)), 0.105 * s, sides=8, color="rust")
    with ctx.mb.bound_to(f"hand.{side}"):
        ctx.mb.sphere(hand_head, 0.085 * s, 8 if ctx.hq else 4, 4 if ctx.hq else 2, "iron", smooth=False)
        for a in ((0, 2.1, 4.2) if ctx.hq else (0, 3.14)):
            ctx.mb.tube(hand_head, hand_tail + Vector((0.06 * math.cos(a), 0.06 * math.sin(a), -0.03)) * s, 0.03 * s, 0.005, sides=4 if ctx.hq else 3, color="iron_light")


def chain_wrap(ctx):
    s, g, w = ctx.s, ctx.g, ctx.w
    with ctx.mb.bound_to("chest"):
        pts = [(-0.3 * w, -0.2 * g, 1.3), (-0.05 * w, -0.25 * g, 1.2), (0.26 * w, -0.2 * g, 1.1)]
        ctx.mb.path([tuple(c * s for c in p) for p in pts], [0.04 * s] * 3, 5 if ctx.hq else 3, "iron")
        if ctx.hq:
            for k in range(5):
                u = k / 4
                ctx.mb.box(tuple(c * s for c in ((-0.3 + 0.56 * u) * w, -0.25 * g, 1.3 - 0.2 * u)), (0.05, 0.03, 0.07), "iron_light")


def dagger_sheaths(ctx):
    """Handles stay visible: she's never unarmed, even when her hands are empty."""
    s, w = ctx.s, ctx.w
    with ctx.mb.bound_to("hips"):
        for sign in (1, -1):
            ctx.mb.tube((sign * 0.23 * w * s, 0.08 * s, 0.98 * s), (sign * 0.28 * w * s, 0.14 * s, 0.56 * s), 0.024 * s, 0.015 * s, sides=4 if ctx.hq else 3, color="leather_dark")
            ctx.mb.tube((sign * 0.23 * w * s, 0.08 * s, 0.98 * s), (sign * 0.21 * w * s, 0.06 * s, 1.1 * s), 0.016 * s, sides=4 if ctx.hq else 3, color="iron_light")


def navigator_case(ctx):
    """Morrow's chart case: a brass tube at the hip, always within reach."""
    s, w = ctx.s, ctx.w
    with ctx.mb.bound_to("hips"):
        ctx.mb.tube((0.25 * w * s, 0.1 * s, 0.98 * s), (0.3 * w * s, 0.14 * s, 0.52 * s), 0.045 * s, sides=8 if ctx.hq else 4, color="brass")


def tool_harness(ctx):
    s, g = ctx.s, ctx.g
    with ctx.mb.bound_to("chest"):
        for sign in (1, -1):
            ctx.mb.tube((sign * 0.14 * s, -0.14 * g * s, 1.32 * s), (sign * 0.14 * s, -0.19 * g * s, 1.08 * s), 0.016 * s, sides=4, color="leather_dark")
    if ctx.hq:
        with ctx.mb.bound_to("chest"):
            ctx.mb.box((-0.13 * s, -0.2 * g * s, 1.2 * s), (0.09 * s, 0.03, 0.11 * s), "brass")
            ctx.mb.box((-0.13 * s, -0.215 * g * s, 1.21 * s), (0.05 * s, 0.01, 0.06 * s), "liftstone")


def ear_guards(ctx):
    """Rook's gunner's muffs, worn round the neck between shots."""
    with ctx.mb.bound_to("neck"):
        for sign in (1, -1):
            ctx.mb.sphere(_at(ctx, sign * 0.15, 0.02, -0.21), (0.05 * ctx.s, 0.06 * ctx.s, 0.07 * ctx.s), 6 if ctx.hq else 4, 3, "brass", smooth=False)


def nomad_layers(ctx):
    """Lyra: a worn leather vest over a green tunic, a patchwork sash slung across, and coin and bone charms."""
    mb, q, s, g, w, hq = ctx.mb, ctx.q, ctx.s, ctx.g, ctx.w, ctx.hq
    sides = q["torso"]

    def shell(bone, rows, color):
        with mb.bound_to(bone):
            mb.loft([_body_ring(ctx, rx, ry, z, sides) for rx, ry, z in rows], color, smooth=hq)

    # The tunic is short at the hips, with a panel on each thigh below that, so her legs can move.
    shell("hips", [(0.225, 0.17, 0.96), (0.262, 0.2, 0.74)], "cloth_green")
    columns = 6 if hq else 4
    for side, sign in (("L", 1), ("R", -1)):
        rings = []
        for rx, ry, z in ((0.25, 0.19, 0.8), (0.275, 0.215, 0.66), (0.3, 0.235, 0.54)):
            ring = []
            for k in range(columns):
                a = math.radians(-93 + 186 * k / (columns - 1))
                ring.append((sign * rx * w * s * math.cos(a), ry * g * s * math.sin(a), z * s))
            rings.append(ring if sign > 0 else ring[::-1])
        with mb.bound_to(f"thigh.{side}"):
            mb.loft(rings, "cloth_green", smooth=False)
    shell("chest", [(0.255, 0.18, 1.06), (0.32, 0.195, 1.28), (0.16, 0.12, 1.38)], "leather")
    shell("spine", [(0.225, 0.17, 0.95), (0.25, 0.18, 1.1)], "leather")
    with mb.bound_to("chest"):
        front = 0.195 * g * s
        mb.plate([(-0.085 * s, -front, 1.33 * s), (0.085 * s, -front, 1.33 * s), (0.065 * s, -0.17 * g * s, 1.06 * s), (-0.065 * s, -0.17 * g * s, 1.06 * s)], 0.03 * s, "cloth_green")
    with mb.bound_to("spine"):
        mb.plate([(-0.065 * s, -0.17 * g * s, 1.07 * s), (0.065 * s, -0.17 * g * s, 1.07 * s), (0.06 * s, -0.165 * g * s, 0.95 * s), (-0.06 * s, -0.165 * g * s, 0.95 * s)], 0.03 * s, "cloth_green")
    with mb.bound_to("hips"):
        # Patchwork: strips of different cloth hanging from the sash on one side.
        patches = (("gold", 0.05, 0.09, 0.56), ("cloth_green", 0.14, 0.09, 0.62), ("gold_dark", 0.23, 0.08, 0.68))
        for color, x, half, low in patches if hq else patches[:2]:
            mb.plate([((x - half / 2) * w * s, -0.195 * g * s, 0.88 * s), ((x + half / 2) * w * s, -0.195 * g * s, 0.88 * s),
                      ((x + half / 2) * w * s, -0.235 * g * s, low * s), ((x - half / 2) * w * s, -0.235 * g * s, low * s)], 0.02 * s, color)
        for k, x in enumerate((-0.15, -0.09, -0.03) if hq else (-0.09,)):
            # Following the curve of the hip, so each charm stays on the body.
            on_hip = 0.19 * g * s * math.sqrt(max(0.1, 1 - (x / 0.25) ** 2))
            mb.tube((x * w * s, -on_hip, 0.86 * s), (x * w * s, -on_hip - 0.012 * s, 0.78 * s), 0.006 * s, sides=3, color="leather_dark")
            mb.sphere((x * w * s, -on_hip - 0.012 * s, 0.76 * s), 0.024 * s, 5 if hq else 4, 3, "gold" if k % 2 else "enamel", smooth=False)
    for side in ("L", "R"):
        elbow, wrist = (Vector(p) for p in ctx.joints[f"lower_arm.{side}"][:2])
        with mb.bound_to(f"lower_arm.{side}"):
            mb.tube(elbow + (wrist - elbow) * 0.4, wrist - (wrist - elbow) * 0.05, 0.06 * s, 0.056 * s, sides=6 if hq else 4, color="leather")


def nomad_headwrap(ctx):
    """Lyra: a green band tied round the head over her hair, with gold coins and short tied tails."""
    mb, s, hq = ctx.mb, ctx.s, ctx.hq
    sides = ctx.q["head_s"]
    rings = []
    for z, r in ((0.06, 0.226), (0.17, 0.214)):
        rings.append([tuple(_at(ctx, r * math.cos(2 * math.pi * j / sides), 0.04 + r * 1.02 * math.sin(2 * math.pi * j / sides), z)) for j in range(sides)])
    with mb.bound_to("head"):
        mb.loft(rings, "cloth_green", smooth=False)
        for x in (-0.11, -0.055, 0.0, 0.055, 0.11) if hq else (-0.08, 0.0, 0.08):
            front = 0.04 - 0.226 * 1.02 * math.sqrt(max(0.1, 1 - (x / 0.226) ** 2))
            mb.sphere(_at(ctx, x, front + (-0.004 if hq else 0.018), 0.115), (0.02 * s, 0.014 * s if hq else 0.03 * s, 0.02 * s), 5 if hq else 4, 3, "gold", smooth=False)
        mb.plate([_at(ctx, -0.14, 0.2, 0.13), _at(ctx, -0.06, 0.25, 0.12), _at(ctx, -0.17, 0.3, -0.06)], 0.02 * s, "cloth_green")
        mb.plate([_at(ctx, 0.14, 0.2, 0.13), _at(ctx, 0.06, 0.25, 0.12), _at(ctx, 0.13, 0.3, -0.1)], 0.02 * s, "grass")


def nomad_scarf(ctx):
    """Lyra: a gold scarf wound close round the neck, with one short end hanging at the shoulder."""
    mb, s, g = ctx.mb, ctx.s, ctx.g
    with mb.bound_to("chest"):
        mb.lathe([(0.17 * s, 1.27 * s), (0.18 * s, 1.35 * s), (0.13 * s, 1.42 * s)], ctx.q["limb"], "gold_dark", smooth=False)
        mb.plate([(0.05 * s, -0.17 * g * s, 1.32 * s), (0.14 * s, -0.16 * g * s, 1.32 * s), (0.17 * s, -0.19 * g * s, 1.02 * s), (0.08 * s, -0.2 * g * s, 1.02 * s)], 0.022 * s, "gold_dark")


def assassin_gear(ctx):
    """Sable: a dark leather vest, a strap of poison vials, a bow, poison arrows and a poison bottle, one steel pauldron and steel bracers."""
    mb, q, s, g, w, hq = ctx.mb, ctx.q, ctx.s, ctx.g, ctx.w, ctx.hq
    sides = q["torso"]
    with mb.bound_to("chest"):
        mb.loft([_body_ring(ctx, rx, ry, z, sides) for rx, ry, z in ((0.25, 0.175, 1.06), (0.31, 0.218, 1.24), (0.16, 0.12, 1.38))], "leather_dark", smooth=hq)
        mb.plate([(-0.06 * s, -0.19 * g * s, 1.35 * s), (0.06 * s, -0.19 * g * s, 1.35 * s), (0.05 * s, -0.17 * g * s, 1.06 * s), (-0.05 * s, -0.17 * g * s, 1.06 * s)], 0.026 * s, "cloth_black")

        def on_chest(u):
            x = (0.27 - 0.5 * u) * w * s
            z = (1.3 - 0.22 * u) * s
            depth = (0.208 - 0.03 * u) * g * s
            return Vector((x, -depth * math.sqrt(max(0.05, 1 - (x / (0.3 * w * s)) ** 2)) - 0.012 * s, z))

        strap = [on_chest(k / 6) for k in range(7)]
        mb.path(strap, [0.024 * s] * len(strap), 4, "leather")
        for k in range(4 if hq else 3):
            at = on_chest((k + 0.6) / (4 if hq else 3))
            mb.sphere(tuple(at + Vector((0, -0.02 * s, 0))), (0.027 * s, 0.022 * s, 0.042 * s), 5 if hq else 4, 3, "grass", smooth=False)
            if hq:
                mb.box(tuple(at + Vector((0, -0.018 * s, 0.035 * s))), (0.018 * s, 0.018 * s, 0.014 * s), "iron_light")
    with mb.bound_to("spine"):
        mb.loft([_body_ring(ctx, rx, ry, z, sides) for rx, ry, z in ((0.22, 0.165, 0.95), (0.25, 0.175, 1.1))], "leather_dark", smooth=hq)
    # The rest of her arsenal, on her back and belt: a bow, a quiver of poison arrows, her poison bottle.
    with mb.bound_to("chest"):
        back = 0.19 * g * s
        bow = [(0.14 * w * s, back, 1.42 * s), (0.34 * w * s, back + 0.015 * s, 1.2 * s), (0.28 * w * s, back + 0.015 * s, 0.98 * s), (0.06 * w * s, back, 0.82 * s)]
        mb.path([Vector(p) for p in bow], [0.016 * s, 0.03 * s, 0.03 * s, 0.016 * s], 4, "wood_light")
        mb.tube(Vector(bow[0]), Vector(bow[-1]), 0.005 * s, sides=3, color="canvas")
        mb.tube((-0.15 * w * s, back, 1.0 * s), (-0.25 * w * s, back + 0.02 * s, 1.34 * s), 0.05 * s, 0.056 * s, sides=6 if hq else 4, color="leather")
        for dx, h in ((0.0, 0.2), (0.035, 0.16), (-0.03, 0.14)) if hq else ((0.0, 0.18),):
            base = Vector(((-0.25 * w + dx) * s, back + 0.02 * s, 1.34 * s))
            tip = base + Vector((-0.02 * s, 0, h * s))
            mb.tube(base, tip, 0.006 * s, sides=3, color="wood_light")
            mb.tube(tip, tip + Vector((0, 0, 0.05 * s)), 0.02 * s, 0.002, sides=4, color="grass")
    with mb.bound_to("head"):
        # Long dark hair escaping the hood, down both sides of her face.
        for sign in (1, -1):
            mb.path([_at(ctx, sign * 0.14, -0.13, 0.08), _at(ctx, sign * 0.175, -0.16, -0.12), _at(ctx, sign * 0.165, -0.15, -0.34)], [0.03 * s, 0.038 * s, 0.012 * s], 5 if hq else 4, ctx.hero.hair)
    with mb.bound_to("hips"):
        # Hips wider than the waist: most of what makes her silhouette read as a woman's.
        mb.loft([_body_ring(ctx, rx, ry, z, sides) for rx, ry, z in ((0.27, 0.185, 0.68), (0.33, 0.2, 0.8), (0.235, 0.165, 0.95))], "cloth_black", smooth=hq)
        at = Vector((0.2 * w * s, -0.165 * g * s, 0.82 * s))
        if not hq:
            # The base LQ belt's buckle would be a bright patch in the middle of a dark waist.
            mb.box((0, -0.18 * g * s, 0.93 * s), (0.11 * s, 0.04 * s, 0.09 * s), "leather_dark")
        mb.sphere(at, (0.05 * s, 0.04 * s, 0.065 * s), 6 if hq else 4, 3, "grass", smooth=False)
        mb.tube(at + Vector((0, 0, 0.05 * s)), at + Vector((-0.01 * s, 0.01 * s, 0.13 * s)), 0.02 * s, 0.024 * s, sides=4, color="leather")
    shoulder, elbow = (Vector(p) for p in ctx.joints["upper_arm.R"][:2])
    with mb.bound_to("upper_arm.R"):
        mb.sphere(shoulder + (elbow - shoulder) * 0.12 + Vector((0, 0, 0.02)) * s, (0.092 * s, 0.086 * s, 0.058 * s), 6 if hq else 4, 3, "silver", smooth=False)
    for side in ("L", "R"):
        near, far = (Vector(p) for p in ctx.joints[f"lower_arm.{side}"][:2])
        with mb.bound_to(f"lower_arm.{side}"):
            mb.tube(near + (far - near) * 0.35, far - (far - near) * 0.05, 0.05 * s, 0.045 * s, sides=6 if hq else 4, color="iron")


def morrow_finery(ctx):
    """Morrow: dark caged spectacles, a black tricorn, an emerald velvet coat with a flared hem, gold filigree,
    lace at the throat and wrists, a gold waistcoat, and skeleton keys on rings at the belt."""
    mb, q, s, g, w, hq = ctx.mb, ctx.q, ctx.s, ctx.g, ctx.w, ctx.hq
    sides = q["torso"]

    def shell(bone, rows, color):
        with mb.bound_to(bone):
            mb.loft([_body_ring(ctx, rx, ry, z, sides) for rx, ry, z in rows], color, smooth=hq)

    def front_plate(bone, half_top, half_low, z_top, z_low, depth_top, depth_low, color, thick=0.024):
        with mb.bound_to(bone):
            mb.plate([(-half_top * s, -depth_top * g * s, z_top * s), (half_top * s, -depth_top * g * s, z_top * s),
                      (half_low * s, -depth_low * g * s, z_low * s), (-half_low * s, -depth_low * g * s, z_low * s)], thick * s, color)

    # The coat, closed over a gold waistcoat that shows down the middle.
    shell("chest", [(0.25, 0.175, 1.06), (0.315, 0.19, 1.28), (0.16, 0.12, 1.38)], "faction_a")
    shell("spine", [(0.22, 0.165, 0.92), (0.25, 0.175, 1.1)], "faction_a")
    shell("hips", [(0.235, 0.17, 0.96), (0.285, 0.21, 0.72)], "faction_a")
    columns = 6 if hq else 4
    for side, sign in (("L", 1), ("R", -1)):
        rings = []
        for rx, ry, z in ((0.26, 0.195, 0.78), (0.3, 0.235, 0.6), (0.36, 0.28, 0.42)):
            ring = []
            for k in range(columns):
                a = math.radians(-93 + 186 * k / (columns - 1))
                ring.append((sign * rx * w * s * math.cos(a), ry * g * s * math.sin(a), z * s))
            rings.append(ring if sign > 0 else ring[::-1])
        with mb.bound_to(f"thigh.{side}"):
            mb.loft(rings, "faction_a", smooth=False)
    front_plate("chest", 0.06, 0.07, 1.33, 1.06, 0.185, 0.18, "gold_dark")
    front_plate("spine", 0.07, 0.07, 1.08, 0.94, 0.175, 0.165, "gold_dark")
    front_plate("hips", 0.07, 0.08, 0.92, 0.66, 0.17, 0.21, "gold_dark")
    with mb.bound_to("chest"):
        for sign in (1, -1):
            # Wide lapels, with a gold edge and a row of polished buttons down each side.
            mb.plate([(sign * 0.06 * s, -0.19 * g * s, 1.35 * s), (sign * 0.22 * w * s, -0.15 * g * s, 1.33 * s), (sign * 0.1 * s, -0.19 * g * s, 1.1 * s)], 0.02 * s, "faction_c")
            mb.plate([(sign * 0.215 * w * s, -0.158 * g * s, 1.335 * s), (sign * 0.235 * w * s, -0.15 * g * s, 1.33 * s), (sign * 0.105 * s, -0.198 * g * s, 1.09 * s), (sign * 0.09 * s, -0.198 * g * s, 1.09 * s)], 0.022 * s, "gold")
            for z in (1.2, 1.1) if hq else (1.14,):
                mb.sphere((sign * 0.1 * s, -0.2 * g * s, z * s), 0.018 * s, 5 if hq else 4, 3, "gold", smooth=False)
        # A white cravat with lace at the throat.
        mb.sphere((0, -0.145 * g * s, 1.38 * s), (0.075 * s, 0.05 * s, 0.05 * s), 6 if hq else 4, 3, "cloth_white", smooth=False)
        mb.plate([(-0.05 * s, -0.19 * g * s, 1.37 * s), (0.05 * s, -0.19 * g * s, 1.37 * s), (0.075 * s, -0.205 * g * s, 1.2 * s), (-0.075 * s, -0.205 * g * s, 1.2 * s)], 0.02 * s, "cloth_white")
    for side in ("L", "R"):
        elbow, wrist = (Vector(p) for p in ctx.joints[f"lower_arm.{side}"][:2])
        with mb.bound_to(f"lower_arm.{side}"):
            mb.tube(elbow + (wrist - elbow) * 0.62, elbow + (wrist - elbow) * 0.82, 0.062 * s, 0.066 * s, sides=6 if hq else 4, color="gold_dark")
            mb.tube(elbow + (wrist - elbow) * 0.82, wrist + (wrist - elbow) * 0.08, 0.05 * s, 0.075 * s, sides=6 if hq else 4, color="cloth_white")
    with mb.bound_to("hips"):
        # Brass rings at the belt, hung with skeleton keys.
        for k, x in enumerate((0.1, 0.17, 0.24) if hq else (0.13, 0.22)):
            on_hip = 0.17 * g * s * math.sqrt(max(0.1, 1 - (x / 0.3) ** 2))
            top = Vector((x * w * s, -on_hip - 0.014 * s, 0.9 * s))
            low = top + Vector((0, -0.006 * s, -0.16 * s))
            mb.tube(top, low, 0.008 * s, sides=3, color="brass")
            mb.sphere(top, 0.022 * s, 5 if hq else 4, 3, "brass", smooth=False)
            mb.box(tuple(low + Vector((0.012 * s, 0, 0.018 * s))), (0.03 * s, 0.012 * s, 0.022 * s), "brass")
    with mb.bound_to("head"):
        # A black tricorn with gold braid, the hair tucked up under it.
        z = ctx.centre.z + 0.12 * s
        ring_sides = 12 if hq else 6
        brim = []
        for dz in (-0.02, 0.03):
            ring = []
            for j in range(ring_sides):
                a = 2 * math.pi * (j + 0.5) / ring_sides
                lobe = 1.0 + 0.3 * math.cos(3 * (a + math.pi / 2))
                ring.append((0.3 * s * lobe * math.cos(a), 0.3 * s * lobe * math.sin(a), z + dz * s))
            brim.append(ring)
        mb.loft(brim, "cloth_black")
        trim = [[(x * 1.03, y * 1.03, h) for x, y, h in brim[1]], [(x * 1.03, y * 1.03, h + 0.012 * s) for x, y, h in brim[1]]]
        mb.loft(trim, "gold")
        with mb.xf(Matrix.Translation((0, 0, z))):
            mb.lathe([(0.2 * s, 0.0), (0.19 * s, 0.11 * s), (0.11 * s, 0.17 * s)], ring_sides, "cloth_black", smooth=hq)
        # Dark round lenses in brass rims, with brass side cages. His eyes never show.
        for sign in (1, -1):
            place = Matrix.Translation(_at(ctx, sign * 0.078, -0.2, 0.03)) @ Matrix.Rotation(math.pi / 2, 4, "X")
            with mb.xf(place):
                mb.lathe([(0.058 * s, -0.012), (0.058 * s, 0.012)], 10 if hq else 5, "brass", smooth=False)
                mb.lathe([(0.046 * s, -0.016), (0.046 * s, 0.016)], 10 if hq else 5, "abyss", smooth=False)
            mb.box(tuple(_at(ctx, sign * 0.15, -0.14, 0.03)), (0.016 * s, 0.1 * s, 0.05 * s), "brass")
            mb.tube(_at(ctx, sign * 0.15, -0.09, 0.04), _at(ctx, sign * 0.2, 0.05, 0.04), 0.007 * s, sides=3, color="brass")
        mb.tube(_at(ctx, -0.03, -0.205, 0.04), _at(ctx, 0.03, -0.205, 0.04), 0.008 * s, sides=3, color="brass")
        # A square jaw, and a tight smirk that lifts on one side.
        mb.sphere(_at(ctx, 0, -0.07, -0.16), (0.15 * s, 0.11 * s, 0.075 * s), 6 if hq else 5, 3, ctx.hero.skin, smooth=hq)
        mb.tube(_at(ctx, -0.055, -0.183, -0.115), _at(ctx, 0.06, -0.178, -0.09), 0.007 * s, sides=3, color="skin_dark", flat=1.4)


def big_guns(ctx):
    """Rook: boulder shoulders, huge arms, a flat slab of chest in a sleeveless vest, and traps."""
    mb, s, g, w, hq = ctx.mb, ctx.s, ctx.g, ctx.w, ctx.hq
    skin = ctx.hero.skin
    detail = (8, 5) if hq else (6, 3)
    for side in ("L", "R"):
        shoulder, elbow = (Vector(p) for p in ctx.joints[f"upper_arm.{side}"][:2])
        wrist = Vector(ctx.joints[f"lower_arm.{side}"][1])
        belly = shoulder + (elbow - shoulder) * 0.55
        with mb.bound_to(f"upper_arm.{side}"):
            mb.sphere(shoulder + (elbow - shoulder) * 0.1, 0.17 * s, detail[0], detail[1], skin, smooth=hq)
            mb.sphere(belly + Vector((0, -0.045, 0)) * s, 0.128 * s, detail[0], detail[1], skin, smooth=hq)  # Bicep.
            if hq:
                mb.sphere(belly + Vector((0, 0.04, 0)) * s, 0.112 * s, detail[0], detail[1], skin, smooth=True)  # Tricep.
        if hq:
            # On LQ a sphere this small shatters against the arm, and the thick limb reads better alone.
            with mb.bound_to(f"lower_arm.{side}"):
                mb.sphere(elbow + (wrist - elbow) * 0.32, 0.112 * s, detail[0], detail[1], skin, smooth=True)

    sides = ctx.q["torso"]
    with mb.bound_to("chest"):
        mb.loft([_body_ring(ctx, rx, ry, z, sides) for rx, ry, z in ((0.24, 0.14, 1.27), (0.13, 0.1, 1.38), (0.085, 0.08, 1.44))], skin, smooth=hq)
        mb.loft([_body_ring(ctx, rx, ry, z, sides) for rx, ry, z in ((0.255, 0.19, 1.06), (0.32, 0.205, 1.28), (0.16, 0.12, 1.39))], "navy", smooth=hq)
        front = 0.205 * g * s
        # The shirt down the middle of the vest, then a bandolier across it, sized for this chest.
        mb.plate([(-0.085 * s, -front, 1.31 * s), (0.085 * s, -front, 1.31 * s), (0.075 * s, -0.19 * g * s, 1.06 * s), (-0.075 * s, -0.19 * g * s, 1.06 * s)], 0.03 * s, ctx.hero.top)

        def on_chest(u):
            # A point on the front of the vest, running from one shoulder down across to the other side's ribs.
            x = (0.27 - 0.5 * u) * w * s
            z = (1.3 - 0.22 * u) * s
            half = 0.3 * w * s
            depth = (0.2 - 0.02 * u) * g * s
            return Vector((x, -depth * math.sqrt(max(0.05, 1 - (x / half) ** 2)) - 0.012 * s, z))

        strap = [on_chest(k / 6) for k in range(7)]
        mb.path(strap, [0.024 * s] * len(strap), 4, "leather")
        for k in range(5 if hq else 3):
            at = on_chest((k + 0.5) / (5 if hq else 3))
            mb.box(tuple(at + Vector((0, -0.016 * s, 0))), (0.035 * s, 0.02 * s, 0.05 * s), "iron_light")
    with mb.bound_to("spine"):
        mb.loft([_body_ring(ctx, rx, ry, z, sides) for rx, ry, z in ((0.225, 0.17, 0.97), (0.25, 0.18, 1.1))], "navy", smooth=hq)
    with mb.bound_to("head"):
        for sign in (1, -1):
            # Copper ear guards, worn on the ears.
            mb.sphere(_at(ctx, sign * 0.205, 0.02, 0.0), (0.04 * s, 0.065 * s, 0.075 * s), 6 if hq else 4, 3, "brass", smooth=False)
        if not hq:
            # The LQ skull is shallow at the front, so its moustache is built into the face.
            mb.box(tuple(_at(ctx, 0, -0.105, -0.1)), (0.2 * s, 0.07 * s, 0.045 * s), ctx.hero.hair)
    if hq:
        moustache(ctx)


def torn_shoulder(ctx, color="navy"):
    """Rook: an Armada coat with the rank ripped off one shoulder, loose threads and all."""
    s, w = ctx.s, ctx.w
    with ctx.mb.bound_to("chest"):
        ctx.mb.box((0.28 * w * s, 0, 1.33 * s), (0.2 * s, 0.17 * s, 0.05 * s), "gold_dark", top_scale=0.8)
        ctx.mb.plate([(-0.31 * w * s, -0.1 * s, 1.34 * s), (-0.22 * w * s, -0.1 * s, 1.35 * s), (-0.31 * w * s, 0.06 * s, 1.3 * s)], 0.02, color)


FEATURES = {f.__name__: f for f in (
    big_guns, morrow_finery, nomad_layers, nomad_headwrap, nomad_scarf, assassin_gear, sorcerer_amulet, sorcerer_hood, sorcerer_robe, sorcerer_sleeves, hair_cap, hair_wild, hair_long, hair_braid, hair_ponytail, hair_slick, hair_side_shave, hair_gray_sides,
    beard_full, goatee, moustache, eyepatch, scar, spectacles, goggles_up, face_mask, hood, bandana, tricorn,
    bicorne, shako, morion, warden_helm, hat_officer, long_coat, short_jacket, cuirass, pauldrons, epaulettes,
    cape, sash, cross_belt, bandolier, apron, tool_belt, tabard, keyring, medals, gold_buttons, high_collar,
    scarf, grapple_gauntlet, iron_arm, chain_wrap, dagger_sheaths, navigator_case, tool_harness, ear_guards,
    torn_shoulder,
)}


CAST = {
    # The hero, kept neutral so any player sees themselves. Warm and scrappy, the only big red accent
    # in the crew so they are always findable in a busy deck brawl.
    "Vane": Hero(skin="skin_mid", hair="hair_black", top="cloth_white", legs="cloth_brown", sleeve="cloth_black", width=0.94, girth=0.94, brow=1, features=[
        ("hair_wild",), ("bandana", "gem_red"), ("short_jacket", "cloth_black"), ("sash", "gem_red"), ("grapple_gauntlet",), ("bandolier",),
    ]),
    "CassianPirate": Hero(skin="skin_light", hair="hair_gray", top="cloth_white", legs="cloth_black", sleeve="faction_a", scale=1.06, width=1.05, features=[
        ("hair_cap",), ("beard_full", 0.34), ("scar",), ("long_coat", "faction_a"), ("gold_buttons",), ("epaulettes", "gold"), ("tricorn",),
    ]),
    "CassianAdmiral": Hero(skin="skin_light", hair="hair_gray", top="navy", legs="enamel", sleeve="enamel", glove="enamel", scale=1.06, width=1.05, brow=2, features=[
        ("hair_cap",), ("beard_full", 0.2), ("scar",), ("long_coat", "enamel", "navy"), ("epaulettes", "gold"), ("medals",), ("gold_buttons",), ("high_collar", "gold"), ("cape", "velvet", 0.26), ("bicorne", "navy", "gold"),
    ]),
    "Morrow": Hero(mouth=False, skin="skin_mid", hair="hair_black", top="gold_dark", legs="cloth_brown", boots="leather_dark", belt="leather", sleeve="faction_a", forearm="faction_a", glove="leather_dark", scale=1.05, width=0.88, girth=0.84, brow=0, iris="eye_dark", features=[
        ("hair_cap",), ("morrow_finery",),
    ]),
    "Rook": Hero(skin="skin_dark", hair="hair_black", top="canvas_dark", legs="navy", sleeve="skin_dark", forearm="skin_dark", scale=1.12, width=1.32, girth=1.28, arm_bulk=1.3, leg_bulk=1.2, iris="eye_dark", features=[
        ("hair_cap",), ("goggles_up",), ("big_guns",),
    ]),
    "Lyra": Hero(skin="skin_mid", hair="hair_white", top="cloth_green", legs="cloth_brown", boots="leather_dark", belt="grass", sleeve="cloth_green", forearm="skin_mid", width=0.86, girth=0.82, iris="eye_dark", features=[
        ("hair_braid",), ("nomad_headwrap",), ("nomad_layers",), ("nomad_scarf",),
    ]),
    "Sable": Hero(mouth=False, skin="skin_light", hair="hair_black", top="cloth_black", legs="cloth_black", boots="leather_dark", belt="leather_dark", sleeve="cloth_black", forearm="cloth_black", glove="leather_dark", scale=0.97, width=0.76, girth=0.8, arm_bulk=0.82, leg_bulk=0.88, brow=0, iris="grass", features=[
        ("sorcerer_hood", "storm_dark"), ("face_mask", "storm"), ("assassin_gear",), ("dagger_sheaths",),
    ]),
    "Thorne": Hero(skin="enamel", hair="hair_black", top="faction_a", legs="faction_a", boots="cloth_black", belt="faction_c", sleeve="cloth_black", scale=1.06, brow=2, iris="faction_b", sclera="abyss", features=[
        ("sorcerer_robe",), ("sorcerer_hood",), ("sorcerer_sleeves",), ("sorcerer_amulet",),
    ]),
    "Krag": Hero(skin="skin_mid", hair="hair_red", top="leather_dark", legs="cloth_black", boots="iron", sleeve="skin_mid", scale=1.2, width=1.42, girth=1.55, brow=2, features=[
        ("beard_full", 0.4), ("eyepatch",), ("bandana", "rust_dark", False), ("apron", "rust_dark"), ("pauldrons", "rust_dark", True), ("chain_wrap",), ("iron_arm", "L"), ("sash", "rust"),
    ]),
    "Vex": Hero(skin="skin_light", hair="hair_white", top="faction_a", legs="cloth_black", sleeve="faction_a", glove="faction_c", width=0.9, girth=0.86, brow=1, features=[
        ("hair_side_shave", False), ("short_jacket", "faction_c", "faction_a"), ("cape", "faction_b", 0.5), ("sash", "faction_b"),
    ]),
    "Vesper": Hero(skin="skin_light", hair="hair_black", top="faction_b", legs="cloth_black", sleeve="faction_b", glove="faction_c", width=0.9, girth=0.86, brow=1, features=[
        ("hair_side_shave", True), ("short_jacket", "faction_c", "faction_b"), ("cape", "faction_a", 0.5), ("sash", "faction_a"),
    ]),
    "Malakor": Hero(skin="skin_mid", hair="hair_black", top="iron", legs="iron", boots="iron", sleeve="iron_light", forearm="iron", glove="iron", scale=1.26, width=1.34, girth=1.4, features=[
        ("warden_helm",), ("cuirass", "iron", "faction_b"), ("pauldrons", "iron_light", True), ("tabard", "faction_a", "faction_b"), ("keyring",), ("cape", "faction_c", 0.32),
    ]),
    "ArmadaSoldier": Hero(skin="skin_light", hair="hair_brown", top="faction_a", legs="enamel", sleeve="faction_a", glove="enamel", features=[
        ("hair_cap",), ("long_coat", "faction_a", "enamel", 0.68), ("cross_belt", "enamel"), ("gold_buttons",), ("shako", "faction_a", "enamel"),
    ]),
    "ArmadaOfficer": Hero(skin="skin_light", hair="hair_blond", top="enamel", legs="enamel", sleeve="faction_a", glove="enamel", width=0.98, features=[
        ("hair_cap",), ("moustache",), ("long_coat", "faction_a", "enamel", 0.5), ("epaulettes", "gold"), ("sash", "gold_dark"), ("gold_buttons",), ("hat_officer", "faction_a"),
    ]),
    "RoyalGuard": Hero(skin="skin_mid", hair="hair_black", top="silver", legs="faction_a", boots="faction_a", sleeve="silver", forearm="silver", glove="gold_dark", scale=1.08, width=1.14, girth=1.1, features=[
        ("morion", "silver", "faction_c"), ("cuirass", "silver", "gold"), ("pauldrons", "gold_dark"), ("tabard", "faction_a", "gold"), ("cape", "faction_a", 0.34),
    ]),
}


def _face(ctx):
    """Portrait-grade face for HQ: almond eyes set into the skull, a lash line, a soft nose. Comms
    portraits and hub close-ups are rendered from this, so it earns its triangles."""
    if not ctx.hq:
        # The base LQ face stands off the skull and has dark eyes, so these replace it.
        if ctx.hero.iris:
            with ctx.mb.bound_to("head"):
                for sign in (1, -1):
                    ctx.mb.box(tuple(_at(ctx, sign * 0.078, -0.16, 0.03)), (0.056 * ctx.s, 0.06 * ctx.s, 0.05 * ctx.s), ctx.hero.iris)
        return
    s = ctx.s
    hero = ctx.hero
    tilt = hero.brow * 0.012
    brow_color = "hair_gray" if hero.hair == "hair_white" else hero.hair
    with ctx.mb.bound_to("head"):
        for sign in (1, -1):
            x = sign * 0.078
            ctx.mb.sphere(_at(ctx, x, -0.172, 0.03), (0.044 * s, 0.016 * s, 0.027 * s), 8, 4, hero.sclera)
            # Pupils sit slightly inward, so the character looks at the viewer instead of through them.
            ctx.mb.sphere(_at(ctx, x - sign * 0.006, -0.183, 0.03), (0.019 * s, 0.008 * s, 0.024 * s), 8, 3, hero.iris or "eye_dark")
            ctx.mb.tube(_at(ctx, x - 0.046, -0.185, 0.05 + sign * 0.0), _at(ctx, x + 0.046, -0.182, 0.05), 0.007 * s, sides=4, color="eye_dark", flat=1.6)
            ctx.mb.tube(_at(ctx, sign * 0.03, -0.192, 0.09 - tilt), _at(ctx, sign * 0.125, -0.166, 0.09 + tilt), 0.012 * s, sides=4, color=brow_color, flat=1.6)
        ctx.mb.sphere(_at(ctx, 0, -0.2, -0.025), (0.026 * s, 0.03 * s, 0.038 * s), 6, 3, hero.skin)
        if hero.mouth:
            ctx.mb.box(tuple(_at(ctx, 0, -0.178, -0.105)), (0.075 * s, 0.018, 0.012 * s), "skin_dark" if hero.skin != "skin_dark" else "hair_black")


def build(mb, name, hq):
    hero = CAST[name]
    q = base._tiers(hq)
    joints = base._joints(hero.scale, hero.width)
    s, g = hero.scale, hero.girth
    ctx = Ctx(mb, hero, joints, hq, q)
    # The base head builder draws skin, eyes and nose. "bald" suppresses its one-size hair.
    look = base.Look(scale=s, width=hero.width, girth=g, skin=hero.skin, hair=hero.hair, shirt=hero.top, trousers=hero.legs, boots=hero.boots, belt=hero.belt, extras=["bald"])
    sleeve = hero.sleeve or hero.top
    forearm = hero.forearm or sleeve
    armless = {f[1] for f in hero.features if f[0] == "iron_arm"}
    for side in ("L", "R"):
        bulk = hero.arm_bulk
        base._limb(mb, joints, f"upper_arm.{side}", 0.075 * s * g * bulk, 0.062 * s * g * bulk, sleeve, q, extend=0.03)
        if side not in armless:
            base._limb(mb, joints, f"lower_arm.{side}", 0.062 * s * g * bulk, 0.05 * s * g * bulk, forearm, q, extend=0.02)
        base._limb(mb, joints, f"thigh.{side}", 0.1 * s * g * hero.leg_bulk, 0.075 * s * g * hero.leg_bulk, hero.legs, q, extend=0.03)
        base._limb(mb, joints, f"shin.{side}", 0.085 * s * g * hero.leg_bulk, 0.07 * s * g * hero.leg_bulk, hero.boots, q, extend=0.02)
    base._torso(mb, joints, look, q)
    base._head(mb, joints, look, q, hq, draw_face=not hq and not hero.iris)
    _face(ctx)
    hand_look = dataclasses.replace(look, skin=hero.glove) if hero.glove else look
    if armless:
        _hands_without(mb, joints, hand_look, q, hq, armless)
    else:
        base._hands_and_feet(mb, joints, hand_look, q, hq)
    for entry in hero.features:
        FEATURES[entry[0]](ctx, *entry[1:])
    mb.socket("head_top", (0, 0, 1.85 * s))
    mb.socket("chest_centre", (0, 0, 1.2 * s))
    mb.socket("portrait_look_at", (0, 0, 1.56 * s))
    return joints


def _hands_without(mb, joints, look, q, hq, skip):
    """Same as the base hands and feet, except sides whose hand is a prosthetic."""
    s = look.scale
    for side, sign in (("L", 1), ("R", -1)):
        if side not in skip:
            wrist = Vector(joints[f"hand.{side}"][0])
            tip = Vector(joints[f"hand.{side}"][1])
            with mb.bound_to(f"hand.{side}"):
                if hq:
                    mb.sphere((wrist + tip) / 2, (0.058 * s, 0.05 * s, 0.075 * s), 8, 4, look.skin)
                    mb.tube(wrist, wrist + (tip - wrist) * 0.6 + Vector((sign * -0.04, -0.05, 0)) * s, 0.018 * s, sides=4, color=look.skin)
                else:
                    mb.box(tuple((wrist + tip) / 2), (0.1 * s, 0.09 * s, 0.14 * s), look.skin)
        ankle = Vector(joints[f"foot.{side}"][0])
        with mb.bound_to(f"foot.{side}"):
            x = ankle.x
            rows = [(0.09, 0.15, 0.0), (0.09, 0.14, 0.09), (0.075, 0.06, 0.17)]
            sides = 8 if hq else 4
            rings = []
            for rx, ry, z in rows:
                ring = []
                for j in range(sides):
                    a = 2 * math.pi * (j + 0.5) / sides
                    ring.append((x + rx * s * math.cos(a), -0.04 * s + ry * s * math.sin(a), z * s))
                rings.append(ring)
            mb.loft(rings, look.boots, smooth=hq)
