"""Thirty additional airship designs for Ransom Skies across five themes:
  1. Elemental Ships (Tidebreaker, TempestSpire, Earthshaker, InfernoForge, ZephyrLotus, GlacierFang)
  2. Spaceships & Sci-Fi Craft (StarlightCruiser, NebulaSaucer, VoidInterceptor, OrbitalCarrier, PlasmaLancer, SolarArk)
  3. Modern Naval Battleships (SteelDreadnought, AegisDestroyer, SkySubmarine, FleetCarrier, HeavyCruiser, GunshipMonitor)
  4. Creative & Fantastical Ships (ClockworkSovereign, SkyNautilus, BoneRevenant, CrystalSanctum, DragonJunker, BeetleScarab)
  5. Specialized Outlaw & Industrial Ships (GyroCopter, WhalerHarpooner, LuxuryYacht, ShadowStalker, PowderKeg, CloudTrain)

Bow faces Blender -Y (glTF +Z). All ships publish the standard Ransom Skies sockets in both HQ and LQ.
"""
import math
from mathutils import Matrix

from story_ships import (
    _lerp,
    _q,
    _window_strip,
    base_sockets,
    broadside,
    cosine_ts,
    fins,
    gasbag,
    gasbag_band,
    mast,
    nacelle,
    rope,
    sail,
    shell,
    striped,
    wing,
)


def _hull_stations(length, half_w, height, count, bow_t=0.36, stern_t=0.68, stern_taper=0.32, keel_bow=0.5, keel_stern=0.35, sheer_bow=0.25, sheer_stern=0.18):
    """Generates smooth (y, half_width, keel_z, deck_z) stations along [-length/2, length/2]."""
    stations = []
    width_fn = _width_curve(half_w, bow_t, stern_t, stern_taper)
    for t in cosine_ts(count):
        y = -length / 2 + t * length
        w = width_fn(t)
        keel = height * keel_bow * (1 - t / bow_t) ** 2 if t < bow_t else (height * keel_stern * ((t - stern_t) / (1 - stern_t)) ** 2 if t > stern_t else 0.0)
        deck = height + (height * sheer_bow * (1 - t / bow_t) ** 2 if t < bow_t else (height * sheer_stern * ((t - stern_t) / (1 - stern_t)) ** 2 if t > stern_t else 0.0))
        stations.append((y, w, keel, deck))
    return stations, width_fn


def _width_curve(half_w, bow_t=0.36, stern_t=0.68, stern_taper=0.32):
    def width(t):
        t = max(0.0, min(1.0, t))
        if t < bow_t:
            return half_w * max(0.06, math.sqrt(max(0.0, 1 - (1 - t / bow_t) ** 2)))
        if t > stern_t:
            return half_w * max(0.08, 1 - stern_taper * ((t - stern_t) / (1 - stern_t)) ** 2)
        return half_w
    return width


def _turret(mb, x, y, z, radius, height, barrels, barrel_len, barrel_r, hq, base_col="steel", gun_col="iron", socket_prefix=None, pitch=0.08):
    """Naval/sci-fi gun turret with 1-3 forward-pointing barrels."""
    sides = _q(hq, 8, 5)
    with mb.xf(Matrix.Translation((x, y, z))):
        mb.lathe([(radius * 1.05, 0.0), (radius, height * 0.72), (radius * 0.76, height)], sides, base_col, smooth=False)
    for i in range(barrels):
        bx = x + (i - (barrels - 1) / 2) * (radius * 0.58)
        bz0 = z + height * 0.55
        bz1 = bz0 + barrel_len * pitch
        by0 = y - radius * 0.55
        by1 = by0 - barrel_len
        mb.tube((bx, by0, bz0), (bx, by1, bz1), barrel_r, barrel_r * 0.86, sides=_q(hq, 6, 4), color=gun_col)
        if socket_prefix:
            mb.socket(f"{socket_prefix}{i}", (bx, by1 - 0.04, bz1))


def _torus_ring(mb, cx, cy, cz, major_r, minor_r, sides, ring_sides, color, rot_x=0.0, rot_y=0.0):
    """Closed torus ring around local Z (or tilted by rot_x / rot_y)."""
    xf = Matrix.Translation((cx, cy, cz))
    if rot_x:
        xf = xf @ Matrix.Rotation(rot_x, 4, "X")
    if rot_y:
        xf = xf @ Matrix.Rotation(rot_y, 4, "Y")
    rings = []
    for i in range(sides):
        theta = 2 * math.pi * i / sides
        ct, st = math.cos(theta), math.sin(theta)
        ring = []
        for j in range(ring_sides):
            phi = 2 * math.pi * j / ring_sides
            r = major_r + minor_r * math.cos(phi)
            z = minor_r * math.sin(phi)
            ring.append((r * ct, r * st, z))
        rings.append(ring)
    rings.append(rings[0])
    with mb.xf(xf):
        mb.loft(rings, color, caps=(False, False), smooth=True)


def _crystal_spire(mb, p0, p1, r_base, r_mid, sides, color):
    """Faceted crystal prism tapering to a sharp point."""
    p0_v, p1_v = p0, p1
    mid = tuple(_lerp(a, b, 0.72) for a, b in zip(p0_v, p1_v))
    mb.path([p0_v, mid, p1_v], [r_base, r_mid, 0.025], sides, color, smooth=False)


# ==============================================================================
# CATEGORY 1: ELEMENTAL SHIPS (Water, Thunder, Earth, Fire, Wind, Ice)
# ==============================================================================

def tidebreaker(mb, hq):
    """1. Water Elemental: Leviathan wave-crest catamaran with glowing aqua water-jets and dorsal fin sails."""
    length, gap, deck_z = 19.0, 3.1, 3.0
    y_of = lambda t: -length / 2 + t * length
    # Twin wave-carved catamaran hulls.
    for sign in (1, -1):
        stations, _ = _hull_stations(length, 1.45, deck_z, _q(hq, 12, 6), bow_t=0.4, stern_t=0.68, keel_bow=0.65)
        paints = {0: "navy", 1: "faction_a", 2: "gem_blue", 3: "liftstone", 4: "enamel"} if hq else {0: "navy", 1: "faction_a", 2: "gem_blue"}
        with mb.xf(Matrix.Translation((sign * gap, 0, 0))):
            shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.6)
        # Wave-crest bow hydrofoils.
        mb.plate([
            (sign * (gap + 1.1), y_of(0.16), 1.6),
            (sign * (gap + 3.6), y_of(0.28), 2.3),
            (sign * (gap + 3.3), y_of(0.42), 2.1),
            (sign * (gap + 1.05), y_of(0.36), 1.45),
        ], 0.09, "liftstone" if hq else "gem_blue")

    # Curved coral-arch bridge deck joining the twin hulls.
    mb.box((0, 0.4, deck_z - 0.1), (gap * 2 - 0.5, 11.2, 0.48), "enamel", top_scale=0.95)
    mb.box((0, y_of(0.76), deck_z + 0.95), (3.8, 3.6, 1.5), "faction_a", top_scale=0.84)
    if hq:
        _window_strip(mb, [-1.1, 0.0, 1.1], y_of(0.76) - 1.82, deck_z + 1.0, (0.65, 0.55), 0.08, "liftstone")

    # Sea-serpent water cannon prow in the center channel.
    mb.path(
        [(0, y_of(0.22), deck_z - 0.1), (0, y_of(0.06), deck_z + 0.8), (0, y_of(0.0) - 2.4, deck_z + 2.1), (0, y_of(0.0) - 3.6, deck_z + 1.9)],
        [0.55, 0.48, 0.42, 0.24],
        _q(hq, 8, 4),
        "gem_blue",
    )
    mb.socket("muzzle_F0", (0, y_of(0.0) - 3.65, deck_z + 1.9))

    # Ribbed nautilus-blimp water envelope overhead with dorsal fin sails.
    env_z = deck_z + 7.4
    rings = _q(hq, 12, 6)
    sides = _q(hq, 14, 8)
    bag_paint = lambda i, j: "liftstone" if (i in (0, rings - 1) or j % 4 == 0) else ("faction_a" if j % 2 else "gem_blue")
    gasbag(mb, 0, 0.3, env_z, 17.5, 3.5, sides, rings, bag_paint, flat=0.86)
    # Dorsal wave-fin atop the envelope.
    mb.plate([(0, -4.5, env_z + 2.6), (0, -1.2, env_z + 5.6), (0, 4.8, env_z + 4.4), (0, 6.2, env_z + 2.2)], 0.12, "faction_b")
    for y in _q(hq, (-3.6, 0.0, 3.8), (-2.4, 2.8)):
        for sign in (1, -1):
            rope(mb, (sign * gap, y, deck_z), (sign * 1.8, y * 0.85, env_z - 2.7), 0.07, hq, "liftstone_dark")

    # Hydro-jet turbine nacelles.
    for sign, label in ((1, "L"), (-1, "R")):
        nacelle(mb, sign * (gap + 2.3), y_of(0.78), 2.1, 1.4, 0.62, hq, label, root_x=sign * (gap + 1.1), color="gem_blue")
        mb.socket(f"afterburner_{label}", (sign * (gap + 2.3), y_of(0.78) + 1.45, 2.1))

    broadside(mb, [y_of(t) for t in (0.34, 0.5, 0.66)], 2.2, lambda _y: gap + 1.38, 0.9, 0.13, hq, color="brass", carriage="navy")
    base_sockets(mb, gap + 1.45, deck_z, env_z, y_of(0.78), deck_z + 2.0)
    mb.socket("lift_core", (0, 0.4, deck_z + 0.5))
    mb.socket("helm", (0, y_of(0.7), deck_z + 0.1))


def tempest_spire(mb, hq):
    """2. Thunder Elemental: Storm-slate trimaran with copper Tesla coils, lightning arcs and railgun prongs."""
    length, half, deck_z = 21.0, 2.6, 3.1
    y_of = lambda t: -length / 2 + t * length
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 12, 6), bow_t=0.42, stern_t=0.72)
    paints = {0: "storm_dark", 1: "storm", 2: "brass", 3: "faction_a", 4: "lightning"} if hq else {0: "storm_dark", 1: "brass", 2: "faction_a"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.55)

    # Twin forward lightning-railgun prongs at the bow.
    for sign in (1, -1):
        mb.tube((sign * 0.75, y_of(0.08), 2.4), (sign * 0.55, y_of(0.0) - 4.8, 2.65), 0.24, 0.08, sides=_q(hq, 6, 4), color="brass")
        mb.tube((sign * 0.55, y_of(0.0) - 4.8, 2.65), (sign * 0.48, y_of(0.0) - 5.6, 2.68), 0.11, 0.04, sides=4, color="lightning")
    mb.tube((-0.52, y_of(0.0) - 3.6, 2.6), (0.52, y_of(0.0) - 3.6, 2.6), 0.07, sides=4, color="lightning")
    mb.socket("muzzle_F0", (0, y_of(0.0) - 5.6, 2.68))

    # Three towering copper Tesla coil spires along the deck spine.
    coil_ys = (y_of(0.28), y_of(0.5), y_of(0.72))
    for idx, cy in enumerate(coil_ys):
        top_z = deck_z + (4.2 if idx == 1 else 3.4)
        mb.tube((0, cy, deck_z - 0.1), (0, cy, top_z), 0.28, 0.16, sides=_q(hq, 8, 5), color="brass")
        if hq:
            for kz in (0.35, 0.62, 0.85):
                zz = _lerp(deck_z, top_z, kz)
                with mb.xf(Matrix.Translation((0, cy, zz))):
                    mb.lathe([(0.55, -0.08), (0.62, 0.0), (0.55, 0.08)], 8, "lightning" if kz > 0.7 else "brass", smooth=False)
        mb.sphere((0, cy, top_z + 0.25), 0.36, _q(hq, 8, 5), _q(hq, 5, 3), "lightning")
    # Glowing arc conduit connecting the coil tops.
    mb.path([(0, coil_ys[0], deck_z + 3.65), (0, coil_ys[1], deck_z + 4.45), (0, coil_ys[2], deck_z + 3.65)], [0.06, 0.08, 0.06], 4, "lightning")

    # Storm-cloud twin envelopes crackling with lightning seams.
    env_z = deck_z + 7.8
    rings = _q(hq, 10, 6)
    sides = _q(hq, 12, 6)
    storm_bag = lambda i, j: "lightning" if (i + j) % 5 == 0 else ("storm_dark" if j % 2 else "storm")
    for sign in (1, -1):
        gasbag(mb, sign * 3.4, 0.4, env_z, 16.5, 2.9, sides, rings, storm_bag, flat=0.9)
        for y in _q(hq, (-4.2, 0.4, 4.8), (-2.8, 3.2)):
            rope(mb, (sign * width_fn((y + length / 2) / length) * 0.88, y, deck_z), (sign * 3.2, y * 0.9, env_z - 2.4), 0.06, hq, "brass")
    fins(mb, 0, 5.8, env_z + 0.6, 3.0, 2.8, 0.1, "lightning")

    # Outrigger storm-foils & arc-nacelles.
    for sign, label in ((1, "L"), (-1, "R")):
        wing(mb, sign, sign * 2.2, y_of(0.35), y_of(0.62), 2.1, 4.2, 1.4, hq, color="storm_dark", spar="brass", thick=0.09)
        nacelle(mb, sign * 4.8, y_of(0.76), 2.3, 1.35, 0.56, hq, label, root_x=sign * 2.2, color="brass")

    broadside(mb, [y_of(t) for t in (0.34, 0.48, 0.62, 0.76)], 2.2, lambda y: width_fn((y + length / 2) / length), 0.95, 0.13, hq, color="brass", carriage="storm_dark")
    base_sockets(mb, half, deck_z, env_z, coil_ys[2], deck_z + 3.8)
    mb.socket("lift_core", (0, coil_ys[1], deck_z + 1.2))
    mb.socket("helm", (0, y_of(0.82), deck_z + 0.1))


