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
    eye_scale: float = 1.0  # Bigger for characters whose eyes carry the expression. Above 1 adds a dilated pupil.
    singed_brow: int = 0  # 1 or -1: that side's brow is half burnt away. 1 is the character's left.
    blind_eye: int = 0  # 1 or -1: that side's eye is milky and blind, no pupil. 1 is the character's left.
    brow_color: str = None  # Brows darker than the hair. None uses the hair colour.
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


def sorcerer_hood(ctx, lining="faction_a", shell="cloth_black"):
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
        mb.loft(rings, lambda _i, j: shell if j < outer_faces else lining, smooth=False)
    with mb.bound_to("chest"):
        # A mantle where the cowl falls onto the shoulders, following the body rather than a circle.
        sides = ctx.q["torso"]
        mb.loft([_body_ring(ctx, rx, ry, z, sides) for rx, ry, z in ((0.335, 0.205, 1.25), (0.25, 0.175, 1.36), (0.15, 0.135, 1.46))], shell, smooth=ctx.hq)


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


def _boot_cuffs(ctx, color, flare=1.12, cords=None):
    """A turned-down cuff at the top of each tall boot, and optionally a cord criss-crossed down the front."""
    mb, s, g, hq = ctx.mb, ctx.s, ctx.g, ctx.hq
    for side in ("L", "R"):
        knee, ankle = (Vector(p) for p in ctx.joints[f"shin.{side}"][:2])
        r = 0.085 * s * g * ctx.hero.leg_bulk
        with mb.bound_to(f"shin.{side}"):
            mb.tube(knee + (ankle - knee) * 0.06, knee + (ankle - knee) * 0.2, r * flare, r * (flare - 0.06), sides=8 if hq else 4, color=color)
            if cords and hq:
                for k in range(3):
                    t0, t1 = 0.25 + 0.2 * k, 0.42 + 0.2 * k
                    top = knee + (ankle - knee) * t0 + Vector((0, -r * (1 - 0.18 * t0) * 0.97, 0))
                    low = knee + (ankle - knee) * t1 + Vector((0, -r * (1 - 0.18 * t1) * 0.97, 0))
                    mb.tube(top + Vector((0.04 * s, 0, 0)), low + Vector((-0.035 * s, 0, 0)), 0.006 * s, sides=3, color=cords)
                    mb.tube(top + Vector((-0.04 * s, 0, 0)), low + Vector((0.035 * s, 0, 0)), 0.006 * s, sides=3, color=cords)


def nomad_hair(ctx):
    """Lyra: thick dark-brown waves streaming back on the wind, thin beaded braids by her face, and long
    brown-and-white feathers pinned near her crown."""
    mb, s, hq = ctx.mb, ctx.s, ctx.hq
    hair_long(ctx, 0.46)
    n = 5 if hq else 3
    with mb.bound_to("head"):
        # Locks blown back and to one side.
        for i in range(n):
            a = -1.0 + 2.0 * i / (n - 1)
            x, z = 0.16 * math.sin(a), 0.1 + 0.11 * math.cos(a)
            mb.plate([_at(ctx, x - 0.06, 0.06, z), _at(ctx, x + 0.06, 0.06, z), _at(ctx, x * 1.5 + 0.14, 0.4, z - 0.14)], 0.045 * s, ctx.hero.hair)
        for sign in (1, -1):
            braid = [_at(ctx, sign * 0.19, -0.07, 0.02), _at(ctx, sign * 0.205, -0.09, -0.14), _at(ctx, sign * 0.2, -0.1, -0.28)]
            mb.path(braid, [0.016 * s] * 3, 4 if hq else 3, ctx.hero.hair)
            mb.sphere(_at(ctx, sign * 0.203, -0.095, -0.2), 0.02 * s, 5 if hq else 4, 3, "iron_light", smooth=False)
            mb.sphere(_at(ctx, sign * 0.2, -0.1, -0.3), (0.024 * s, 0.024 * s, 0.03 * s), 5 if hq else 4, 3, "faction_c", smooth=False)
        # Pale feathers with dark tips, pinned at the crown and swept out to the side so their broad face shows.
        feathers = (((0.12, 0.06, 0.2), (0.15, 0.06, 0.06), (-0.012, 0.0, 0.03), "enamel"), ((0.1, 0.09, 0.2), (0.13, 0.1, 0.09), (-0.018, 0.0, 0.026), "canvas"))
        for base, d, u, color in feathers if hq else feathers[:1]:
            b0, d, u = Vector(base), Vector(d), Vector(u)
            vane = [b0 - u * 0.3, b0 + u * 0.3, b0 + d * 0.45 + u * 0.6, b0 + d * 0.76 + u * 0.45, b0 + d * 0.76 - u * 0.45, b0 + d * 0.45 - u * 0.6]
            mb.plate([_at(ctx, *p) for p in vane], 0.01 * s, color)
            mb.plate([_at(ctx, *p) for p in (b0 + d * 0.72 + u * 0.48, b0 + d, b0 + d * 0.72 - u * 0.48)], 0.012 * s, "leather_dark")
        if hq:
            mb.sphere(_at(ctx, 0.09, 0.04, 0.24), 0.026 * s, 5, 3, "faction_c", smooth=False)


def nomad_layers(ctx):
    """Lyra: a fitted emerald waistcoat edged in gold over her cream blouse, a heavy belt with a green sash
    of coin charms and gold fringe, a pouch, brass trinkets and a curved dagger, green-patched knees, and
    tall slouching boots bound with green cord."""
    mb, q, s, g, w, hq = ctx.mb, ctx.q, ctx.s, ctx.g, ctx.w, ctx.hq
    sides = q["torso"]

    def shell(bone, rows, color):
        with mb.bound_to(bone):
            mb.loft([_body_ring(ctx, rx, ry, z, sides) for rx, ry, z in rows], color, smooth=hq)

    shell("chest", [(0.25, 0.175, 1.06), (0.315, 0.19, 1.28), (0.16, 0.12, 1.37)], "faction_b")
    shell("spine", [(0.22, 0.165, 0.92), (0.25, 0.175, 1.1)], "faction_b")
    # The waistcoat is open down the middle: cream blouse between two gold-embroidered edges.
    for bone, z_top, z_low, d_top, d_low in (("chest", 1.34, 1.06, 0.19, 0.18), ("spine", 1.08, 0.93, 0.175, 0.168)):
        with mb.bound_to(bone):
            mb.plate([(-0.05 * s, -d_top * g * s, z_top * s), (0.05 * s, -d_top * g * s, z_top * s), (0.04 * s, -d_low * g * s, z_low * s), (-0.04 * s, -d_low * g * s, z_low * s)], 0.026 * s, "canvas")
            for sign in (1, -1):
                mb.plate([(sign * 0.05 * s, -d_top * g * s, z_top * s), (sign * 0.075 * s, -d_top * g * s, z_top * s), (sign * 0.065 * s, -d_low * g * s, z_low * s), (sign * 0.04 * s, -d_low * g * s, z_low * s)], 0.03 * s, "gold")
    with mb.bound_to("hips"):
        # The sash hangs from her left hip, edged with coins and fringe.
        x0, x1 = 0.1, 0.24
        mb.plate([(x0 * w * s, -0.2 * g * s, 0.9 * s), (x1 * w * s, -0.19 * g * s, 0.9 * s), (x1 * w * s, -0.225 * g * s, 0.62 * s), ((x0 + 0.03) * w * s, -0.235 * g * s, 0.6 * s)], 0.022 * s, "faction_b")
        for k in range(4 if hq else 2):
            x = (x0 + 0.03 + (x1 - x0 - 0.03) * (k + 0.5) / (4 if hq else 2)) * w * s
            mb.sphere((x, -0.245 * g * s, 0.61 * s), (0.02 * s, 0.01 * s, 0.02 * s), 5 if hq else 4, 3, "gold", smooth=False)
            if hq:
                mb.tube((x, -0.235 * g * s, 0.6 * s), (x, -0.235 * g * s, 0.54 * s), 0.006 * s, sides=3, color="gold_dark")
        # A buttoned pouch on the right hip.
        on_hip = Vector((-0.17 * w * s, -0.18 * g * s + 0.03 * s, (0.82 if hq else 0.83) * s))
        mb.box(tuple(on_hip), (0.08 * s, 0.05 * s, 0.08 * s), "leather")
        if hq:
            mb.sphere(tuple(on_hip + Vector((0, -0.027 * s, 0.02 * s))), 0.012 * s, 4, 3, "brass", smooth=False)
            for k, x in enumerate((-0.05, -0.02)):
                hip_y = 0.19 * g * s * math.sqrt(max(0.1, 1 - (x / 0.25) ** 2))
                mb.tube((x * w * s, -hip_y, 0.86 * s), (x * w * s, -hip_y - 0.01 * s, 0.79 * s), 0.005 * s, sides=3, color="brass")
                mb.sphere((x * w * s, -hip_y - 0.012 * s, 0.77 * s), 0.018 * s, 4, 3, "brass", smooth=False)
        # The curved dagger in its green-and-silver scabbard, at the back of her left hip.
        sheath = [Vector((0.23 * w * s, 0.08 * s, 0.98 * s)), Vector((0.27 * w * s, 0.12 * s, 0.78 * s)), Vector((0.26 * w * s, 0.18 * s, 0.6 * s))]
        mb.path(sheath, [0.026 * s, 0.024 * s, 0.012 * s], 4 if hq else 3, "faction_b")
        mb.tube(sheath[0], sheath[0] + Vector((-0.01 * s, -0.01 * s, 0.11 * s)), 0.016 * s, sides=4 if hq else 3, color="silver")
        if hq:
            mb.tube(sheath[1] + Vector((0, 0, 0.03 * s)), sheath[1] - Vector((0, 0, 0.03 * s)), 0.03 * s, sides=4, color="silver")
    for side in ("L", "R"):
        elbow, wrist = (Vector(p) for p in ctx.joints[f"lower_arm.{side}"][:2])
        with mb.bound_to(f"lower_arm.{side}"):
            # Stacked leather wraps, then a beaded bracelet at the wrist.
            mb.tube(elbow + (wrist - elbow) * 0.4, wrist - (wrist - elbow) * 0.2, 0.06 * s, 0.056 * s, sides=6 if hq else 4, color="leather")
            mb.tube(wrist - (wrist - elbow) * 0.18, wrist - (wrist - elbow) * 0.06, 0.058 * s, sides=6 if hq else 4, color="faction_c")
        knee = Vector(ctx.joints[f"shin.{side}"][0])
        r = 0.08 * s * g * ctx.hero.leg_bulk * (1.0 if hq else 0.87)
        with mb.bound_to(f"thigh.{side}"):
            mb.plate([knee + Vector((-0.045 * s, -r, 0.16 * s)), knee + Vector((0.045 * s, -r, 0.16 * s)), knee + Vector((0.045 * s, -r, 0.03 * s)), knee + Vector((-0.045 * s, -r, 0.03 * s))], 0.022 * s, "cloth_green")
    _boot_cuffs(ctx, ctx.hero.boots, 1.2, cords="faction_b")


def nomad_scarf(ctx):
    """Lyra: a thick ribbed emerald scarf wound tight round the neck, trailing back into a patchwork cloak
    of green, olive and earth-toned squares with a frayed hem."""
    mb, s, g, w, hq = ctx.mb, ctx.s, ctx.g, ctx.w, ctx.hq
    with mb.bound_to("chest"):
        mb.lathe([(0.19 * s, 1.27 * s), (0.192 * s, 1.31 * s), (0.18 * s, 1.35 * s), (0.17 * s, 1.38 * s), (0.14 * s, 1.42 * s)], ctx.q["limb"], "faction_b", smooth=False)
    # The cloak, in patches: two columns, three rows, each patch its own cloth. The lowest row is cut ragged.
    colors = ("faction_a", "cloth_green", "leather", "faction_b", "gold_dark", "faction_a") if hq else ("faction_a", "cloth_green", "cloth_green", "faction_a", "faction_a", "leather")
    rows = (("chest", 1.36, 1.1, 0.2, 0.215), ("spine", 1.1, 0.92, 0.2, 0.215), ("hips", 0.92, 0.72, 0.225, 0.255))
    for r, (bone, z_top, z_low, d_top, d_low) in enumerate(rows):
        with mb.bound_to(bone):
            for c, (xa, xb) in enumerate(((-0.25, 0.0), (0.0, 0.25))):
                low = z_low
                poly = [(xa * w * s, d_top * g * s, z_top * s), (xb * w * s, d_top * g * s, z_top * s)]
                if r == 2:
                    poly += [(xb * w * s, d_low * g * s, (low + 0.02) * s), ((xa + xb) / 2 * w * s, d_low * g * s, (low - 0.05) * s), (xa * w * s, d_low * g * s, (low + 0.03) * s)]
                else:
                    poly += [(xb * w * s, d_low * g * s, low * s), (xa * w * s, d_low * g * s, low * s)]
                mb.plate(poly, 0.02 * s + 0.004 * s * c, colors[r * 2 + c])
    with mb.bound_to("chest"):
        # The scarf's long end, blown back over her shoulder into the cloak.
        mb.plate([(0.1 * s, 0.12 * g * s, 1.38 * s), (0.2 * s, 0.14 * g * s, 1.34 * s), (0.22 * s, 0.24 * g * s, 1.06 * s), (0.12 * s, 0.24 * g * s, 1.08 * s)], 0.024 * s, "faction_b")


def assassin_gear(ctx):
    """Sable: a weathered double-breasted grey coat with pewter buttons over a dark vest, crossed leather
    bandoliers with a bone-handled dagger across her chest, twin daggers at her left hip, knife bracers,
    a steel-bracketed recurve bow and a quiver of green-fletched poison arrows, and a poison bottle."""
    mb, q, s, g, w, hq = ctx.mb, ctx.q, ctx.s, ctx.g, ctx.w, ctx.hq
    sides = q["torso"]

    def shell(bone, rows, color):
        with mb.bound_to(bone):
            mb.loft([_body_ring(ctx, rx, ry, z, sides) for rx, ry, z in rows], color, smooth=hq)

    shell("chest", [(0.25, 0.175, 1.06), (0.31, 0.2, 1.24), (0.16, 0.12, 1.38)], "faction_a")
    shell("spine", [(0.22, 0.165, 0.95), (0.25, 0.175, 1.1)], "faction_a")
    with mb.bound_to("chest"):
        # The dark vest shows in a V at the throat; the coat's front laps over it, buttoned twice.
        mb.plate([(-0.06 * s, -0.2 * g * s, 1.35 * s), (0.06 * s, -0.2 * g * s, 1.35 * s), (0, -0.19 * g * s, 1.2 * s)], 0.024 * s, "cloth_black")
        for sign in (1, -1):
            for k in range(3 if hq else 2):
                z = 1.17 - k * (0.07 if hq else 0.1)
                depth = (0.175 + 0.025 * max(0.0, z - 1.06) / 0.18) * g * s + (0.006 if hq else -0.006) * s - (0.004 * s if z < 1.05 else 0.0)
                mb.sphere((sign * 0.055 * s, -depth, z * s), 0.014 * s, 5 if hq else 4, 3, "faction_b", smooth=False)

        def on_chest(u, flip):
            x = (0.27 - 0.52 * u) * w * s * (-1 if flip else 1)
            z = (1.3 - 0.24 * u) * s
            depth = (0.21 - 0.025 * u) * g * s
            return Vector((x, -depth * math.sqrt(max(0.05, 1 - (x / (0.31 * w * s)) ** 2)) - 0.014 * s, z))

        # Two bandoliers crossing her chest.
        for flip in (False, True):
            strap = [on_chest(k / 6, flip) for k in range(7)]
            mb.path(strap, [0.022 * s] * len(strap), 4, "leather")
        # The bone-handled dagger, sheathed diagonally along one strap.
        top, low = on_chest(0.2, False) + Vector((0, -0.018 * s, 0)), on_chest(0.72, False) + Vector((0, -0.02 * s, 0))
        mb.tube(top, low, 0.024 * s, 0.014 * s, sides=4, color="leather_dark")
        grip_end = top + (top - low).normalized() * 0.1 * s
        mb.tube(top, grip_end, 0.016 * s, sides=4 if hq else 3, color="enamel")
        if hq:
            mb.box(tuple(top), (0.07 * s, 0.02 * s, 0.02 * s), "iron_light")

    with mb.bound_to("hips"):
        # Hips wider than the waist: most of what makes her silhouette read as a woman's.
        mb.loft([_body_ring(ctx, rx, ry, z, sides) for rx, ry, z in ((0.27, 0.185, 0.68), (0.33, 0.2, 0.8), (0.235, 0.165, 0.95))], "faction_a", smooth=hq)
        if not hq:
            # The base LQ belt's buckle would be a bright patch in the middle of a dark waist.
            mb.box((0, -0.18 * g * s, 0.93 * s), (0.11 * s, 0.04 * s, 0.09 * s), "leather_dark")
        # Twin curved daggers at her left hip.
        for dy in (0.06, 0.14):
            start = Vector((0.235 * w * s, dy * s - 0.04 * s, 0.98 * s))
            sheath = [start, start + Vector((0.05 * w * s, 0.02 * s, -0.2 * s)), start + Vector((0.07 * w * s, 0.05 * s, -0.36 * s))]
            mb.path(sheath, [0.022 * s, 0.02 * s, 0.01 * s], 4 if hq else 3, "leather_dark")
            mb.tube(start, start + Vector((-0.01 * s, -0.01 * s, 0.1 * s)), 0.014 * s, sides=4 if hq else 3, color="iron_light")
        # The poison bottle on her right hip.
        at = Vector((-0.2 * w * s, -0.165 * g * s, 0.82 * s))
        mb.sphere(at, (0.05 * s, 0.04 * s, 0.065 * s), 6 if hq else 4, 3, "grass", smooth=False)
        mb.tube(at + Vector((0, 0, 0.05 * s)), at + Vector((0.01 * s, 0.01 * s, 0.12 * s)), 0.02 * s, 0.024 * s, sides=4, color="leather")
    columns = 6 if hq else 4
    for side, sign in (("L", 1), ("R", -1)):
        # The coat's skirts, one panel per leg so they part when she moves.
        rings = []
        for rx, ry, z in ((0.27, 0.19, 0.74), (0.3, 0.235, 0.62), (0.33, 0.27, 0.52)):
            ring = []
            for k in range(columns):
                a = math.radians(-89 + 178 * k / (columns - 1))
                ring.append((sign * rx * w * s * math.cos(a), ry * g * s * math.sin(a), z * s))
            rings.append(ring if sign > 0 else ring[::-1])
        with mb.bound_to(f"thigh.{side}"):
            mb.loft(rings, "faction_a", smooth=False)
        # Leather bracers with throwing knives along the outside of each forearm.
        near, far = (Vector(p) for p in ctx.joints[f"lower_arm.{side}"][:2])
        with mb.bound_to(f"lower_arm.{side}"):
            mb.tube(near + (far - near) * 0.3, far - (far - near) * 0.05, 0.058 * s, 0.05 * s, sides=6 if hq else 4, color="leather")
            for k in range(2 if hq else 1):
                out = Vector((sign * (0.056 if hq else 0.049) * s, (0.018 - 0.036 * k) * s, 0))
                mb.tube(near + (far - near) * 0.38 + out, near + (far - near) * 0.85 + out, 0.009 * s, sides=3, color="iron_light")
    # Bow and quiver on her back: a recurve with steel brackets, venom dripping from its upper limb.
    with mb.bound_to("chest"):
        back = 0.2 * g * s
        bow = [(0.2 * w * s, back + 0.02 * s, 1.47 * s), (0.14 * w * s, back, 1.42 * s), (0.34 * w * s, back + 0.015 * s, 1.2 * s), (0.28 * w * s, back + 0.015 * s, 0.98 * s), (0.06 * w * s, back, 0.82 * s), (0.02 * w * s, back + 0.02 * s, 0.86 * s)]
        mb.path([Vector(p) for p in bow], [0.012 * s, 0.016 * s, 0.03 * s, 0.03 * s, 0.016 * s, 0.012 * s], 4, "wood_light")
        mb.tube(Vector(bow[1]), Vector(bow[-2]), 0.005 * s, sides=3, color="canvas")
        if hq:
            for p in (bow[2], bow[3]):
                mb.box(p, (0.05 * s, 0.05 * s, 0.03 * s), "iron_light")
            mb.sphere((bow[0][0], bow[0][1] - 0.01 * s, bow[0][2] - 0.03 * s), (0.012 * s, 0.012 * s, 0.02 * s), 4, 3, "grass", smooth=False)
        mb.tube((-0.15 * w * s, back, 1.0 * s), (-0.25 * w * s, back - 0.004 * s, 1.34 * s), 0.05 * s, 0.056 * s, sides=6 if hq else 4, color="leather")
        for dx, h in ((0.0, 0.2), (0.035, 0.16), (-0.03, 0.14)) if hq else ((0.0, 0.18), (0.03, 0.14)):
            base = Vector(((-0.25 * w + dx) * s, back - 0.004 * s, 1.34 * s))
            tip = base + Vector((-0.02 * s, 0, h * s))
            mb.tube(base, tip, 0.006 * s, sides=3, color="wood_light")
            mb.tube(tip, tip + Vector((0, 0, 0.05 * s)), 0.02 * s, 0.002, sides=4, color="grass")
    with mb.bound_to("head"):
        # Salt-matted strands escaping the cowl, and thin beaded braids along her jaw.
        for sign in (1, -1):
            mb.path([_at(ctx, sign * 0.14, -0.13, 0.08), _at(ctx, sign * 0.175, -0.16, -0.12), _at(ctx, sign * 0.165, -0.15, -0.34)], [0.03 * s, 0.038 * s, 0.012 * s], 5 if hq else 4, ctx.hero.hair)
            mb.sphere(_at(ctx, sign * 0.168, -0.16, -0.24), 0.02 * s, 5 if hq else 4, 3, "faction_b", smooth=False)
        if hq:
            # Heavy black kohl round her pale eyes, and a jagged crimson scar on her left cheekbone.
            for sign in (1, -1):
                ctx.mb.sphere(_at(ctx, sign * 0.078, -0.168, 0.03), (0.054 * s, 0.014 * s, 0.036 * s), 8, 4, "cloth_black")
            mb.path([_at(ctx, 0.06, -0.188, -0.0), _at(ctx, 0.095, -0.18, -0.035), _at(ctx, 0.085, -0.182, -0.055), _at(ctx, 0.125, -0.165, -0.085)], [0.004 * s, 0.007 * s, 0.007 * s, 0.003 * s], 3, "faction_c")
    _boot_cuffs(ctx, ctx.hero.boots, 1.2)


