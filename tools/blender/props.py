"""Props and environment pieces. Each function fills a MeshBuilder at HQ or LQ detail."""
import math
import random

from mathutils import Matrix


def _rotate_y_axis():
    """Maps a local Z-axis lathe onto world Y."""
    return Matrix.Rotation(math.pi / 2, 4, "X")


def propeller(mb, hq):
    """Spins around the 'hub' socket's Y axis; see the manifest."""
    blades = 4 if hq else 3
    radius = 1.0
    width = 0.2
    with mb.xf(Matrix.Translation((0, 0, radius))):
        mb.socket("hub", (0, 0, 0))
        with mb.xf(_rotate_y_axis()):
            if hq:
                mb.lathe([(0.03, -0.12), (0.12, -0.1), (0.15, 0.0), (0.15, 0.08)], 8, "brass")
            else:
                mb.lathe([(0.04, -0.1), (0.14, 0.08)], 5, "brass", smooth=False)
        for i in range(blades):
            with mb.xf(Matrix.Rotation(2 * math.pi * i / blades, 4, "Y")):
                if hq:
                    outline = [(0.1, 0, -width * 0.25), (0.55, 0.04, -width * 0.5), (radius * 0.95, 0.05, -width * 0.36), (radius, 0.05, 0.0), (radius * 0.9, -0.02, width * 0.3), (0.42, -0.04, width * 0.42), (0.1, 0, width * 0.25)]
                else:
                    outline = [(0.1, 0, -width * 0.3), (radius, 0.05, -width * 0.4), (radius, -0.02, width * 0.3), (0.1, 0, width * 0.3)]
                mb.plate(outline, 0.025, "wood_light")


def cannon(mb, hq):
    length = 1.5
    r = 0.13
    z = 0.42
    if hq:
        mb.path(
            [(0, 0.55, z), (0, 0.4, z), (0, -0.05, z), (0, -0.7, z), (0, -0.72, z), (0, -0.84, z)],
            [r * 0.55, r * 1.3, r * 1.15, r * 0.85, r * 1.1, r * 1.1],
            10,
            "iron",
            smooth=True,
        )
        mb.sphere((0, 0.6, z), r * 0.45, 6, 3, "iron")
        mb.box((0, 0.1, 0.2), (0.44, 0.95, 0.15), "wood_mid")
        mb.box((0, 0.3, 0.32), (0.44, 0.5, 0.14), "wood_mid")
        for x in (0.25, -0.25):
            for y in (-0.22, 0.42):
                with mb.xf(Matrix.Translation((x, y, 0.13)) @ Matrix.Rotation(math.pi / 2, 4, "Y")):
                    mb.lathe([(0.13, -0.04), (0.13, 0.04)], 10, "wood_dark", smooth=False)
        mb.box((0, 0, 0.35), (0.48, 0.05, 0.1), "iron_light")
    else:
        mb.tube((0, 0.5, z), (0, -length + 0.65, z), r * 1.1, r * 0.95, sides=6, color="iron")
        mb.box((0, 0.1, 0.17), (0.5, 1.0, 0.3), "wood_mid")
    mb.socket("muzzle", (0, -0.84 if hq else -length + 0.65, z))


def cannonball(mb, hq):
    mb.sphere((0, 0, 0.14), 0.14, 10 if hq else 6, 6 if hq else 4, "iron", smooth=True)