def earthshaker(mb, hq):
    """3. Earth Elemental: Floating carved stone monolith bound in iron chains, lifted by giant Liftstone crystal spires."""
    length, half, deck_z = 22.0, 4.4, 4.2
    y_of = lambda t: -length / 2 + t * length
    # Faceted craggy rock hull: low side count and low power for angular stone blocks.
    stations = []
    for t in cosine_ts(_q(hq, 10, 6)):
        y = y_of(t)
        w = half * (0.45 + 0.55 * math.sin(math.pi * t) ** 0.45)
        keel = 2.4 * abs(2 * t - 1) ** 1.6
        deck = deck_z + (0.9 if t < 0.25 or t > 0.75 else 0.0)
        stations.append((y, w, keel, deck))
    paints = {0: "rock_dark", 1: "rock", 2: "iron", 3: "rock_dark", 4: "grass_dark"} if hq else {0: "rock_dark", 1: "rock", 2: "iron"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.32)

    # Stone fortress keep at the stern and monolith ram at the bow.
    mb.box((0, y_of(0.78), deck_z + 1.6), (5.8, 4.6, 2.8), "rock_dark", top_scale=0.86)
    mb.box((0, y_of(0.78), deck_z + 3.1), (6.2, 5.0, 0.35), "iron")
    mb.path([(0, y_of(0.1), 2.5), (0, y_of(0.0) - 2.2, 2.8), (0, y_of(0.0) - 4.2, 3.1)], [1.6, 1.1, 0.18], _q(hq, 6, 4), "rock_dark")
    mb.socket("ram_tip", (0, y_of(0.0) - 4.2, 3.1))
    mb.socket("muzzle_F0", (0, y_of(0.0) - 4.2, 3.1))

    # Colossal glowing Liftstone crystal cluster erupting above the deck (replaces soft envelope).
    env_z = deck_z + 7.2
    crystals = [
        ((0, -0.5, deck_z - 0.3), (0, -0.8, env_z + 3.2), 1.45, 0.95, "liftstone"),
        ((2.2, 0.6, deck_z - 0.2), (3.8, 0.9, env_z + 1.4), 1.0, 0.68, "liftstone"),
        ((-2.2, 0.6, deck_z - 0.2), (-3.8, 0.9, env_z + 1.4), 1.0, 0.68, "liftstone"),
        ((1.4, -3.4, deck_z - 0.2), (2.5, -4.4, env_z + 0.4), 0.82, 0.52, "liftstone_dark"),
        ((-1.4, -3.4, deck_z - 0.2), (-2.5, -4.4, env_z + 0.4), 0.82, 0.52, "liftstone_dark"),
    ]
    if hq:
        crystals += [
            ((1.6, 3.8, deck_z), (2.8, 4.8, env_z + 0.2), 0.75, 0.48, "liftstone"),
            ((-1.6, 3.8, deck_z), (-2.8, 4.8, env_z + 0.2), 0.75, 0.48, "liftstone"),
        ]
    for p0, p1, r0, r1, col in crystals:
        _crystal_spire(mb, p0, p1, r0, r1, _q(hq, 6, 4), col)
    # Iron binding collar and chains around the central crystal cluster.
    _torus_ring(mb, 0, -0.2, deck_z + 3.6, 2.8, 0.22, _q(hq, 10, 6), 4, "iron")
    for sign in (1, -1):
        rope(mb, (sign * 3.8, -3.2, deck_z + 0.2), (sign * 2.6, -0.4, deck_z + 3.6), 0.14, hq, "iron")
        rope(mb, (sign * 3.8, 3.4, deck_z + 0.2), (sign * 2.6, 0.2, deck_z + 3.6), 0.14, hq, "iron")

    # Outrigger stone-and-iron engine pods.
    for sign, label in ((1, "L"), (-1, "R")):
        mb.box((sign * 4.8, y_of(0.52), 2.8), (1.8, 4.2, 1.1), "rock_dark", top_scale=0.8)
        nacelle(mb, sign * 5.6, y_of(0.75), 2.8, 1.5, 0.75, hq, label, root_x=sign * 3.8, color="iron")

    broadside(mb, [y_of(t) for t in (0.3, 0.45, 0.6)], 3.1, lambda _y: half * 0.92, 1.15, 0.18, hq, color="iron", carriage="rock_dark")
    base_sockets(mb, half, deck_z, env_z, y_of(0.78), deck_z + 3.3)
    mb.socket("lift_core", (0, -0.5, deck_z + 2.0))
    mb.socket("helm", (0, y_of(0.72), deck_z + 0.2))


def inferno_forge(mb, hq):
    """4. Fire Elemental: Volcanic obsidian smelter-dreadnought with glowing magma channels and triple furnace stacks."""
    length, half, deck_z = 24.0, 4.1, 3.8
    y_of = lambda t: -length / 2 + t * length
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 12, 6), bow_t=0.34, stern_t=0.72)
    paints = {0: "abyss", 1: "ember", 2: "iron", 3: "rust_dark", 4: "ember", 5: "abyss"} if hq else {0: "abyss", 1: "ember", 2: "rust_dark"}
    shell(mb, stations, _q(hq, 6, 3), lambda r: paints[r], power=0.45)

    # Dragon-maw flamethrower prow with glowing magma throat.
    bow_y = y_of(0.0)
    mb.box((0, bow_y - 1.2, 2.9), (2.4, 2.8, 1.6), "iron", top_scale=0.82)
    mb.tube((0, bow_y - 0.8, 2.85), (0, bow_y - 3.6, 2.75), 0.58, 0.42, sides=_q(hq, 8, 5), color="rust_dark")
    mb.sphere((0, bow_y - 3.55, 2.75), 0.34, _q(hq, 6, 4), 4, "ember")
    mb.socket("muzzle_F0", (0, bow_y - 3.7, 2.75))

    # Smelter citadel & three belching volcanic smokestacks.
    mb.box((0, y_of(0.74), deck_z + 1.3), (5.4, 5.2, 2.2), "rust_dark", top_scale=0.88)
    for idx, sy in enumerate((y_of(0.38), y_of(0.52), y_of(0.66))):
        h = 3.6 if idx == 1 else 3.0
        mb.tube((0, sy, deck_z - 0.1), (0, sy + 0.4, deck_z + h), 0.58, 0.44, sides=_q(hq, 8, 5), color="iron")
        mb.sphere((0, sy + 0.4, deck_z + h + 0.05), (0.38, 0.38, 0.18), _q(hq, 6, 4), 3, "ember")

    # Blistered ember-veined hot-air envelope with under-slung magma brazier.
    env_z = deck_z + 9.2
    rings = _q(hq, 11, 6)
    sides = _q(hq, 14, 8)
    lava_bag = lambda i, j: "iron" if i in (0, rings - 1) else ("ember" if j % 4 == 0 else ("abyss" if j % 2 else "rust_dark"))
    gasbag(mb, 0, 0.4, env_z, 21.0, 4.4, sides, rings, lava_bag, flat=0.92)
    if hq:
        for s in (0.28, 0.5, 0.72):
            gasbag_band(mb, 0, 0.4, env_z, 21.0, 4.4, s, sides, "brass", flat=0.92)
    fins(mb, 0, 7.6, env_z + 1.2, 3.6, 3.5, 0.14, "rust_dark")
    for y in _q(hq, (-5.2, -1.6, 2.0, 5.6), (-3.8, 3.8)):
        for sign in (1, -1):
            rope(mb, (sign * 3.4, y, deck_z), (sign * 2.4, y * 0.85, env_z - 3.8), 0.09, hq, "iron")

    for sign, label in ((1, "L"), (-1, "R")):
        wing(mb, sign, sign * 3.5, y_of(0.36), y_of(0.62), 2.5, 4.2, 1.2, hq, color="rust_dark", spar="iron", thick=0.12)
        nacelle(mb, sign * 5.6, y_of(0.78), 2.4, 1.6, 0.74, hq, label, root_x=sign * 3.5, color="rust")
        mb.socket(f"afterburner_{label}", (sign * 5.6, y_of(0.78) + 1.65, 2.4))

    broadside(mb, [y_of(t) for t in (0.28, 0.42, 0.56, 0.7)], 2.6, lambda y: width_fn((y + length / 2) / length), 1.15, 0.17, hq, color="brass", carriage="iron")
    base_sockets(mb, half, deck_z, env_z, y_of(0.52) + 0.4, deck_z + 3.7)
    mb.socket("lift_core", (0, y_of(0.52), 2.2))
    mb.socket("helm", (0, y_of(0.74), deck_z + 2.45))


def zephyr_lotus(mb, hq):
    """5. Wind Elemental: Graceful ivory-and-gold cloud-dancer with six sweeping lotus-petal wing sails and a vortex halo."""
    length, half, deck_z = 18.5, 2.1, 2.6
    y_of = lambda t: -length / 2 + t * length
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 12, 6), bow_t=0.44, stern_t=0.65, stern_taper=0.45)
    paints = {0: "gold_dark", 1: "enamel", 2: "wind", 3: "enamel", 4: "faction_a"} if hq else {0: "gold_dark", 1: "enamel", 2: "wind"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.72)

    # Sweeping avian bowsprit.
    mb.path([(0, y_of(0.05), 2.7), (0, y_of(0.0) - 2.5, 3.4), (0, y_of(0.0) - 4.8, 4.3)], [0.24, 0.14, 0.03], _q(hq, 6, 4), "gold")
    mb.socket("muzzle_F0", (0, y_of(0.0) - 4.8, 4.3))

    # Pavilion cabin amidships.
    mb.box((0, y_of(0.68), deck_z + 0.85), (2.7, 4.0, 1.5), "enamel", top_scale=0.82)
    mb.box((0, y_of(0.68), deck_z + 1.68), (3.1, 4.4, 0.18), "gold")

    # Six blooming lotus-petal wing-sails (3 per side, tiered in height and sweep).
    petal_specs = ((-2.6, 0.4, 2.2, 5.2, 2.2, "enamel"), (-0.2, 2.8, 2.5, 6.2, 3.4, "wind"), (2.2, 5.2, 2.2, 4.6, 1.8, "faction_b"))
    for y0, y1, z0, span, lift, col in petal_specs:
        for sign in (1, -1):
            wing(mb, sign, sign * 1.45, y0, y1, z0, span, lift, hq, color=col, spar="gold", thick=0.07, ribs=1)

    # Levitating wind-vortex ring halo above the ship instead of a traditional blimp.
    env_z = deck_z + 6.4
    _torus_ring(mb, 0, 0.2, env_z, 4.6, 0.58, _q(hq, 16, 8), _q(hq, 6, 4), "wind", rot_x=0.12)
    _torus_ring(mb, 0, 0.2, env_z, 3.2, 0.28, _q(hq, 12, 6), 4, "gold", rot_x=-0.12)
    mb.sphere((0, 0.2, env_z), (0.95, 1.8, 0.95), _q(hq, 8, 5), 4, "wind")
    for sign in (1, -1):
        rope(mb, (sign * 1.3, -2.2, deck_z), (sign * 3.1, -0.8, env_z - 0.3), 0.055, hq, "gold")
        rope(mb, (sign * 1.3, 2.6, deck_z), (sign * 3.1, 1.2, env_z - 0.3), 0.055, hq, "gold")

    for sign, label in ((1, "L"), (-1, "R")):
        nacelle(mb, sign * 3.5, y_of(0.78), 2.0, 1.25, 0.48, hq, label, root_x=sign * 1.6, color="gold")

    broadside(mb, [y_of(t) for t in (0.36, 0.54)], 2.0, lambda y: width_fn((y + length / 2) / length), 0.85, 0.1, hq, color="gold", carriage="enamel")
    base_sockets(mb, half, deck_z, env_z, y_of(0.72), deck_z + 2.0)
    mb.socket("lift_core", (0, 0.2, env_z))
    mb.socket("helm", (0, y_of(0.62), deck_z + 0.1))


def glacier_fang(mb, hq):
    """6. Ice Elemental: Jagged crystalline icebreaker with frost-shard levitation array and cryo-ram prow."""
    length, half, deck_z = 20.5, 3.2, 3.2
    y_of = lambda t: -length / 2 + t * length
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 10, 6), bow_t=0.42, stern_t=0.72)
    paints = {0: "gem_blue", 1: "cloud_shade", 2: "cloud", 3: "liftstone", 4: "cloud"} if hq else {0: "gem_blue", 1: "cloud_shade", 2: "cloud"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.38)

    # Serrated crystalline ice-ram and icicle keel spikes.
    _crystal_spire(mb, (0, y_of(0.08), 2.4), (0, y_of(0.0) - 5.2, 2.7), 0.95, 0.52, _q(hq, 6, 4), "liftstone")
    mb.socket("ram_tip", (0, y_of(0.0) - 5.2, 2.7))
    mb.socket("muzzle_F0", (0, y_of(0.0) - 5.2, 2.7))
    for sign in (1, -1):
        _crystal_spire(mb, (sign * 1.4, y_of(0.14), 2.2), (sign * 2.3, y_of(0.0) - 2.6, 2.4), 0.52, 0.28, 4, "cloud")
        if hq:
            for ty in (-3.2, 0.0, 3.2):
                _crystal_spire(mb, (sign * 2.6, ty, 2.4), (sign * 4.4, ty + 0.6, 1.6), 0.36, 0.18, 4, "liftstone")

    # Crystalline ice-citadel bridge.
    mb.box((0, y_of(0.75), deck_z + 1.2), (4.2, 4.2, 2.1), "cloud_shade", top_scale=0.78)
    _crystal_spire(mb, (0, y_of(0.76), deck_z + 2.1), (0, y_of(0.82), deck_z + 5.2), 0.85, 0.45, 5, "liftstone")

    # Faceted glacier-envelope prism overhead with aurora dorsal sail.
    env_z = deck_z + 7.6
    rings = _q(hq, 8, 5)
    sides = _q(hq, 8, 6)
    ice_bag = lambda i, j: "liftstone" if i in (0, rings - 1) else ("cloud" if j % 2 else "cloud_shade")
    gasbag(mb, 0, 0.3, env_z, 18.0, 3.4, sides, rings, ice_bag, flat=0.85)
    mb.plate([(0, -5.0, env_z + 2.5), (0, -0.5, env_z + 5.2), (0, 5.5, env_z + 4.0), (0, 6.5, env_z + 2.0)], 0.1, "liftstone")
    for y in (-3.4, 3.2):
        for sign in (1, -1):
            rope(mb, (sign * 2.4, y, deck_z), (sign * 1.8, y * 0.85, env_z - 2.6), 0.08, hq, "silver")

    for sign, label in ((1, "L"), (-1, "R")):
        wing(mb, sign, sign * 2.6, y_of(0.38), y_of(0.64), 2.2, 4.4, 1.5, hq, color="cloud", spar="gem_blue", thick=0.1)
        nacelle(mb, sign * 4.6, y_of(0.78), 2.2, 1.35, 0.58, hq, label, root_x=sign * 2.5, color="silver")

    broadside(mb, [y_of(t) for t in (0.34, 0.5, 0.66)], 2.3, lambda y: width_fn((y + length / 2) / length), 0.95, 0.14, hq, color="silver", carriage="gem_blue")
    base_sockets(mb, half, deck_z, env_z, y_of(0.76), deck_z + 3.2)
    mb.socket("lift_core", (0, 0.0, 2.0))
    mb.socket("helm", (0, y_of(0.68), deck_z + 0.1))


# ==============================================================================
# CATEGORY 2: SPACESHIPS & SCI-FI CRAFT
# ==============================================================================

