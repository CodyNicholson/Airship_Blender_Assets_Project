"""Cinder, Rook's robot hound: a four-legged skeleton of its own, and its own three clips.

Faces Blender -Y like the crew. Parts are rigid-bound to one bone each, as the crew are. Clip poses use the
same convention: rotations in degrees about the armature's rest axes. -X swings a hanging leg forward,
and on a bone pointing forward, -X raises it and +X lowers it.

The muzzle bone carries no skin. It's there so the game can find the barrel's tip at any moment of a clip.
"""
from mathutils import Vector

ASSET = "SK_Cinder"

BONE_PARENTS = {
    "root": None,
    "hips": "root",
    "chest": "hips",
    "neck": "chest",
    "head": "neck",
    "jaw": "head",
    "muzzle": "head",
    "tail.1": "hips",
    "tail.2": "tail.1",
    "upper_leg.FL": "chest",
    "lower_leg.FL": "upper_leg.FL",
    "foot.FL": "lower_leg.FL",
    "upper_leg.FR": "chest",
    "lower_leg.FR": "upper_leg.FR",
    "foot.FR": "lower_leg.FR",
    "upper_leg.BL": "hips",
    "lower_leg.BL": "upper_leg.BL",
    "foot.BL": "lower_leg.BL",
    "upper_leg.BR": "hips",
    "lower_leg.BR": "upper_leg.BR",
    "foot.BR": "lower_leg.BR",
}

LEG_X = 0.15
FRONT_Y = -0.2
BACK_Y = 0.34
BARREL_Y = -1.0
BARREL_Z = 0.73


def _joints():
    joints = {
        "root": ((0, 0, 0), (0, 0, 0.15)),
        "hips": ((0, 0.42, 0.56), (0, 0.04, 0.58)),
        "chest": ((0, 0.04, 0.58), (0, -0.28, 0.6)),
        "neck": ((0, -0.28, 0.66), (0, -0.42, 0.8)),
        "head": ((0, -0.42, 0.8), (0, -0.68, 0.82)),
        "jaw": ((0, -0.48, 0.7), (0, -0.92, 0.64)),
        "muzzle": ((0, BARREL_Y - 0.01, BARREL_Z), (0, BARREL_Y - 0.11, BARREL_Z)),  # Its head is the barrel's tip.
        "tail.1": ((0, 0.44, 0.64), (0, 0.6, 0.76)),
        "tail.2": ((0, 0.6, 0.76), (0, 0.7, 0.98)),
    }
    for side, x in (("L", LEG_X), ("R", -LEG_X)):
        for end, y in (("F", FRONT_Y), ("B", BACK_Y)):
            key = end + side
            joints[f"upper_leg.{key}"] = ((x, y, 0.5), (x, y + 0.02, 0.28))
            joints[f"lower_leg.{key}"] = ((x, y + 0.02, 0.28), (x, y, 0.08))
            joints[f"foot.{key}"] = ((x, y, 0.08), (x, y - 0.1, 0.03))
    return joints