def bosun_build(ctx):
    """Bosun Brill: a barrel of a man. A massive chest and round belly in an indigo-and-cream striped shirt,
    an open, tar-stained navy waistcoat with mismatched buttons, a thick neck, and a bushy grizzled beard
    with beaded braids spilling down his chest. A charcoal watch cap stuck with pins, a tarnished gold
    hoop, and an anchor tattoo on his right cheek. A brass bosun's call on a hemp cord, a coil of rope
    over his right shoulder, and a sagging belt with a knife, a marlinspike and a ring of rusted keys.
    Rolled sleeves over tattooed forearms, huge hands, patched trousers and cord-bound sea boots."""
    mb, q, s, g, w, hq = ctx.mb, ctx.q, ctx.s, ctx.g, ctx.w, ctx.hq
    sides = q["torso"]

    def ring(rx, ry, z, dy=0.0):
        return [(x, y + dy * g * s, z_) for x, y, z_ in _body_ring(ctx, rx, ry, z, sides)]

    # The shirt, in horizontal stripes: chest and the belly below it.
    chest_rows = [(0.27, 0.2, 1.06, -0.02), (0.31, 0.23, 1.14, -0.02), (0.33, 0.235, 1.22, -0.01), (0.32, 0.22, 1.3, 0.0), (0.2, 0.15, 1.38, 0.0)]
    belly_rows = [(0.26, 0.2, 0.84, -0.02), (0.29, 0.23, 0.89, -0.05), (0.31, 0.25, 0.95, -0.06), (0.31, 0.25, 1.01, -0.05), (0.27, 0.2, 1.1, -0.02)]
    if not hq:
        chest_rows = [chest_rows[i] for i in (0, 2, 4)]
        belly_rows = [belly_rows[i] for i in (0, 1, 2, 4)]
    stripe = lambda i, _j: "faction_a" if i % 2 else "faction_b"
    with mb.bound_to("chest"):
        mb.loft([ring(*r) for r in chest_rows], stripe, smooth=hq)
    with mb.bound_to("spine"):
        mb.loft([ring(*r) for r in belly_rows], stripe, smooth=hq)

    def front_y(z):
        # How far forward the shirt is at height z (unscaled), down the middle.
        table = [(r[2], (r[1] - r[3]) * (0.966 if hq else 1.0)) for r in chest_rows]
        for (z0, d0), (z1, d1) in zip(table, table[1:]):
            if z0 <= z <= z1:
                return -(d0 + (d1 - d0) * (z - z0) / (z1 - z0)) * g * s
        return -table[0][1] * g * s

    # The open waistcoat: a thick shell with the front left open, over chest and belly.
    points = 9 if hq else 5
    wall = 0.022

    def vest_rings(rows, opening):
        out = []
        for rx, ry, z, dy in rows:
            def arc(rx_, ry_, backward):
                pts = []
                for k in range(points):
                    a = math.radians(270 + opening + (360 - 2 * opening) * k / (points - 1))
                    pts.append((rx_ * w * s * math.cos(a), (ry_ * math.sin(a) + dy) * g * s, z * s))
                return pts[::-1] if backward else pts
            out.append(arc(rx, ry, False) + arc(rx - wall, ry - wall, True))
        return out

    vest_chest = [(0.295, 0.215, 1.06, -0.02), (0.35, 0.255, 1.22, -0.01), (0.225, 0.17, 1.37, 0.0)]
    vest_belly = [(0.305, 0.25, 0.9, -0.05), (0.33, 0.275, 0.97, -0.06), (0.295, 0.215, 1.08, -0.02)]
    with mb.bound_to("chest"):
        mb.loft(vest_rings(vest_chest, 34), "navy", smooth=False)
    with mb.bound_to("spine"):
        mb.loft(vest_rings(vest_belly, 42), "navy", smooth=False)
        # Mismatched buttons down the left edge.
        a = math.radians(270 + 42)
        for k, (z, color) in enumerate(((1.05, "brass"), (0.99, "iron_light"), (0.95, "brass")) if hq else ((1.0, "brass"),)):
            for (z0, *r0), (z1, *r1) in zip([(r[2], r[0], r[1], r[3]) for r in vest_belly], [(r[2], r[0], r[1], r[3]) for r in vest_belly[1:]]):
                if z0 <= z <= z1:
                    t = (z - z0) / (z1 - z0)
                    rx, ry, dy = (u + (v - u) * t for u, v in zip(r0, r1))
            face = 1.0 if hq else 0.93
            mb.sphere((rx * w * s * math.cos(a) * face, (ry * math.sin(a) * face + dy) * g * s - 0.004 * s, z * s), 0.016 * s, 5 if hq else 4, 3, color, smooth=False)

    # A thick neck.
    with mb.bound_to("neck"):
        mb.tube((0, 0.01 * s, 1.3 * s), (0, 0.01 * s, 1.42 * s), 0.115 * s * g, 0.105 * s * g, sides=8 if hq else 6, color=ctx.hero.skin)

    with mb.bound_to("head"):
        # The beard under the jaw: a bushy mass, grizzled grey.
        mb.sphere(_at(ctx, 0, -0.1, -0.15), (0.15 * s, 0.12 * s, 0.12 * s), 8 if hq else 6, 4 if hq else 3, ctx.hero.hair, smooth=False)
        mb.plate([_at(ctx, -0.15, -0.14, -0.05), _at(ctx, 0.15, -0.14, -0.05), _at(ctx, 0.13, -0.19, -0.2), _at(ctx, 0, -0.21, -0.25), _at(ctx, -0.13, -0.19, -0.2)], 0.06 * s, ctx.hero.hair)
        # A charcoal watch cap with a turned-up cuff, pins stuck in its side.
        with mb.xf(Matrix.Translation(_at(ctx, 0, 0.04, 0))):
            mb.lathe([(0.235 * s, 0.115 * s), (0.236 * s, 0.17 * s)], q["head_s"], "cloth_black", smooth=False)
            mb.lathe([(0.226 * s, 0.168 * s), (0.212 * s, 0.24 * s), (0.15 * s, 0.3 * s), (0.04 * s, 0.322 * s)], q["head_s"], "faction_c", smooth=hq)
        if hq:
            for theta, z, r in ((-55, 0.25, 0.2), (-30, 0.21, 0.214)):
                c, n = math.cos(math.radians(theta)), math.sin(math.radians(theta))
                base, tip = _at(ctx, r * 0.9 * c, 0.04 + r * 0.9 * n, z), _at(ctx, r * 1.18 * c, 0.04 + r * 1.18 * n, z + 0.04)
                mb.tube(base, tip, 0.005 * s, sides=3, color="rust")
                mb.sphere(tip, 0.01 * s, 4, 3, "iron_light", smooth=False)
        # A heavy, tarnished gold hoop in his left ear.
        hoop = [_at(ctx, 0.198 + 0.03 * math.cos(t), -0.01, -0.09 + 0.03 * math.sin(t)) for t in [2 * math.pi * k / 6 for k in range(6)]]
        mb.path(hoop + [hoop[0]], [0.008 * s] * 7, 4 if hq else 3, "gold_dark")
        if hq:
            # Squinting lids, a bulbous sea-worn nose, and a faded indigo anchor on his right cheek.
            for sign in (1, -1):
                mb.sphere(_at(ctx, sign * 0.078, -0.176, 0.046), (0.05 * s, 0.016 * s, 0.016 * s), 8, 3, ctx.hero.skin, smooth=False)
            mb.sphere(_at(ctx, 0, -0.205, -0.035), (0.046 * s, 0.042 * s, 0.044 * s), 8, 4, "skin_mid")
            mb.sphere(_at(ctx, 0.026, -0.215, -0.02), 0.018 * s, 5, 3, "skin_mid", smooth=False)
            tat = [(_at(ctx, -0.1, -0.174, -0.02), _at(ctx, -0.1, -0.172, -0.09)), (_at(ctx, -0.122, -0.166, -0.035), _at(ctx, -0.078, -0.176, -0.035)),
                   (_at(ctx, -0.125, -0.164, -0.07), _at(ctx, -0.1, -0.174, -0.093)), (_at(ctx, -0.1, -0.174, -0.093), _at(ctx, -0.075, -0.178, -0.07))]
            for a, b in tat:
                mb.tube(a, b, 0.004 * s, sides=3, color="faction_a", flat=1.6)
        else:
            mb.box(tuple(_at(ctx, 0, -0.2, -0.04)), (0.08 * s, 0.07 * s, 0.07 * s), "skin_mid")
        # A brown moustache over the grey, so the beard reads grizzled.
        for sign in (1, -1):
            mb.plate([_at(ctx, 0.0, -0.215, -0.075), _at(ctx, sign * 0.11, -0.19, -0.11), _at(ctx, sign * 0.05, -0.212, -0.115)], 0.028 * s, "hair_brown")

    with mb.bound_to("chest"):
        # The beard cascades down his chest: a slab following the shirt, thick and tapering.
        beard = []
        for z, half in ((1.37, 0.15), (1.29, 0.15), (1.2, 0.12), (1.12, 0.06)) if hq else ((1.37, 0.15), (1.24, 0.13), (1.12, 0.05)):
            y = front_y(z)
            beard.append([(-half * s, y - 0.075 * s, z * s), (half * s, y - 0.075 * s, z * s), (half * 0.9 * s, y - 0.01 * s, z * s), (-half * 0.9 * s, y - 0.01 * s, z * s)])
        mb.loft(beard, ctx.hero.hair, smooth=False)
        # A couple of braids in it, bound with tarnished beads and twine.
        for x in (-0.06, 0.06):
            y = front_y(1.12)
            braid = [Vector((x * s, y - 0.05 * s, 1.14 * s)), Vector((x * s, y - 0.07 * s, 1.07 * s)), Vector((x * s, y - 0.09 * s, 1.02 * s))]
            mb.path(braid, [0.016 * s, 0.014 * s, 0.01 * s], 4 if hq else 3, "hair_brown")
            mb.sphere(tuple(braid[1]), 0.016 * s, 5 if hq else 4, 3, "iron_light", smooth=False)
            if hq:
                mb.sphere(tuple(braid[2] + Vector((0, -0.002 * s, 0.012 * s))), 0.012 * s, 4, 3, "rope", smooth=False)

        # A coil of Manila rope slung over his right shoulder, near the neck where the arm can't reach it, and
        # across to his left ribs: separate strands fanning out from the shoulder, front and back.
        def chest_at(z):
            rows = [(r[2], r[0], r[1], r[3]) for r in chest_rows]
            for (z0, *a0), (z1, *a1) in zip(rows, rows[1:]):
                if z0 <= z <= z1:
                    t = (z - z0) / (z1 - z0)
                    return [u + (v - u) * t for u, v in zip(a0, a1)]
            return rows[0][1:]

        def on_surface(x, z, back, lift):
            rx, ry, dy = chest_at(z / s)
            half = rx * w * s
            depth = (ry + (dy if back else -dy)) * g * s * math.sqrt(max(0.05, 1 - (x / half) ** 2)) * (0.966 if hq else 0.9)
            return Vector((x, depth + lift if back else -depth - lift, z))

        # The coil itself hangs on his right shoulder blade: stacked loops lying against his back, each turn
        # offset so the coil reads. One strand runs from it over the shoulder, by the neck, and tucks under the beard.
        cx, cz = -0.15 * w * s, 1.2 * s
        n = 10 if hq else 6
        for k in range(3 if hq else 2):
            rad = (0.12 - 0.012 * k) * s
            loop = []
            for j in range(n):
                t = 2 * math.pi * j / n
                x, z = cx + 0.012 * s * k + rad * math.cos(t), cz - 0.012 * s * k + rad * 1.0 * math.sin(t)
                loop.append(on_surface(x, min(z, 1.36 * s), True, 0.045 * s + 0.03 * s * k))
            mb.path(loop + [loop[0]], [0.022 * s] * (n + 1), 6 if hq else 4, "rope")
        top_x = -0.185 * s
        sling = [on_surface(cx - 0.02 * s, cz + 0.1 * s, True, 0.05 * s), on_surface(top_x, 1.3 * s, True, 0.026 * s),
                 Vector((top_x, 0.1 * s, 1.37 * s)), Vector((top_x, -0.1 * s, 1.37 * s)), on_surface(top_x, 1.3 * s, False, 0.026 * s),
                 on_surface(-0.11 * s, 1.2 * s, False, 0.022 * s)]
        mb.path(sling, [0.022 * s] * len(sling), 6 if hq else 4, "rope")
        # The brass bosun's call on a knotted hemp cord, to the left of the beard.
        x = 0.19 * w * s
        y = front_y(1.2) * math.sqrt(max(0.05, 1 - (x / (0.33 * w * s)) ** 2)) - 0.02 * s
        call = Vector((x, y, 1.2 * s))
        mb.path([Vector((0.09 * s, front_y(1.36) + 0.01 * s, 1.37 * s)), Vector((0.15 * w * s, front_y(1.3) * 0.92 - 0.01 * s, 1.29 * s)), call], [0.007 * s] * 3, 3, "rope")
        mb.tube(call, call + Vector((0.06 * s, -0.004 * s, 0.02 * s)), 0.011 * s, 0.008 * s, sides=5 if hq else 4, color="brass")
        mb.sphere(tuple(call + Vector((0.065 * s, -0.004 * s, 0.022 * s))), 0.02 * s, 6 if hq else 4, 3, "brass", smooth=False)

    with mb.bound_to("hips"):
        # A wide, sagging leather belt with a brass buckle.
        mb.loft([ring(0.26, 0.2, 0.79, -0.02), ring(0.265, 0.205, 0.86, -0.02)], "leather", smooth=hq)
        front = (0.205 + 0.02) * g * s
        mb.box((0, -front - 0.005 * s, 0.83 * s), (0.11 * s, 0.03 * s, 0.08 * s), "brass")
        # A folding knife in its sheath on the right hip.
        mb.box((-0.24 * w * s, -0.17 * g * s, 0.8 * s), (0.05 * s, 0.05 * s, 0.13 * s), "leather_dark")
        if hq:
            mb.tube((-0.24 * w * s, -0.17 * g * s, 0.86 * s), (-0.24 * w * s, -0.17 * g * s, 0.92 * s), 0.014 * s, sides=4, color="wood_mid")
        # A steel marlinspike at the left hip.
        spike_x = (0.28 if hq else 0.25) * w * s
        mb.tube((spike_x, -0.08 * g * s, 0.92 * s), (spike_x + 0.01 * s, -0.1 * g * s, 0.62 * s), 0.016 * s, 0.003 * s, sides=4, color="iron_light")
        # A ring of giant rusted keys hanging at the front of his left hip.
        at = Vector((0.18 * w * s, (-0.2 if hq else -0.18) * g * s + 0.01 * s, 0.77 * s))
        loop = [at + Vector((0.035 * s * math.cos(t), -0.01 * s * math.sin(t), 0.035 * s * math.sin(t))) for t in [2 * math.pi * k / 6 for k in range(6)]]
        mb.path(loop + [loop[0]], [0.008 * s] * 7, 4 if hq else 3, "rust")
        # A short leather hanger from the belt's lower edge down to the ring.
        half = 0.26 * w * s
        belt_y = -(0.2 * math.sqrt(max(0.05, 1 - (at.x / half) ** 2)) + 0.02) * g * s * (0.966 if hq else 0.9)
        mb.tube(Vector((at.x, belt_y + 0.006 * s, 0.805 * s)), at + Vector((0, -0.01 * s, 0.033 * s)), 0.009 * s, sides=4 if hq else 3, color="leather")
        for k, dx in enumerate((-0.025, 0.0, 0.025) if hq else (-0.015, 0.015)):
            top = at + Vector((dx * s, 0.0, -0.028 * s))
            mb.tube(top, top + Vector((dx * 0.4 * s, -0.005 * s, -0.11 * s)), 0.008 * s, sides=4, color="rust_dark")
            mb.box(tuple(top + Vector((dx * 0.4 * s + 0.012 * s, -0.005 * s, -0.1 * s))), (0.022 * s, 0.01 * s, 0.02 * s), "rust_dark")

    for side, sign in (("L", 1), ("R", -1)):
        shoulder, elbow = (Vector(p) for p in ctx.joints[f"upper_arm.{side}"][:2])
        wrist, tip = (Vector(p) for p in ctx.joints[f"hand.{side}"][:2])
        bulk = ctx.hero.arm_bulk
        with mb.bound_to(f"upper_arm.{side}"):
            # Round, heavy shoulders, so the silhouette reads as a barrel rather than a box.
            mb.sphere(shoulder + (elbow - shoulder) * 0.12 + Vector((sign * 0.03 * s, 0, 0)), 0.12 * s * g, 8 if hq else 6, 4 if hq else 3, "faction_a", smooth=hq)
            # The rolled-up, frayed sleeve.
            mb.tube(shoulder + (elbow - shoulder) * 0.78, elbow + (elbow - shoulder) * 0.02, 0.07 * s * g * bulk, sides=8 if hq else 4, color="faction_b")
        with mb.bound_to(f"lower_arm.{side}"):
            if hq:
                # Faded tattoos of waves and an anchor.
                mid = elbow + (wrist - elbow) * 0.5
                r = 0.058 * s * g * bulk
                mb.tube(mid + Vector((sign * r * 0.5, -r * 0.88, 0.04 * s)), mid + Vector((sign * r * 0.5, -r * 0.88, -0.05 * s)), 0.006 * s, sides=3, color="faction_a", flat=1.6)
                mb.tube(mid + Vector((sign * r * 0.88, -r * 0.45, 0.0)), mid + Vector((sign * r * 0.88, -r * 0.45, -0.07 * s)), 0.006 * s, sides=3, color="faction_a", flat=1.6)
        with mb.bound_to(f"hand.{side}"):
            # Huge calloused hands.
            if hq:
                mb.sphere((wrist + tip) / 2, (0.07 * s, 0.06 * s, 0.085 * s), 8, 4, ctx.hero.skin)
            else:
                mb.box(tuple((wrist + tip) / 2), (0.12 * s, 0.11 * s, 0.15 * s), ctx.hero.skin)
        # Patches on the baggy trousers.
        hip, knee = (Vector(p) for p in ctx.joints[f"thigh.{side}"][:2])
        t = 0.45 if sign > 0 else 0.7
        r = (0.1 - 0.025 * t) * s * g * ctx.hero.leg_bulk * (0.97 if hq else 0.76)
        mid = hip + (knee - hip) * t
        with mb.bound_to(f"thigh.{side}"):
            mb.plate([mid + Vector((-0.05 * s, -r, 0.06 * s)), mid + Vector((0.05 * s, -r, 0.06 * s)), mid + Vector((0.05 * s, -r, -0.05 * s)), mid + Vector((-0.05 * s, -r, -0.05 * s))], 0.02 * s, "canvas_dark")
    _boot_cuffs(ctx, ctx.hero.boots, 1.18, cords="rope")


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
        for k, x in enumerate((0.09, 0.15, 0.21) if hq else (0.1, 0.16)):
            on_hip = 0.17 * g * s * math.sqrt(max(0.1, 1 - (x / 0.3) ** 2))
            top = Vector((x * w * s, -on_hip - 0.014 * s, 0.9 * s))
            low = top + Vector((0, -0.006 * s, -0.16 * s))
            mb.tube(top, low, 0.008 * s, sides=3, color="brass")
            mb.sphere(top, 0.022 * s, 5 if hq else 4, 3, "brass", smooth=False)
            mb.box(tuple(low + Vector((0.012 * s, 0, 0.018 * s))), (0.03 * s, 0.012 * s, 0.022 * s), "brass")
    with mb.bound_to("head"):
        # A black tricorn with gold braid, the hair tucked up under it. The brim turns up most at its three
        # corners, and the braid is only a thin band along the edge.
        z = ctx.centre.z + 0.12 * s
        ring_sides = 12 if hq else 6

        def brim_ring(scale_r, lift):
            ring = []
            for j in range(ring_sides):
                a = 2 * math.pi * (j + 0.5) / ring_sides
                corner = 0.5 + 0.5 * math.cos(3 * (a + math.pi / 2))
                lobe = 1.0 + 0.25 * corner
                ring.append((0.3 * s * scale_r * lobe * math.cos(a), 0.3 * s * scale_r * lobe * math.sin(a), z + (lift * (0.3 + 0.7 * corner)) * s))
            return ring

        mb.loft([brim_ring(0.62, 0.0), brim_ring(0.85, 0.03), brim_ring(1.0, 0.11)], "cloth_black")
        edge = [Vector(p) for p in brim_ring(1.0, 0.11)]
        mb.path(edge + [edge[0]], [0.011 * s] * (len(edge) + 1), 4, "gold")  # A braided cord along the very edge.
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
        if hq:
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


def stormcaller_trainee(ctx):
    """Ivo, the jittery trainee stormcaller: slight, wiry and far too small for the storms he summons.
    Enormous pale-blue eyes, a static-charged bush of dark frizz with a burnt-white streak down the right,
    one brow half singed off, soot smudges and branching Lichtenberg scars down his right cheek and neck.
    A singed linen high collar under an oversized, patched slate oilskin coat worn open over a patchwork
    leather vest laced with copper mesh. Harness belts packed with glowing Leyden jars and brass ampoules,
    copper wire spools, a dangling weather dial and a water-logged journal. A coiled copper-and-brass
    grounding gauntlet on his right arm, a bulky insulated mitt on his left, baggy patched trousers, and
    greased boots trailing grounding chains."""
    import copy
    mb, q, s, g, w, hq = ctx.mb, ctx.q, ctx.s, ctx.g, ctx.w, ctx.hq
    hero = ctx.hero
    right = -1  # The character's right side is -X.

    # ---- hair: a static-charged bush, with a burnt-white streak down the right side.
    hair_cap(ctx)
    with mb.bound_to("head"):
        spikes = 15 if hq else 6
        for k in range(spikes):
            t = k / (spikes - 1)
            a = -1.3 + 2.6 * t  # Across the crown, ear to ear.
            lean = math.sin(k * 2.7) * 0.06
            root = _at(ctx, 0.15 * math.sin(a), 0.05 + 0.08 * math.cos(k * 1.9), 0.11 + 0.1 * math.cos(a))
            tip = _at(ctx, 0.3 * math.sin(a) + lean, 0.07 + 0.12 * math.cos(k * 1.3), 0.26 + 0.13 * math.cos(a) + 0.04 * math.sin(k * 3.1))
            mb.tube(root, tip, 0.07 * s, 0.006 * s, sides=4 if hq else 3, color=hero.hair)
        # The streak cascades down the right temple, frayed at the ends.
        streak = [(-0.17, -0.1, 0.16, -0.27, -0.12, 0.02), (-0.19, -0.04, 0.12, -0.3, -0.06, -0.06), (-0.16, -0.15, 0.2, -0.24, -0.17, 0.05)]
        for x0, y0, z0, x1, y1, z1 in (streak if hq else streak[:1]):
            mb.tube(_at(ctx, x0, y0, z0), _at(ctx, x1, y1, z1), 0.045 * s, 0.006 * s, sides=4 if hq else 3, color="hair_white")
        if hq:
            for x0, y0, z0 in ((-0.27, -0.12, 0.02), (-0.3, -0.06, -0.06)):
                for dz in (-0.04, 0.03):
                    mb.tube(_at(ctx, x0, y0, z0), _at(ctx, x0 - 0.04, y0 - 0.01, z0 + dz), 0.008 * s, 0.002 * s, sides=3, color="hair_gray")

        # ---- face: a slack, breathless mouth, soot, and lightning scars.
        mb.sphere(_at(ctx, 0, -0.176, -0.108), (0.034 * s, 0.012 * s, 0.026 * s), 8 if hq else 4, 3, "eye_dark", smooth=False)
        if hq:
            for x, z, rx, rz in ((0.115, -0.05, 0.03, 0.014), (0.04, -0.16, 0.022, 0.008)):
                mb.sphere(_at(ctx, x, -0.178 + 0.012 * abs(x) * 6, z), (rx * s, 0.004 * s, rz * s), 6, 3, "storm_dark", smooth=False)
            # A Lichtenberg figure branching down the right cheek and on toward the neck.
            trunk = [(-0.09, -0.18, -0.01), (-0.12, -0.165, -0.08), (-0.13, -0.14, -0.16), (-0.12, -0.11, -0.24)]
            mb.path([_at(ctx, *p) for p in trunk], [0.006 * s, 0.005 * s, 0.004 * s, 0.003 * s], 3, "rust")
            for (x0, y0, z0), (dx, dz) in zip(trunk[:3], ((-0.035, -0.02), (0.03, -0.03), (-0.03, -0.035))):
                mb.tube(_at(ctx, x0, y0, z0), _at(ctx, x0 + dx, y0 + 0.008, z0 + dz), 0.004 * s, 0.001 * s, sides=3, color="rust")

    # ---- a thin neck under a frayed, singed linen high collar.
    with mb.bound_to("neck"):
        mb.tube((0, 0.01 * s, 1.3 * s), (0, 0.01 * s, 1.42 * s), 0.07 * s, 0.064 * s, sides=8 if hq else 4, color=hero.skin)
        if hq:
            mb.path([(-0.06 * s, -0.045 * s, 1.4 * s), (-0.07 * s, -0.04 * s, 1.36 * s), (-0.06 * s, -0.05 * s, 1.32 * s)], [0.004 * s, 0.003 * s, 0.002 * s], 3, "rust")
    with mb.bound_to("chest"):
        mb.lathe([(0.11 * s, 1.31 * s), (0.125 * s, 1.43 * s)], q["limb"], hero.top, smooth=False, caps=(False, False))
        if hq:
            for k in range(5):
                a = math.radians(200 + 28 * k)
                mb.tube((0.125 * s * math.cos(a), 0.125 * s * math.sin(a), 1.43 * s), (0.13 * s * math.cos(a), 0.13 * s * math.sin(a), 1.455 * s), 0.012 * s, 0.002 * s, sides=3, color="storm_dark")

    # ---- the oversized oilskin coat, worn open over the patchwork vest. Cut for someone bigger.
    big = copy.copy(ctx)
    big.w, big.g = w * 1.16, g * 1.2
    long_coat(big, "storm", "leather", tail_len=0.34)
    with mb.bound_to("chest"):
        # A standing coat collar behind the neck, and shoulders that slump past his own.
        mb.plate([(-0.17 * s, 0.07 * s, 1.36 * s), (0.17 * s, 0.07 * s, 1.36 * s), (0.2 * s, 0.1 * s, 1.52 * s), (-0.2 * s, 0.1 * s, 1.52 * s)], 0.025 * s, "storm")
        for side in (1, -1):
            mb.sphere((side * 0.26 * w * s, 0.0, 1.31 * s), (0.11 * s, 0.13 * g * s, 0.07 * s), 6 if hq else 4, 3, "storm", smooth=False)
        # Copper mesh woven through the vest: bands across the open front.
        for z in ((1.24, 1.16, 1.08) if hq else (1.16,)):
            mb.box((0, -0.205 * g * s, z * s), (0.17 * s, 0.012 * s, 0.022 * s), "rust")
        if hq:
            for x, z, c in ((-0.07, 1.2, "leather_dark"), (0.06, 1.12, "canvas_dark"), (-0.3, 1.0, "leather")):
                y = -0.212 * g * s if abs(x) < 0.2 else -0.16 * g * s
                mb.box((x * s, y, z * s), (0.06 * s, 0.012 * s, 0.06 * s), c)

    # ---- oversized coat cuffs on both arms.
    for side in ("L", "R"):
        elbow, wrist = (Vector(p) for p in ctx.joints[f"lower_arm.{side}"])
        with mb.bound_to(f"lower_arm.{side}"):
            if side == "L":
                mb.tube(elbow.lerp(wrist, 0.72), elbow.lerp(wrist, 1.02), 0.07 * s, 0.085 * s, sides=8 if hq else 4, color="storm")

    # ---- the right arm: a gauntlet of tightly coiled copper wire and brass rings, to ground his magic.
    elbow, wrist = (Vector(p) for p in ctx.joints["lower_arm.R"])
    with mb.bound_to("lower_arm.R"):
        mb.tube(elbow.lerp(wrist, 0.18), elbow.lerp(wrist, 1.0), 0.06 * s, 0.056 * s, sides=8 if hq else 4, color="rust")
        if hq:
            for k in range(6):
                t = 0.22 + 0.13 * k
                mb.tube(elbow.lerp(wrist, t - 0.025), elbow.lerp(wrist, t + 0.025), 0.068 * s, 0.068 * s, sides=8, color="brass" if k % 2 else "rust_dark")
            # A grounding lead running from the gauntlet back up to the harness.
            shoulder = Vector(ctx.joints["upper_arm.R"][0])
            mb.path([elbow.lerp(wrist, 0.3) + Vector((0, 0.05, 0)) * s, elbow + Vector((0, 0.07, 0.02)) * s, shoulder.lerp(elbow, 0.5) + Vector((0, 0.09, 0)) * s], [0.009 * s] * 3, 3, "rust")
    # A bulky insulated mitt on the left hand: nothing about him matches.
    wrist_l, tip_l = (Vector(p) for p in ctx.joints["hand.L"])
    with mb.bound_to("hand.L"):
        mb.sphere((wrist_l + tip_l) / 2, (0.075 * s, 0.066 * s, 0.09 * s), 8 if hq else 4, 4 if hq else 3, "canvas_dark", smooth=False)
        mb.tube(wrist_l + (wrist_l - tip_l) * 0.15, wrist_l + (tip_l - wrist_l) * 0.2, 0.072 * s, 0.07 * s, sides=8 if hq else 4, color="leather_dark")

    # ---- harness belts packed with stormcatcher gear.
    with mb.bound_to("chest"):
        for sign in (1, -1):
            mb.tube((sign * 0.2 * s, -0.17 * g * s, 1.32 * s), (-sign * 0.16 * s, -0.215 * g * s, 1.02 * s), 0.02 * s, sides=4, color="leather_dark", flat=1.5)
        if hq:
            # Brass ampoules along the left strap, each tip sparking.
            for k in range(4):
                t = (k + 0.6) / 5
                x, y, z = 0.2 - 0.36 * t, -0.17 - 0.045 * t, 1.32 - 0.3 * t
                mb.tube((x * s, (y - 0.02) * g * s, (z - 0.035) * s), (x * s, (y - 0.02) * g * s, (z + 0.035) * s), 0.014 * s, sides=4, color="brass")
                mb.sphere((x * s, (y - 0.02) * g * s, (z + 0.045) * s), 0.011 * s, 4, 3, "lightning", smooth=False)
    with mb.bound_to("hips"):
        # A second, sagging belt, slung low, with the gear hanging off it.
        mb.lathe([(0.205 * w * s, 0.84 * s), (0.205 * w * s, 0.875 * s)], q["torso"], "leather_dark", smooth=False, caps=(False, False))
        jars = ((-0.16, 0.0), (0.0, -0.02), (0.16, 0.01)) if hq else ((-0.12, 0.0),)
        for x, dz in jars:
            centre = Vector((x * s, -0.2 * g * s, (0.79 + dz) * s))
            # Leyden jars: glass full of trapped blue-white static, brass-capped.
            mb.tube(centre + Vector((0, 0, -0.05)) * s, centre + Vector((0, 0, 0.04)) * s, 0.032 * s, 0.03 * s, sides=6 if hq else 4, color="lightning")
            mb.tube(centre + Vector((0, 0, 0.04)) * s, centre + Vector((0, 0, 0.065)) * s, 0.034 * s, 0.026 * s, sides=6 if hq else 4, color="brass")
            if hq:
                mb.tube(centre + Vector((0, 0, 0.065)) * s, centre + Vector((0, 0, 0.1)) * s, 0.005 * s, sides=3, color="brass")
                mb.sphere(centre + Vector((0, 0, 0.105)) * s, 0.01 * s, 4, 3, "brass", smooth=False)
        if hq:
            # A spool of copper wire on his right hip, its loose end trailing.
            spool = Vector((-0.24 * w * s, -0.06 * g * s, 0.8 * s))
            mb.tube(spool + Vector((0.03, 0, 0)) * s, spool + Vector((-0.03, 0, 0)) * s, 0.05 * s, sides=8, color="rust")
            mb.tube(spool + Vector((0.035, 0, 0)) * s, spool + Vector((-0.035, 0, 0)) * s, 0.02 * s, sides=6, color="brass")
            mb.path([spool + Vector((-0.02, -0.04, -0.02)) * s, spool + Vector((-0.02, -0.06, -0.1)) * s, spool + Vector((0.01, -0.05, -0.17)) * s], [0.004 * s] * 3, 3, "rust")
            # A brass weather dial dangling from the left of the belt on a short chain.
            dial = Vector((0.23 * w * s, -0.12 * g * s, 0.72 * s))
            mb.tube(dial + Vector((0, 0, 0.13)) * s, dial + Vector((0, 0, 0.05)) * s, 0.005 * s, sides=3, color="iron_light")
            with mb.xf(Matrix.Translation(dial) @ Matrix.Rotation(math.pi / 2, 4, "X")):
                mb.lathe([(0.05 * s, -0.012 * s), (0.05 * s, 0.012 * s)], 8, "brass", smooth=False)
            mb.box(tuple(dial + Vector((0, -0.013, 0)) * s), (0.07 * s, 0.004 * s, 0.07 * s), "parchment")
            mb.box(tuple(dial + Vector((0.01, -0.016, 0.01)) * s), (0.006 * s, 0.003 * s, 0.04 * s), "eye_dark")
            # A water-logged journal crammed into the back of the belt, pages fanned.
            book = Vector((0.06 * s, 0.2 * g * s, 0.86 * s))
            mb.box(tuple(book), (0.15 * s, 0.05 * s, 0.11 * s), "leather")
            mb.box(tuple(book + Vector((0.004, 0, 0.004)) * s), (0.14 * s, 0.055 * s, 0.1 * s), "parchment")

    # ---- baggy, patched trousers tucked into bulky greased boots trailing grounding chains.
    _boot_cuffs(ctx, "leather_dark", flare=1.22)
    for side, sign in (("L", 1), ("R", -1)):
        hip, knee = (Vector(p) for p in ctx.joints[f"thigh.{side}"][:2])
        if hq:
            with mb.bound_to(f"thigh.{side}"):
                at = hip.lerp(knee, 0.55)
                mb.box(tuple(at + Vector((sign * 0.0, -0.095 * g * s * hero.leg_bulk, 0))), (0.07 * s, 0.01 * s, 0.08 * s), "canvas_dark" if side == "L" else "leather")
        ankle = Vector(ctx.joints[f"foot.{side}"][0])
        with mb.bound_to(f"foot.{side}"):
            heel = ankle + Vector((0, 0.07, -0.02)) * s
            ground = Vector((ankle.x + sign * 0.03 * s, ankle.y + 0.24 * s, 0.01 * s))
            mb.tube(heel + Vector((0.06, 0, 0.04)) * s, heel + Vector((-0.06, 0, 0.04)) * s, 0.012 * s, sides=4, color="iron")
            if hq:
                links = 4
                for k in range(links):
                    p0, p1 = heel.lerp(ground, k / links), heel.lerp(ground, (k + 1) / links)
                    mb.tube(p0, p1, 0.011 * s, sides=4, color="iron_light", flat=0.5 if k % 2 else 2.0)
            else:
                mb.tube(heel, ground, 0.012 * s, sides=3, color="iron_light")