def starlight_cruiser(mb, hq):
    """7. Spaceship: Deep-space battlecruiser with hammerhead bridge, warp-ring drive and dorsal beam turrets."""
    length, half, deck_z = 23.0, 3.6, 3.0
    y_of = lambda t: -length / 2 + t * length
    # Angular terraced sci-fi wedge hull.
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 10, 6), bow_t=0.45, stern_t=0.82, stern_taper=0.15, keel_bow=0.35, keel_stern=0.25)
    paints = {0: "steel", 1: "iron_light", 2: "plasma", 3: "silver", 4: "faction_a"} if hq else {0: "steel", 1: "silver", 2: "faction_a"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.35)

    # Hammerhead sensor prow with glowing bridge slit.
    mb.box((0, y_of(0.06), 2.5), (4.6, 2.2, 1.1), "steel", top_scale=0.88)
    mb.box((0, y_of(0.06) - 1.12, 2.55), (3.6, 0.1, 0.35), "liftstone")
    mb.tube((0, y_of(0.06) - 1.1, 2.1), (0, y_of(0.0) - 3.2, 2.1), 0.18, 0.08, sides=_q(hq, 6, 4), color="silver")
    mb.socket("muzzle_F0", (0, y_of(0.0) - 3.25, 2.1))

    # Stepped command superstructure and twin dorsal plasma turrets.
    mb.box((0, y_of(0.68), deck_z + 0.9), (4.2, 6.8, 1.4), "silver", top_scale=0.86)
    mb.box((0, y_of(0.74), deck_z + 2.0), (2.6, 3.8, 1.1), "faction_a", top_scale=0.82)
    _turret(mb, 0, y_of(0.32), deck_z, 0.95, 0.65, 2, 1.6, 0.11, hq, "silver", "steel")
    _turret(mb, 0, y_of(0.48), deck_z + 0.3, 0.95, 0.65, 2, 1.6, 0.11, hq, "silver", "steel")

    # Giant glowing Alcubierre warp-ring encircling the ship's waist.
    env_z = deck_z + 2.2
    _torus_ring(mb, 0, y_of(0.58), env_z, 6.2, 0.55, _q(hq, 16, 10), _q(hq, 6, 4), "steel", rot_x=math.pi / 2)
    _torus_ring(mb, 0, y_of(0.58) - 0.35, env_z, 5.8, 0.22, _q(hq, 16, 8), 4, "plasma", rot_x=math.pi / 2)
    for sign in (1, -1):
        mb.box((sign * 4.2, y_of(0.58), deck_z - 0.2), (3.8, 1.1, 0.45), "steel")

    # Swept delta strike-wings and quad rear plasma thruster cones.
    for sign, label in ((1, "L"), (-1, "R")):
        wing(mb, sign, sign * 3.1, y_of(0.42), y_of(0.84), 2.1, 5.2, 0.4, hq, color="silver", spar="steel", thick=0.12, ribs=1)
        nacelle(mb, sign * 4.8, y_of(0.84), 2.1, 1.8, 0.72, hq, label, root_x=sign * 3.2, color="steel", index=0)
        mb.sphere((sign * 4.8, y_of(0.84) + 1.82, 2.1), (0.45, 0.15, 0.45), _q(hq, 6, 4), 3, "plasma")
        mb.socket(f"afterburner_{label}", (sign * 4.8, y_of(0.84) + 1.9, 2.1))

    broadside(mb, [y_of(t) for t in (0.28, 0.44, 0.6, 0.76)], 2.2, lambda y: width_fn((y + length / 2) / length), 0.95, 0.12, hq, color="silver", carriage="steel")
    base_sockets(mb, half, deck_z, env_z + 4.0, y_of(0.74), deck_z + 2.8)
    mb.socket("lift_core", (0, y_of(0.58), env_z))
    mb.socket("helm", (0, y_of(0.74), deck_z + 2.6))


def nebula_saucer(mb, hq):
    """8. Spaceship: Flying saucer mothership with glowing grav-pad rim, command dome and ventral tractor core."""
    radius, deck_z = 9.2, 2.8
    sides = _q(hq, 20, 10)
    # Main lenticular saucer body revolved around Z.
    profile = [
        (1.2, 0.4),
        (3.8, 0.7),
        (7.2, 1.4),
        (radius, 2.1),
        (radius * 0.96, 2.45),
        (6.4, deck_z),
        (3.2, deck_z + 0.55),
    ]
    saucer_paint = lambda i, j: "plasma" if (i == 3 and j % 2 == 0) else ("silver" if i in (2, 4) else ("faction_a" if i == 5 else "steel"))
    mb.lathe(profile, sides, saucer_paint, smooth=True)

    # Upper observation & bridge dome.
    mb.sphere((0, 0, deck_z + 0.6), (2.9, 2.9, 1.55), _q(hq, 12, 8), _q(hq, 6, 4), "liftstone")
    _torus_ring(mb, 0, 0, deck_z + 0.55, 3.05, 0.24, _q(hq, 12, 8), 4, "gold")
    # Ventral glowing tractor/antigrav dome.
    mb.sphere((0, 0, 0.55), (2.2, 2.2, 0.55), _q(hq, 10, 6), 4, "plasma")

    # Forward twin pulse-cannon mandibles extending to -Y so bow direction is unmistakable.
    for sign in (1, -1):
        mb.box((sign * 1.8, -radius * 0.82, 2.15), (1.1, 3.4, 0.55), "steel", top_scale=0.8)
        mb.tube((sign * 1.8, -radius - 0.4, 2.15), (sign * 1.8, -radius - 2.4, 2.15), 0.18, 0.1, sides=_q(hq, 6, 4), color="silver")
    mb.socket("muzzle_F0", (0, -radius - 2.4, 2.15))

    # Rear impulse nacelles and stabilizer fin.
    for sign, label in ((1, "L"), (-1, "R")):
        nacelle(mb, sign * 4.2, radius * 0.78, 2.2, 1.6, 0.65, hq, label, root_x=sign * 2.5, color="silver")
        mb.socket(f"afterburner_{label}", (sign * 4.2, radius * 0.78 + 1.65, 2.2))
    mb.plate([(0, 2.8, deck_z + 0.4), (0, 6.8, deck_z + 2.8), (0, 8.2, deck_z + 2.4), (0, 6.2, deck_z + 0.1)], 0.14, "faction_c")

    # Rim broadside plasma emitters.
    broadside(mb, (-3.6, 0.0, 3.6), 2.15, lambda y: math.sqrt(max(4.0, radius * radius - y * y * 0.65)), 0.75, 0.13, hq, color="silver", carriage="steel")
    base_sockets(mb, radius * 0.85, deck_z, deck_z + 1.6, 4.5, deck_z + 1.2)
    mb.socket("lift_core", (0, 0, 1.2))
    mb.socket("helm", (0, -1.2, deck_z + 1.4))


def void_interceptor(mb, hq):
    """9. Spaceship: Twin-mandible space interceptor with suspended plasma orb and X-wing quad strike foils."""
    length, half, deck_z = 19.0, 2.2, 2.5
    y_of = lambda t: -length / 2 + t * length
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 10, 6), bow_t=0.35, stern_t=0.75)
    paints = {0: "abyss", 1: "steel", 2: "faction_a", 3: "faction_b", 4: "abyss"} if hq else {0: "abyss", 1: "steel", 2: "faction_a"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.5)

    # Split forward mandibles gripping a glowing plasma singularity orb.
    bow_y = y_of(0.0)
    for sign in (1, -1):
        mb.path(
            [(sign * 1.4, y_of(0.18), 2.0), (sign * 1.65, bow_y - 1.2, 2.05), (sign * 1.1, bow_y - 4.4, 2.1)],
            [0.65, 0.48, 0.12],
            _q(hq, 6, 4),
            "steel",
        )
    mb.sphere((0, bow_y - 2.4, 2.05), 0.78, _q(hq, 8, 6), 4, "plasma")
    mb.socket("muzzle_F0", (0, bow_y - 4.4, 2.1))

    # Armored angular cockpit canopy.
    mb.box((0, y_of(0.55), deck_z + 0.65), (2.2, 5.2, 1.1), "abyss", top_scale=0.75)
    mb.box((0, y_of(0.45), deck_z + 0.72), (1.6, 2.4, 0.75), "liftstone", top_scale=0.7)

    # X-Wing style quad strike foils (upper and lower swept wings per side) with wingtip laser cannons.
    for sign, label in ((1, "L"), (-1, "R")):
        for vz, lift in ((2.3, 2.1), (1.5, -1.1)):
            wing(mb, sign, sign * 1.8, y_of(0.42), y_of(0.76), vz, 5.6, lift, hq, color="faction_a", spar="steel", thick=0.09, ribs=1)
            tip_x = sign * 7.35
            mb.tube((tip_x, y_of(0.76), vz + lift * 0.92), (tip_x, y_of(0.48), vz + lift * 0.98), 0.14, 0.07, sides=4, color="silver")
        nacelle(mb, sign * 2.8, y_of(0.82), 2.1, 1.7, 0.64, hq, label, root_x=sign * 1.6, color="steel")
        mb.socket(f"afterburner_{label}", (sign * 2.8, y_of(0.82) + 1.75, 2.1))

    broadside(mb, [y_of(t) for t in (0.36, 0.62)], 2.0, lambda y: width_fn((y + length / 2) / length), 0.85, 0.11, hq, color="silver", carriage="abyss")
    base_sockets(mb, half, deck_z, deck_z + 2.2, y_of(0.78), deck_z + 1.4)
    mb.socket("lift_core", (0, bow_y - 2.4, 2.05))
    mb.socket("helm", (0, y_of(0.48), deck_z + 0.2))


def orbital_carrier(mb, hq):
    """10. Spaceship: Twin-boom orbital drone carrier with lit launch runway and starboard command tower."""
    length, half, deck_z = 27.0, 5.2, 3.8
    y_of = lambda t: -length / 2 + t * length
    # Wide twin-boom carrier hull with open bow flight slot.
    stations, _ = _hull_stations(length, half, deck_z, _q(hq, 10, 6), bow_t=0.22, stern_t=0.82, stern_taper=0.18)
    paints = {0: "steel", 1: "iron", 2: "faction_a", 3: "silver", 4: "steel"} if hq else {0: "steel", 1: "faction_a", 2: "silver"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.25)

    # Full-length armored flight deck plate & glowing plasma launch runway strip.
    mb.box((0, 0.0, deck_z + 0.25), (half * 2.05, length * 0.92, 0.45), "iron")
    mb.box((0, -0.5, deck_z + 0.5), (1.1, length * 0.82, 0.06), "liftstone")
    # Twin bow catapult prongs.
    for sign in (1, -1):
        mb.box((sign * 3.2, y_of(0.02) - 1.4, deck_z + 0.2), (2.4, 3.2, 0.65), "steel", top_scale=0.88)
    mb.socket("muzzle_F0", (0, y_of(0.0) - 2.2, deck_z + 0.5))

    # Starboard (-X) island bridge tower with radar arrays.
    ix = -half * 0.72
    mb.box((ix, y_of(0.62), deck_z + 1.8), (2.1, 6.2, 2.7), "steel", top_scale=0.86)
    mb.box((ix, y_of(0.6), deck_z + 3.6), (1.6, 3.4, 1.2), "faction_c", top_scale=0.84)
    mb.tube((ix, y_of(0.6), deck_z + 4.1), (ix, y_of(0.6), deck_z + 6.2), 0.14, 0.06, sides=4, color="silver")
    if hq:
        mb.box((ix + 1.08, y_of(0.55), deck_z + 2.4), (0.08, 2.2, 0.45), "liftstone")
        # Two parked mini strike-fighters on the flight deck.
        for fy in (-4.5, 2.5):
            mb.box((2.2, fy, deck_z + 0.72), (1.8, 2.1, 0.38), "faction_a", top_scale=0.6)

    # Twin ventral/side grav-lift pontoons.
    env_z = 2.0
    for sign, label in ((1, "L"), (-1, "R")):
        gasbag(mb, sign * (half + 1.8), 0.0, env_z, 19.0, 1.65, _q(hq, 10, 6), _q(hq, 8, 5), striped("steel", "faction_a", "silver", _q(hq, 8, 5)), flat=0.75)
        mb.box((sign * (half + 0.4), 0.0, 2.2), (2.2, 10.0, 0.55), "iron")
        nacelle(mb, sign * (half + 1.8), y_of(0.86), 2.1, 1.8, 0.78, hq, label, color="silver", index=0)
        mb.socket(f"afterburner_{label}", (sign * (half + 1.8), y_of(0.86) + 1.85, 2.1))
        mb.socket(f"glider_launch_{label}", (sign * 2.2, y_of(0.2), deck_z + 0.6))

    broadside(mb, [y_of(t) for t in (0.25, 0.45, 0.65, 0.82)], 3.1, lambda _y: half + 0.3, 1.0, 0.14, hq, color="silver", carriage="steel")
    base_sockets(mb, half + 1.8, deck_z + 0.5, deck_z + 3.6, y_of(0.65), deck_z + 4.3)
    mb.socket("lift_core", (0, 0.0, 2.1))
    mb.socket("helm", (ix, y_of(0.6), deck_z + 3.6))


def plasma_lancer(mb, hq):
    """11. Spaceship: Spinal-mount orbital railgun destroyer built around a 26m magnetic accelerator barrel."""
    length, half, deck_z = 25.0, 2.4, 2.9
    y_of = lambda t: -length / 2 + t * length
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 10, 6), bow_t=0.38, stern_t=0.78)
    paints = {0: "iron", 1: "steel", 2: "faction_a", 3: "plasma", 4: "silver"} if hq else {0: "iron", 1: "steel", 2: "faction_a"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.45)

    # Massive spinal railgun running from midships 8m past the bow, with glowing accelerator rings.
    barrel_z = deck_z + 0.75
    mb.box((0, y_of(0.35), barrel_z), (1.5, 14.0, 0.95), "steel", top_scale=0.82)
    mb.tube((0, y_of(0.2), barrel_z + 0.1), (0, y_of(0.0) - 7.5, barrel_z + 0.1), 0.38, 0.28, sides=_q(hq, 8, 5), color="silver")
    mb.tube((0, y_of(0.2), barrel_z + 0.1), (0, y_of(0.0) - 7.6, barrel_z + 0.1), 0.18, 0.18, sides=4, color="plasma")
    for ry in _q(hq, (-15.5, -13.0, -10.5, -8.0, -5.5), (-14.5, -10.0, -5.5)):
        _torus_ring(mb, 0, ry, barrel_z + 0.1, 0.78, 0.12, _q(hq, 8, 6), 4, "plasma", rot_x=math.pi / 2)
    mb.socket("siege_muzzle", (0, y_of(0.0) - 7.65, barrel_z + 0.1))
    mb.socket("muzzle_F0", (0, y_of(0.0) - 7.65, barrel_z + 0.1))

    # Aft reactor dome and bridge tower.
    mb.box((0, y_of(0.75), deck_z + 1.1), (3.1, 4.8, 1.7), "steel", top_scale=0.84)
    mb.sphere((0, y_of(0.58), deck_z + 1.0), (1.1, 1.6, 0.9), _q(hq, 8, 5), 4, "plasma")

    # Side grav-cylinders and angled radiator wings.
    env_z = deck_z + 1.4
    for sign, label in ((1, "L"), (-1, "R")):
        gasbag(mb, sign * 4.2, 1.2, env_z, 15.0, 1.5, _q(hq, 10, 6), _q(hq, 8, 5), striped("steel", "plasma", "silver", _q(hq, 8, 5)), flat=0.8)
        mb.box((sign * 2.6, 1.2, 2.4), (2.8, 3.6, 0.42), "iron")
        wing(mb, sign, sign * 4.4, y_of(0.45), y_of(0.78), env_z, 4.2, 1.8, hq, color="faction_b", spar="silver", thick=0.08, ribs=1)
        nacelle(mb, sign * 4.2, y_of(0.84), env_z - 0.2, 1.6, 0.65, hq, label, color="silver")
        mb.socket(f"afterburner_{label}", (sign * 4.2, y_of(0.84) + 1.65, env_z - 0.2))

    broadside(mb, [y_of(t) for t in (0.32, 0.5, 0.68)], 2.2, lambda y: width_fn((y + length / 2) / length), 0.85, 0.12, hq, color="silver", carriage="steel")
    base_sockets(mb, 4.2, deck_z, env_z + 2.0, y_of(0.75), deck_z + 2.3)
    mb.socket("lift_core", (0, y_of(0.58), deck_z + 1.0))
    mb.socket("helm", (0, y_of(0.72), deck_z + 2.0))


