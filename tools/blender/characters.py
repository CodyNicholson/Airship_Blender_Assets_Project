"""Pirate crew: one 22-bone skeleton and one animation set shared by every character.

Characters face Blender -Y (glTF +Z). Their left side is +X. Parts are rigid-bound to a
single bone each and overlap at the joints, which suits the chunky style and costs the
least skinning on old GPUs.

weapon.R/L and gun.R/L carry no skin. Parent a held item's .glb root to one with no rotation
offset: in glTF a joint's +Y runs from bone head to tail, and an item's length is its +Y.
weapon.* aims the item forward from the fist (blades); gun.* aims it along the forearm (pistols).

Clip poses are written as rotations about the armature's rest axes, in degrees:
  +X leans an upright bone forward; a hanging arm or leg swings forward with -X.
  +Z turns the character towards its own left.
  An arm lifts away from the body with -Y on the left, +Y on the right.
"""
import math
from dataclasses import dataclass, field

import bpy
from mathutils import Euler, Matrix, Vector

FPS = 24

BONE_PARENTS = {
    "root": None,
    "hips": "root",
    "spine": "hips",
    "chest": "spine",
    "neck": "chest",
    "head": "neck",
    "upper_arm.L": "chest",
    "lower_arm.L": "upper_arm.L",
    "hand.L": "lower_arm.L",
    "weapon.L": "hand.L",
    "gun.L": "hand.L",
    "upper_arm.R": "chest",
    "lower_arm.R": "upper_arm.R",
    "hand.R": "lower_arm.R",
    "weapon.R": "hand.R",
    "gun.R": "hand.R",
    "thigh.L": "hips",
    "shin.L": "thigh.L",
    "foot.L": "shin.L",
    "thigh.R": "hips",
    "shin.R": "thigh.R",
    "foot.R": "shin.R",
}


def _joints(scale, width):
    """Bone (head, tail) in metres. width spreads shoulders and hips for bulky characters."""
    joints = {
        "root": ((0, 0, 0), (0, 0, 0.2)),
        "hips": ((0, 0, 0.8), (0, 0, 0.94)),
        "spine": ((0, 0, 0.94), (0, 0, 1.08)),
        "chest": ((0, 0, 1.08), (0, 0, 1.32)),
        "neck": ((0, 0, 1.32), (0, 0, 1.38)),
        "head": ((0, 0, 1.38), (0, 0, 1.8)),
    }
    for sign, side in ((1, "L"), (-1, "R")):
        s = (sign * 0.25 * width, 0, 1.28)
        e = (sign * 0.36 * width, 0.01, 1.02)
        w = (sign * 0.42 * width, -0.03, 0.8)
        t = (sign * 0.44 * width, -0.04, 0.7)
        h = (sign * 0.12 * width, 0, 0.8)
        k = (sign * 0.13 * width, -0.01, 0.44)
        a = (sign * 0.13 * width, 0.01, 0.12)
        f = (sign * 0.13 * width, -0.17, 0.05)
        joints[f"upper_arm.{side}"] = (s, e)
        joints[f"lower_arm.{side}"] = (e, w)
        joints[f"hand.{side}"] = (w, t)
        joints[f"thigh.{side}"] = (h, k)
        joints[f"shin.{side}"] = (k, a)
        joints[f"foot.{side}"] = (a, f)
    for side in ("L", "R"):
        palm = tuple((a + b) / 2 for a, b in zip(joints[f"hand.{side}"][0], joints[f"hand.{side}"][1]))
        hand_dir = [b - a for a, b in zip(joints[f"hand.{side}"][0], joints[f"hand.{side}"][1])]
        length = sum(d * d for d in hand_dir) ** 0.5
        joints[f"weapon.{side}"] = (palm, (palm[0], palm[1] - 0.12, palm[2]))
        joints[f"gun.{side}"] = (palm, tuple(p + d / length * 0.12 for p, d in zip(palm, hand_dir)))
    return {
        bone: (tuple(c * scale for c in head), tuple(c * scale for c in tail))
        for bone, (head, tail) in joints.items()
    }


@dataclass
class Look:
    scale: float = 1.0
    width: float = 1.0
    girth: float = 1.0
    skin: str = "skin_light"
    hair: str = "hair_brown"
    shirt: str = "cloth_white"
    trousers: str = "cloth_brown"
    boots: str = "leather_dark"
    belt: str = "leather"
    extras: list = field(default_factory=list)


