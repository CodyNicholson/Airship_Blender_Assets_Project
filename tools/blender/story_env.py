"""Shattered Skies environments: sky landmarks for each act, plus the fighting arenas.

Interiors use solid slab walls, because the gate makes normals face outward on closed meshes and
materials are single-sided: a slab's inner face shows into the room, a hollowed box would not.
Arenas keep the camera side (-Y) open, and publish party_slot_1..4 and enemy_slot_1..4 exactly as
SM_Env_BoardingDeck does, so the combat code needs no per-arena logic.
"""
import math
import random

from mathutils import Matrix


def _q(hq, high, low):
    return high if hq else low


def _combat_slots(mb, floor, spread=4.4, depth_step=1.05):
    for i in range(4):
        depth = -1.6 + i * depth_step
        offset = 1.0 if i % 2 else 0.0
        mb.socket(f"party_slot_{i + 1}", (-spread - offset, depth, floor))
        mb.socket(f"enemy_slot_{i + 1}", (spread + offset, depth, floor))
    mb.socket("centre_stage", (0, 0, floor))
    mb.socket("camera_look_at", (0, 0, floor + 1.1))


def _planks(mb, half_x, half_y, top, rows, hq, swatches=("wood_deck", "wood_light", "wood_deck", "wood_mid")):
    pw = 2 * half_y / rows
    for r in range(rows):
        y = -half_y + (r + 0.5) * pw
        mb.box((0, y, top - 0.05), (2 * half_x - 0.02, pw - 0.025, 0.1), swatches[r % len(swatches)])


def _rock_island(mb, rng, rows, sides, top_color="grass", under=("rock_dark", "rock"), lump=0.18):
    rings = []
    for radius, z, jitter in rows:
        ring = []
        for j in range(sides):
            a = 2 * math.pi * j / sides
            r = radius * (1 + rng.uniform(-lump, lump)) + rng.uniform(-jitter, jitter)
            ring.append((r * math.cos(a), r * math.sin(a), z + rng.uniform(-jitter, jitter)))
        rings.append(ring)
    half = len(rows) // 2
    mb.loft(rings, lambda i, _j: under[0] if i < half else under[1], caps=(True, False), smooth=False)
    top = rows[-1][1]
    grass = [[(x * s, y * s, top + dz) for x, y, _ in rings[-1]] for s, dz in ((1.02, -0.2), (0.4, 0.3))]
    mb.loft(grass, top_color, caps=(False, True), smooth=False)
    return top


def _house(mb, x, y, z, w, d, h, wall, roof, lit=None, yaw=0.0):
    place = Matrix.Translation((x, y, z)) @ Matrix.Rotation(yaw, 4, "Z")
    with mb.xf(place):
        mb.box((0, 0, h / 2), (w, d, h), wall)
        mb.loft([[(-w * 0.58, -d * 0.58, h), (w * 0.58, -d * 0.58, h), (w * 0.58, d * 0.58, h), (-w * 0.58, d * 0.58, h)], [(-w * 0.58, -0.05, h + w * 0.42), (w * 0.58, -0.05, h + w * 0.42), (w * 0.58, 0.05, h + w * 0.42), (-w * 0.58, 0.05, h + w * 0.42)]], roof)
        if lit:
            mb.box((0, -d / 2 - 0.02, h * 0.55), (w * 0.34, 0.08, h * 0.32), lit)


# ---- Sky landmarks --------------------------------------------------------------------------

def sky_vault(mb, hq):
    """Prologue heist target: a gilded imperial vault built into a floating rock."""
    rng = random.Random(30)
    top = _rock_island(mb, rng, [(0.8, 0, 0.2), (5, 5, 0.5), (9, 9.5, 0.5), (11, 12, 0.3)] if hq else [(1.2, 0, 0), (7, 6.5, 0.6), (11, 12, 0.3)], _q(hq, 12, 7), top_color="enamel")
    with mb.xf(Matrix.Translation((0, 0, top + 0.2))):
        mb.lathe([(8.0, 0.0), (8.0, 1.0), (6.4, 1.2), (6.4, 5.2), (4.8, 6.2), (2.2, 8.0), (0.3, 9.0)], _q(hq, 16, 8), lambda i, _j: ("enamel", "gold_dark", "faction_a", "gold_dark", "gold", "gold")[i], smooth=False)
    # Columns around the drum and a great vault door.
    n = _q(hq, 10, 0)
    for i in range(n):
        a = 2 * math.pi * i / n
        mb.tube((7.0 * math.cos(a), 7.0 * math.sin(a), top + 1.2), (7.0 * math.cos(a), 7.0 * math.sin(a), top + 5.5), 0.34, sides=6, color="enamel")
    with mb.xf(Matrix.Translation((0, -6.5, top + 3.2)) @ Matrix.Rotation(math.pi / 2, 4, "X")):
        mb.lathe([(2.4, -0.3), (2.4, 0.3), (1.8, 0.45), (0.5, 0.5)], _q(hq, 12, 6), lambda i, _j: "gold" if i != 1 else "iron", smooth=False)
    for sign in (1, -1):
        with mb.xf(Matrix.Translation((sign * 8.5, -2.0, top))):
            mb.lathe([(1.2, 0.0), (1.0, 5.5), (1.5, 5.9), (0.12, 8.6)], _q(hq, 8, 4), lambda i, _j: "gold" if i == 2 else "enamel", smooth=False)
        mb.sphere((sign * 8.5, -2.0, top + 8.9), 0.5, _q(hq, 6, 4), 3, "liftstone", smooth=False)
    mb.socket("door", (0, -7.0, top + 3.2))
    mb.socket("beacon_L", (8.5, -2.0, top + 8.9))
    mb.socket("beacon_R", (-8.5, -2.0, top + 8.9))


def scrap_isle(mb, hq):
    """Act I landmark: a rock half eaten by a salvage yard, with hulks wedged into it."""
    rng = random.Random(44)
    top = _rock_island(mb, rng, [(0.8, 0, 0.2), (4, 3.5, 0.8), (8, 8, 0.8), (10, 10.6, 0.3)] if hq else [(1.1, 0, 0), (6, 5.5, 0.7), (10, 10.6, 0.3)], _q(hq, 12, 7), top_color="toxic_dark", under=("rust_dark", "rock_dark"), lump=0.26)
    # A wrecked hull rammed in at an angle.
    with mb.xf(Matrix.Translation((-3.0, 2.0, top - 0.2)) @ Matrix.Rotation(0.5, 4, "Y") @ Matrix.Rotation(0.8, 4, "Z")):
        rings = []
        for y, w in ((-5.5, 0.3), (-3.5, 1.7), (1.5, 2.2), (5.5, 1.7)):
            rings.append([(-w, y, 0.2), (0, y, -0.8), (w, y, 0.2), (w, y, 2.0), (-w, y, 2.0)])
        mb.loft(rings, lambda i, j: "abyss" if (i + j) % 4 == 0 else ("rust" if j % 2 else "wood_dark"))
    # Crane and yard.
    mb.tube((4.5, -2.0, top), (4.5, -2.0, top + 8.0), 0.3, 0.18, sides=_q(hq, 6, 3), color="iron")
    mb.tube((4.5, -2.0, top + 7.6), (-1.5, -5.5, top + 9.0), 0.17, sides=_q(hq, 5, 3), color="rust")
    mb.tube((-1.5, -5.5, top + 9.0), (-1.5, -5.5, top + 4.5), 0.05, sides=3, color="iron")
    for x, y, w in ((-3.0, -3.0, 2.0), (6.0, 2.5, 1.7), (1.0, 5.5, 2.1)) if hq else ((-3.0, -3.0, 2.0),):
        _house(mb, x, y, top, w * 1.4, w, w * 1.1, "rust_dark", "iron", lit=("ember" if hq else None), yaw=rng.uniform(-0.5, 0.5))
    # Boiler stacks venting Scrap-Winds smog.
    for x, y in _q(hq, ((5.0, 2.0), (6.6, 3.0), (0.0, -6.0)), ((5.0, 2.0),)):
        mb.tube((x, y, top - 0.2), (x, y, top + 5.2), 0.5, 0.4, sides=_q(hq, 8, 4), color="iron")
        mb.socket(f"smog_{x:.0f}_{y:.0f}".replace("-", "n"), (x, y, top + 5.3))
    mb.socket("dock", (9.5, 0, top))
    mb.socket("hook", (-1.5, -5.5, top + 4.5))