def solar_ark(mb, hq):
    """12. Spaceship: Golden crescent solar-sailer with spherical astrolabe core and radiant upper/lower sails."""
    length, half, deck_z = 20.0, 2.8, 3.2
    y_of = lambda t: -length / 2 + t * length
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 12, 6), bow_t=0.4, stern_t=0.7, keel_bow=0.6, keel_stern=0.5)
    paints = {0: "gold_dark", 1: "enamel", 2: "gold", 3: "faction_a", 4: "gold"} if hq else {0: "gold_dark", 1: "enamel", 2: "gold"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.65)

    # Crescent golden prow & sternhorn.
    mb.path([(0, y_of(0.06), 2.8), (0, y_of(0.0) - 2.6, 4.2), (0, y_of(0.0) - 1.2, 6.2)], [0.42, 0.25, 0.05], _q(hq, 6, 4), "gold")
    mb.socket("muzzle_F0", (0, y_of(0.0) - 2.6, 4.2))
    mb.box((0, y_of(0.78), deck_z + 1.1), (3.8, 4.2, 1.9), "enamel", top_scale=0.84)
    mb.box((0, y_of(0.78), deck_z + 2.12), (4.1, 4.5, 0.2), "gold")

    # Central glowing solar-astrolabe sphere suspended above the deck.
    env_z = deck_z + 6.8
    mb.sphere((0, 0.0, env_z), 2.3, _q(hq, 12, 6), _q(hq, 8, 4), "lamp")
    _torus_ring(mb, 0, 0.0, env_z, 3.1, 0.18, _q(hq, 12, 8), 4, "gold", rot_x=0.35)
    _torus_ring(mb, 0, 0.0, env_z, 3.5, 0.18, _q(hq, 12, 8), 4, "brass", rot_y=0.45)
    mb.tube((0, 0.0, deck_z - 0.1), (0, 0.0, env_z - 2.2), 0.28, 0.22, sides=_q(hq, 6, 4), color="gold")

    # Sweeping golden diamond solar-collector sails (upper, side, and ventral keel fin).
    for y, h, w in ((-3.8, 9.2, 5.2), (3.4, 8.6, 4.6)):
        mast(mb, 0, y, deck_z, deck_z + h, 0.18, hq, yards=((deck_z + h * 0.55, w),))
        mb.plate([(0, y - 0.1, deck_z + h), (-w, y - 0.35, deck_z + h * 0.55), (0, y - 0.1, deck_z + 1.1), (w, y - 0.35, deck_z + h * 0.55)], 0.06, "gold" if y < 0 else "lamp")
    for sign, label in ((1, "L"), (-1, "R")):
        wing(mb, sign, sign * 2.4, y_of(0.32), y_of(0.66), 2.4, 6.2, 1.8, hq, color="gold", spar="gold_dark", thick=0.08, ribs=2)
        nacelle(mb, sign * 4.2, y_of(0.8), 2.3, 1.4, 0.56, hq, label, root_x=sign * 2.2, color="gold")

    broadside(mb, [y_of(t) for t in (0.34, 0.5, 0.66)], 2.3, lambda y: width_fn((y + length / 2) / length), 0.9, 0.12, hq, color="gold", carriage="enamel")
    base_sockets(mb, half, deck_z, env_z, y_of(0.78), deck_z + 2.4)
    mb.socket("lift_core", (0, 0.0, env_z))
    mb.socket("helm", (0, y_of(0.7), deck_z + 0.15))


# ==============================================================================
# CATEGORY 3: MODERN & WWI/WWII NAVAL BATTLESHIPS (Part 1: 13-15)
# ==============================================================================

def steel_dreadnought(mb, hq):
    """13. Modern Battleship: Heavy naval battleship with triple-gun main turrets, pagoda bridge and armored blisters."""
    length, half, deck_z = 28.0, 4.4, 3.8
    y_of = lambda t: -length / 2 + t * length
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 14, 7), bow_t=0.38, stern_t=0.76, stern_taper=0.25, sheer_bow=0.18, sheer_stern=0.05)
    paints = {0: "rust_dark", 1: "iron", 2: "steel", 3: "iron_light", 4: "steel"} if hq else {0: "rust_dark", 1: "steel", 2: "iron_light"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.42)

    # Superfiring triple-barrel naval gun turrets (A and B forward, X aft).
    _turret(mb, 0, y_of(0.19), deck_z, 1.35, 0.85, 3, 2.6, 0.13, hq, "steel", "iron", socket_prefix="muzzle_F")
    mb.box((0, y_of(0.31), deck_z + 0.5), (2.7, 2.7, 1.0), "steel")
    _turret(mb, 0, y_of(0.31), deck_z + 0.95, 1.3, 0.82, 3, 2.4, 0.13, hq, "steel", "iron")
    _turret(mb, 0, y_of(0.83), deck_z, 1.35, 0.85, 3, 2.4, 0.13, hq, "steel", "iron")

    # Stepped armored pagoda bridge tower & twin raked naval funnels.
    mb.box((0, y_of(0.45), deck_z + 1.2), (3.8, 3.6, 2.4), "steel", top_scale=0.88)
    mb.box((0, y_of(0.44), deck_z + 3.1), (2.8, 2.4, 1.6), "iron_light", top_scale=0.84)
    mb.box((0, y_of(0.43), deck_z + 4.4), (2.1, 1.6, 1.1), "steel", top_scale=0.82)
    if hq:
        mb.box((0, y_of(0.43) - 0.82, deck_z + 4.5), (1.6, 0.08, 0.32), "lamp")
    for fy in (y_of(0.57), y_of(0.68)):
        mb.tube((0, fy, deck_z + 0.4), (0, fy + 0.55, deck_z + 3.8), 0.68, 0.58, sides=_q(hq, 8, 5), color="steel")
        mb.tube((0, fy + 0.55, deck_z + 3.8), (0, fy + 0.6, deck_z + 4.15), 0.59, 0.55, sides=_q(hq, 8, 5), color="abyss")

    # Low-slung armored zeppelin lift blisters along both flanks.
    env_z = 2.4
    for sign, label in ((1, "L"), (-1, "R")):
        gasbag(mb, sign * (half + 1.5), 0.2, env_z, 21.0, 1.65, _q(hq, 10, 6), _q(hq, 8, 5), striped("steel", "iron", "faction_a", _q(hq, 8, 5)), flat=0.82)
        for by in (-5.0, 0.0, 5.0):
            mb.box((sign * (half + 0.2), by, 2.5), (1.8, 1.4, 0.7), "iron")
        nacelle(mb, sign * (half + 1.5), y_of(0.88), 2.1, 1.6, 0.72, hq, label, color="iron", index=0)

    broadside(mb, [y_of(t) for t in (0.38, 0.48, 0.58, 0.68, 0.76)], 3.2, lambda y: width_fn((y + length / 2) / length) + 1.2, 1.1, 0.14, hq, color="iron", carriage="steel")
    base_sockets(mb, half + 1.5, deck_z, deck_z + 4.5, y_of(0.57) + 0.6, deck_z + 4.2)
    mb.socket("siege_muzzle", (0, y_of(0.19) - 3.3, deck_z + 0.65))
    mb.socket("lift_core", (0, y_of(0.52), 2.2))
    mb.socket("helm", (0, y_of(0.44), deck_z + 3.1))


def aegis_destroyer(mb, hq):
    """14. Modern Battleship: Stealth guided-missile destroyer with faceted tumblehome hull and VLS missile cells."""
    length, half, deck_z = 24.0, 3.5, 3.5
    y_of = lambda t: -length / 2 + t * length
    # Tumblehome stealth hull (slopes inward towards deck).
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 10, 6), bow_t=0.42, stern_t=0.78, stern_taper=0.2, sheer_bow=0.1, sheer_stern=0.0)
    paints = {0: "storm_dark", 1: "iron", 2: "steel", 3: "steel"} if hq else {0: "storm_dark", 1: "iron", 2: "steel"}
    shell(mb, stations, _q(hq, 4, 3), lambda r: paints[r], power=0.25, tumble=0.22)

    # Stealth faceted railgun turret & VLS vertical missile block on the foredeck.
    mb.box((0, y_of(0.2), deck_z + 0.5), (1.9, 2.4, 0.95), "steel", top_scale=0.65)
    mb.tube((0, y_of(0.2) - 0.8, deck_z + 0.55), (0, y_of(0.2) - 3.4, deck_z + 0.72), 0.16, 0.11, sides=4, color="iron")
    mb.socket("muzzle_F0", (0, y_of(0.2) - 3.45, deck_z + 0.72))

    # VLS vertical launch missile cells.
    vls_y = y_of(0.33)
    mb.box((0, vls_y, deck_z + 0.22), (2.4, 2.4, 0.42), "iron")
    for sign, side_tag in ((1, "L"), (-1, "R")):
        for r in range(_q(hq, 2, 1)):
            my = vls_y + (r - 0.5) * 0.85
            mb.box((sign * 0.6, my, deck_z + 0.45), (0.55, 0.55, 0.08), "ember" if hq and r == 0 else "steel")
            mb.socket(f"missile_{side_tag}0{r}", (sign * 0.6, my, deck_z + 0.5))

    # Integrated stealth pyramid mast with octagon SPY radar arrays.
    mb.box((0, y_of(0.54), deck_z + 1.8), (4.2, 6.2, 3.6), "steel", top_scale=0.58)
    mb.tube((0, y_of(0.52), deck_z + 3.5), (0, y_of(0.52), deck_z + 5.6), 0.45, 0.08, sides=4, color="iron_light")
    if hq:
        mb.box((0, y_of(0.54) - 2.45, deck_z + 2.2), (1.8, 0.1, 0.35), "liftstone")
        for sign in (1, -1):
            mb.box((sign * 1.65, y_of(0.48), deck_z + 2.1), (0.12, 1.2, 1.0), "silver")

    # Outrigger stealth ducted lift pods & aft helipad.
    for sign, label in ((1, "L"), (-1, "R")):
        mb.box((sign * 4.4, y_of(0.62), 2.3), (2.2, 8.5, 0.85), "steel", top_scale=0.78)
        _torus_ring(mb, sign * 4.6, y_of(0.52), 2.35, 0.85, 0.16, _q(hq, 8, 6), 4, "iron")
        mb.sphere((sign * 4.6, y_of(0.52), 2.3), (0.65, 0.65, 0.15), _q(hq, 6, 4), 3, "liftstone")
        nacelle(mb, sign * 4.4, y_of(0.84), 2.3, 1.4, 0.58, hq, label, color="iron")
        mb.socket(f"afterburner_{label}", (sign * 4.4, y_of(0.84) + 1.45, 2.3))

    broadside(mb, [y_of(t) for t in (0.38, 0.54, 0.7)], 2.6, lambda y: width_fn((y + length / 2) / length), 0.85, 0.11, hq, color="iron", carriage="steel")
    base_sockets(mb, half + 1.2, deck_z, deck_z + 3.6, y_of(0.62), deck_z + 3.6)
    mb.socket("lift_core", (0, y_of(0.54), 2.2))
    mb.socket("helm", (0, y_of(0.48), deck_z + 2.2))