def _front_shell(ctx, rows, wall=0.02):
    """Loft rings for a thick panel over the front of the body, such as an apron. Each row is
    (rx, ry, z, half-angle in degrees): an arc centred on the front, given thickness inward."""
    s, w, g = ctx.s, ctx.w, ctx.g
    points = 9 if ctx.hq else 5
    out = []
    for rx, ry, z, half in rows:
        def arc(rx_, ry_, backward):
            pts = []
            for k in range(points):
                a = math.radians(270 - half + 2 * half * k / (points - 1))
                pts.append((rx_ * w * s * math.cos(a), ry_ * g * s * math.sin(a), z * s))
            return pts[::-1] if backward else pts
        out.append(arc(rx, ry, False) + arc(rx - wall, ry - wall, True))
    return out


def _front_y(ctx, rows, x, z):
    """The outer surface of a _front_shell panel at (x, z), both scaled, as a y value."""
    s, w, g = ctx.s, ctx.w, ctx.g
    rows = sorted(rows, key=lambda r: r[2])
    rx, ry = rows[0][0], rows[0][1]
    for (rx0, ry0, z0, _), (rx1, ry1, z1, _) in zip(rows, rows[1:]):
        if z0 * s <= z <= z1 * s:
            t = (z - z0 * s) / ((z1 - z0) * s)
            rx, ry = rx0 + (rx1 - rx0) * t, ry0 + (ry1 - ry0) * t
    if z > rows[-1][2] * s:
        rx, ry = rows[-1][0], rows[-1][1]
    return -ry * g * s * math.sqrt(max(0.05, 1 - (x / (rx * w * s)) ** 2))


def _tallies(mb, frame, groups, color, radius, gap=5.6):
    """Tally-mark tattoos: groups of four strokes struck through by a fifth. frame(u, v) -> a point on the
    skin, u running along the row one unit per stroke, v up the stroke from 0 to 1."""
    for k in range(groups):
        u0 = k * gap
        for j in range(4):
            mb.tube(frame(u0 + j, 0.0), frame(u0 + j, 1.0), radius, sides=3, color=color)
        mb.tube(frame(u0 - 0.5, 0.15), frame(u0 + 3.5, 0.85), radius, sides=3, color=color)


def master_gunner(ctx):
    """Hask, the pressed master gunner: broad, heavily muscled and utterly still. A shaved, soot-weathered
    skull ruled with black tally-mark tattoos from the right temple down the neck and in rows down both
    forearms. An angular, grim face: powder stippling, a flash burn, salt-and-ash stubble on a set jaw, and a
    vertical scar through the left brow over a milky, blind eye. A sleeveless off-white linen shirt under a
    scorched bull-hide gunner's apron on leather straps and tarnished brass buckles. A cracked bandolier with
    brass powder flasks, a horn priming flask and iron priming spikes. A riveted press-gang shackle on his
    right wrist, its chain snapped to a few links. A wide soot-dark belt with canvas shot pouches and coils of
    smouldering slow-match, tar-stained dark canvas breeches, and huge rope-callused hands."""
    mb, q, s, g, w, hq = ctx.mb, ctx.q, ctx.s, ctx.g, ctx.w, ctx.hq
    hero = ctx.hero
    skin = hero.skin
    sides = q["torso"]
    detail = (8, 4) if hq else (6, 3)
    ink = "eye_dark"

    # ---- arms: boulder shoulders, heavy biceps and forearms, bare from the shoulder.
    for side in ("L", "R"):
        shoulder, elbow = (Vector(p) for p in ctx.joints[f"upper_arm.{side}"][:2])
        wrist = Vector(ctx.joints[f"lower_arm.{side}"][1])
        belly = shoulder.lerp(elbow, 0.55)
        with mb.bound_to(f"upper_arm.{side}"):
            mb.sphere(shoulder.lerp(elbow, 0.1), 0.155 * s, *detail, skin, smooth=hq)  # Deltoid.
            mb.sphere(belly + Vector((0, -0.04, 0)) * s, 0.118 * s, *detail, skin, smooth=hq)  # Bicep.
            if hq:
                mb.sphere(belly + Vector((0, 0.04, 0)) * s, 0.104 * s, *detail, skin, smooth=True)  # Tricep.
        if hq:
            with mb.bound_to(f"lower_arm.{side}"):
                mb.sphere(elbow.lerp(wrist, 0.3), 0.104 * s, *detail, skin, smooth=True)

    # ---- torso: traps climbing into a thick neck, and a slab of chest in the sleeveless linen shirt.
    shirt = ((0.255, 0.19, 1.06), (0.32, 0.205, 1.28), (0.17, 0.125, 1.38))
    with mb.bound_to("chest"):
        mb.loft([_body_ring(ctx, rx, ry, z, sides) for rx, ry, z in ((0.24, 0.14, 1.27), (0.13, 0.1, 1.38), (0.085, 0.08, 1.44))], skin, smooth=hq)
        mb.loft([_body_ring(ctx, rx, ry, z, sides) for rx, ry, z in shirt], hero.top, smooth=hq)
    with mb.bound_to("spine"):
        mb.loft([_body_ring(ctx, rx, ry, z, sides) for rx, ry, z in ((0.225, 0.17, 0.97), (0.25, 0.18, 1.1))], hero.top, smooth=hq)
    with mb.bound_to("neck"):
        mb.tube((0, 0.01 * s, 1.3 * s), (0, 0.01 * s, 1.45 * s), 0.112 * s * g, 0.1 * s * g, sides=8 if hq else 6, color=skin)

    # ---- the bull-hide apron: a thick panel over the front, bib to knees, scorched.
    bib = [(0.27, 0.215, 1.06, 46), (0.31, 0.228, 1.18, 38), (0.33, 0.225, 1.3, 28)]
    waist = [(0.26, 0.215, 0.95, 48), (0.27, 0.215, 1.07, 46)]
    skirt = [(0.26, 0.218, 0.96, 50), (0.27, 0.235, 0.78, 50), (0.28, 0.25, 0.57, 47)]
    with mb.bound_to("chest"):
        mb.loft(_front_shell(ctx, bib), "leather", smooth=False)
    with mb.bound_to("spine"):
        mb.loft(_front_shell(ctx, waist), "leather", smooth=False)
    with mb.bound_to("hips"):
        mb.loft(_front_shell(ctx, skirt), "leather", smooth=False)

    torso_front = waist[:1] + bib
    with mb.bound_to("chest"):
        # Heavy neck strap from the bib's corners up round the back of the neck, on tarnished brass buckles.
        corner_x = 0.33 * w * s * math.sin(math.radians(28))
        for sign in (1, -1):
            corner = Vector((sign * corner_x, _front_y(ctx, bib, corner_x, 1.3 * s) - 0.004 * s, 1.29 * s))
            strap = [corner, Vector((sign * 0.15, -0.12, 1.43)) * s, Vector((sign * 0.12, 0.11, 1.44)) * s, Vector((0, 0.15, 1.43)) * s]
            mb.path(strap, [0.016 * s] * 4, 4 if hq else 3, "leather_dark")
            mb.box(tuple(corner + Vector((0, -0.01, 0.0)) * s), (0.05 * s, 0.014 * s, 0.045 * s), "gold_dark")
            if hq:
                mb.box(tuple(corner + Vector((0, -0.018, 0.0)) * s), (0.03 * s, 0.008 * s, 0.026 * s), "leather_dark")
        if hq:
            # Scorch marks burnt into the hide.
            for x, z, rx, rz in ((0.09, 1.21, 0.045, 0.03), (-0.13, 1.11, 0.03, 0.04), (0.02, 1.27, 0.022, 0.016)):
                mb.sphere((x * s, _front_y(ctx, bib, x * s, z * s), z * s), (rx * s, 0.006 * s, rz * s), 6, 3, "leather_dark", smooth=False)
    if hq:
        with mb.bound_to("hips"):
            for x, z, rx, rz in ((0.1, 0.7, 0.05, 0.035), (-0.08, 0.6, 0.035, 0.05), (0.16, 0.58, 0.02, 0.02)):
                mb.sphere((x * s, _front_y(ctx, skirt, x * s, z * s), z * s), (rx * s, 0.006 * s, rz * s), 6, 3, "rust_dark", smooth=False)

    # ---- a cracked leather bandolier from his left shoulder down to his right hip.
    def on_front(u):
        x = (0.19 - 0.46 * u) * w * s
        z = (1.3 - 0.33 * u) * s
        return Vector((x, _front_y(ctx, torso_front, x, z) - 0.014 * s, z))

    with mb.bound_to("chest"):
        over = [Vector((0.22 * w, 0.02 * g, 1.42)) * s, Vector((0.21 * w, -0.13 * g, 1.38)) * s]
        front = [on_front(k / 6) for k in range(7)]
        mb.path(over + front, [0.028 * s] * (len(over) + len(front)), 4 if hq else 3, "leather_dark")
        if hq:
            back = [over[0], Vector((0.19 * w, 0.17 * g, 1.34)) * s, Vector((0.0, 0.235 * g, 1.18)) * s, Vector((-0.2 * w, 0.2 * g, 1.02)) * s]
            mb.path(back, [0.028 * s] * 4, 4, "leather_dark")
            # Cracks in the old leather.
            for u in (0.18, 0.55):
                at = on_front(u)
                mb.box(tuple(at + Vector((0, -0.012, 0)) * s), (0.05 * s, 0.006 * s, 0.006 * s), "leather")
            # Brass powder-measuring flasks.
            for u in (0.3, 0.45, 0.6):
                at = on_front(u) + Vector((0, -0.03, 0)) * s
                mb.tube(at + Vector((0, 0, -0.045)) * s, at + Vector((0, 0, 0.035)) * s, 0.024 * s, 0.02 * s, sides=6, color="brass", flat=0.7)
                mb.tube(at + Vector((0, 0, 0.035)) * s, at + Vector((0, 0, 0.065)) * s, 0.008 * s, 0.006 * s, sides=4, color="iron_light")
            # Slender iron priming spikes tucked under the strap, ring heads up.
            for k in range(3):
                at = on_front(0.08 + 0.05 * k) + Vector((0, -0.016, 0)) * s
                mb.tube(at + Vector((0, 0, 0.06)) * s, at + Vector((0.01, 0, -0.08)) * s, 0.006 * s, 0.001 * s, sides=3, color="iron_light")
                mb.tube(at + Vector((-0.01, 0, 0.07)) * s, at + Vector((0.01, 0, 0.07)) * s, 0.01 * s, sides=4, color="iron", flat=0.4)
            # A curved horn priming flask hung at the bottom of the strap, brass-capped.
            hang = on_front(0.92) + Vector((0, -0.03, -0.02)) * s
            horn = [hang, hang + Vector((0.06, -0.025, -0.07)) * s, hang + Vector((0.14, -0.02, -0.09)) * s, hang + Vector((0.2, -0.01, -0.06)) * s]
            mb.path(horn, [0.032 * s, 0.028 * s, 0.018 * s, 0.006 * s], 6, "parchment")
            mb.tube(hang + Vector((-0.012, 0.004, 0.012)) * s, hang + Vector((0.008, -0.004, -0.012)) * s, 0.036 * s, sides=6, color="brass")
        else:
            at = on_front(0.45) + Vector((0, -0.025, 0)) * s
            mb.box(tuple(at), (0.05 * s, 0.03 * s, 0.08 * s), "brass")

    # ---- a wide, soot-darkened belt over the apron: canvas shot pouches and coils of slow-match.
    with mb.bound_to("hips"):
        mb.loft([_body_ring(ctx, rx, ry, z, sides) for rx, ry, z in ((0.26, 0.235, 0.85), (0.265, 0.24, 0.96))], "leather_dark", smooth=False)
        mb.box((0, -0.27 * g * s, 0.905 * s), (0.09 * s, 0.02 * s, 0.08 * s), "iron")
        for x in ((0.17, -0.19) if hq else (-0.19,)):
            px = x * w * s
            py = -0.235 * g * s * math.sqrt(max(0.05, 1 - (px / (0.26 * w * s)) ** 2)) - 0.035 * s
            mb.box((px, py, 0.82 * s), (0.1 * s, 0.06 * s, 0.11 * s), "canvas_dark")
            mb.box((px, py - 0.005 * s, 0.86 * s), (0.105 * s, 0.065 * s, 0.035 * s), "leather_dark")
        coil_x = 0.265 * w * s + 0.012 * s
        for k in range(2 if hq else 1):
            n = 9 if hq else 6
            loop = [Vector((coil_x + 0.025 * k * s, 0.02 * s + 0.065 * s * math.cos(2 * math.pi * j / (n - 1)), 0.835 * s + 0.065 * s * math.sin(2 * math.pi * j / (n - 1)))) for j in range(n)]
            mb.path(loop, [0.013 * s] * n, 4 if hq else 3, "rope")
        if hq:
            # The match's loose end, still smouldering.
            tail = [Vector((coil_x + 0.04 * s, 0.02 * s, 0.77 * s)), Vector((coil_x + 0.05 * s, -0.02 * s, 0.715 * s)), Vector((coil_x + 0.045 * s, -0.05 * s, 0.675 * s))]
            mb.path(tail, [0.012 * s] * 3, 4, "rope")
            mb.sphere(tail[-1], 0.014 * s, 4, 3, "ember", smooth=False)

    # ---- the press-gang shackle, locked on his right wrist, its chain snapped to a few links.
    elbow_r, wrist_r = (Vector(p) for p in ctx.joints["lower_arm.R"])
    with mb.bound_to("lower_arm.R"):
        mb.tube(elbow_r.lerp(wrist_r, 0.78), elbow_r.lerp(wrist_r, 0.99), 0.1 * s, sides=8 if hq else 5, color="iron")
        axis = (wrist_r - elbow_r).normalized()
        out = Vector((-0.5, -1, 0)).normalized()
        out = (out - axis * out.dot(axis)).normalized()
        side_v = axis.cross(out)
        if hq:
            for k in range(4):
                a = 2 * math.pi * (k + 0.5) / 4
                at = elbow_r.lerp(wrist_r, 0.885) + (out * math.cos(a) + side_v * math.sin(a)) * 0.102 * s
                mb.sphere(at, 0.011 * s, 4, 3, "iron_light", smooth=False)
        link = elbow_r.lerp(wrist_r, 0.95) + out * 0.1 * s
        for k in range(3 if hq else 1):
            nxt = link + Vector((-0.004, -0.004, -0.042)) * s
            mb.tube(link, nxt, 0.013 * s if k < 2 else 0.009 * s, 0.013 * s if k < 2 else 0.003 * s, sides=4, color="iron_light", flat=0.45 if k % 2 else 2.2)
            link = nxt

    # ---- huge, rope-callused hands.
    for side in ("L", "R"):
        wrist, tip = (Vector(p) for p in ctx.joints[f"hand.{side}"])
        with mb.bound_to(f"hand.{side}"):
            mb.sphere(wrist.lerp(tip, 0.5), (0.074 * s, 0.064 * s, 0.09 * s), 8 if hq else 4, 4 if hq else 3, skin, smooth=hq)

    # ---- tar-stained breeches into heavy boots.
    _boot_cuffs(ctx, "leather", flare=1.16)

    # ---- the head: shaved, angular, stubbled, scarred.
    with mb.bound_to("head"):
        # Salt-and-ash stubble over a broad, set jaw.
        mb.sphere(_at(ctx, 0, -0.07, -0.115), (0.17 * s, 0.108 * s, 0.088 * s), 8 if hq else 6, 4 if hq else 3, "rock", smooth=hq)
        if hq:
            # A heavy brow ridge, a mouth pressed into a tight line, and a vertical scar through the left brow.
            mb.box(tuple(_at(ctx, 0, -0.178, 0.078)), (0.25 * s, 0.03 * s, 0.03 * s), skin)
            mb.box(tuple(_at(ctx, 0, -0.183, -0.1)), (0.08 * s, 0.012 * s, 0.009 * s), ink)

            def skull(x, z, lift=0.004):
                y = -0.2 * math.sqrt(max(0.0, 1 - (x / 0.2) ** 2 - (z / 0.22) ** 2))
                return _at(ctx, x, y - lift, z)

            mb.path([skull(0.094, 0.13), _at(ctx, 0.088, -0.208, 0.085), _at(ctx, 0.082, -0.2, 0.03), skull(0.076, -0.04)], [0.004 * s, 0.008 * s, 0.008 * s, 0.003 * s], 3, "skin_light")

            # Black-powder stippling and an old flash burn.
            for x, z in ((-0.12, -0.03), (-0.1, -0.06), (-0.14, -0.06), (0.12, -0.05), (0.04, 0.12), (-0.05, 0.15)):
                mb.sphere(skull(x, z), 0.006 * s, 4, 3, ink, smooth=False)
            mb.sphere(skull(0.125, -0.04, 0.0), (0.03 * s, 0.006 * s, 0.022 * s), 6, 3, "rust", smooth=False)

            # Tally marks: rows starting at his right temple and trailing back and down the side of the skull.
            def skull_row(az0, el0):
                def frame(u, v):
                    az, el = az0 - 0.075 * u, el0 + 0.11 * v
                    lift = 1.03
                    return _at(ctx, 0.2 * math.sin(az) * math.cos(el) * lift, -0.2 * math.cos(az) * math.cos(el) * lift, 0.22 * math.sin(el) * lift)
                return frame

            for az0, el0, groups in ((-1.12, 0.44, 2), (-1.2, 0.2, 2), (-1.55, -0.08, 1), (-1.85, -0.34, 1)):
                _tallies(mb, skull_row(az0, el0), groups, ink, 0.005 * s)
    if hq:
        # And in clustered rows down both forearms.
        for side, sign in (("L", 1), ("R", -1)):
            elbow, wrist = (Vector(p) for p in ctx.joints[f"lower_arm.{side}"])
            axis = (wrist - elbow).normalized()
            n = Vector((sign * 0.7, -1, 0)).normalized()
            n = (n - axis * n.dot(axis)).normalized()
            b = axis.cross(n)
            length = (wrist - elbow).length
            limb0, limb1 = 0.062 * s * g * hero.arm_bulk, 0.05 * s * g * hero.arm_bulk

            def radius(t):
                r = limb0 + (limb1 - limb0) * t
                d = abs(t - 0.3) * length
                bulge = math.sqrt(max(0.0, (0.104 * s) ** 2 - d * d))
                return max(r, bulge) + 0.005 * s

            def arm_row(t0, elbow=elbow, wrist=wrist, n=n, b=b, radius=radius):
                def frame(u, v):
                    t = t0 + 0.13 * v
                    phi = (u - 2.0) * 0.17
                    return elbow.lerp(wrist, t) + (n * math.cos(phi) + b * math.sin(phi)) * radius(t)
                return frame

            with mb.bound_to(f"lower_arm.{side}"):
                for t0 in (0.18, 0.5):
                    _tallies(mb, arm_row(t0), 1, ink, 0.005 * s)



def _on_skull(ctx, x, z, lift=0.004):
    """A point on the front of the skull at head-relative (x, z), lifted off it."""
    y = -0.2 * math.sqrt(max(0.0, 1 - (x / 0.2) ** 2 - (z / 0.22) ** 2))
    return _at(ctx, x, y - lift, z)