def lift_mine(mb, hq):
    """Lift-Stone quarry. Exposed veins glow, explaining why the rock floats at all."""
    rng = random.Random(61)
    top = _rock_island(mb, rng, [(1.2, 0, 0.3), (5, 5, 0.8), (7.5, 9.5, 0.5), (8, 11.5, 0.3)] if hq else [(1.5, 0, 0), (6, 6, 0.6), (8, 11.5, 0.3)], _q(hq, 12, 7), top_color="rock", under=("rock_dark", "liftstone_dark"), lump=0.2)
    for i in range(_q(hq, 12, 4)):
        a = rng.uniform(0, 6.28)
        z = rng.uniform(1.0, 9.0)
        r = 1.5 + z * 0.65
        x, y = r * math.cos(a), r * math.sin(a)
        with mb.xf(Matrix.Translation((x, y, z)) @ Matrix.Rotation(rng.uniform(1.0, 2.1), 4, "Y") @ Matrix.Rotation(a, 4, "X")):
            s = rng.uniform(0.5, 1.1)
            mb.lathe([(s * 0.5, -0.6), (s * 0.55, s * 0.6), (s * 0.06, s * 1.5)], _q(hq, 5, 3), "liftstone", smooth=False)
    # Scaffold and a pit head.
    for x, y in ((-3.0, -6.0), (3.0, -6.0), (-3.0, -7.8), (3.0, -7.8)):
        mb.tube((x, y, 1.5), (x, y, top + 1.0), 0.13, sides=_q(hq, 4, 3), color="wood_dark")
    mb.box((0, -6.9, top + 1.0), (7.5, 3.2, 0.2), "wood_mid")
    if hq:
        for z in (4.0, 7.0):
            mb.box((0, -6.9, z), (7.2, 3.0, 0.15), "wood_dark")
    for sign in (1, -1):
        mb.tube((sign * 1.6, 0, top), (0, 0, top + 6.5), 0.18, sides=_q(hq, 4, 3), color="wood_dark")
    with mb.xf(Matrix.Translation((0, 0.0, top + 6.3)) @ Matrix.Rotation(math.pi / 2, 4, "X")):
        mb.lathe([(1.1, -0.1), (1.1, 0.1)], _q(hq, 10, 6), "iron_light", smooth=False)
    mb.tube((0, -0.2, top + 5.6), (0, -6.0, top + 1.2), 0.04, sides=3, color="rope")
    _house(mb, 3.8, 1.7, top, 2.6, 2.0, 2.2, "wood_mid", "iron", lit="lamp" if hq else None)
    mb.socket("loot", (0, -6.9, top + 1.2))


def smugglers_haven(mb, hq):
    """Act II port: a stack of timber docks and lanterns on a spire, in the Syndicate's colours."""
    rng = random.Random(70)
    # A slender spire of rock, far taller than wide, so the Jetstream wraps round it.
    rows = [(0.6, 0, 0.1), (3.0, 5, 0.3), (4.6, 11, 0.4), (4.0, 15, 0.3), (5.4, 19, 0.3)] if hq else [(1, 0, 0), (4.2, 9, 0.3), (5.4, 19, 0.3)]
    top = _rock_island(mb, rng, rows, _q(hq, 10, 6), top_color="wood_mid", lump=0.12)
    # Ring of docks.
    tiers = _q(hq, ((10.0, 5.6), (15.0, 6.0), (top, 7.2)), ((top, 7.2),))
    for z, r in tiers:
        with mb.xf(Matrix.Translation((0, 0, z))):
            mb.lathe([(r, -0.25), (r, 0.05), (r - 1.2, 0.05)], _q(hq, 12, 6), "wood_deck", smooth=False)
        n = _q(hq, 5, 3)
        for k in range(n):
            a = 2 * math.pi * (k + 0.3) / n
            x, y = r * math.cos(a), r * math.sin(a)
            mb.tube((x, y, z), (x * 0.5, y * 0.5, z - 2.7), 0.1, sides=_q(hq, 4, 3), color="wood_dark")
            if hq or z == top:
                mb.tube((x, y, z), (x, y, z + 1.6), 0.06, sides=3, color="wood_dark")
                mb.sphere((x, y, z + 1.75), 0.2, _q(hq, 6, 4), 3, "lamp", smooth=False)
    # Hanging jetties.
    for k, a in enumerate((0.5, 2.3, 4.4)):
        x, y = math.cos(a), math.sin(a)
        with mb.xf(Matrix.Translation((x * 7.2, y * 7.2, top)) @ Matrix.Rotation(a, 4, "Z")):
            mb.box((3.2, 0, -0.1), (6.4, 1.3, 0.2), "wood_light")
        mb.socket(f"berth_{k}", (x * 12, y * 12, top))
    # Town on top: stacked towers and a Syndicate lighthouse.
    for x, y, w, d, h, wall, roof in ((-2.5, -2.8, 2.6, 2.2, 2.4, "wood_mid", "faction_a"), (2.5, -2.3, 2.2, 2.2, 3.2, "wood_red", "faction_c"), (-2.6, 2.3, 2.4, 2.1, 2.8, "wood_light", "faction_a"), (3.2, 2.5, 2.4, 2.4, 2.2, "wood_mid", "faction_c")) if hq else ((-2.5, -2.8, 2.6, 2.2, 2.4, "wood_mid", "faction_a"), (2.5, 2.5, 2.4, 2.4, 2.8, "wood_red", "faction_c")):
        _house(mb, x, y, top, w, d, h, wall, roof, lit="lamp" if hq else None, yaw=rng.uniform(-0.3, 0.3))
    with mb.xf(Matrix.Translation((0, 0, top))):
        mb.lathe([(1.3, 0.0), (0.85, 8.0), (1.2, 8.3), (1.2, 8.4), (0.8, 8.4)], _q(hq, 8, 5), lambda i, _j: "faction_b" if i >= 1 else "enamel", smooth=False)
        mb.lathe([(0.7, 8.4), (0.7, 9.5), (0.95, 9.6), (0.12, 10.8)], _q(hq, 8, 5), lambda i, _j: "plasma" if i == 0 else "faction_a", smooth=False)
    mb.socket("beacon", (0, 0, top + 9.0))


def free_haven(mb, hq):
    """Act IV stakes: the free pirate town the Armada is about to bombard. Warm, lived in, alive."""
    rng = random.Random(90)
    top = _rock_island(mb, rng, [(0.7, 0, 0.2), (4, 4, 0.5), (8, 7.5, 0.5), (11, 9.5, 0.3)] if hq else [(1, 0, 0), (6.5, 5, 0.5), (11, 9.5, 0.3)], _q(hq, 14, 7))
    n = _q(hq, 11, 4)
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.15, 0.15)
        r = rng.uniform(4.0, 7.8)
        w = rng.uniform(1.9, 2.8)
        _house(mb, r * math.cos(a), r * math.sin(a), top + 0.3, w, w * 0.84, rng.uniform(1.8, 3.4), rng.choice(("wood_mid", "wood_light", "wood_red", "canvas_dark")), rng.choice(("faction_a", "faction_c", "wood_red")), lit="lamp" if hq else None, yaw=a + math.pi / 2)
    # Tall pirate mast in the square, with a huge flag visible from the sky lanes.
    mb.tube((0, 0, top), (0, 0, top + 12.0), 0.3, 0.14, sides=_q(hq, 8, 4), color="wood_mid")
    mb.plate([(0, 0, top + 11.8), (5.0, 0, top + 10.8), (3.8, 0, top + 9.8), (5.0, 0, top + 8.6), (0, 0, top + 8.6)], 0.05, "faction_a")
    # Docked ships' berths and hanging lanterns.
    for k, a in enumerate((0.0, 2.1, 4.2)):
        x, y = math.cos(a), math.sin(a)
        with mb.xf(Matrix.Translation((x * 11, y * 11, top - 0.1)) @ Matrix.Rotation(a, 4, "Z")):
            mb.box((2.3, 0, 0), (4.6, 1.4, 0.2), "wood_deck")
        mb.socket(f"berth_{k}", (x * 15.5, y * 15.5, top))
    if hq:
        for i in range(10):
            a = 2 * math.pi * i / 10
            mb.tube((10.4 * math.cos(a), 10.4 * math.sin(a), top - 0.2), (10.4 * math.cos(a), 10.4 * math.sin(a), top + 1.5), 0.06, sides=3, color="wood_dark")
            mb.sphere((10.4 * math.cos(a), 10.4 * math.sin(a), top + 1.66), 0.2, 5, 3, "lamp", smooth=False)
        for x, y in ((-1.2, 2.4), (1.5, -2.1)):
            with mb.xf(Matrix.Translation((x, y, top))):
                mb.tube((0, 0, 0.0), (0, 0, 1.0), 0.12, sides=4, color="wood_dark")
                mb.lathe([(1.0, 1.0), (0.6, 2.0), (0.08, 3.2)], 6, "grass_dark", smooth=False)