def sky_submarine(mb, hq):
    """15. Modern Battleship: Cloud-diving U-boat attack submarine with conning tower, periscopes and torpedo tubes."""
    length, radius, z_mid = 24.0, 2.35, 2.6
    y_of = lambda t: -length / 2 + t * length
    # Cylindrical cigar pressure hull with flat slatted casing deck on top.
    rings = _q(hq, 12, 6)
    sides = _q(hq, 14, 8)
    sub_paint = lambda i, j: "rust_dark" if j in (sides // 2 - 1, sides // 2) else ("iron" if i in (0, rings - 1) else "storm_dark")
    gasbag(mb, 0, 0.0, z_mid, length, radius, sides, rings, sub_paint, flat=0.95)
    deck_z = z_mid + radius * 0.82
    mb.box((0, -0.4, deck_z - 0.25), (2.2, length * 0.76, 0.55), "iron", top_scale=0.82)

    # Bow torpedo shutter doors & forward dive planes.
    for sign in (1, -1):
        mb.tube((sign * 0.55, y_of(0.06), z_mid + 0.1), (sign * 0.55, y_of(0.0) - 0.6, z_mid + 0.1), 0.22, 0.18, sides=5, color="brass")
        mb.plate([(sign * 1.4, y_of(0.14), z_mid + 0.2), (sign * 4.2, y_of(0.18), z_mid + 0.25), (sign * 4.0, y_of(0.24), z_mid + 0.2), (sign * 1.3, y_of(0.24), z_mid + 0.15)], 0.1, "iron")
    mb.socket("muzzle_F0", (0, y_of(0.0) - 0.65, z_mid + 0.1))

    # Streamlined sail / conning tower with sailplanes and twin periscopes.
    sail_y = y_of(0.44)
    mb.box((0, sail_y, deck_z + 1.35), (1.5, 4.2, 2.7), "storm_dark", top_scale=0.82)
    for sign in (1, -1):
        mb.plate([(sign * 0.68, sail_y - 0.8, deck_z + 1.6), (sign * 2.6, sail_y - 0.4, deck_z + 1.65), (sign * 2.5, sail_y + 0.4, deck_z + 1.6), (sign * 0.68, sail_y + 0.6, deck_z + 1.55)], 0.09, "iron")
    mb.tube((0, sail_y - 0.6, deck_z + 2.6), (0, sail_y - 0.6, deck_z + 4.4), 0.1, 0.07, sides=4, color="silver")
    mb.tube((0, sail_y + 0.4, deck_z + 2.6), (0, sail_y + 0.4, deck_z + 3.9), 0.14, 0.1, sides=4, color="iron")

    # Fore and aft naval deck guns.
    _turret(mb, 0, y_of(0.24), deck_z, 0.65, 0.45, 1, 1.5, 0.1, hq, "iron", "steel")
    _turret(mb, 0, y_of(0.68), deck_z, 0.65, 0.45, 1, 1.5, 0.1, hq, "iron", "steel")

    # Side ballast lift tanks and cruciform stern rudder + twin shrouded propulsors.
    for sign, label in ((1, "L"), (-1, "R")):
        gasbag(mb, sign * 2.6, 0.2, z_mid - 0.2, 14.0, 1.1, _q(hq, 8, 5), _q(hq, 8, 5), "faction_a", flat=0.85)
        nacelle(mb, sign * 2.8, y_of(0.86), z_mid, 1.3, 0.55, hq, label, root_x=sign * 1.4, color="brass")
    fins(mb, 0, y_of(0.82), z_mid + 0.8, 3.2, 2.8, 0.12, "storm_dark")

    broadside(mb, [y_of(t) for t in (0.3, 0.52, 0.72)], z_mid + 0.2, lambda _y: 2.8, 0.8, 0.12, hq, color="iron", carriage="storm_dark")
    base_sockets(mb, 2.8, deck_z, z_mid, sail_y + 0.4, deck_z + 3.9)
    mb.socket("lift_core", (0, 0.0, z_mid))
    mb.socket("helm", (0, sail_y, deck_z + 2.7))



def fleet_carrier(mb, hq):
    """16. Modern Battleship: Flat-top naval aircraft carrier with angled flight deck, island tower and sponson flak."""
    length, half, deck_z = 29.0, 4.8, 4.2
    y_of = lambda t: -length / 2 + t * length
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 12, 6), bow_t=0.32, stern_t=0.78, stern_taper=0.22, sheer_bow=0.05, sheer_stern=0.02)
    paints = {0: "rust_dark", 1: "iron", 2: "steel", 3: "steel", 4: "iron_light"} if hq else {0: "rust_dark", 1: "iron", 2: "steel"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.35)

    # Full-width armored flight deck overhang & port-side angled landing deck.
    mb.box((0.4, 0.0, deck_z + 0.25), (half * 2.25, length * 0.96, 0.42), "iron")
    mb.box((1.8, 1.5, deck_z + 0.27), (4.2, length * 0.65, 0.4), "iron")
    # Centerline & angled runway painted stripes.
    mb.box((0.0, 0.0, deck_z + 0.48), (0.35, length * 0.88, 0.04), "cloth_white")
    mb.box((2.4, 1.5, deck_z + 0.48), (0.35, length * 0.58, 0.04), "gold")
    # Ski-jump bow ramp & bow CIWS gun.
    mb.box((-0.6, y_of(0.04) - 0.8, deck_z + 0.55), (4.2, 3.2, 0.55), "iron", top_scale=0.88)
    _turret(mb, -2.2, y_of(0.06), deck_z + 0.45, 0.55, 0.45, 1, 1.2, 0.09, hq, "steel", "iron", socket_prefix="muzzle_F")

    # Starboard (-X) island superstructure, bridge windows, funnel & radar mast.
    ix = -half * 0.88
    mb.box((ix, y_of(0.48), deck_z + 1.8), (2.0, 6.8, 2.8), "steel", top_scale=0.88)
    mb.box((ix, y_of(0.42), deck_z + 3.5), (1.7, 3.2, 1.1), "iron_light", top_scale=0.86)
    mb.tube((ix, y_of(0.56), deck_z + 3.0), (ix, y_of(0.58), deck_z + 4.8), 0.55, 0.48, sides=_q(hq, 6, 4), color="steel")
    mb.tube((ix, y_of(0.44), deck_z + 3.9), (ix, y_of(0.44), deck_z + 6.2), 0.14, 0.06, sides=4, color="silver")
    if hq:
        # Three parked biplane/strike planes on the flight deck.
        for px, py in ((2.4, -5.5), (2.6, 0.5), (2.2, 6.2)):
            mb.box((px, py, deck_z + 0.68), (2.2, 0.55, 0.25), "faction_a")
            mb.box((px, py, deck_z + 0.68), (0.5, 1.8, 0.35), "steel")

    # Twin under-deck rigid lift dirigibles & stern engine nacelles.
    for sign, label in ((1, "L"), (-1, "R")):
        gasbag(mb, sign * (half + 1.4), 0.5, 2.3, 21.0, 1.7, _q(hq, 10, 6), _q(hq, 8, 5), striped("steel", "iron", "faction_a", _q(hq, 8, 5)), flat=0.82)
        nacelle(mb, sign * (half + 1.4), y_of(0.88), 2.2, 1.7, 0.75, hq, label, color="iron", index=0)
        mb.socket(f"glider_launch_{label}", (sign * 1.8, y_of(0.18), deck_z + 0.55))

    broadside(mb, [y_of(t) for t in (0.26, 0.44, 0.62, 0.8)], 3.5, lambda y: width_fn((y + length / 2) / length) + 0.8, 0.95, 0.13, hq, color="iron", carriage="steel")
    base_sockets(mb, half + 1.4, deck_z + 0.45, deck_z + 4.2, y_of(0.56), deck_z + 4.8)
    mb.socket("lift_core", (0, 0.5, 2.3))
    mb.socket("helm", (ix, y_of(0.42), deck_z + 3.5))


def heavy_cruiser(mb, hq):
    """17. Modern Battleship: Armored pocket battleship with superfiring twin turrets, catapult and dorsal dirigible."""
    length, half, deck_z = 24.0, 3.6, 3.5
    y_of = lambda t: -length / 2 + t * length
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 12, 6), bow_t=0.38, stern_t=0.76, stern_taper=0.22)
    paints = {0: "rust_dark", 1: "iron", 2: "navy", 3: "steel", 4: "iron_light"} if hq else {0: "rust_dark", 1: "navy", 2: "steel"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.45)

    # Twin superfiring forward turrets + aft turret.
    _turret(mb, 0, y_of(0.18), deck_z, 1.05, 0.72, 2, 2.1, 0.12, hq, "steel", "iron", socket_prefix="muzzle_F")
    mb.box((0, y_of(0.3), deck_z + 0.45), (2.1, 2.2, 0.9), "steel")
    _turret(mb, 0, y_of(0.3), deck_z + 0.85, 1.0, 0.68, 2, 1.9, 0.12, hq, "steel", "iron")
    _turret(mb, 0, y_of(0.82), deck_z, 1.05, 0.72, 2, 2.0, 0.12, hq, "steel", "iron")

    # Armored bridge citadel, raked funnel & midships floatplane catapult.
    mb.box((0, y_of(0.45), deck_z + 1.2), (3.1, 3.2, 2.2), "steel", top_scale=0.84)
    mb.box((0, y_of(0.44), deck_z + 2.7), (2.1, 2.0, 1.1), "navy", top_scale=0.82)
    mb.tube((0, y_of(0.58), deck_z + 0.3), (0, y_of(0.6), deck_z + 3.4), 0.58, 0.48, sides=_q(hq, 8, 5), color="steel")
    mb.box((0, y_of(0.69), deck_z + 0.45), (3.8, 1.2, 0.35), "iron")

    # Rigid naval zeppelin overhead with steel mooring struts.
    env_z = deck_z + 7.2
    rings = _q(hq, 10, 6)
    gasbag(mb, 0, 0.2, env_z, 21.0, 3.4, _q(hq, 12, 8), rings, striped("steel", "navy", "faction_a", rings), flat=0.92)
    fins(mb, 0, 7.8, env_z, 3.6, 2.6, 0.12, "navy")
    for y in (-4.5, 4.2):
        for sign in (1, -1):
            rope(mb, (sign * 2.4, y, deck_z), (sign * 1.9, y * 0.9, env_z - 2.8), 0.11, hq, "iron")

    for sign, label in ((1, "L"), (-1, "R")):
        nacelle(mb, sign * 3.8, y_of(0.78), 2.4, 1.5, 0.65, hq, label, root_x=sign * 2.6, color="steel")

    broadside(mb, [y_of(t) for t in (0.36, 0.5, 0.64, 0.76)], 2.8, lambda y: width_fn((y + length / 2) / length), 0.95, 0.13, hq, color="iron", carriage="navy")
    base_sockets(mb, half, deck_z, env_z, y_of(0.6), deck_z + 3.4)
    mb.socket("lift_core", (0, 0.2, env_z))
    mb.socket("helm", (0, y_of(0.44), deck_z + 2.7))


def gunship_monitor(mb, hq):
    """18. Modern Battleship: Low-freeboard armored siege monitor with oversized twin siege turret and 4 corner rotors."""
    length, half, deck_z = 19.5, 4.4, 2.5
    y_of = lambda t: -length / 2 + t * length
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 10, 6), bow_t=0.35, stern_t=0.72, stern_taper=0.35, sheer_bow=0.05, sheer_stern=0.05)
    paints = {0: "rust_dark", 1: "iron", 2: "steel", 3: "brass"} if hq else {0: "rust_dark", 1: "iron", 2: "steel"}
    shell(mb, stations, _q(hq, 4, 3), lambda r: paints[r], power=0.35, tumble=0.18)

    # Oversized central casemate & colossal twin 380mm siege cannon turret dominating the deck.
    mb.box((0, y_of(0.46), deck_z + 0.55), (5.4, 7.2, 1.1), "iron", top_scale=0.82)
    _turret(mb, 0, y_of(0.42), deck_z + 1.05, 2.1, 1.35, 2, 4.6, 0.26, hq, "steel", "brass", socket_prefix="muzzle_F")
    mb.socket("siege_muzzle", (0, y_of(0.42) - 6.6, deck_z + 1.95))

    # Armored spotting cupola & twin diesel exhaust stacks behind the turret.
    mb.box((0, y_of(0.74), deck_z + 1.4), (2.4, 2.6, 1.8), "steel", top_scale=0.8)
    for sign in (1, -1):
        mb.tube((sign * 1.4, y_of(0.78), deck_z + 0.8), (sign * 1.4, y_of(0.8), deck_z + 3.4), 0.32, 0.26, sides=_q(hq, 6, 4), color="iron")

    # Four corner armored ducted lift-rotor pods keeping the heavy ironclad aloft.
    for sign, label in ((1, "L"), (-1, "R")):
        for idx, ry in enumerate((y_of(0.24), y_of(0.78))):
            rx = sign * (half + 1.4)
            mb.box((sign * (half + 0.1), ry, 2.0), (2.2, 1.2, 0.55), "iron")
            _torus_ring(mb, rx, ry, 2.0, 1.35, 0.24, _q(hq, 10, 6), 4, "steel")
            mb.sphere((rx, ry, 2.0), (0.95, 0.95, 0.18), _q(hq, 8, 5), 3, "brass")
        nacelle(mb, sign * (half + 1.4), y_of(0.86), 2.0, 1.4, 0.62, hq, label, color="iron")

    broadside(mb, [y_of(t) for t in (0.34, 0.52, 0.68)], 2.1, lambda y: width_fn((y + length / 2) / length), 0.95, 0.15, hq, color="iron", carriage="brass")
    base_sockets(mb, half + 1.4, deck_z, deck_z + 2.4, y_of(0.78), deck_z + 3.4)
    mb.socket("lift_core", (0, y_of(0.46), 2.0))
    mb.socket("helm", (0, y_of(0.74), deck_z + 2.3))


# ==============================================================================
# CATEGORY 4: CREATIVE & FANTASTICAL SHIP DESIGNS
# ==============================================================================

def clockwork_sovereign(mb, hq):
    """19. Creative: Brass clockwork gear-ship with giant protruding cogwheels and a spinning armillary lift-orrery."""
    length, half, deck_z = 21.0, 3.3, 3.4
    y_of = lambda t: -length / 2 + t * length
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 12, 6), bow_t=0.38, stern_t=0.74, sheer_bow=0.22, sheer_stern=0.28)
    paints = {0: "wood_dark", 1: "brass", 2: "gold", 3: "wood_red", 4: "brass"} if hq else {0: "wood_dark", 1: "brass", 2: "gold"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.58)

    # Ornate brass clock-face stern cabin & wind-up key at the stern.
    mb.box((0, y_of(0.78), deck_z + 1.3), (4.2, 4.4, 2.2), "wood_red", top_scale=0.88)
    _torus_ring(mb, 0, y_of(0.78) + 2.25, deck_z + 1.3, 1.35, 0.18, _q(hq, 10, 6), 4, "gold", rot_x=math.pi / 2)
    mb.tube((0, y_of(0.78) + 2.2, deck_z + 1.3), (0, y_of(0.78) + 3.6, deck_z + 1.3), 0.18, 0.14, sides=4, color="brass")
    for sign in (1, -1):
        _torus_ring(mb, sign * 0.75, y_of(0.78) + 3.7, deck_z + 1.3, 0.55, 0.12, _q(hq, 8, 5), 4, "gold")

    # Protruding giant brass cogwheels slicing through the hull flanks.
    for sign, label in ((1, "L"), (-1, "R")):
        for gy, gr in ((y_of(0.35), 2.1), (y_of(0.62), 2.6)):
            gx = sign * (width_fn((gy + length / 2) / length) + 0.35)
            _torus_ring(mb, gx, gy, 2.5, gr, 0.28, _q(hq, 12, 8), 4, "brass", rot_y=math.pi / 2)
            mb.tube((gx - sign * 0.6, gy, 2.5), (gx + sign * 0.4, gy, 2.5), 0.35, 0.35, sides=6, color="gold")
            if hq:
                for t_idx in range(6):
                    ang = t_idx * math.pi / 3.0
                    ty = gy + math.cos(ang) * (gr + 0.22)
                    tz = 2.5 + math.sin(ang) * (gr + 0.22)
                    mb.box((gx, ty, tz), (0.35, 0.32, 0.32), "gold")
        nacelle(mb, sign * 4.2, y_of(0.8), 2.4, 1.4, 0.6, hq, label, root_x=sign * 2.5, color="brass")

    # Bow pendulum ram & forward brass cannon.
    mb.tube((0, y_of(0.06), 2.8), (0, y_of(0.0) - 2.6, 3.1), 0.32, 0.12, sides=6, color="brass")
    mb.socket("muzzle_F0", (0, y_of(0.0) - 2.65, 3.1))

    # Overhead multi-ring brass armillary sphere / clockwork orrery lift core.
    env_z = deck_z + 7.2
    mb.sphere((0, 0.0, env_z), 1.85, _q(hq, 10, 6), _q(hq, 6, 4), "lamp")
    _torus_ring(mb, 0, 0.0, env_z, 3.2, 0.24, _q(hq, 12, 8), 4, "brass", rot_x=0.45)
    _torus_ring(mb, 0, 0.0, env_z, 3.8, 0.24, _q(hq, 12, 8), 4, "gold", rot_y=-0.5)
    _torus_ring(mb, 0, 0.0, env_z, 4.3, 0.2, _q(hq, 12, 8), 4, "iron", rot_x=1.2)
    for sign in (1, -1):
        mb.tube((sign * 2.1, 0.0, deck_z), (sign * 3.1, 0.0, env_z - 1.5), 0.2, 0.16, sides=5, color="brass")

    broadside(mb, [y_of(t) for t in (0.28, 0.48, 0.68)], 2.6, lambda y: width_fn((y + length / 2) / length), 0.95, 0.14, hq, color="brass", carriage="wood_dark")
    base_sockets(mb, half + 0.6, deck_z, env_z, y_of(0.72), deck_z + 2.6)
    mb.socket("lift_core", (0, 0.0, env_z))
    mb.socket("helm", (0, y_of(0.7), deck_z + 2.4))


