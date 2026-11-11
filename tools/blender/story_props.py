"""Shattered Skies props: boss hardware, ammo, story items and signature weapons.

Held weapons stand on the pommel with their length along +Z and publish grip / trail_tip / muzzle
sockets, the same way the base kit's cutlass and flintlock do, so they attach with no extra code.
"""
import math
import random

from mathutils import Matrix


def _q(hq, high, low):
    return high if hq else low


def _x_axis():
    """Local lathe Z becomes world X."""
    return Matrix.Rotation(math.pi / 2, 4, "Y")


def _y_axis():
    """Local lathe Z becomes world -Y, the forward direction of ship-mounted hardware."""
    return Matrix.Rotation(math.pi / 2, 4, "X")


# ---- Ship hardware --------------------------------------------------------------------------

def harpoon_winch(mb, hq):
    """Krag's signature weapon, unlocked as a module after Act I. Fires along -Y."""
    sides = _q(hq, 10, 5)
    mb.box((0, 0.2, 0.25), (1.5, 2.0, 0.5), "iron", top_scale=0.86)
    with mb.xf(Matrix.Translation((-0.6, 0.45, 0.85)) @ _x_axis()):
        mb.lathe([(0.45, 0.0), (0.45, 0.14), (0.28, 0.14), (0.28, 1.06), (0.45, 1.06), (0.45, 1.2)], sides, lambda i, _j: "rope" if i == 2 else "iron_light", smooth=False)
    mb.path([(0, 0.0, 0.9), (0, -0.7, 1.0), (0, -1.5, 1.06), (0, -1.53, 1.06), (0, -1.75, 1.06)], [0.2, 0.18, 0.13, 0.2, 0.2], _q(hq, 8, 4), "rust_dark")
    mb.tube((0, -1.7, 1.06), (0, -2.35, 1.07), 0.06, 0.012, sides=_q(hq, 5, 3), color="iron_light")
    if hq:
        for sign in (1, -1):
            mb.plate([(sign * 0.05, -2.05, 1.07), (sign * 0.36, -1.75, 1.18), (sign * 0.34, -1.75, 0.94)], 0.05, "iron_light")
            mb.box((sign * 0.55, 0.45, 0.65), (0.1, 0.6, 0.45), "rust")
        mb.tube((-0.72, 1.0, 0.45), (-0.95, 1.3, 1.2), 0.035, sides=4, color="iron")
        mb.sphere((-0.95, 1.3, 1.25), 0.07, 6, 3, "gem_red")
    mb.socket("muzzle", (0, -1.75, 1.06))
    mb.socket("rope", (0, 0.45, 1.3))


def harpoon(mb, hq):
    """The tethered projectile. Length along +Z so it can fly straight; rope ties to the tail."""
    mb.tube((0, 0, 0.0), (0, 0, 1.3), 0.03, 0.03, sides=_q(hq, 6, 4), color="iron")
    mb.tube((0, 0, 1.3), (0, 0, 1.75), 0.08, 0.008, sides=_q(hq, 6, 3), color="iron_light")
    for i in range(_q(hq, 3, 2)):
        with mb.xf(Matrix.Rotation(2 * math.pi * i / _q(hq, 3, 2), 4, "Z")):
            mb.plate([(0.02, 0, 1.5), (0.2, 0, 1.2), (0.02, 0, 1.3)], 0.025, "iron_light")
    if hq:
        with mb.xf(Matrix.Translation((0, 0, 0.1))):
            mb.lathe([(0.05, 0.0), (0.05, 0.1)], 6, "brass", smooth=False)
    mb.socket("rope", (0, 0, 0.0))
    mb.socket("tip", (0, 0, 1.75))


def krag_anchor(mb, hq):
    """The iron anchors Krag bolts onto enemy hulls to drag them into the Undertow."""
    h = 2.3
    mb.tube((0, 0, 0.2), (0, 0, h), 0.11, 0.09, sides=_q(hq, 6, 4), color="iron")
    mb.tube((-0.65, 0, h - 0.42), (0.65, 0, h - 0.42), 0.055, sides=_q(hq, 5, 3), color="rust_dark")
    with mb.xf(Matrix.Translation((0, 0, h + 0.11)) @ _y_axis()):
        mb.lathe([(0.17, -0.04), (0.17, 0.04)], _q(hq, 8, 4), "iron_light", smooth=False)
    arc = [(-1.05, 0, 0.62), (-0.82, 0, 0.26), (-0.42, 0, 0.05), (0, 0, 0.02), (0.42, 0, 0.05), (0.82, 0, 0.26), (1.05, 0, 0.62)]
    mb.path(arc, [0.012, 0.11, 0.14, 0.16, 0.14, 0.11, 0.012], _q(hq, 5, 3), "iron")
    if hq:
        for sign in (1, -1):
            mb.plate([(sign * 1.05, 0, 0.74), (sign * 0.74, 0, 0.22), (sign * 1.28, 0, 0.3)], 0.05, "iron_light")
    mb.socket("rope", (0, 0, h + 0.15))
    mb.socket("hook", (0, 0, 0.04))


def afterburner_turbine(mb, hq):
    """The Mirage's module. Exhaust at +Y; put the plume VFX at the 'exhaust' socket."""
    z = 0.78
    rim = _q(hq, 12, 6)
    with mb.xf(Matrix.Translation((0, 0, z)) @ Matrix.Rotation(-math.pi / 2, 4, "X")):
        mb.lathe([(0.3, -1.3), (0.7, -0.85), (0.78, 0.0), (0.66, 0.9), (0.6, 1.25)], rim, "iron_light", smooth=hq)
        mb.lathe([(0.47, 1.26), (0.47, 1.3)], rim, "plasma", smooth=False)
        if hq:
            mb.lathe([(0.8, -0.2), (0.8, 0.14)], rim, "brass", smooth=False, caps=(False, False))
    if hq:
        for i in range(8):
            with mb.xf(Matrix.Translation((0, -1.32, z)) @ Matrix.Rotation(2 * math.pi * i / 8, 4, "Y")):
                mb.plate([(0.04, 0, 0.0), (0.55, 0.06, 0.1), (0.55, 0.06, -0.1)], 0.02, "brass")
    mb.socket("exhaust", (0, 1.32, z))
    mb.socket("intake", (0, -1.32, z))


def deck_mortar(mb, hq):
    """Act III siege weapon. Lobs along -Y at about 60 degrees."""
    with mb.xf(Matrix.Translation((0, 0, 0))):
        mb.lathe([(0.82, 0.0), (0.82, 0.22), (0.58, 0.34)], _q(hq, 12, 6), "wood_dark", smooth=False)
    mb.path([(0, 0.26, 0.42), (0, 0.05, 0.75), (0, -0.25, 1.2), (0, -0.27, 1.23), (0, -0.33, 1.34)], [0.42, 0.5, 0.37, 0.48, 0.48], _q(hq, 10, 5), "iron")
    if hq:
        for sign in (1, -1):
            mb.box((sign * 0.46, 0.0, 0.58), (0.14, 0.72, 0.65), "iron_light")
        with mb.xf(Matrix.Translation((0, -0.33, 1.34))):
            mb.sphere((0, 0.05, 0.0), 0.31, 6, 2, "abyss", smooth=False)
    mb.socket("muzzle", (0, -0.34, 1.36))


def siege_cannon(mb, hq):
    """Enormous fixed gun on a slewing ring. Turned on the Sovereign Gale in the Act IV gauntlet."""
    sides = _q(hq, 12, 6)
    mb.lathe([(1.2, 0.0), (1.2, 0.26), (0.9, 0.42)], sides, "gold_dark", smooth=False)
    mb.box((0, 0.2, 0.75), (1.4, 2.2, 0.7), "faction_a", top_scale=0.84)
    mb.path([(0, 1.25, 1.1), (0, 0.2, 1.12), (0, -2.6, 1.22), (0, -2.65, 1.22), (0, -3.1, 1.24)], [0.5, 0.48, 0.28, 0.4, 0.4], _q(hq, 10, 5), "iron")
    if hq:
        for y in (-0.5, -1.4):
            with mb.xf(Matrix.Translation((0, y, 1.15 + (y + 0.5) * -0.03)) @ _y_axis()):
                mb.lathe([(0.44 - 0.04 * abs(y), -0.08), (0.44 - 0.04 * abs(y), 0.08)], 10, "gold_dark", smooth=False)
    mb.socket("muzzle", (0, -3.1, 1.24))
    mb.socket("pivot", (0, 0, 0.42))


def flak_gun(mb, hq):
    """Rook's heavy flak, a quad-barrel swivel for clearing Assault Gliders."""
    mb.lathe([(0.48, 0.0), (0.42, 0.14), (0.14, 0.2), (0.12, 0.7)], _q(hq, 10, 5), "iron", smooth=False)
    mb.box((0, -0.05, 0.86), (0.72, 0.8, 0.36), "faction_a")
    for sx in (-0.17, 0.17):
        for sz in _q(hq, (-0.09, 0.09), (0.0,)):
            mb.tube((sx, -0.4, 0.86 + sz), (sx, -1.2, 0.9 + sz), 0.05, 0.04, sides=_q(hq, 6, 3), color="iron_light")
    if hq:
        mb.box((0, 0.42, 0.72), (0.5, 0.08, 0.55), "steel")
        for sign in (1, -1):
            mb.tube((sign * 0.1, 0.28, 0.82), (sign * 0.22, 0.42, 0.95), 0.03, sides=4, color="leather_dark")
    mb.socket("muzzle", (0, -1.22, 0.9))
    mb.socket("gunner", (0, 0.5, 0.0))


def missile(mb, hq):
    """Armada frigate missile. Flies nose-first along +Z, thruster VFX at 'exhaust'."""
    sides = _q(hq, 8, 4)
    profile = [(0.09, 0.0), (0.12, 0.1), (0.12, 0.85), (0.08, 1.05), (0.01, 1.3)] if hq else [(0.11, 0.0), (0.11, 0.85), (0.01, 1.3)]
    mb.lathe(profile, sides, lambda i, _j: "gold" if i >= len(profile) - 3 else "enamel", smooth=False)
    for i in range(_q(hq, 4, 3)):
        with mb.xf(Matrix.Rotation(2 * math.pi * i / _q(hq, 4, 3), 4, "Z")):
            mb.plate([(0.1, 0, 0.3), (0.3, 0, 0.0), (0.3, 0, -0.06), (0.1, 0, 0.1)], 0.015, "faction_a")
    mb.socket("exhaust", (0, 0, -0.06))
    mb.socket("tip", (0, 0, 1.3))


def lift_core(mb, hq):
    """The heart of every airship and a sub-system target. Morrow sabotages this one."""
    sides = _q(hq, 12, 6)
    mb.lathe([(1.1, 0.0), (1.1, 0.28), (0.72, 0.44), (0.72, 0.6)], sides, "iron", smooth=False)
    mb.lathe([(0.72, 2.1), (0.72, 2.25), (1.1, 2.42), (1.1, 2.7)], sides, "iron", smooth=False)
    with mb.xf(Matrix.Translation((0, 0, 1.35))):
        mb.lathe([(0.1, -0.78), (0.42, -0.5), (0.55, 0.0), (0.42, 0.5), (0.1, 0.78)], _q(hq, 8, 5), lambda i, _j: "liftstone", smooth=False, phase=0.2)
    n = _q(hq, 4, 3)
    for i in range(n):
        a = 2 * math.pi * i / n
        mb.tube((0.8 * math.cos(a), 0.8 * math.sin(a), 0.5), (0.8 * math.cos(a), 0.8 * math.sin(a), 2.2), 0.075, sides=_q(hq, 6, 3), color="brass")
    if hq:
        for z, r in ((1.0, 0.86), (1.7, 0.86)):
            mb.lathe([(r, z - 0.04), (r, z + 0.04)], 12, "brass", smooth=False)
    mb.socket("glow", (0, 0, 1.35))
    mb.socket("charge_slot", (0.72, 0, 0.8))


def lift_stone(mb, hq):
    """Raw Lift-Stone pickup: civilisation's fuel. Glows, so it reads as a collectible at distance."""
    rng = random.Random(14)
    for i, (x, y, r, h) in enumerate(((0, 0, 0.22, 0.85), (0.2, 0.08, 0.13, 0.5), (-0.16, 0.12, 0.11, 0.44), (-0.03, -0.2, 0.09, 0.36)) if hq else ((0, 0, 0.22, 0.85), (0.2, 0.08, 0.12, 0.46))):
        with mb.xf(Matrix.Translation((x, y, 0.08)) @ Matrix.Rotation(rng.uniform(-0.28, 0.28), 4, "X") @ Matrix.Rotation(rng.uniform(-0.28, 0.28), 4, "Y")):
            mb.lathe([(r * 0.6, -0.08), (r, h * 0.25), (r * 0.74, h * 0.72), (r * 0.06, h)], _q(hq, 6, 4), "liftstone", smooth=False)
    mb.lathe([(0.38, 0.0), (0.26, 0.12)], _q(hq, 7, 4), "liftstone_dark", smooth=False)