def _puff_cloud(mb, hq, seed, base, shade, puffs_hq=9, puffs_lq=4, stretch=10.0, tall=1.0):
    rng = random.Random(seed)
    puffs = _q(hq, puffs_hq, puffs_lq)
    for i in range(puffs):
        x = (i - (puffs - 1) / 2) * (stretch / puffs)
        edge = 1 - abs(i - (puffs - 1) / 2) / (puffs / 2)
        r = 1.5 + 2.1 * edge + rng.uniform(-0.2, 0.2)
        y = rng.uniform(-1.3, 1.3)
        z = r * 0.72 * tall
        mb.sphere((x, y, z), (r * 1.1, r, r * 0.72 * tall), _q(hq, 10, 6), _q(hq, 6, 3), lambda ring, _j: shade if ring == 0 else base, smooth=True)


def toxic_cloud(mb, hq):
    """Scrap-Winds smog bank: sickly, low and heavy. Hides enemies and damages the hull over time."""
    _puff_cloud(mb, hq, 12, "toxic", "toxic_dark", tall=0.72)
    mb.socket("centre", (0, 0, 2.0))


def storm_cloud(mb, hq):
    """Maelstrom and cyclone cloud: towering and black, with lightning waiting at its sockets."""
    _puff_cloud(mb, hq, 17, "storm", "storm_dark", tall=1.7, puffs_hq=8, puffs_lq=4)
    mb.socket("lightning_0", (-2.0, 0, 0.3))
    mb.socket("lightning_1", (2.2, 0, 0.3))


def storm_wall(mb, hq):
    """One arc of the Maelstrom's eye wall. Twelve instances rotated 30 degrees about the ring_centre
    socket make the full ring. The inner face looks towards ring_centre, where the player flies."""
    arc = math.radians(30)
    radius = 150.0
    height = 90.0
    span = _q(hq, 14, 5)
    levels = _q(hq, 12, 5)

    def billow(u, k):
        """Smooth cloud field, zero at both edges so neighbouring arcs meet without a seam."""
        return math.sin(math.pi * u) * (math.sin(u * 9.0 + k * 5.0) + 0.5 * math.sin(u * 17.0 - k * 11.0))

    rings = []
    for lv in range(levels + 1):
        k = lv / levels
        ring = []
        for j in range(span + 1):
            u = j / span
            a = -arc / 2 + arc * u
            r = radius + 8 * math.sin(k * math.pi * 3.0) + 6.0 * billow(u, k)
            ring.append((r * math.sin(a), radius - r * math.cos(a), height * k))
        # The flat dark side faces away from ring_centre; the player sees the billowing inner face.
        rings.append(ring + [(x, y - 12.0, z) for x, y, z in reversed(ring)])

    # One swatch per sheet: smooth shading over the billows gives soft cloud. Mixed swatches here
    # show as hard-edged blocks, because each face maps to a single atlas cell.
    def paint(_i, j):
        return "storm_dark" if j >= span else "storm"

    mb.loft(rings, paint, smooth=True)
    mb.socket("ring_centre", (0, radius, 0))
    for k in range(_q(hq, 3, 1)):
        a = -arc * 0.3 + k * arc * 0.3
        mb.socket(f"lightning_{k}", (radius * math.sin(a), -2.0, 30 + k * 18))


def lightning_bolt(mb, hq):
    """Hazard mesh for Act IV. Glows through the emissive atlas: flash it for a few frames only.
    Strike point at the bottom (pivot), top reaches 60 m."""
    rng = random.Random(8)
    n = _q(hq, 11, 6)
    points = [(0, 0, 0)]
    for i in range(1, n):
        k = i / (n - 1)
        wobble = 7.0 * math.sin(k * math.pi)
        points.append((rng.uniform(-wobble, wobble), rng.uniform(-wobble, wobble) * 0.6, 60.0 * k))
    mb.path(points, [0.25 + 0.65 * (i / (n - 1)) for i in range(n)], _q(hq, 4, 3), "lightning")
    if hq:
        for branch in (3, 6, 8):
            sx, sy, sz = points[branch]
            mb.path([(sx, sy, sz), (sx + rng.uniform(-6, 6), sy + rng.uniform(-3, 3), sz - 6), (sx + rng.uniform(-9, 9), sy + rng.uniform(-3, 3), sz - 13)], [0.3, 0.18, 0.04], 3, "lightning")
    mb.socket("strike", (0, 0, 0))


def updraft_column(mb, hq):
    """Act II wind draft and Act IV updraft. A spiral of ribbons: scroll or spin it about local Z."""
    n = _q(hq, 3, 2)
    seg = _q(hq, 16, 8)
    height = 40.0
    for r in range(n):
        phase = 2 * math.pi * r / n
        rings = []
        for i in range(seg + 1):
            k = i / seg
            radius = 4.0 + 6.0 * k
            a = phase + k * 3.5 * math.pi
            cx, cy = radius * math.cos(a), radius * math.sin(a)
            tx, ty = -math.sin(a), math.cos(a)
            width = 0.22 + 1.05 * math.sin(k * math.pi)
            z = height * k
            rings.append([(cx - tx * width, cy - ty * width, z), (cx + tx * width, cy + ty * width, z), (cx + tx * width, cy + ty * width, z + 0.15), (cx - tx * width, cy - ty * width, z + 0.15)])
        mb.loft(rings, "wind")
    mb.socket("top", (0, 0, height))


def wind_current(mb, hq):
    """Lyra's Wind Currents: a straight ribbon, flow towards -Y. Chain them end to end at sockets."""
    length = 60.0
    seg = _q(hq, 16, 8)
    streams = _q(hq, 5, 3)
    rng = random.Random(77)
    for s in range(streams):
        x0 = (s - (streams - 1) / 2) * 3.6
        z0 = rng.uniform(1.0, 5.0)
        amp = rng.uniform(0.6, 1.4)
        phase = rng.uniform(0, 6.28)
        rings = []
        for i in range(seg + 1):
            k = i / seg
            y = length * (0.5 - k)
            x = x0 + amp * math.sin(k * 6.28 * 2 + phase)
            z = z0 + amp * 0.7 * math.cos(k * 6.28 * 2 + phase)
            w = 0.02 + 0.3 * math.sin(k * math.pi)
            rings.append([(x - w, y, z), (x + w, y, z), (x + w, y, z + 0.06), (x - w, y, z + 0.06)])
        mb.loft(rings, "wind")
    mb.socket("flow_start", (0, length / 2, 3.0))
    mb.socket("flow_end", (0, -length / 2, 3.0))


def undertow_disc(mb, hq):
    """The Undertow: a storm-choked abyss seen from above. Tile it far below the action."""
    rings_n = _q(hq, 10, 5)
    sides = _q(hq, 24, 12)
    radius = 200.0
    rng = random.Random(33)
    rings = []
    for i in range(rings_n + 1):
        k = i / rings_n
        ring = []
        for j in range(sides):
            a = 2 * math.pi * j / sides + k * 1.5
            r = 6.0 + radius * k
            z = rng.uniform(0.0, 3.0) * (0 < i < rings_n) + 8.0 * math.sin(k * 3.14) * (0.6 + 0.4 * math.sin(a * 3))
            ring.append((r * math.cos(a), r * math.sin(a), z))
        rings.append(ring)

    def paint(i, j):
        if i == 0:
            return "abyss"
        if (i * 2 + j) % 7 == 0:
            return "plasma" if i < rings_n // 2 and j % 3 == 0 else "storm"
        return "storm_dark" if (i + j) % 3 else "abyss"

    mb.loft(rings, paint, smooth=True)
    mb.socket("eye", (0, 0, 0.5))