def sky_nautilus(mb, hq):
    """20. Creative: Giant logarithmic spiral ammonite shell ship with brass observation cabin and tentacle bow rams."""
    length, half, deck_z = 20.0, 3.1, 3.1
    y_of = lambda t: -length / 2 + t * length
    # Organic biomech lower mantle hull.
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 10, 6), bow_t=0.35, stern_t=0.75, keel_bow=0.5, keel_stern=0.4)
    paints = {0: "abyss", 1: "brass", 2: "parchment", 3: "amber", 4: "brass"} if hq else {0: "abyss", 1: "parchment", 2: "amber"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.68)

    # Coiled logarithmic Nautilus shell rising above the mid-and-aft deck (untwisted YZ-plane frames).
    coil_rings = []
    steps = _q(hq, 14, 9)
    ring_sides = _q(hq, 10, 6)
    for i in range(steps):
        u = i / (steps - 1)
        ang = u * math.pi * 1.85 - 0.35
        rad_orbit = 1.1 + (1.0 - u * 0.65) * 3.6
        cy = 1.4 + math.cos(ang) * rad_orbit
        cz = deck_z + 3.4 + math.sin(ang) * rad_orbit
        cr = 0.35 + (1.0 - u) * 2.15
        ring = []
        for j in range(ring_sides):
            phi = 2 * math.pi * j / ring_sides
            # Local frame: X is lateral width, radial vector (cos(ang), sin(ang)) in YZ is outward.
            rx = math.cos(phi) * cr * 0.78
            ry = cy + math.sin(phi) * cr * math.cos(ang)
            rz = cz + math.sin(phi) * cr * math.sin(ang)
            ring.append((rx, ry, rz))
        coil_rings.append(ring)
    nautilus_paint = lambda i, _j: "brass" if (hq and i in (2, 5, 8, 11)) or (not hq and i in (2, 5)) else "parchment"
    mb.loft(coil_rings, nautilus_paint, smooth=True)

    # Jules-Verne brass & glass forward observation dome + curling bronze tentacle rams.
    mb.sphere((0, y_of(0.22), deck_z + 0.65), (1.8, 2.4, 1.3), _q(hq, 10, 6), 5, "lamp")
    _torus_ring(mb, 0, y_of(0.22), deck_z + 0.5, 2.0, 0.18, _q(hq, 8, 6), 4, "brass")
    for sign in (1, -1):
        mb.path(
            [(sign * 1.1, y_of(0.14), 2.3), (sign * 1.5, y_of(0.0) - 1.4, 2.0), (sign * 0.7, y_of(0.0) - 3.4, 2.6)],
            [0.42, 0.25, 0.06],
            _q(hq, 6, 4),
            "brass",
        )
    mb.socket("muzzle_F0", (0, y_of(0.0) - 3.4, 2.6))

    # Lateral fin-wings and brass screw nacelles.
    for sign, label in ((1, "L"), (-1, "R")):
        wing(mb, sign, sign * 2.5, y_of(0.35), y_of(0.65), 2.3, 4.2, 0.8, hq, color="amber", spar="brass", thick=0.09)
        nacelle(mb, sign * 3.8, y_of(0.78), 2.3, 1.4, 0.58, hq, label, root_x=sign * 2.3, color="brass")

    broadside(mb, [y_of(t) for t in (0.32, 0.5, 0.68)], 2.3, lambda y: width_fn((y + length / 2) / length), 0.88, 0.13, hq, color="brass", carriage="wood_dark")
    base_sockets(mb, half, deck_z, deck_z + 4.5, y_of(0.72), deck_z + 2.5)
    mb.socket("lift_core", (0, 1.2, deck_z + 3.2))
    mb.socket("helm", (0, y_of(0.22), deck_z + 1.2))


def bone_revenant(mb, hq):
    """21. Creative: Necromantic ghost ship built inside a colossal sky-whale ribcage and horned skull prow."""
    length, half, deck_z = 22.0, 3.2, 3.2
    y_of = lambda t: -length / 2 + t * length
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 12, 6), bow_t=0.36, stern_t=0.74, sheer_bow=0.25, sheer_stern=0.35)
    paints = {0: "abyss", 1: "wood_dark", 2: "parchment", 3: "abyss", 4: "parchment"} if hq else {0: "abyss", 1: "wood_dark", 2: "parchment"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.55)

    # Colossal horned leviathan skull prow with glowing green eye sockets.
    bow_y = y_of(0.04)
    mb.box((0, bow_y - 1.1, 2.9), (2.5, 2.8, 1.6), "parchment", top_scale=0.72)
    for sign in (1, -1):
        mb.sphere((sign * 0.85, bow_y - 1.8, 3.1), 0.35, 6, 4, "toxic")
        mb.path(
            [(sign * 1.1, bow_y - 0.8, 3.2), (sign * 2.4, bow_y - 2.2, 3.8), (sign * 1.6, bow_y - 4.2, 4.5)],
            [0.38, 0.22, 0.05],
            _q(hq, 6, 4),
            "parchment",
        )
    mb.socket("ram_tip", (0, bow_y - 4.2, 3.5))
    mb.socket("muzzle_F0", (0, bow_y - 2.6, 2.9))

    # Giant curving bone ribs arching over the deck to form an external skeleton cage.
    rib_ys = [y_of(t) for t in _q(hq, (0.24, 0.38, 0.52, 0.66, 0.8), (0.28, 0.52, 0.76))]
    for ry in rib_ys:
        w = width_fn((ry + length / 2) / length)
        for sign in (1, -1):
            mb.path(
                [(sign * (w + 0.15), ry, 2.2), (sign * (w + 1.1), ry, deck_z + 1.8), (sign * 0.8, ry, deck_z + 3.6)],
                [0.24, 0.2, 0.1],
                _q(hq, 6, 4),
                "parchment",
            )
    # Dorsal spine vertebrae connecting the ribs.
    mb.tube((0, rib_ys[0], deck_z + 3.65), (0, rib_ys[-1], deck_z + 3.65), 0.24, 0.2, sides=5, color="parchment")

    # Mausoleum stern crypt & hanging green soul-fire braziers.
    mb.box((0, y_of(0.82), deck_z + 1.4), (3.4, 3.6, 2.4), "abyss", top_scale=0.82)
    mb.sphere((0, y_of(0.82) + 1.9, deck_z + 1.6), 0.55, 6, 4, "toxic")

    # Tattered spectral sails & bone-ribbed gasbag.
    env_z = deck_z + 7.4
    rings = _q(hq, 8, 5)
    gasbag(mb, 0, 0.2, env_z, 16.5, 3.0, _q(hq, 10, 6), rings, striped("abyss", "toxic_dark", "parchment", rings), flat=0.88)
    for y in (-3.2, 3.0):
        mast(mb, 0, y, deck_z, env_z - 1.8, 0.18, hq, yards=((deck_z + 2.2, 3.2),))
        sail(mb, y - 0.2, deck_z + 2.1, deck_z + 0.9, 3.0, 0.55, hq, color="toxic", tatter=True)
        for sign in (1, -1):
            rope(mb, (sign * 2.2, y, deck_z + 1.8), (sign * 1.8, y * 0.9, env_z - 2.1), 0.09, hq, "parchment")

    for sign, label in ((1, "L"), (-1, "R")):
        nacelle(mb, sign * 3.8, y_of(0.78), 2.3, 1.35, 0.56, hq, label, root_x=sign * 2.4, color="parchment")

    broadside(mb, [y_of(t) for t in (0.32, 0.48, 0.64)], 2.4, lambda y: width_fn((y + length / 2) / length), 0.9, 0.14, hq, color="iron", carriage="parchment")
    base_sockets(mb, half + 0.8, deck_z, env_z, y_of(0.82), deck_z + 2.8)
    mb.socket("lift_core", (0, 0.0, deck_z + 2.0))
    mb.socket("helm", (0, y_of(0.72), deck_z + 0.2))


def crystal_sanctum(mb, hq):
    """22. Creative: Floating gothic cathedral with flying buttresses, twin bell-spires, rose window and prism halo."""
    length, half, deck_z = 23.0, 3.8, 3.6
    y_of = lambda t: -length / 2 + t * length
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 10, 6), bow_t=0.35, stern_t=0.78, keel_bow=0.45, keel_stern=0.4)
    paints = {0: "rock_dark", 1: "cloth_white", 2: "gold", 3: "enamel", 4: "gold"} if hq else {0: "rock_dark", 1: "cloth_white", 2: "gold"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.48)

    # Grand vaulted cathedral nave rising along the ship's centerline.
    nave_y = y_of(0.54)
    mb.box((0, nave_y, deck_z + 1.8), (3.8, 10.5, 3.6), "cloth_white", top_scale=0.86)
    # Pitched golden cathedral roof.
    mb.loft(
        [
            [(0.0, nave_y - 5.2, deck_z + 5.5), (-1.75, nave_y - 5.2, deck_z + 3.6), (1.75, nave_y - 5.2, deck_z + 3.6)],
            [(0.0, nave_y + 5.2, deck_z + 5.5), (-1.75, nave_y + 5.2, deck_z + 3.6), (1.75, nave_y + 5.2, deck_z + 3.6)],
        ],
        "gold",
    )
    # Glowing stained-glass rose windows on bow & stern facades of the nave.
    _torus_ring(mb, 0, nave_y - 5.28, deck_z + 2.2, 1.1, 0.16, _q(hq, 10, 6), 4, "gold", rot_x=math.pi / 2)
    mb.sphere((0, nave_y - 5.25, deck_z + 2.2), (0.95, 0.12, 0.95), _q(hq, 8, 5), 3, "lamp")
    mb.socket("muzzle_F0", (0, y_of(0.0) - 1.5, deck_z + 0.8))

    # Twin forward gothic bell-spires & flying buttresses along the flanks.
    for sign in (1, -1):
        sx = sign * 1.55
        sy = y_of(0.24)
        mb.box((sx, sy, deck_z + 2.4), (1.35, 1.35, 4.8), "cloth_white", top_scale=0.84)
        mb.tube((sx, sy, deck_z + 4.8), (sx, sy, deck_z + 8.2), 0.65, 0.05, sides=4, color="gold")
        for by in _q(hq, (y_of(0.38), y_of(0.54), y_of(0.7)), (y_of(0.42), y_of(0.66))):
            mb.path([(sign * 3.3, by, deck_z), (sign * 2.7, by, deck_z + 1.9), (sign * 1.85, by, deck_z + 2.9)], [0.22, 0.18, 0.15], 4, "cloth_white")

    # Floating radiant halo ring & central prism crystal above the cathedral crossing, anchored by golden arches.
    env_z = deck_z + 8.0
    _torus_ring(mb, 0, nave_y + 0.8, env_z, 3.8, 0.28, _q(hq, 14, 8), 4, "gold")
    _crystal_spire(mb, (0, nave_y + 0.8, deck_z + 5.1), (0, nave_y + 0.8, env_z + 1.8), 0.95, 0.72, _q(hq, 6, 4), "liftstone")
    for sign in (1, -1):
        mb.tube((sign * 1.5, nave_y + 0.8, deck_z + 3.6), (sign * 3.6, nave_y + 0.8, env_z), 0.16, 0.12, sides=4, color="gold")

    for sign, label in ((1, "L"), (-1, "R")):
        nacelle(mb, sign * 4.2, y_of(0.82), 2.5, 1.5, 0.62, hq, label, root_x=sign * 2.6, color="gold")

    broadside(mb, [y_of(t) for t in (0.32, 0.5, 0.68)], 2.6, lambda y: width_fn((y + length / 2) / length), 0.95, 0.13, hq, color="gold", carriage="cloth_white")
    base_sockets(mb, half, deck_z, env_z, nave_y + 2.5, deck_z + 5.2)
    mb.socket("lift_core", (0, nave_y + 0.8, env_z))
    mb.socket("helm", (0, y_of(0.18), deck_z + 0.4))


def dragon_junker(mb, hq):
    """23. Creative: Eastern imperial pagoda junk with upturned eaves, battened fan sails and dragon-head prow."""
    length, half, deck_z = 22.0, 3.4, 3.4
    y_of = lambda t: -length / 2 + t * length
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 12, 6), bow_t=0.35, stern_t=0.72, sheer_bow=0.3, sheer_stern=0.4)
    paints = {0: "wood_dark", 1: "wood_red", 2: "gold", 3: "faction_a", 4: "gold"} if hq else {0: "wood_dark", 1: "wood_red", 2: "gold"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.58)

    # Sculpted golden dragon-head figurehead with whisker horns & fire-cannon mouth.
    bow_y = y_of(0.0)
    mb.path([(0, y_of(0.08), 2.8), (0, bow_y - 1.4, 3.8), (0, bow_y - 2.6, 4.2)], [0.65, 0.52, 0.35], _q(hq, 6, 4), "gold")
    mb.box((0, bow_y - 2.9, 4.2), (0.95, 1.2, 0.65), "gold", top_scale=0.8)
    mb.sphere((0, bow_y - 3.3, 4.15), 0.32, 6, 4, "ember")
    mb.socket("muzzle_F0", (0, bow_y - 3.5, 4.15))

    # Multi-tiered imperial pagoda pavilion on the aft deck with upturned golden eaves.
    py = y_of(0.76)
    for tier, (tw, tl, tz, th) in enumerate(((4.2, 4.8, deck_z + 0.9, 1.6), (3.2, 3.6, deck_z + 2.4, 1.3), (2.2, 2.4, deck_z + 3.6, 1.0))):
        if not hq and tier == 2:
            continue
        mb.box((0, py, tz), (tw, tl, th), "wood_red", top_scale=0.88)
        mb.box((0, py, tz + th * 0.52), (tw + 0.9, tl + 0.9, 0.22), "gold", top_scale=1.12)

    # Three battened Eastern junk sails with bamboo ribs.
    for sy, sh, sw in ((y_of(0.24), 7.8, 3.0), (y_of(0.46), 9.0, 3.6), (y_of(0.66), 7.2, 2.8)):
        mast(mb, 0, sy, deck_z, deck_z + sh, 0.18, hq, yards=((deck_z + sh * 0.88, sw), (deck_z + sh * 0.55, sw), (deck_z + sh * 0.25, sw)))
        sail(mb, sy - 0.2, deck_z + sh * 0.88, deck_z + sh * 0.22, sw, 0.65, hq, color="faction_a")

    # Side paper-lantern lift blimps along port & starboard.
    for sign, label in ((1, "L"), (-1, "R")):
        rings = _q(hq, 8, 5)
        gasbag(mb, sign * 4.4, 0.0, deck_z + 2.2, 13.5, 1.55, _q(hq, 8, 6), rings, striped("gold", "faction_a", "ember", rings), flat=0.9)
        mb.tube((sign * 2.2, -2.5, deck_z + 0.4), (sign * 4.2, -2.5, deck_z + 1.6), 0.16, 0.14, sides=4, color="wood_red")
        mb.tube((sign * 2.2, 2.5, deck_z + 0.4), (sign * 4.2, 2.5, deck_z + 1.6), 0.16, 0.14, sides=4, color="wood_red")
        nacelle(mb, sign * 4.0, y_of(0.8), 2.3, 1.4, 0.58, hq, label, root_x=sign * 2.4, color="gold")

    broadside(mb, [y_of(t) for t in (0.3, 0.48, 0.64)], 2.5, lambda y: width_fn((y + length / 2) / length), 0.9, 0.14, hq, color="gold", carriage="wood_red")
    base_sockets(mb, 4.4, deck_z, deck_z + 4.5, py, deck_z + 4.6)
    mb.socket("lift_core", (0, 0.0, deck_z + 2.2))
    mb.socket("helm", (0, y_of(0.62), deck_z + 0.2))