def build(mb, hq):
    joints = _joints()
    limb = 6 if hq else 4
    round_sides = 8 if hq else 5

    with mb.bound_to("chest"):
        mb.box((0, -0.1, 0.6), (0.4, 0.42, 0.36), "iron_light")
        mb.box((0, -0.1, 0.79), (0.26, 0.3, 0.05), "rust")
        if hq:
            for sign in (1, -1):
                mb.box((sign * 0.205, -0.1, 0.6), (0.015, 0.22, 0.1), "ember")
    with mb.bound_to("hips"):
        mb.box((0, 0.24, 0.58), (0.36, 0.42, 0.32), "iron_light")
        mb.box((0, 0.24, 0.75), (0.24, 0.3, 0.05), "rust")
    with mb.bound_to("neck"):
        mb.tube((0, -0.2, 0.62), (0, -0.46, 0.82), 0.1, 0.09, sides=limb, color="iron")
    for bone, p0, p1, r0, r1 in (("tail.1", (0, 0.42, 0.63), (0, 0.6, 0.76), 0.04, 0.03), ("tail.2", (0, 0.6, 0.76), (0, 0.7, 0.98), 0.03, 0.012)):
        with mb.bound_to(bone):
            mb.tube(p0, p1, r0, r1, sides=4, color="iron")

    with mb.bound_to("head"):
        mb.box((0, -0.5, 0.86), (0.32, 0.26, 0.24), "iron_light")
        for sign in (1, -1):
            # Ears like blades, and ember eyes set under a heavy brow.
            mb.plate([(sign * 0.09, -0.46, 0.96), (sign * 0.15, -0.46, 0.96), (sign * 0.18, -0.42, 1.16)], 0.03, "iron")
            mb.box((sign * 0.09, -0.635, 0.89), (0.06, 0.02, 0.045), "ember")
            mb.box((sign * 0.09, -0.635, 0.925), (0.09, 0.03, 0.025), "iron")
        # The upper jaw: a sharp steel wedge that comes to a point above the barrel, with a row of fangs.
        mb.plate([(-0.15, -0.6, 0.81), (0.15, -0.6, 0.81), (0.05, -0.9, 0.79), (0, -0.98, 0.78), (-0.05, -0.9, 0.79)], 0.05, "silver")
        fangs = ((0.12, -0.64), (0.09, -0.72), (0.06, -0.8), (0.035, -0.88)) if hq else ((0.11, -0.66), (0.06, -0.8))
        for x, y in fangs:
            for sign in (1, -1):
                mb.tube((sign * x, y, 0.79), (sign * x, y - 0.005, 0.71), 0.018, 0.002, sides=4, color="silver")
        # Steel cheeks run down past the jaw's hinge, so the jaw stays joined to the head when it opens.
        for sign in (1, -1):
            mb.box((sign * 0.14, -0.53, 0.69), (0.06, 0.2, 0.26), "iron")
        # The cannon: a brass barrel held in the mouth, with a dark bore and a glow at the back of it.
        mb.tube((0, -0.62, BARREL_Z), (0, -0.97, BARREL_Z), 0.062, 0.055, sides=round_sides, color="brass")
        mb.tube((0, -0.95, BARREL_Z), (0, BARREL_Y, BARREL_Z), 0.07, sides=round_sides, color="gold_dark")
        mb.tube((0, -0.995, BARREL_Z), (0, -1.004, BARREL_Z), 0.05, sides=round_sides, color="abyss")
        mb.tube((0, -1.004, BARREL_Z), (0, -1.008, BARREL_Z), 0.024, sides=round_sides, color="ember")
    with mb.bound_to("jaw"):
        # The lower jaw: thinner, hinged at the back, fangs pointing up past the barrel.
        mb.plate([(-0.13, -0.46, 0.68), (0.13, -0.46, 0.68), (0.045, -0.86, 0.63), (0, -0.94, 0.62), (-0.045, -0.86, 0.63)], 0.04, "silver")
        fangs = ((0.1, -0.62), (0.07, -0.72), (0.04, -0.82)) if hq else ((0.09, -0.64), (0.05, -0.78))
        for x, y in fangs:
            for sign in (1, -1):
                mb.tube((sign * x, y, 0.65), (sign * x, y - 0.005, 0.72), 0.016, 0.002, sides=4, color="silver")

    for side in ("L", "R"):
        for end in ("F", "B"):
            key = end + side
            upper, knee = (Vector(p) for p in joints[f"upper_leg.{key}"])
            _, ankle = (Vector(p) for p in joints[f"lower_leg.{key}"])
            with mb.bound_to(f"upper_leg.{key}"):
                mb.tube(upper + Vector((0, 0, 0.08)), knee, 0.08, 0.055, sides=limb, color="iron")
            with mb.bound_to(f"lower_leg.{key}"):
                mb.tube(knee, ankle, 0.05, 0.04, sides=limb, color="iron_light")
            with mb.bound_to(f"foot.{key}"):
                mb.box((ankle.x, ankle.y - 0.04, 0.045), (0.11, 0.2, 0.09), "iron")

    mb.socket("muzzle", (0, BARREL_Y - 0.01, BARREL_Z))
    mb.socket("head_top", (0, -0.5, 1.0))
    mb.socket("chest_centre", (0, -0.1, 0.6))
    return joints