def debris_field(mb, hq):
    """Scrap-Winds junk cluster for mid-distance dressing. One draw call, many chunks."""
    rng = random.Random(55)
    n = _q(hq, 26, 12)
    for i in range(n):
        x, y, z = rng.uniform(-16, 16), rng.uniform(-16, 16), rng.uniform(0.0, 13.0)
        kind = i % 3
        place = Matrix.Translation((x, y, z)) @ Matrix.Rotation(rng.uniform(0, 3.14), 4, "X") @ Matrix.Rotation(rng.uniform(0, 3.14), 4, "Y")
        s = rng.uniform(0.6, 1.9)
        with mb.xf(place):
            if kind == 0:
                mb.box((0, 0, 0), (s * 0.3, s * 2.4, s * 0.2), rng.choice(("rust", "wood_dark", "iron")))
            elif kind == 1:
                mb.lathe([(s * 0.5, -s * 0.4), (s * 0.7, 0.0), (s * 0.2, s * 0.55)], _q(hq, 6, 4), rng.choice(("rust_dark", "iron", "wood_mid")), smooth=False)
            else:
                mb.plate([(0, 0, 0), (s * 1.2, 0, s * 0.2), (s * 0.9, 0, s * 1.2), (0.1 * s, 0, s * 0.8)], 0.08, rng.choice(("rust", "faction_a", "iron_light")))


# ---- Arenas ---------------------------------------------------------------------------------

def _bulwark(mb, half_l, half_w, floor, wall="wood_mid", cap="faction_a", wall_h=1.05, wall_t=0.22):
    z = floor + wall_h / 2
    y = half_w - wall_t / 2
    mb.box((0, y, z), (2 * half_l, wall_t, wall_h), wall)
    mb.box((0, y, floor + wall_h + 0.05), (2 * half_l + 0.2, wall_t + 0.14, 0.12), cap)
    for side in (1, -1):
        x = side * (half_l - wall_t / 2)
        mb.box((x, 0, z), (wall_t, 2 * half_w, wall_h), wall)
        mb.box((x, 0, floor + wall_h + 0.05), (wall_t + 0.14, 2 * half_w + 0.2, 0.12), cap)


def scrap_deck(mb, hq):
    """Act I boss arena on the Iron Maw: rusted plate, the winch behind you, and the cargo bay doors
    wide open to the Undertow right behind Krag. The duel's danger is visible from frame one."""
    half_l, half_w, floor = 8.0, 4.0, 0.6
    rows = _q(hq, 8, 4)
    pw = 2 * half_w / rows
    for r in range(rows):
        y = -half_w + (r + 0.5) * pw
        mb.box((-1.8, y, floor - 0.05), (12.4, pw - 0.03, 0.1), ("rust_dark", "rust", "rust_dark", "iron")[r % 4])
    mb.box((-1.8, 0, floor / 2 - 0.05), (12.4, 2 * half_w, floor - 0.1), "rust_dark")
    # Bay opening at +X: a dark hole in the deck between x=4.4 and x=7.9, with walkways either side.
    mb.box((-1.8, 0, -0.6), (12.4, 2 * half_w, 1.0), "rust_dark")
    for sign in (1, -1):
        mb.box((6.2, sign * 3.1, 0.0), (3.6, 1.8, 1.2), "iron")
        # Doors hinged at the hole's long edges, hanging open underneath.
        mb.box((6.2, sign * 2.14, -1.8), (3.5, 0.12, 3.6), "iron_light")
        mb.box((6.2, sign * 2.08, -1.8), (3.5, 0.06, 0.3), "ember")
        # Hazard edging round the drop.
        mb.box((6.2, sign * 2.26, 0.61), (3.6, 0.12, 0.04), "gold_dark")
    mb.box((7.9, 0, 0.0), (0.2, 4.4, 1.2), "iron")
    mb.box((4.45, 0, 0.61), (0.12, 4.4, 0.04), "gold_dark")
    wall_y = half_w - 0.11
    mb.box((0, wall_y, floor + 0.5), (16.0, 0.22, 1.0), "rust")
    mb.box((0, wall_y, floor + 1.06), (16.2, 0.36, 0.12), "iron")
    mb.box((-7.9, 0, floor + 0.5), (0.22, 2 * half_w, 1.0), "rust")
    # The winch, huge against the back wall: mirrors SM_Prop_HarpoonWinch.
    with mb.xf(Matrix.Translation((-4.0, 2.6, floor))):
        mb.box((0, 0, 0.5), (3.2, 1.4, 1.0), "iron", top_scale=0.88)
        with mb.xf(Matrix.Translation((-1.2, 0, 1.5)) @ Matrix.Rotation(math.pi / 2, 4, "Y")):
            mb.lathe([(0.8, 0.0), (0.8, 0.25), (0.5, 0.25), (0.5, 2.15), (0.8, 2.15), (0.8, 2.4)], _q(hq, 10, 5), lambda i, _j: "rope" if i == 2 else "iron_light", smooth=False)
    # Iron-chain rigging and a salvage crane.
    mb.tube((3.5, 3.4, floor), (3.5, 3.4, 8.5), 0.26, 0.15, sides=_q(hq, 6, 3), color="iron")
    mb.tube((3.5, 3.4, 8.0), (6.2, 0.0, 7.0), 0.11, sides=_q(hq, 4, 3), color="rust_dark")
    mb.tube((6.2, 0.0, 7.0), (6.2, 0.0, 2.6), 0.035, sides=3, color="iron")
    mb.plate([(5.5, 0.0, 2.6), (6.9, 0.0, 2.6), (6.2, 0.0, 1.5)], 0.08, "iron_light")
    # Clutter behind the fight.
    if hq:
        for x, y, r in ((-7.0, -1.8, 0.33), (-7.1, -1.1, 0.33), (-6.3, -2.6, 0.33)):
            with mb.xf(Matrix.Translation((x, y, floor))):
                mb.lathe([(r * 0.8, 0.0), (r, 0.45), (r * 0.8, 0.9)], 8, "rust", smooth=False)
        mb.box((0.6, 3.25, floor + 0.4), (0.8, 0.8, 0.8), "wood_light")
        mb.box((1.45, 3.1, floor + 0.3), (0.6, 0.6, 0.6), "wood_mid")
    # Enemy slots stop short of the hole, which starts at x=4.4.
    _combat_slots(mb, floor, spread=2.9)
    mb.socket("winch_controls", (-1.5, 3.1, floor))
    mb.socket("bay_edge", (4.4, 0, floor))
    mb.socket("krag_start", (3.2, 0, floor))