LOOKS = {
    # Player avatar: long coat and tricorn in faction colours.
    "PirateCaptain": Look(skin="skin_light", hair="hair_black", shirt="cloth_white", trousers="cloth_black",
                          extras=["coat", "tricorn", "beard", "gold_trim"]),
    # Common melee enemy.
    "PirateDeckhand": Look(skin="skin_mid", hair="hair_brown", shirt="faction_b", trousers="cloth_blue",
                           extras=["bandana", "sash"]),
    # Ranged enemy.
    "PirateGunner": Look(skin="skin_dark", hair="hair_black", shirt="cloth_green", trousers="cloth_brown",
                         extras=["bandolier", "goggles", "skullcap"]),
    # Tank.
    "PirateBrute": Look(scale=1.14, width=1.32, girth=1.45, skin="skin_mid", hair="hair_red", shirt="leather",
                        trousers="cloth_black", extras=["pauldrons", "beard", "bald"]),
}


def _tiers(hq):
    return {
        "limb": 8 if hq else 4,
        "torso": 12 if hq else 6,
        "head_s": 12 if hq else 6,
        "head_r": 8 if hq else 4,
        "joint": 8 if hq else 0,
    }


def _limb(mb, joints, bone, r0, r1, color, q, extend=0.0):
    head, tail = (Vector(p) for p in joints[bone])
    direction = (tail - head).normalized()
    with mb.bound_to(bone):
        mb.tube(head - direction * extend, tail + direction * extend, r0, r1, sides=q["limb"], color=color, smooth=q["joint"] > 0)


def _torso(mb, joints, look, q):
    s, g = look.scale, look.girth
    wide = look.width
    sections = {
        "hips": [(0.2 * wide, 0.14 * g, 0.74), (0.21 * wide, 0.15 * g, 0.94)],
        "spine": [(0.2 * wide, 0.14 * g, 0.92), (0.24 * wide, 0.16 * g, 1.1)],
        "chest": [(0.235 * wide, 0.16 * g, 1.08), (0.3 * wide, 0.17 * g, 1.28), (0.14 * wide, 0.1 * g, 1.37)],
    }
    colours = {"hips": look.trousers, "spine": look.shirt, "chest": look.shirt}
    for bone, rows in sections.items():
        with mb.bound_to(bone):
            rings = []
            for rx, ry, z in rows:
                ring = []
                for j in range(q["torso"]):
                    a = 2 * math.pi * (j + 0.5) / q["torso"]
                    ring.append((rx * s * math.cos(a), ry * s * math.sin(a), z * s))
                rings.append(ring)
            mb.loft(rings, colours[bone], smooth=q["joint"] > 0)
    with mb.bound_to("hips"):
        mb.lathe([(0.205 * wide * s * 1.03, 0.87 * s), (0.205 * wide * s * 1.03, 0.94 * s)], q["torso"], look.belt, smooth=False)
        mb.box((0, -0.16 * g * s, 0.905 * s), (0.08 * s, 0.03, 0.06 * s), "brass")


def _head(mb, joints, look, q, hq, draw_face=True):
    """draw_face=False leaves eyes and nose to the caller, for characters with custom close-ups."""
    s = look.scale
    centre = Vector((0, 0, 1.56 * s))
    with mb.bound_to("neck"):
        mb.tube((0, 0, 1.3 * s), (0, 0, 1.42 * s), 0.08 * s, sides=q["limb"], color=look.skin, smooth=hq)
    with mb.bound_to("head"):
        mb.sphere(centre, (0.2 * s, 0.2 * s, 0.22 * s), q["head_s"], q["head_r"], look.skin, smooth=hq)
        eye_z = centre.z + 0.03 * s
        eye_y = centre.y - 0.178 * s
        for sign in (1, -1) if draw_face else ():
            x = sign * 0.075 * s
            if hq:
                mb.sphere((x, eye_y, eye_z), 0.035 * s, 6, 4, "eye_white")
                mb.sphere((x, eye_y - 0.022 * s, eye_z), 0.02 * s, 6, 3, "eye_dark")
            else:
                mb.box((x, eye_y - 0.01 * s, eye_z), (0.05 * s, 0.03 * s, 0.06 * s), "eye_dark")
        nose_y = centre.y - 0.2 * s
        if hq and draw_face:
            mb.sphere((0, nose_y, centre.z - 0.03 * s), (0.035 * s, 0.05 * s, 0.045 * s), 6, 3, look.skin)
        extras = look.extras
        if "bald" not in extras and "tricorn" not in extras and "bandana" not in extras and "skullcap" not in extras:
            mb.sphere(centre + Vector((0, 0.02, 0.05)) * s, 0.205 * s, q["head_s"], q["head_r"], look.hair, smooth=hq)
        if "tricorn" in extras:
            # Back and sides of the hair show under the hat brim; the front stays clear for the face.
            mb.sphere(centre + Vector((0, 0.05, -0.02)) * s, (0.195 * s, 0.185 * s, 0.21 * s), q["head_s"], q["head_r"], look.hair, smooth=hq)
        if "beard" in extras:
            beard = [(-0.13, -0.11, -0.08), (0.13, -0.11, -0.08), (0.1, -0.16, -0.24), (0, -0.19, -0.33), (-0.1, -0.16, -0.24)]
            mb.plate([centre + Vector(p) * s for p in beard], 0.07 * s, look.hair)
        if "tricorn" in extras:
            _tricorn(mb, centre, s, hq)
        if "bandana" in extras:
            mb.sphere(centre + Vector((0, 0.01, 0.06)) * s, (0.21 * s, 0.21 * s, 0.19 * s), q["head_s"], q["head_r"], "faction_a", smooth=hq)
            tail_y = centre.y + 0.22 * s
            mb.plate([(0, tail_y, centre.z + 0.05 * s), (0.08 * s, tail_y + 0.14 * s, centre.z - 0.13 * s), (-0.05 * s, tail_y + 0.1 * s, centre.z - 0.16 * s)], 0.025, "faction_a")
        if "skullcap" in extras:
            mb.sphere(centre + Vector((0, 0.01, 0.075)) * s, 0.205 * s, q["head_s"], q["head_r"], "leather", smooth=hq)
        if "goggles" in extras:
            z = centre.z + 0.09 * s
            for sign in (1, -1):
                with mb.xf(Matrix.Translation((sign * 0.075 * s, eye_y + 0.01, z)) @ Matrix.Rotation(math.pi / 2, 4, "X")):
                    mb.lathe([(0.052 * s, -0.025), (0.052 * s, 0.025)], 6 if hq else 4, "brass", smooth=False)