def ammo_chain_shot(mb, hq):
    """Two halves on a chain, for shredding sails. Spin the projectile about +Y as it flies."""
    z = 0.2
    for sign in (1, -1):
        with mb.xf(Matrix.Translation((sign * 0.34, 0, z))):
            mb.sphere((0, 0, 0), 0.19, _q(hq, 8, 5), _q(hq, 5, 3), "iron", smooth=True)
    # One tube: separate links would share end caps, which the gate's weld removes.
    points = [(-0.2 + 0.4 * i / 4, 0, z) for i in range(5)] if hq else [(-0.2, 0, z), (0.2, 0, z)]
    mb.path(points, [0.024] * len(points), _q(hq, 4, 3), "iron_light")


def ammo_fire_shot(mb, hq):
    """Incendiary shell for setting decks alight. Ember cracks show through a black casing."""
    r_n = _q(hq, 7, 4)
    s_n = _q(hq, 10, 6)
    mb.sphere((0, 0, 0.19), 0.19, s_n, r_n, lambda i, j: "ember" if (i * 3 + j * 5) % 4 == 0 else "abyss", smooth=False)
    mb.tube((0, 0, 0.35), (0, 0.02, 0.47), 0.018, sides=_q(hq, 5, 3), color="rope")
    if hq:
        mb.sphere((0, 0.02, 0.49), 0.035, 5, 3, "ember", smooth=False)


def ammo_grapeshot(mb, hq):
    """Rook's incendiary grapeshot loyalty unlock: a canvas bag of shot tied with cord."""
    rng = random.Random(7)
    n = _q(hq, 10, 3)
    for _ in range(n):
        a, r, z = rng.uniform(0, 6.28), rng.uniform(0.0, 0.1), rng.uniform(0.05, 0.27)
        mb.sphere((r * math.cos(a), r * math.sin(a), z), 0.065, _q(hq, 6, 4), _q(hq, 4, 2), "iron", smooth=False)
    mb.lathe([(0.09, 0.0), (0.16, 0.1), (0.15, 0.24), (0.05, 0.34), (0.06, 0.4)], _q(hq, 8, 5), lambda i, j: "ember" if hq and i == 1 and j % 3 == 0 else "canvas_dark", smooth=False)


def ammo_mortar_shell(mb, hq):
    mb.sphere((0, 0, 0.3), 0.3, _q(hq, 10, 6), _q(hq, 6, 4), "iron", smooth=True)
    with mb.xf(Matrix.Translation((0, 0, 0.54))):
        mb.lathe([(0.07, 0.0), (0.07, 0.1)], _q(hq, 6, 4), "brass", smooth=False)
    if hq:
        with mb.xf(Matrix.Translation((0, 0, 0.3))):
            mb.lathe([(0.305, -0.03), (0.305, 0.03)], 10, "gold_dark", smooth=False)


# ---- Rewards and story items ----------------------------------------------------------------

def scrap_pile(mb, hq):
    """Sinking a ship yields only this: 20% scrap, deliberately miserable next to a treasure chest."""
    rng = random.Random(4)
    mb.lathe([(0.8, 0.0), (0.55, 0.16), (0.2, 0.36), (0.1, 0.42)], _q(hq, 8, 5), lambda _i, j: ("rust_dark", "iron", "rust")[j % 3], smooth=False)
    for _ in range(_q(hq, 7, 2)):
        a, r = rng.uniform(0, 6.28), rng.uniform(0.15, 0.62)
        x, y = r * math.cos(a), r * math.sin(a)
        z = 0.34 * (1 - r / 0.8) + 0.05
        mb.tube((x, y, z), (x + rng.uniform(-0.3, 0.3), y + rng.uniform(-0.3, 0.3), z + rng.uniform(0.1, 0.45)), 0.035, sides=3, color=rng.choice(("iron", "rust", "iron_light")))
    if hq:
        mb.plate([(0.1, -0.2, 0.3), (0.5, -0.15, 0.36), (0.42, -0.4, 0.6), (0.14, -0.42, 0.55)], 0.02, "rust")
        with mb.xf(Matrix.Translation((-0.3, 0.1, 0.45)) @ Matrix.Rotation(1.1, 4, "X")):
            mb.lathe([(0.2, -0.015), (0.2, 0.015)], 8, "iron_light", smooth=False)


def weapon_module(mb, hq):
    """The Scuttle & Plunder reward: a boss's module on a pallet, swapped by faction atlas."""
    mb.box((0, 0, 0.09), (1.2, 1.2, 0.18), "wood_mid")
    mb.box((0, 0, 0.55), (0.9, 0.9, 0.72), "iron")
    mb.box((0, 0, 0.94), (0.72, 0.72, 0.1), "faction_a")
    with mb.xf(Matrix.Translation((0, 0, 1.0))):
        mb.lathe([(0.27, 0.0), (0.2, 0.18), (0.07, 0.3)], _q(hq, 8, 4), "brass", smooth=False)
    mb.sphere((0, 0, 1.28), 0.08, _q(hq, 6, 4), 3, "liftstone", smooth=False)
    if hq:
        for sx in (-1, 1):
            for sy in (-1, 1):
                mb.box((sx * 0.45, sy * 0.45, 0.55), (0.1, 0.1, 0.76), "iron_light")
        for sign in (1, -1):
            mb.box((sign * 0.46, 0, 0.55), (0.03, 0.42, 0.28), "lamp")
            mb.box((0, sign * 0.46, 0.55), (0.42, 0.03, 0.28), "faction_b")


def cipher_key(mb, hq):
    """One of three Syndicate navigation ciphers. Faction atlas colours each lord's key."""
    sides = _q(hq, 12, 6)
    with mb.xf(Matrix.Translation((0, 0, 0.42)) @ Matrix.Rotation(math.pi / 2, 4, "X")):
        mb.lathe([(0.26, -0.03), (0.27, 0.0), (0.26, 0.03)], sides, "gold", smooth=False)
        mb.lathe([(0.17, 0.03), (0.17, 0.045)], sides, "faction_a", smooth=False)
        if hq:
            for i in range(6):
                a = 2 * math.pi * i / 6
                mb.box((0.215 * math.cos(a), 0.215 * math.sin(a), 0.03), (0.04, 0.04, 0.03), "lamp")
    mb.sphere((0, -0.03, 0.42), (0.09, 0.05, 0.09), _q(hq, 6, 4), 3, "liftstone", smooth=False)
    mb.tube((0, 0, 0.16), (0, 0, 0.0 + 0.02), 0.022, sides=_q(hq, 4, 3), color="brass")
    mb.box((0.05, 0, 0.05), (0.08, 0.025, 0.04), "brass")
    mb.box((0.04, 0, 0.13), (0.06, 0.025, 0.035), "brass")
    mb.socket("glow", (0, -0.08, 0.42))


def saboteur_charge(mb, hq):
    """Sable's charge, planted on enemy Lift-Cores. The countdown lamp is at the 'timer' socket."""
    for x in _q(hq, (-0.13, 0.0, 0.13), (-0.08, 0.08)):
        mb.tube((x, 0, 0.0 + 0.01), (x, 0, 0.42), 0.065, sides=_q(hq, 8, 4), color="velvet")
    mb.box((0, -0.03, 0.2), (0.42, 0.1, 0.08), "leather_dark")
    mb.box((0, -0.095, 0.3), (0.16, 0.05, 0.12), "iron")
    mb.box((0.03, -0.128, 0.3), (0.06, 0.02, 0.07), "ember")
    if hq:
        mb.path([(-0.05, -0.1, 0.33), (-0.12, -0.13, 0.42), (-0.05, -0.1, 0.46)], [0.006] * 3, 3, "gem_red")
    mb.socket("timer", (0.03, -0.14, 0.3))


def repair_kit(mb, hq):
    """Dr. Thorne's mid-combat hull patch: a plate, rivets and a glowing lift-solder canister."""
    mb.box((0, 0, 0.17), (0.8, 0.46, 0.34), "faction_a")
    mb.box((0, 0, 0.36), (0.82, 0.48, 0.05), "iron_light")
    mb.tube((-0.14, 0, 0.42), (0.14, 0, 0.42), 0.022, sides=_q(hq, 4, 3), color="leather_dark")
    mb.box((0, -0.24, 0.17), (0.2, 0.03, 0.14), "faction_b")
    if hq:
        with mb.xf(Matrix.Translation((0.5, 0, 0.0))):
            mb.lathe([(0.1, 0.0), (0.1, 0.32), (0.05, 0.4)], 8, "brass", smooth=False)
            mb.lathe([(0.105, 0.1), (0.105, 0.2)], 8, "liftstone", smooth=False, caps=(False, False))
        mb.plate([(-0.85, -0.2, 0.012), (-0.45, -0.2, 0.012), (-0.45, 0.2, 0.012), (-0.85, 0.2, 0.012)], 0.024, "iron_light")
        for x, y in ((-0.8, -0.15), (-0.5, -0.15), (-0.8, 0.15), (-0.5, 0.15)):
            mb.box((x, y, 0.032), (0.03, 0.03, 0.02), "iron")


def helm_wheel(mb, hq):
    """Seize the Helm: the camera's target on the Davy Jones' Choice, and the hub's centrepiece."""
    mb.box((0, 0.1, 0.05), (0.78, 0.72, 0.1), "wood_dark")
    mb.tube((0, 0.1, 0.1), (0, 0.1, 0.88), 0.13, 0.09, sides=_q(hq, 8, 4), color="wood_mid")
    wheel_z = 1.08
    spokes = _q(hq, 8, 4)
    with mb.xf(Matrix.Translation((0, -0.05, wheel_z)) @ Matrix.Rotation(math.pi / 2, 4, "X")):
        # An open ring, not a disc: spokes and the sky show through it at the Seize the Helm close-up.
        mb.lathe([(0.56, -0.04), (0.56, 0.04), (0.47, 0.04), (0.47, -0.04), (0.56, -0.04)], _q(hq, 16, 8), "wood_light", smooth=False, caps=(False, False))
        mb.lathe([(0.11, -0.07), (0.11, 0.07)], _q(hq, 8, 4), "brass", smooth=False)
        for i in range(spokes):
            a = 2 * math.pi * i / spokes
            mb.tube((0.1 * math.cos(a), 0.1 * math.sin(a), 0), (0.66 * math.cos(a), 0.66 * math.sin(a), 0), 0.022, 0.03, sides=_q(hq, 5, 3), color="wood_dark")
            if hq:
                mb.sphere((0.68 * math.cos(a), 0.68 * math.sin(a), 0), 0.035, 5, 3, "brass", smooth=False)
    mb.socket("hub", (0, -0.12, wheel_z))
    mb.socket("hand_L", (0.45, -0.1, wheel_z))
    mb.socket("hand_R", (-0.45, -0.1, wheel_z))


def aether_comm(mb, hq):
    """The set your crew's Aether-Comms bark from. Dressing for the helm on the hub."""
    mb.box((0, 0, 0.26), (0.72, 0.42, 0.52), "wood_dark")
    mb.box((0, -0.22, 0.32), (0.56, 0.02, 0.32), "brass")
    with mb.xf(Matrix.Translation((-0.1, -0.235, 0.34)) @ Matrix.Rotation(math.pi / 2, 4, "X")):
        mb.lathe([(0.11, -0.01), (0.11, 0.01)], _q(hq, 10, 5), "liftstone_dark", smooth=False)
    mb.box((0.18, -0.235, 0.34), (0.1, 0.02, 0.1), "lamp")
    mb.tube((0.22, 0, 0.52), (0.28, 0.06, 0.94), 0.014, sides=3, color="iron_light")
    mb.tube((-0.2, 0.0, 0.52), (-0.3, 0.1, 0.8), 0.014, sides=3, color="iron_light")
    if hq:
        with mb.xf(Matrix.Translation((0.32, 0.1, 0.5))):
            mb.lathe([(0.03, 0.0), (0.1, 0.13)], 8, "brass", smooth=False)
        mb.sphere((0.28, 0.06, 0.96), 0.03, 6, 3, "liftstone", smooth=False)
        for x in (-0.15, -0.03, 0.09):
            mb.box((x, -0.235, 0.12), (0.06, 0.02, 0.06), "iron_light")
    mb.socket("speaker", (-0.1, -0.25, 0.34))