def gale_quarterdeck(mb, hq):
    """The Gale's quarterdeck at dusk: the set for the prologue cutscenes aboard Cassian's ship. It was
    the main menu before SM_Env_HangarHub, which kept its footprint, stations and sockets."""
    half_l, half_w, floor = 9.0, 5.0, 0.6
    _planks(mb, half_l, half_w, floor, _q(hq, 10, 4), hq)
    mb.box((0, 0, floor / 2 - 0.05), (2 * half_l, 2 * half_w, floor - 0.1), "wood_dark")
    mb.box((0, 0, -0.6), (2 * half_l, 2 * half_w, 1.0), "wood_dark")
    _bulwark(mb, half_l, half_w, floor)
    # Raised helm platform at the back, with stairs: the hub's "throne".
    px, py = 0.0, 3.3
    mb.box((px, py, floor + 0.4), (7.2, 3.0, 0.8), "wood_mid")
    mb.box((px, py, floor + 0.84), (7.4, 3.2, 0.08), "wood_deck")
    for sign in (1, -1):
        for i in range(3):
            mb.box((sign * 4.2, py - 0.1 - i * 0.3, floor + 0.13 + (2 - i) * 0.26), (0.9, 0.38, 0.26), "wood_light")
    # The helm itself.
    mb.tube((0, 3.2, floor + 0.88), (0, 3.2, floor + 1.72), 0.1, sides=_q(hq, 6, 4), color="wood_mid")
    with mb.xf(Matrix.Translation((0, 3.05, floor + 1.9)) @ Matrix.Rotation(math.pi / 2, 4, "X")):
        mb.lathe([(0.55, -0.04), (0.55, 0.04), (0.46, 0.04), (0.46, -0.04), (0.55, -0.04)], _q(hq, 12, 6), "wood_light", smooth=False, caps=(False, False))
        for i in range(_q(hq, 6, 3)):
            a = math.pi * i / _q(hq, 6, 3)
            mb.tube((-0.5 * math.cos(a), -0.5 * math.sin(a), 0), (0.5 * math.cos(a), 0.5 * math.sin(a), 0), 0.022, sides=3, color="wood_dark")
    # Great mast and furled sail: a sense of ship above the frame.
    mast_y = 1.5
    mb.tube((-5.6, mast_y, floor), (-5.6, mast_y, 12.0), 0.3, 0.17, sides=_q(hq, 8, 4), color="wood_mid", smooth=hq)
    mb.tube((-9.0, mast_y - 0.2, 8.4), (-2.2, mast_y - 0.2, 8.4), 0.1, sides=_q(hq, 4, 3), color="wood_dark")
    mb.plate([(-8.7, mast_y - 0.25, 8.3), (-2.5, mast_y - 0.25, 8.3), (-3.0, mast_y - 0.7, 5.8), (-8.2, mast_y - 0.7, 5.8)], 0.06, "canvas")
    # Rigging that frames the top-right of the shot.
    for x, y in ((8.6, 4.6), (2.0, 4.8), (-2.0, 4.8)):
        mb.tube((x, y, floor + 1.1), (-5.6, mast_y, 11.0), 0.025, sides=3, color="rope")
    # Rook's cannon station, Lyra's table, Sable's perch, Thorne's bench, Morrow's cell-hatch.
    # (Props go in the game as separate models; these low blocks just give them a home on deck.)
    for i in range(_q(hq, 3, 1)):
        x = 6.9
        y = 3.3 - i * 2.2
        mb.box((x, y, floor + 0.21), (0.9, 1.1, 0.42), "wood_mid")
        mb.tube((x + 0.05, y, floor + 0.6), (x + 1.7, y, floor + 0.73), 0.13, 0.1, sides=_q(hq, 8, 4), color="iron")
    # Lanterns on the rail for warmth.
    if hq:
        for x in (-7.5, -3.4, 3.4, 7.5):
            mb.tube((x, 4.72, floor + 1.15), (x, 4.72, floor + 2.3), 0.04, sides=3, color="iron")
            mb.tube((x, 4.72, floor + 2.3), (x, 4.42, floor + 2.3), 0.025, sides=3, color="iron")
            mb.sphere((x, 4.42, floor + 2.05), 0.16, 6, 3, "lamp", smooth=False)
        mb.box((-8.0, 0.8, floor + 0.4), (0.8, 0.8, 0.8), "wood_light")
        mb.box((-8.0, -0.2, floor + 0.3), (0.6, 0.6, 0.6), "wood_mid")
        with mb.xf(Matrix.Translation((-7.8, -1.2, floor))):
            mb.lathe([(0.25, 0.0), (0.33, 0.45), (0.25, 0.9)], 8, "wood_mid", smooth=False)
        for i in range(4):
            mb.box((-0.36 + i * 0.24, -0.6, floor + 0.01), (0.14, 1.2, 0.03), "iron")
    mb.socket("station_helm", (0, 2.4, floor + 0.88))
    mb.socket("station_rook", (6.1, 3.3, floor))
    mb.socket("station_lyra", (-2.6, 1.0, floor))
    mb.socket("station_lyra_table", (-2.6, 1.85, floor))
    mb.socket("station_sable", (-7.0, 3.6, floor))
    mb.socket("station_thorne", (5.0, -1.0, floor))
    mb.socket("station_morrow", (-5.0, -2.0, floor))
    mb.socket("station_bounty_board", (2.6, 4.7, floor))
    mb.socket("camera_look_at", (0, 0.5, floor + 1.6))
    mb.socket("lantern_0", (-7.5, 4.42, floor + 2.05))
    mb.socket("lantern_1", (7.5, 4.42, floor + 2.05))
    _combat_slots(mb, floor, spread=4.0)


# The ship you fly sits in the berth beyond the hangar's bay, broadside to the camera. The game scales
# each ship to fit this length, so a sloop and a galleon both fill the berth.
HANGAR_BERTH = (0.0, 11.5, 5.2)
HANGAR_BERTH_LENGTH = 13.0