def ship_surgeon(ctx):
    """Wren, the gaunt ship's surgeon: tall and nearly skeletal, pallid from months below deck. A shaved skull,
    sharp cheekbones, and fine clinical tally marks on the right temple, down a corded neck and round both
    bony wrists. Black catgut sutures across the lower face and left jaw pull his mouth into a thin, calm smile;
    the left eye is milky and scarred over, the right dark and unblinking. A leather headband with a flip-up
    brass loupe. A collarless linen shirt with the sleeves rolled past the elbows under a cracked, stained
    leather surgeon's apron on a neck strap and brass rings. A tooled apothecary bandolier of scalpels,
    forceps, a cauterising iron, suture spools and corked vials, two glowing green. A weathered belt with a
    stained rag and a roll of bandages, dark fitted breeches, long stained fingers, and a curved silver suture
    needle trailing catgut pinched in his left hand."""
    mb, q, s, g, w, hq = ctx.mb, ctx.q, ctx.s, ctx.g, ctx.w, ctx.hq
    hero = ctx.hero
    skin = hero.skin
    ink = "eye_dark"

    # ---- a long, corded neck.
    with mb.bound_to("neck"):
        mb.tube((0, 0.01 * s, 1.3 * s), (0, 0.01 * s, 1.47 * s), 0.064 * s, 0.058 * s, sides=8 if hq else 5, color=skin)
        if hq:
            for sign in (1, -1):
                mb.tube((sign * 0.05 * s, 0.0, 1.45 * s), (sign * 0.018 * s, -0.062 * s, 1.31 * s), 0.013 * s, 0.01 * s, sides=4, color=skin)

    # ---- the head: shaved, all cheekbone, sutured into a smile.
    with mb.bound_to("head"):
        for sign in (1, -1):
            mb.sphere(_on_skull(ctx, sign * 0.118, -0.03, -0.006), (0.05 * s, 0.022 * s, 0.024 * s), 6 if hq else 4, 3, skin, smooth=False)
        # A leather headband round the brow, a brass loupe flipped up over the right eye.
        with mb.xf(Matrix.Translation(_at(ctx, 0, 0, 0))):
            mb.lathe([(0.172 * s, 0.125 * s), (0.12 * s, 0.185 * s)], q["head_s"], "leather", smooth=False, caps=(False, False))
        hinge = _on_skull(ctx, -0.075, 0.15, 0.03)
        mb.tube(hinge, hinge + Vector((0, -0.05, 0.035)) * s, 0.026 * s, 0.03 * s, sides=8 if hq else 4, color="brass")
        mb.sphere(hinge + Vector((0, -0.052, 0.036)) * s, (0.024 * s, 0.006 * s, 0.024 * s), 6 if hq else 4, 3, "cloud_shade", smooth=False)
        if hq:
            # The mouth, a thin line hauled up at its left corner by black catgut sutures across the jaw.
            mb.path([_on_skull(ctx, x, z) for x, z in ((-0.045, -0.104), (0.0, -0.108), (0.038, -0.098), (0.058, -0.082))], [0.004 * s] * 4, 3, ink)
            wound = [(0.058, -0.082), (0.09, -0.11), (0.125, -0.1), (0.15, -0.13), (0.17, -0.1)]
            mb.path([_on_skull(ctx, x, z, 0.002) for x, z in wound], [0.005 * s] * len(wound), 3, "wood_red")
            for (x0, z0), (x1, z1) in zip(wound, wound[1:]):
                x, z = (x0 + x1) / 2, (z0 + z1) / 2
                dx, dz = z1 - z0, -(x1 - x0)
                n = math.hypot(dx, dz) / 0.018
                mb.tube(_on_skull(ctx, x - dx / n, z - dz / n, 0.006), _on_skull(ctx, x + dx / n, z + dz / n, 0.006), 0.0035 * s, sides=3, color=ink)
            # The old scar over the blind left eye.
            mb.path([_on_skull(ctx, 0.11, 0.08), _at(ctx, 0.095, -0.196, 0.03), _on_skull(ctx, 0.07, -0.04)], [0.003 * s, 0.006 * s, 0.003 * s], 3, "skin_mid")

            # Fine, clinical tally marks in neat rows across the right temple.
            def temple_row(az0, el0):
                def frame(u, v):
                    az, el = az0 - 0.06 * u, el0 + 0.09 * v
                    return _at(ctx, 0.206 * math.sin(az) * math.cos(el), -0.206 * math.cos(az) * math.cos(el), 0.226 * math.sin(el))
                return frame

            for az0, el0, groups in ((-1.1, 0.36, 2), (-1.2, 0.16, 2), (-1.55, -0.06, 1)):
                _tallies(mb, temple_row(az0, el0), groups, ink, 0.0035 * s, gap=5.4)
    if hq:
        # ...down the right side of the neck...
        r = 0.066 * s
        with mb.bound_to("neck"):
            for z0 in (1.4, 1.34):
                _tallies(mb, lambda u, v, z0=z0: Vector((-r * math.sin(0.9 + 0.16 * u), 0.01 * s - r * math.cos(0.9 + 0.16 * u), (z0 + 0.035 * v) * s)), 1, ink, 0.0035 * s)

    # ---- sleeves rolled past bony elbows; tally marks round both wrists; long, stained fingers.
    for side, sign in (("L", 1), ("R", -1)):
        elbow, wrist = (Vector(p) for p in ctx.joints[f"lower_arm.{side}"])
        r0 = 0.062 * s * g * hero.arm_bulk
        with mb.bound_to(f"lower_arm.{side}"):
            mb.tube(elbow.lerp(wrist, 0.04), elbow.lerp(wrist, 0.22), r0 * 1.45, r0 * 1.35, sides=8 if hq else 4, color=hero.top)
            if hq:
                mb.sphere(elbow + Vector((0, 0.03, 0)) * s, 0.04 * s, 5, 3, skin, smooth=False)  # The bony point of the elbow.
                axis = (wrist - elbow).normalized()
                n = Vector((sign * 0.6, -1, 0)).normalized()
                n = (n - axis * n.dot(axis)).normalized()
                b = axis.cross(n)
                rw = 0.05 * s * g * hero.arm_bulk + 0.004 * s

                def wrist_row(u, v, elbow=elbow, wrist=wrist, n=n, b=b, rw=rw):
                    phi = (u - 2.0) * 0.26
                    return elbow.lerp(wrist, 0.74 + 0.12 * v) + (n * math.cos(phi) + b * math.sin(phi)) * rw * 1.04
                _tallies(mb, wrist_row, 1, ink, 0.0035 * s)
        if hq:
            hand_w, hand_t = (Vector(p) for p in ctx.joints[f"hand.{side}"])
            along = (hand_t - hand_w).normalized()
            with mb.bound_to(f"hand.{side}"):
                for k in range(4):
                    root = hand_w.lerp(hand_t, 0.7) + Vector((-sign * 0.012, -0.03 + 0.02 * k, 0)) * s
                    knuckle = root + along * 0.06 * s + Vector((-sign * 0.012, 0, 0)) * s
                    tip = knuckle + along * 0.035 * s + Vector((-sign * 0.016, 0, 0)) * s
                    mb.tube(root, knuckle, 0.011 * s, 0.009 * s, sides=3, color=skin)
                    mb.tube(knuckle, tip, 0.009 * s, 0.007 * s, sides=3, color="rust" if k % 2 else "wood_red")
    if hq:
        # The curved silver suture needle pinched in his left hand, trailing black catgut.
        hand_w, hand_t = (Vector(p) for p in ctx.joints["hand.L"])
        pinch = hand_w.lerp(hand_t, 1.1) + Vector((-0.02, -0.05, 0)) * s
        with mb.bound_to("hand.L"):
            arc = [pinch + Vector((0.025 * math.cos(a), -0.025 * math.sin(a), 0.01 * math.sin(a))) * s for a in (0.0, 0.8, 1.6, 2.4, 3.1)]
            mb.path(arc, [0.003 * s, 0.003 * s, 0.003 * s, 0.003 * s, 0.001 * s], 3, "silver")
            mb.path([arc[0], arc[0] + Vector((0.01, -0.01, -0.06)) * s, arc[0] + Vector((-0.005, -0.02, -0.13)) * s], [0.002 * s] * 3, 3, ink)

    # ---- the surgeon's apron: cracked dark leather, stained, on a neck strap and brass rings.
    bib = [(0.25, 0.18, 1.08, 44), (0.3, 0.19, 1.22, 34), (0.3, 0.185, 1.3, 26)]
    waist = [(0.22, 0.17, 0.93, 48), (0.25, 0.18, 1.09, 44)]
    skirt = [(0.22, 0.17, 0.94, 50), (0.235, 0.19, 0.75, 50), (0.245, 0.205, 0.5, 46)]
    with mb.bound_to("chest"):
        mb.loft(_front_shell(ctx, bib, wall=0.016), "leather_dark", smooth=False)
        corner_x = 0.3 * w * s * math.sin(math.radians(26))
        for sign in (1, -1):
            corner = Vector((sign * corner_x, _front_y(ctx, bib, corner_x, 1.3 * s) - 0.006 * s, 1.31 * s))
            ring = [corner + Vector((0.022 * math.cos(a), -0.004, 0.022 * math.sin(a))) * s for a in [2 * math.pi * k / 6 for k in range(7)]]
            if hq:
                mb.path(ring, [0.006 * s] * 7, 3, "brass")
            else:
                mb.box(tuple(corner), (0.04 * s, 0.012 * s, 0.04 * s), "brass")
        strap = [Vector((corner_x, 0, 1.33 * s)), Vector((0.075, -0.04, 1.44)) * s, Vector((0.07, 0.07, 1.45)) * s, Vector((0, 0.09, 1.44)) * s,
                 Vector((-0.07, 0.07, 1.45)) * s, Vector((-0.075, -0.04, 1.44)) * s, Vector((-corner_x, 0, 1.33 * s))]
        for p_ in (strap[0], strap[-1]):
            p_.y = _front_y(ctx, bib, abs(p_.x), 1.3 * s) - 0.008 * s
        mb.path(strap, [0.014 * s] * len(strap), 4 if hq else 3, "leather_dark")
        if hq:
            for x, z, rx, rz, c in ((0.08, 1.15, 0.05, 0.035, "velvet"), (-0.1, 1.24, 0.03, 0.02, "toxic_dark"), (0.11, 1.26, 0.02, 0.025, "velvet")):
                mb.sphere((x * s, _front_y(ctx, bib, x * s, z * s), z * s), (rx * s, 0.005 * s, rz * s), 6, 3, c, smooth=False)
    with mb.bound_to("spine"):
        mb.loft(_front_shell(ctx, waist, wall=0.016), "leather_dark", smooth=False)
    with mb.bound_to("hips"):
        mb.loft(_front_shell(ctx, skirt, wall=0.016), "leather_dark", smooth=False)
        if hq:
            for x, z, rx, rz, c in ((-0.06, 0.66, 0.06, 0.04, "velvet"), (0.09, 0.58, 0.035, 0.05, "abyss"), (0.02, 0.78, 0.03, 0.02, "toxic_dark")):
                mb.sphere((x * s, _front_y(ctx, skirt, x * s, z * s), z * s), (rx * s, 0.005 * s, rz * s), 6, 3, c, smooth=False)
        # The belt sits over the apron: a stained rag tucked on the right, a roll of bandages on the left.
        belt_r = 0.205 * w * s * 1.03
        mb.plate([(-belt_r * 0.82, -belt_r * 0.6, 0.88 * s), (-belt_r * 0.55, -belt_r * 0.86, 0.88 * s), (-belt_r * 0.6, -belt_r * 0.88, 0.66 * s), (-belt_r * 0.9, -belt_r * 0.6, 0.7 * s)], 0.012 * s, "canvas_dark")
        if hq:
            mb.sphere((-belt_r * 0.72, -belt_r * 0.8, 0.74 * s), (0.04 * s, 0.006 * s, 0.03 * s), 5, 3, "velvet", smooth=False)
        roll = Vector((belt_r * 0.9, -belt_r * 0.35, 0.85 * s))
        mb.tube(roll + Vector((0, -0.045, 0)) * s, roll + Vector((0, 0.045, 0)) * s, 0.038 * s, sides=8 if hq else 4, color="cloth_white")
        if hq:
            mb.tube(roll + Vector((0, -0.046, 0)) * s, roll + Vector((0, -0.046, -0.09)) * s, 0.02 * s, sides=4, color="cloth_white", flat=0.3)

    # ---- the tooled apothecary bandolier, from his right shoulder down to his left hip.
    torso_front = waist[:1] + bib

    def on_front(u):
        x = (-0.17 + 0.42 * u) * w * s
        z = (1.3 - 0.33 * u) * s
        return Vector((x, _front_y(ctx, torso_front, x, z) - 0.012 * s, z))

    with mb.bound_to("chest"):
        over = [Vector((-0.2 * w, 0.02 * g, 1.41)) * s, Vector((-0.19 * w, -0.12 * g, 1.37)) * s]
        mb.path(over + [on_front(k / 6) for k in range(7)], [0.024 * s] * 9, 4 if hq else 3, "leather")
        if hq:
            mb.path([over[0], Vector((-0.17 * w, 0.15 * g, 1.33)) * s, Vector((0.0, 0.2 * g, 1.18)) * s, Vector((0.2 * w, 0.17 * g, 1.0)) * s], [0.024 * s] * 4, 4, "leather")
            out = Vector((0, -1, 0))
            # Polished scalpels, blades up.
            for k, u in enumerate((0.1, 0.16)):
                at = on_front(u) + out * 0.016 * s
                mb.tube(at + Vector((0, 0, -0.05)) * s, at + Vector((0, 0, 0.03)) * s, 0.006 * s, sides=3, color="steel")
                mb.tube(at + Vector((0, 0, 0.03)) * s, at + Vector((0.004, 0, 0.065)) * s, 0.008 * s, 0.001 * s, sides=3, color="silver", flat=0.3)
            # Bullet forceps, jaws down.
            at = on_front(0.25) + out * 0.018 * s
            for sx in (1, -1):
                mb.tube(at + Vector((sx * 0.012, 0, 0.05)) * s, at + Vector((sx * 0.002, 0, -0.06)) * s, 0.004 * s, 0.003 * s, sides=3, color="silver")
            # A cauterising iron: a wooden handle and a blackened iron head.
            at = on_front(0.36) + out * 0.02 * s
            mb.tube(at + Vector((0, 0, -0.07)) * s, at + Vector((0, 0, 0.0)) * s, 0.01 * s, sides=4, color="wood_mid")
            mb.tube(at, at + Vector((0, 0, 0.06)) * s, 0.004 * s, sides=3, color="iron")
            mb.sphere(at + Vector((0, 0, 0.068)) * s, (0.014 * s, 0.006 * s, 0.012 * s), 4, 3, "iron", smooth=False)
            # Corked vials: two of glowing green sedative, laudanum, murky antiseptic.
            for u, c in ((0.48, "liftstone"), (0.56, "amber"), (0.64, "liftstone"), (0.72, "toxic")):
                at = on_front(u) + out * 0.022 * s
                mb.tube(at + Vector((0, 0, -0.035)) * s, at + Vector((0, 0, 0.025)) * s, 0.013 * s, sides=5, color=c)
                mb.tube(at + Vector((0, 0, 0.025)) * s, at + Vector((0, 0, 0.04)) * s, 0.01 * s, sides=4, color="wood_light")
            # Wooden spools of waxed suture thread.
            for u in (0.84, 0.93):
                at = on_front(u) + out * 0.022 * s
                mb.tube(at + Vector((-0.02, 0, 0)) * s, at + Vector((0.02, 0, 0)) * s, 0.016 * s, sides=5, color="wood_light")
                mb.tube(at + Vector((-0.014, 0, 0)) * s, at + Vector((0.014, 0, 0)) * s, 0.02 * s, sides=5, color="parchment")
        else:
            at = on_front(0.6) + Vector((0, -0.02, 0)) * s
            mb.box(tuple(at), (0.03 * s, 0.025 * s, 0.06 * s), "liftstone")

    # ---- dark fitted breeches tucked into plain boots.
    _boot_cuffs(ctx, "leather_dark", flare=1.1)



# ---- Vane, across the three acts ----------------------------------------------------------------

def _open_shell(ctx, rows, opening, wall=0.018):
    """Loft rings for a garment wrapped round the body but open down the front, such as a vest or jerkin.
    Each row is (rx, ry, z); opening is the half-angle of the front gap in degrees."""
    s, w, g = ctx.s, ctx.w, ctx.g
    points = 11 if ctx.hq else 8
    pad = 0.0 if ctx.hq else 0.014  # LQ bodies are coarse polygons: stand clear of their corners.
    out = []
    for rx, ry, z in rows:
        rx, ry = rx + pad, ry + pad

        def arc(rx_, ry_, backward):
            angles = [math.radians(270 + opening + (360 - 2 * opening) * k / (points - 1)) for k in range(points)]
            pts = [(rx_ * w * s * math.cos(a), ry_ * g * s * math.sin(a), z * s) for a in angles]
            return pts[::-1] if backward else pts
        out.append(arc(rx, ry, False) + arc(rx - wall, ry - wall, True))
    return out


def _surface_y(ctx, rows, x, z):
    """y of the front of a body loft at (x, z), both scaled. rows are (rx, ry, z) as given to _body_ring."""
    s, w, g = ctx.s, ctx.w, ctx.g
    rows = sorted(rows, key=lambda r: r[2])
    rx, ry = rows[0][0], rows[0][1]
    for (rx0, ry0, z0), (rx1, ry1, z1) in zip(rows, rows[1:]):
        if z0 * s <= z <= z1 * s:
            t = (z - z0 * s) / ((z1 - z0) * s)
            rx, ry = rx0 + (rx1 - rx0) * t, ry0 + (ry1 - ry0) * t
    if z > rows[-1][2] * s:
        rx, ry = rows[-1][0], rows[-1][1]
    return -ry * g * s * math.sqrt(max(0.05, 1 - (x / (rx * w * s)) ** 2))


_BASE_CHEST = [(0.235, 0.16, 1.08), (0.3, 0.17, 1.28), (0.14, 0.1, 1.37)]
_COAT_FRONT = [(0.22, 0.165, 0.9), (0.25, 0.175, 1.06), (0.315, 0.185, 1.28), (0.15, 0.11, 1.38)]


def _v_neck(ctx, rows, inner, outer=None, depth=1.18):
    """An open collar: a V of bare throat, optionally framed by a wider V of shirt."""
    mb, s, w = ctx.mb, ctx.s, ctx.w
    with mb.bound_to("chest"):
        for color, half, bottom, lift in ((outer, 0.1, depth - 0.03, 0.004), (inner, 0.065, depth, 0.008)):
            if color is None:
                continue
            top = 1.35
            pts = [(-half * w * s, top * s), (half * w * s, top * s), (0.0, bottom * s)]
            mb.plate([(x, _surface_y(ctx, rows, x, z) - lift * s, z) for x, z in pts], 0.004 * s, color)


def _vane_head(ctx, act):
    """Vane's face and hair, constant across the acts (from the newVane reference): golden-brown hair swept up
    and back off the brow with real volume and wavy locks over the ears to the jaw; hazel-green eyes under dark
    brows; a small scar through the right brow; a crooked half-smile pulled up on the left; and the red bandana
    across the forehead, knotted on the right with its tails streaming. From Act 2 the hair is longer and
    half-gathered at the nape with a braided leather cord, and the bandana has a gold-thread hem. In Act 3 the
    hat covers the crown."""
    mb, q, s, hq = ctx.mb, ctx.q, ctx.s, ctx.hq
    hair, red = ctx.hero.hair, "gem_red"
    hair_cap(ctx)
    with mb.bound_to("head"):
        mb.sphere(_at(ctx, 0, 0.1, -0.05), (0.19 * s, 0.125 * s, 0.17 * s), 8 if hq else 5, 4 if hq else 3, hair, smooth=hq)
        if act < 3:
            # Volume swept up off the forehead and back over the crown.
            xs = (-0.13, -0.065, 0.0, 0.065, 0.13) if hq else (-0.09, 0.0, 0.09)
            for k, x in enumerate(xs):
                lift = 0.02 * math.cos(k * 1.7)
                pts = [_at(ctx, x, -0.15, 0.165), _at(ctx, x * 1.05, -0.1, 0.255 + lift * 0.5), _at(ctx, x * 1.12, 0.04, 0.275 + lift * 0.5), _at(ctx, x * 1.2, 0.17, 0.2)]
                radii = [0.058 * s, 0.082 * s, 0.072 * s, 0.03 * s]
                if not hq:
                    pts, radii = pts[:1] + pts[2:], [0.065 * s, 0.085 * s, 0.03 * s]
                mb.path(pts, radii, 6 if hq else 4, hair, smooth=hq)
            if hq:
                # One wave breaks forward over the bandana, on the left.
                mb.path([_at(ctx, 0.04, -0.165, 0.2), _at(ctx, 0.08, -0.215, 0.14), _at(ctx, 0.065, -0.215, 0.09)], [0.03 * s, 0.022 * s, 0.006 * s], 4, hair)
        # Wavy locks over the ears to the jaw, flicking out at the ends. Longer once he's a captain.
        drop = 0.06 if act >= 2 else 0.0
        for sign in (1, -1):
            pts = [_at(ctx, sign * 0.165, -0.06, 0.13), _at(ctx, sign * 0.215, -0.01, 0.02), _at(ctx, sign * 0.205, 0.0, -0.1 - drop), _at(ctx, sign * 0.24, -0.035, -0.17 - drop)]
            radii = [0.05 * s, 0.055 * s, 0.045 * s, 0.012 * s]
            if not hq:
                pts, radii = [pts[0], pts[2], pts[3]], [radii[0], radii[2], radii[3]]
            mb.path(pts, radii, 5 if hq else 3, hair, smooth=hq)
        if act >= 2:
            # Half-gathered at the nape, tied with a braided leather cord.
            tail = [_at(ctx, 0, 0.19, -0.1), _at(ctx, 0, 0.24, -0.2), _at(ctx, 0.01, 0.225, -0.33)]
            mb.path(tail, [0.05 * s, 0.042 * s, 0.012 * s], 5 if hq else 3, hair)
            mb.tube(tail[0].lerp(tail[1], 0.25), tail[0].lerp(tail[1], 0.5), 0.05 * s, 0.047 * s, sides=6 if hq else 4, color="leather_dark")

        # The bandana: a band round the brow, above the eyebrows and hugging the hair at the back.
        n = 16 if hq else 6
        rings = []
        for z, pad in ((0.108, 0.012), (0.172, 0.01)):
            ring = []
            for j in range(n):
                a = 2 * math.pi * (j + 0.5) / n
                ca, sa = math.cos(a), math.sin(a)
                skull = 0.2 * math.sqrt(max(0.0, 1 - (z / 0.22) ** 2))
                cap = 0.04 * sa + math.sqrt(max(0.0, 0.208 ** 2 - (z - 0.06) ** 2 - (0.04 * ca) ** 2))
                r = max(skull, cap) + pad
                ring.append(_at(ctx, r * ca, r * sa, z))
            rings.append(ring)
        mb.loft(rings, red, smooth=False, caps=(False, False))
        if act >= 2 and hq:
            for ring in rings:
                mb.path(ring + ring[:1], [0.004 * s] * (n + 1), 3, "gold")
        # The knot on the right, and two tails streaming back.
        knot = _at(ctx, -0.19, 0.08, 0.14)
        mb.sphere(knot, 0.032 * s, 6 if hq else 4, 3, red, smooth=False)
        tails = [[knot, knot + Vector((-0.09, 0.12, 0.03)) * s, knot + Vector((-0.17, 0.2, -0.02)) * s, knot + Vector((-0.11, 0.17, -0.05)) * s],
                 [knot, knot + Vector((-0.06, 0.1, -0.08)) * s, knot + Vector((-0.12, 0.17, -0.17)) * s, knot + Vector((-0.08, 0.13, -0.15)) * s]]
        for tail in (tails if hq else tails[:1]):
            if act == 1 and hq:
                # Frayed by sun and salt: a ragged end.
                a, b = tail[2], tail[3]
                tail = tail[:2] + [a, a.lerp(b, 0.35) + Vector((0, 0, -0.02)) * s, a.lerp(b, 0.6), a.lerp(b, 0.8) + Vector((0, 0, -0.02)) * s, b]
            mb.plate(tail, 0.012 * s, red)

        if hq:
            # A small scar through the right brow, and the crooked half-smile pulled up on the left.
            mb.path([_on_skull(ctx, -0.088, 0.15), _at(ctx, -0.083, -0.207, 0.09), _on_skull(ctx, -0.078, 0.055)], [0.003 * s, 0.005 * s, 0.003 * s], 3, "skin_light")
            mb.path([_on_skull(ctx, x, z) for x, z in ((-0.05, -0.1), (0.0, -0.104), (0.04, -0.097), (0.068, -0.077))], [0.004 * s, 0.0045 * s, 0.0045 * s, 0.003 * s], 3, "eye_dark")