def bounty_board(mb, hq):
    """Nemesis Bounty Board: posters are slots, so UI can pin each rival's portrait on the wood."""
    for sign in (1, -1):
        mb.tube((sign * 1.0, 0, 0.0), (sign * 1.0, 0, 2.3), 0.07, sides=_q(hq, 6, 4), color="wood_dark")
    mb.box((0, 0, 1.45), (2.2, 0.08, 1.45), "wood_mid")
    mb.box((0, 0, 2.28), (2.5, 0.42, 0.1), "wood_dark", top_scale=0.66)
    for i, (x, z, w, h) in enumerate(((-0.65, 1.68, 0.56, 0.72), (0.05, 1.72, 0.56, 0.72), (0.72, 1.62, 0.5, 0.64), (-0.34, 1.0, 0.5, 0.42), (0.42, 1.05, 0.58, 0.42))):
        mb.box((x, -0.05, z), (w, 0.02, h), "parchment")
        mb.socket(f"poster_{i}", (x, -0.07, z))
        if hq:
            mb.box((x, -0.065, z + h * 0.34), (w * 0.72, 0.01, h * 0.09), "gem_red" if i < 3 else "wood_dark")
            mb.box((x, -0.065, z - h * 0.05), (w * 0.5, 0.01, h * 0.34), "cloth_black")
            mb.box((x, -0.068, z + h * 0.48), (0.05, 0.015, 0.05), "iron")
    if hq:
        mb.tube((0.95, -0.05, 2.1), (0.95, -0.34, 1.86), 0.016, sides=3, color="silver")
        mb.sphere((-1.0, -0.24, 2.05), 0.1, 6, 3, "lamp", smooth=False)
    mb.socket("lamp", (-1.0, -0.24, 2.05))


def sky_chart_table(mb, hq):
    """Lyra's table on the hub. Stand her at 'reader' playing the Work clip."""
    mb.box((0, 0, 0.95), (1.8, 1.2, 0.08), "wood_mid")
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.tube((sx * 0.78, sy * 0.5, 0.0), (sx * 0.72, sy * 0.45, 0.92), 0.05, sides=_q(hq, 5, 3), color="wood_dark")
    mb.box((0.0, 0.0, 1.0), (1.48, 0.96, 0.015), "parchment")
    if hq:
        mb.tube((-0.64, 0.42, 0.998), (0.58, -0.26, 0.998), 0.006, sides=3, color="gem_red")
        for x, y in ((-0.3, 0.26), (0.1, -0.05), (0.42, 0.2)):
            mb.box((x, y, 1.012), (0.13, 0.1, 0.01), "liftstone_dark")
        with mb.xf(Matrix.Translation((0.62, -0.3, 0.99))):
            mb.lathe([(0.1, 0.0), (0.1, 0.03), (0.04, 0.06)], 8, "brass", smooth=False)
            mb.sphere((0, 0, 0.09), 0.04, 6, 3, "liftstone", smooth=False)
        with mb.xf(Matrix.Translation((-0.68, 0.34, 1.03)) @ Matrix.Rotation(0.4, 4, "Z") @ _x_axis()):
            mb.lathe([(0.035, -0.32), (0.035, 0.32)], 6, "parchment", smooth=False)
    mb.socket("reader", (0, -0.85, 0))


def winch_controls(mb, hq):
    """Act I boss objective: fight to this panel and pull the release to free your ship."""
    mb.box((0, 0, 0.55), (1.4, 0.55, 1.1), "iron", top_scale=0.86)
    mb.box((0, -0.05, 1.15), (1.5, 0.6, 0.1), "rust_dark")
    for x, c in ((-0.32, "gem_red"), (0.0, "iron_light"), (0.32, "iron_light")):
        mb.tube((x, -0.05, 1.18), (x, -0.27, 1.72), 0.026, sides=_q(hq, 5, 3), color="iron_light")
        mb.sphere((x, -0.27, 1.75), 0.07, _q(hq, 6, 4), 3, c, smooth=False)
    if hq:
        with mb.xf(Matrix.Translation((0.42, -0.29, 0.72)) @ Matrix.Rotation(math.pi / 2, 4, "X")):
            mb.lathe([(0.16, -0.02), (0.16, 0.02)], 10, "brass", smooth=False)
        mb.box((-0.34, -0.285, 0.72), (0.34, 0.02, 0.18), "ember")
    mb.socket("release", (-0.32, -0.27, 1.75))
    mb.socket("operator", (0, -0.85, 0))


def cell_door(mb, hq):
    """Below-deck brig door. Slides on +X. Half-size bars keep the alpha-free silhouette cheap."""
    h, w = 2.4, 1.3
    mb.box((0, 0, 0.06), (w, 0.14, 0.12), "iron")
    mb.box((0, 0, h - 0.06), (w, 0.14, 0.12), "iron")
    mb.box((0, 0, h * 0.5), (w, 0.12, 0.1), "iron")
    for sign in (1, -1):
        mb.box((sign * (w / 2 - 0.05), 0, h / 2), (0.1, 0.14, h), "iron")
    bars = _q(hq, 6, 3)
    for i in range(bars):
        x = -w * 0.34 + i * (w * 0.68 / max(1, bars - 1))
        mb.tube((x, 0, 0.1), (x, 0, h - 0.1), 0.024, sides=_q(hq, 5, 3), color="iron_light")
    mb.box((w * 0.4, -0.1, h * 0.5), (0.2, 0.06, 0.26), "brass")
    mb.socket("lock", (w * 0.4, -0.13, h * 0.5))


def armada_banner(mb, hq):
    """Gilded Armada standard. Dresses decks and the war room; the atlas sets its allegiance."""
    mb.tube((0, 0, 0), (0, 0, 3.6), 0.05, 0.04, sides=_q(hq, 6, 4), color="gold_dark")
    mb.sphere((0, 0, 3.66), 0.09, _q(hq, 6, 4), 3, "gold", smooth=False)
    mb.tube((-0.75, 0, 3.4), (0.75, 0, 3.4), 0.024, sides=_q(hq, 4, 3), color="gold_dark")
    mb.plate([(-0.7, 0, 3.38), (0.7, 0, 3.38), (0.7, 0, 1.25), (0, 0, 0.8), (-0.7, 0, 1.25)], 0.02, "faction_a")
    mb.plate([(-0.42, -0.02, 3.0), (0.42, -0.02, 3.0), (0.42, -0.02, 1.75), (0, -0.02, 1.3), (-0.42, -0.02, 1.75)], 0.014, "faction_c")
    if hq:
        mb.plate([(0, -0.035, 2.6), (0.3, -0.035, 2.95), (0.2, -0.035, 2.3), (0, -0.035, 1.75), (-0.2, -0.035, 2.3), (-0.3, -0.035, 2.95)], 0.01, "faction_b")
    mb.socket("base", (0, 0, 0))


def hanging_lantern(mb, hq):
    """Warm hub lamp. Hang by 'rope'; the emissive atlas carries its light with no real-time lights."""
    sides = _q(hq, 8, 4)
    mb.lathe([(0.12, 0.0), (0.14, 0.03)], sides, "iron", smooth=False)
    mb.lathe([(0.12, 0.04), (0.14, 0.26), (0.08, 0.32)], sides, "lamp", smooth=False)
    mb.lathe([(0.14, 0.32), (0.04, 0.42)], sides, "iron", smooth=False)
    if hq:
        for i in range(4):
            a = 2 * math.pi * i / 4
            mb.tube((0.145 * math.cos(a), 0.145 * math.sin(a), 0.03), (0.145 * math.cos(a), 0.145 * math.sin(a), 0.32), 0.01, sides=3, color="iron")
    with mb.xf(Matrix.Translation((0, 0, 0.47)) @ _y_axis()):
        mb.lathe([(0.05, -0.008), (0.05, 0.008)], _q(hq, 6, 4), "iron", smooth=False)
    mb.socket("rope", (0, 0, 0.52))


def rope_coil(mb, hq):
    """Deck dressing around the hub and boarding decks."""
    rings = _q(hq, 4, 2)
    sides = _q(hq, 12, 6)
    for i in range(rings):
        r = 0.42 - i * 0.03
        z = 0.05 + i * 0.09
        mb.lathe([(r - 0.09, z - 0.05), (r, z - 0.03), (r + 0.01, z + 0.03), (r - 0.09, z + 0.05)], sides, "rope", smooth=hq)


def wreck_chunk(mb, hq):
    """Falling debris for ship deaths and the Scrap-Winds field: a torn section of hull with its
    ribs exposed. Rotate freely; works any way up."""
    rng = random.Random(23)
    stations = _q(hq, 5, 3)
    rings = []
    for i in range(stations + 1):
        k = i / stations
        y = -1.7 + 3.4 * k
        # Both ends tear off at an angle and the top edge is jagged.
        tear = rng.uniform(0.0, 0.9) if 0 < i < stations else 0.2
        rings.append([(-1.5, y, 2.2 - tear), (-1.25, y, 0.8), (-0.55, y, 0.05), (0.55, y, 0.05), (1.25, y, 0.8), (1.5, y, 2.1 - tear * 0.6), (1.0, y + 0.03, 1.2), (-1.0, y + 0.03, 1.2)])
    def paint(i, j):
        if j in (6, 7):
            return "abyss"
        return "wood_dark" if (i + j) % 3 == 0 else ("wood_mid" if j % 2 else "faction_a" if j == 4 else "wood_mid")
    mb.loft(rings, paint)
    for y in _q(hq, (-1.3, -0.3, 0.7, 1.5), (-0.8, 0.9)):
        h = rng.uniform(2.6, 3.4)
        for sign in (1, -1):
            mb.tube((sign * 1.42, y, 1.6), (sign * 1.65, y + rng.uniform(-0.15, 0.15), h), 0.07, 0.012, sides=_q(hq, 4, 3), color="wood_light")
    if hq:
        mb.tube((-1.5, -1.7, 1.2), (-2.3, -2.6, 2.1), 0.06, 0.02, sides=4, color="iron")
        mb.sphere((0.5, 1.0, 1.15), (0.5, 0.42, 0.14), 6, 3, "ember", smooth=False)
    mb.socket("fire", (0.5, 1.0, 1.25))


# ---- Signature weapons ----------------------------------------------------------------------

def _curved(mb, edge, spine, thick, color):
    mb.plate(edge + list(reversed(spine)), thick, color)


def boarding_hook_sabre(mb, hq):
    """Vane's blade: a boarding cutlass with a hooked back, the hero's silhouette in one object."""
    if hq:
        mb.sphere((0, 0, 0.02), 0.03, 6, 3, "brass")
        mb.tube((0, 0, 0.04), (0, 0, 0.18), 0.02, 0.022, sides=6, color="leather_dark")
        mb.box((0, 0, 0.19), (0.17, 0.035, 0.024), "brass")
        mb.path([(0.08, 0, 0.19), (0.13, 0, 0.1), (0.05, 0, 0.03)], [0.01, 0.01, 0.01], 4, "brass")
        mb.plate([(-0.03, 0, 0.2), (0.03, 0, 0.2), (0.055, 0, 0.5), (0.08, 0, 0.72), (0.095, 0, 0.9), (0.06, 0, 0.88), (-0.03, 0, 0.72), (-0.115, 0, 0.8), (-0.13, 0, 0.72), (-0.04, 0, 0.6)], 0.009, "iron_light")
    else:
        mb.tube((0, 0, 0.0), (0, 0, 0.18), 0.024, sides=4, color="leather_dark")
        mb.box((0, 0, 0.19), (0.17, 0.03, 0.03), "brass")
        mb.plate([(-0.03, 0, 0.2), (0.03, 0, 0.2), (0.095, 0, 0.9), (0.0, 0, 0.74), (-0.13, 0, 0.76), (-0.04, 0, 0.6)], 0.012, "iron_light")
    mb.socket("grip", (0, 0, 0.11))
    mb.socket("trail_tip", (0.095, 0, 0.9))