def beetle_scarab(mb, hq):
    """24. Creative: Domed golden scarab carapace hull with open wing-casings, gossamer wings and pincer mandibles."""
    length, half, deck_z = 19.0, 3.8, 3.0
    y_of = lambda t: -length / 2 + t * length
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 10, 6), bow_t=0.42, stern_t=0.68, keel_bow=0.5, keel_stern=0.45)
    paints = {0: "abyss", 1: "gold_dark", 2: "cloth_green", 3: "gold", 4: "liftstone"} if hq else {0: "abyss", 1: "cloth_green", 2: "gold"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.72)

    # Armored rhinoceros-scarab head shield, central horn & curved pincer mandibles.
    bow_y = y_of(0.06)
    mb.sphere((0, bow_y, 2.7), (2.4, 2.2, 1.2), _q(hq, 8, 5), 4, "gold_dark")
    mb.path([(0, bow_y - 0.8, 2.8), (0, bow_y - 2.8, 3.6), (0, bow_y - 3.6, 4.8)], [0.45, 0.25, 0.06], _q(hq, 6, 4), "gold")
    for sign in (1, -1):
        mb.path(
            [(sign * 1.4, bow_y - 0.5, 2.3), (sign * 2.2, bow_y - 2.2, 2.3), (sign * 0.9, bow_y - 3.8, 2.4)],
            [0.38, 0.26, 0.06],
            _q(hq, 6, 4),
            "gold",
        )
    mb.socket("ram_tip", (0, bow_y - 3.8, 2.4))
    mb.socket("muzzle_F0", (0, bow_y - 3.6, 3.6))

    # Exposed glowing amber/liftstone abdomen core under parted elytra (wing-casings).
    mb.sphere((0, y_of(0.56), deck_z + 1.1), (2.5, 5.2, 1.8), _q(hq, 10, 6), 5, "liftstone")
    for sign, label in ((1, "L"), (-1, "R")):
        # Raised hard-shell elytra wing-cases & translucent insect flight wings.
        wing(mb, sign, sign * 1.2, y_of(0.32), y_of(0.78), deck_z + 1.4, 4.2, 2.2, hq, color="cloth_green", spar="gold", thick=0.16, ribs=1)
        wing(mb, sign, sign * 2.2, y_of(0.38), y_of(0.72), deck_z + 0.8, 6.4, 0.9, hq, color="liftstone", spar="gold", thick=0.06, ribs=2)
        nacelle(mb, sign * 3.8, y_of(0.8), 2.2, 1.35, 0.56, hq, label, root_x=sign * 2.4, color="gold")

    broadside(mb, [y_of(t) for t in (0.34, 0.52, 0.7)], 2.3, lambda y: width_fn((y + length / 2) / length), 0.85, 0.13, hq, color="gold", carriage="gold_dark")
    base_sockets(mb, half, deck_z, deck_z + 2.4, y_of(0.76), deck_z + 2.6)
    mb.socket("lift_core", (0, y_of(0.56), deck_z + 1.1))
    mb.socket("helm", (0, y_of(0.24), deck_z + 0.5))


# ==============================================================================
# CATEGORY 5: SPECIALIZED OUTLAW, INDUSTRIAL & DIESELPUNK SHIPS
# ==============================================================================

def gyro_copter(mb, hq):
    """25. Specialized: Quad-rotor dieselpunk heli-gunship with 4 outrigger shrouded rotors, chin turret and twin tail booms."""
    length, half, deck_z = 20.0, 2.8, 3.0
    y_of = lambda t: -length / 2 + t * length
    stations, width_fn = _hull_stations(length * 0.75, half, deck_z, _q(hq, 8, 5), bow_t=0.35, stern_t=0.72)
    paints = {0: "iron", 1: "rust", 2: "faction_a", 3: "steel", 4: "brass"} if hq else {0: "iron", 1: "faction_a", 2: "steel"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.52)

    # Greenhouse glass gunship cockpit & chin-mounted rotary gatling turret.
    bow_y = -length * 0.375
    mb.sphere((0, bow_y + 1.4, 2.4), (1.7, 2.2, 1.1), _q(hq, 8, 5), 4, "glass")
    _turret(mb, 0, bow_y + 0.8, 1.25, 0.62, 0.45, 2, 1.8, 0.1, hq, "steel", "brass", socket_prefix="muzzle_F")

    # Twin high-mounted tail booms extending aft to an H-tail stabilizer.
    for sign in (1, -1):
        mb.tube((sign * 1.6, 1.5, 2.7), (sign * 1.6, 10.2, 3.2), 0.38, 0.22, sides=_q(hq, 6, 4), color="steel")
        mb.plate([(sign * 1.6, 8.8, 2.2), (sign * 1.6, 10.6, 2.4), (sign * 1.6, 10.4, 4.6), (sign * 1.6, 9.0, 4.4)], 0.1, "faction_a")
    mb.box((0, 9.6, 3.3), (3.4, 1.1, 0.16), "steel")

    # Quad outrigger rotor arms with shrouded multi-blade helicopter rotors.
    for sign, label in ((1, "L"), (-1, "R")):
        for idx, (ry, rx_mult, rz) in enumerate(((-2.8, 5.4, 3.6), (3.4, 5.8, 4.1))):
            rx = sign * rx_mult
            mb.tube((sign * 2.1, ry * 0.7, 2.6), (rx, ry, rz), 0.32, 0.24, sides=5, color="iron")
            _torus_ring(mb, rx, ry, rz, 2.2, 0.22, _q(hq, 12, 8), 4, "steel")
            mb.tube((rx, ry, rz - 0.35), (rx, ry, rz + 0.35), 0.35, 0.3, sides=6, color="brass")
            for b in range(2):
                ang = b * math.pi / 2.0
                bx, by = math.cos(ang) * 1.95, math.sin(ang) * 1.95
                mb.box((rx, ry, rz + 0.05), (3.8 if b == 0 else 0.32, 0.32 if b == 0 else 3.8, 0.06), "iron_light")
        nacelle(mb, sign * 2.8, 5.2, 2.3, 1.4, 0.58, hq, label, root_x=sign * 1.6, color="brass")

    broadside(mb, (-2.2, 0.4, 2.8), 2.2, lambda _y: half, 0.85, 0.12, hq, color="iron", carriage="rust")
    base_sockets(mb, 5.6, deck_z, 4.1, 2.2, deck_z + 1.2)
    mb.socket("lift_core", (0, 0.0, 2.8))
    mb.socket("helm", (0, bow_y + 1.8, 2.5))


def whaler_harpooner(mb, hq):
    """26. Specialized: Heavy sky-whaler factory ship with stern slipway, twin gantry cranes and bow harpoon battery."""
    length, half, deck_z = 23.0, 3.8, 3.4
    y_of = lambda t: -length / 2 + t * length
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 12, 6), bow_t=0.36, stern_t=0.78, stern_taper=0.45)
    paints = {0: "rust_dark", 1: "wood_dark", 2: "iron", 3: "rust", 4: "wood_mid"} if hq else {0: "rust_dark", 1: "iron", 2: "rust"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.48)

    # Elevated bow harpoon pulpit with oversized twin-rail barbed sky-harpoon launcher.
    bow_y = y_of(0.05)
    mb.box((0, bow_y, deck_z + 0.55), (2.4, 2.6, 1.1), "iron", top_scale=0.85)
    mb.tube((0, bow_y + 0.4, deck_z + 1.3), (0, bow_y - 3.4, deck_z + 1.45), 0.24, 0.14, sides=6, color="brass")
    for sign in (1, -1):
        mb.plate([(sign * 0.12, bow_y - 3.4, deck_z + 1.45), (sign * 0.65, bow_y - 2.6, deck_z + 1.45), (sign * 0.12, bow_y - 2.8, deck_z + 1.45)], 0.08, "steel")
    mb.socket("harpoon_muzzle", (0, bow_y - 3.45, deck_z + 1.45))
    mb.socket("muzzle_F0", (0, bow_y - 3.45, deck_z + 1.45))

    # Midships rendering oil cauldrons, heavy winch drum & twin A-frame gantry cranes.
    mb.tube((-1.4, y_of(0.45), deck_z + 0.45), (1.4, y_of(0.45), deck_z + 0.45), 0.55, 0.55, sides=_q(hq, 8, 5), color="iron")
    mb.socket("winch", (0, y_of(0.45), deck_z + 0.5))
    for gy in (y_of(0.35), y_of(0.68)):
        for sign in (1, -1):
            mb.tube((sign * 2.8, gy, deck_z), (sign * 1.6, gy, deck_z + 3.8), 0.2, 0.16, sides=4, color="rust")
        mb.box((0, gy, deck_z + 3.8), (3.8, 0.38, 0.38), "iron")

    # Forward wheelhouse bridge (leaving the stern open as a Monster-hauling slipway ramp).
    mb.box((0, y_of(0.24), deck_z + 1.3), (3.4, 2.8, 2.2), "wood_dark", top_scale=0.86)
    mb.tube((1.1, y_of(0.52), deck_z), (1.1, y_of(0.54), deck_z + 3.6), 0.38, 0.32, sides=6, color="iron")

    # Twin rugged leather-strapped gasbags overhead.
    env_z = deck_z + 7.2
    for sign, label in ((1, "L"), (-1, "R")):
        rings = _q(hq, 8, 5)
        gasbag(mb, sign * 2.2, 0.2, env_z, 17.5, 2.1, _q(hq, 10, 6), rings, striped("leather_dark", "canvas_dark", "rust", rings), flat=0.9)
        rope(mb, (sign * 2.6, -3.5, deck_z), (sign * 2.2, -3.2, env_z - 1.8), 0.1, hq, "rope")
        rope(mb, (sign * 2.6, 3.5, deck_z), (sign * 2.2, 3.2, env_z - 1.8), 0.1, hq, "rope")
        nacelle(mb, sign * 4.2, y_of(0.78), 2.3, 1.5, 0.62, hq, label, root_x=sign * 2.8, color="iron")

    broadside(mb, [y_of(t) for t in (0.32, 0.48, 0.64)], 2.5, lambda y: width_fn((y + length / 2) / length), 0.95, 0.15, hq, color="iron", carriage="wood_dark")
    base_sockets(mb, half, deck_z, env_z, y_of(0.54), deck_z + 3.6)
    mb.socket("lift_core", (0, 0.2, env_z))
    mb.socket("helm", (0, y_of(0.24), deck_z + 2.4))


def luxury_yacht(mb, hq):
    """27. Specialized: Art-deco white-and-gold sky cruise liner with tiered promenade decks and glass conservatory."""
    length, half, deck_z = 25.0, 3.4, 3.4
    y_of = lambda t: -length / 2 + t * length
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 12, 6), bow_t=0.4, stern_t=0.76, sheer_bow=0.22, sheer_stern=0.15)
    paints = {0: "gold_dark", 1: "enamel", 2: "gold", 3: "cloth_white", 4: "gold"} if hq else {0: "gold_dark", 1: "enamel", 2: "cloth_white"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.58)

    # Tiered white Art-Deco promenade superstructure with golden trim & glowing cabin windows.
    mb.box((0, y_of(0.54), deck_z + 0.85), (4.6, 13.5, 1.5), "cloth_white", top_scale=0.92)
    mb.box((0, y_of(0.56), deck_z + 2.0), (3.4, 9.2, 1.1), "enamel", top_scale=0.88)
    mb.sphere((0, y_of(0.52), deck_z + 2.7), (1.4, 3.2, 0.95), _q(hq, 10, 6), 4, "glass")
    if hq:
        for sign in (1, -1):
            mb.box((sign * 2.25, y_of(0.54), deck_z + 0.95), (0.08, 10.5, 0.35), "lamp")
    # Aft turquoise sky-pool / sun deck & golden bow chaser turret.
    mb.box((0, y_of(0.86), deck_z + 0.18), (2.4, 2.6, 0.12), "liftstone")
    _turret(mb, 0, y_of(0.16), deck_z, 0.72, 0.48, 2, 1.6, 0.1, hq, "gold", "enamel", socket_prefix="muzzle_F")

    # Streamlined white-and-gold luxury dirigible overhead with swept art-deco fins.
    env_z = deck_z + 7.8
    rings = _q(hq, 10, 6)
    gasbag(mb, 0, 0.0, env_z, 22.0, 3.6, _q(hq, 12, 8), rings, striped("enamel", "gold", "faction_a", rings), flat=0.92)
    fins(mb, 0, 8.2, env_z, 3.8, 2.8, 0.1, "gold")
    for y in (-4.8, 4.5):
        for sign in (1, -1):
            rope(mb, (sign * 2.2, y, deck_z + 1.5), (sign * 2.0, y * 0.9, env_z - 3.0), 0.09, hq, "gold")

    for sign, label in ((1, "L"), (-1, "R")):
        nacelle(mb, sign * 4.0, y_of(0.78), 2.5, 1.5, 0.6, hq, label, root_x=sign * 2.4, color="gold")

    broadside(mb, [y_of(t) for t in (0.3, 0.48, 0.66, 0.8)], 2.5, lambda y: width_fn((y + length / 2) / length), 0.85, 0.11, hq, color="gold", carriage="enamel")
    base_sockets(mb, half, deck_z, env_z, y_of(0.62), deck_z + 3.2)
    mb.socket("lift_core", (0, 0.0, env_z))
    mb.socket("helm", (0, y_of(0.36), deck_z + 2.2))