def grappling_hook(mb, hq):
    """Fired between ships to start a boarding. The rope attaches at the 'rope' socket."""
    prongs = 4 if hq else 3
    shaft_top = 0.72
    mb.tube((0, 0, 0.1), (0, 0, shaft_top), 0.035, sides=6 if hq else 4, color="iron_light")
    with mb.xf(Matrix.Translation((0, 0, shaft_top + 0.02)) @ Matrix.Rotation(math.pi / 2, 4, "X")):
        mb.lathe([(0.05, -0.015), (0.05, 0.015)], 6 if hq else 4, "iron", smooth=False)
    mb.socket("rope", (0, 0, shaft_top + 0.06))
    for i in range(prongs):
        with mb.xf(Matrix.Rotation(2 * math.pi * i / prongs, 4, "Z")):
            if hq:
                mb.path(
                    [(0, 0, 0.14), (0.14, 0, 0.03), (0.27, 0, 0.1), (0.3, 0, 0.3)],
                    [0.032, 0.03, 0.022, 0.006],
                    5,
                    "iron_light",
                )
            else:
                mb.path([(0, 0, 0.14), (0.24, 0, 0.04), (0.3, 0, 0.28)], [0.035, 0.03, 0.008], 3, "iron_light")


def _chest_body(mb, hq):
    w, d, h = 0.9, 0.56, 0.38
    mb.box((0, 0, h / 2), (w, d, h), "wood_mid")
    if hq:
        for z in (0.09, 0.27):
            mb.box((0, -d / 2 + 0.005, z), (w * 0.98, 0.015, 0.012), "wood_dark")
        for x in (-w / 2 + 0.05, w / 2 - 0.05):
            mb.box((x, 0, h / 2), (0.07, d + 0.03, h + 0.02), "iron_light")
    else:
        mb.box((0, 0, h / 2), (w * 0.14, d + 0.02, h + 0.01), "iron_light")
    return w, d, h


def _chest_lid(mb, w, d, hq):
    sides = 8 if hq else 4
    rings = []
    for x in (-w / 2, w / 2):
        ring = []
        for j in range(sides + 1):
            a = math.pi * j / sides
            ring.append((x, d / 2 * math.cos(a), d * 0.42 * math.sin(a)))
        rings.append(ring)
    mb.loft(rings, "wood_red", smooth=False)
    if hq:
        for x in (-w / 2 + 0.05, w / 2 - 0.05):
            band = []
            for dx in (x - 0.04, x + 0.04):
                ring = []
                for j in range(sides + 1):
                    a = math.pi * j / sides
                    ring.append((dx, d * 0.52 * math.cos(a), d * 0.44 * math.sin(a)))
                band.append(ring)
            mb.loft(band, "iron_light", smooth=False)


def treasure_chest(mb, hq):
    w, d, h = _chest_body(mb, hq)
    # Sits just inside the body: flush faces would be welded away by the gate.
    with mb.xf(Matrix.Translation((0, 0, h - 0.002))):
        _chest_lid(mb, w, d, hq)
    mb.box((0, -d / 2 - 0.01, h - 0.02), (0.11, 0.05, 0.15), "gold")


def treasure_chest_open(mb, hq):
    w, d, h = _chest_body(mb, hq)
    mb.box((0, 0, h + 0.002), (w * 0.9, d * 0.86, 0.05), "gold")
    if hq:
        rng = random.Random(4)
        for _ in range(14):
            x, y = rng.uniform(-w * 0.38, w * 0.38), rng.uniform(-d * 0.34, d * 0.34)
            with mb.xf(Matrix.Translation((x, y, h + 0.03))):
                mb.lathe([(0.05, 0.0), (0.05, 0.016)], 6, "gold", smooth=False)
        mb.sphere((0.14, -0.02, h + 0.065), 0.05, 6, 3, "gem_red", smooth=False)
        mb.sphere((-0.18, 0.06, h + 0.065), 0.045, 6, 3, "gem_blue", smooth=False)
    with mb.xf(Matrix.Translation((0, d / 2, h)) @ Matrix.Rotation(math.radians(-105), 4, "X") @ Matrix.Translation((0, -d / 2, 0))):
        _chest_lid(mb, w, d, hq)