def hangar_hub(mb, hq):
    """Main menu: the crew's hangar, with the ship you're flying moored in the berth through the bay
    behind them. Each crew member has a tappable station. The camera side (-Y) stays open; the bay
    (+Y) frames the ship. Swap the faction atlas to match the ship you currently command."""
    half_l, half_w, floor = 9.0, 5.0, 0.6
    # Floor: workshop planks on a heavy sub-floor, with a painted line where the dock begins.
    _planks(mb, half_l, half_w, floor, _q(hq, 10, 4), hq, swatches=("wood_deck", "iron_light", "wood_deck", "wood_mid"))
    mb.box((0, 0, floor / 2 - 0.05), (2 * half_l, 2 * half_w, floor - 0.1), "wood_dark")
    mb.box((0, 0, -0.6), (2 * half_l, 2 * half_w, 1.0), "wood_dark")
    mb.box((0, half_w - 0.35, floor + 0.01), (12.6, 0.3, 0.03), "faction_a")

    # Timber frame walls down each side: posts, a top beam, and a half-height plank wall.
    wall_top = 9.0
    for side in (1, -1):
        x = side * (half_l - 0.25)
        for y in _q(hq, (-4.5, 0.0, 4.5), (-4.5, 4.5)):
            mb.box((x, y, (floor + wall_top) / 2), (0.5, 0.5, wall_top - floor), "wood_mid")
        mb.box((x, 0, wall_top), (0.55, 2 * half_w, 0.5), "wood_dark")
        mb.box((x, 0, floor + 1.4), (0.3, 2 * half_w, 2.8), "wood_red")
        if hq:
            for y0, y1 in ((-4.5, 0.0), (0.0, 4.5)):
                mb.tube((x, y0, floor + 2.8), (x, y1, wall_top - 0.3), 0.09, sides=3, color="wood_dark")

    # Roof trusses, open to the sky so the dusk light still reaches the crew.
    for y in _q(hq, (-3.2, 0.8, 4.6), (-2.0, 4.6)):
        mb.box((0, y, wall_top + 0.2), (2 * half_l, 0.4, 0.45), "wood_dark")
        if hq:
            for side in (1, -1):
                mb.tube((side * 8.6, y, wall_top + 0.2), (0, y, wall_top + 1.9), 0.08, sides=3, color="wood_mid")

    # The back wall, with a tall bay opening onto the berth.
    bay_half, bay_top = 6.6, 11.0
    for side in (1, -1):
        mb.box((side * bay_half, half_w, (floor + bay_top) / 2), (1.0, 1.0, bay_top - floor), "wood_mid")
        mb.box((side * (bay_half + half_l) / 2, half_w + 0.15, (floor + wall_top) / 2), (half_l - bay_half, 0.3, wall_top - floor), "wood_red")
        mb.plate([(side * (bay_half - 0.55), half_w - 0.52, bay_top - 0.6), (side * (bay_half - 1.75), half_w - 0.52, bay_top - 0.6),
                  (side * (bay_half - 1.75), half_w - 0.52, bay_top - 3.4), (side * (bay_half - 1.15), half_w - 0.52, bay_top - 2.9),
                  (side * (bay_half - 0.55), half_w - 0.52, bay_top - 3.4)], 0.04, "faction_a")
    mb.box((0, half_w, bay_top + 0.35), (2 * bay_half + 1.2, 1.1, 0.8), "wood_dark")
    # The bay door, rolled up under the lintel.
    mb.tube((-bay_half + 0.5, half_w - 0.1, bay_top - 0.45), (bay_half - 0.5, half_w - 0.1, bay_top - 0.45), 0.38, sides=_q(hq, 8, 4), color="canvas_dark")

    # Raised overlook at the back, where Vane keeps watch over the ship: the hub's "throne".
    px, py = 0.0, 3.3
    mb.box((px, py, floor + 0.4), (7.2, 3.0, 0.8), "wood_mid")
    mb.box((px, py, floor + 0.84), (7.4, 3.2, 0.08), "wood_deck")
    for sign in (1, -1):
        for i in range(_q(hq, 3, 1)):
            mb.box((sign * 4.2, py - 0.1 - i * 0.3, floor + 0.13 + (2 - i) * 0.26), (0.9, 0.38, 0.26), "wood_light")
    mb.box((0, py + 1.45, floor + 1.35), (7.2, 0.12, 0.08), "iron")
    for x in (-3.5, 3.5):
        mb.box((x, py + 1.45, floor + 1.1), (0.12, 0.12, 0.6), "iron")

    # The berth: a dock reaching out from the bay, with two cradles under the ship's keel.
    bx, by, bz = HANGAR_BERTH
    mb.box((0, (half_w + 17.0) / 2, floor - 0.2), (2 * bay_half - 0.4, 17.0 - half_w, 0.4), "wood_deck")
    for x in (-5.5, 5.5):
        mb.tube((x, by + 4.0, floor - 0.4), (x, by + 4.0, -6.0), 0.3, sides=_q(hq, 6, 4), color="wood_dark")
    for x in (-3.6, 3.6):
        mb.box((x, by, floor + 0.9), (0.5, 0.6, 1.8), "iron")
        mb.box((x, by, floor + 1.9), (0.6, 3.2, 0.3), "wood_mid")
        if hq:
            for side in (1, -1):
                mb.box((x, by + side * 1.45, floor + 2.35), (0.5, 0.3, 0.7), "leather_dark")

    # A gantry crane over the berth, its hook hanging just above the deck of the ship.
    crane_y, crane_top = 16.4, 12.6
    for x in (-6.0, 6.0):
        mb.box((x, crane_y, (floor - 0.4 + crane_top) / 2), (0.6, 0.6, crane_top - floor + 0.4), "iron")
    mb.box((0, crane_y, crane_top), (12.6, 0.7, 0.6), "iron_light")
    mb.box((2.2, (crane_y + by) / 2, crane_top - 0.5), (1.0, crane_y - by + 0.6, 0.4), "iron")
    if hq:
        mb.tube((2.2, by, crane_top - 0.7), (2.2, by, bz + 3.6), 0.05, sides=3, color="rope")
        mb.box((2.2, by, bz + 3.4), (0.4, 0.4, 0.5), "iron")

    # Workshop: Rook's gun rack, crates, a barrel and Thorne's bench.
    for i in range(_q(hq, 3, 1)):
        x = 7.4
        y = 3.3 - i * 2.2
        mb.box((x, y, floor + 0.21), (0.9, 1.1, 0.42), "wood_mid")
        mb.tube((x + 0.05, y, floor + 0.6), (x - 1.6, y, floor + 0.73), 0.13, 0.1, sides=_q(hq, 8, 4), color="iron")
    if hq:
        mb.box((-8.0, 0.8, floor + 0.4), (0.8, 0.8, 0.8), "wood_light")
        mb.box((-8.0, -0.2, floor + 0.3), (0.6, 0.6, 0.6), "wood_mid")
        with mb.xf(Matrix.Translation((-7.8, -1.2, floor))):
            mb.lathe([(0.25, 0.0), (0.33, 0.45), (0.25, 0.9)], 8, "wood_mid", smooth=False)
        mb.box((6.0, -2.6, floor + 0.45), (2.0, 0.9, 0.9), "wood_mid")
        mb.box((6.0, -2.6, floor + 0.95), (2.2, 1.0, 0.1), "wood_light")
        mb.plate([(-8.7, -3.6, floor + 1.4), (-8.7, -1.6, floor + 1.4), (-8.7, -1.6, floor + 2.6), (-8.7, -3.6, floor + 2.6)], 0.05, "parchment")
        # Lanterns on posts by the bay, for warmth.
        for x in (-7.5, 7.5):
            mb.tube((x, 4.72, floor), (x, 4.72, floor + 2.3), 0.05, sides=3, color="iron")
            mb.tube((x, 4.72, floor + 2.3), (x, 4.42, floor + 2.3), 0.025, sides=3, color="iron")
            mb.sphere((x, 4.42, floor + 2.05), 0.16, 6, 3, "lamp", smooth=False)

    mb.socket("station_helm", (0, 2.4, floor + 0.88))
    mb.socket("station_rook", (6.1, 3.3, floor))
    mb.socket("station_lyra", (-2.6, 1.0, floor))
    mb.socket("station_lyra_table", (-2.6, 1.85, floor))
    mb.socket("station_sable", (-7.0, 3.6, floor))
    mb.socket("station_thorne", (5.0, -1.0, floor))
    mb.socket("station_morrow", (-5.0, -2.0, floor))
    mb.socket("station_bounty_board", (-7.9, 4.3, floor))
    mb.socket("lantern_0", (-7.5, 4.42, floor + 2.05))
    mb.socket("lantern_1", (7.5, 4.42, floor + 2.05))
    mb.socket("ship_berth", (bx, by, bz))
    _combat_slots(mb, floor, spread=4.0)
    mb.socket("camera_look_at", (0, 0.5, floor + 1.6))


def dreadnought_deck(mb, hq):
    """Act IV upper-deck brawl on the Sovereign Gale. Wider than other arenas for the full crew,
    gilded by the Armada refit. Enamel plank highlights read as rain-slicked under stormlight."""
    half_l, half_w, floor = 10.0, 5.0, 0.6
    _planks(mb, half_l, half_w, floor, _q(hq, 12, 4), hq, swatches=("wood_dark", "navy", "wood_dark", "storm_dark"))
    mb.box((0, 0, floor / 2 - 0.05), (2 * half_l, 2 * half_w, floor - 0.1), "wood_dark")
    mb.box((0, 0, -0.8), (2 * half_l, 2 * half_w, 1.4), "wood_dark")
    _bulwark(mb, half_l, half_w, floor, wall="navy", cap="gold_dark", wall_h=1.25)
    if hq:
        # Wet streaks: long lightning-coloured glints running with the planks.
        rng = random.Random(3)
        for i in range(7):
            x, y = rng.uniform(-8, 8), rng.uniform(-3.9, 2.6)
            mb.box((x, y, floor + 0.004), (rng.uniform(1.2, 3.6), 0.05, 0.012), "storm")
    # Huge mainmast base and a broken sail.
    mast_y = 3.6
    mb.tube((0, mast_y, floor), (0, mast_y, 14.0), 0.55, 0.32, sides=_q(hq, 10, 4), color="wood_mid", smooth=hq)
    with mb.xf(Matrix.Translation((0, mast_y, floor))):
        mb.lathe([(1.1, 0.0), (1.1, 0.4), (0.68, 0.5)], _q(hq, 10, 5), "gold_dark", smooth=False)
    mb.tube((-7.0, mast_y - 0.3, 9.5), (7.0, mast_y - 0.3, 9.5), 0.14, sides=_q(hq, 4, 3), color="wood_dark")
    mb.plate([(-6.7, mast_y - 0.4, 9.4), (6.7, mast_y - 0.4, 9.4), (5.5, mast_y - 0.9, 5.0), (2.6, mast_y - 0.9, 6.2), (0.8, mast_y - 0.9, 4.7), (-2.1, mast_y - 0.9, 6.0), (-5.5, mast_y - 0.9, 5.0)], 0.06, "faction_a")
    # Cannon row and a pair of armada standards along the rear rail.
    ports = _q(hq, 6, 2)
    for i in range(ports):
        x = -9 + (i + 0.5) * 18 / ports
        if abs(x) < 1.5:
            continue
        mb.tube((x, 4.72, floor + 0.65), (x, 3.76, floor + 0.65), 0.13, 0.1, sides=_q(hq, 6, 3), color="iron")
        if hq:
            mb.box((x, 4.2, floor + 0.2), (0.5, 0.95, 0.3), "navy")
    for sign in (1, -1):
        mb.tube((sign * 3.6, 4.6, floor + 1.25), (sign * 3.6, 4.6, floor + 5.2), 0.05, sides=_q(hq, 5, 3), color="gold")
        mb.plate([(sign * 3.2, 4.58, floor + 5.0), (sign * 4.0, 4.58, floor + 5.0), (sign * 4.0, 4.58, floor + 2.9), (sign * 3.6, 4.58, floor + 2.5), (sign * 3.2, 4.58, floor + 2.9)], 0.02, "faction_c")
    # Hatch to the Lift-Core chamber, leaking its glow up on deck.
    mb.box((0, 1.4, floor + 0.05), (2.5, 1.8, 0.1), "iron")
    mb.box((0, 1.4, floor + 0.105), (1.8, 1.1, 0.03), "liftstone")
    if hq:
        for i in range(4):
            mb.box((-0.66 + i * 0.44, 1.4, floor + 0.14), (0.16, 1.2, 0.05), "iron")
    _combat_slots(mb, floor, spread=4.6)
    mb.socket("hatch", (0, 1.4, floor + 0.1))
    for i, x in enumerate((-7, 7)):
        mb.socket(f"lightning_strike_{i}", (x, 0.6, floor))