def shadow_stalker(mb, hq):
    """28. Specialized: Asymmetric assassin blade-ship with port outrigger wing, forward-swept scythes and stealth shroud."""
    length, half, deck_z = 21.0, 2.3, 2.7
    y_of = lambda t: -length / 2 + t * length
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 10, 6), bow_t=0.45, stern_t=0.78)
    paints = {0: "abyss", 1: "cloth_black", 2: "velvet", 3: "faction_a", 4: "abyss"} if hq else {0: "abyss", 1: "cloth_black", 2: "velvet"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.42)

    # Razor-vertical assassin blade prow & twin silenced sniper railguns.
    bow_y = y_of(0.0)
    mb.plate([(0, bow_y + 1.5, 0.5), (0, bow_y - 3.8, 2.1), (0, bow_y - 2.6, 3.6), (0, bow_y + 1.8, deck_z + 0.4)], 0.14, "steel")
    mb.tube((0, bow_y + 0.5, 2.5), (0, bow_y - 3.6, 2.5), 0.14, 0.09, sides=4, color="abyss")
    mb.socket("ram_tip", (0, bow_y - 3.8, 2.1))
    mb.socket("muzzle_F0", (0, bow_y - 3.65, 2.5))

    # Asymmetric layout: Starboard (-X) offset stealth cockpit pod, Port (+X) outrigger shadow-pod & scythe blade.
    mb.box((-1.1, y_of(0.58), deck_z + 0.7), (1.8, 4.8, 1.2), "abyss", top_scale=0.72)
    mb.box((-1.1, y_of(0.46), deck_z + 0.8), (1.3, 1.8, 0.55), "ember", top_scale=0.68)
    # Port (+X) outrigger shadow-foil & twin crossbeams.
    mb.box((2.8, y_of(0.52), 2.2), (3.8, 0.55, 0.35), "abyss")
    mb.box((2.8, y_of(0.74), 2.2), (3.8, 0.55, 0.35), "abyss")
    gasbag(mb, 4.8, y_of(0.62), 2.2, 12.5, 1.15, _q(hq, 8, 5), _q(hq, 8, 5), "abyss", flat=0.8)

    # Forward-swept bat/scythe wings on both sides & shrouded thrusters.
    for sign, label in ((1, "L"), (-1, "R")):
        root = sign * (4.8 if sign > 0 else 1.8)
        wing(mb, sign, root, y_of(0.68), y_of(0.32), 2.3, 4.2, 1.4, hq, color="velvet", spar="abyss", thick=0.09, ribs=1)
        nacelle(mb, sign * 3.2, y_of(0.84), 2.1, 1.5, 0.56, hq, label, root_x=sign * 1.6, color="abyss")
        mb.socket(f"afterburner_{label}", (sign * 3.2, y_of(0.84) + 1.55, 2.1))

    broadside(mb, [y_of(t) for t in (0.34, 0.52, 0.7)], 2.1, lambda y: width_fn((y + length / 2) / length), 0.85, 0.11, hq, color="abyss", carriage="velvet")
    base_sockets(mb, 4.8, deck_z, deck_z + 1.8, y_of(0.76), deck_z + 1.5)
    mb.socket("lift_core", (4.8, y_of(0.62), 2.2))
    mb.socket("helm", (-1.1, y_of(0.52), deck_z + 0.8))


def powder_keg(mb, hq):
    """29. Specialized: Riveted demolition bombardier with strapped powder barrels, twin giant deck mortars and hot-air blimp."""
    length, half, deck_z = 18.0, 3.9, 3.2
    y_of = lambda t: -length / 2 + t * length
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 10, 6), bow_t=0.35, stern_t=0.72, stern_taper=0.35)
    paints = {0: "rust_dark", 1: "iron", 2: "rust", 3: "faction_a", 4: "brass"} if hq else {0: "rust_dark", 1: "iron", 2: "rust"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.55)

    # Twin colossal stubby brass siege mortars angled skyward on the fore & mid deck.
    for idx, my in enumerate((y_of(0.28), y_of(0.55))):
        mb.box((0, my, deck_z + 0.35), (2.4, 2.2, 0.7), "iron", top_scale=0.88)
        mb.tube((0, my + 0.3, deck_z + 0.6), (0, my - 1.3, deck_z + 2.3), 0.78, 0.68, sides=_q(hq, 10, 6), color="brass")
        mb.tube((0, my - 1.2, deck_z + 2.2), (0, my - 1.45, deck_z + 2.45), 0.6, 0.55, sides=_q(hq, 8, 5), color="abyss")
        if idx == 0:
            mb.socket("siege_muzzle", (0, my - 1.45, deck_z + 2.45))
            mb.socket("muzzle_F0", (0, my - 1.45, deck_z + 2.45))

    # Racks of oversized red-striped black-powder kegs strapped along the flanks & stern.
    for sign in (1, -1):
        for ky in (-2.6, 0.0, 2.6):
            kx = sign * (width_fn((ky + length / 2) / length) + 0.35)
            mb.tube((kx, ky - 0.8, 2.4), (kx, ky + 0.8, 2.4), 0.62, 0.62, sides=_q(hq, 8, 5), color="wood_red")
    mb.box((0, y_of(0.8), deck_z + 1.1), (3.6, 3.2, 1.9), "iron", top_scale=0.84)

    # Bulbous patched hot-air demolition balloon with roaring open burner basket underneath.
    env_z = deck_z + 7.6
    rings = _q(hq, 10, 6)
    gasbag(mb, 0, 0.0, env_z, 15.5, 4.1, _q(hq, 12, 8), rings, striped("rust", "faction_a", "ember", rings), flat=0.95)
    mb.sphere((0, 0.0, env_z - 3.6), 0.75, 6, 4, "ember")
    for y in (-3.2, 3.2):
        for sign in (1, -1):
            rope(mb, (sign * 2.8, y, deck_z), (sign * 2.2, y * 0.9, env_z - 3.2), 0.11, hq, "iron")

    for sign, label in ((1, "L"), (-1, "R")):
        nacelle(mb, sign * 4.2, y_of(0.76), 2.2, 1.4, 0.62, hq, label, root_x=sign * 2.8, color="brass")

    broadside(mb, [y_of(t) for t in (0.3, 0.5, 0.7)], 2.3, lambda y: width_fn((y + length / 2) / length), 1.0, 0.16, hq, color="brass", carriage="iron")
    base_sockets(mb, half + 0.6, deck_z, env_z, y_of(0.8), deck_z + 2.6)
    mb.socket("lift_core", (0, 0.0, env_z - 3.6))
    mb.socket("helm", (0, y_of(0.75), deck_z + 2.1))


def cloud_train(mb, hq):
    """30. Specialized: Flying steam locomotive airship with cowcatcher prow, cylindrical boiler, smokestack and caboose."""
    length, half, deck_z = 25.0, 2.8, 2.6
    y_of = lambda t: -length / 2 + t * length
    # Heavy steel rail-frame flatbed chassis with side running boards.
    stations, width_fn = _hull_stations(length, half, deck_z, _q(hq, 10, 6), bow_t=0.25, stern_t=0.82, stern_taper=0.15, sheer_bow=0.05, sheer_stern=0.05)
    paints = {0: "rust_dark", 1: "iron", 2: "wood_red", 3: "brass", 4: "steel"} if hq else {0: "rust_dark", 1: "iron", 2: "brass"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.35)

    # Iconic wedge iron cowcatcher plough on the bow & glowing brass headlamp.
    bow_y = y_of(0.0)
    mb.loft(
        [
            [(0.0, bow_y - 3.8, 0.8), (-2.4, bow_y - 0.8, 0.8), (2.4, bow_y - 0.8, 0.8)],
            [(0.0, bow_y - 3.2, 2.5), (-2.2, bow_y - 0.8, 2.5), (2.2, bow_y - 0.8, 2.5)],
        ],
        "iron",
    )
    mb.tube((0, bow_y + 0.6, deck_z + 1.4), (0, bow_y - 0.8, deck_z + 1.4), 0.55, 0.62, sides=6, color="brass")
    mb.sphere((0, bow_y - 0.82, deck_z + 1.4), (0.45, 0.15, 0.45), 6, 4, "lamp")
    mb.socket("ram_tip", (0, bow_y - 3.8, 1.2))
    mb.socket("muzzle_F0", (0, bow_y - 0.9, deck_z + 1.4))

    # Cylindrical steam-locomotive boiler barrel with brass bands & balloon smokestack.
    boiler_z = deck_z + 1.35
    mb.tube((0, y_of(0.08), boiler_z), (0, y_of(0.62), boiler_z), 1.45, 1.45, sides=_q(hq, 12, 8), color="iron")
    for by in _q(hq, (y_of(0.14), y_of(0.28), y_of(0.42), y_of(0.56)), (y_of(0.18), y_of(0.48))):
        _torus_ring(mb, 0, by, boiler_z, 1.48, 0.1, _q(hq, 10, 6), 4, "brass", rot_x=math.pi / 2)
    # Diamond spark-arrestor smokestack & steam domes.
    mb.tube((0, y_of(0.16), boiler_z + 1.2), (0, y_of(0.16), boiler_z + 3.4), 0.45, 0.72, sides=_q(hq, 8, 5), color="iron")
    mb.sphere((0, y_of(0.36), boiler_z + 1.35), 0.65, 6, 4, "brass")

    # Engineer's locomotive cab & red caboose stern cabin.
    mb.box((0, y_of(0.72), deck_z + 1.6), (3.6, 3.8, 2.8), "wood_red", top_scale=0.92)
    mb.box((0, y_of(0.72), deck_z + 3.1), (3.9, 4.1, 0.25), "brass")
    mb.box((0, y_of(0.9), deck_z + 1.2), (3.2, 2.8, 2.0), "faction_a", top_scale=0.9)

    # Locomotive drive wheels & coupling rods along the hull sides.
    for sign, label in ((1, "L"), (-1, "R")):
        for wy in (y_of(0.26), y_of(0.44), y_of(0.62)):
            _torus_ring(mb, sign * (half + 0.25), wy, 1.8, 0.85, 0.16, _q(hq, 8, 6), 4, "brass", rot_y=math.pi / 2)
        mb.box((sign * (half + 0.42), y_of(0.44), 1.8), (0.12, 9.4, 0.22), "steel")
        nacelle(mb, sign * 3.8, y_of(0.82), 2.3, 1.5, 0.64, hq, label, root_x=sign * 2.5, color="brass")

    # Overhead iron-banded Pullman dirigible.
    env_z = deck_z + 8.0
    rings = _q(hq, 10, 6)
    gasbag(mb, 0, 0.2, env_z, 21.0, 3.2, _q(hq, 12, 8), rings, striped("iron", "brass", "faction_a", rings), flat=0.92)
    for y in (-4.5, 4.5):
        for sign in (1, -1):
            rope(mb, (sign * 2.2, y, deck_z + 1.2), (sign * 1.9, y * 0.9, env_z - 2.6), 0.1, hq, "iron")

    broadside(mb, [y_of(t) for t in (0.28, 0.46, 0.64, 0.8)], 2.3, lambda y: width_fn((y + length / 2) / length), 0.95, 0.14, hq, color="brass", carriage="iron")
    base_sockets(mb, half + 0.4, deck_z, env_z, y_of(0.16), boiler_z + 3.4)
    mb.socket("lift_core", (0, y_of(0.36), boiler_z))
    mb.socket("helm", (0, y_of(0.72), deck_z + 2.0))


# ==============================================================================
# REGISTRY MAPS FOR CATALOG & FX ICONS
# ==============================================================================

FLEET_SHIPS = {
    # Elemental Ships (1-6)
    "SM_Ship_Tidebreaker": tidebreaker,
    "SM_Ship_TempestSpire": tempest_spire,
    "SM_Ship_Earthshaker": earthshaker,
    "SM_Ship_InfernoForge": inferno_forge,
    "SM_Ship_ZephyrLotus": zephyr_lotus,
    "SM_Ship_GlacierFang": glacier_fang,
    # Spaceships & Sci-Fi Craft (7-12)
    "SM_Ship_StarlightCruiser": starlight_cruiser,
    "SM_Ship_NebulaSaucer": nebula_saucer,
    "SM_Ship_VoidInterceptor": void_interceptor,
    "SM_Ship_OrbitalCarrier": orbital_carrier,
    "SM_Ship_PlasmaLancer": plasma_lancer,
    "SM_Ship_SolarArk": solar_ark,
    # Modern Naval Battleships (13-18)
    "SM_Ship_SteelDreadnought": steel_dreadnought,
    "SM_Ship_AegisDestroyer": aegis_destroyer,
    "SM_Ship_SkySubmarine": sky_submarine,
    "SM_Ship_FleetCarrier": fleet_carrier,
    "SM_Ship_HeavyCruiser": heavy_cruiser,
    "SM_Ship_GunshipMonitor": gunship_monitor,
    # Creative & Fantastical Designs (19-24)
    "SM_Ship_ClockworkSovereign": clockwork_sovereign,
    "SM_Ship_SkyNautilus": sky_nautilus,
    "SM_Ship_BoneRevenant": bone_revenant,
    "SM_Ship_CrystalSanctum": crystal_sanctum,
    "SM_Ship_DragonJunker": dragon_junker,
    "SM_Ship_BeetleScarab": beetle_scarab,
    # Specialized Outlaw & Industrial Ships (25-30)
    "SM_Ship_GyroCopter": gyro_copter,
    "SM_Ship_WhalerHarpooner": whaler_harpooner,
    "SM_Ship_LuxuryYacht": luxury_yacht,
    "SM_Ship_ShadowStalker": shadow_stalker,
    "SM_Ship_PowderKeg": powder_keg,
    "SM_Ship_CloudTrain": cloud_train,
}

FLEET_FACTIONS = {
    "SM_Ship_Tidebreaker": "Azure",
    "SM_Ship_TempestSpire": "Sorcerer",
    "SM_Ship_Earthshaker": "Emerald",
    "SM_Ship_InfernoForge": "Obsidian",
    "SM_Ship_ZephyrLotus": "Nomad",
    "SM_Ship_GlacierFang": "Azure",
    "SM_Ship_StarlightCruiser": "Syndicate",
    "SM_Ship_NebulaSaucer": "Sorcerer",
    "SM_Ship_VoidInterceptor": "Shadow",
    "SM_Ship_OrbitalCarrier": "Warden",
    "SM_Ship_PlasmaLancer": "Syndicate",
    "SM_Ship_SolarArk": "Gilded",
    "SM_Ship_SteelDreadnought": "Warden",
    "SM_Ship_AegisDestroyer": "Syndicate",
    "SM_Ship_SkySubmarine": "Obsidian",
    "SM_Ship_FleetCarrier": "Gilded",
    "SM_Ship_HeavyCruiser": "Warden",
    "SM_Ship_GunshipMonitor": "Scrap",
    "SM_Ship_ClockworkSovereign": "Gilded",
    "SM_Ship_SkyNautilus": "Nomad",
    "SM_Ship_BoneRevenant": "Sorcerer",
    "SM_Ship_CrystalSanctum": "Gilded",
    "SM_Ship_DragonJunker": "Crimson",
    "SM_Ship_BeetleScarab": "Emerald",
    "SM_Ship_GyroCopter": "Scrap",
    "SM_Ship_WhalerHarpooner": "Bosun",
    "SM_Ship_LuxuryYacht": "Gilded",
    "SM_Ship_ShadowStalker": "Shadow",
    "SM_Ship_PowderKeg": "Crimson",
    "SM_Ship_CloudTrain": "Scrap",
}

FLEET_ICONS = {name.replace("SM_", ""): name for name in FLEET_SHIPS}