def _tricorn(mb, centre, s, hq):
    z = centre.z + 0.12 * s
    sides = 12 if hq else 6
    rings = []
    for scale_r, dz in ((0.92, -0.02), (0.92, 0.03)):
        ring = []
        for j in range(sides):
            a = 2 * math.pi * (j + 0.5) / sides
            # Three lobes make the brim read as a tricorn even at distance.
            lobe = 1.0 + 0.3 * math.cos(3 * (a + math.pi / 2))
            ring.append((scale_r * 0.33 * s * lobe * math.cos(a), scale_r * 0.33 * s * lobe * math.sin(a), z + dz * s))
        rings.append(ring)
    mb.loft(rings, "faction_c")
    with mb.xf(Matrix.Translation((0, 0, z))):
        mb.lathe([(0.2 * s, 0.0), (0.19 * s, 0.11 * s), (0.11 * s, 0.17 * s)], sides, "faction_c", smooth=hq)
    mb.box((0, centre.y - 0.27 * s, z + 0.03 * s), (0.12 * s, 0.05 * s, 0.03 * s), "gold")


def _hands_and_feet(mb, joints, look, q, hq):
    s = look.scale
    for side, sign in (("L", 1), ("R", -1)):
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


def _coat(mb, look, q, hq):
    s, w = look.scale, look.width
    sides = q["torso"]
    open_front = {j for j in range(sides) if math.sin(2 * math.pi * (j + 0.5) / sides) < -0.85}

    def shell(bone, rows, colour):
        with mb.bound_to(bone):
            rings = []
            for rx, ry, z in rows:
                ring = []
                for j in range(sides):
                    a = 2 * math.pi * (j + 0.5) / sides
                    ring.append((rx * s * math.cos(a), ry * s * math.sin(a), z * s))
                rings.append(ring)
            mb.loft(rings, lambda _i, j: look.shirt if j in open_front else colour, smooth=hq)

    shell("chest", [(0.25 * w, 0.175, 1.06), (0.315 * w, 0.185, 1.28), (0.15 * w, 0.11, 1.38)], "faction_a")
    shell("spine", [(0.22 * w, 0.165, 0.9), (0.25 * w, 0.175, 1.1)], "faction_a")
    # Coat tails hang behind the legs and are bound to the hips so they swing with them.
    with mb.bound_to("hips"):
        rows = [(0.235, 0.17, 0.95), (0.27, 0.2, 0.74), (0.3, 0.23, 0.42)]
        rings = []
        arc = 8 if hq else 4
        for rx, ry, z in rows:
            outer = []
            inner = []
            for j in range(arc + 1):
                a = math.radians(-10 + 200 * j / arc)
                outer.append((rx * s * w * math.cos(a), ry * s * math.sin(a), z * s))
                inner.append((rx * 0.9 * s * w * math.cos(a), ry * 0.9 * s * math.sin(a), z * s))
            rings.append(outer + list(reversed(inner)))
        mb.loft(rings, "faction_a", smooth=False)