def vane_deckhand(ctx):
    """Act 1, the cast-off deckhand, thrown off the Sovereign Gale with nothing. A torn off-white linen shirt,
    ripped open at the collar, sleeves rolled unevenly past the elbows, under a scavenged sleeveless leather
    jerkin with a ghost of darker leather where the First Mate insignia was ripped off the left breast.
    Hemp rope knotted round the waist with a cracked belt, a bone-handled rigging knife and a belaying pin.
    Forearms and knuckles wrapped in tarred cord and linen bandage. Baggy charcoal breeches, the left knee
    torn and stitched shut with black catgut, over worn brown ankle boots bound with twine."""
    mb, q, s, g, w, hq = ctx.mb, ctx.q, ctx.s, ctx.g, ctx.w, ctx.hq
    hero = ctx.hero
    _vane_head(ctx, 1)

    # ---- the torn shirt's open collar, and the scavenged jerkin.
    _v_neck(ctx, _BASE_CHEST, hero.skin, depth=1.2)
    jerkin_chest = [(0.252, 0.18, 1.07), (0.315, 0.188, 1.28), (0.165, 0.118, 1.37)]
    with mb.bound_to("chest"):
        mb.loft(_open_shell(ctx, jerkin_chest, 28), "leather", smooth=False)
        if hq:
            for sign in (1, -1):
                y0 = _surface_y(ctx, _BASE_CHEST, sign * 0.065 * w * s, 1.35 * s)
                mb.plate([(sign * 0.065 * w * s, y0 - 0.01 * s, 1.35 * s), (sign * 0.13 * w * s, y0 - 0.025 * s, 1.34 * s), (sign * 0.07 * w * s, _surface_y(ctx, _BASE_CHEST, sign * 0.07 * w * s, 1.27 * s) - 0.012 * s, 1.27 * s)], 0.006 * s, hero.top)
        # Where the First Mate insignia was ripped away: darker, unfaded leather ringed with stitch holes.
        x, z = 0.18 * w * s, 1.22 * s
        y = _surface_y(ctx, jerkin_chest, x, z)
        mb.sphere((x, y, z), (0.042 * s, 0.006 * s, 0.036 * s), 6 if hq else 4, 3, "leather_dark", smooth=False)
        if hq:
            for k in range(6):
                a = 2 * math.pi * k / 6
                hx, hz = x + 0.05 * s * math.cos(a), z + 0.044 * s * math.sin(a)
                mb.box((hx, _surface_y(ctx, jerkin_chest, hx, hz) - 0.002 * s, hz), (0.007 * s, 0.006 * s, 0.007 * s), "eye_dark")
    with mb.bound_to("spine"):
        mb.loft(_open_shell(ctx, [(0.212, 0.158, 0.93), (0.252, 0.18, 1.08)], 22), "leather", smooth=False)

    # ---- sleeves rolled unevenly past the elbows; forearms and knuckles wrapped.
    for side in ("L", "R"):
        elbow, wrist = (Vector(p) for p in ctx.joints[f"lower_arm.{side}"])
        r0, r1 = 0.062 * s * g * hero.arm_bulk, 0.05 * s * g * hero.arm_bulk
        radius = lambda t, r0=r0, r1=r1: r0 + (r1 - r0) * t  # noqa: E731
        roll = (0.1, 0.27) if side == "L" else (0.0, 0.14)
        with mb.bound_to(f"lower_arm.{side}"):
            mb.tube(elbow.lerp(wrist, roll[0]), elbow.lerp(wrist, roll[1]), radius(roll[0]) * 1.42, radius(roll[1]) * 1.36, sides=8 if hq else 4, color=hero.top)
            if side == "L":
                mb.tube(elbow.lerp(wrist, 0.55), elbow.lerp(wrist, 0.97), radius(0.55) * 1.12, radius(0.97) * 1.14, sides=8 if hq else 4, color="canvas")
            elif hq:
                axis = (wrist - elbow).normalized()
                n = Vector((0, -1, 0))
                n = (n - axis * n.dot(axis)).normalized()
                b = axis.cross(n)
                spiral = [elbow.lerp(wrist, 0.5 + 0.47 * k / 13) + (n * math.cos(k * 1.5) + b * math.sin(k * 1.5)) * radius(0.5 + 0.47 * k / 13) * 1.08 for k in range(14)]
                mb.path(spiral, [0.008 * s] * 14, 3, "leather_dark")
            else:
                mb.tube(elbow.lerp(wrist, 0.6), elbow.lerp(wrist, 0.95), radius(0.6) * 1.1, radius(0.95) * 1.1, sides=4, color="leather_dark")
        hand_w, hand_t = (Vector(p) for p in ctx.joints[f"hand.{side}"])
        with mb.bound_to(f"hand.{side}"):
            mb.tube(hand_w.lerp(hand_t, 0.38), hand_w.lerp(hand_t, 0.68), 0.062 * s, sides=6 if hq else 4, color="canvas")

    # ---- rope and a cracked belt at the waist, a rigging knife and a belaying pin.
    with mb.bound_to("hips"):
        n = 12 if hq else 6
        for z in ((0.835, 0.812) if hq else (0.825,)):
            loop = [Vector((0.218 * w * s * math.cos(a), 0.16 * g * s * math.sin(a), z * s)) for a in (2 * math.pi * k / n for k in range(n + 1))]
            mb.path(loop, [0.012 * s] * (n + 1), 4 if hq else 3, "rope")
        if hq:
            knot = Vector((0.1 * w * s, -0.16 * g * s * math.sqrt(1 - (0.1 / 0.218) ** 2) - 0.008 * s, 0.82 * s))
            mb.sphere(knot, 0.02 * s, 5, 3, "rope", smooth=False)
            for dx in (-0.012, 0.014):
                mb.path([knot, knot + Vector((dx, -0.008, -0.07)) * s, knot + Vector((dx * 1.6, -0.004, -0.12)) * s], [0.01 * s, 0.009 * s, 0.006 * s], 3, "rope")
            belt_r = 0.205 * w * s * 1.03
            for x in (0.06, -0.11):
                mb.box((x * s, -math.sqrt(belt_r ** 2 - (x * s) ** 2) - 0.002 * s, 0.905 * s), (0.005 * s, 0.006 * s, 0.05 * s), "leather_dark")
        # A bone-handled rigging knife on the right hip, a belaying pin shoved through the back of the belt.
        knife = Vector((-0.205 * w * s, -0.075 * s, 0.9 * s))
        mb.tube(knife, knife + Vector((-0.015, -0.015, -0.17)) * s, 0.017 * s, 0.012 * s, sides=4, color="leather")
        mb.tube(knife, knife + Vector((0.005, 0.0, 0.09)) * s, 0.013 * s, sides=4, color="enamel")
        pin = Vector((0.09 * w * s, 0.215 * s, 1.0 * s))
        mb.tube(pin, pin + Vector((0.02, -0.04, -0.28)) * s, 0.02 * s, 0.015 * s, sides=5 if hq else 3, color="wood_mid")
        mb.sphere(pin + Vector((0, 0, 0.02)) * s, 0.028 * s, 5 if hq else 4, 3, "wood_mid", smooth=False)

    # ---- baggy breeches, gathered over brown ankle boots bound with twine; the stitched tear on the left knee.
    for side, sign in (("L", 1), ("R", -1)):
        knee, ankle = (Vector(p) for p in ctx.joints[f"shin.{side}"][:2])
        r0, r1 = 0.085 * s * g * hero.leg_bulk, 0.07 * s * g * hero.leg_bulk
        radius = lambda t, r0=r0, r1=r1: r0 + (r1 - r0) * t  # noqa: E731
        with mb.bound_to(f"shin.{side}"):
            # One continuous tube: two tubes meeting at a shared ring weld into a doubled cap on export.
            mb.path([knee.lerp(ankle, -0.04), knee.lerp(ankle, 0.5), knee.lerp(ankle, 0.58)], [radius(0.0) * 1.2, radius(0.5) * 1.18, radius(0.58) * 1.02], 8 if hq else 4, hero.legs)
            for t in ((0.66, 0.8) if hq else (0.72,)):
                mb.tube(knee.lerp(ankle, t - 0.015), knee.lerp(ankle, t + 0.015), radius(t) * 1.07, sides=6 if hq else 4, color="rope")
        if hq and side == "L":
            hip, knee_ = (Vector(p) for p in ctx.joints["thigh.L"][:2])
            rt = (0.1 - 0.025 * 0.88) * s * g * hero.leg_bulk + 0.004 * s
            at = hip.lerp(knee_, 0.88) + Vector((0, -rt, 0))
            with mb.bound_to("thigh.L"):
                tear = [at + Vector((dx, 0, dz)) * s for dx, dz in ((-0.04, 0.02), (-0.015, -0.01), (0.005, 0.02), (0.025, -0.012), (0.045, 0.01))]
                mb.path(tear, [0.006 * s] * 5, 3, "rock")
                for p0, p1 in zip(tear, tear[1:]):
                    mid = p0.lerp(p1, 0.5)
                    mb.tube(mid + Vector((0, -0.002, 0.018)) * s, mid + Vector((0, -0.002, -0.018)) * s, 0.003 * s, sides=3, color="eye_dark")


def _pistol(mb, s, at, down, out, barrel="iron", grip="wood_dark", mount="brass", hq=True):
    """A flintlock pistol holstered against the body: barrel along down, grip kicked out sideways."""
    side = down.cross(out).normalized()
    mb.tube(at, at + down * 0.15 * s, 0.012 * s, 0.011 * s, sides=5 if hq else 3, color=barrel)
    mb.tube(at, at - down * 0.02 * s + side * 0.07 * s, 0.019 * s, 0.022 * s, sides=5 if hq else 3, color=grip)
    if hq:
        mb.sphere(at - down * 0.025 * s + side * 0.075 * s, 0.022 * s, 5, 3, mount, smooth=False)
        mb.tube(at + down * 0.13 * s, at + down * 0.155 * s, 0.015 * s, sides=5, color=mount)


def _scabbard(ctx, color, fitting):
    """An empty scabbard at the left hip: the sword is in his hand."""
    mb, s, w, hq = ctx.mb, ctx.s, ctx.w, ctx.hq
    top, bottom = Vector((0.235 * w * s, -0.04 * s, 0.9 * s)), Vector((0.31 * w * s, 0.17 * s, 0.34 * s))
    with mb.bound_to("hips"):
        mb.tube(top, bottom, 0.024 * s, 0.018 * s, sides=6 if hq else 3, color=color)
        mb.tube(top, top.lerp(bottom, 0.08), 0.028 * s, sides=6 if hq else 3, color=fitting)
        if hq:
            mb.tube(top.lerp(bottom, 0.9), bottom, 0.022 * s, 0.012 * s, sides=6, color=fitting)


def vane_captain(ctx):
    """Act 2, the rising captain: earned authority, battle-worn. A knee-length storm-navy captain's coat with
    dark oiled-leather lapels and upturned cuffs, structured shoulders and double rows of tarnished silver
    buttons, over a charcoal-and-silver brocade waistcoat and an open-collared cream shirt. A double-strapped
    tooled leather baldric carrying two brass-mounted flintlocks and a navigator's pocket watch on a chain.
    Fingerless duelling gloves, dark slate breeches into cuffed knee-high black sea-boots with brass buckles,
    and an empty tooled scabbard at the left hip."""
    mb, q, s, g, w, hq = ctx.mb, ctx.q, ctx.s, ctx.g, ctx.w, ctx.hq
    hero = ctx.hero
    _vane_head(ctx, 2)
    long_coat(ctx, "navy", hero.top, tail_len=0.46)
    _v_neck(ctx, _COAT_FRONT, hero.skin, "canvas", depth=1.2)
    with mb.bound_to("chest"):
        # Oiled-leather lapels and structured shoulders.
        for sign in (1, -1):
            outline = [(0.07, 1.37), (0.17, 1.33), (0.15, 1.15), (0.1, 1.1)]
            mb.plate([(sign * x * w * s, _surface_y(ctx, _COAT_FRONT, x * w * s, z * s) - 0.012 * s, z * s) for x, z in outline], 0.008 * s, "leather_dark")
            mb.box((sign * 0.27 * w * s, 0.0, 1.325 * s), (0.13 * s, 0.15 * s, 0.035 * s), "navy", top_scale=0.8)
        # Double rows of tarnished silver buttons, and the waistcoat's own down the middle.
        for z in ((1.24, 1.16, 1.08) if hq else (1.2,)):
            for sign in (1, -1):
                x = sign * 0.2 * w * s
                mb.sphere((x, _surface_y(ctx, _COAT_FRONT, x, z * s) - 0.006 * s, z * s), 0.015 * s, 5 if hq else 4, 3, "silver", smooth=False)
        if hq:
            for z in (1.15, 1.08, 1.01):
                mb.sphere((0, _surface_y(ctx, _COAT_FRONT, 0, z * s) - 0.004 * s, z * s), 0.009 * s, 4, 3, "silver", smooth=False)

    # ---- upturned leather cuffs.
    for side in ("L", "R"):
        elbow, wrist = (Vector(p) for p in ctx.joints[f"lower_arm.{side}"])
        r1 = 0.05 * s * g * hero.arm_bulk
        with mb.bound_to(f"lower_arm.{side}"):
            mb.tube(elbow.lerp(wrist, 0.7), elbow.lerp(wrist, 0.97), r1 * 1.35, r1 * 1.6, sides=8 if hq else 4, color="leather_dark")

    # ---- the baldric, left shoulder to right hip: two flintlocks and the pocket watch.
    def on_front(u, dz=0.0):
        x = (0.2 - 0.46 * u) * w * s
        z = (1.32 - 0.38 * u + dz) * s
        return Vector((x, _surface_y(ctx, _COAT_FRONT, x, z) - 0.014 * s, z))

    with mb.bound_to("chest"):
        over = Vector((0.21 * w, 0.02, 1.42)) * s
        for dz in ((0.0, -0.05) if hq else (0.0,)):
            mb.path([over + Vector((0, 0, dz)) * s] + [on_front(k / 6, dz) for k in range(7)], [0.02 * s] * 8, 4 if hq else 3, "leather")
        if hq:
            mb.path([over, Vector((0.17 * w, 0.17 * g, 1.34)) * s, Vector((0.0, 0.2 * g, 1.18)) * s, Vector((-0.2 * w, 0.17 * g, 0.98)) * s], [0.02 * s] * 4, 4, "leather")
            for k in range(6):
                mb.sphere(on_front(0.1 + 0.15 * k, -0.025) + Vector((0, -0.008, 0)) * s, 0.008 * s, 4, 3, "brass", smooth=False)
        for u in ((0.3, 0.58) if hq else (0.45,)):
            at = on_front(u, -0.025) + Vector((0, -0.025, 0)) * s
            _pistol(mb, s, at, Vector((-0.3, -0.05, -1)).normalized(), Vector((0, -1, 0)), hq=hq)
        if hq:
            watch = on_front(0.86, -0.06) + Vector((0, -0.02, -0.06)) * s
            mb.path([on_front(0.8, -0.03), watch + Vector((0, 0, 0.035)) * s], [0.003 * s] * 2, 3, "gold_dark")
            with mb.xf(Matrix.Translation(watch) @ Matrix.Rotation(math.pi / 2, 4, "X")):
                mb.lathe([(0.034 * s, -0.01 * s), (0.034 * s, 0.01 * s)], 8, "brass", smooth=False)
            mb.box(tuple(watch + Vector((0, -0.011, 0)) * s), (0.045 * s, 0.003 * s, 0.045 * s), "parchment")

    _scabbard(ctx, "leather_dark", "brass")
    _boot_cuffs(ctx, "leather_dark", flare=1.2)
    if hq:
        for side, sign in (("L", 1), ("R", -1)):
            knee, ankle = (Vector(p) for p in ctx.joints[f"shin.{side}"][:2])
            r = 0.085 * s * g * hero.leg_bulk * 1.2
            with mb.bound_to(f"shin.{side}"):
                at = knee.lerp(ankle, 0.13)
                mb.box(tuple(at + Vector((sign * r * 0.75, -r * 0.7, 0))), (0.03 * s, 0.03 * s, 0.026 * s), "brass")


def _vane_hat(ctx):
    """A grand, wide-brimmed black tricorn-cavalier hat, pinned up on the left with a silver-and-gold fleet crest
    and a sweeping storm-petrel plume, edged in heavy braided gold."""
    mb, q, s, hq = ctx.mb, ctx.q, ctx.s, ctx.hq
    z0 = 0.165
    n = 18 if hq else 8
    with mb.bound_to("head"):
        rings = []
        for dz in (0.0, 0.02):
            ring = []
            for j in range(n):
                a = 2 * math.pi * (j + 0.5) / n
                r = 0.36 * (1.0 + 0.2 * math.cos(3 * (a + math.pi / 2)))
                up = 0.11 * max(0.0, math.cos(a)) ** 2
                ring.append(_at(ctx, r * math.cos(a), 0.02 + r * math.sin(a), z0 + dz + up))
            rings.append(ring)
        mb.loft(rings, "cloth_black", smooth=False)
        edge = [a.lerp(b, 0.5) for a, b in zip(*rings)]
        mb.path(edge + edge[:1], [0.012 * s] * (n + 1), 4 if hq else 3, "gold")
        with mb.xf(Matrix.Translation(_at(ctx, 0, 0.02, z0))):
            mb.lathe([(0.218 * s, 0.0), (0.205 * s, 0.1 * s), (0.15 * s, 0.165 * s), (0.04 * s, 0.18 * s)], q["head_s"], "cloth_black", smooth=hq)
        crest = _at(ctx, 0.215, -0.04, z0 + 0.07)
        mb.sphere(crest, (0.01 * s, 0.04 * s, 0.04 * s), 6 if hq else 4, 3, "silver", smooth=False)
        mb.sphere(crest + Vector((0.008, 0, 0)) * s, (0.008 * s, 0.022 * s, 0.022 * s), 5 if hq else 4, 3, "gold", smooth=False)
        plume = [crest, crest + Vector((0.04, 0.09, 0.12)) * s, crest + Vector((-0.04, 0.27, 0.16)) * s, crest + Vector((-0.17, 0.44, 0.06)) * s]
        mb.path(plume, [0.02 * s, 0.045 * s, 0.035 * s, 0.004 * s], 5 if hq else 3, "storm_dark")
        if hq:
            mb.path([p + Vector((0.0, -0.006, 0.022)) * s for p in plume[1:]], [0.025 * s, 0.02 * s, 0.003 * s], 3, "gem_blue")


def vane_king(ctx):
    """Act 3, the King of All Pirates: royal regalia over the same rule-breaking deckhand. The red bandana still
    under a grand gold-edged tricorn-cavalier hat with a fleet crest and storm-petrel plume. A calf-length
    obsidian greatcoat lined in crimson silk, a high flared collar, a layered storm-cape mantle trimmed in gold,
    wide cuffs with gold buttons and braided epaulets. A black leather-and-gold brigandine over a dark silk shirt
    open at the throat, a wide crimson sash with a gold buckle, twin ivory-gripped gold pistols holstered across
    the chest, a parrying dagger and an empty gold-fitted scabbard. Brass-cuffed gauntlets, signet rings, and
    cavalier boots with gold heel guards and spurs."""
    mb, q, s, g, w, hq = ctx.mb, ctx.q, ctx.s, ctx.g, ctx.w, ctx.hq
    hero = ctx.hero
    _vane_head(ctx, 3)
    _vane_hat(ctx)
    long_coat(ctx, "cloth_black", hero.top, tail_len=0.26)
    cape(ctx, "cloth_black", length=1.02, lining="gem_red")
    _v_neck(ctx, _COAT_FRONT, hero.skin, "cloth_black", depth=1.2)
    with mb.bound_to("chest"):
        # Crimson silk lining turned back as lapels, edged in gold.
        for sign in (1, -1):
            outline = [(0.07, 1.37), (0.17, 1.33), (0.15, 1.1), (0.1, 1.04)]
            pts = [(sign * x * w * s, _surface_y(ctx, _COAT_FRONT, x * w * s, z * s) - 0.012 * s, z * s) for x, z in outline]
            mb.plate(pts, 0.008 * s, "gem_red")
            if hq:
                mb.path([Vector(p) + Vector((0, -0.006, 0)) * s for p in pts[1:3]], [0.006 * s] * 2, 3, "gold")
        # A high, flared collar.
        mb.plate([(-0.16 * s, 0.06 * s, 1.36 * s), (0.16 * s, 0.06 * s, 1.36 * s), (0.22 * s, 0.1 * s, 1.56 * s), (-0.22 * s, 0.1 * s, 1.56 * s)], 0.025 * s, "cloth_black")
        if hq:
            mb.tube((-0.22 * s, 0.085 * s, 1.56 * s), (0.22 * s, 0.085 * s, 1.56 * s), 0.008 * s, sides=4, color="gold")
        # The storm-cape mantle over the shoulders, two layers, fringed and trimmed in gold.
        for sign in (1, -1):
            for dz, k in ((0.0, 1.0), (-0.07, 0.92)):
                mb.sphere((sign * 0.28 * w * s, 0.0, (1.31 + dz) * s), (0.15 * k * s, 0.17 * g * k * s, 0.07 * s), 8 if hq else 4, 3, "cloth_black", smooth=False)
            if hq:
                hem = [Vector((sign * (0.16 + 0.06 * j) * w * s, -0.12 * g * s, (1.24 - 0.02 * math.sin(j * 2.4)) * s)) for j in range(5)]
                mb.path(hem, [0.006 * s] * 5, 3, "gold")
                for k in (-0.06, 0.0, 0.06):
                    mb.tube((sign * 0.4 * w * s, k * s, 1.3 * s), (sign * 0.42 * w * s, k * s, 1.2 * s), 0.011 * s, sides=3, color="gold")
        # The brigandine studded in gold, and twin pistols holstered across the chest.
        if hq:
            for x in (-0.05, 0.05):
                for z in (1.22, 1.13, 1.04):
                    mb.sphere((x * s, _surface_y(ctx, _COAT_FRONT, x * s, z * s) - 0.004 * s, z * s), 0.009 * s, 4, 3, "gold", smooth=False)
        for sign in (1, -1):
            a = Vector((sign * 0.24 * w * s, _surface_y(ctx, _COAT_FRONT, sign * 0.24 * w * s, 1.32 * s) - 0.01 * s, 1.32 * s))
            b = Vector((-sign * 0.12 * w * s, _surface_y(ctx, _COAT_FRONT, -sign * 0.12 * w * s, 1.06 * s) - 0.014 * s, 1.06 * s))
            mb.path([a, a.lerp(b, 0.5) + Vector((0, -0.012, 0)) * s, b], [0.017 * s] * 3, 4 if hq else 3, "leather_dark")
            at = a.lerp(b, 0.3) + Vector((0, -0.03, 0)) * s
            _pistol(mb, s, at, Vector((-sign * 0.25, -0.05, -1)).normalized(), Vector((0, -1, 0)), barrel="gold", grip="enamel", mount="gold", hq=hq)

    # ---- wide cuffs with gold buttons, brass-cuffed gauntlets and signet rings.
    for side, sign in (("L", 1), ("R", -1)):
        elbow, wrist = (Vector(p) for p in ctx.joints[f"lower_arm.{side}"])
        r1 = 0.05 * s * g * hero.arm_bulk
        with mb.bound_to(f"lower_arm.{side}"):
            mb.tube(elbow.lerp(wrist, 0.62), elbow.lerp(wrist, 0.96), r1 * 1.45, r1 * 1.8, sides=8 if hq else 4, color="cloth_black")
            if hq:
                mb.tube(elbow.lerp(wrist, 0.955), elbow.lerp(wrist, 0.975), r1 * 1.85, sides=8, color="gold")
                for t in (0.72, 0.84):
                    mb.sphere(elbow.lerp(wrist, t) + Vector((sign * 0.4, -1, 0)).normalized() * r1 * 1.72, 0.012 * s, 4, 3, "gold", smooth=False)
        hand_w, hand_t = (Vector(p) for p in ctx.joints[f"hand.{side}"])
        with mb.bound_to(f"hand.{side}"):
            mb.tube(hand_w.lerp(hand_t, -0.05), hand_w.lerp(hand_t, 0.2), 0.064 * s, 0.06 * s, sides=6 if hq else 4, color="brass")
            if hq:
                for dy in (-0.02, 0.015):
                    mb.sphere(hand_w.lerp(hand_t, 0.85) + Vector((-sign * 0.045, dy, 0)) * s, 0.012 * s, 4, 3, "gold", smooth=False)

    # ---- the crimson sash and its gold buckle, a parrying dagger, the empty scabbard.
    sash(ctx, "gem_red")
    with mb.bound_to("hips"):
        sash_r = 0.215 * w * s * g ** 0.3
        mb.box((0, -sash_r - 0.006 * s, 0.885 * s), (0.08 * s, 0.016 * s, 0.07 * s), "gold")
        dagger = Vector((-0.24 * w * s, -0.05 * s, 0.9 * s))
        mb.tube(dagger, dagger + Vector((-0.02, -0.03, -0.24)) * s, 0.016 * s, 0.01 * s, sides=4, color="cloth_black")
        mb.box(tuple(dagger + Vector((0, 0, 0.012)) * s), (0.09 * s, 0.022 * s, 0.016 * s), "gold")
        mb.tube(dagger + Vector((0, 0, 0.02)) * s, dagger + Vector((0.004, 0.0, 0.09)) * s, 0.012 * s, sides=4, color="leather_dark")
        if hq:
            mb.sphere(dagger + Vector((0.004, 0, 0.1)) * s, 0.016 * s, 4, 3, "gold", smooth=False)
    _scabbard(ctx, "cloth_black", "gold")

    # ---- cavalier boots: wide cuffs, gold heel guards and spurs.
    _boot_cuffs(ctx, "leather_dark", flare=1.34)
    for side in ("L", "R"):
        ankle = Vector(ctx.joints[f"foot.{side}"][0])
        with mb.bound_to(f"foot.{side}"):
            heel = Vector((ankle.x, 0.05 * s, 0.04 * s))
            mb.box(tuple(heel), (0.1 * s, 0.03 * s, 0.07 * s), "gold")
            if hq:
                mb.tube(heel + Vector((0, 0.01, 0.02)) * s, heel + Vector((0, 0.07, 0.03)) * s, 0.005 * s, sides=3, color="gold")
                mb.sphere(heel + Vector((0, 0.08, 0.03)) * s, (0.004 * s, 0.018 * s, 0.018 * s), 6, 3, "gold", smooth=False)



def _gorse_hat(ctx):
    """An absurdly oversized tricorn, brass-edged and sitting askew, its feather plume singed and bent."""
    mb, q, s, hq = ctx.mb, ctx.q, ctx.s, ctx.hq
    n = 18 if hq else 9
    place = Matrix.Translation(_at(ctx, 0, 0.02, 0.15)) @ Matrix.Rotation(-0.26, 4, "Y") @ Matrix.Rotation(0.07, 4, "X")
    with mb.bound_to("head"), mb.xf(place):
        rings = []
        for dz in (0.0, 0.03):
            ring = []
            for j in range(n):
                a = 2 * math.pi * (j + 0.5) / n
                corner = 0.5 + 0.5 * math.cos(3 * (a + math.pi / 2))
                r = 0.46 * (1.0 + 0.24 * corner)
                ring.append((r * math.cos(a) * s, r * math.sin(a) * s, (dz + 0.13 * (1 - corner)) * s))
            rings.append(ring)
        mb.loft(rings, "leather", smooth=False)
        edge = [a.lerp(b, 0.5) for a, b in zip((Vector(p) for p in rings[0]), (Vector(p) for p in rings[1]))]
        mb.path(edge + edge[:1], [0.012 * s] * (n + 1), 4 if hq else 3, "brass")
        mb.lathe([(0.225 * s, 0.0), (0.215 * s, 0.13 * s), (0.15 * s, 0.2 * s), (0.04 * s, 0.215 * s)], q["head_s"], "leather", smooth=hq)
        # The plume, snapped halfway and burnt at the end.
        plume = [Vector((0.15, 0.06, 0.14)) * s, Vector((0.26, 0.14, 0.32)) * s, Vector((0.33, 0.24, 0.34)) * s, Vector((0.43, 0.36, 0.2)) * s]
        mb.path(plume, [0.022 * s, 0.05 * s, 0.045 * s, 0.012 * s], 5 if hq else 3, "parchment")
        mb.sphere(plume[-1], 0.02 * s, 5 if hq else 4, 3, "rock_dark", smooth=False)
        if hq:
            mb.path([plume[1] + Vector((0, -0.01, 0.03)) * s, plume[2] + Vector((0.01, -0.012, 0.04)) * s, plume[3] + Vector((-0.02, -0.01, 0.06)) * s], [0.02 * s, 0.018 * s, 0.004 * s], 3, "gem_red")