def royal_sabre(mb, hq):
    """Cassian's sword: gold basket hilt and a long elegant blade."""
    if hq:
        mb.sphere((0, 0, 0.02), 0.034, 6, 3, "gold")
        mb.tube((0, 0, 0.04), (0, 0, 0.19), 0.019, 0.021, sides=6, color="velvet")
        mb.path([(0.09, 0, 0.21), (0.12, 0, 0.12), (0.07, 0, 0.03)], [0.01, 0.012, 0.01], 4, "gold")
        mb.path([(-0.09, 0, 0.21), (-0.12, 0, 0.12), (-0.07, 0, 0.03)], [0.01, 0.012, 0.01], 4, "gold")
        mb.lathe([(0.13, 0.19), (0.13, 0.21), (0.03, 0.23)], 8, "gold", smooth=False)
        mb.plate([(-0.02, 0, 0.22), (0.02, 0, 0.22), (0.022, 0, 0.8), (0.045, 0, 1.0), (0.05, 0, 1.08), (0.012, 0, 0.98), (-0.018, 0, 0.8)], 0.008, "silver")
        mb.plate([(-0.008, -0.005, 0.26), (0.008, -0.005, 0.26), (0.006, -0.005, 0.72), (-0.006, -0.005, 0.72)], 0.003, "gold")
    else:
        mb.tube((0, 0, 0.0), (0, 0, 0.19), 0.023, sides=4, color="velvet")
        mb.lathe([(0.13, 0.19), (0.03, 0.23)], 5, "gold", smooth=False)
        mb.plate([(-0.02, 0, 0.22), (0.02, 0, 0.22), (0.05, 0, 1.08), (-0.018, 0, 0.8)], 0.012, "silver")
    mb.socket("grip", (0, 0, 0.11))
    mb.socket("trail_tip", (0.05, 0, 1.08))