def _extras(mb, joints, look, q, hq):
    s, w, g = look.scale, look.width, look.girth
    extras = look.extras
    if "coat" in extras:
        _coat(mb, look, q, hq)
        for side in ("L", "R"):
            head, tail = (Vector(p) for p in joints[f"lower_arm.{side}"])
            cuff = head + (tail - head) * 0.72
            with mb.bound_to(f"lower_arm.{side}"):
                mb.tube(cuff, tail, 0.062 * s, 0.078 * s, sides=q["limb"], color="faction_a")
    if "gold_trim" in extras:
        with mb.bound_to("chest"):
            for sign in (1, -1):
                mb.box((sign * 0.27 * s, 0.0, 1.29 * s), (0.13 * s, 0.17 * s, 0.05 * s), "gold")
        if hq:
            with mb.bound_to("spine"):
                for z in (0.97, 1.05):
                    mb.box((0.07 * s, -0.17 * s, z * s), (0.03, 0.02, 0.03), "gold")
    if "sash" in extras:
        with mb.bound_to("hips"):
            mb.lathe([(0.215 * s, 0.84 * s), (0.215 * s, 0.93 * s)], q["torso"], "faction_a", smooth=False)
            mb.plate([(0.15 * s, -0.16 * s, 0.86 * s), (0.22 * s, -0.17 * s, 0.6 * s), (0.1 * s, -0.17 * s, 0.62 * s)], 0.02, "faction_a")
    if "bandolier" in extras:
        with mb.bound_to("chest"):
            mb.tube((-0.27 * s, -0.11 * s, 1.31 * s), (0.2 * s, -0.17 * s, 1.08 * s), 0.024 * s, sides=4, color="leather_dark", flat=1.4)
            if hq:
                for i in range(4):
                    k = (i + 0.5) / 4
                    mb.box(((-0.27 + 0.47 * k) * s, (-0.135 - 0.05 * k) * s, (1.31 - 0.23 * k) * s), (0.026, 0.03, 0.06), "brass")
    if "pauldrons" in extras:
        with mb.bound_to("chest"):
            for sign in (1, -1):
                mb.sphere((sign * 0.3 * w * s, 0, 1.3 * s), (0.17 * s, 0.17 * s, 0.11 * s), 8 if hq else 4, 4 if hq else 2, "iron_light", smooth=hq)
        with mb.bound_to("spine"):
            mb.tube((-0.25 * s, -0.17 * g * s, 1.08 * s), (0.2 * s, -0.17 * g * s, 0.94 * s), 0.04 * s, sides=4, color="leather_dark")


def build_character(mb, name, hq):
    look = LOOKS[name]
    q = _tiers(hq)
    joints = _joints(look.scale, look.width)
    s, g = look.scale, look.girth

    sleeve = "faction_a" if "coat" in look.extras else look.skin if name == "PirateBrute" else look.shirt
    for side in ("L", "R"):
        _limb(mb, joints, f"upper_arm.{side}", 0.075 * s * g, 0.062 * s * g, sleeve, q, extend=0.03)
        _limb(mb, joints, f"lower_arm.{side}", 0.062 * s * g, 0.05 * s * g, sleeve if "coat" in look.extras else look.skin, q, extend=0.02)
        _limb(mb, joints, f"thigh.{side}", 0.1 * s * g, 0.075 * s * g, look.trousers, q, extend=0.03)
        _limb(mb, joints, f"shin.{side}", 0.085 * s * g, 0.07 * s * g, look.boots, q, extend=0.02)
    _torso(mb, joints, look, q)
    _head(mb, joints, look, q, hq)
    _hands_and_feet(mb, joints, look, q, hq)
    _extras(mb, joints, look, q, hq)

    mb.socket("head_top", (0, 0, 1.85 * s))
    mb.socket("chest_centre", (0, 0, 1.2 * s))
    return joints


# ---- rig -----------------------------------------------------------------------------