def scrap_captain(ctx):
    """Captain Gorse, the bellowing Scrap-brig rival: a barrel-chested, short-legged blowhard whose belly arrives
    first. Ruddy and sunburnt, with enormous ginger-brown mutton chops bristling out, a wide gap-toothed grin
    with a gold tooth, amber eyes, a bulbous much-broken nose and flushed cheeks. An absurdly oversized tricorn
    worn askew, its plume singed and bent. A long patchwork coat of salvaged sailcloth with riveted scrap-metal
    plates across the shoulders, a gaudy brass-buttoned waistcoat straining over the belly, a sash of stolen
    brocade, a belt hung with a dented brass speaking-trumpet, and oversized cuffed boots."""
    import copy
    mb, q, s, g, w, hq = ctx.mb, ctx.q, ctx.s, ctx.g, ctx.w, ctx.hq
    hero = ctx.hero

    # ---- the belly, straining the gaudy waistcoat, with brass buttons down it.
    belly = Vector((0, -0.13 * g * s, 1.0 * s))
    rx, ry, rz = 0.19 * w * s, 0.15 * g * s, 0.2 * s
    with mb.bound_to("spine"):
        mb.sphere(belly, (rx, ry, rz), 10 if hq else 8, 5 if hq else 4, hero.top, smooth=hq)
        for z in ((1.12, 1.04, 0.96, 0.88) if hq else (1.0,)):
            f = math.sqrt(max(0.0, 1 - ((z * s - belly.z) / rz) ** 2))
            mb.sphere((0, belly.y - ry * f - 0.004 * s, z * s), 0.017 * s, 5 if hq else 4, 3, "brass", smooth=False)

    # ---- the patchwork coat, cut wide enough to go round all that, riveted scrap across the shoulders.
    big = copy.copy(ctx)
    big.g = g * 1.25
    long_coat(big, "canvas_dark", hero.top, tail_len=0.4)
    with mb.bound_to("chest"):
        # The waistcoat down the open front, centred: the coat's own opening sits a little off to one side.
        mb.loft(_front_shell(big, [(0.255, 0.18, 1.06, 30), (0.32, 0.19, 1.28, 30), (0.16, 0.118, 1.37, 30)], wall=0.012), hero.top, smooth=False)
    patches = [(0.24, 1.18, "cloth_brown"), (-0.22, 1.02, "cloth_green"), (0.22, 0.97, "canvas"), (-0.25, 1.22, "navy")]
    with mb.bound_to("chest"):
        for x, z, c in (patches if hq else patches[:2]):
            y = _surface_y(big, _COAT_FRONT, x * w * s, z * s)
            mb.sphere((x * w * s, y, z * s), (0.06 * s, 0.006 * s, 0.05 * s), 6 if hq else 4, 3, c, smooth=False)
            if hq:
                for dz in (-0.03, 0.03):
                    mb.box((x * w * s - 0.055 * s, y - 0.003 * s, (z + dz) * s), (0.012 * s, 0.004 * s, 0.003 * s), "eye_dark")
        if hq:
            for x, z, c in ((0.1, 1.15, "cloth_green"), (-0.14, 1.0, "faction_a")):
                y = -_surface_y(big, _COAT_FRONT, x * w * s, z * s)
                mb.sphere((x * w * s, y, z * s), (0.07 * s, 0.006 * s, 0.06 * s), 6, 3, c, smooth=False)
        for sign in (1, -1):
            for (x, y, z, sx, sy, c, roll) in ((0.27, -0.01, 1.355, 0.15, 0.17, "iron_light", 0.25), (0.37, 0.0, 1.25, 0.12, 0.15, "rust", 1.2)):
                at = Vector((sign * x * w * s, y * s, z * s))
                with mb.xf(Matrix.Translation(at) @ Matrix.Rotation(-sign * roll, 4, "Y")):
                    mb.box((0, 0, 0), (sx * s, sy * s, 0.03 * s), c)
                    if hq:
                        for rx_, ry_ in ((-0.4, -0.35), (0.4, -0.35), (0.0, 0.38)):
                            mb.sphere((rx_ * sx * s, ry_ * sy * s, 0.017 * s), 0.008 * s, 4, 3, "iron", smooth=False)

    # ---- big turned-back cuffs, and a mismatched patch on the left sleeve.
    for side in ("L", "R"):
        elbow, wrist = (Vector(p) for p in ctx.joints[f"lower_arm.{side}"])
        r1 = 0.05 * s * g * hero.arm_bulk
        with mb.bound_to(f"lower_arm.{side}"):
            mb.tube(elbow.lerp(wrist, 0.68), elbow.lerp(wrist, 0.97), r1 * 1.4, r1 * 1.75, sides=8 if hq else 4, color="leather")
    if hq:
        shoulder, elbow = (Vector(p) for p in ctx.joints["upper_arm.L"][:2])
        r = 0.075 * s * g * hero.arm_bulk
        with mb.bound_to("upper_arm.L"):
            mb.tube(shoulder.lerp(elbow, 0.35), shoulder.lerp(elbow, 0.62), r * 1.06, r * 0.98, sides=8, color="cloth_green")

    # ---- a sash of stolen brocade under the belly, and the dented brass speaking-trumpet on the left hip.
    with mb.bound_to("hips"):
        mb.loft([_body_ring(ctx, 0.235, 0.2, z, q["torso"]) for z in (0.78, 0.86)], "gold_dark", smooth=False)
        knot = Vector((0.2 * w * s, -0.1 * g * s, 0.8 * s))
        mb.sphere(knot, 0.035 * s, 6 if hq else 4, 3, "gold_dark", smooth=False)
        # Each tail starts at its own spot on the knot: tails sharing an edge weld into a doubled face on export.
        for k, (dx, dz) in enumerate(((0.02, -0.2), (0.06, -0.16)) if hq else ((0.03, -0.18),)):
            top = Vector((0.025 * k, -0.006 * k, -0.012 * k)) * s
            mb.plate([knot + top + Vector((-0.02, -0.01, 0)) * s, knot + top + Vector((0.03, -0.01, 0)) * s, knot + Vector((dx + 0.03, -0.02, dz)) * s, knot + Vector((dx - 0.02, -0.02, dz)) * s], 0.01 * s, "gold_dark")
        horn = Vector((0.27 * w * s, 0.04 * s, 0.86 * s))
        with mb.xf(Matrix.Translation(horn) @ Matrix.Rotation(math.pi * 0.82, 4, "X") @ Matrix.Rotation(-0.3, 4, "Y")):
            mb.lathe([(0.012 * s, 0.0), (0.015 * s, 0.12 * s), (0.03 * s, 0.2 * s), (0.065 * s, 0.25 * s)], 8 if hq else 5, "brass", smooth=False, caps=(True, False))
            if hq:
                mb.sphere((0.04 * s, 0.0, 0.18 * s), (0.012 * s, 0.02 * s, 0.02 * s), 4, 3, "gold_dark", smooth=False)  # The dent.

    # ---- oversized cuffed boots.
    _boot_cuffs(ctx, "leather", flare=1.45)

    # ---- the head: mutton chops, a bulbous broken nose, flushed cheeks, the gap-toothed grin, the hat.
    hair_cap(ctx)
    with mb.bound_to("head"):
        for sign in (1, -1):
            chop = [_at(ctx, sign * 0.17, -0.07, 0.06), _at(ctx, sign * 0.205, -0.1, -0.06), _at(ctx, sign * 0.19, -0.125, -0.15)]
            mb.path(chop, [0.05 * s, 0.072 * s, 0.05 * s], 6 if hq else 4, hero.hair, smooth=hq)
            if hq:
                for k, z in enumerate((0.0, -0.06, -0.12)):
                    root = _at(ctx, sign * 0.23, -0.1, z)
                    mb.tube(root, root + Vector((sign * 0.08, -0.02 + 0.02 * k, 0.02 - 0.03 * k)) * s, 0.024 * s, 0.003 * s, sides=4, color=hero.hair)
                mb.sphere(_on_skull(ctx, sign * 0.1, -0.05, -0.002), (0.042 * s, 0.008 * s, 0.03 * s), 6, 3, "rust", smooth=False)
        mb.sphere(_at(ctx, 0.012, -0.215, -0.035), 0.048 * s, 8 if hq else 5, 4 if hq else 3, hero.skin, smooth=hq)
        mb.sphere(_at(ctx, 0.018, -0.252, -0.045), 0.024 * s, 6 if hq else 4, 3, "rust", smooth=False)
        if hq:
            mb.box(tuple(_at(ctx, 0, -0.178, -0.11)), (0.12 * s, 0.02 * s, 0.036 * s), "eye_dark")
            for x, c in ((-0.045, "enamel"), (-0.025, "enamel"), (0.015, "gold"), (0.035, "enamel")):
                mb.box(tuple(_at(ctx, x, -0.19, -0.099)), (0.016 * s, 0.008 * s, 0.016 * s), c)
            for sign in (1, -1):
                mb.tube(_at(ctx, sign * 0.058, -0.182, -0.11), _at(ctx, sign * 0.075, -0.175, -0.088), 0.005 * s, sides=3, color="eye_dark")
        else:
            mb.box(tuple(_at(ctx, 0, -0.165, -0.11)), (0.1 * s, 0.04 * s, 0.03 * s), "eye_dark")
    _gorse_hat(ctx)



def syndicate_lord(ctx):
    """Lord Ashgrave, the pinched Syndicate toll-lord: tall, narrow-shouldered and brittle-thin. A long, pinched
    face powdered chalk-white, a beauty mark high on the left cheek, thin pursed lips, pale violet eyes in
    shadowed, sleepless sockets behind a gold-rimmed monocle on a fine chain, and a tight grey-powdered queue
    tied with black ribbon. A towering starched collar rising past the jaw, a lace jabot, a deep plum frock coat
    frogged in tarnished silver with the Syndicate cipher-case bulging from its inner pocket, a ring of toll-keys
    on a silver chatelaine at the hip, knee breeches, silk stockings and buckled shoes."""
    import copy
    mb, q, s, g, w, hq = ctx.mb, ctx.q, ctx.s, ctx.g, ctx.w, ctx.hq
    hero = ctx.hero

    # ---- the frock coat, tailored tight, frogged in tarnished silver, the cipher-case peeking from inside.
    long_coat(ctx, "faction_a", hero.top, tail_len=0.5)
    with mb.bound_to("chest"):
        # Close the coat's off-centre opening, then show a narrow, centred strip of shirt.
        for bone, coat_rows in (("chest", [(0.25, 0.175, 1.06), (0.315, 0.185, 1.28), (0.15, 0.11, 1.38)]), ("spine", [(0.22, 0.165, 0.9), (0.252, 0.176, 1.08)])):
            with mb.bound_to(bone):
                mb.loft(_front_shell(ctx, [(rx + 0.006, ry + 0.006, z, 48) for rx, ry, z in coat_rows], wall=0.01), "faction_a", smooth=False)
                mb.loft(_front_shell(ctx, [(rx + 0.012, ry + 0.012, z, 17) for rx, ry, z in coat_rows], wall=0.01), hero.top, smooth=False)
        for z in ((1.27, 1.2, 1.13, 1.06) if hq else (1.22, 1.1)):
            for sign in (1, -1):
                x0, x1 = sign * 0.05 * w * s, sign * 0.16 * w * s
                y0, y1 = (_surface_y(ctx, _COAT_FRONT, x, z * s) - 0.006 * s for x in (x0, x1))
                mb.tube((x0, y0, z * s), (x1, y1, z * s), 0.007 * s, sides=4 if hq else 3, color="silver")
                if hq:
                    mb.sphere((x1, y1 - 0.002 * s, z * s), 0.011 * s, 4, 3, "silver", smooth=False)
        case = Vector((0.11 * w * s, _surface_y(ctx, _COAT_FRONT, 0.11 * w * s, 1.22 * s) - 0.005 * s, 1.22 * s))
        mb.tube(case + Vector((0, 0, -0.05)) * s, case + Vector((0.008, 0, 0.06)) * s, 0.021 * s, sides=6 if hq else 4, color="brass")
        if hq:
            mb.sphere(case + Vector((0.008, 0, 0.065)) * s, 0.021 * s, 6, 3, "faction_b", smooth=False)
        # The lace jabot, spilling down the throat in tiers.
        for k, z in enumerate((1.33, 1.27, 1.21) if hq else (1.3,)):
            half = (0.035 + 0.015 * k) * s
            y = _surface_y(ctx, _COAT_FRONT, 0, z * s) - (0.01 + 0.004 * k) * s
            mb.plate([(-half, y, z * s), (half, y, z * s), (half * 0.6, y - 0.012 * s, (z - 0.07) * s), (-half * 0.6, y - 0.012 * s, (z - 0.07) * s)], 0.008 * s, "cloth_white")

    # ---- the towering starched collar, rising past the jaw, open at the throat.
    flat = copy.copy(ctx)
    flat.w = flat.g = 1.0
    with mb.bound_to("neck"):
        mb.loft(_open_shell(flat, [(0.1, 0.1, 1.31), (0.19, 0.19, 1.47)], 32, wall=0.012), "cloth_white", smooth=False)
        mb.tube((0, 0.01 * s, 1.3 * s), (0, 0.01 * s, 1.44 * s), 0.06 * s, 0.055 * s, sides=8 if hq else 5, color=hero.skin)

    # ---- the chatelaine at the left hip: a silver chain and a ring of toll-keys.
    with mb.bound_to("hips"):
        hook = Vector((0.18 * w * s, -0.15 * g * s, 0.9 * s))
        ring = hook + Vector((0.03, -0.01, -0.17)) * s
        mb.path([hook, hook.lerp(ring, 0.5) + Vector((0.01, -0.005, 0)) * s, ring + Vector((0, 0, 0.03)) * s], [0.004 * s] * 3, 3, "silver")
        loop = [ring + Vector((0.03 * math.cos(a), -0.005, 0.03 * math.sin(a))) * s for a in [2 * math.pi * k / 6 for k in range(7)]]
        mb.path(loop, [0.005 * s] * 7, 3, "silver")
        for k in range(4 if hq else 1):
            top = ring + Vector((-0.02 + 0.013 * k, -0.008, -0.025)) * s
            mb.tube(top, top + Vector((0.004 * (k - 1.5), 0, -0.07)) * s, 0.005 * s, sides=3, color="iron_light")
            if hq:
                mb.box(tuple(top + Vector((0.008, 0, -0.065)) * s), (0.014 * s, 0.004 * s, 0.012 * s), "iron_light")

    # ---- knee breeches gartered over silk stockings, and buckled shoes.
    for side in ("L", "R"):
        knee, ankle = (Vector(p) for p in ctx.joints[f"shin.{side}"][:2])
        r = 0.085 * s * g * hero.leg_bulk
        with mb.bound_to(f"shin.{side}"):
            mb.tube(knee.lerp(ankle, -0.05), knee.lerp(ankle, 0.08), r * 1.12, r * 1.08, sides=8 if hq else 4, color=hero.legs)
            if hq:
                mb.tube(knee.lerp(ankle, 0.08), knee.lerp(ankle, 0.11), r * 1.1, sides=8, color="silver")
        ankle = Vector(ctx.joints[f"foot.{side}"][0])
        with mb.bound_to(f"foot.{side}"):
            sides = 8 if hq else 4
            rings = []
            for rx, ry, z in ((0.096, 0.16, -0.004), (0.096, 0.15, 0.09), (0.081, 0.066, 0.172)):
                rings.append([(ankle.x + rx * s * math.cos(2 * math.pi * (j + 0.5) / sides), -0.04 * s + ry * s * math.sin(2 * math.pi * (j + 0.5) / sides), z * s) for j in range(sides)])
            mb.loft(rings, "cloth_black", smooth=hq)
            mb.box((ankle.x, -0.16 * s, 0.1 * s), (0.05 * s, 0.012 * s, 0.035 * s), "silver")

    # ---- the head: a long, pinched, powdered face, the monocle, the queue.
    hair_cap(ctx)
    with mb.bound_to("head"):
        mb.sphere(_at(ctx, 0, -0.06, -0.19), (0.075 * s, 0.09 * s, 0.07 * s), 6 if hq else 4, 3, hero.skin, smooth=hq)  # The long chin.
        mb.sphere(_at(ctx, 0, -0.205, -0.035), (0.022 * s, 0.034 * s, 0.055 * s), 6 if hq else 4, 3, hero.skin, smooth=hq)
        # Thin, pursed lips.
        mb.sphere(_at(ctx, 0, -0.183, -0.115), (0.02 * s, 0.008 * s, 0.009 * s), 6 if hq else 4, 3, "wood_red", smooth=False)
        if hq:
            # Shadowed, sleepless sockets, and the beauty mark high on the left cheek.
            for sign in (1, -1):
                mb.sphere(_on_skull(ctx, sign * 0.08, -0.015, 0.0), (0.04 * s, 0.004 * s, 0.012 * s), 6, 3, "storm", smooth=False)
            mb.sphere(_on_skull(ctx, 0.11, -0.03, 0.002), 0.006 * s, 4, 3, "eye_dark", smooth=False)
        # The gold-rimmed monocle over the right eye, on a fine chain to the collar.
        rim = [_at(ctx, -0.078 + 0.042 * math.cos(a), -0.2, 0.03 + 0.042 * math.sin(a)) for a in [2 * math.pi * k / (10 if hq else 6) for k in range(11 if hq else 7)]]
        mb.path(rim, [0.006 * s] * len(rim), 3, "gold")
        if hq:
            mb.path([rim[7], _at(ctx, -0.11, -0.19, -0.12), _at(ctx, -0.09, -0.15, -0.26)], [0.002 * s] * 3, 3, "gold")
        # The tight, powdered queue, tied with a black ribbon.
        queue = [_at(ctx, 0, 0.19, -0.06), _at(ctx, 0, 0.235, -0.18), _at(ctx, 0, 0.225, -0.3)]
        mb.path(queue, [0.04 * s, 0.032 * s, 0.012 * s], 5 if hq else 3, hero.hair, smooth=hq)
        bow = queue[0].lerp(queue[1], 0.4)
        mb.sphere(bow, (0.03 * s, 0.03 * s, 0.025 * s), 5 if hq else 4, 3, "cloth_black", smooth=False)
        for sign in ((1, -1) if hq else (1,)):
            mb.plate([bow, bow + Vector((sign * 0.06, 0.01, 0.03)) * s, bow + Vector((sign * 0.06, 0.01, -0.03)) * s], 0.006 * s, "cloth_black")
        if hq:
            # A single tight roll above each ear.
            for sign in (1, -1):
                mb.tube(_at(ctx, sign * 0.19, -0.06, 0.04), _at(ctx, sign * 0.195, 0.08, 0.04), 0.032 * s, sides=6, color=hero.hair)



def sky_duelist(ctx):
    """Lady Thrace, the untouchable sky-lounge duelist: statuesque, chin raised, heavy-lidded. A fine-boned face
    with high cheekbones, a hooded green stare, deep crimson lips in a half-smirk, and a towering swept-up
    coiffure the colour of old wine, pinned with jewelled combs, one stray lock curling down over her right eye.
    A fitted wine-and-black duelling coat with a high split collar and long tails, cut away over a corseted silver
    waistcoat; strands of pearls at the throat and one wound round the left wrist; a black silk half-cape clasped
    at the left shoulder with a garnet brooch. Fitted black breeches, tall polished boots with silver heels, long
    black gloves, and a black lace fan snapped open in the left hand."""
    mb, q, s, g, w, hq = ctx.mb, ctx.q, ctx.s, ctx.g, ctx.w, ctx.hq
    hero = ctx.hero
    coat_color = "velvet"

    # ---- the duelling coat, cut away at the front over the corseted silver waistcoat.
    long_coat(ctx, coat_color, hero.top, tail_len=0.36)
    # The coat's own opening sits off-centre: close it and cut a centred one. Panels overlap rather than share a ring.
    for bone, rows, half in (("chest", [(0.25, 0.175, 1.06), (0.315, 0.185, 1.28), (0.15, 0.11, 1.38)], 22),
                             ("spine", [(0.22, 0.165, 0.9), (0.252, 0.176, 1.08)], 34)):
        with mb.bound_to(bone):
            mb.loft(_front_shell(ctx, [(rx + 0.006, ry + 0.006, z, 50) for rx, ry, z in rows], wall=0.01), coat_color, smooth=False)
            mb.loft(_front_shell(ctx, [(rx + 0.012, ry + 0.012, z, half) for rx, ry, z in rows], wall=0.01), hero.top, smooth=False)
    with mb.bound_to("chest"):
        # Black brocade edging down the cut-away fronts, and the corset's lacing.
        for sign in (1, -1):
            edge = []
            for z in ((1.36, 1.24, 1.12, 1.02, 0.94) if hq else (1.36, 1.12, 0.94)):
                rows = _COAT_FRONT
                a = math.radians(22 if z > 1.07 else 34)
                rx = 0.315 if z > 1.2 else 0.27
                x = sign * (rx + 0.012) * w * s * math.sin(a)
                edge.append(Vector((x, _surface_y(ctx, rows, x, z * s) - 0.01 * s, z * s)))
            mb.path(edge, [0.011 * s] * len(edge), 4 if hq else 3, "cloth_black")
        if hq:
            for k in range(4):
                z0, z1 = 1.22 - 0.07 * k, 1.15 - 0.07 * k
                for sign in (1, -1):
                    p0 = Vector((sign * 0.03 * s, _surface_y(ctx, _COAT_FRONT, 0.03 * s, z0 * s) - 0.016 * s, z0 * s))
                    p1 = Vector((-sign * 0.03 * s, _surface_y(ctx, _COAT_FRONT, 0.03 * s, z1 * s) - 0.016 * s, z1 * s))
                    mb.tube(p0, p1, 0.004 * s, sides=3, color="cloth_black")
        # The high split collar, rising behind the neck in two wings.
        for sign in (1, -1):
            mb.plate([(sign * 0.03 * s, 0.07 * s, 1.36 * s), (sign * 0.16 * s, 0.03 * s, 1.36 * s), (sign * 0.22 * s, 0.06 * s, 1.56 * s), (sign * 0.05 * s, 0.11 * s, 1.58 * s)], 0.018 * s, coat_color)
        # The black silk half-cape, clasped at the left shoulder with a garnet brooch.
        # Draped over the left half of the back, rippling as it falls; a fold over the shoulder to the brooch.
        rows, cols = (3, 5) if hq else (2, 3)
        rings = []
        for r in range(rows + 1):
            k = r / rows
            z = (1.37 - 0.4 * k) * s
            outer, inner = [], []
            for c in range(cols + 1):
                u = c / cols
                x = (-0.04 + (0.34 + 0.06 * k) * u) * w * s
                back = (0.15 + 0.06 * k + 0.035 * math.sin(u * math.pi * 2.5) * k) * s * g / 0.8
                outer.append((x, back + 0.012 * s, z))
                inner.append((x, back, z))
            rings.append(outer + inner[::-1])
        mb.loft(rings, "cloth_black", smooth=False)
        mb.plate([(0.16 * w * s, -0.1 * s, 1.37 * s), (0.31 * w * s, 0.08 * s, 1.38 * s), (0.37 * w * s, 0.05 * s, 1.14 * s), (0.31 * w * s, -0.09 * s, 1.18 * s)], 0.012 * s, "cloth_black")
        brooch = Vector((0.17 * w * s, -0.13 * s, 1.34 * s))
        mb.sphere(brooch, (0.024 * s, 0.012 * s, 0.024 * s), 6 if hq else 4, 3, "gem_red", smooth=False)
        if hq:
            ring = [brooch + Vector((0.027 * math.cos(a), 0.002, 0.027 * math.sin(a))) * s for a in [2 * math.pi * k / 8 for k in range(9)]]
            mb.path(ring, [0.004 * s] * 9, 3, "gold")

    # ---- a slender neck, looped with strands of pearls.
    with mb.bound_to("neck"):
        mb.tube((0, 0.01 * s, 1.3 * s), (0, 0.01 * s, 1.46 * s), 0.056 * s, 0.05 * s, sides=8 if hq else 5, color=hero.skin)
        for k, (z, sag) in enumerate(((1.37, 0.03), (1.34, 0.07), (1.32, 0.12)) if hq else ((1.35, 0.06),)):
            arc = [Vector((0.075 * s * math.cos(a), 0.01 * s + 0.07 * s * math.sin(a), (z - sag * math.sin(-a) ** 4) * s)) for a in [math.radians(200 + 140 * j / 8) for j in range(9)]]
            mb.path(arc, [0.008 * s] * 9, 4 if hq else 3, "enamel")

    # ---- long black gloves, a pearl strand round the left wrist, and the lace fan snapped open.
    for side in ("L", "R"):
        elbow, wrist = (Vector(p) for p in ctx.joints[f"lower_arm.{side}"])
        r0 = 0.062 * s * g * hero.arm_bulk
        with mb.bound_to(f"lower_arm.{side}"):
            mb.tube(elbow.lerp(wrist, 0.02), elbow.lerp(wrist, 0.12), r0 * 1.22, r0 * 1.12, sides=8 if hq else 4, color="cloth_black")
    elbow, wrist = (Vector(p) for p in ctx.joints["lower_arm.L"])
    axis = (wrist - elbow).normalized()
    n = Vector((0, -1, 0))
    n = (n - axis * n.dot(axis)).normalized()
    b = axis.cross(n)
    rw = 0.05 * s * g * ctx.hero.arm_bulk * 1.12
    with mb.bound_to("lower_arm.L"):
        coil = [elbow.lerp(wrist, 0.72 + 0.2 * k / 12) + (n * math.cos(k * 1.6) + b * math.sin(k * 1.6)) * rw for k in range(13 if hq else 6)]
        mb.path(coil, [0.008 * s] * len(coil), 3, "enamel")
    hand_w, hand_t = (Vector(p) for p in ctx.joints["hand.L"])
    pivot = hand_w.lerp(hand_t, 0.9) + Vector((-0.02, -0.04, 0)) * s
    with mb.bound_to("hand.L"):
        fan = [pivot] + [pivot + Vector((0.17 * math.sin(a), -0.05, -0.17 * math.cos(a))) * s for a in [math.radians(-55 + 110 * k / (8 if hq else 4)) for k in range(9 if hq else 5)]]
        mb.plate(fan, 0.006 * s, "cloth_black")
        mb.sphere(pivot, 0.012 * s, 4, 3, "gold", smooth=False)
        if hq:
            for p_ in fan[1::2]:
                mb.tube(pivot + Vector((0, -0.006, 0)) * s, pivot.lerp(p_, 0.95) + Vector((0, -0.006, 0)) * s, 0.003 * s, sides=3, color="silver")

    # ---- tall polished boots on silver heels.
    _boot_cuffs(ctx, "cloth_black", flare=1.08)
    for side in ("L", "R"):
        ankle = Vector(ctx.joints[f"foot.{side}"][0])
        with mb.bound_to(f"foot.{side}"):
            mb.box((ankle.x, 0.06 * s, 0.035 * s), (0.06 * s, 0.05 * s, 0.07 * s), "silver")

    # ---- the head: high cheekbones, hooded lids, crimson lips, and the towering coiffure.
    hair = hero.hair
    hair_cap(ctx)
    with mb.bound_to("head"):
        for sign in (1, -1):
            mb.sphere(_on_skull(ctx, sign * 0.12, -0.035, -0.004), (0.045 * s, 0.02 * s, 0.022 * s), 6 if hq else 4, 3, hero.skin, smooth=False)
        if hq:
            for sign in (1, -1):
                # Heavy, hooded lids, half down over the eyes.
                mb.sphere(_at(ctx, sign * 0.078, -0.176, 0.045), (0.05 * s, 0.017 * s, 0.017 * s), 8, 3, hero.skin, smooth=False)
            # Deep crimson lips in a half-smirk, lifted at the left corner.
            mb.path([_on_skull(ctx, x, z) for x, z in ((-0.045, -0.106), (-0.015, -0.11), (0.02, -0.108), (0.05, -0.095))], [0.007 * s, 0.009 * s, 0.009 * s, 0.005 * s], 4, "gem_red")
        else:
            mb.box(tuple(_at(ctx, 0, -0.17, -0.105)), (0.07 * s, 0.03 * s, 0.018 * s), "gem_red")
        # The towering, swept-up coiffure the colour of old wine.
        tiers = (((0, 0.03, 0.25), (0.17, 0.16, 0.15)), ((0.01, 0.05, 0.4), (0.12, 0.12, 0.13)))
        for centre, radii in tiers:
            mb.sphere(_at(ctx, *centre), tuple(r * s for r in radii), 10 if hq else 8, 5 if hq else 4, hair, smooth=hq)
        if hq:
            for sign in (1, -1):
                mb.path([_at(ctx, sign * 0.17, -0.06, 0.08), _at(ctx, sign * 0.16, -0.02, 0.22), _at(ctx, sign * 0.1, 0.03, 0.34)], [0.04 * s, 0.045 * s, 0.03 * s], 5, hair, smooth=True)
            # Jewelled combs pinned high.
            for x, z, gem in ((0.13, 0.32, "faction_b"), (-0.1, 0.42, "gem_red"), (0.07, 0.47, "faction_b")):
                mb.box(tuple(_at(ctx, x, 0.0, z)), (0.06 * s, 0.012 * s, 0.022 * s), "gold")
                mb.sphere(_at(ctx, x, -0.008, z + 0.012), 0.011 * s, 4, 3, gem, smooth=False)
        # The one deliberate stray lock, curling down over her right eye.
        lock = [_at(ctx, -0.05, -0.17, 0.14), _at(ctx, -0.085, -0.205, 0.07), _at(ctx, -0.1, -0.21, 0.0), _at(ctx, -0.08, -0.205, -0.04)]
        mb.path(lock if hq else lock[::3], [0.014 * s, 0.012 * s, 0.009 * s, 0.003 * s] if hq else [0.014 * s, 0.004 * s], 4 if hq else 3, hair, smooth=hq)