def gun_deck(mb, hq):
    """Below-deck combat, Act III. Low ceiling, cannons along both sides, lit only by port light.
    Vertical slab walls: the camera sits outside the -Y wall, which is left out."""
    half_l, half_w, floor, ceil = 9.0, 3.6, 0.5, 3.1
    _planks(mb, half_l, half_w, floor, _q(hq, 8, 4), hq, swatches=("wood_mid", "wood_dark", "wood_mid", "wood_dark"))
    mb.box((0, 0, 0.0), (2 * half_l, 2 * half_w, 0.8), "wood_dark")
    # Back wall and ceiling, thick enough to look like hull.
    mb.box((0, half_w + 0.2, (floor + ceil) / 2), (2 * half_l, 0.4, ceil - floor + 0.4), "wood_dark")
    mb.box((0, 0, ceil + 0.15), (2 * half_l, 2 * half_w + 0.8, 0.3), "wood_dark")
    for sign in (1, -1):
        mb.box((sign * (half_l + 0.2), 0, (floor + ceil) / 2), (0.4, 2 * half_w, ceil - floor + 0.4), "wood_mid")
    # Ceiling beams give the low-ceiling rhythm.
    for i in range(_q(hq, 7, 3)):
        x = -half_l + (i + 0.5) * 2 * half_l / _q(hq, 7, 3)
        mb.box((x, 0, ceil - 0.1), (0.32, 2 * half_w, 0.28), "wood_mid")
    # Gun ports along the back wall: daylight pours in.
    guns = _q(hq, 5, 3)
    for i in range(guns):
        x = -half_l + (i + 0.5) * 2 * half_l / guns
        mb.box((x, half_w + 0.02, floor + 1.15), (0.95, 0.06, 0.8), "wind")
        mb.tube((x, half_w - 0.05, floor + 0.85), (x, half_w - 1.9, floor + 0.82), 0.15, 0.12, sides=_q(hq, 8, 4), color="iron")
        mb.box((x, half_w - 1.1, floor + 0.28), (0.8, 1.6, 0.4), "wood_mid")
        if hq:
            with mb.xf(Matrix.Translation((x + 0.5, half_w - 1.5, floor))):
                mb.lathe([(0.17, 0.0), (0.2, 0.24), (0.17, 0.48)], 6, "wood_light", smooth=False)
    # Hanging lanterns (the hub's prop works too; these are cheap bakes).
    if hq:
        for x in (-6.0, 0.0, 6.0):
            mb.tube((x, -0.4, ceil - 0.25), (x, -0.4, ceil - 0.8), 0.015, sides=3, color="iron")
            mb.sphere((x, -0.4, ceil - 0.95), 0.15, 6, 3, "lamp", smooth=False)
        for x in (-8.45, -7.75):
            mb.box((x, -2.3, floor + 0.4), (0.6, 0.8, 0.8), "wood_light")
    _combat_slots(mb, floor, spread=3.8, depth_step=0.8)
    mb.socket("ladder_up", (0, 3.0, floor))
    mb.socket("floor_breach", (2.6, -1.4, floor))


def cell_block(mb, hq):
    """The high-security brig of Tartarus Aloft. Barred cells line the back wall, cold light above,
    and the far +X door opens straight into SM_Env_WarRoom for the twist."""
    half_l, half_w, floor, ceil = 9.0, 3.6, 0.5, 3.6
    rows = _q(hq, 6, 3)
    pw = 2 * half_w / rows
    for r in range(rows):
        mb.box((0, -half_w + (r + 0.5) * pw, floor - 0.05), (2 * half_l - 0.02, pw - 0.03, 0.1), ("steel", "iron")[r % 2])
    mb.box((0, 0, 0.0), (2 * half_l, 2 * half_w, 0.8), "iron")
    mb.box((0, half_w + 1.6, (floor + ceil) / 2), (2 * half_l, 0.4, ceil - floor + 0.4), "steel")
    mb.box((0, 0.8, ceil + 0.15), (2 * half_l, 2 * half_w + 3.2, 0.3), "iron")
    # Cell floor extends behind the bars.
    mb.box((0, half_w + 0.75, floor - 0.2), (2 * half_l, 1.5, 0.4), "iron")
    cells = _q(hq, 5, 3)
    cell_w = 2 * half_l / cells
    for i in range(cells):
        x = -half_l + (i + 0.5) * cell_w
        mb.box((x - cell_w / 2 + 0.11, half_w + 0.75, (floor + ceil) / 2), (0.22, 1.5, ceil - floor), "steel")
        # Bars.
        for b in range(_q(hq, 6, 3)):
            bx = x - cell_w * 0.36 + b * (cell_w * 0.72 / max(1, _q(hq, 6, 3) - 1))
            mb.tube((bx, half_w, floor), (bx, half_w, ceil), 0.028, sides=_q(hq, 4, 3), color="iron_light")
        # A bunk, a dark corner and one lit slit far back in each cell.
        if hq:
            mb.box((x + 0.3, half_w + 1.05, floor + 0.28), (1.7, 0.7, 0.14), "canvas_dark")
            mb.box((x, half_w + 1.38, ceil - 0.9), (0.5, 0.06, 0.18), "wind")
    # One continuous rail top and bottom: per-cell rails would meet in flush faces the gate welds away.
    mb.box((0, half_w, ceil - 0.15), (2 * half_l, 0.14, 0.3), "iron")
    mb.box((0, half_w, floor + 0.08), (2 * half_l, 0.14, 0.16), "iron")
    # Overhead strip lights, the cold light of the Armada.
    for i in range(_q(hq, 4, 2)):
        x = -half_l + (i + 0.5) * 2 * half_l / _q(hq, 4, 2)
        mb.box((x, 0.0, ceil - 0.03), (2.2, 0.32, 0.08), "wind")
    # Bulkhead doors on both ends.
    for sign, color in ((1, "gold"), (-1, "iron_light")):
        x = sign * (half_l + 0.2)
        mb.box((x, 0, (floor + ceil) / 2), (0.4, 2 * half_w, ceil - floor + 0.4), "steel")
        mb.box((x - sign * 0.22, 0.4, floor + 1.15), (0.06, 1.7, 2.3), color)
        if hq:
            with mb.xf(Matrix.Translation((x - sign * 0.26, 0.4, floor + 1.15)) @ Matrix.Rotation(math.pi / 2, 4, "Y")):
                mb.lathe([(0.3, -0.03), (0.3, 0.03)], 8, "iron", smooth=False)
    _combat_slots(mb, floor, spread=3.8, depth_step=0.8)
    mb.socket("door_to_war_room", (9.0, 0.4, floor))
    mb.socket("door_in", (-9.0, 0.4, floor))
    for i in range(cells):
        mb.socket(f"cell_{i}", (-half_l + (i + 0.5) * cell_w, half_w + 0.8, floor))