def create_armature(name, joints, offset, parents=None):
    parents = parents or BONE_PARENTS
    data = bpy.data.armatures.new(f"{name}_Rig")
    arm = bpy.data.objects.new(f"{name}_Rig", data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    created = {}
    for bone in parents:
        head, tail = joints[bone]
        ebone = data.edit_bones.new(bone)
        ebone.head = Vector(head) + offset
        ebone.tail = Vector(tail) + offset
        created[bone] = ebone
    for bone, parent in parents.items():
        if parent:
            created[bone].parent = created[parent]
            created[bone].use_connect = False
    # Roll puts each bone's +X, which is an attached item's top, up when the arm is raised to aim.
    for bone in ("weapon.R", "gun.R", "weapon.L", "gun.L"):
        if bone in created:
            created[bone].align_roll((1, 0, 0))
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm


# ---- animation -----------------------------------------------------------------------

STANCE = {
    "upper_arm.L": (-8, -8, 0), "lower_arm.L": (-28, 0, 0),
    "upper_arm.R": (-12, 8, 0), "lower_arm.R": (-42, 0, 0),
    "thigh.L": (-6, -3, 0), "shin.L": (12, 0, 0), "foot.L": (-6, 0, 0),
    "thigh.R": (5, 3, 0), "shin.R": (10, 0, 0), "foot.R": (-15, 0, 0),
    "chest": (4, 0, 0),
    "hips@": (0, 0, -0.025),
}


def _pose(**over):
    pose = dict(STANCE)
    for key, value in over.items():
        pose[key.replace("__L", ".L").replace("__R", ".R").replace("_loc", "@")] = value
    return pose


# name: (loop, {frame: pose})
CLIPS = {
    "Idle": (True, {
        0: _pose(),
        24: _pose(chest=(7, 0, 0), head=(-3, 0, 0), hips_loc=(0, 0, -0.04), upper_arm__L=(-8, -11, 0), upper_arm__R=(-12, 11, 0)),
        48: _pose(),
    }),
    "Walk": (True, {
        0: _pose(thigh__L=(-30, 0, 0), shin__L=(8, 0, 0), foot__L=(15, 0, 0), thigh__R=(28, 0, 0), shin__R=(24, 0, 0), foot__R=(-15, 0, 0), upper_arm__L=(18, -6, 0), upper_arm__R=(-26, 6, 0), chest=(6, 0, 6), hips_loc=(0, 0, -0.02)),
        6: _pose(thigh__L=(-4, 0, 0), shin__L=(4, 0, 0), foot__L=(0, 0, 0), thigh__R=(-16, 0, 0), shin__R=(62, 0, 0), foot__R=(0, 0, 0), upper_arm__L=(0, -6, 0), upper_arm__R=(-8, 6, 0), chest=(6, 0, 0), hips_loc=(0, 0, 0.02)),
        12: _pose(thigh__L=(28, 0, 0), shin__L=(24, 0, 0), foot__L=(-15, 0, 0), thigh__R=(-30, 0, 0), shin__R=(8, 0, 0), foot__R=(15, 0, 0), upper_arm__L=(-26, -6, 0), upper_arm__R=(18, 6, 0), chest=(6, 0, -6), hips_loc=(0, 0, -0.02)),
        18: _pose(thigh__L=(-16, 0, 0), shin__L=(62, 0, 0), foot__L=(0, 0, 0), thigh__R=(-4, 0, 0), shin__R=(4, 0, 0), foot__R=(0, 0, 0), upper_arm__L=(-8, -6, 0), upper_arm__R=(0, 6, 0), chest=(6, 0, 0), hips_loc=(0, 0, 0.02)),
        24: _pose(thigh__L=(-30, 0, 0), shin__L=(8, 0, 0), foot__L=(15, 0, 0), thigh__R=(28, 0, 0), shin__R=(24, 0, 0), foot__R=(-15, 0, 0), upper_arm__L=(18, -6, 0), upper_arm__R=(-26, 6, 0), chest=(6, 0, 6), hips_loc=(0, 0, -0.02)),
    }),
    "AttackMelee": (False, {
        0: _pose(),
        9: _pose(upper_arm__R=(-150, 18, 0), lower_arm__R=(-55, 0, 0), chest=(-12, 0, -28), spine=(-5, 0, -10), head=(4, 0, 18), thigh__R=(16, 3, 0), hips_loc=(0, 0.06, -0.03)),
        14: _pose(upper_arm__R=(-58, -8, 0), lower_arm__R=(-8, 0, 0), chest=(24, 0, 32), spine=(10, 0, 12), head=(-14, 0, -22), thigh__L=(-34, -3, 0), shin__L=(26, 0, 0), thigh__R=(22, 3, 0), hips_loc=(0, -0.14, -0.08)),
        20: _pose(upper_arm__R=(-48, -8, 0), lower_arm__R=(-18, 0, 0), chest=(20, 0, 26), spine=(8, 0, 10), head=(-12, 0, -18), thigh__L=(-30, -3, 0), shin__L=(24, 0, 0), thigh__R=(20, 3, 0), hips_loc=(0, -0.12, -0.08)),
        36: _pose(),
    }),
    "AttackRanged": (False, {
        0: _pose(),
        10: _pose(upper_arm__R=(-88, -4, 0), lower_arm__R=(-4, 0, 0), chest=(0, 0, 24), head=(0, 0, -22)),
        14: _pose(upper_arm__R=(-112, -4, 0), lower_arm__R=(-14, 0, 0), chest=(-6, 0, 18), head=(-3, 0, -18), hips_loc=(0, 0.05, -0.025)),
        20: _pose(upper_arm__R=(-90, -4, 0), lower_arm__R=(-4, 0, 0), chest=(0, 0, 24), head=(0, 0, -22)),
        32: _pose(),
    }),
    "Hit": (False, {
        0: _pose(),
        4: _pose(chest=(-24, 0, 6), spine=(-10, 0, 0), head=(-20, 0, 0), upper_arm__L=(14, -24, 0), upper_arm__R=(14, 24, 0), hips_loc=(0, 0.09, -0.05)),
        18: _pose(),
    }),
    "Block": (False, {
        0: _pose(),
        7: _pose(upper_arm__R=(-72, -22, 0), lower_arm__R=(-96, 0, 0), upper_arm__L=(-72, 22, 0), lower_arm__L=(-96, 0, 0), chest=(14, 0, 0), head=(14, 0, 0), hips_loc=(0, 0.04, -0.09)),
        22: _pose(upper_arm__R=(-72, -22, 0), lower_arm__R=(-96, 0, 0), upper_arm__L=(-72, 22, 0), lower_arm__L=(-96, 0, 0), chest=(14, 0, 0), head=(14, 0, 0), hips_loc=(0, 0.04, -0.09)),
        32: _pose(),
    }),
    "Death": (False, {
        0: _pose(),
        8: _pose(chest=(-22, 0, 12), head=(-22, 0, 0), upper_arm__L=(20, -30, 0), upper_arm__R=(20, 30, 0), thigh__L=(-14, 0, 0), shin__L=(24, 0, 0), hips_loc=(0, 0.1, -0.08)),
        28: _pose(root=(-84, 0, 0), chest=(-6, 0, 0), head=(-8, 0, 14), upper_arm__L=(6, -58, 0), lower_arm__L=(-12, 0, 0), upper_arm__R=(6, 52, 0), lower_arm__R=(-18, 0, 0), thigh__L=(-18, -6, 0), shin__L=(24, 0, 0), foot__L=(10, 0, 0), thigh__R=(-6, 6, 0), shin__R=(10, 0, 0), foot__R=(10, 0, 0), hips_loc=(0, 0, 0.06)),
        36: _pose(root=(-90, 0, 0), chest=(-6, 0, 0), head=(-8, 0, 14), upper_arm__L=(6, -58, 0), lower_arm__L=(-12, 0, 0), upper_arm__R=(6, 52, 0), lower_arm__R=(-18, 0, 0), thigh__L=(-18, -6, 0), shin__L=(24, 0, 0), foot__L=(10, 0, 0), thigh__R=(-6, 6, 0), shin__R=(10, 0, 0), foot__R=(10, 0, 0), hips_loc=(0, 0, 0.06)),
    }),
    "Victory": (True, {
        0: _pose(),
        10: _pose(upper_arm__R=(-172, 8, 0), lower_arm__R=(-8, 0, 0), chest=(-8, 0, 0), head=(-14, 0, 0), hips_loc=(0, 0, -0.06), thigh__L=(-16, -3, 0), shin__L=(26, 0, 0), thigh__R=(-6, 3, 0), shin__R=(26, 0, 0)),
        16: _pose(upper_arm__R=(-178, 12, 0), lower_arm__R=(0, 0, 0), upper_arm__L=(-8, -30, 0), chest=(-12, 0, 0), head=(-18, 0, 0), hips_loc=(0, 0, 0.11), thigh__L=(-8, -3, 0), shin__L=(8, 0, 0), thigh__R=(-4, 3, 0), shin__R=(8, 0, 0)),
        24: _pose(upper_arm__R=(-172, 8, 0), lower_arm__R=(-8, 0, 0), chest=(-8, 0, 0), head=(-14, 0, 0), hips_loc=(0, 0, -0.06), thigh__L=(-16, -3, 0), shin__L=(26, 0, 0), thigh__R=(-6, 3, 0), shin__R=(26, 0, 0)),
        32: _pose(upper_arm__R=(-178, 12, 0), lower_arm__R=(0, 0, 0), upper_arm__L=(-8, -30, 0), chest=(-12, 0, 0), head=(-18, 0, 0), hips_loc=(0, 0, 0.11), thigh__L=(-8, -3, 0), shin__L=(8, 0, 0), thigh__R=(-4, 3, 0), shin__R=(8, 0, 0)),
        40: _pose(upper_arm__R=(-172, 8, 0), lower_arm__R=(-8, 0, 0), chest=(-8, 0, 0), head=(-14, 0, 0), hips_loc=(0, 0, -0.06), thigh__L=(-16, -3, 0), shin__L=(26, 0, 0), thigh__R=(-6, 3, 0), shin__R=(26, 0, 0)),
    }),
    # Campaign clips. Grapple: the swing onto a ship. Work: hub tasks (cleaning, sharpening, chart reading).
    # Surrender: the Davy Jones' Choice pose. Talk: hub conversations. Taunt: Nemesis rivals.
    "Run": (True, {
        0: _pose(thigh__L=(-52, 0, 0), shin__L=(18, 0, 0), foot__L=(18, 0, 0), thigh__R=(38, 0, 0), shin__R=(62, 0, 0), upper_arm__L=(34, -10, 0), lower_arm__L=(-70, 0, 0), upper_arm__R=(-46, 10, 0), lower_arm__R=(-74, 0, 0), chest=(16, 0, 10), spine=(6, 0, 0), hips_loc=(0, -0.03, -0.05)),
        4: _pose(thigh__L=(-10, 0, 0), shin__L=(10, 0, 0), thigh__R=(-34, 0, 0), shin__R=(92, 0, 0), upper_arm__L=(6, -10, 0), lower_arm__L=(-70, 0, 0), upper_arm__R=(-14, 10, 0), lower_arm__R=(-74, 0, 0), chest=(16, 0, 0), spine=(6, 0, 0), hips_loc=(0, -0.03, 0.05)),
        8: _pose(thigh__L=(38, 0, 0), shin__L=(62, 0, 0), thigh__R=(-52, 0, 0), shin__R=(18, 0, 0), foot__R=(18, 0, 0), upper_arm__L=(-46, -10, 0), lower_arm__L=(-74, 0, 0), upper_arm__R=(34, 10, 0), lower_arm__R=(-70, 0, 0), chest=(16, 0, -10), spine=(6, 0, 0), hips_loc=(0, -0.03, -0.05)),
        12: _pose(thigh__L=(-34, 0, 0), shin__L=(92, 0, 0), thigh__R=(-10, 0, 0), shin__R=(10, 0, 0), upper_arm__L=(-14, -10, 0), lower_arm__L=(-74, 0, 0), upper_arm__R=(6, 10, 0), lower_arm__R=(-70, 0, 0), chest=(16, 0, 0), spine=(6, 0, 0), hips_loc=(0, -0.03, 0.05)),
        16: _pose(thigh__L=(-52, 0, 0), shin__L=(18, 0, 0), foot__L=(18, 0, 0), thigh__R=(38, 0, 0), shin__R=(62, 0, 0), upper_arm__L=(34, -10, 0), lower_arm__L=(-70, 0, 0), upper_arm__R=(-46, 10, 0), lower_arm__R=(-74, 0, 0), chest=(16, 0, 10), spine=(6, 0, 0), hips_loc=(0, -0.03, -0.05)),
    }),
    "Grapple": (True, {
        0: _pose(root=(14, 0, 0), upper_arm__L=(-176, -6, 0), lower_arm__L=(-12, 0, 0), upper_arm__R=(-30, 26, 0), lower_arm__R=(-40, 0, 0), thigh__L=(-62, -6, 0), shin__L=(84, 0, 0), thigh__R=(-20, 6, 0), shin__R=(46, 0, 0), chest=(-4, 0, 0), head=(6, 0, 0)),
        12: _pose(root=(-14, 0, 0), upper_arm__L=(-176, -6, 0), lower_arm__L=(-12, 0, 0), upper_arm__R=(-14, 34, 0), lower_arm__R=(-26, 0, 0), thigh__L=(-20, -6, 0), shin__L=(28, 0, 0), thigh__R=(14, 6, 0), shin__R=(40, 0, 0), chest=(6, 0, 0), head=(-4, 0, 0)),
        24: _pose(root=(14, 0, 0), upper_arm__L=(-176, -6, 0), lower_arm__L=(-12, 0, 0), upper_arm__R=(-30, 26, 0), lower_arm__R=(-40, 0, 0), thigh__L=(-62, -6, 0), shin__L=(84, 0, 0), thigh__R=(-20, 6, 0), shin__R=(46, 0, 0), chest=(-4, 0, 0), head=(6, 0, 0)),
    }),
    "Talk": (True, {
        0: _pose(upper_arm__R=(-38, 10, 0), lower_arm__R=(-82, 0, 0), chest=(2, 0, 0)),
        14: _pose(upper_arm__R=(-58, 22, 0), lower_arm__R=(-58, 0, 0), chest=(4, 0, -7), head=(5, 0, 6)),
        30: _pose(upper_arm__R=(-34, 10, 0), lower_arm__R=(-92, 0, 0), upper_arm__L=(-30, -16, 0), lower_arm__L=(-58, 0, 0), chest=(0, 0, 5), head=(-4, 0, -5)),
        48: _pose(upper_arm__R=(-38, 10, 0), lower_arm__R=(-82, 0, 0), chest=(2, 0, 0)),
    }),
    "Work": (True, {
        0: _pose(thigh__L=(-46, -5, 0), shin__L=(58, 0, 0), foot__L=(-12, 0, 0), thigh__R=(-8, 7, 0), shin__R=(38, 0, 0), foot__R=(-30, 0, 0), spine=(14, 0, 0), chest=(22, 0, 0), head=(-10, 0, 0), upper_arm__L=(-44, 6, 0), lower_arm__L=(-44, 0, 0), upper_arm__R=(-44, -6, 0), lower_arm__R=(-44, 0, 0), hips_loc=(0, 0, -0.2)),
        12: _pose(thigh__L=(-46, -5, 0), shin__L=(58, 0, 0), foot__L=(-12, 0, 0), thigh__R=(-8, 7, 0), shin__R=(38, 0, 0), foot__R=(-30, 0, 0), spine=(14, 0, 0), chest=(25, 0, 4), head=(-12, 0, -6), upper_arm__L=(-44, 6, 0), lower_arm__L=(-54, 0, 0), upper_arm__R=(-58, -6, 0), lower_arm__R=(-26, 0, 0), hips_loc=(0, 0, -0.2)),
        24: _pose(thigh__L=(-46, -5, 0), shin__L=(58, 0, 0), foot__L=(-12, 0, 0), thigh__R=(-8, 7, 0), shin__R=(38, 0, 0), foot__R=(-30, 0, 0), spine=(14, 0, 0), chest=(22, 0, 0), head=(-10, 0, 0), upper_arm__L=(-44, 6, 0), lower_arm__L=(-44, 0, 0), upper_arm__R=(-44, -6, 0), lower_arm__R=(-44, 0, 0), hips_loc=(0, 0, -0.2)),
    }),
    "Surrender": (False, {
        0: _pose(),
        14: _pose(thigh__L=(-82, -5, 0), shin__L=(84, 0, 0), foot__L=(-6, 0, 0), thigh__R=(6, 6, 0), shin__R=(96, 0, 0), foot__R=(-24, 0, 0), upper_arm__L=(-120, -28, 0), lower_arm__L=(-70, 0, 0), upper_arm__R=(-120, 28, 0), lower_arm__R=(-70, 0, 0), chest=(8, 0, 0), head=(16, 0, 0), hips_loc=(0, 0.04, -0.34)),
        30: _pose(thigh__L=(-82, -5, 0), shin__L=(84, 0, 0), foot__L=(-6, 0, 0), thigh__R=(6, 6, 0), shin__R=(96, 0, 0), foot__R=(-24, 0, 0), upper_arm__L=(-120, -28, 0), lower_arm__L=(-70, 0, 0), upper_arm__R=(-120, 28, 0), lower_arm__R=(-70, 0, 0), chest=(10, 0, 0), head=(20, 0, 0), hips_loc=(0, 0.04, -0.34)),
    }),
    "Taunt": (False, {
        0: _pose(),
        8: _pose(upper_arm__R=(-92, -4, 0), lower_arm__R=(-4, 0, 0), chest=(-8, 0, 16), head=(-12, 0, -14), upper_arm__L=(-30, -30, 0), lower_arm__L=(-110, 0, 0)),
        16: _pose(upper_arm__R=(-104, -4, 0), lower_arm__R=(-4, 0, 0), chest=(-10, 0, 18), head=(-14, 0, -16), upper_arm__L=(-30, -30, 0), lower_arm__L=(-110, 0, 0), hips_loc=(0, 0.03, -0.01)),
        28: _pose(upper_arm__R=(-92, -4, 0), lower_arm__R=(-4, 0, 0), chest=(-8, 0, 16), head=(-12, 0, -14), upper_arm__L=(-30, -30, 0), lower_arm__L=(-110, 0, 0)),
        40: _pose(),
    }),
}


def _apply_pose(arm, pose, frame, parents=None):
    for bone_name in parents or BONE_PARENTS:
        pbone = arm.pose.bones[bone_name]
        pbone.rotation_mode = "QUATERNION"
        rest = pbone.bone.matrix_local.to_3x3()
        degrees = pose.get(bone_name, (0, 0, 0))
        world_q = Euler([math.radians(a) for a in degrees], "XYZ").to_quaternion()
        pbone.rotation_quaternion = (rest.inverted() @ world_q.to_matrix() @ rest).to_quaternion()
        pbone.keyframe_insert("rotation_quaternion", frame=frame, group=bone_name)
    hips = arm.pose.bones["hips"]
    rest = hips.bone.matrix_local.to_3x3()
    hips.location = rest.inverted() @ Vector(pose.get("hips@", (0, 0, 0)))
    hips.keyframe_insert("location", frame=frame, group="hips")


def add_clips(arm, clips=None, parents=None):
    arm.animation_data_create()
    bpy.context.scene.render.fps = FPS
    for clip, (_, frames) in (clips or CLIPS).items():
        action = bpy.data.actions.new(clip)
        action.use_fake_user = False
        arm.animation_data.action = action
        for frame, pose in frames.items():
            _apply_pose(arm, pose, frame, parents)
        arm.animation_data.action = None
        track = arm.animation_data.nla_tracks.new()
        track.name = clip
        strip = track.strips.new(clip, int(min(frames)), action)
        strip.name = clip
    # The budget gate measures the evaluated mesh for its pivot, so it must see the rest pose.
    # Muted tracks still export: glTF export looks at strip mutes, not track mutes.
    for track in arm.animation_data.nla_tracks:
        track.mute = True
    for pbone in arm.pose.bones:
        pbone.rotation_quaternion = (1, 0, 0, 0)
        pbone.location = (0, 0, 0)
    bpy.context.scene.frame_set(0)


def clip_table(clips=None):
    return {
        clip: {"loop": loop, "frames": max(frames), "seconds": round(max(frames) / FPS, 3)}
        for clip, (loop, frames) in (clips or CLIPS).items()
    }