def free_fleet_flyer(ctx):
    """Captain Ria, the joyful free-fleet wingmate: compact, wiry and quick. Sun-browned and freckled, dark hair
    cropped short and wind-tousled on top and shaved close at the sides, bright amber eyes, an enormous open toothy
    grin, a burst of gold earrings climbing the right ear and a thin white scar on the chin. A sleeveless, faded
    sky-blue flight jacket with a sheepskin collar, open over a rust-orange shirt, the free fleet's sigil (a broken
    chain sprouting wings) painted on its back, and a crossed pair of signal-flag tubes slung behind. Brass flight
    goggles with amber lenses pushed up into the hair, fingerless leather gloves, a belt of brass grapple clips,
    patched canvas trousers and lace-up flight boots."""
    mb, q, s, g, w, hq = ctx.mb, ctx.q, ctx.s, ctx.g, ctx.w, ctx.hq
    hero = ctx.hero
    jacket = "cloud_shade"

    # ---- the sleeveless flight jacket, open over the shirt, centred (the helper's opening sits off to one side).
    short_jacket(ctx, jacket, hero.top)
    for bone, rows in (("chest", [(0.245, 0.17, 1.06), (0.31, 0.18, 1.28), (0.15, 0.11, 1.38)]), ("spine", [(0.225, 0.165, 0.97), (0.247, 0.173, 1.09)])):
        with mb.bound_to(bone):
            mb.loft(_front_shell(ctx, [(rx + 0.006, ry + 0.006, z, 50) for rx, ry, z in rows], wall=0.01), jacket, smooth=False)
            mb.loft(_front_shell(ctx, [(rx + 0.012, ry + 0.012, z, 24) for rx, ry, z in rows], wall=0.01), hero.top, smooth=False)
    with mb.bound_to("chest"):
        # The sheepskin-lined collar, turned out round the neck.
        mb.lathe([(0.12 * s, 1.33 * s), (0.17 * s, 1.37 * s), (0.15 * s, 1.42 * s)], 10 if hq else 6, "canvas", smooth=hq, caps=(False, False))
        # The free fleet's sigil on the back: a broken chain sprouting wings.
        back = Vector((0, 0.18 * g * s + 0.006 * s, 1.16 * s))
        for sign in (1, -1):
            link = [back + Vector((sign * (0.03 + 0.02 * math.cos(a)), 0, 0.03 * math.sin(a))) * s for a in [2 * math.pi * k / 6 for k in range(6)]]
            mb.path(link + ([link[0]] if hq else []), [0.006 * s] * (len(link) + (1 if hq else 0)), 3, "iron_light")
            wing = [back + Vector((sign * 0.05, 0.002, 0.0)) * s, back + Vector((sign * 0.17, 0.004, 0.09)) * s, back + Vector((sign * 0.15, 0.004, 0.02)) * s, back + Vector((sign * 0.12, 0.004, -0.04)) * s]
            mb.plate(wing, 0.006 * s, "cloud")
        # A crossed pair of signal-flag tubes slung across the back, flags poking out the top.
        for sign in (1, -1):
            top = Vector((sign * 0.2 * w * s, 0.21 * g * s, 1.44 * s))
            bottom = Vector((-sign * 0.16 * w * s, 0.22 * g * s, 1.0 * s))
            mb.tube(top, bottom, 0.026 * s, sides=6 if hq else 4, color="leather")
            mb.tube(top, top + (top - bottom).normalized() * 0.02 * s, 0.03 * s, sides=6 if hq else 4, color="brass")
            if hq:
                flag = top + Vector((0, 0, 0.02)) * s
                mb.plate([flag, flag + Vector((sign * 0.08, 0.0, 0.04)) * s, flag + Vector((0.0, 0.0, 0.1)) * s], 0.005 * s, "gem_red" if sign > 0 else "amber")

    # ---- a belt of brass grapple clips, and patches on the canvas trousers.
    with mb.bound_to("hips"):
        belt_r = 0.205 * w * s * 1.03
        for a in ([-70, -40, -10, 200, 230] if hq else [-50, 210]):
            ra = math.radians(a)
            at = Vector((belt_r * math.cos(ra), belt_r * math.sin(ra), 0.89 * s)) * 1.03
            mb.tube(at, at + Vector((0, 0, -0.06)) * s, 0.008 * s, sides=4, color="brass")
            if hq:
                mb.box(tuple(at + Vector((0, 0, -0.065)) * s), (0.03 * s, 0.03 * s, 0.012 * s), "brass")
    if hq:
        for side, sign, c in (("L", 1, "cloth_brown"), ("R", -1, "canvas")):
            hip, knee = (Vector(p) for p in ctx.joints[f"thigh.{side}"][:2])
            r = (0.1 - 0.025 * 0.5) * s * g * hero.leg_bulk
            with mb.bound_to(f"thigh.{side}"):
                mb.sphere(hip.lerp(knee, 0.5) + Vector((sign * 0.02, -r, 0)) * s / s, (0.04 * s, 0.006 * s, 0.05 * s), 6, 3, c, smooth=False)

    # ---- fingerless gloves: bare fingers past the leather.
    if hq:
        for side, sign in (("L", 1), ("R", -1)):
            hand_w, hand_t = (Vector(p) for p in ctx.joints[f"hand.{side}"])
            with mb.bound_to(f"hand.{side}"):
                mb.sphere(hand_w.lerp(hand_t, 0.85), (0.05 * s, 0.045 * s, 0.032 * s), 6, 3, hero.skin, smooth=False)

    # ---- lace-up flight boots.
    _boot_cuffs(ctx, "leather_dark", flare=1.08, cords="rope")

    # ---- the head: cropped and tousled on top, shaved at the sides, goggles up, the grin, the earrings.
    hair = hero.hair
    with mb.bound_to("head"):
        mb.sphere(_at(ctx, 0, 0.03, 0.1), (0.19 * s, 0.205 * s, 0.15 * s), q["head_s"], 4 if hq else 3, hair, smooth=hq)
        for k in range(7 if hq else 0):  # On LQ a few tufts read as ears: the cropped cap alone is cleaner.
            a = -1.0 + 2.0 * k / 6
            root = _at(ctx, 0.14 * math.sin(a), -0.02 + 0.06 * math.cos(k * 2.3), 0.2)
            mb.tube(root, root + Vector((0.04 * math.sin(a) + 0.02 * math.cos(k * 1.7), 0.05, 0.07)) * s, 0.04 * s, 0.004 * s, sides=4 if hq else 3, color=hair)
    goggles_up(ctx, lens="amber")
    with mb.bound_to("head"):
        if hq:
            # The enormous open grin, top teeth showing.
            mb.box(tuple(_at(ctx, 0, -0.176, -0.11)), (0.11 * s, 0.02 * s, 0.04 * s), "eye_dark")
            mb.box(tuple(_at(ctx, 0, -0.188, -0.096)), (0.085 * s, 0.008 * s, 0.014 * s), "enamel")
            for sign in (1, -1):
                mb.tube(_at(ctx, sign * 0.052, -0.18, -0.115), _at(ctx, sign * 0.075, -0.172, -0.088), 0.006 * s, sides=3, color="eye_dark")
            # Freckles from open-air flying, and the thin white scar on the chin.
            for x, z in ((-0.1, -0.03), (-0.07, -0.05), (-0.12, -0.06), (0.1, -0.03), (0.07, -0.05), (0.12, -0.06), (-0.02, -0.02), (0.02, -0.025)):
                mb.sphere(_on_skull(ctx, x, z, 0.003), 0.005 * s, 4, 3, "skin_dark", smooth=False)
            mb.path([_on_skull(ctx, 0.025, -0.16), _on_skull(ctx, 0.03, -0.2)], [0.003 * s, 0.002 * s], 3, "skin_light")
        else:
            mb.box(tuple(_at(ctx, 0, -0.165, -0.11)), (0.1 * s, 0.04 * s, 0.04 * s), "eye_dark")
        # A burst of gold earrings climbing the right ear.
        for k, z in enumerate((-0.07, -0.03, 0.01, 0.05) if hq else (-0.05,)):
            hoop = [_at(ctx, -0.205 - 0.018 * math.cos(a) - 0.005 * k, -0.01, z + 0.018 * math.sin(a)) for a in [2 * math.pi * j / 6 for j in range(7)]]
            mb.path(hoop, [0.004 * s] * 7, 3, "gold")



def gale_gunner(ctx):
    """Mirren, the laughing master gunner of the old crew: stocky, broad-hipped, round-faced and mid-laugh. A wild
    riot of copper curls exploding out from under a knotted green-and-gold headscarf; a rosy, freckled face dusted
    with black powder across the nose and cheeks; bright green eyes crinkled almost shut over a huge open laugh.
    The Sovereign Gale's crimson gun-crew colours worn soft and scorched: a short open crimson waistcoat with brass
    buttons, half of them missing, over a billowing cream shirt, its sleeves rolled and tied off with powder-stained
    ribbon. Padded brass ear-cups hung round the neck, never worn; a wide sash with a powder horn painted with a
    laughing moon; a canvas shot bag at the hip; striped sailcloth trousers and cuffed sea-boots."""
    mb, q, s, g, w, hq = ctx.mb, ctx.q, ctx.s, ctx.g, ctx.w, ctx.hq
    hero = ctx.hero
    vest = "faction_a"

    # ---- the short open waistcoat, centred, buttons half missing.
    short_jacket(ctx, vest, hero.top)
    for bone, rows in (("chest", [(0.245, 0.17, 1.06), (0.31, 0.18, 1.28), (0.15, 0.11, 1.38)]), ("spine", [(0.225, 0.165, 0.97), (0.247, 0.173, 1.09)])):
        with mb.bound_to(bone):
            mb.loft(_front_shell(ctx, [(rx + 0.006, ry + 0.006, z, 50) for rx, ry, z in rows], wall=0.01), vest, smooth=False)
            mb.loft(_front_shell(ctx, [(rx + 0.012, ry + 0.012, z, 22) for rx, ry, z in rows], wall=0.01), hero.top, smooth=False)
    with mb.bound_to("chest"):
        rows = [(0.257, 0.182, 1.06), (0.322, 0.192, 1.28), (0.162, 0.122, 1.38)]
        for z, there in (((1.24, True), (1.17, False), (1.1, True), (1.03, False)) if hq else ((1.2, True),)):
            x = 0.105 * w * s
            y = _surface_y(ctx, [(rx, ry, z_) for rx, ry, z_ in rows], x, z * s) - 0.006 * s
            if there:
                mb.sphere((x, y, z * s), 0.015 * s, 5 if hq else 4, 3, "brass", smooth=False)
            else:
                mb.tube((x, y, z * s), (x - 0.004 * s, y - 0.004 * s, (z - 0.02) * s), 0.002 * s, sides=3, color="rope")

    # ---- billowing sleeves, rolled and tied off with powder-stained ribbon over thick forearms.
    for side, sign in (("L", 1), ("R", -1)):
        shoulder, elbow = (Vector(p) for p in ctx.joints[f"upper_arm.{side}"][:2])
        wrist = Vector(ctx.joints[f"lower_arm.{side}"][1])
        r = 0.075 * s * g * hero.arm_bulk
        with mb.bound_to(f"upper_arm.{side}"):
            mb.sphere(shoulder.lerp(elbow, 0.55), (r * 1.35, r * 1.35, r * 1.8), 8 if hq else 5, 4 if hq else 3, hero.top, smooth=hq)
        with mb.bound_to(f"lower_arm.{side}"):
            mb.tube(elbow.lerp(wrist, 0.04), elbow.lerp(wrist, 0.2), r * 1.2, r * 1.1, sides=8 if hq else 4, color=hero.top)
            mb.tube(elbow.lerp(wrist, 0.2), elbow.lerp(wrist, 0.24), r * 1.12, sides=8 if hq else 4, color="rock_dark")
            if hq:
                knot = elbow.lerp(wrist, 0.22) + Vector((sign * 0.4, -1, 0)).normalized() * r * 1.12
                for dz in (0.03, -0.03):
                    mb.tube(knot, knot + Vector((sign * 0.02, -0.02, dz - 0.03)) * s, 0.008 * s, 0.003 * s, sides=3, color="rock_dark")
                for k, t_ in enumerate((0.4, 0.55, 0.7)):
                    mb.sphere(elbow.lerp(wrist, t_) + Vector((sign * 0.3, -1, 0.1 * k)).normalized() * r * 0.92, 0.006 * s, 4, 3, "rust", smooth=False)

    # ---- the ear-cups round the neck, never worn.
    ear_guards(ctx)
    if hq:
        with mb.bound_to("neck"):
            band = [_at(ctx, 0.15 * math.cos(a), 0.02 + 0.09 * math.sin(a), -0.21 + 0.05 * math.sin(a)) for a in [math.pi * k / 6 for k in range(7)]]
            mb.path(band, [0.009 * s] * 7, 3, "leather_dark")

    # ---- the wide sash, its powder horn painted with a laughing moon, and a canvas shot bag.
    with mb.bound_to("hips"):
        mb.loft([_body_ring(ctx, 0.235, 0.2, z, q["torso"]) for z in (0.84, 0.95)], "faction_c", smooth=False)
        horn = [Vector((-0.17 * w * s, -0.19 * g * s, 0.92 * s)), Vector((-0.08 * w * s, -0.22 * g * s, 0.86 * s)), Vector((0.03 * w * s, -0.22 * g * s, 0.84 * s))]
        mb.path(horn, [0.03 * s, 0.022 * s, 0.006 * s], 6 if hq else 3, "parchment")
        mb.sphere(horn[0], 0.032 * s, 6 if hq else 4, 3, "brass", smooth=False)
        if hq:
            moon = horn[0].lerp(horn[1], 0.5) + Vector((0, -0.025, 0)) * s
            mb.sphere(moon, (0.02 * s, 0.004 * s, 0.02 * s), 6, 3, "cloud", smooth=False)
            mb.box(tuple(moon + Vector((0, -0.004, -0.006)) * s), (0.016 * s, 0.002 * s, 0.004 * s), "eye_dark")
        bag = Vector((0.25 * w * s, -0.05 * s, 0.8 * s))
        mb.box(tuple(bag), (0.07 * s, 0.12 * s, 0.12 * s), "canvas_dark")
        mb.box(tuple(bag + Vector((0, 0, 0.05)) * s), (0.075 * s, 0.125 * s, 0.035 * s), "leather")

    # ---- striped sailcloth trousers into cuffed sea-boots.
    if hq:
        for side in ("L", "R"):
            hip, knee = (Vector(p) for p in ctx.joints[f"thigh.{side}"][:2])
            with mb.bound_to(f"thigh.{side}"):
                for t_ in (0.22, 0.48, 0.74):
                    r = (0.1 - 0.025 * t_) * s * g * hero.leg_bulk * 1.03
                    mb.tube(hip.lerp(knee, t_ - 0.04), hip.lerp(knee, t_ + 0.04), r, sides=8, color="faction_a")
    _boot_cuffs(ctx, "leather", flare=1.26)

    # ---- the head: a riot of copper curls under the knotted headscarf, and the laugh.
    hair = hero.hair
    hair_cap(ctx)
    with mb.bound_to("head"):
        curls = [(0.2, 0.05, 0.08), (-0.2, 0.05, 0.08), (0.21, 0.0, -0.05), (-0.21, 0.0, -0.05), (0.15, 0.15, 0.02), (-0.15, 0.15, 0.02),
                 (0.0, 0.21, 0.05), (0.08, 0.2, -0.08), (-0.08, 0.2, -0.08), (0.17, 0.1, 0.2), (-0.17, 0.1, 0.2), (0.0, 0.08, 0.28), (0.1, 0.0, 0.26), (-0.1, 0.0, 0.26)]
        for k, (x, y, z) in enumerate(curls if hq else curls[:2] + curls[6:7] + curls[9:12]):
            mb.sphere(_at(ctx, x, y, z), (0.07 + 0.012 * (k % 3)) * s, 6 if hq else 5, 3, hair, smooth=hq)
        # The knotted green-and-gold headscarf across the crown.
        n = 14 if hq else 6
        rings = []
        for z, pad in ((0.12, 0.03), (0.2, 0.025)):
            ring = []
            for j in range(n):
                a = 2 * math.pi * (j + 0.5) / n
                ca, sa = math.cos(a), math.sin(a)
                cap = 0.04 * sa + math.sqrt(max(0.0, 0.208 ** 2 - (z - 0.06) ** 2 - (0.04 * ca) ** 2))
                skull = 0.2 * math.sqrt(max(0.0, 1 - (z / 0.22) ** 2))
                r = max(cap, skull) + pad
                ring.append(_at(ctx, r * ca, r * sa, z))
            rings.append(ring)
        mb.loft(rings, "cloth_green", smooth=False, caps=(False, False))
        if hq:
            mb.path(rings[0] + rings[0][:1], [0.005 * s] * (n + 1), 3, "gold")
        knot = _at(ctx, 0.0, 0.24, 0.16)
        mb.sphere(knot, 0.035 * s, 6 if hq else 4, 3, "cloth_green", smooth=False)
        for dx in ((-0.05, 0.06) if hq else (0.03,)):
            mb.plate([knot, knot + Vector((dx, 0.06, -0.08)) * s, knot + Vector((dx * 0.5, 0.04, -0.12)) * s], 0.01 * s, "cloth_green")
        if hq:
            # Eyes crinkled almost shut with laughing.
            for sign in (1, -1):
                mb.sphere(_at(ctx, sign * 0.078, -0.178, 0.05), (0.052 * s, 0.018 * s, 0.022 * s), 8, 3, hero.skin, smooth=False)
                mb.sphere(_at(ctx, sign * 0.078, -0.178, 0.003), (0.048 * s, 0.016 * s, 0.014 * s), 8, 3, hero.skin, smooth=False)
            # The huge open laugh, showing every tooth.
            mb.box(tuple(_at(ctx, 0, -0.174, -0.115)), (0.11 * s, 0.02 * s, 0.06 * s), "eye_dark")
            for dz in (0.022, -0.022):
                mb.box(tuple(_at(ctx, 0, -0.186, -0.115 + dz)), (0.09 * s, 0.008 * s, 0.014 * s), "enamel")
            for sign in (1, -1):
                mb.tube(_at(ctx, sign * 0.054, -0.178, -0.1), _at(ctx, sign * 0.078, -0.168, -0.072), 0.006 * s, sides=3, color="eye_dark")
            # Black powder dusted across the nose and cheeks like soot-coloured blush, and freckles under it.
            for x, z, rx, rz in ((0.0, -0.03, 0.05, 0.02), (0.11, -0.04, 0.04, 0.022), (-0.11, -0.04, 0.04, 0.022)):
                mb.sphere(_on_skull(ctx, x, z, -0.001), (rx * s, 0.005 * s, rz * s), 6, 3, "rock_dark", smooth=False)
            for x, z in ((0.07, -0.07), (0.14, -0.07), (-0.07, -0.07), (-0.14, -0.07), (0.04, -0.06), (-0.04, -0.06)):
                mb.sphere(_on_skull(ctx, x, z, 0.003), 0.005 * s, 4, 3, "rust", smooth=False)
        else:
            mb.box(tuple(_at(ctx, 0, -0.165, -0.11)), (0.1 * s, 0.04 * s, 0.05 * s), "eye_dark")