def gold_pile(mb, hq):
    rng = random.Random(9)
    sides = 12 if hq else 6
    mb.lathe([(0.42, 0.0), (0.34, 0.1), (0.2, 0.2), (0.07, 0.26)] if hq else [(0.42, 0.0), (0.2, 0.17), (0.06, 0.26)], sides, "gold", smooth=False)
    if hq:
        for _ in range(26):
            a = rng.uniform(0, 2 * math.pi)
            r = rng.uniform(0.1, 0.46)
            z = max(0.012, 0.28 * (1 - r / 0.46)) + 0.005
            tilt = Matrix.Rotation(rng.uniform(-0.5, 0.5), 4, "X") @ Matrix.Rotation(rng.uniform(-0.5, 0.5), 4, "Y")
            with mb.xf(Matrix.Translation((r * math.cos(a), r * math.sin(a), z)) @ tilt):
                mb.lathe([(0.042, -0.006), (0.042, 0.006)], 6, "gold", smooth=False)
        mb.sphere((0.1, -0.2, 0.14), 0.045, 6, 3, "gem_red", smooth=False)


def barrel(mb, hq):
    h = 0.9
    sides = 12 if hq else 6
    profile = [(0.25, 0), (0.31, h * 0.25), (0.335, h * 0.5), (0.31, h * 0.75), (0.25, h)] if hq else [(0.25, 0), (0.33, h / 2), (0.25, h)]
    mb.lathe(profile, sides, lambda _i, j: "wood_mid" if j % 2 else "wood_light", smooth=False)
    for z, r in ((h * 0.17, 0.298), (h * 0.83, 0.298)) if hq else ():
        mb.lathe([(r, z - 0.03), (r, z + 0.03)], sides, "iron", smooth=False, caps=(False, False))


def crate(mb, hq):
    s = 0.8
    mb.box((0, 0, s / 2), (s, s, s), "wood_light")
    if not hq:
        return
    t = 0.07
    for dx in (-1, 1):
        for dy in (-1, 1):
            mb.box((dx * (s / 2 - t / 2 + 0.01), dy * (s / 2 - t / 2 + 0.01), s / 2), (t, t, s + 0.01), "wood_mid")
    for z in (t / 2, s - t / 2):
        for dy in (-1, 1):
            mb.box((0, dy * (s / 2 - t / 2 + 0.012), z), (s, t, t), "wood_mid")
        for dx in (-1, 1):
            mb.box((dx * (s / 2 - t / 2 + 0.012), 0, z), (t, s, t), "wood_mid")


def cutlass(mb, hq):
    """Stands on the pommel. Its outer edge faces -X, the downward side on the weapon.R bone."""
    if hq:
        mb.sphere((0, 0, 0.025), 0.028, 6, 3, "brass")
        mb.tube((0, 0, 0.04), (0, 0, 0.17), 0.018, 0.02, sides=6, color="leather_dark")
        mb.box((0, 0, 0.18), (0.14, 0.03, 0.022), "brass")
        outline = [(-0.024, 0, 0.19), (0.024, 0, 0.19), (0.05, 0, 0.5), (0.09, 0, 0.74), (0.11, 0, 0.87), (0.075, 0, 0.87), (0.012, 0, 0.72), (-0.024, 0, 0.45)]
        mb.plate(outline, 0.008, "silver")
        mb.path([(0.07, 0, 0.18), (0.11, 0, 0.1), (0.05, 0, 0.04)], [0.009, 0.009, 0.009], 4, "brass")
    else:
        mb.tube((0, 0, 0), (0, 0, 0.17), 0.022, sides=4, color="leather_dark")
        mb.box((0, 0, 0.18), (0.14, 0.03, 0.025), "brass")
        mb.plate([(-0.025, 0, 0.19), (0.025, 0, 0.19), (0.11, 0, 0.87), (0.05, 0, 0.84)], 0.012, "silver")
    mb.socket("grip", (0, 0, 0.1))
    mb.socket("trail_tip", (0.1, 0, 0.87))