def duel_pistol(mb, hq):
    """Ornate pistol for the Lift-Core duel, oriented for gun.R or gun.L like SM_Prop_Flintlock."""
    upright = Matrix(((0, 0, 1, 0), (-1, 0, 0, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
    with mb.xf(upright):
        z = 0.21
        sides = _q(hq, 8, 4)
        mb.tube((0, 0.1, z), (0, -0.33, z), 0.016, 0.018, sides=sides, color="silver")
        if hq:
            mb.path([(0, -0.32, z), (0, -0.33, z), (0, -0.345, z)], [0.023, 0.023, 0.02], 8, "gold")
            mb.path([(0, -0.16, z - 0.018), (0, -0.05, z - 0.022), (0, 0.05, z - 0.022)], [0.012, 0.012, 0.012], 4, "gold")
            mb.box((0.022, 0.05, z + 0.012), (0.012, 0.09, 0.032), "gold")
            mb.tube((0.022, 0.085, z + 0.02), (0.022, 0.05, z + 0.06), 0.006, sides=3, color="gold")
        mb.path([(0, 0.08, z - 0.018), (0, 0.13, z - 0.06), (0, 0.17, z - 0.17), (0, 0.17, z - 0.2)], [0.02, 0.024, 0.03, 0.033], sides, "velvet")
        mb.socket("grip", (0, 0.15, z - 0.12))
        mb.socket("muzzle", (0, -0.345, z))


def anchor_hammer(mb, hq):
    """Krag's weapon: a two-metre ship's anchor swung by hand, with a chain wrapped round the shaft."""
    h = 1.65
    mb.tube((0, 0, 0.0), (0, 0, h), 0.04, 0.04, sides=_q(hq, 6, 4), color="iron")
    with mb.xf(Matrix.Translation((0, 0, 0.0))):
        mb.tube((0, 0, 0.12), (0, 0, 0.4), 0.05, sides=_q(hq, 6, 4), color="leather_dark")
    arc = [(-0.5, 0, h - 0.2), (-0.32, 0, h + 0.12), (0, 0, h + 0.2), (0.32, 0, h + 0.12), (0.5, 0, h - 0.2)]
    mb.path(arc, [0.012, 0.09, 0.12, 0.09, 0.012], _q(hq, 5, 3), "iron_light")
    mb.tube((-0.28, 0, h - 0.45), (0.28, 0, h - 0.45), 0.032, sides=_q(hq, 4, 3), color="rust_dark")
    if hq:
        for sign in (1, -1):
            mb.plate([(sign * 0.5, 0, h - 0.1), (sign * 0.36, 0, h - 0.36), (sign * 0.66, 0, h - 0.36)], 0.03, "iron_light")
        for i in range(6):
            z = 0.55 + i * 0.13
            mb.lathe([(0.052, z), (0.052, z + 0.05)], 6, "rust", smooth=False)
    mb.socket("grip", (0, 0, 0.27))
    mb.socket("trail_tip", (0.5, 0, h - 0.2))


def twin_scimitar(mb, hq):
    """Carried in pairs by Vex and Vesper on weapon.R and weapon.L. The fuller glows plasma."""
    if hq:
        mb.tube((0, 0, 0.02), (0, 0, 0.16), 0.018, 0.02, sides=6, color="faction_c")
        mb.sphere((0, 0, 0.02), 0.026, 6, 3, "silver")
        mb.path([(-0.09, 0, 0.21), (0, 0, 0.17), (0.09, 0, 0.21)], [0.012, 0.018, 0.012], 4, "silver")
        mb.plate([(-0.02, 0, 0.18), (0.022, 0, 0.18), (0.08, 0, 0.42), (0.16, 0, 0.66), (0.18, 0, 0.76), (0.11, 0, 0.72), (0.02, 0, 0.56), (-0.018, 0, 0.36)], 0.007, "faction_b")
        mb.plate([(0.01, -0.005, 0.26), (0.03, -0.005, 0.26), (0.11, -0.005, 0.6), (0.09, -0.005, 0.6)], 0.003, "plasma")
    else:
        mb.tube((0, 0, 0.0), (0, 0, 0.17), 0.022, sides=4, color="faction_c")
        mb.plate([(-0.02, 0, 0.18), (0.022, 0, 0.18), (0.18, 0, 0.76), (0.02, 0, 0.56)], 0.012, "faction_b")
    mb.socket("grip", (0, 0, 0.1))
    mb.socket("trail_tip", (0.18, 0, 0.76))


def warden_flail(mb, hq):
    """Malakor's weapon: a prison key-ring gone wrong. The mace head is a cage full of keys."""
    h = 0.85
    mb.tube((0, 0, 0.0), (0, 0, h), 0.03, 0.035, sides=_q(hq, 6, 4), color="iron")
    mb.tube((0, 0, 0.05), (0, 0, 0.24), 0.036, sides=_q(hq, 6, 4), color="leather_dark")
    head = h + 0.14
    mb.sphere((0, 0, head), 0.17, _q(hq, 8, 5), _q(hq, 5, 3), "iron_light", smooth=False)
    spikes = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0.7, 0.7, 0.5), (-0.7, -0.7, 0.5), (0.7, -0.7, -0.4), (-0.7, 0.7, -0.4)) if hq else ((1, 0, 0), (-1, 0, 0), (0, 0, 1))
    for dx, dy, dz in spikes:
        n = (dx * dx + dy * dy + dz * dz) ** 0.5
        ux, uy, uz = dx / n, dy / n, dz / n
        mb.tube((ux * 0.14, uy * 0.14, head + uz * 0.14), (ux * 0.33, uy * 0.33, head + uz * 0.33), 0.045, 0.006, sides=_q(hq, 4, 3), color="iron")
    if hq:
        for sign in (1, -1):
            mb.box((sign * 0.05, -0.04, h - 0.1), (0.018, 0.012, 0.14), "brass")
            mb.box((sign * 0.05, -0.04, h - 0.16), (0.045, 0.012, 0.018), "brass")
    mb.socket("grip", (0, 0, 0.14))
    mb.socket("trail_tip", (0.33, 0, head))


def hand_mortar(mb, hq):
    """Rook's sidearm: a flared blunderbuss. Oriented for gun.R like the flintlock."""
    upright = Matrix(((0, 0, 1, 0), (-1, 0, 0, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
    with mb.xf(upright):
        z = 0.2
        mb.path([(0, 0.14, z), (0, -0.05, z), (0, -0.34, z), (0, -0.44, z)], [0.038, 0.034, 0.04, 0.085], _q(hq, 8, 5), "brass")
        mb.path([(0, 0.13, z - 0.015), (0, 0.2, z - 0.07), (0, 0.27, z - 0.2), (0, 0.27, z - 0.24)], [0.028, 0.03, 0.036, 0.036], _q(hq, 6, 4), "wood_mid")
        if hq:
            mb.box((0.036, 0.1, z + 0.016), (0.012, 0.09, 0.036), "iron")
            for y in (-0.13, -0.25):
                with mb.xf(Matrix.Translation((0, y, z)) @ _y_axis()):
                    mb.lathe([(0.044, -0.012), (0.044, 0.012)], 8, "iron", smooth=False)
        mb.socket("grip", (0, 0.24, z - 0.15))
        mb.socket("muzzle", (0, -0.44, z))


def sable_dagger(mb, hq):
    """Sable's parrying dagger. Short, so it reads best in pairs; poison stripe along the blade."""
    if hq:
        mb.sphere((0, 0, 0.018), 0.022, 6, 3, "iron")
        mb.tube((0, 0, 0.03), (0, 0, 0.13), 0.016, sides=6, color="cloth_black")
        mb.path([(-0.06, 0, 0.145), (0, 0, 0.135), (0.06, 0, 0.17)], [0.008, 0.012, 0.008], 4, "iron_light")
        mb.plate([(-0.018, 0, 0.145), (0.018, 0, 0.145), (0.01, 0, 0.4), (0, 0, 0.47), (-0.01, 0, 0.4)], 0.008, "iron_light")
        mb.plate([(-0.004, -0.005, 0.17), (0.004, -0.005, 0.17), (0.002, -0.005, 0.38), (-0.002, -0.005, 0.38)], 0.002, "toxic")
        mb.plate([(-0.008, 0, 0.41), (0.008, 0, 0.41), (0, 0, 0.465)], 0.01, "faction_c")  # Blood on the tip.
    else:
        mb.tube((0, 0, 0.0), (0, 0, 0.135), 0.018, sides=4, color="cloth_black")
        mb.plate([(-0.02, 0, 0.14), (0.02, 0, 0.14), (0, 0, 0.47)], 0.012, "iron_light")
    mb.socket("grip", (0, 0, 0.08))
    mb.socket("trail_tip", (0, 0, 0.47))


def spyglass(mb, hq):
    """Morrow's and Lyra's sidearm of choice. A hub prop and a held item on weapon.R."""
    mb.lathe([(0.04, 0.0), (0.04, 0.16), (0.032, 0.17), (0.032, 0.32), (0.026, 0.33), (0.026, 0.48)], _q(hq, 8, 4), lambda i, _j: "brass" if i % 2 == 0 else "leather_dark", smooth=False)
    if hq:
        mb.lathe([(0.044, -0.004), (0.044, 0.018)], 8, "gold", smooth=False)
        mb.lathe([(0.03, 0.47), (0.03, 0.49)], 8, "gold", smooth=False)
    mb.socket("grip", (0, 0, 0.08))


def big_wrench(mb, hq):
    """Dr. Thorne's only weapon."""
    mb.tube((0, 0, 0.0), (0, 0, 0.56), 0.025, 0.03, sides=_q(hq, 6, 4), color="iron_light")
    mb.tube((0, 0, 0.03), (0, 0, 0.2), 0.032, sides=_q(hq, 6, 4), color="wood_red")
    mb.plate([(-0.045, 0, 0.54), (-0.1, 0, 0.62), (-0.1, 0, 0.76), (-0.04, 0, 0.74), (-0.04, 0, 0.66), (0.04, 0, 0.66), (0.04, 0, 0.74), (0.1, 0, 0.76), (0.1, 0, 0.62), (0.045, 0, 0.54)], 0.04, "iron_light")
    if hq:
        with mb.xf(Matrix.Translation((0, 0, 0.47)) @ _x_axis()):
            mb.lathe([(0.034, -0.018), (0.034, 0.018)], 6, "brass", smooth=False)
    mb.socket("grip", (0, 0, 0.11))
    mb.socket("trail_tip", (0.1, 0, 0.76))


def shadow_staff(mb, hq):
    """Dr. Thorne's staff: black wood, a purple wrap at the grip, and a green stone held in a claw."""
    h = 1.72
    sides = _q(hq, 6, 4)
    mb.tube((0, 0, 0), (0, 0, h), 0.02, 0.028, sides=sides, color="cloth_black")
    mb.tube((0, 0, 1.08), (0, 0, 1.32), 0.03, sides=sides, color="faction_a")
    for a in range(_q(hq, 3, 2)):
        angle = a * 6.283 / _q(hq, 3, 2)
        x, y = 0.075 * math.cos(angle), 0.075 * math.sin(angle)
        mb.tube((0, 0, h - 0.04), (x, y, h + 0.1), 0.016, 0.008, sides=4, color="cloth_black")
    mb.sphere((0, 0, h + 0.08), 0.062, _q(hq, 8, 4), _q(hq, 4, 3), "faction_b", smooth=hq)
    # Held high on the shaft, so the stone stays clear of his face in the arm's rest pose.
    mb.socket("grip", (0, 0, 1.2))
    mb.socket("trail_tip", (0, 0, h + 0.08))


def shadow_spear(mb, hq):
    """Dr. Thorne's Shadow Spear, conjured out of nothing and thrown: a shaft of black shadow banded with
    violet light and set with backward thorns, a long barbed head whose edge glows, and a spiked butt.
    Lies tip up along +Z, so it can be pointed at a target and thrown."""
    sides = _q(hq, 6, 4)
    mb.tube((0, 0, 0.12), (0, 0, 1.62), 0.024, 0.02, sides=sides, color="abyss")
    mb.tube((0, 0, 0.11), (0, 0, -0.06), 0.024, 0.003, sides=sides, color="abyss")
    mb.tube((0, 0, 1.58), (0, 0, 1.7), 0.03, 0.042, sides=sides, color="cloth_black")
    for z in ((0.35, 0.75, 1.15, 1.45) if hq else (0.6, 1.2)):
        mb.tube((0, 0, z - 0.015), (0, 0, z + 0.015), 0.03, sides=sides, color="plasma")
    if hq:
        for k in range(6):
            a = k * 2.4
            z = 0.3 + k * 0.2
            mb.tube((0.02 * math.cos(a), 0.02 * math.sin(a), z), (0.075 * math.cos(a), 0.075 * math.sin(a), z - 0.08), 0.012, 0.002, sides=3, color="abyss")
    blade = [(0, 1.66), (0.085, 1.78), (0.06, 2.0), (0, 2.32), (-0.06, 2.0), (-0.085, 1.78)]
    # Two blades crossed, so the head reads from any angle in flight. The glow is the edge of a plate
    # left showing round a thicker black one.
    for turn in ((0.0, math.pi / 2) if hq else (0.0,)):
        with mb.xf(Matrix.Rotation(turn, 4, "Z")):
            mb.plate([(x, 0, z) for x, z in blade], 0.02, "plasma")
            mb.plate([(x * 0.72, 0, 1.66 + (z - 1.66) * 0.9) for x, z in blade], 0.034, "abyss")
            for sign in (1, -1):
                mb.plate([(sign * 0.07, 0, 1.75), (sign * 0.16, 0, 1.6), (sign * 0.05, 0, 1.69)], 0.016, "abyss")
    mb.socket("grip", (0, 0, 0.95))
    mb.socket("trail_tip", (0, 0, 2.32))


def lightning_staff(mb, hq):
    """Ivo's lightning catcher: a makeshift staff of storm-worn wood bound in copper, a copper wire spiralling
    up it, and three brass lightning-rod tines at the top cradling a glass orb of caught, crackling light."""
    h = 1.62
    sides = _q(hq, 6, 4)
    mb.tube((0, 0, 0), (0, 0, h), 0.022, 0.026, sides=sides, color="wood_mid")
    mb.tube((0, 0, -0.03), (0, 0, 0.06), 0.03, sides=sides, color="iron")  # A grounding ferrule.
    mb.tube((0, 0, 1.0), (0, 0, 1.28), 0.032, sides=sides, color="leather")  # The grip, wrapped in leather.
    for z in ((0.3, 0.62, 0.9, 1.38, 1.5) if hq else (0.6, 1.4)):
        mb.tube((0, 0, z - 0.02), (0, 0, z + 0.02), 0.034, sides=sides, color="rust")
    if hq:
        # A copper wire wound loosely up the shaft.
        coil = [(0.03 * math.cos(k * 1.3), 0.03 * math.sin(k * 1.3), 0.08 + k * 0.075) for k in range(12)]
        mb.path(coil, [0.006] * len(coil), 3, "rust")
    # The head: a brass collar, three tines flaring out, and the orb they hold.
    mb.tube((0, 0, h - 0.02), (0, 0, h + 0.05), 0.03, 0.04, sides=sides, color="brass")
    for k in range(3):
        a = k * 2 * math.pi / 3
        x, y = math.cos(a), math.sin(a)
        mb.path([(0.035 * x, 0.035 * y, h + 0.04), (0.08 * x, 0.08 * y, h + 0.12), (0.06 * x, 0.06 * y, h + 0.24)], [0.011, 0.009, 0.004], _q(hq, 4, 3), "brass")
    mb.sphere((0, 0, h + 0.13), 0.052, _q(hq, 8, 4), _q(hq, 4, 3), "lightning", smooth=hq)
    if hq:
        # Sparks jumping from tine to tine.
        for k in range(3):
            a0, a1 = k * 2 * math.pi / 3 + 0.35, (k + 1) * 2 * math.pi / 3 - 0.35
            p0 = (0.075 * math.cos(a0), 0.075 * math.sin(a0), h + 0.18)
            mid = (0.1 * math.cos((a0 + a1) / 2), 0.1 * math.sin((a0 + a1) / 2), h + 0.2)
            p1 = (0.075 * math.cos(a1), 0.075 * math.sin(a1), h + 0.17)
            mb.path([p0, mid, p1], [0.006, 0.008, 0.005], 3, "lightning")
    mb.socket("grip", (0, 0, 1.14))
    mb.socket("trail_tip", (0, 0, h + 0.13))


def linstock(mb, hq):
    """Hask's linstock: a plain wooden staff with an iron butt spike, a forked iron head with a short spear
    point between the prongs, and hemp slow-match wound round the shaft, clamped in the prongs, its end
    smouldering a hot orange. Shots go off from the glowing match."""
    h = 1.02
    sides = _q(hq, 6, 4)
    mb.tube((0, 0, 0.05), (0, 0, h), 0.02, 0.017, sides=sides, color="wood_mid")
    mb.tube((0, 0, -0.06), (0, 0, 0.06), 0.004, 0.024, sides=sides, color="iron")  # Butt spike, for planting on deck.
    mb.tube((0, 0, 0.42), (0, 0, 0.62), 0.025, sides=sides, color="leather")  # Grip, worn smooth.
    # The iron head: a socket, two prongs curling out like a serpent's jaws, and a spear point between them.
    mb.tube((0, 0, h - 0.05), (0, 0, h + 0.02), 0.024, 0.02, sides=sides, color="iron")
    mb.tube((0, 0, h + 0.02), (0, 0, h + 0.17), 0.012, 0.001, sides=_q(hq, 4, 3), color="iron_light")  # A true point leaves degenerate tris.
    tips = []
    for sign in (1, -1):
        prong = [(0, 0, h + 0.01), (sign * 0.05, 0, h + 0.04), (sign * 0.075, 0, h + 0.1), (sign * 0.06, 0, h + 0.14)]
        if not hq:
            prong = [prong[0], prong[2], prong[3]]
        mb.path(prong, [0.011, 0.01, 0.008, 0.006][-len(prong):], _q(hq, 4, 3), "iron")
        tips.append(prong[-1])
    # The slow-match: wound down the shaft, up to each prong, ends glowing.
    if hq:
        coil = [(0.026 * math.cos(k * 1.4), 0.026 * math.sin(k * 1.4), h - 0.08 - k * 0.022) for k in range(10)]
        mb.path(coil, [0.008] * len(coil), 3, "rope")
        for x, _, z in tips:
            mb.path([coil[0], (x * 0.6, -0.01, z - 0.07), (x * 1.05, -0.006, z + 0.02)], [0.008, 0.008, 0.007], 3, "rope")
    else:
        mb.tube((0, 0, h - 0.2), (0, 0, h - 0.06), 0.026, sides=sides, color="rope")
    glow = (tips[0][0] * 1.05, -0.006, tips[0][2] + 0.02)
    mb.sphere(glow, 0.02, _q(hq, 6, 4), 3, "ember", smooth=False)
    if hq:
        mb.sphere((tips[1][0] * 1.05, -0.006, tips[1][2] + 0.03), 0.012, 4, 3, "ember", smooth=False)
    mb.socket("grip", (0, 0, 0.52))
    mb.socket("trail_tip", (0, 0, h + 0.17))
    mb.socket("muzzle", glow)


def bone_saw(mb, hq):
    """Wren's bone saw: a turned wooden handle with a brass ferrule, and a curved steel blade, toothed along
    its inner edge and spotted with old blood."""
    sides = _q(hq, 8, 4)
    mb.lathe([(0.018, 0.0), (0.024, 0.02), (0.019, 0.045), (0.025, 0.075), (0.02, 0.11), (0.024, 0.13)] if hq else [(0.02, 0.0), (0.024, 0.07), (0.022, 0.13)], sides, "wood_mid", smooth=False)
    mb.tube((0, 0, 0.13), (0, 0, 0.155), 0.022, 0.018, sides=sides, color="brass")
    # The blade sweeps up and curves forward, in the XZ plane.
    spine = [(0.0, 0.15), (0.012, 0.26), (0.032, 0.36), (0.065, 0.45), (0.11, 0.51)]
    edge = [(-0.038, 0.16), (-0.03, 0.26), (-0.01, 0.35), (0.025, 0.43), (0.11, 0.51)]
    outline = [(x, 0.0, z) for x, z in spine] + [(x, 0.0, z) for x, z in edge[-2::-1]]
    mb.plate(outline, 0.004, "silver")
    if hq:
        for (x0, z0), (x1, z1) in zip(edge[:-1], edge[1:]):
            for k in range(3):
                a, b = k / 3, (k + 0.5) / 3
                p0 = (x0 + (x1 - x0) * a, 0.0, z0 + (z1 - z0) * a)
                p1 = (x0 + (x1 - x0) * b - 0.008, 0.0, z0 + (z1 - z0) * b)
                mb.tube(p0, p1, 0.003, 0.001, sides=3, color="steel")
        for x, z in ((0.005, 0.3), (0.04, 0.42)):
            mb.box((x, -0.003, z), (0.02, 0.002, 0.014), "velvet")
    mb.socket("grip", (0, 0, 0.07))
    mb.socket("trail_tip", (0.11, 0, 0.51))


def scrap_cutlass(mb, hq):
    """Vane's Act 1 blade: a notched, rust-pitted boarding cutlass with a plain iron cross-guard and a grip
    bound in tarred cord. No scabbard; it lives shoved through a belt loop. Edge faces -X, like every cutlass."""
    sides = _q(hq, 6, 4)
    mb.tube((0, 0, 0.0), (0, 0, 0.035), 0.016, 0.024, sides=sides, color="iron")
    mb.tube((0, 0, 0.035), (0, 0, 0.17), 0.02, sides=sides, color="rope")
    if hq:
        for z in (0.06, 0.1, 0.14):
            mb.tube((0, 0, z - 0.008), (0, 0, z + 0.008), 0.023, sides=sides, color="leather_dark")
    mb.box((0, 0, 0.18), (0.13, 0.03, 0.02), "iron")
    if hq:
        outline = [(-0.024, 0.19), (0.024, 0.19), (0.05, 0.5), (0.09, 0.74), (0.11, 0.86), (0.075, 0.85), (0.04, 0.8), (0.03, 0.77),
                   (0.012, 0.72), (0.0, 0.66), (0.012, 0.64), (-0.012, 0.6), (-0.016, 0.52), (-0.002, 0.5), (-0.024, 0.45),
                   (-0.024, 0.34), (-0.01, 0.32), (-0.024, 0.3)]
        mb.plate([(x, 0, z) for x, z in outline], 0.008, "rust")
        for x, z in ((0.03, 0.4), (0.06, 0.62), (0.015, 0.28)):
            mb.box((x, -0.004, z), (0.022, 0.002, 0.018), "rust_dark")
    else:
        mb.plate([(-0.025, 0, 0.19), (0.025, 0, 0.19), (0.11, 0, 0.86), (0.05, 0, 0.83)], 0.012, "rust")
    mb.socket("grip", (0, 0, 0.1))
    mb.socket("trail_tip", (0.1, 0, 0.86))


def captain_cutlass(mb, hq):
    """Vane's Act 2 blade: a masterwork cutlass, polished steel with a steel basket hilt, a black leather grip
    and a brass pommel. Edge faces -X."""
    sides = _q(hq, 6, 4)
    mb.sphere((0, 0, 0.02), 0.028, sides, 3, "brass", smooth=False)
    mb.tube((0, 0, 0.04), (0, 0, 0.18), 0.018, 0.02, sides=sides, color="leather_dark")
    mb.box((0, 0, 0.19), (0.14, 0.035, 0.02), "silver")
    # The basket: bars sweeping from the guard round the knuckles to the pommel.
    for dy in ((-0.035, 0.0, 0.035) if hq else (0.0,)):
        mb.path([(0.07, dy, 0.19), (0.115, dy * 1.3, 0.12), (0.09, dy, 0.05), (0.03, dy * 0.5, 0.02)], [0.008, 0.008, 0.008, 0.007], _q(hq, 4, 3), "silver")
    if hq:
        mb.plate([(-0.024, 0, 0.2), (0.024, 0, 0.2), (0.05, 0, 0.5), (0.09, 0, 0.76), (0.11, 0, 0.9), (0.075, 0, 0.9), (0.012, 0, 0.74), (-0.024, 0, 0.46)], 0.008, "silver")
        mb.plate([(0.0, -0.005, 0.24), (0.012, -0.005, 0.24), (0.04, -0.005, 0.5), (0.03, -0.005, 0.5)], 0.002, "steel")
    else:
        mb.plate([(-0.025, 0, 0.2), (0.025, 0, 0.2), (0.11, 0, 0.9), (0.05, 0, 0.86)], 0.012, "silver")
    mb.socket("grip", (0, 0, 0.11))
    mb.socket("trail_tip", (0.1, 0, 0.9))


def king_cutlass(mb, hq):
    """Vane's Act 3 blade: a legendary cutlass with a swept golden guard, a crimson grip, and gold runes etched
    down a long polished blade. Edge faces -X."""
    sides = _q(hq, 6, 4)
    mb.sphere((0, 0, 0.02), 0.032, sides, 3, "gold", smooth=False)
    mb.tube((0, 0, 0.04), (0, 0, 0.19), 0.019, 0.021, sides=sides, color="gem_red")
    if hq:
        for z in (0.08, 0.15):
            mb.tube((0, 0, z - 0.006), (0, 0, z + 0.006), 0.024, sides=sides, color="gold")
    mb.box((0, 0, 0.2), (0.16, 0.035, 0.022), "gold")
    for sign in ((1, -1) if hq else (1,)):
        mb.path([(sign * 0.08, 0, 0.2), (sign * 0.125, 0, 0.13), (sign * 0.095, 0, 0.05), (sign * 0.03, 0, 0.02)] if sign > 0 else [(-0.08, 0, 0.2), (-0.11, 0, 0.25), (-0.09, 0, 0.29)],
                [0.01, 0.011, 0.01, 0.008] if sign > 0 else [0.01, 0.008, 0.004], _q(hq, 4, 3), "gold")
    if hq:
        mb.plate([(-0.026, 0, 0.21), (0.026, 0, 0.21), (0.055, 0, 0.55), (0.1, 0, 0.82), (0.12, 0, 0.98), (0.08, 0, 0.97), (0.012, 0, 0.8), (-0.026, 0, 0.5)], 0.008, "silver")
        for k in range(5):
            z = 0.28 + 0.11 * k
            x = 0.008 + 0.04 * (z - 0.21) / 0.6
            mb.box((x, -0.005, z), (0.014, 0.002, 0.03 if k % 2 else 0.018), "gold")
    else:
        mb.plate([(-0.026, 0, 0.21), (0.026, 0, 0.21), (0.12, 0, 0.98), (0.05, 0, 0.92)], 0.012, "silver")
    mb.socket("grip", (0, 0, 0.11))
    mb.socket("trail_tip", (0.11, 0, 0.98))


def sword_cane(mb, hq):
    """Ashgrave's sword-cane, half-drawn: a silver skull pommel on a black grip, a slender blade showing, and the
    black lacquered cane that sheathes the rest, tipped in silver. Stands on the pommel, like every blade."""
    sides = _q(hq, 6, 4)
    mb.sphere((0, 0, 0.03), (0.028, 0.03, 0.032), sides, _q(hq, 4, 3), "silver", smooth=hq)
    if hq:
        for x in (-0.011, 0.011):
            mb.sphere((x, -0.026, 0.035), 0.007, 4, 3, "eye_dark", smooth=False)
        mb.box((0, -0.02, 0.012), (0.024, 0.012, 0.008), "silver")
    mb.tube((0, 0, 0.055), (0, 0, 0.15), 0.015, 0.016, sides=sides, color="cloth_black")
    mb.tube((0, 0, 0.15), (0, 0, 0.165), 0.02, sides=sides, color="silver")
    mb.plate([(-0.008, 0, 0.165), (0.008, 0, 0.165), (0.007, 0, 0.42), (-0.007, 0, 0.42)], 0.004, "silver")
    mb.tube((0, 0, 0.42), (0, 0, 0.44), 0.019, sides=sides, color="silver")
    mb.tube((0, 0, 0.44), (0, 0, 0.92), 0.017, 0.014, sides=sides, color="cloth_black")
    mb.tube((0, 0, 0.918), (0, 0, 0.95), 0.0155, 0.009, sides=sides, color="silver")  # Not sharing the sheath's end ring.
    mb.socket("grip", (0, 0, 0.1))
    mb.socket("trail_tip", (0, 0, 0.95))


def gilded_rapier(mb, hq):
    """Thrace's rapier: a long, slender blade under a gilded swept hilt, bars curling round the hand, long
    straight quillons, a black wire-bound grip and a gold pommel. Stands on the pommel, like every blade."""
    sides = _q(hq, 6, 4)
    mb.sphere((0, 0, 0.022), 0.024, sides, 3, "gold", smooth=False)
    mb.tube((0, 0, 0.04), (0, 0, 0.15), 0.014, 0.016, sides=sides, color="cloth_black")
    if hq:
        for z in (0.07, 0.1, 0.13):
            mb.tube((0, 0, z - 0.004), (0, 0, z + 0.004), 0.018, sides=sides, color="gold")
    mb.tube((-0.11, 0, 0.165), (0.11, 0, 0.165), 0.008, 0.006, sides=_q(hq, 4, 3), color="gold")
    for dy, lean in ((-0.03, 0.0), (0.0, 0.02), (0.03, 0.0)) if hq else ((0.0, 0.02),):
        mb.path([(0.03, dy, 0.17), (0.075 + lean, dy * 1.4, 0.13), (0.07, dy * 1.2, 0.07), (0.025, dy * 0.5, 0.025)], [0.006, 0.006, 0.006, 0.005], _q(hq, 4, 3), "gold")
    if hq:
        mb.path([(-0.03, 0, 0.17), (-0.06, 0, 0.21), (-0.04, 0, 0.24)], [0.006, 0.005, 0.003], 4, "gold")
    mb.plate([(-0.009, 0, 0.17), (0.009, 0, 0.17), (0.005, 0, 1.0), (0.0, 0, 1.06), (-0.005, 0, 1.0)], 0.005, "silver")
    mb.socket("grip", (0, 0, 0.09))
    mb.socket("trail_tip", (0, 0, 1.06))


def fleet_cutlass(mb, hq):
    """Ria's cutlass: bright and well kept, a polished blade under a brass guard and knuckle-bow, the grip wrapped
    in red cord. Edge faces -X, like every cutlass."""
    sides = _q(hq, 6, 4)
    mb.sphere((0, 0, 0.025), 0.027, sides, 3, "brass", smooth=False)
    mb.tube((0, 0, 0.045), (0, 0, 0.17), 0.018, 0.02, sides=sides, color="gem_red")
    if hq:
        for z in (0.07, 0.11, 0.15):
            mb.tube((0, 0, z - 0.005), (0, 0, z + 0.005), 0.022, sides=sides, color="faction_c")
    mb.box((0, 0, 0.18), (0.14, 0.03, 0.022), "brass")
    mb.path([(0.07, 0, 0.18), (0.11, 0, 0.1), (0.028, 0, 0.026)], [0.009, 0.009, 0.008], _q(hq, 4, 3), "brass")  # Meets the pommel.
    if hq:
        mb.plate([(-0.024, 0, 0.19), (0.024, 0, 0.19), (0.05, 0, 0.5), (0.09, 0, 0.74), (0.11, 0, 0.87), (0.075, 0, 0.87), (0.012, 0, 0.72), (-0.024, 0, 0.45)], 0.008, "silver")
    else:
        mb.plate([(-0.025, 0, 0.19), (0.025, 0, 0.19), (0.11, 0, 0.87), (0.05, 0, 0.84)], 0.012, "silver")
    mb.socket("grip", (0, 0, 0.1))
    mb.socket("trail_tip", (0.1, 0, 0.87))


def blunderbuss(mb, hq):
    """Mirren's blunderbuss: a short, fat brass barrel flaring into a wide bell mouth, a walnut stock and an iron
    lock. Muzzle towards +Z and top towards +X, like every gun, so it aims along the arm on the gun.R bone."""
    upright = Matrix(((0, 0, 1, 0), (-1, 0, 0, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
    with mb.xf(upright):
        z = 0.21
        sides = _q(hq, 8, 5)
        mb.tube((0, 0.1, z), (0, -0.3, z), 0.026, 0.03, sides=sides, color="brass")
        with mb.xf(Matrix.Translation((0, -0.3, z)) @ Matrix.Rotation(math.pi / 2, 4, "X")):
            # The bell starts just inside the barrel: sharing the barrel's end ring would weld into a doubled cap.
            mb.lathe([(0.027, -0.012), (0.042, 0.06), (0.072, 0.11)] if hq else [(0.027, -0.012), (0.07, 0.11)], sides, "brass", smooth=False, caps=(False, False))
            if hq:
                mb.lathe([(0.062, 0.108), (0.05, 0.1)], sides, "eye_dark", smooth=False, caps=(False, True))
        if hq:
            for y in (0.05, -0.12):
                mb.tube((0, y + 0.01, z), (0, y - 0.01, z), 0.034, sides=sides, color="brass")
            mb.box((0.03, 0.06, z + 0.012), (0.014, 0.09, 0.034), "iron")
            mb.tube((0.03, 0.085, z + 0.02), (0.03, 0.05, z + 0.065), 0.007, sides=3, color="iron_light")
        mb.path([(0, 0.08, z - 0.02), (0, 0.15, z - 0.07), (0, 0.22, z - 0.17), (0, 0.23, z - 0.22)], [0.026, 0.028, 0.034, 0.036], sides, "wood_mid")
        mb.socket("grip", (0, 0.16, z - 0.12))
        mb.socket("muzzle", (0, -0.42, z))


def regulator_key(mb, hq):
    """Odessa's Lift-Core regulator key, half wrench and half sceptre: a long brass shaft with a leather grip and a
    T-handle at the foot, an open wrench jaw at the head cradling a crystal that glows faint blue from the core."""
    sides = _q(hq, 6, 4)
    mb.tube((-0.07, 0, 0.02), (0.07, 0, 0.02), 0.014, sides=sides, color="brass")
    mb.tube((0, 0, 0.0), (0, 0, 0.98), 0.016, 0.014, sides=sides, color="brass")
    mb.tube((0, 0, 0.3), (0, 0, 0.5), 0.022, sides=sides, color="leather_dark")
    if hq:
        for z in (0.6, 0.75, 0.88):
            mb.tube((0, 0, z - 0.01), (0, 0, z + 0.01), 0.022, sides=sides, color="gold_dark")
    mb.tube((0, 0, 0.97), (0, 0, 1.02), 0.028, 0.032, sides=sides, color="brass")
    for sign in (1, -1):
        jaw = [(sign * 0.025, 0, 1.01), (sign * 0.06, 0, 1.06), (sign * 0.055, 0, 1.13), (sign * 0.03, 0, 1.15)]
        mb.path(jaw if hq else jaw[::3], [0.014, 0.013, 0.011, 0.008][: 4 if hq else 2], _q(hq, 4, 3), "brass")
    mb.sphere((0, 0, 1.09), (0.03, 0.03, 0.045), _q(hq, 6, 4), 3, "liftstone", smooth=False)
    mb.socket("grip", (0, 0, 0.4))
    mb.socket("trail_tip", (0, 0, 1.12))


def weather_staff(mb, hq):
    """Tobin's stormcaller weather-staff: a tall, weathered wooden staff topped with a brass spindle, three
    anemometer cups on arms that spin in the wind, and a brass wind vane above them."""
    h = 1.66
    sides = _q(hq, 6, 4)
    mb.tube((0, 0, 0), (0, 0, h), 0.024, 0.02, sides=sides, color="wood_mid")
    mb.tube((0, 0, -0.03), (0, 0, 0.04), 0.028, sides=sides, color="iron")
    mb.tube((0, 0, 1.0), (0, 0, 1.24), 0.03, sides=sides, color="rope")
    mb.tube((0, 0, h - 0.02), (0, 0, h + 0.2), 0.008, sides=_q(hq, 4, 3), color="brass")
    mb.sphere((0, 0, h + 0.04), 0.026, sides, 3, "brass", smooth=False)
    for k in range(3):
        a = 2 * math.pi * k / 3
        arm_end = (0.11 * math.cos(a), 0.11 * math.sin(a), h + 0.06)
        mb.tube((0, 0, h + 0.06), arm_end, 0.005, sides=3, color="brass")
        with mb.xf(Matrix.Translation(arm_end) @ Matrix.Rotation(a + math.pi / 2, 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "X")):
            mb.lathe([(0.004, -0.022), (0.026, 0.0)] if not hq else [(0.004, -0.024), (0.022, -0.012), (0.028, 0.004)], sides, "brass", smooth=False, caps=(True, False))
    # The wind vane: an arrow with a broad tail fin.
    mb.tube((-0.13, 0, h + 0.17), (0.12, 0, h + 0.17), 0.006, sides=_q(hq, 4, 3), color="brass")
    mb.plate([(0.12, 0, h + 0.17), (0.07, 0, h + 0.2), (0.07, 0, h + 0.14)], 0.005, "brass")
    mb.plate([(-0.08, 0, h + 0.17), (-0.15, 0, h + 0.24), (-0.16, 0, h + 0.11)], 0.004, "brass")
    mb.socket("grip", (0, 0, 1.12))
    mb.socket("trail_tip", (0, 0, h + 0.2))


def driftwood_lyre(mb, hq):
    """Lyra's lyre: two curved driftwood arms, a pale bone crossbar and horn tips, gold strings, and feathers
    and wind chimes hanging from the crossbar."""
    sides = _q(hq, 6, 4)
    mb.tube((0, 0, -0.1), (0, 0, 0.06), 0.02, sides=sides, color="wood_mid")  # A short handle, to hold it by.
    mb.box((0, 0, 0.12), (0.26, 0.08, 0.16), "wood_light")
    for sign in (1, -1):
        mb.path([(sign * 0.1, 0, 0.16), (sign * 0.18, 0, 0.32), (sign * 0.11, 0, 0.5)], [0.03, 0.026, 0.02], sides, "wood_light")
        mb.tube((sign * 0.11, 0, 0.5), (sign * 0.16, 0, 0.6), 0.018, 0.003, sides=sides, color="enamel")
    mb.tube((-0.14, 0, 0.47), (0.14, 0, 0.47), 0.014, sides=sides, color="enamel")
    for x in (-0.06, -0.02, 0.02, 0.06) if hq else (-0.04, 0.04):
        mb.tube((x, -0.01, 0.2), (x, -0.01, 0.47), 0.003, sides=3, color="gold")
    for sign, color in ((1, "enamel"), (-1, "wood_light")):
        mb.tube((sign * 0.13, -0.01, 0.465), (sign * 0.14, -0.01, 0.42), 0.003, sides=3, color="leather_dark")
        mb.plate([(sign * 0.13, -0.012, 0.42), (sign * 0.15, -0.012, 0.42), (sign * 0.15, -0.012, 0.3), (sign * 0.14, -0.012, 0.28)], 0.008, color)
    if hq:
        for k, x in enumerate((-0.09, 0.09)):
            mb.tube((x, -0.02, 0.46), (x, -0.02, 0.4 - 0.02 * k), 0.002, sides=3, color="leather_dark")
            mb.tube((x, -0.02, 0.4 - 0.02 * k), (x, -0.02, 0.33 - 0.02 * k), 0.008, sides=4, color="silver")
    mb.socket("grip", (0, 0, -0.03))
    mb.socket("trail_tip", (0, 0, 0.6))


def armada_halberd(mb, hq):
    """Royal Guard polearm. Long enough to read on-screen behind the group in the upper-deck brawl."""
    h = 1.95
    mb.tube((0, 0, 0), (0, 0, h), 0.022, 0.018, sides=_q(hq, 6, 4), color="navy")
    mb.tube((0, 0, 0), (0, 0, 0.05), 0.028, sides=_q(hq, 6, 4), color="gold")
    mb.plate([(0.015, 0, h - 0.32), (0.25, 0, h - 0.28), (0.3, 0, h - 0.08), (0.11, 0, h - 0.12), (0.015, 0, h - 0.06)], 0.012, "silver")
    mb.plate([(-0.015, 0, h - 0.28), (-0.18, 0, h - 0.22), (-0.015, 0, h - 0.12)], 0.012, "gold")
    mb.plate([(-0.022, 0, h - 0.04), (0.022, 0, h - 0.04), (0, 0, h + 0.3)], 0.01, "silver")
    if hq:
        mb.lathe([(0.03, h - 0.42), (0.03, h - 0.34)], 6, "gold", smooth=False)
        mb.plate([(0.0, -0.02, h - 0.4), (0.12, -0.02, h - 0.52), (0.0, -0.02, h - 0.72)], 0.008, "faction_a")
    mb.socket("grip", (0, 0, 0.75))
    mb.socket("trail_tip", (0.3, 0, h - 0.08))


def armada_musket(mb, hq):
    """Standard Armada long gun. Oriented for gun.R, gripped at the trigger."""
    upright = Matrix(((0, 0, 1, 0), (-1, 0, 0, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
    with mb.xf(upright):
        z = 0.1
        mb.tube((0, 0.2, z), (0, -0.92, z), 0.018, 0.016, sides=_q(hq, 6, 4), color="iron")
        mb.path([(0, 0.0, z - 0.02), (0, 0.22, z - 0.03), (0, 0.42, z - 0.1), (0, 0.48, z - 0.13)], [0.024, 0.028, 0.038, 0.042], _q(hq, 6, 4), "wood_red")
        if hq:
            mb.box((0.026, 0.12, z + 0.01), (0.012, 0.09, 0.03), "brass")
            mb.tube((0, -0.92, z - 0.03), (0, -1.15, z - 0.03), 0.01, 0.002, sides=3, color="silver")
            for y in (-0.6, -0.1):
                with mb.xf(Matrix.Translation((0, y, z)) @ _y_axis()):
                    mb.lathe([(0.021, -0.008), (0.021, 0.008)], 6, "brass", smooth=False)
        mb.socket("grip", (0, 0.1, z - 0.06))
        mb.socket("muzzle", (0, -0.92, z))


def gatling_gun(mb, hq):
    """Rook's gatling gun, without its barrels: an iron receiver with a brass ammo drum on top, a wooden
    pistol grip, a carry handle and a crank. The spinning barrel cluster (SM_Prop_GatlingBarrels) mounts at the
    'barrel_hub' socket and points the way the gun does. Oriented for gun.R like the hand mortar."""
    upright = Matrix(((0, 0, 1, 0), (-1, 0, 0, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
    with mb.xf(upright):
        z = 0.2
        mb.box((0, 0.13, z), (0.17, 0.28, 0.19), "iron")
        mb.box((0, 0.13, z - 0.1), (0.12, 0.22, 0.03), "iron_light")
        mb.tube((-0.075, 0.1, z + 0.17), (0.075, 0.1, z + 0.17), 0.1, sides=_q(hq, 10, 6), color="brass")
        if hq:
            for x in (-0.078, 0.078):
                mb.tube((x - 0.004, 0.1, z + 0.17), (x + 0.004, 0.1, z + 0.17), 0.104, sides=10, color="iron")
        # The shroud the barrels turn in.
        with mb.xf(Matrix.Translation((0, 0.0, z)) @ _y_axis()):
            mb.lathe([(0.085, 0.0), (0.095, 0.03), (0.095, 0.06)], _q(hq, 10, 6), "iron_light", smooth=False)
        mb.path([(0, 0.22, z - 0.08), (0, 0.27, z - 0.17), (0, 0.3, z - 0.27)], [0.032, 0.03, 0.034], _q(hq, 6, 4), "wood_mid")
        mb.path([(0, 0.24, z + 0.1), (0, 0.18, z + 0.3), (0, -0.02, z + 0.3), (0, -0.06, z + 0.1)], [0.016] * 4, _q(hq, 4, 3), "iron")
        mb.path([(0.09, 0.2, z), (0.16, 0.2, z), (0.16, 0.27, z - 0.06)], [0.012, 0.012, 0.012], _q(hq, 4, 3), "iron")
        mb.sphere((0.16, 0.27, z - 0.08), 0.022, _q(hq, 6, 4), 3, "wood_dark", smooth=False)
        mb.socket("grip", (0, 0.28, z - 0.2))
        mb.socket("barrel_hub", (0, -0.045, z))
        mb.socket("muzzle", (0, -0.86, z))


def gatling_barrels(mb, hq):
    """The gatling's barrel cluster, which spins as it fires: barrels in a ring round a spindle, held by two
    brass clamps. Built up +Z from its hub, so it points the way the gun does once mounted at 'barrel_hub'."""
    length = 0.8
    count = _q(hq, 6, 4)
    mb.tube((0, 0, 0), (0, 0, length - 0.02), 0.022, sides=_q(hq, 6, 4), color="iron_light")
    for k in range(count):
        a = 2 * math.pi * k / count
        x, y = 0.05 * math.cos(a), 0.05 * math.sin(a)
        mb.tube((x, y, 0.0), (x, y, length), 0.017, sides=_q(hq, 6, 3), color="steel")
        if hq:
            mb.tube((x, y, length - 0.005), (x, y, length + 0.004), 0.009, sides=4, color="eye_dark")
    for z in ((0.32, 0.72) if hq else (0.6,)):
        mb.tube((0, 0, z - 0.02), (0, 0, z + 0.02), 0.075, sides=_q(hq, 10, 6), color="brass")
    mb.socket("muzzle", (0, 0, length))


def bomb(mb, hq):
    """Rook's bomb for his Bomb Charge: a round black iron shell with a brass fuse cap and a lit fuse.
    Held out from the palm on weapon.R, with sparks at the 'fuse' socket."""
    mb.sphere((0, 0, 0.17), 0.155, _q(hq, 12, 6), _q(hq, 8, 4), "iron", smooth=hq)
    mb.tube((0, 0, 0.3), (0, 0, 0.36), 0.045, sides=_q(hq, 8, 5), color="brass")
    if hq:
        mb.tube((-0.002, 0, 0.17), (0.002, 0, 0.17), 0.158, sides=12, color="iron_light")
    fuse = [(0, 0, 0.36), (0.02, 0, 0.41), (0.06, 0, 0.44), (0.1, 0, 0.43)]
    mb.path(fuse, [0.009] * len(fuse), _q(hq, 4, 3), "rope")
    mb.sphere((0.11, 0, 0.43), 0.018, _q(hq, 6, 4), 3, "ember", smooth=False)
    mb.socket("grip", (0, 0, 0.0))
    mb.socket("fuse", (0.11, 0, 0.43))


def wind_blade(mb, hq):
    """One of Lyra's Gale Slash blades: a flat crescent of solid wind, bright at its cutting edge, with thinner
    crescents trailing behind it. Lies flat, its edge bulging towards the front (-Y), so it can be rolled to any
    angle in flight."""
    def crescent(scale, back, thickness, color):
        n = _q(hq, 10, 5)
        outer = [(1.0 * scale * math.sin(a), back - 0.35 * scale * math.cos(a)) for a in (math.pi * (k / n - 0.5) for k in range(n + 1))]
        inner = [(0.86 * scale * math.sin(a), back - 0.12 * scale * math.cos(a) + 0.02) for a in (math.pi * (k / n - 0.5) for k in range(n, -1, -1))]
        mb.plate([(x, y, 0) for x, y in outer + inner], thickness, color)

    crescent(0.6, 0.0, 0.03, "wind")
    crescent(0.56, 0.008, 0.045, "cloud")
    if hq:
        crescent(0.48, 0.14, 0.02, "wind")
        crescent(0.36, 0.26, 0.015, "wind")
    mb.socket("edge", (0, -0.21, 0))


def music_note(mb, hq):
    """A glowing eighth note, flat and two-sided, for Lyra's songs. Stands on its head."""
    with mb.xf(Matrix.Rotation(-0.35, 4, "Y")):
        mb.sphere((0, 0, 0.06), (0.075, 0.03, 0.055), _q(hq, 10, 6), _q(hq, 4, 3), "lamp", smooth=False)
    mb.box((0.062, 0, 0.24), (0.022, 0.022, 0.36), "lamp")
    flag = [(0.05, 0, 0.42), (0.17, 0, 0.32), (0.15, 0, 0.22), (0.12, 0, 0.3), (0.05, 0, 0.36)]
    mb.plate(flag, 0.022, "lamp")
    mb.socket("centre", (0.03, 0, 0.2))


def tornado(mb, hq):
    """Storm Ballad's tornado: a funnel of wind ribbons twisting up from a narrow foot to a wide crown, with a
    pale core. Spun about its axis in game. About 4 m tall."""
    height = 4.2
    turns = 2.5
    ribbons = _q(hq, 4, 2)
    steps = _q(hq, 20, 12)
    for r in range(ribbons):
        phase = 2 * math.pi * r / ribbons
        points, radii = [], []
        for k in range(steps + 1):
            t = k / steps
            a = phase + 2 * math.pi * turns * t
            radius = 0.25 + 1.55 * t ** 1.4
            points.append((radius * math.cos(a), radius * math.sin(a), height * t))
            radii.append(0.05 + 0.12 * t)
        mb.path(points, radii, _q(hq, 4, 3), "wind" if r % 2 == 0 else "cloud")
    if hq:
        mb.lathe([(0.12, 0.0), (0.3, height * 0.45), (0.55, height * 0.8), (0.02, height * 0.82)], 8, "cloud_shade", smooth=True, caps=(True, False))
    mb.socket("crown", (0, 0, height))


def sable_bow(mb, hq):
    """Sable's recurve bow in hand, the same as the one on her back: pale wood limbs with steel brackets,
    the tips curling away from her, venom on the upper limb, a taut string. Stands upright with its belly
    towards her (+Y) and its back to the target (-Y), gripped at the middle."""
    limb = [(0, 0.0, 0.0), (0, -0.05, 0.22), (0, -0.04, 0.48), (0, 0.02, 0.62), (0, -0.03, 0.7)]
    for sign in (1, -1):
        points = [(x, y, sign * z) for x, y, z in limb]
        mb.path(points, [0.03, 0.026, 0.02, 0.014, 0.01], _q(hq, 5, 3), "wood_light")
        if hq:
            mb.tube((0, -0.05, sign * 0.2), (0, -0.05, sign * 0.26), 0.032, sides=5, color="steel")
    mb.tube((0, 0.0, -0.1), (0, 0.0, 0.1), 0.036, sides=_q(hq, 6, 4), color="leather_dark")
    mb.tube((0, 0.015, 0.66), (0, 0.015, -0.66), 0.005, sides=3, color="canvas")
    if hq:
        mb.sphere((0, -0.05, 0.56), (0.012, 0.012, 0.022), 4, 3, "grass", smooth=False)
    mb.socket("grip", (0, 0, 0))
    mb.socket("nock", (0, 0.015, 0))


def poison_arrow(mb, hq):
    """One of Sable's poison arrows: a dark shaft, green fletching and a barbed head wet with venom. Points
    up +Z, tip at the top, so it can be turned to fly point first."""
    sides = _q(hq, 4, 3)
    mb.tube((0, 0, 0), (0, 0, 0.62), 0.008, sides=sides, color="cloth_black")
    for k in range(_q(hq, 3, 2)):
        a = 2 * math.pi * k / _q(hq, 3, 2)
        x, y = math.cos(a), math.sin(a)
        mb.plate([(0.006 * x, 0.006 * y, 0.02), (0.045 * x, 0.045 * y, 0.05), (0.04 * x, 0.04 * y, 0.14), (0.006 * x, 0.006 * y, 0.15)], 0.004, "grass")
    mb.tube((0, 0, 0.6), (0, 0, 0.72), 0.024, 0.002, sides=sides, color="toxic")
    if hq:
        mb.sphere((0, 0, 0.64), 0.02, 4, 3, "toxic_dark", smooth=False)
    mb.socket("tip", (0, 0, 0.72))


def fireball(mb, hq):
    """Ivo's fireball: a white-hot core in a shell of flame, with tongues of fire streaming back from it. Flies
    towards +Z, so its trail hangs below its centre in the model."""
    centre = (0, 0, 0.55)
    mb.sphere(centre, 0.2, _q(hq, 10, 6), _q(hq, 6, 4), "lamp", smooth=hq)
    mb.sphere((0, 0, 0.52), (0.27, 0.27, 0.3), _q(hq, 10, 6), _q(hq, 6, 4), "ember", smooth=hq)
    tongues = _q(hq, 7, 4)
    for k in range(tongues):
        a = 2 * math.pi * k / tongues
        x, y = math.cos(a), math.sin(a)
        length = 0.35 + 0.15 * ((k * 7) % 3)
        mb.path([(0.2 * x, 0.2 * y, 0.5), (0.16 * x, 0.16 * y, 0.5 - length * 0.5), (0.05 * x, 0.05 * y, 0.5 - length)],
                [0.09, 0.06, 0.012], _q(hq, 5, 3), "ember" if k % 2 == 0 else "lamp")
    mb.socket("centre", centre)


def trap_door(mb, hq):
    """A deck trap door's frame, lying on the deck with the dark hole below it. The lid is its own prop
    (SM_Prop_TrapDoorLid) so it can swing open on its hinge: mount the lid's 'hinge' on this one's 'hinge'.
    The hinge runs along the back edge (+Y), so the lid opens towards the back and the front is clear."""
    half, rim = 0.55, 0.08
    mb.box((0, 0, 0.004), (2 * half, 2 * half, 0.008), "abyss")
    for x, y, sx, sy in ((0, half, 2 * half + 2 * rim, rim), (0, -half, 2 * half + 2 * rim, rim), (half, 0, rim, 2 * half), (-half, 0, rim, 2 * half)):
        mb.box((x, y, 0.02), (sx, sy, 0.04), "wood_dark")
    if hq:
        for x in (-half - rim * 0.5, half + rim * 0.5):
            for y in (-half, half):
                mb.box((x, y, 0.045), (0.05, 0.05, 0.012), "iron")
    mb.socket("hinge", (0, half - 0.02, 0.04))
    mb.socket("centre", (0, 0, 0.0))


def trap_door_lid(mb, hq):
    """The trap door's lid: deck planks on two iron straps, with a ring pull at the front. Its 'hinge' is along
    its back edge, where it meets the frame's."""
    half = 0.55
    planks = _q(hq, 5, 3)
    width = 2 * half / planks
    for k in range(planks):
        x = -half + width * (k + 0.5)
        mb.box((x, 0, 0.025), (width * 0.94, 2 * half, 0.05), "wood_deck")
    for y in (-half * 0.6, half * 0.6):
        mb.box((0, y, 0.054), (2 * half, 0.06, 0.012), "iron")
    with mb.xf(Matrix.Translation((0, -half * 0.75, 0.062)) @ Matrix.Rotation(math.pi / 2, 4, "X")):
        mb.lathe([(0.05, -0.01), (0.05, 0.01)], _q(hq, 8, 5), "brass", smooth=False)
    mb.socket("hinge", (0, half, 0.0))


def corsair_lance(mb, hq):
    """Roxi's weapon: a Syndicate corsair lance. Steeled shaft, brass vamplate guard, sharp spearhead with plasma fuller, and a cyan/magenta pennant."""
    h = 2.05
    mb.tube((0, 0, -0.2), (0, 0, h), 0.02, 0.016, sides=_q(hq, 6, 4), color="wood_dark")
    mb.tube((0, 0, -0.2), (0, 0, -0.32), 0.02, 0.005, sides=_q(hq, 6, 4), color="brass")
    mb.tube((0, 0, 0.1), (0, 0, 0.42), 0.025, 0.025, sides=_q(hq, 6, 4), color="leather_dark")
    mb.tube((0, 0, 0.42), (0, 0, 0.52), 0.028, 0.09, sides=_q(hq, 8, 5), color="brass")
    mb.plate([(-0.02, 0, h - 0.05), (0.02, 0, h - 0.05), (0.055, 0, h + 0.18), (0, 0, h + 0.38), (-0.055, 0, h + 0.18)], 0.012, "silver")
    if hq:
        mb.plate([(0.0, -0.005, h), (0.02, -0.005, h + 0.16), (0.0, -0.005, h + 0.32), (-0.02, -0.005, h + 0.16)], 0.004, "plasma")
        mb.lathe([(0.026, h - 0.08), (0.026, h - 0.02)], 6, "brass", smooth=False)
        mb.plate([(0.0, -0.01, h - 0.06), (0.16, -0.01, h - 0.18), (0.0, -0.01, h - 0.38)], 0.006, "faction_a")
        mb.plate([(0.0, 0.01, h - 0.08), (-0.14, 0.01, h - 0.22), (0.0, 0.01, h - 0.44)], 0.006, "faction_b")
    else:
        mb.plate([(0.0, 0, h - 0.06), (0.12, 0, h - 0.22), (0.0, 0, h - 0.36)], 0.01, "faction_a")
    mb.socket("grip", (0, 0, 0.26))
    mb.socket("trail_tip", (0, 0, h + 0.38))


def chainsaw(mb, hq):
    """Sawbones Wren's brutal pirate chainsaw. A smoke-blackened engine block, pull-cord starter,
    top and rear grips, and an elongated guide bar with toothed cutting chain spotted with dried gore."""
    sides = _q(hq, 6, 4)
    # Rear grip (handle held by hand): extends along Z from -0.15 to 0.02
    mb.tube((0, 0, -0.15), (0, 0, 0.02), 0.02, 0.02, sides=sides, color="leather_dark")
    # Trigger guard under grip
    mb.plate([(-0.025, 0, -0.12), (-0.05, 0, -0.06), (-0.025, 0, 0.0)], 0.008, "brass")

    # Engine body housing: box from z = 0.0 to 0.28
    mb.box((-0.02, 0, 0.14), (0.16, 0.15, 0.24), "iron")
    mb.box((-0.02, 0, 0.22), (0.13, 0.12, 0.1), "rust")
    if hq:
        # Starter pull-cord housing on side
        mb.lathe([(0.035, 0.08), (0.04, 0.12), (0.01, 0.12)], sides=8, color="brass", smooth=False)
        # Exhaust muffler port on top/side
        mb.tube((-0.08, 0.04, 0.18), (-0.12, 0.06, 0.22), 0.015, 0.015, sides=6, color="iron_light")
        # Fuel cap
        mb.sphere((-0.02, -0.06, 0.06), 0.018, 6, 4, "brass")

    # Top wraparound handle
    mb.path([(0.07, -0.07, 0.1), (0.09, 0, 0.18), (0.07, 0.07, 0.1)], [0.012, 0.012, 0.012], 4, "steel")

    # Front handguard plate
    mb.plate([(-0.05, 0, 0.27), (0.08, 0, 0.27), (0.06, 0, 0.31), (-0.03, 0, 0.31)], 0.01, "iron")

    # Long guide bar extending forward along Z: z = 0.26 to 0.78
    # Outer edge faces -X (matching cutlass standard: -X is down/cutting edge, +Z is forward)
    spine = [(0.02, 0.28), (0.02, 0.5), (0.02, 0.72), (0.0, 0.78)]
    edge = [(-0.06, 0.28), (-0.06, 0.5), (-0.06, 0.72), (0.0, 0.78)]
    outline = [(x, 0.0, z) for x, z in spine] + [(x, 0.0, z) for x, z in edge[-2::-1]]
    mb.plate(outline, 0.016, "steel")

    # Chain teeth around the blade perimeter
    teeth_outline = [(-0.068, 0.0, 0.27), (0.028, 0.0, 0.27), (0.028, 0.0, 0.73), (0.0, 0.0, 0.795), (-0.068, 0.0, 0.73)]
    mb.plate(teeth_outline, 0.008, "silver")

    if hq:
        # Gore/blood flecks along teeth
        mb.box((-0.065, 0, 0.45), (0.015, 0.012, 0.08), "velvet")
        mb.box((-0.065, 0, 0.65), (0.015, 0.012, 0.06), "velvet")
        mb.box((0.0, 0, 0.78), (0.02, 0.012, 0.03), "velvet")

    mb.socket("grip", (0, 0, -0.06))
    mb.socket("trail_tip", (0, 0, 0.8))


def poison_flask(mb, hq):
    """Wren's volatile poison flask: a spherical apothecary glass filled with churning green venom,
    reinforced with brass cage straps and sealed with a cork stopper."""
    sides = _q(hq, 8, 5)
    # Flask main spherical bulb
    mb.sphere((0, 0, 0.06), 0.065, sides, _q(hq, 6, 4), "glass")
    # Glowing green toxic liquid inside
    mb.sphere((0, 0, 0.058), 0.055, sides, _q(hq, 5, 3), "toxic")
    # Brass cage straps around bulb
    mb.lathe([(0.066, 0.055), (0.066, 0.065)], sides, "brass", smooth=False)
    if hq:
        with mb.xf(Matrix.Rotation(math.pi / 2, 4, "Y")):
            mb.lathe([(0.066, -0.005), (0.066, 0.005)], sides, "brass", smooth=False)
    # Flask neck
    mb.tube((0, 0, 0.11), (0, 0, 0.18), 0.026, 0.024, sides=sides, color="glass")
    mb.tube((0, 0, 0.15), (0, 0, 0.18), 0.028, 0.032, sides=sides, color="brass")
    # Cork stopper
    mb.tube((0, 0, 0.175), (0, 0, 0.215), 0.023, 0.027, sides=sides, color="leather")
    mb.socket("grip", (0, 0, 0.14))
    mb.socket("centre", (0, 0, 0.06))