def _stride(fl, fr, bl, br, lift=(0, 0, 0, 0), **extra):
    """Leg swing in degrees for front-left, front-right, back-left, back-right, and knee bend for each."""
    pose = {}
    for key, swing, bend in (("FL", fl, lift[0]), ("FR", fr, lift[1]), ("BL", bl, lift[2]), ("BR", br, lift[3])):
        pose[f"upper_leg.{key}"] = (swing, 0, 0)
        pose[f"lower_leg.{key}"] = (bend, 0, 0)
    for bone, value in extra.items():
        pose[bone.replace("__", ".").replace("_loc", "@")] = value
    return pose


# name: (loop, {frame: pose})
CLIPS = {
    "Idle": (True, {
        0: _stride(0, 0, 0, 0, tail__1=(0, 0, 14), head=(-2, 0, 0)),
        12: _stride(0, 0, 0, 0, tail__1=(0, 0, -14), chest=(1.5, 0, 0), jaw=(3, 0, 0)),
        24: _stride(0, 0, 0, 0, tail__1=(0, 0, 14), head=(-4, 0, 0)),
        36: _stride(0, 0, 0, 0, tail__1=(0, 0, -14), chest=(1.5, 0, 0), jaw=(3, 0, 0)),
        48: _stride(0, 0, 0, 0, tail__1=(0, 0, 14), head=(-2, 0, 0)),
    }),
    # A trot: diagonal pairs move together. Each knee folds as that leg swings through.
    "Walk": (True, {
        0: _stride(-26, 24, 24, -26, (4, 14, 14, 4), hips_loc=(0, 0, 0.018), tail__1=(0, 0, 10), head=(3, 0, 0)),
        6: _stride(-4, 0, 0, -4, (6, 48, 48, 6), hips_loc=(0, 0, 0.023), tail__1=(0, 0, 0), head=(-1, 0, 0)),
        12: _stride(24, -26, -26, 24, (14, 4, 4, 14), hips_loc=(0, 0, 0.018), tail__1=(0, 0, -10), head=(3, 0, 0)),
        18: _stride(0, -4, -4, 0, (48, 6, 6, 48), hips_loc=(0, 0, 0.023), tail__1=(0, 0, 0), head=(-1, 0, 0)),
        24: _stride(-26, 24, 24, -26, (4, 14, 14, 4), hips_loc=(0, 0, 0.018), tail__1=(0, 0, 10), head=(3, 0, 0)),
    }),
    # Rears its head back, then braces and opens its jaws wide around the barrel for the fire.
    "Fire": (False, {
        0: _stride(0, 0, 0, 0),
        8: _stride(-4, -4, 4, 4, head=(-20, 0, 0), jaw=(10, 0, 0), neck=(-8, 0, 0), hips_loc=(0, 0, 0.01)),
        12: _stride(-9, -9, 8, 8, head=(4, 0, 0), jaw=(30, 0, 0), neck=(4, 0, 0), hips_loc=(0, 0, 0.012), tail__1=(-30, 0, 0)),
        30: _stride(-9, -9, 8, 8, head=(7, 0, 0), jaw=(32, 0, 0), neck=(4, 0, 0), hips_loc=(0, 0, 0.012), tail__1=(-30, 0, 0)),
        40: _stride(0, 0, 0, 0),
    }),
}