def flintlock(mb, hq):
    """Muzzle towards +Z and top towards +X, so it aims along the arm on the gun.R bone."""
    upright = Matrix(((0, 0, 1, 0), (-1, 0, 0, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
    with mb.xf(upright):
        z = 0.21
        sides = 8 if hq else 4
        mb.tube((0, 0.1, z), (0, -0.28, z), 0.018, 0.02, sides=sides, color="iron")
        if hq:
            mb.path([(0, -0.27, z), (0, -0.29, z), (0, -0.3, z)], [0.024, 0.024, 0.024], 8, "brass")
            mb.box((0.024, 0.06, z + 0.012), (0.012, 0.09, 0.032), "iron_light")
            mb.tube((0.024, 0.085, z + 0.02), (0.024, 0.05, z + 0.06), 0.006, sides=3, color="iron_light")
        mb.path([(0, 0.08, z - 0.018), (0, 0.13, z - 0.06), (0, 0.17, z - 0.17), (0, 0.17, z - 0.2)], [0.02, 0.024, 0.03, 0.03], sides, "wood_red")
        mb.socket("grip", (0, 0.15, z - 0.12))
        mb.socket("muzzle", (0, -0.3, z))


def boarding_axe(mb, hq):
    """Blade faces -X, which is the downward side when carried on the weapon.R bone."""
    with mb.xf(Matrix.Rotation(math.pi, 4, "Z")):
        sides = 6 if hq else 4
        h = 0.92
        mb.tube((0, 0, 0), (0, 0, h), 0.022, 0.018, sides=sides, color="wood_mid")
        if hq:
            mb.plate([(0.02, 0, h - 0.04), (0.14, 0, h - 0.02), (0.22, 0, h + 0.05), (0.22, 0, h - 0.24), (0.14, 0, h - 0.2), (0.02, 0, h - 0.18)], 0.024, "iron_light")
            mb.plate([(-0.02, 0, h - 0.06), (-0.16, 0, h - 0.11), (-0.02, 0, h - 0.17)], 0.02, "iron")
            mb.tube((0, 0, 0.05), (0, 0, 0.22), 0.026, sides=sides, color="leather_dark")
        else:
            mb.plate([(0.02, 0, h - 0.02), (0.22, 0, h + 0.03), (0.22, 0, h - 0.24), (0.02, 0, h - 0.18)], 0.03, "iron_light")
        mb.socket("grip", (0, 0, 0.14))
        mb.socket("trail_tip", (0.22, 0, h - 0.1))


def rum_bottle(mb, hq):
    """Consumable item used in turn-based combat."""
    sides = 10 if hq else 6
    profile = [(0.075, 0), (0.08, 0.02), (0.08, 0.18), (0.03, 0.26), (0.028, 0.34)] if hq else [(0.08, 0), (0.08, 0.18), (0.028, 0.34)]
    mb.lathe(profile, sides, "glass", smooth=hq)
    mb.tube((0, 0, 0.33), (0, 0, 0.37), 0.024, sides=sides if hq else 4, color="wood_light")
    if hq:
        mb.lathe([(0.0815, 0.06), (0.0815, 0.14)], sides, "canvas", smooth=True, caps=(False, False))


# ---- environment ----------------------------------------------------------------------

DECK_LENGTH = 16.0  # Along X, side-on to the combat camera.
DECK_WIDTH = 8.0
DECK_TOP = 0.6


def boarding_deck(mb, hq):
    """Turn-based arena: the deck of the defeated ship, with sockets for each combatant."""
    rows = 10 if hq else 4
    half_l, half_w = DECK_LENGTH / 2, DECK_WIDTH / 2
    pw = DECK_WIDTH / rows
    # Long planks run along the ship, with staggered butt joints on HQ.
    for r in range(rows):
        y = -half_w + (r + 0.5) * pw
        swatch = ("wood_deck", "wood_light", "wood_deck", "wood_mid")[r % 4] if hq else ("wood_deck" if r % 2 else "wood_light")
        joints = [-half_l, half_l] if not hq else [-half_l, -half_l + DECK_LENGTH * (0.3 + 0.4 * ((r * 0.618) % 1.0)), half_l]
        for x0, x1 in zip(joints, joints[1:]):
            mb.box(((x0 + x1) / 2, y, DECK_TOP - 0.05), (x1 - x0 - 0.02, pw - 0.025, 0.1), swatch)
    mb.box((0, 0, DECK_TOP / 2 - 0.05), (DECK_LENGTH, DECK_WIDTH, DECK_TOP - 0.1), "wood_dark")

    # Solid bulwark behind and beside the fight; the camera side (-Y) stays open.
    wall_h = 1.05
    wall_t = 0.22
    back_y = half_w - wall_t / 2
    wall_z = DECK_TOP + wall_h / 2
    mb.box((0, back_y, wall_z), (DECK_LENGTH, wall_t, wall_h), "wood_mid")
    mb.box((0, back_y, DECK_TOP + wall_h + 0.05), (DECK_LENGTH + 0.2, wall_t + 0.14, 0.12), "faction_a")
    for side in (-1, 1):
        x = side * (half_l - wall_t / 2)
        mb.box((x, 0, wall_z), (wall_t, DECK_WIDTH, wall_h), "wood_mid")
        mb.box((x, 0, DECK_TOP + wall_h + 0.05), (wall_t + 0.14, DECK_WIDTH + 0.2, 0.12), "faction_a")
    # Hull flare below the deck, so the arena reads as a ship and not a floating slab.
    # Sinks 1 cm into the deck block: flush faces would be welded away by the gate.
    mb.box((0, 0, -0.69), (DECK_LENGTH, DECK_WIDTH, 1.4), "wood_dark", top_scale=1.0)
    if hq:
        ports = 6
        for i in range(ports):
            x = -half_l + (i + 0.5) * DECK_LENGTH / ports
            mb.box((x, back_y - 0.12, DECK_TOP + 0.55), (0.55, 0.05, 0.5), "wood_dark")
            mb.tube((x, back_y - 0.1, DECK_TOP + 0.55), (x, back_y - 0.95, DECK_TOP + 0.55), 0.11, 0.09, sides=6, color="iron")
            mb.box((x, back_y - 0.5, DECK_TOP + 0.13), (0.44, 0.75, 0.24), "wood_mid")

    # Centre mast sets the back of the arena.
    mast_y = half_w - 1.0
    mb.tube((0, mast_y, DECK_TOP), (0, mast_y, 9.0), 0.28, 0.16, sides=8 if hq else 4, color="wood_mid", smooth=hq)
    mb.tube((-3.8, mast_y - 0.2, 6.2), (3.8, mast_y - 0.2, 6.2), 0.09, sides=4 if hq else 3, color="wood_dark")
    mb.plate([(-3.6, mast_y - 0.25, 6.1), (3.6, mast_y - 0.25, 6.1), (3.1, mast_y - 0.7, 2.7), (-3.1, mast_y - 0.7, 2.7)], 0.06, "canvas")
    mb.plate([(0, mast_y, 9.0), (1.6, mast_y, 8.65), (0, mast_y, 8.3)], 0.04, "faction_a")

    # Scenery blocks clear the combat lanes at y ~ -1.5..1.5.
    def dressing_barrel(x, y, hq_sides):
        with mb.xf(Matrix.Translation((x, y, DECK_TOP))):
            mb.lathe([(0.25, 0), (0.33, 0.45), (0.25, 0.9)], hq_sides, "wood_mid", smooth=False)

    if hq:
        for x, y in ((-7.0, 0.9), (-7.2, 0.1), (7.0, 0.6)):
            dressing_barrel(x, y, 8)
        for x, y, s in ((7.0, -0.5, 0.8), (7.0, -0.5, 0.45), (-7.1, -1.1, 0.8)):
            z = DECK_TOP + s / 2 + (0.8 if s == 0.45 else 0)
            mb.box((x, y, z), (s, s, s), "wood_light")
        # Hatch grate in the middle of the deck, clear of every combat slot's feet.
        for i in range(4):
            mb.box((-0.36 + i * 0.24, 1.3, DECK_TOP + 0.01), (0.14, 1.2, 0.03), "iron")
    else:
        dressing_barrel(-7.1, 0.5, 5)
        mb.box((7.0, -0.2, DECK_TOP + 0.4), (0.8, 0.8, 0.8), "wood_light")

    for i in range(4):
        depth = -1.6 + i * 1.05
        offset = 1.0 if i % 2 else 0.0
        mb.socket(f"party_slot_{i + 1}", (-4.4 - offset, depth, DECK_TOP))
        mb.socket(f"enemy_slot_{i + 1}", (4.4 + offset, depth, DECK_TOP))
    mb.socket("centre_stage", (0, 0, DECK_TOP))
    mb.socket("camera_look_at", (0, 0, DECK_TOP + 1.1))


def sky_island(mb, hq):
    """Floating rock landmark for dogfights. Reads from far, so most of the budget is silhouette."""
    rng = random.Random(21)
    sides = 16 if hq else 8
    # (radius, height, jitter), from the underside tip up to the top rim.
    rows = [(0.5, 0, 0.1), (3, 3.2, 0.5), (5.5, 6.2, 0.6), (8, 8.6, 0.5), (9.5, 10.6, 0.3)] if hq else [(1, 0, 0), (6, 5, 0.6), (9.5, 10.6, 0.3)]
    rings = []
    for radius, z, jitter in rows:
        ring = []
        for j in range(sides):
            a = 2 * math.pi * j / sides
            r = radius * (1 + rng.uniform(-0.18, 0.18)) + rng.uniform(-jitter, jitter)
            ring.append((r * math.cos(a), r * math.sin(a), z + rng.uniform(-jitter, jitter)))
        rings.append(ring)
    mb.loft(rings, lambda i, _j: "rock_dark" if i < len(rows) // 2 else "rock", caps=(True, False), smooth=False)

    grass = []
    for scale, dz in ((1.02, -0.2), (0.82, 0.55), (0.3, 0.85)) if hq else ((1.02, -0.2), (0.45, 0.8)):
        ring = [(x * scale, y * scale, rows[-1][1] + dz) for x, y, _ in rings[-1]]
        grass.append(ring)
    mb.loft(grass, "grass", caps=(False, True), smooth=False)

    trees = 7 if hq else 2
    for i in range(trees):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(1.5, 6)
        x, y, z = r * math.cos(a), r * math.sin(a), rows[-1][1] + 0.4
        mb.tube((x, y, z - 0.2), (x, y, z + 1.0), 0.2, sides=4 if hq else 3, color="wood_dark")
        with mb.xf(Matrix.Translation((x, y, z + 1.0))):
            if hq:
                mb.lathe([(1.4, 0), (0.75, 1.4), (0.08, 2.8)], 6, "grass_dark", smooth=False)
            else:
                mb.lathe([(1.4, 0), (0.08, 2.8)], 4, "grass_dark", smooth=False)
    if hq:
        for i in range(3):
            mb.sphere((rng.uniform(-6, 6), rng.uniform(-6, 6), rows[-1][1] + 0.6), rng.uniform(0.6, 1.1), 6, 3, "rock", smooth=False)


def cloud(mb, hq):
    """Prefer alpha-free mesh clouds on low-end devices: they avoid transparent overdraw."""
    rng = random.Random(3)
    puffs = 9 if hq else 4
    for i in range(puffs):
        x = (i - (puffs - 1) / 2) * (10.0 / puffs)
        edge = 1 - abs(i - (puffs - 1) / 2) / (puffs / 2)
        r = 1.5 + 2.1 * edge + rng.uniform(-0.2, 0.2)
        y = rng.uniform(-1.3, 1.3)
        z = r * 0.72
        mb.sphere((x, y, z), (r * 1.1, r, r * 0.72), 10 if hq else 6, 6 if hq else 3, lambda ring, _j: "cloud_shade" if ring == 0 else "cloud", smooth=True)