def core_keeper(ctx):
    """Odessa, the weary keeper of the Lift-Core and the Gale's surgeon: middle-aged, solid and soft-framed, the
    most tired face in the sky. Warm brown skin lined round the eyes, heavy drooping lids and deep bags over
    steady brown eyes, a mouth set in a flat line, grey hair wound into a tight bun skewered with two steel probes,
    and a polished head-mirror on a leather band across the brow. A long slate-grey surgeon's coat buttoned to the
    throat, its oversized pockets bulging with bandage rolls, under a heavy quilted vest with insulated,
    scorch-marked shoulder pads. A belt of glass-fronted pressure gauges, a ring of brass valve-keys and a
    stethoscope with a flared brass bell at the hip; thick woollen trousers and padded engine-room boots."""
    mb, q, s, g, w, hq = ctx.mb, ctx.q, ctx.s, ctx.g, ctx.w, ctx.hq
    hero = ctx.hero
    coat = "storm"

    # ---- the surgeon's coat, buttoned to the throat, pockets bulging with bandage rolls.
    long_coat(ctx, coat, coat, tail_len=0.42)
    with mb.bound_to("chest"):
        mb.lathe([(0.11 * s, 1.34 * s), (0.105 * s, 1.43 * s)], 8 if hq else 5, coat, smooth=False, caps=(False, False))
        for z in ((1.32, 1.24, 1.16, 1.08) if hq else (1.2,)):
            mb.sphere((0, _surface_y(ctx, _COAT_FRONT, 0, z * s) - 0.004 * s, z * s), 0.012 * s, 4, 3, "iron", smooth=False)
    with mb.bound_to("spine"):
        for sign in (1, -1):
            x, z = sign * 0.15 * w * s, 0.99 * s
            y = _surface_y(ctx, _COAT_FRONT, x, z)
            mb.box((x, y - 0.02 * s, z), (0.12 * s, 0.04 * s, 0.11 * s), coat)
            mb.tube((x - 0.03 * s, y - 0.025 * s, z + 0.05 * s), (x - 0.03 * s, y - 0.025 * s, z + 0.1 * s), 0.022 * s, sides=6 if hq else 4, color="cloth_white")
            if hq:
                mb.tube((x + 0.025 * s, y - 0.025 * s, z + 0.05 * s), (x + 0.025 * s, y - 0.025 * s, z + 0.085 * s), 0.018 * s, sides=6, color="canvas")

    # ---- the heavy quilted vest over it, open at the front, insulated shoulder pads scorched by the core.
    vest = [(0.262, 0.188, 1.07), (0.33, 0.198, 1.28), (0.17, 0.125, 1.37)]
    with mb.bound_to("chest"):
        mb.loft(_open_shell(ctx, vest, 26), "canvas_dark", smooth=False)
        if hq:
            for z in (1.12, 1.19, 1.26):
                for sign in (1, -1):
                    pts = []
                    for k in range(4):
                        a = math.radians(270 + sign * (30 + 22 * k))
                        pts.append(Vector((0.3 * w * s * math.cos(a), 0.195 * g * s * math.sin(a) - 0.004 * s, z * s)))
                    mb.path(pts, [0.004 * s] * 4, 3, "rope")
        for sign in (1, -1):
            pad = Vector((sign * 0.27 * w * s, 0.0, 1.33 * s))
            mb.sphere(pad, (0.13 * s, 0.15 * g * s, 0.06 * s), 8 if hq else 4, 3, "leather", smooth=False)
            if hq:
                mb.sphere(pad + Vector((sign * 0.02, -0.05, 0.045)) * s, (0.045 * s, 0.04 * s, 0.012 * s), 5, 3, "rock_dark", smooth=False)
    with mb.bound_to("spine"):
        mb.loft(_open_shell(ctx, [(0.235, 0.178, 0.94), (0.262, 0.188, 1.09)], 22), "canvas_dark", smooth=False)

    # ---- the belt: glass-fronted pressure gauges, a ring of brass valve-keys, the stethoscope.
    with mb.bound_to("hips"):
        belt_r = 0.205 * w * s * 1.03
        for a, big in ((-115, True), (-75, False), (-60, True)) if hq else ((-110, True),):
            ra = math.radians(a)
            at = Vector((belt_r * math.cos(ra), belt_r * math.sin(ra), 0.9 * s)) * 1.04
            out = Vector((math.cos(ra), math.sin(ra), 0))
            r = (0.035 if big else 0.026) * s
            mb.tube(at, at + out * 0.025 * s, r, sides=8 if hq else 5, color="brass")
            mb.tube(at + out * 0.025 * s, at + out * 0.028 * s, r * 0.82, sides=8 if hq else 5, color="cloud")
            if hq:
                mb.tube(at + out * 0.029 * s, at + out * 0.029 * s + Vector((0.01, 0, 0.015)) * s, 0.002 * s, sides=3, color="eye_dark")
        ring = Vector((0.21 * w * s, -0.1 * g * s, 0.8 * s))
        loop = [ring + Vector((0.035 * math.cos(a), -0.004, 0.035 * math.sin(a))) * s for a in [2 * math.pi * k / 6 for k in range(7)]]
        mb.path(loop, [0.006 * s] * 7, 3, "brass")
        for k in range(3 if hq else 1):
            top = ring + Vector((-0.02 + 0.02 * k, -0.01, -0.03)) * s
            mb.tube(top, top + Vector((0.005 * (k - 1), 0, -0.1)) * s, 0.006 * s, sides=3, color="brass")
            if hq:
                # Staggered, so neighbouring handles never share an end cap.
                mb.tube(top + Vector((-0.015, 0, 0.005 - 0.012 * k)) * s, top + Vector((0.015, 0, 0.005 - 0.012 * k)) * s, 0.006 * s, sides=3, color="brass")
        # The stethoscope coiled at the right hip, its flared brass bell hanging.
        coil_c = Vector((-0.23 * w * s, -0.06 * s, 0.84 * s))
        coil = [coil_c + Vector((0.0, 0.05 * math.cos(a), 0.05 * math.sin(a))) * s for a in [2 * math.pi * k / 8 for k in range(9 if hq else 5)]]
        mb.path(coil, [0.007 * s] * len(coil), 3, "leather_dark")
        tail = [coil_c + Vector((0, -0.05, -0.02)) * s, coil_c + Vector((-0.01, -0.07, -0.12)) * s]
        mb.path(tail, [0.006 * s] * 2, 3, "leather_dark")
        with mb.xf(Matrix.Translation(tail[-1]) @ Matrix.Rotation(math.pi, 4, "X")):
            mb.lathe([(0.008 * s, 0.0), (0.03 * s, 0.04 * s)], 8 if hq else 5, "brass", smooth=False)

    # ---- thick woollen trousers into padded engine-room boots.
    _boot_cuffs(ctx, "canvas_dark", flare=1.32)

    # ---- the head: tired eyes, a flat mouth, the head-mirror, the bun skewered with steel probes.
    hair_cap(ctx)
    with mb.bound_to("head"):
        bun = _at(ctx, 0, 0.17, 0.12)
        mb.sphere(bun, (0.1 * s, 0.09 * s, 0.09 * s), 8 if hq else 5, 4 if hq else 3, hero.hair, smooth=hq)
        for sign in (1, -1):
            mb.tube(bun + Vector((sign * 0.14, -0.04, -0.05)) * s, bun + Vector((-sign * 0.1, 0.05, 0.07)) * s, 0.005 * s, sides=3, color="silver")
        # The head-mirror on its leather band.
        with mb.xf(Matrix.Translation(_at(ctx, 0, 0, 0))):
            mb.lathe([(0.19 * s, 0.1 * s), (0.17 * s, 0.14 * s)], q["head_s"], "leather_dark", smooth=False, caps=(False, False))
        mirror = _at(ctx, 0.0, -0.215, 0.145)
        with mb.xf(Matrix.Translation(mirror) @ Matrix.Rotation(math.radians(70), 4, "X")):
            mb.lathe([(0.055 * s, -0.006 * s), (0.055 * s, 0.006 * s)], 10 if hq else 6, "silver", smooth=False)
        if hq:
            mb.sphere(mirror + Vector((0, -0.008, -0.002)) * s, 0.008 * s, 4, 3, "eye_dark", smooth=False)
            for sign in (1, -1):
                # Heavy, drooping lids and deep bags.
                mb.sphere(_at(ctx, sign * 0.078, -0.176, 0.042), (0.05 * s, 0.018 * s, 0.02 * s), 8, 3, hero.skin, smooth=False)
                mb.sphere(_on_skull(ctx, sign * 0.08, -0.015, -0.002), (0.04 * s, 0.006 * s, 0.014 * s), 6, 3, "wood_dark", smooth=False)
                for k in range(2):
                    mb.tube(_on_skull(ctx, sign * 0.13, 0.04 - 0.03 * k), _on_skull(ctx, sign * 0.16, 0.05 - 0.04 * k), 0.003 * s, sides=3, color="wood_dark")
            # The mouth set in a flat line of infinite patience.
            mb.path([_on_skull(ctx, -0.045, -0.108), _on_skull(ctx, 0.045, -0.108)], [0.004 * s] * 2, 3, "eye_dark")



def old_helmsman(ctx):
    """Tobin, the old helmsman who doesn't trust luck: tall, rangy and weathered, a kind face etched with worry lines
    and crow's feet, brows knotted in mild suspicion of good weather, gentle grey-blue eyes, and a magnificent
    drooping grey walrus moustache hiding the mouth. A battered, wide-brimmed oilskin storm-hat tied under the chin,
    its brim weighed with fishing-weight beads. A long, salt-stained navy greatcoat with a turned-up storm collar and
    patched elbows over a thick cream cable-knit sweater, a knitted scarf wrapped twice round the neck, a brass
    barometer on a chain, a canvas satchel stuffed with folded wind charts, heavy wool trousers and worn sea-boots,
    and a battered spyglass tucked under the left arm."""
    import copy
    mb, q, s, g, w, hq = ctx.mb, ctx.q, ctx.s, ctx.g, ctx.w, ctx.hq
    hero = ctx.hero
    coat, scarf = "navy", "hair_red"

    # ---- the greatcoat, open over the cable-knit sweater (centred: the helper's opening sits off to one side).
    long_coat(ctx, coat, hero.top, tail_len=0.32)
    for bone, rows in (("chest", [(0.25, 0.175, 1.06), (0.315, 0.185, 1.28), (0.15, 0.11, 1.38)]), ("spine", [(0.22, 0.165, 0.9), (0.252, 0.176, 1.08)])):
        with mb.bound_to(bone):
            mb.loft(_front_shell(ctx, [(rx + 0.006, ry + 0.006, z, 50) for rx, ry, z in rows], wall=0.01), coat, smooth=False)
            mb.loft(_front_shell(ctx, [(rx + 0.012, ry + 0.012, z, 24) for rx, ry, z in rows], wall=0.01), hero.top, smooth=False)
    with mb.bound_to("chest"):
        if hq:
            # Cables knitted down the sweater.
            for x in (-0.04, 0.04):
                pts = [Vector((x * s + 0.012 * s * math.sin(k * 1.6), _surface_y(ctx, _COAT_FRONT, x * s, z * s) - 0.016 * s, z * s)) for k, z in enumerate((1.3, 1.22, 1.14, 1.06, 0.98))]
                mb.path(pts, [0.008 * s] * 5, 3, "canvas_dark")
            # Salt stains on the coat.
            for x, z in ((0.24, 1.15), (-0.26, 1.02), (0.2, 0.96)):
                xs = x * w * s
                mb.sphere((xs, _surface_y(ctx, _COAT_FRONT, xs, z * s) - 0.004 * s, z * s), (0.04 * s, 0.004 * s, 0.025 * s), 6, 3, "canvas", smooth=False)
    # The turned-up storm collar.
    flat = copy.copy(ctx)
    flat.w = flat.g = 1.0
    with mb.bound_to("neck"):
        mb.loft(_open_shell(flat, [(0.12, 0.12, 1.33), (0.19, 0.19, 1.44)], 42, wall=0.014), coat, smooth=False)
    # The knitted scarf, wrapped twice round the neck, one end hanging down the chest.
    with mb.bound_to("neck"):
        for z, r in ((1.36, 0.1), (1.42, 0.095)):
            mb.lathe([(r * s, (z - 0.03) * s), ((r + 0.012) * s, z * s), (r * s, (z + 0.03) * s)], 10 if hq else 6, scarf, smooth=hq, caps=(False, False))
    with mb.bound_to("chest"):
        end = [Vector((0.06 * s, -0.1 * s, 1.35 * s)), Vector((0.08 * s, _surface_y(ctx, _COAT_FRONT, 0.08 * s, 1.2 * s) - 0.03 * s, 1.2 * s)), Vector((0.07 * s, _surface_y(ctx, _COAT_FRONT, 0.07 * s, 1.06 * s) - 0.03 * s, 1.04 * s))]
        mb.path(end, [0.035 * s, 0.032 * s, 0.03 * s], 4 if hq else 3, scarf)
        # A small brass barometer on a chain, its needle on "Change".
        dial = Vector((-0.16 * w * s, _surface_y(ctx, _COAT_FRONT, -0.16 * w * s, 1.1 * s) - 0.02 * s, 1.1 * s))
        mb.path([dial + Vector((0.02, 0.008, 0.1)) * s, dial + Vector((0, 0, 0.04)) * s], [0.003 * s] * 2, 3, "gold_dark")
        with mb.xf(Matrix.Translation(dial) @ Matrix.Rotation(math.pi / 2, 4, "X")):
            mb.lathe([(0.04 * s, -0.01 * s), (0.04 * s, 0.01 * s)], 8 if hq else 5, "brass", smooth=False)
        if hq:
            mb.box(tuple(dial + Vector((0, -0.011, 0)) * s), (0.055 * s, 0.003 * s, 0.055 * s), "parchment")
            mb.box(tuple(dial + Vector((0.006, -0.014, 0.004)) * s), (0.004 * s, 0.002 * s, 0.03 * s), "eye_dark")
        # The battered spyglass tucked under the left arm.
        glass = [Vector((0.33 * w * s, -0.14 * s, 1.1 * s)), Vector((0.31 * w * s, 0.2 * s, 1.16 * s))]
        mb.tube(glass[0], glass[1], 0.026 * s, 0.03 * s, sides=8 if hq else 4, color="brass")
        if hq:
            mb.tube(glass[0].lerp(glass[1], 0.45), glass[0].lerp(glass[1], 0.65), 0.033 * s, sides=8, color="leather")

    # ---- patched elbows.
    for side, sign in (("L", 1), ("R", -1)):
        shoulder, elbow = (Vector(p) for p in ctx.joints[f"upper_arm.{side}"][:2])
        r = 0.062 * s * g * hero.arm_bulk
        with mb.bound_to(f"upper_arm.{side}"):
            mb.sphere(elbow + Vector((0, 0.04, 0.02)) * s, (0.055 * s, r * 0.5, 0.05 * s), 6 if hq else 4, 3, "cloth_brown", smooth=False)

    # ---- the canvas satchel on the right hip, stuffed with folded wind charts.
    with mb.bound_to("hips"):
        bag = Vector((-0.27 * w * s, -0.04 * s, 0.8 * s))
        mb.box(tuple(bag), (0.08 * s, 0.17 * s, 0.14 * s), "canvas_dark")
        for k, (dy, dz) in enumerate(((-0.03, 0.08), (0.02, 0.09), (0.05, 0.075)) if hq else ((0.0, 0.08),)):
            mb.box(tuple(bag + Vector((0.0, dy, dz)) * s), (0.05 * s, 0.07 * s, 0.04 * s), "parchment")
    with mb.bound_to("chest"):
        mb.tube((0.24 * w * s, -0.14 * g * s, 1.34 * s), (-0.25 * w * s, -0.19 * g * s, 0.98 * s), 0.014 * s, sides=4, color="leather_dark", flat=1.5)

    # ---- worn sea-boots.
    _boot_cuffs(ctx, "leather", flare=1.15)

    # ---- the head: the walrus moustache, worry lines, crow's feet, and the storm-hat tied under the chin.
    hair = hero.hair
    hair_cap(ctx)
    with mb.bound_to("head"):
        for sign in (1, -1):
            mb.path([_at(ctx, sign * 0.01, -0.22, -0.065), _at(ctx, sign * 0.06, -0.205, -0.09), _at(ctx, sign * 0.085, -0.19, -0.14), _at(ctx, sign * 0.09, -0.175, -0.18)], [0.024 * s, 0.03 * s, 0.022 * s, 0.006 * s], 5 if hq else 3, hair, smooth=hq)
        mb.box(tuple(_at(ctx, 0, -0.205, -0.085)), (0.06 * s, 0.03 * s, 0.03 * s), hair)
        if hq:
            for z in (0.09, 0.115):
                mb.path([_on_skull(ctx, x, z) for x in (-0.07, 0.0, 0.07)], [0.003 * s] * 3, 3, "skin_dark")
            for sign in (1, -1):
                for k in range(2):
                    mb.tube(_on_skull(ctx, sign * 0.125, 0.04 - 0.025 * k), _on_skull(ctx, sign * 0.155, 0.05 - 0.04 * k), 0.003 * s, sides=3, color="skin_dark")
        # The storm-hat: a domed crown and a wide, drooping brim weighed with fishing-weight beads.
        with mb.xf(Matrix.Translation(_at(ctx, 0, 0.02, 0.12))):
            mb.lathe([(0.37 * s, -0.08 * s), (0.3 * s, -0.035 * s), (0.22 * s, 0.0), (0.215 * s, 0.1 * s), (0.15 * s, 0.17 * s), (0.04 * s, 0.19 * s)], q["head_s"], "steel", smooth=hq)
            if hq:
                for k in range(8):
                    a = 2 * math.pi * (k + 0.5) / 8
                    mb.sphere((0.36 * s * math.cos(a), 0.36 * s * math.sin(a), -0.09 * s), 0.012 * s, 4, 3, "iron_light", smooth=False)
        # The cord tied under the chin.
        for sign in (1, -1):
            mb.path([_at(ctx, sign * 0.2, 0.0, 0.1), _at(ctx, sign * 0.19, -0.06, -0.1), _at(ctx, sign * 0.06, -0.12, -0.23)], [0.005 * s] * 3, 3, "rope")


FEATURES = {f.__name__: f for f in (
    old_helmsman, core_keeper, gale_gunner, free_fleet_flyer, sky_duelist, syndicate_lord, scrap_captain, vane_deckhand, vane_captain, vane_king, ship_surgeon, master_gunner, stormcaller_trainee, big_guns, bosun_build, morrow_finery, nomad_layers, nomad_hair, nomad_scarf, assassin_gear, sorcerer_amulet, sorcerer_hood, sorcerer_robe, sorcerer_sleeves, hair_cap, hair_wild, hair_long, hair_braid, hair_ponytail, hair_slick, hair_side_shave, hair_gray_sides,
    beard_full, goatee, moustache, eyepatch, scar, spectacles, goggles_up, face_mask, hood, bandana, tricorn,
    bicorne, shako, morion, warden_helm, hat_officer, long_coat, short_jacket, cuirass, pauldrons, epaulettes,
    cape, sash, cross_belt, bandolier, apron, tool_belt, tabard, keyring, medals, gold_buttons, high_collar,
    scarf, grapple_gauntlet, iron_arm, chain_wrap, dagger_sheaths, navigator_case, tool_harness, ear_guards,
    torn_shoulder,
)}


CAST = {
    # The hero, kept neutral so any player sees themselves. Warm and scrappy, the only big red accent
    # in the crew so they are always findable in a busy deck brawl.
    # The player, from the newVane reference: golden-brown hair, hazel-green eyes, a crooked half-smile and the
    # only red bandana in the sky. One body, three acts of clothes (see vane_deckhand, vane_captain, vane_king).
    "Vane": Hero(mouth=False, skin="skin_mid", hair="wood_mid", brow_color="hair_brown", iris="toxic_dark", top="cloth_white", legs="cloth_black", boots="leather", belt="leather", sleeve="cloth_white", forearm="skin_mid", width=0.96, girth=0.88, arm_bulk=0.95, leg_bulk=1.12, features=[
        ("vane_deckhand",),
    ]),
    "VaneCaptain": Hero(mouth=False, skin="skin_mid", hair="wood_mid", brow_color="hair_brown", iris="toxic_dark", top="cloth_black", legs="rock_dark", boots="leather_dark", belt="leather_dark", sleeve="navy", forearm="navy", glove="leather_dark", width=0.96, girth=0.88, arm_bulk=0.95, features=[
        ("vane_captain",),
    ]),
    "VaneKing": Hero(mouth=False, skin="skin_mid", hair="wood_mid", brow_color="hair_brown", iris="toxic_dark", top="leather_dark", legs="cloth_black", boots="leather_dark", belt="leather_dark", sleeve="cloth_black", forearm="cloth_black", glove="leather_dark", width=0.96, girth=0.88, arm_bulk=0.95, features=[
        ("vane_king",),
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
    "Lyra": Hero(skin="skin_mid", hair="hair_brown", top="canvas", legs="faction_a", boots="leather", belt="leather", sleeve="canvas", forearm="skin_mid", width=0.86, girth=0.82, iris="eye_dark", features=[
        ("nomad_hair",), ("nomad_layers",), ("nomad_scarf",),
    ]),
    "Sable": Hero(mouth=False, skin="skin_light", hair="hair_black", top="faction_a", legs="cloth_black", boots="cloth_black", belt="leather", sleeve="faction_a", forearm="faction_a", glove="cloth_black", scale=0.97, width=0.76, girth=0.8, arm_bulk=0.82, leg_bulk=0.88, brow=0, iris="silver", features=[
        ("sorcerer_hood", "cloth_black", "faction_a"), ("assassin_gear",),
    ]),
    "Brill": Hero(mouth=False, skin="skin_light", hair="hair_gray", top="faction_b", legs="cloth_black", boots="leather_dark", belt="leather", sleeve="faction_a", forearm="skin_light", scale=0.95, width=1.3, girth=1.38, arm_bulk=1.25, leg_bulk=1.25, brow=1, iris="eye_dark", features=[
        ("hair_cap",), ("bosun_build",),
    ]),
    # The jittery trainee stormcaller: small, wiry, all eyes and frizz, buried in a coat cut for someone
    # twice his size and hung with gear that sparks.
    "Ivo": Hero(mouth=False, skin="skin_light", hair="hair_black", top="canvas", legs="cloth_black", boots="leather_dark", belt="leather", sleeve="storm", forearm="storm", glove="leather_dark", scale=0.92, width=0.82, girth=0.78, arm_bulk=0.85, leg_bulk=1.12, brow=-1, iris="wind", eye_scale=1.45, singed_brow=-1, features=[
        ("stormcaller_trainee",),
    ]),
    # The pressed master gunner: broad, heavily muscled and still as a loaded gun. Shaved and tattooed with a
    # tally of days or ships, one eye milky and blind, the other locked on you.
    "Hask": Hero(mouth=False, skin="skin_mid", hair="rock_dark", top="canvas", legs="cloth_black", boots="leather_dark", belt="leather_dark", sleeve="skin_mid", forearm="skin_mid", scale=1.06, width=1.22, girth=1.12, arm_bulk=1.35, leg_bulk=1.12, brow=2, iris="steel", blind_eye=1, features=[
        ("master_gunner",),
    ]),
    # The gaunt ship's surgeon: tall, skeletal and pallid, a shaved skull, a sutured smile, one milky eye and
    # one that examines you like a specimen.
    "Wren": Hero(mouth=False, skin="skin_light", hair="hair_black", top="cloth_white", legs="cloth_black", boots="leather_dark", belt="leather", sleeve="cloth_white", forearm="skin_light", scale=1.1, width=0.86, girth=0.76, arm_bulk=0.72, leg_bulk=0.85, brow=0, iris="eye_dark", blind_eye=1, features=[
        ("ship_surgeon",),
    ]),
    # The bellowing Scrap-brig rival: a barrel of bravado on short legs, mutton chops, a gold tooth and a hat
    # far too big for him, already leaning towards the exit.
    "Gorse": Hero(mouth=False, skin="skin_mid", hair="hair_red", iris="amber", top="velvet", legs="cloth_brown", boots="leather_dark", belt="leather", sleeve="canvas_dark", forearm="canvas_dark", scale=0.95, width=1.22, girth=1.3, arm_bulk=1.1, leg_bulk=1.15, brow=-1, features=[
        ("scrap_captain",),
    ]),
    # The pinched Syndicate toll-lord: tall, brittle-thin and powdered white, monocled, already eyeing the exit.
    "Ashgrave": Hero(mouth=False, skin="enamel", hair="hair_gray", brow_color="hair_black", iris="faction_a", top="cloth_white", legs="faction_c", boots="cloth_white", belt="faction_c", sleeve="faction_a", forearm="faction_a", glove="enamel", scale=1.1, width=0.8, girth=0.74, arm_bulk=0.7, leg_bulk=0.8, brow=-1, features=[
        ("syndicate_lord",),
    ]),
    # The untouchable sky-lounge duelist: statuesque and heavy-lidded, chin up, wine-dark coiffure towering.
    "Thrace": Hero(mouth=False, skin="skin_light", hair="velvet", iris="grass", top="silver", legs="cloth_black", boots="cloth_black", belt="cloth_black", sleeve="velvet", forearm="cloth_black", glove="cloth_black", scale=1.06, width=0.88, girth=0.8, arm_bulk=0.8, leg_bulk=0.92, features=[
        ("sky_duelist",),
    ]),
    # The joyful free-fleet wingmate: compact and quick, all grin, goggles up and patched twice over.
    "Ria": Hero(mouth=False, skin="skin_mid", hair="hair_black", iris="amber", top="hair_red", legs="canvas_dark", boots="leather_dark", belt="leather", sleeve="hair_red", forearm="skin_mid", glove="leather_dark", scale=0.94, width=0.92, girth=0.86, arm_bulk=0.9, leg_bulk=0.95, features=[
        ("free_fleet_flyer",),
    ]),
    # The laughing master gunner of the old crew: stocky and broad-hipped, a riot of copper curls, mid-laugh.
    "Mirren": Hero(mouth=False, skin="skin_light", hair="hair_red", iris="grass", top="cloth_white", legs="canvas", boots="leather_dark", belt="faction_c", sleeve="cloth_white", forearm="skin_light", scale=0.98, width=1.1, girth=1.12, arm_bulk=1.2, leg_bulk=1.2, features=[
        ("gale_gunner",),
    ]),
    # The weary keeper of the Lift-Core: solid and soft-framed, heavy-lidded, buttoned to the throat.
    "Odessa": Hero(mouth=False, skin="skin_dark", hair="hair_gray", brow_color="hair_gray", iris="leather", top="storm", legs="cloth_brown", boots="leather_dark", belt="leather_dark", sleeve="storm", forearm="storm", scale=1.0, width=1.12, girth=1.14, arm_bulk=1.05, leg_bulk=1.15, brow=-1, features=[
        ("core_keeper",),
    ]),
    # The old helmsman who doesn't trust luck: tall and rangy, a walrus moustache under a storm-hat.
    "Tobin": Hero(mouth=False, skin="skin_mid", hair="hair_gray", iris="steel", top="canvas", legs="rock_dark", boots="leather_dark", belt="leather", sleeve="navy", forearm="navy", scale=1.08, width=0.95, girth=0.9, arm_bulk=0.9, leg_bulk=0.95, brow=-1, features=[
        ("old_helmsman",),
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
                    color = "cloud" if ctx.hero.blind_eye == sign else ctx.hero.iris
                    ctx.mb.box(tuple(_at(ctx, sign * 0.078, -0.16, 0.03)), (0.056 * ctx.s, 0.06 * ctx.s, 0.05 * ctx.s), color)
        return
    s = ctx.s
    hero = ctx.hero
    tilt = hero.brow * 0.012
    brow_color = hero.brow_color or ("hair_gray" if hero.hair == "hair_white" else hero.hair)
    e = hero.eye_scale
    with ctx.mb.bound_to("head"):
        for sign in (1, -1):
            x = sign * 0.078
            ctx.mb.sphere(_at(ctx, x, -0.172, 0.03), (0.044 * s * e, 0.016 * s, 0.027 * s * e), 8, 4, hero.sclera)
            # Pupils sit slightly inward, so the character looks at the viewer instead of through them.
            blind = hero.blind_eye == sign
            # A blind eye is a milky film over the whole iris, staring dead ahead.
            ctx.mb.sphere(_at(ctx, x - sign * 0.006 * (not blind), -0.183, 0.03), (0.019 * s * e, 0.008 * s, 0.024 * s * e), 8, 3, "cloud" if blind else hero.iris or "eye_dark")
            if e > 1.0 and not blind:
                ctx.mb.sphere(_at(ctx, x - sign * 0.006, -0.19, 0.03), (0.009 * s * e, 0.004 * s, 0.011 * s * e), 6, 3, "eye_dark")
            lid = 0.05 + 0.027 * (e - 1.0)
            ctx.mb.tube(_at(ctx, x - 0.046 * e, -0.185, lid), _at(ctx, x + 0.046 * e, -0.182, lid), 0.007 * s, sides=4, color="eye_dark", flat=1.6)
            brow_z = 0.09 + 0.03 * (e - 1.0)
            inner, outer = sign * 0.03, sign * 0.125
            if hero.singed_brow == sign:
                outer = sign * 0.075  # Burnt short at the outer end.
            ctx.mb.tube(_at(ctx, inner, -0.192, brow_z - tilt), _at(ctx, outer, -0.166 - 0.012 * (abs(outer) < 0.1), brow_z + tilt), 0.012 * s, sides=4, color=brow_color, flat=1.6)
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