def war_room(mb, hq):
    """The Act III twist in one set: you expected a dungeon, and it's velvet and gold, with
    Cassian's chart table and an open stern gallery. Should feel wrong next to SM_Env_CellBlock."""
    half_l, half_w, floor, ceil = 8.0, 4.2, 0.5, 4.2
    rows = _q(hq, 8, 3)
    pw = 2 * half_w / rows
    for r in range(rows):
        mb.box((0, -half_w + (r + 0.5) * pw, floor - 0.05), (2 * half_l - 0.02, pw - 0.03, 0.1), ("wood_red", "wood_mid")[r % 2])
    mb.box((0, 0, 0.0), (2 * half_l, 2 * half_w, 0.8), "wood_dark")
    # Velvet carpet down the centre, gold border: a royal runner into the fight.
    mb.box((0, 0, floor + 0.012), (2 * half_l - 2.0, 2.6, 0.022), "velvet")
    for sign in (1, -1):
        mb.box((0, sign * 1.32, floor + 0.014), (2 * half_l - 2.0, 0.09, 0.026), "gold")
    # Back wall with a great stern gallery looking out on the fleet.
    mb.box((0, half_w + 0.2, floor + 0.65), (2 * half_l, 0.4, 1.3), "wood_dark")
    mb.box((0, half_w + 0.2, ceil - 0.5), (2 * half_l, 0.4, 1.0), "wood_dark")
    panes = _q(hq, 7, 3)
    for i in range(panes):
        x = -half_l + (i + 0.5) * 2 * half_l / panes
        mb.box((x, half_w + 0.28, floor + 1.95), (2 * half_l / panes - 0.26, 0.05, ceil - floor - 2.3), "lamp")
        mb.box((x + half_l / panes, half_w + 0.2, floor + 1.95), (0.24, 0.3, ceil - floor - 2.3), "gold_dark")
    mb.box((0, 0.2, ceil + 0.2), (2 * half_l, 2 * half_w + 0.8, 0.4), "faction_a")
    if hq:
        for i in range(5):
            x = -half_l + (i + 0.5) * 2 * half_l / 5
            mb.box((x, 0, ceil - 0.06), (0.26, 2 * half_w, 0.2), "gold_dark")
    for sign in (1, -1):
        mb.box((sign * (half_l + 0.2), 0, (floor + ceil) / 2), (0.4, 2 * half_w + 0.4, ceil - floor + 0.4), "velvet")
    # Chart table, chairs, and the map: Cassian's plan for the fleet, in plain sight.
    tx, ty = 0.0, 2.3
    mb.box((tx, ty, floor + 0.95), (3.6, 1.4, 0.12), "wood_red")
    mb.box((tx, ty, floor + 1.02), (3.2, 1.1, 0.016), "parchment")
    for sx in (1, -1):
        mb.box((tx + sx * 1.5, ty, floor + 0.45), (0.2, 1.1, 0.9), "gold_dark")
    if hq:
        for i, (ox, oy) in enumerate(((-1.0, 0.2), (0.2, -0.2), (0.9, 0.3))):
            mb.box((tx + ox, ty + oy, floor + 1.07), (0.3, 0.14, 0.05), ("gem_blue", "gem_red", "gold")[i])
        with mb.xf(Matrix.Translation((tx + 1.3, ty - 0.4, floor + 1.03))):
            mb.lathe([(0.08, 0.0), (0.05, 0.14), (0.08, 0.26)], 6, "gold", smooth=False)
        # Fat wine racks and a chandelier: luxury props the player must fight around.
        mb.box((-7.0, 3.3, floor + 1.1), (1.4, 0.7, 2.2), "wood_red")
        with mb.xf(Matrix.Translation((0, 0, ceil - 1.1))):
            mb.lathe([(1.0, 0.0), (1.0, 0.06), (0.2, 0.2)], 10, "gold", smooth=False)
        mb.tube((0, 0, ceil - 0.9), (0, 0, ceil), 0.03, sides=3, color="gold")
        for i in range(6):
            a = 2 * math.pi * i / 6
            mb.sphere((0.95 * math.cos(a), 0.95 * math.sin(a), ceil - 1.0), 0.08, 5, 3, "lamp", smooth=False)
    # Cassian's chair and a banner on either end: this is his room, not his cell.
    mb.box((0, 3.5, floor + 0.3), (1.0, 0.8, 0.6), "velvet")
    mb.box((0, 3.85, floor + 1.15), (1.1, 0.2, 1.7), "velvet")
    mb.box((0, 3.85, floor + 2.04), (1.2, 0.26, 0.12), "gold")
    for sign in (1, -1):
        mb.plate([(sign * 5.5, 4.1, ceil - 0.1), (sign * 6.9, 4.1, ceil - 0.1), (sign * 6.9, 4.1, floor + 1.4), (sign * 6.2, 4.1, floor + 0.9), (sign * 5.5, 4.1, floor + 1.4)], 0.03, "faction_c")
    _combat_slots(mb, floor, spread=3.8, depth_step=0.8)
    mb.socket("cassian_mark", (0, 3.0, floor))
    mb.socket("door_in", (-8.0, 0.0, floor))
    mb.socket("gallery_escape", (5.0, 4.0, floor))


def lift_core_chamber(mb, hq):
    """The final duel, inside the Sovereign Gale's failing gravity engine. A vast glowing core,
    a ring walkway, and broken gantries: the arena itself says the ship is coming apart."""
    floor = 1.0
    r_out, r_in = 10.0, 4.4
    sides = _q(hq, 20, 10)
    # Fighting ring. Flat lathe: its top is the duel floor.
    mb.lathe([(r_in, floor - 0.9), (r_in, floor), (r_out, floor), (r_out, floor - 0.9)], sides, lambda i, _j: "iron" if i == 0 else ("steel" if i == 1 else "iron"), smooth=False, caps=(False, False))
    mb.lathe([(r_in, floor - 0.9), (r_out, floor - 0.9)], sides, "iron", smooth=False, caps=(False, False))
    if hq:
        with mb.xf(Matrix.Translation((0, 0, floor + 0.008))):
            mb.lathe([(r_in + 0.1, 0.0), (r_in + 0.1, 0.02), (r_in + 0.38, 0.02), (r_in + 0.38, 0.0)], sides, "liftstone", smooth=False, caps=(False, False))
    # The Lift-Core: an immense crystal column, running through the whole room.
    with mb.xf(Matrix.Translation((0, 0, floor - 1.6))):
        mb.lathe([(1.2, 0.0), (2.5, 2.0), (2.9, 5.0), (2.5, 8.0), (1.1, 11.0)], _q(hq, 10, 6), lambda i, j: "lightning" if (i + j) % 5 == 0 else "liftstone", smooth=False, phase=0.3)
    # Containment rings around the core: tilted, because gravity is failing.
    for k, (z, tilt, r) in enumerate(((floor + 0.9, 0.14, 3.6), (floor + 3.7, -0.2, 3.9), (floor + 6.2, 0.28, 3.4))):
        with mb.xf(Matrix.Translation((0, 0, z)) @ Matrix.Rotation(tilt, 4, "X") @ Matrix.Rotation(tilt * 0.6, 4, "Y")):
            mb.lathe([(r - 0.25, -0.16), (r - 0.25, 0.16), (r + 0.25, 0.16), (r + 0.25, -0.16)], _q(hq, 16, 8), "brass" if k % 2 == 0 else "iron_light", smooth=False, caps=(False, False))
    # Back wall segment, behind the duel, with ribs. Camera side stays open.
    wall = _q(hq, 10, 6)
    for i in range(wall):
        a = math.radians(20 + 140 * (i + 0.5) / wall)
        x, y = 11.2 * math.cos(a), 11.2 * math.sin(a)
        w = 2 * 11.2 * math.tan(math.radians(140 / wall / 2)) + 0.05
        with mb.xf(Matrix.Translation((x, y, floor + 4.0)) @ Matrix.Rotation(a - math.pi / 2, 4, "Z")):
            mb.box((0, 0, 0), (w, 1.0, 11.0), "iron" if i % 2 else "steel")
            if hq and i % 2 == 0:
                mb.box((0, -0.52, -1.0), (0.24, 0.1, 8.6), "liftstone_dark")
                mb.box((0, -0.54, 2.5), (w * 0.5, 0.06, 0.5), "ember")
    # Fallen gantry and a jagged rupture in the floor: the ship is dying.
    mb.path([(5.2, 4.3, floor + 5.5), (7.2, 3.8, floor + 3.3), (8.2, 2.1, floor + 0.2)], [0.25, 0.25, 0.25], _q(hq, 5, 3), "iron_light")
    mb.path([(-8.5, 2.2, floor + 6.6), (-6.2, 4.2, floor + 3.5), (-4.6, 3.4, floor + 0.3)], [0.2, 0.2, 0.2], _q(hq, 5, 3), "rust_dark")
    if hq:
        for x, y in ((6.7, -3.0), (7.8, -1.9), (7.0, -1.1)):
            mb.plate([(x - 0.5, y, floor), (x + 0.6, y + 0.2, floor), (x, y + 0.7, floor + 1.4)], 0.09, "iron_light")
        for k in range(3):
            a = 0.8 + k * 0.9
            mb.sphere((7.8 * math.cos(a), 7.8 * math.sin(a), floor + 0.1), (0.5, 0.5, 0.06), 6, 2, "ember", smooth=False)
    _combat_slots(mb, floor, spread=6.3, depth_step=0.6)
    for i in range(3):
        mb.socket(f"gravity_flip_{i}", (6.5 * math.cos(i * 2.1), 6.5 * math.sin(i * 2.1), floor))
    mb.socket("core", (0, 0, floor + 3.4))
    mb.socket("rupture_0", (7.8 * math.cos(0.8), 7.8 * math.sin(0.8), floor))
