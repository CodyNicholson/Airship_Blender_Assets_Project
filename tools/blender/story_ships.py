"""Shattered Skies campaign ships. Every capturable ship gets its own silhouette.

Bow faces Blender -Y, like ships.py. All ships publish the same base sockets (propeller_*,
muzzle_*, boarding_L/R, deck_centre, smoke_vent, envelope_centre) plus their signature hardpoints.
Socket names are identical in HQ and LQ even where LQ drops the geometry, so gameplay never branches.
"""
import math

from mathutils import Matrix


def _q(hq, high, low):
    return high if hq else low


def _lerp(a, b, t):
    return a + (b - a) * t


def cosine_ts(count):
    return [0.5 - 0.5 * math.cos(math.pi * i / count) for i in range(count + 1)]


def shell(mb, stations, rows, paint, power=0.75, tumble=0.0):
    """Closed hull from (y, half_width, keel_z, deck_z) stations. paint(row) colours the sides."""
    rings = []
    for y, width, keel, deck in stations:
        side = []
        for j in range(rows + 1):
            phi = j / rows * math.pi / 2
            rise = 1 - math.cos(phi)
            x = width * math.sin(phi) ** power * (1 - tumble * rise * rise)
            side.append((x, y, keel + (deck - keel) * rise))
        rings.append(side + [(-x, yy, z) for x, yy, z in reversed(side[1:])])

    def colour(_i, j):
        if j == rows:
            return "wood_deck"
        return paint(j if j < rows else 2 * rows - j)

    mb.loft(rings, colour)


def gasbag(mb, x, y, z, length, radius, sides, rings, paint, flat=1.0, phase=None):
    """Teardrop lift envelope along Y with its nose at -Y. flat squashes it vertically."""
    half = length / 2
    profile = []
    for i in range(rings):
        s = 0.5 - 0.5 * math.cos(math.pi * (i + 0.5) / rings)
        profile.append((radius * max(0.08, math.sin(math.pi * s ** 0.85) ** 0.72), -half + length * s))
    place = Matrix.Translation((x, y, z)) @ Matrix.Rotation(-math.pi / 2, 4, "X") @ Matrix.Diagonal((1, flat, 1, 1))
    with mb.xf(place):
        mb.lathe(profile, sides, paint, smooth=True, phase=math.pi / sides if phase is None else phase)


def gasbag_band(mb, x, y, z, length, radius, s, sides, color, flat=1.0):
    half = length / 2
    r = radius * max(0.08, math.sin(math.pi * s ** 0.85) ** 0.72)
    at = -half + length * s
    place = Matrix.Translation((x, y, z)) @ Matrix.Rotation(-math.pi / 2, 4, "X") @ Matrix.Diagonal((1, flat, 1, 1))
    with mb.xf(place):
        mb.lathe([(r * 0.98, at - 0.14), (r * 1.03, at - 0.1), (r * 1.03, at + 0.1), (r * 0.98, at + 0.14)], sides, color, smooth=False, phase=math.pi / sides)


def striped(a, b, tip, rings):
    def paint(i, j):
        if i == 0 or i == rings - 1:
            return tip
        return a if j % 2 else b
    return paint


def sail(mb, y, z_top, z_bot, half, belly, hq, color="canvas", tatter=False):
    """Billowed square sail across X. Bellies towards -Y, the way the ship flies."""
    if not hq:
        mb.plate([(-half, y, z_top), (half, y, z_top), (half * 0.85, y - belly, z_bot), (-half * 0.85, y - belly, z_bot)], 0.05, color)
        return
    across = 6
    rows = 3
    rings = []
    for r in range(rows + 1):
        k = r / rows
        z = _lerp(z_top, z_bot, k)
        w = _lerp(half, half * 0.85, k)
        front, back = [], []
        for c in range(across + 1):
            u = c / across
            bulge = belly * math.sin(math.pi * u) * math.sin(math.pi * min(1.0, k * 1.1 + 0.15))
            drop = 0.0
            if tatter and r == rows:
                drop = (z_top - z_bot) * (0.28 if c % 2 else -0.08)
            front.append((-w + 2 * w * u, y - bulge, z + drop))
            back.append((-w + 2 * w * u, y - bulge + 0.04, z + drop))
        rings.append(front + list(reversed(back)))
    mb.loft(rings, color)


def mast(mb, x, y, z0, z1, r, hq, yards=()):
    mb.tube((x, y, z0), (x, y, z1), r, r * 0.55, sides=_q(hq, 6, 3), color="wood_mid")
    for z, half in yards:
        mb.tube((x - half, y, z), (x + half, y, z), r * 0.45, sides=_q(hq, 4, 3), color="wood_dark")


def rope(mb, a, b, r, hq, color="rope"):
    mb.tube(a, b, r, sides=_q(hq, 4, 3), color=color)


def nacelle(mb, x, y, z, length, r, hq, label, root_x=None, color="brass", index=0):
    """Pod with a propeller socket at its tail. root_x adds a pylon back to the hull."""
    if root_x is not None:
        mb.tube((root_x, y, z), (x, y, z), r * 0.34, sides=_q(hq, 4, 3), color="iron")
    if hq:
        mb.path([(x, y - length, z), (x, y - length * 0.5, z), (x, y + length * 0.5, z), (x, y + length, z)], [r * 0.35, r, r, r * 0.55], 8, color, smooth=True)
    else:
        mb.tube((x, y - length, z), (x, y + length, z), r * 0.8, r * 0.6, sides=5, color=color)
    mb.socket(f"propeller_{label}{index}", (x, y + length + 0.02, z))


def broadside(mb, ys, z, half_at, barrel, r, hq, draw=True, tag=None, carriage="wood_dark", color="iron", lean=False):
    """A row of guns per side. Always publishes muzzle sockets; LQ can skip the geometry."""
    for i, y in enumerate(ys):
        half = half_at(y)
        for sign, label in ((1, "L"), (-1, "R")):
            x0 = sign * (half * 0.94)
            x1 = x0 + sign * barrel
            if draw:
                if hq and lean:
                    mb.box((x0, y, z), (0.14, r * 3.3, r * 3.3), carriage)
                    mb.tube((x0, y, z), (x1, y, z), r * 1.05, r * 0.85, sides=5, color=color)
                elif hq:
                    mb.box((x0, y, z), (0.14, r * 3.3, r * 3.3), carriage)
                    mb.path([(x0, y, z), (x1 - sign * barrel * 0.2, y, z), (x1 - sign * barrel * 0.18, y, z), (x1, y, z)], [r, r * 0.8, r * 1.2, r * 1.2], 6, color)
                else:
                    mb.tube((x0, y, z), (x1, y, z), r, r, sides=3, color=color)
            name = f"muzzle_{label}{tag or ''}{'_' if tag else ''}{i}"
            mb.socket(name, (x1, y, z))


def wing(mb, sign, root, y0, y1, z, span, lift, hq, color="faction_a", spar="wood_dark", thick=0.1, ribs=2):
    tip = root + sign * span
    mid = y0 + (y1 - y0) * 0.6
    mb.plate([(root, y0, z), (tip, mid, z + lift), (tip, y1, z + lift * 0.86), (root, y1, z - 0.08)], thick, color)
    mb.tube((root, y0, z), (tip, mid, z + lift), 0.05 + span * 0.012, sides=_q(hq, 5, 3), color=spar)
    if hq:
        for k in range(ribs):
            u = (k + 1) / (ribs + 1)
            mb.tube((root + sign * span * u, y0 + (mid - y0) * u, z + lift * u), (root, _lerp(y0, y1, 0.3 + 0.6 * u), z), 0.03 + span * 0.006, sides=3, color=spar)


def fins(mb, x, y, z, length, span, thick, color, under=True):
    mb.plate([(x, y, z), (x, y + length, z + span), (x, y + length, z), (x, y + length * 0.55, z - 0.1)], thick, color)
    for sign in (1, -1):
        root = x + sign * span * 0.42
        mb.plate([(root, y, z - span * 0.4), (root + sign * span, y + length, z - span * 0.4), (root, y + length, z - span * 0.4), (root - sign * 0.1, y + length * 0.55, z - span * 0.4)], thick, color)


def base_sockets(mb, half, deck_z, env_z, vent_y, vent_z):
    mb.socket("deck_centre", (0, 0, deck_z))
    mb.socket("boarding_L", (half, 0, deck_z))
    mb.socket("boarding_R", (-half, 0, deck_z))
    mb.socket("smoke_vent", (0, vent_y, vent_z))
    mb.socket("envelope_centre", (0, 0, env_z))
    # Deck fires: bow, waist and stern. Ships with a shaped deck overwrite these afterwards.
    mb.socket("fire_0", (half * 0.4, -vent_y * 0.6, deck_z))
    mb.socket("fire_1", (-half * 0.4, 0, deck_z))
    mb.socket("fire_2", (half * 0.2, vent_y * 0.7, deck_z))


def _window_strip(mb, x_list, y, z, size, thick, color="lamp"):
    for x in x_list:
        mb.box((x, y, z), (size[0], thick, size[1]), color)


# ---- The Sovereign Gale ---------------------------------------------------------------------

def _gale_width(t):
    half = 5.0
    if t < 0.4:
        return half * max(0.05, math.sqrt(max(0.0, 1 - (1 - t / 0.4) ** 2)))
    if t > 0.7:
        return half * (1 - 0.34 * ((t - 0.7) / 0.3) ** 2)
    return half


def _gale_hull(mb, hq, wrecked=False):
    length = 38.0
    rows = _q(hq, 7, 3)
    bands = {0: "wood_dark", 1: "navy", 2: "wood_dark", 3: "faction_a", 4: "wood_dark", 5: "gold_dark", 6: "wood_mid"}
    lq_bands = {0: "wood_dark", 1: "wood_dark", 2: "faction_a"}
    if wrecked:
        # Charred: the gilding and paint have burned off.
        bands = {0: "storm_dark", 1: "wood_dark", 2: "abyss", 3: "rust_dark", 4: "abyss", 5: "wood_dark", 6: "storm_dark"}
        lq_bands = {0: "storm_dark", 1: "abyss", 2: "rust_dark"}
    stations = []
    for t in cosine_ts(_q(hq, 16, 8)):
        keel = 3.8 * (1 - t / 0.34) ** 2 if t < 0.34 else (2.6 * ((t - 0.72) / 0.28) ** 2 if t > 0.72 else 0.0)
        deck = 7.6 + (2.2 * (1 - t / 0.3) ** 2 if t < 0.3 else (2.0 * ((t - 0.62) / 0.38) ** 2 if t > 0.62 else 0.0))
        stations.append((-length / 2 + t * length, _gale_width(t), keel, deck))
    shell(mb, stations, rows, lambda r: (bands if hq else lq_bands)[r], power=0.55, tumble=0.14)
    return length


def _deck_y(t, length=38.0):
    return -length / 2 + t * length


def sovereign_gale(mb, hq, wrecked=False):
    """3-deck dreadnought: triple envelope, tiered stern gallery, gilded figurehead."""
    length = _gale_hull(mb, hq, wrecked)
    deck_z = 7.6
    y_of = _deck_y
    # Stern castle: two stepped tiers with a lit gallery across the transom.
    y0, y1 = y_of(0.74), y_of(0.985)
    mb.box((0, (y0 + y1) / 2, deck_z + 2.1), (7.2, y1 - y0, 3.4), "wood_red", top_scale=0.92)
    mb.box((0, (y0 + y1) / 2 + 1.0, deck_z + 4.5), (5.4, (y1 - y0) * 0.72, 1.9), "faction_c", top_scale=0.9)
    mb.box((0, (y0 + y1) / 2, deck_z + 3.92), (7.6, y1 - y0 + 0.5, 0.26), "gold_dark")
    mb.box((0, (y0 + y1) / 2 + 1.0, deck_z + 5.5), (5.8, (y1 - y0) * 0.78, 0.2), "gold_dark")
    if hq:
        _window_strip(mb, [-2.5, -1.25, 0, 1.25, 2.5], y1 + 0.03, deck_z + 2.2, (0.8, 1.5), 0.1, "ember" if wrecked else "lamp")
        _window_strip(mb, [-1.6, 0, 1.6], y1 + 0.03, deck_z + 4.5, (0.9, 0.9), 0.1, "ember" if wrecked else "lamp")
        for sign in (1, -1):
            for i in range(5):
                mb.box((sign * 3.55, y0 + 1.1 + i * 1.6, deck_z + 2.2), (0.1, 0.8, 1.2), "ember" if wrecked else "lamp")
    else:
        mb.box((0, y1 + 0.03, deck_z + 2.2), (6.0, 0.1, 1.5), "ember" if wrecked else "lamp")
    # Forecastle.
    fy0, fy1 = y_of(0.13), y_of(0.26)
    mb.box((0, (fy0 + fy1) / 2, deck_z + 2.1), (5.0, fy1 - fy0, 1.9), "wood_red", top_scale=0.86)
    # Figurehead: a winged gale spirit on the cutwater, the ship's calling card.
    bow = (0, y_of(0.0) - 0.4, 9.3)
    mb.tube((0, y_of(0.03), 7.8), (0, y_of(0.0) - 8.0, 11.8), 0.5, 0.06, sides=_q(hq, 6, 3), color="wood_dark")
    if hq:
        mb.sphere((bow[0], bow[1] - 0.2, bow[2] + 0.9), (0.42, 0.42, 0.5), 8, 4, "gold")
        mb.path([(0, bow[1], bow[2] - 1.0), (0, bow[1] - 0.2, bow[2]), (0, bow[1] - 0.2, bow[2] + 0.6)], [0.3, 0.55, 0.32], 6, "gold")
    for sign in (1, -1):
        mb.plate([(sign * 0.2, bow[1], bow[2] + 0.5), (sign * 3.0, bow[1] + 1.6, bow[2] + 2.8), (sign * 2.5, bow[1] + 2.0, bow[2] + 0.9), (sign * 0.2, bow[1] + 0.4, bow[2] - 0.5)], 0.1, "gold")

    # Three gun decks.
    half_at = lambda y: _gale_width((y + length / 2) / length)
    tiers = ((2.5, "a"), (4.3, "b"), (6.1, "c"))
    for z, tag in tiers:
        ys = [y_of(0.3 + 0.42 * (i + 0.5) / 7) for i in range(7)]
        draw = hq or tag != "b"
        broadside(mb, ys, z, half_at, 1.5, 0.21, hq, draw=draw, tag=tag, lean=True)
    # Triple envelope.
    z_centre = deck_z + 12.2
    rings = _q(hq, 12, 6)
    sides = _q(hq, 16, 8)
    if wrecked:
        # Holed and sagging: the belly drops and the panels tear to dark.
        def torn(i, j):
            if i == 0 or i == rings - 1:
                return "faction_c"
            if (i * 3 + j * 5) % 5 == 0:
                return "abyss"
            if (i + j * 3) % 9 == 0:
                return "ember"
            return "faction_a" if j % 2 else "canvas_dark"
        gasbag(mb, 0, 0.5, z_centre - 1.5, 32, 5.8, sides, rings, torn, flat=0.62)
    else:
        gasbag(mb, 0, 0.5, z_centre, 32, 6.4, sides, rings, striped("faction_a", "faction_b", "faction_c", rings))
    if hq:
        for s in (0.25, 0.5, 0.75):
            gasbag_band(mb, 0, 0.5, z_centre - (1.5 if wrecked else 0), 32, 5.8 if wrecked else 6.4, s, sides, "gold_dark", flat=0.62 if wrecked else 1.0)
    side_rings = _q(hq, 10, 5)
    side_sides = _q(hq, 12, 6)
    for sign in (1, -1):
        if wrecked and sign == -1:
            continue  # The starboard bag has burned away entirely.
        gasbag(mb, sign * 9.2, 3.0, z_centre - 5.4, 24, 3.7, side_sides, side_rings, striped("faction_a", "faction_b", "faction_c", side_rings))
        rope(mb, (sign * 4.6, 3.0, deck_z), (sign * 8.2, 3.0, z_centre - 8.6), 0.13, hq)
        rope(mb, (sign * 4.6, -4.0, deck_z), (sign * 8.2, -4.0, z_centre - 8.2), 0.13, hq)
    # Lift rig to the central bag.
    for t in _q(hq, (0.22, 0.42, 0.62, 0.8), (0.3, 0.7)):
        for sign in (1, -1):
            rope(mb, (sign * 4.2, y_of(t), deck_z), (sign * 2.4, y_of(t) * 0.8, z_centre - 5.6), 0.13, hq)
    fins(mb, 0, 11.0, z_centre + 2.0, 6.0, 5.8, 0.18, "faction_c")
    # Masts stand in the gap under the bag, with war sails.
    for i, t in enumerate((0.3, 0.48, 0.66)):
        y = y_of(t)
        top = z_centre - 5.5
        snapped = wrecked and i == 1
        h = (top - deck_z) * (0.45 if snapped else 1.0)
        mast(mb, 0, y, deck_z - 0.1, deck_z + h, 0.3, hq, yards=() if snapped else ((deck_z + h * 0.92, 4.2),))
        if not snapped:
            sail(mb, y - 0.15, deck_z + h * 0.9, deck_z + h * 0.22, 4.0, 0.9, hq, color="faction_a" if i == 1 else "canvas", tatter=wrecked)
    # Rear wings.
    for sign in (1, -1):
        if wrecked and sign == -1:
            wing(mb, sign, sign * 3.8, y_of(0.33), y_of(0.48), 5.8, 3.0, 0.2, hq, thick=0.16)
            continue
        wing(mb, sign, sign * 4.2, y_of(0.33), y_of(0.6), 5.8, 8.5, 2.8, hq, thick=0.16)
    # Four engines.
    for index, (t, z) in enumerate(((0.8, 5.2), (0.55, 3.6))):
        for sign, label in ((1, "L"), (-1, "R")):
            y = y_of(t)
            nacelle(mb, sign * 7.6, y, z, 2.0, 1.1, hq, label, root_x=sign * 4.4, color="brass", index=index)
    # Rudder.
    y = y_of(0.995)
    mb.plate([(0, y, 8.0), (0, y + 2.6, 6.8), (0, y + 3.4, 3.2), (0, y + 2.0, 1.8), (0, y, 3.0)], 0.2, "wood_dark")
    if hq:
        # Helm, capstan and quarterdeck rail: the camera lands here in the finale.
        mb.tube((0, y_of(0.71), deck_z), (0, y_of(0.71), deck_z + 0.9), 0.1, sides=4, color="wood_dark")
        with mb.xf(Matrix.Translation((0, y_of(0.71) - 0.1, deck_z + 1.1)) @ Matrix.Rotation(math.pi / 2, 4, "X")):
            mb.lathe([(0.6, -0.05), (0.6, 0.05)], 10, "wood_light", smooth=False)
        for sign in (1, -1):
            points = [(sign * _gale_width(k) * 0.9, y_of(k), deck_z + 0.75) for k in (0.1, 0.25, 0.4, 0.55, 0.72)]
            mb.path(points, [0.09] * len(points), 4, "gold_dark")
        mb.box((0, y_of(0.5), deck_z + 0.08), (2.2, 3.4, 0.26), "iron")
    base_sockets(mb, 5.0, deck_z, z_centre, y_of(0.82), deck_z + 6.5)
    mb.socket("lift_core", (0, y_of(0.5), 3.4))
    mb.socket("helm", (0, y_of(0.7), deck_z + 0.1))
    mb.socket("weakpoint_L", (5.0, y_of(0.5), 4.3))
    mb.socket("weakpoint_R", (-5.0, y_of(0.5), 4.3))
    for i, t in enumerate((0.25, 0.5, 0.78)):
        mb.socket(f"fire_{i}", (0, y_of(t), deck_z + 0.3))


def sovereign_gale_wrecked(mb, hq):
    """Prologue ending: the same ship after Morrow's sabotage, for its fall into the clouds."""
    sovereign_gale(mb, hq, wrecked=True)


# ---- The Rust-Wing / Armada Scout -----------------------------------------------------------

def rust_wing(mb, hq):
    """Agile one-deck gunboat. This model is both the Armada Scout (Gilded atlas) and the stolen
    Rust-Wing (Scrap atlas), so the prologue theft is literally the same ship."""
    length = 10.5
    stations = []
    for t in cosine_ts(_q(hq, 12, 6)):
        w = 1.25 * max(0.06, math.sqrt(max(0.0, 1 - (1 - t / 0.5) ** 2))) if t < 0.5 else 1.25 * (1 - 0.55 * ((t - 0.5) / 0.5) ** 1.6)
        keel = 0.8 * (1 - t / 0.5) ** 2 + 0.05 if t < 0.5 else 0.05 + 0.8 * ((t - 0.5) / 0.5) ** 2
        deck = 1.5 + 0.35 * (1 - t / 0.4) ** 2 if t < 0.4 else 1.5
        stations.append((-length / 2 + t * length, w, keel, deck))
    paints = {0: "iron", 1: "faction_c", 2: "faction_a", 3: "faction_a", 4: "faction_b"} if hq else {0: "iron", 1: "faction_a", 2: "faction_a"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.65)
    # Cigar envelope, slung close over the deck, with reinforcing riveted panels.
    z = 5.0
    rings = _q(hq, 10, 6)
    sides = _q(hq, 14, 8)
    def bag(i, j):
        if i == 0 or i == rings - 1:
            return "iron"
        if hq and (i * 2 + j * 3) % 11 == 0:
            return "canvas_dark"
        return "faction_a" if j % 4 < 2 else "faction_b"
    gasbag(mb, 0, 0.2, z, 10.0, 1.95, sides, rings, bag, flat=0.82)
    if hq:
        for s in (0.22, 0.55, 0.82):
            gasbag_band(mb, 0, 0.2, z, 10.0, 1.95, s, sides, "iron", flat=0.82)
    for y in _q(hq, (-3.0, -1.0, 1.0, 3.0), (-2.0, 2.0)):
        for sign in (1, -1):
            rope(mb, (sign * 0.9, y, 1.55), (sign * 0.7, y * 0.9, z - 1.42), 0.045, hq, "iron")
    # Open cockpit with a wind-screen at the bow, gun mount behind it.
    mb.box((0, 2.6, 1.85), (1.3, 2.0, 0.7), "faction_c", top_scale=0.84)
    if hq:
        mb.plate([(-0.5, -2.05, 1.65), (0.5, -2.05, 1.65), (0.38, -2.4, 2.25), (-0.38, -2.4, 2.25)], 0.04, "glass")
        with mb.xf(Matrix.Translation((0, -0.6, 1.5))):
            mb.lathe([(0.42, 0.0), (0.42, 0.18), (0.26, 0.3)], 8, "iron", smooth=False)
        mb.path([(0, -0.1, 1.95), (0, -0.6, 1.95), (0, -1.7, 1.98), (0, -1.75, 1.98), (0, -1.95, 1.98)], [0.12, 0.13, 0.085, 0.12, 0.12], 8, "iron")
    else:
        mb.tube((0, -0.2, 1.95), (0, -1.95, 1.98), 0.12, 0.1, sides=4, color="iron")
    mb.socket("muzzle_F0", (0, -1.95, 1.98))
    # Swept outrigger wings carry the engines at their tips: that is the agile silhouette.
    for sign, label in ((1, "L"), (-1, "R")):
        mb.plate([(sign * 0.95, -1.6, 1.0), (sign * 3.7, 0.2, 1.65), (sign * 3.7, 1.2, 1.58), (sign * 0.8, 2.2, 0.95)], 0.08, "faction_a")
        mb.tube((sign * 0.95, -1.6, 1.0), (sign * 3.7, 0.2, 1.65), 0.07, sides=_q(hq, 4, 3), color="iron")
        nacelle(mb, sign * 3.85, 0.7, 1.65, 1.0, 0.36, hq, label, color="iron_light")
    fins(mb, 0, 3.4, z + 0.3, 1.6, 1.8, 0.05, "faction_c")
    y = length / 2 - 0.1
    mb.plate([(0, y - 0.5, 1.5), (0, y + 0.55, 1.2), (0, y + 0.6, 0.4), (0, y - 0.1, 0.2)], 0.07, "faction_c")
    # Ram spur.
    mb.tube((0, -4.6, 0.95), (0, -6.3, 1.05), 0.17, 0.02, sides=_q(hq, 5, 3), color="iron_light")
    if hq:
        # Bolted repair plates, in iron so they read on either faction.
        for x, y, z2 in ((1.05, -1.0, 1.1), (-1.05, 1.1, 1.05), (1.0, 1.9, 0.92)):
            mb.box((x, y, z2), (0.06, 0.8, 0.4), "iron_light")
        mb.sphere((0.42, 2.6, 2.32), 0.14, 6, 3, "lamp", smooth=False)
    base_sockets(mb, 1.25, 1.5, z, 3.2, 2.7)
    mb.socket("lift_core", (0, 0, 0.9))
    mb.socket("helm", (0, -1.6, 1.5))
    mb.socket("hatch_escape", (0, 2.4, 2.2))


# ---- The Iron Maw ---------------------------------------------------------------------------

def _maw_hull(mb, x, hq, length=18.0):
    def width(t):
        return 1.8 * max(0.06, math.sqrt(max(0.0, 1 - (1 - t / 0.3) ** 2))) if t < 0.3 else 1.8 * (1 - 0.28 * ((t - 0.6) / 0.4) ** 2 if t > 0.6 else 1)
    stations = []
    for t in cosine_ts(_q(hq, 12, 6)):
        keel = 1.6 * (1 - t / 0.28) ** 2 if t < 0.28 else (0.8 * ((t - 0.75) / 0.25) ** 2 if t > 0.75 else 0.0)
        deck = 3.5 + 0.9 * (1 - t / 0.3) ** 2 if t < 0.3 else 3.5
        stations.append((-length / 2 + t * length, width(t), keel, deck))
    paints = {0: "rust_dark", 1: "faction_a", 2: "rust", 3: "faction_c", 4: "iron"} if hq else {0: "rust_dark", 1: "faction_a", 2: "iron"}
    place = Matrix.Translation((x, 0, 0))
    with mb.xf(place):
        shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.5)


def iron_maw(mb, hq):
    """Twin-hull brigantine: a bridge deck between two hulls and a toothed mouth at the bow.
    The harpoon winch sits inside the jaws, firing forward."""
    gap = 3.6
    for sign in (1, -1):
        _maw_hull(mb, sign * gap, hq)
    deck_z = 3.5
    # Bridge deck between hulls.
    mb.box((0, 2.0, deck_z - 0.12), (2 * gap, 11.0, 0.5), "wood_mid")
    for y in _q(hq, (-3.3, 0.0, 2.5, 5.5, 7.2), (-3.3, 7.2)):
        mb.box((0, y, deck_z - 0.5), (2 * gap + 0.7, 0.6, 0.6), "rust_dark")
    # The maw: iron jaw plates and triangular teeth framing the bow gap.
    jaw_y = -8.9
    mb.box((0, -3.9, 1.3), (2 * gap - 0.6, 1.2, 1.5), "rust_dark")
    teeth = _q(hq, 7, 3)
    for i in range(teeth):
        x = (i - (teeth - 1) / 2) * ((2 * gap - 1.8) / max(1, teeth - 1))
        h = 1.55 - abs(i - (teeth - 1) / 2) * _q(hq, 0.16, 0.3)
        mb.plate([(x - 0.42, -4.3, 3.4), (x + 0.42, -4.3, 3.4), (x, -5.3, 3.4 - h)], 0.2, "iron_light")
        mb.plate([(x - 0.42, -4.3, 0.75), (x + 0.42, -4.3, 0.75), (x, -5.0, 0.75 + h * 0.62)], 0.2, "iron_light")
    for sign in (1, -1):
        mb.tube((sign * gap, -8.7, 3.8), (sign * (gap - 0.5), jaw_y - 2.4, 3.4), 0.42, 0.03, sides=_q(hq, 6, 3), color="iron_light")
        mb.tube((sign * gap, -7.7, 1.2), (sign * (gap - 0.8), jaw_y - 1.9, 0.3), 0.32, 0.03, sides=_q(hq, 5, 3), color="iron_light")
        if hq:
            for y in (-6.3, -3.4, -0.5, 2.4):
                mb.plate([(sign * (gap + 1.7), y - 0.45, 2.75), (sign * (gap + 1.72), y + 0.45, 2.75), (sign * (gap + 2.65), y, 3.1)], 0.14, "iron_light")
    # Harpoon winch: drum and launcher on a pedestal, exposed so the player can reach it.
    with mb.xf(Matrix.Translation((0, -2.2, deck_z - 0.12))):
        mb.box((0, 0.6, 0.45), (2.7, 2.4, 0.9), "faction_c", top_scale=0.82)
        with mb.xf(Matrix.Translation((-1.0, 0.8, 1.35)) @ Matrix.Rotation(math.pi / 2, 4, "Y")):
            mb.lathe([(0.75, 0.0), (0.75, 0.25), (0.48, 0.25), (0.48, 1.75), (0.75, 1.75), (0.75, 2.0)], _q(hq, 10, 5), lambda i, _j: "rope" if i == 2 else "iron", smooth=False)
        mb.path([(0, 0.2, 1.5), (0, -0.8, 1.68), (0, -2.0, 1.78), (0, -2.05, 1.78), (0, -2.35, 1.78)], [0.3, 0.27, 0.2, 0.32, 0.32], _q(hq, 8, 4), "iron")
        mb.tube((0, -2.3, 1.78), (0, -3.1, 1.8), 0.1, 0.02, sides=_q(hq, 5, 3), color="iron_light")
        if hq:
            for sign in (1, -1):
                mb.plate([(sign * 0.08, -2.75, 1.8), (sign * 0.55, -2.25, 1.95), (sign * 0.5, -2.25, 1.6)], 0.08, "iron_light")
    mb.socket("harpoon_muzzle", (0, -5.4, deck_z + 1.66))
    mb.socket("winch", (0, -1.4, deck_z + 1.2))
    # One huge patched envelope over both hulls.
    z = deck_z + 8.2
    rings = _q(hq, 12, 6)
    sides = _q(hq, 16, 8)
    def bag(i, j):
        if i == 0 or i == rings - 1:
            return "iron"
        if (i * 5 + j * 3) % 13 == 0:
            return "faction_c"
        if (i * 3 + j * 7) % 9 == 0:
            return "canvas_dark"
        return "faction_b" if j % 2 else "faction_a"
    gasbag(mb, 0, 1.0, z, 19, 4.8, sides, rings, bag, flat=0.88)
    if hq:
        for s in (0.2, 0.42, 0.66, 0.84):
            gasbag_band(mb, 0, 1.0, z, 19, 4.8, s, sides, "iron", flat=0.88)
    fins(mb, 0, 8.2, z + 1.1, 3.6, 3.8, 0.12, "rust_dark")
    # Heavy iron chains instead of rope.
    for y in _q(hq, (-3.0, 0.5, 3.5, 6.5), (-1.5, 5.0)):
        for sign in (1, -1):
            rope(mb, (sign * gap, y, deck_z), (sign * 2.8, y * 0.85 + 0.5, z - 3.2), 0.1, hq, "iron")
    # Single mast and scrap sail on the bridge.
    mast(mb, 0, 2.2, deck_z, z - 4.0, 0.22, hq, yards=((z - 4.5, 3.4),))
    sail(mb, 2.05, z - 4.6, deck_z + 1.2, 3.1, 0.7, hq, color="canvas_dark", tatter=True)
    # Anchors dragging from the stern: Krag's signature.
    def anchor(x, y, top, h):
        mb.tube((x, y, top), (x, y, top - h), 0.09, sides=_q(hq, 5, 3), color="iron")
        mb.tube((x - 0.55, y, top - 0.25), (x + 0.55, y, top - 0.25), 0.05, sides=3, color="iron")
        mb.path([(x - 0.8, y, top - h + 0.42), (x - 0.45, y, top - h + 0.05), (x, y, top - h), (x + 0.45, y, top - h + 0.05), (x + 0.8, y, top - h + 0.42)], [0.02, 0.11, 0.13, 0.11, 0.02], _q(hq, 4, 3), "iron")
    for sign in (1, -1):
        anchor(sign * gap, 7.6, 3.0, 2.2)
    # Engines on outer hull shoulders, plus exhaust stacks.
    for sign, label in ((1, "L"), (-1, "R")):
        nacelle(mb, sign * (gap + 3.1), 5.2, 2.4, 1.5, 0.72, hq, label, root_x=sign * (gap + 1.3), color="iron_light")
    if hq:
        for x in (-1.4, 1.4):
            mb.tube((x, 7.0, deck_z), (x, 7.2, deck_z + 2.4), 0.32, 0.26, sides=6, color="rust_dark")
    # Three heavy cannon per hull.
    half = lambda _y: gap + 1.72
    broadside(mb, (-3.0, 0.3, 3.6), 2.45, half, 1.05, 0.16, hq)
    base_sockets(mb, gap + 1.8, deck_z, z, 7.0, deck_z + 2.6)
    mb.socket("lift_core", (0, 3.0, deck_z - 1.0))
    mb.socket("helm", (0, 6.6, deck_z + 0.1))
    mb.socket("cargo_door", (0, 6.0, deck_z - 0.8))
    mb.socket("hook_tether_L", (gap, 7.6, 0.8))
    mb.socket("hook_tether_R", (-gap, 7.6, 0.8))


# ---- The Mirage -----------------------------------------------------------------------------

def mirage(mb, hq):
    """Stealth clipper: needle hull under a flat manta lift-wing, with raked sails and afterburners.
    Vex's and Vesper's ships are this model with the Syndicate and Obsidian atlases."""
    length = 20.0
    stations = []
    for t in cosine_ts(_q(hq, 14, 7)):
        w = 1.55 * max(0.04, math.sin(math.pi * min(1.0, t * 1.05) ** 0.6)) if t < 0.92 else 1.55 * max(0.04, math.sin(math.pi * 0.966 ** 0.6)) * 2.8 * (1 - t) + 0.25
        keel = 1.8 * (1 - t / 0.42) ** 2 + 0.0 if t < 0.42 else 0.7 * ((t - 0.42) / 0.58) ** 2
        deck = 2.5 + 0.55 * (1 - t / 0.5) ** 2 if t < 0.5 else 2.5 + 0.2 * ((t - 0.5) / 0.5)
        stations.append((-length / 2 + t * length, w, keel, deck))
    paints = {0: "faction_c", 1: "faction_c", 2: "faction_a", 3: "faction_b", 4: "faction_c"} if hq else {0: "faction_c", 1: "faction_a", 2: "faction_b"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: paints[r], power=0.8)
    # Long needle bowsprit makes the silhouette unmistakable.
    mb.tube((0, -9.8, 2.9), (0, -16.5, 4.3), 0.2, 0.02, sides=_q(hq, 6, 3), color="silver")
    # Manta lift-wing: a very flat envelope, wider than long, with swept tips.
    z = 8.0
    sides = _q(hq, 18, 10)
    rings = _q(hq, 11, 6)
    def bag(i, j):
        if i == 0 or i == rings - 1:
            return "faction_c"
        return "faction_a" if (j // 2) % 2 else "faction_c"
    place = Matrix.Translation((0, 1.0, z)) @ Matrix.Diagonal((1.0, 1.0, 1.0, 1.0))
    with mb.xf(place):
        half = 8.5
        profile = []
        for i in range(rings):
            s = 0.5 - 0.5 * math.cos(math.pi * (i + 0.5) / rings)
            profile.append((max(0.08, math.sin(math.pi * s ** 0.75)) ** 0.7, -half + 2 * half * s))
        with mb.xf(Matrix.Rotation(-math.pi / 2, 4, "X") @ Matrix.Diagonal((6.0, 1.15, 1.0, 1.0))):
            mb.lathe(profile, sides, bag, smooth=True, phase=math.pi / sides)
    for sign in (1, -1):
        # Swept wingtips and a glowing edge stripe.
        mb.plate([(sign * 5.2, -1.5, z), (sign * 9.6, 4.5, z + 0.55), (sign * 9.4, 7.2, z + 0.5), (sign * 4.6, 5.8, z)], 0.14, "faction_c")
        mb.plate([(sign * 8.9, 3.5, z + 0.5), (sign * 9.7, 4.5, z + 0.8), (sign * 9.55, 7.2, z + 0.7), (sign * 9.0, 6.6, z + 0.45)], 0.1, "faction_b")
    # Struts.
    for y in _q(hq, (-3.6, 0.2, 4.0), (-2.0, 3.0)):
        for sign in (1, -1):
            rope(mb, (sign * 1.15, y, 2.7), (sign * 2.6, y, z - 0.8), 0.06, hq, "silver")
    # Raked lateen sails: thin blades angled back along the hull.
    for y, rake in ((-3.5, 2.6), (1.2, 2.2)):
        mb.tube((0, y, 2.8), (0, y + rake * 0.5, z - 1.0), 0.09, 0.05, sides=_q(hq, 5, 3), color="wood_dark")
        mb.plate([(0, y + 0.14, 3.1), (0, y + rake * 0.56, z - 1.25), (0, y + rake * 2.1, 3.6)], 0.05, "faction_b")
    # Wide low outrigger fins near the waterline carry nothing but speed.
    for sign in (1, -1):
        mb.plate([(sign * 1.15, -2.4, 1.05), (sign * 6.2, 3.0, 0.6), (sign * 6.2, 4.6, 0.62), (sign * 1.05, 3.4, 1.0)], 0.07, "faction_a")
        if hq:
            mb.tube((sign * 1.15, -2.4, 1.05), (sign * 6.2, 3.0, 0.6), 0.055, sides=4, color="silver")
    # Stern: afterburner turbines with glowing throats.
    for sign, label in ((1, "L"), (-1, "R")):
        x = sign * 2.3
        y = 7.7
        zz = 2.15
        mb.tube((sign * 0.7, y - 1.6, zz), (x, y - 1.6, zz), 0.16, sides=_q(hq, 4, 3), color="iron")
        rim = _q(hq, 10, 6)
        with mb.xf(Matrix.Translation((x, y, zz)) @ Matrix.Rotation(-math.pi / 2, 4, "X")):
            mb.lathe([(0.32, -2.9), (0.74, -2.1), (0.8, -0.9), (0.68, 0.45), (0.62, 0.95)], rim, "iron_light", smooth=hq)
            mb.lathe([(0.48, 0.96), (0.48, 1.0)], rim, "plasma", smooth=False)
            if hq:
                mb.lathe([(0.82, -1.2), (0.82, -0.9)], rim, "brass", smooth=False, caps=(False, False))
        mb.socket(f"afterburner_{label}", (x, y + 1.02, zz))
        mb.socket(f"propeller_{label}0", (x, y - 2.95, zz))
    y = 9.5
    mb.plate([(0, y - 1.8, 3.0), (0, y + 0.2, 5.8), (0, y + 1.1, 5.6), (0, y + 0.3, 2.6)], 0.1, "faction_c")
    # Slim gun pair each side.
    half_at = lambda y2: 1.45
    broadside(mb, (-1.7, 1.0), 2.05, half_at, 0.95, 0.09, hq)
    if hq:
        # Crystal cockpit canopy and a glow strip along the wale.
        mb.sphere((0, 6.0, 2.75), (0.8, 1.7, 0.6), 8, 4, "glass")
        for sign in (1, -1):
            mb.tube((sign * 1.53, -4.2, 2.42), (sign * 1.53, 5.4, 2.42), 0.03, sides=3, color="plasma")
    base_sockets(mb, 1.55, 2.5, z, 7.0, 3.6)
    mb.socket("lift_core", (0, 2.5, 1.3))
    mb.socket("helm", (0, 5.0, 2.55))


# ---- The Bastion ----------------------------------------------------------------------------

def bastion(mb, hq):
    """Ironclad frigate: sloped casemate, armoured gas cells, and a prow built to ram."""
    length = 26.0
    stations = []
    for t in cosine_ts(_q(hq, 10, 6)):
        w = 5.0 * max(0.28, math.sqrt(max(0.0, 1 - (1 - t / 0.3) ** 2))) if t < 0.3 else (5.0 * (1 - 0.3 * ((t - 0.78) / 0.22) ** 2) if t > 0.78 else 5.0)
        keel = 2.5 * (1 - t / 0.3) ** 2 if t < 0.3 else 1.3 * ((t - 0.7) / 0.3) ** 2 if t > 0.7 else 0.0
        stations.append((-length / 2 + t * length, w, keel, 4.0))
    shell(mb, stations, _q(hq, 4, 3), lambda r: ("iron", "steel", "iron", "faction_a")[r] if hq else ("iron", "steel", "faction_a")[r], power=0.28)
    y_of = lambda t: -length / 2 + t * length
    # The ram: a stepped iron wedge longer than the bow.
    ram_tip = y_of(0.0) - 7.5
    rings = []
    for y, half_w, half_h, zc in ((y_of(0.14), 2.8, 1.7, 2.4), (y_of(0.04), 1.9, 1.25, 2.1), (y_of(0.0) - 3.0, 0.9, 0.7, 1.75), (ram_tip, 0.08, 0.1, 1.45)):
        rings.append([(-half_w, y, zc - half_h), (half_w, y, zc - half_h), (half_w, y, zc + half_h * 0.72), (0, y, zc + half_h), (-half_w, y, zc + half_h * 0.72)])
    mb.loft(rings, lambda i, _j: "iron_light" if i >= 1 else "iron")
    if hq:
        for y in (y_of(0.0) - 1.4, y_of(0.04)):
            mb.box((0, y, 3.2), (0.3, 0.7, 0.55), "iron")
    # Sloped casemate.
    rings = []
    for z, half_w, y0, y1 in ((4.0, 4.7, y_of(0.13), y_of(0.86)), (6.3, 3.3, y_of(0.2), y_of(0.8))):
        rings.append([(-half_w, y0, z), (half_w, y0, z), (half_w, y1, z), (-half_w, y1, z)])
    mb.loft(rings, "steel")
    # Armour seams and gunports on the slope.
    if hq:
        for t in (0.26, 0.38, 0.5, 0.62, 0.74):
            y = y_of(t)
            for sign in (1, -1):
                mb.plate([(sign * 4.72, y - 0.09, 4.0), (sign * 3.32, y - 0.09, 6.3), (sign * 3.32, y + 0.09, 6.3), (sign * 4.72, y + 0.09, 4.0)], 0.1, "iron")
    half = lambda _y: 4.05
    broadside(mb, [y_of(t) for t in (0.3, 0.42, 0.54, 0.66)], 5.0, half, 1.3, 0.2, hq, color="iron_light")
    # Roof: conning tower, mortar pit, twin stacks.
    mb.box((0, y_of(0.32), 7.0), (2.4, 2.8, 1.5), "iron", top_scale=0.84)
    if hq:
        mb.box((0, y_of(0.32) - 1.2, 7.1), (1.8, 0.35, 0.28), "lamp")
    with mb.xf(Matrix.Translation((0, y_of(0.5), 6.3))):
        mb.lathe([(1.25, 0.0), (1.25, 0.5), (0.8, 0.55)], _q(hq, 10, 6), "iron_light", smooth=False)
    mb.tube((0, y_of(0.5), 6.5), (0, y_of(0.5) - 1.0, 8.4), 0.45, 0.58, sides=_q(hq, 8, 4), color="iron")
    mb.socket("muzzle_Mortar", (0, y_of(0.5) - 1.0, 8.4))
    for sign in (1, -1):
        x = sign * 1.15
        mb.tube((x, y_of(0.68), 6.3), (x, y_of(0.68), 9.0), 0.48, 0.42, sides=_q(hq, 8, 4), color="iron")
        if hq:
            with mb.xf(Matrix.Translation((x, y_of(0.68), 0))):
                mb.lathe([(0.52, 8.7), (0.52, 9.0)], 8, "faction_b", smooth=False)
    # Three armoured gas cells on a rigid frame, rather than one soft bag.
    z = 13.0
    rings_n = _q(hq, 8, 5)
    sides = _q(hq, 10, 6)
    armour = lambda i, j: "iron" if (i == 0 or i == rings_n - 1) else ("steel" if j % 2 else "faction_a")
    for x, r, zz, ln in ((0, 3.6, z + 0.6, 20), (6.2, 2.7, z - 1.2, 15), (-6.2, 2.7, z - 1.2, 15)):
        gasbag(mb, x, 0.6, zz, ln, r, sides, rings_n, armour)
        if hq:
            for s in (0.3, 0.6):
                gasbag_band(mb, x, 0.6, zz, ln, r, s, sides, "iron", flat=1.0)
    # Rigid girder frame linking them to the casemate.
    for y in _q(hq, (-6.0, 0.0, 6.0), (-4.0, 4.0)):
        for sign in (1, -1):
            mb.tube((sign * 3.0, y, 6.2), (sign * 6.2, y * 0.8, z - 3.7), 0.15, sides=_q(hq, 4, 3), color="iron")
            mb.tube((sign * 2.2, y, 6.3), (sign * 1.5, y * 0.9, z - 2.8), 0.15, sides=_q(hq, 4, 3), color="iron")
    mb.tube((-6.2, 0.6, z - 3.5), (6.2, 0.6, z - 3.5), 0.18, sides=_q(hq, 4, 3), color="iron")
    # Stubby armoured fins and four engines.
    fins(mb, 0, 9.0, z + 3.0, 3.6, 3.2, 0.16, "iron")
    for index, y in enumerate((y_of(0.82), y_of(0.55))):
        for sign, label in ((1, "L"), (-1, "R")):
            nacelle(mb, sign * 6.8, y, 2.7, 1.5, 0.82, hq, label, root_x=sign * 4.8, color="iron_light", index=index)
    y = y_of(0.99)
    mb.plate([(0, y, 3.6), (0, y + 2.2, 2.8), (0, y + 2.4, 0.7), (0, y, 1.3)], 0.2, "iron")
    base_sockets(mb, 5.0, 4.0, z, y_of(0.68), 9.2)
    mb.socket("ram_tip", (0, ram_tip, 1.45))
    mb.socket("lift_core", (0, y_of(0.5), 2.5))
    mb.socket("helm", (0, y_of(0.32), 6.4))


# ---- Tartarus Aloft -------------------------------------------------------------------------

def tartarus_aloft(mb, hq):
    """The prison that never lands: a fortress block on a barge, cells down both flanks."""
    length, half = 30.0, 7.0
    # Barge belly: nearly a box with sloped ends.
    rings = []
    for y, h, b in ((-length / 2 - 1.5, 2.2, 3.0), (-length / 2 + 3.0, half, 0.6), (length / 2 - 3.0, half, 0.6), (length / 2 + 1.0, 3.0, 2.0)):
        rings.append([(-h, y, 6.0), (-h * 0.72, y, b), (h * 0.72, y, b), (h, y, 6.0)])
    mb.loft(rings, lambda _i, j: "iron" if j == 1 else "steel")
    deck_z = 6.0
    # Hanging solitary block under the keel.
    mb.box((0, 2.0, 0.0), (6.0, 11.0, 1.4), "iron", top_scale=1.2)
    mb.socket("brig", (0, 2.0, 0.7))
    # Keep: three stepped tiers.
    tiers = ((deck_z, 3.8, 6.4, 22.0), (deck_z + 3.8, 3.2, 5.2, 17.0), (deck_z + 7.0, 2.8, 3.7, 10.0))
    for i, (z, h, w, l) in enumerate(tiers):
        mb.box((0, 0.5, z + h / 2), (w * 2, l, h), ("steel", "faction_a", "faction_c")[i], top_scale=0.96)
        mb.box((0, 0.5, z + h + 0.1), (w * 2 + 0.5, l + 0.5, 0.28), "faction_b")
        # Cell windows: barred and lit, in rows down both flanks.
        windows = (8, 6, 0)[i]
        for k in range(windows):
            y = 0.5 + (k + 0.5 - windows / 2) * (l - 2) / max(1, windows)
            for sign in (1, -1):
                if hq:
                    mb.box((sign * (w * 0.985), y, z + h * 0.55), (0.14, 0.7, 1.15), "abyss")
                    mb.box((sign * (w * 0.995), y, z + h * 0.55), (0.1, 0.42, 0.8), "lamp")
                    for b in (-0.18, 0.18):
                        mb.box((sign * (w * 1.015), y + b, z + h * 0.55), (0.09, 0.07, 1.2), "iron")
                elif k % 2 == 0:
                    mb.box((sign * (w * 0.995), y, z + h * 0.55), (0.1, 0.62, 1.0), "lamp")
    # Luxury war room: a warm gallery hidden on top, the only pretty thing aboard (the twist).
    top = deck_z + 9.8
    mb.box((0, 3.5, top + 0.9), (5.0, 4.0, 1.8), "velvet", top_scale=0.86)
    if hq:
        _window_strip(mb, [-1.6, 0.0, 1.6], 1.45, top + 0.95, (1.0, 1.1), 0.1, "lamp")
        mb.box((0, 3.5, top + 1.88), (5.2, 4.2, 0.16), "gold")
    mb.socket("war_room", (0, 3.5, top))
    # Corner watchtowers with searchlights.
    for sx in (1, -1):
        for sy in (1, -1):
            x, y = sx * 6.3, 0.5 + sy * 12.0
            s = _q(hq, 8, 4)
            with mb.xf(Matrix.Translation((x, y, deck_z - 0.2))):
                mb.lathe([(1.5, 0.0), (1.2, 7.0), (1.7, 7.4), (1.7, 8.3), (0.8, 9.5), (0.08, 10.6)], s, lambda i, _j: "faction_b" if i == 2 else ("faction_a" if i >= 3 else "steel"), smooth=False)
            mb.box((x - sx * 1.72, y, deck_z + 7.75), (0.3, 1.1, 0.7), "lamp")
            mb.socket(f"tower_{'F' if sy < 0 else 'B'}{'L' if sx > 0 else 'R'}", (x, y, deck_z + 8.1))
    # Four small gas cells, chained: it wallows, it never soars.
    z = deck_z + 19.5
    r_n = _q(hq, 8, 5)
    s_n = _q(hq, 12, 6)
    bag = lambda i, j: "iron" if (i == 0 or i == r_n - 1) else ("faction_a" if j % 2 else "faction_b" if j % 4 == 0 else "faction_c")
    for x, y, r in ((6.4, -5.0, 4.4), (-6.4, -5.0, 4.4), (6.4, 7.0, 4.4), (-6.4, 7.0, 4.4)):
        gasbag(mb, x, y, z, 13.5, r, s_n, r_n, bag)
        if hq:
            gasbag_band(mb, x, y, z, 13.5, r, 0.5, s_n, "iron")
        rope(mb, (x * 0.8, y - 4, deck_z + 3.5), (x, y - 3, z - r * 0.88), 0.15, hq, "iron")
        rope(mb, (x * 0.8, y + 4, deck_z + 3.5), (x, y + 3, z - r * 0.88), 0.15, hq, "iron")
    # Bow gatehouse with dock, spiked prow and gibbet cages hanging off the stern.
    mb.box((0, -14.2, deck_z + 1.7), (8.0, 2.4, 3.4), "steel", top_scale=0.92)
    mb.box((0, -15.45, deck_z + 1.4), (3.2, 0.2, 2.6), "abyss")
    if hq:
        for x in (-1.2, -0.4, 0.4, 1.2):
            mb.box((x, -15.6, deck_z + 1.4), (0.14, 0.14, 2.6), "iron")
    for sign in (1, -1):
        mb.tube((sign * 3.2, -15.5, 4.8), (sign * 3.2, -20.8, 3.8), 0.42, 0.03, sides=_q(hq, 6, 3), color="iron_light")
    for x in _q(hq, (-4.2, 0.0, 4.2), (0.0,)):
        y = 15.5
        mb.tube((x, y, 5.6), (x, y + 1.5, 2.7), 0.05, sides=3, color="iron")
        s = _q(hq, 8, 4)
        with mb.xf(Matrix.Translation((x, y + 1.5, 0.8))):
            mb.lathe([(0.75, 0.0), (0.8, 1.2), (0.45, 1.9)], s, lambda _i, j: "iron" if j % 2 else "abyss", smooth=False)
    # Engines and guns.
    for index, y in enumerate((11.0, -7.0)):
        for sign, label in ((1, "L"), (-1, "R")):
            nacelle(mb, sign * 10.0, y, 4.0, 1.9, 1.05, hq, label, root_x=sign * 6.6, color="iron_light", index=index)
    half_at = lambda _y: half
    broadside(mb, (-8.0, -3.0, 3.0, 8.0), 4.5, half_at, 1.4, 0.2, hq)
    base_sockets(mb, half, deck_z, z, 9.0, deck_z + 11.0)
    mb.socket("dock", (0, -15.5, deck_z))
    mb.socket("glider_launch_L", (6.0, 0.0, deck_z + 0.3))
    mb.socket("glider_launch_R", (-6.0, 0.0, deck_z + 0.3))
    mb.socket("lift_core", (0, 0, 3.4))


# ---- Armada escorts -------------------------------------------------------------------------

def _armada_hull(mb, length, half, height, hq, stations=12):
    def width(t):
        if t < 0.38:
            return half * max(0.05, math.sqrt(max(0.0, 1 - (1 - t / 0.38) ** 2)))
        return half * (1 - 0.32 * ((t - 0.68) / 0.32) ** 2) if t > 0.68 else half
    out = []
    for t in cosine_ts(_q(hq, stations, stations // 2)):
        keel = height * 0.55 * (1 - t / 0.34) ** 2 if t < 0.34 else (height * 0.36 * ((t - 0.7) / 0.3) ** 2 if t > 0.7 else 0.0)
        deck = height + (height * 0.26 * (1 - t / 0.3) ** 2 if t < 0.3 else 0.0)
        out.append((-length / 2 + t * length, width(t), keel, deck))
    paints = {0: "faction_a", 1: "faction_a", 2: "enamel", 3: "faction_c", 4: "faction_a"} if hq else {0: "faction_a", 1: "enamel", 2: "faction_c"}
    shell(mb, out, _q(hq, 5, 3), lambda r: paints[r], power=0.6, tumble=0.1)
    return width


def armada_corvette(mb, hq):
    """Fast Gilded Armada escort: white and gold, with a rigid fin-stabilised envelope."""
    length, half, height = 15.0, 2.5, 2.6
    width = _armada_hull(mb, length, half, height, hq)
    y_of = lambda t: -length / 2 + t * length
    deck = height
    # Golden eagle prow.
    mb.tube((0, y_of(0.02), height + 0.4), (0, y_of(0.0) - 3.2, height + 1.5), 0.26, 0.03, sides=_q(hq, 6, 3), color="gold")
    for sign in (1, -1):
        mb.plate([(sign * 0.1, y_of(0.04), height + 0.75), (sign * 2.5, y_of(0.0) + 1.5, height + 2.1), (sign * 1.8, y_of(0.0) + 2.0, height + 0.95)], 0.08, "gold")
    # Superstructure.
    mb.box((0, y_of(0.75), deck + 0.9), (3.6, 3.7, 1.9), "enamel", top_scale=0.86)
    mb.box((0, y_of(0.75), deck + 1.92), (3.8, 3.9, 0.16), "gold_dark")
    if hq:
        for x in (-1.1, 0.0, 1.1):
            mb.box((x, y_of(0.75) - 1.87, deck + 1.0), (0.7, 0.1, 0.65), "lamp")
    # Envelope with fins and a gold nose.
    z = deck + 6.2
    rings = _q(hq, 11, 6)
    sides = _q(hq, 14, 8)
    def bag(i, j):
        if i == 0 or i == rings - 1:
            return "faction_c"
        return "faction_a" if j % 3 == 0 else "enamel"
    gasbag(mb, 0, 0, z, 14.5, 3.1, sides, rings, bag)
    if hq:
        for s in (0.3, 0.65):
            gasbag_band(mb, 0, 0, z, 14.5, 3.1, s, sides, "gold_dark")
    fins(mb, 0, 4.5, z + 0.8, 3.2, 3.2, 0.1, "faction_a")
    for y in _q(hq, (-4.0, -1.2, 1.6, 4.2), (-2.5, 3.0)):
        for sign in (1, -1):
            rope(mb, (sign * width((y + length / 2) / length) * 0.86, y, deck), (sign * 1.3, y * 0.9, z - 2.8), 0.05, hq, "gold_dark")
    # Standard on the keel-line mast.
    mast(mb, 0, -1.3, deck, z - 2.9, 0.12, hq)
    mb.plate([(0, -1.2, z - 3.1), (0, 0.9, z - 3.5), (0, -1.2, z - 4.6)], 0.04, "faction_c")
    for sign, label in ((1, "L"), (-1, "R")):
        wing(mb, sign, sign * 2.2, y_of(0.32), y_of(0.58), 1.7, 3.2, 1.1, hq, color="enamel", spar="gold_dark", thick=0.08)
        nacelle(mb, sign * 3.8, y_of(0.8), 1.7, 1.1, 0.5, hq, label, root_x=sign * 2.0, color="gold_dark")
    half_at = lambda y: width((y + length / 2) / length)
    broadside(mb, [y_of(t) for t in (0.4, 0.55, 0.7)], height - 0.75, half_at, 0.75, 0.11, hq, color="gold_dark", carriage="faction_a")
    base_sockets(mb, half, deck, z, y_of(0.75), deck + 2.2)
    mb.socket("lift_core", (0, 0, 1.2))
    mb.socket("helm", (0, y_of(0.68), deck + 0.05))
    for i, t in enumerate((0.3, 0.72)):
        mb.socket(f"fire_{i}", (0, y_of(t), deck + 0.2))


def armada_frigate(mb, hq):
    """Missile frigate from the Act IV ship-hopping gauntlet. Its siege cannon can be turned on
    the Sovereign Gale once boarded, so the gun is huge and mounted to traverse."""
    length, half, height = 22.0, 3.8, 3.6
    width = _armada_hull(mb, length, half, height, hq, stations=14)
    y_of = lambda t: -length / 2 + t * length
    deck = height
    mb.tube((0, y_of(0.02), height + 0.5), (0, y_of(0.0) - 3.8, height + 1.7), 0.32, 0.03, sides=_q(hq, 6, 3), color="gold")
    # Siege turret: a pivoting drum with one long gun.
    ty = y_of(0.3)
    with mb.xf(Matrix.Translation((0, ty, deck))):
        mb.lathe([(2.0, 0.0), (1.95, 0.8), (1.5, 1.2), (0.9, 1.25)], _q(hq, 12, 6), lambda i, _j: "gold_dark" if i == 0 else "faction_a", smooth=False)
    mb.path([(0, ty + 1.3, deck + 1.0), (0, ty - 0.5, deck + 1.05), (0, ty - 5.0, deck + 1.35), (0, ty - 5.05, deck + 1.35), (0, ty - 5.8, deck + 1.4)], [0.62, 0.55, 0.32, 0.46, 0.46], _q(hq, 10, 5), "iron")
    mb.socket("siege_muzzle", (0, ty - 5.8, deck + 1.4))
    mb.socket("siege_pivot", (0, ty, deck + 1.05))
    # Missile racks amidships.
    for sign in (1, -1):
        rx = sign * 1.95
        ry = y_of(0.55)
        mb.box((rx, ry, deck + 0.8), (1.5, 3.8, 1.5), "faction_a")
        cols = _q(hq, 2, 1)
        rws = _q(hq, 3, 1)
        for c in range(cols):
            for r in range(rws):
                offx = (c - (cols - 1) / 2) * 0.62
                offy = (r - (rws - 1) / 2) * 1.15
                mb.tube((rx + offx, ry + offy, deck + 1.4), (rx + offx, ry + offy, deck + 2.15), 0.22, 0.03, sides=_q(hq, 6, 3), color="ember" if hq and r == 1 else "enamel")
                mb.socket(f"missile_{'L' if sign > 0 else 'R'}{c}{r}", (rx + offx, ry + offy, deck + 2.15))
    # Bridge.
    mb.box((0, y_of(0.8), deck + 1.2), (5.2, 4.8, 2.4), "enamel", top_scale=0.88)
    mb.box((0, y_of(0.82), deck + 3.1), (3.3, 2.3, 1.5), "faction_a", top_scale=0.88)
    mb.box((0, y_of(0.8), deck + 2.42), (5.5, 5.0, 0.16), "gold_dark")
    if hq:
        for x in (-1.0, 0.0, 1.0):
            mb.box((x, y_of(0.82) - 1.15, deck + 3.2), (0.7, 0.1, 0.55), "lamp")
    # Twin envelopes.
    z = deck + 9.0
    rings = _q(hq, 11, 6)
    sides = _q(hq, 12, 6)
    def bag(i, j):
        if i == 0 or i == rings - 1:
            return "faction_c"
        return "faction_a" if j % 3 == 0 else "enamel"
    for sign in (1, -1):
        gasbag(mb, sign * 3.9, 0, z, 18, 3.5, sides, rings, bag)
        if hq:
            gasbag_band(mb, sign * 3.9, 0, z, 18, 3.5, 0.5, sides, "gold_dark")
        fins(mb, sign * 3.9, 5.5, z + 0.8, 3.2, 3.0, 0.1, "faction_a")
        for y in _q(hq, (-5.0, 0.0, 5.0), (-3.5, 3.5)):
            rope(mb, (sign * width((y + length / 2) / length) * 0.85, y, deck), (sign * 3.9, y * 0.9, z - 3.2), 0.07, hq, "gold_dark")
    mb.tube((-3.9, 0, z - 2.8), (3.9, 0, z - 2.8), 0.12, sides=_q(hq, 4, 3), color="gold_dark")
    # Tall gold-and-blue banner between the bags.
    mast(mb, 0, 1.0, deck + 0.0, z + 3.2, 0.14, hq)
    mb.plate([(0, 1.1, z + 3.0), (0, 3.6, z + 2.6), (0, 1.1, z + 1.4)], 0.04, "faction_c")
    for sign, label in ((1, "L"), (-1, "R")):
        wing(mb, sign, sign * 3.3, y_of(0.36), y_of(0.6), 2.4, 4.4, 1.6, hq, color="enamel", spar="gold_dark", thick=0.1)
        nacelle(mb, sign * 5.4, y_of(0.82), 2.3, 1.4, 0.68, hq, label, root_x=sign * 3.0, color="gold_dark")
    half_at = lambda y: width((y + length / 2) / length)
    broadside(mb, [y_of(t) for t in (0.42, 0.56, 0.7)], height - 1.0, half_at, 0.95, 0.14, hq, color="gold_dark", carriage="faction_a")
    base_sockets(mb, half, deck, z, y_of(0.82), deck + 4.2)
    mb.socket("lift_core", (0, 0, 1.6))
    mb.socket("helm", (0, y_of(0.7), deck + 0.05))
    for i, t in enumerate((0.2, 0.62, 0.86)):
        mb.socket(f"fire_{i}", (0, y_of(t), deck + 0.2))


def assault_glider(mb, hq):
    """Act III boarding craft: drops onto your deck, two troopers aboard, no envelope."""
    length = 5.5
    stations = []
    for t in cosine_ts(_q(hq, 8, 4)):
        w = 0.62 * max(0.1, math.sin(math.pi * min(1.0, t * 1.05) ** 0.55))
        stations.append((-length / 2 + t * length, w, 0.2 + 0.32 * (1 - t) ** 2, 0.85))
    shell(mb, stations, _q(hq, 3, 2), lambda r: ("iron", "faction_a", "enamel")[r] if hq else ("iron", "faction_a")[r], power=0.7)
    # Long forward-swept wings: bat-like.
    for sign in (1, -1):
        mb.plate([(sign * 0.45, -0.6, 0.9), (sign * 5.0, 1.2, 1.7), (sign * 4.5, 2.2, 1.6), (sign * 3.0, 1.2, 1.3), (sign * 1.6, 2.2, 1.2), (sign * 0.4, 1.8, 0.85)], 0.05, "faction_a")
        mb.tube((sign * 0.45, -0.6, 0.9), (sign * 5.0, 1.2, 1.7), 0.05, sides=_q(hq, 4, 3), color="gold_dark")
    mb.plate([(0, 1.2, 0.9), (0, 3.2, 2.0), (0, 3.2, 1.0)], 0.05, "faction_c")
    # Grapple claw on the nose fires into the enemy deck.
    mb.tube((0, -2.6, 0.5), (0, -3.4, 0.36), 0.07, sides=_q(hq, 4, 3), color="iron")
    for i in range(_q(hq, 3, 2)):
        a = 2 * math.pi * i / _q(hq, 3, 2)
        mb.tube((0, -3.4, 0.36), (0.32 * math.cos(a), -3.86, 0.36 + 0.32 * math.sin(a)), 0.05, 0.015, sides=3, color="iron_light")
    if hq:
        mb.box((0, 0.2, 1.05), (0.72, 1.7, 0.42), "faction_c", top_scale=0.72)
        mb.box((0, 1.5, 0.9), (0.2, 0.6, 0.2), "ember")
        for sign in (1, -1):
            mb.path([(sign * 0.3, 0.3, 0.2), (sign * 0.6, 0.3, -0.1), (sign * 0.6, -1.0, -0.14)], [0.03, 0.03, 0.03], 3, "iron")
    mb.socket("rope", (0, -3.5, 0.36))
    mb.socket("seat_0", (0, -0.2, 0.9))
    mb.socket("seat_1", (0, 0.7, 0.9))
    mb.socket("thruster", (0, 1.8, 0.9))


def lifeboat(mb, hq):
    """Scuttle & Plunder: the captain you kick overboard leaves in this."""
    stations = []
    for t in cosine_ts(_q(hq, 8, 4)):
        w = 0.72 * max(0.12, math.sin(math.pi * t) ** 0.55)
        stations.append((-1.7 + 3.4 * t, w, 0.42 * abs(2 * t - 1) ** 2, 0.8 + 0.2 * abs(2 * t - 1) ** 2))
    shell(mb, stations, _q(hq, 3, 2), lambda r: ("wood_dark", "wood_mid", "faction_a")[r] if hq else ("wood_dark", "faction_a")[r], power=0.8)
    rings = _q(hq, 7, 5)
    sides = _q(hq, 8, 5)
    gasbag(mb, 0, 0, 3.3, 2.9, 1.0, sides, rings, lambda i, j: "faction_c" if i in (0, rings - 1) else ("faction_a" if j % 2 else "faction_b"))
    for x, y in ((0.5, -1.0), (-0.5, -1.0), (0.5, 1.0), (-0.5, 1.0)):
        rope(mb, (x, y, 0.85), (x * 0.8, y * 0.6, 2.5), 0.015, hq)
    if hq:
        mb.box((0, 0.2, 0.84), (1.0, 0.24, 0.05), "wood_light")
        mb.sphere((0, 1.45, 1.05), 0.08, 6, 3, "lamp", smooth=False)
    mb.socket("seat_0", (0, 0, 0.82))
    mb.socket("envelope_centre", (0, 0, 3.3))


# ---- Pirate commons for colour --------------------------------------------------------------

def scrap_raider(mb, hq):
    """Scrap-Winds bounty hunter: a barge bolted together, under mismatched salvaged bags."""
    length = 14.0
    stations = []
    for t in cosine_ts(_q(hq, 8, 4)):
        w = 2.8 * max(0.5, math.sin(math.pi * min(0.5, t)) ** 0.5) * (1 - 0.1 * t)
        keel = 0.7 * abs(2 * t - 1) ** 3
        stations.append((-length / 2 + t * length, w, keel, 2.6))
    bands = {0: "rust_dark", 1: "rust", 2: "faction_a", 3: "wood_dark"} if hq else {0: "rust_dark", 1: "rust", 2: "faction_a"}
    shell(mb, stations, _q(hq, 4, 3), lambda r: bands[r], power=0.35)
    # Salvage plates tacked over the hull.
    if hq:
        for sign in (1, -1):
            for y, z, c in ((-3.2, 1.7, "iron"), (0.4, 1.3, "steel"), (3.1, 1.8, "rust_dark")):
                mb.box((sign * 2.65, y, z), (0.12, 1.9, 1.05), c)
    # Three bags at odd sizes and angles.
    r_n = _q(hq, 8, 5)
    s_n = _q(hq, 10, 6)
    for x, y, z, ln, r, a, b in ((-1.9, -1.2, 8.3, 11.0, 2.9, "faction_b", "canvas_dark"), (2.6, 0.9, 7.3, 8.5, 2.2, "faction_a", "rust_dark"), (0.1, 4.3, 10.2, 6.0, 1.7, "cloth_brown", "faction_c")):
        gasbag(mb, x, y, z, ln, r, s_n, r_n, striped(a, b, "iron", r_n))
        for sign in (1, -1):
            rope(mb, (x * 0.6 + sign * 1.0, y, 2.7), (x + sign * 0.8, y, z - r * 0.85), 0.05, hq, "iron")
    # Crane, cabin, boiler stack.
    mb.box((0, 4.4, 3.6), (3.2, 3.0, 2.0), "rust_dark", top_scale=0.86)
    if hq:
        mb.box((0, 2.86, 3.8), (1.5, 0.1, 0.6), "ember")
    mb.tube((1.1, 5.0, 4.5), (1.15, 5.2, 6.8), 0.28, 0.33, sides=_q(hq, 6, 4), color="iron")
    mb.tube((-1.2, -3.6, 2.6), (-1.2, -3.6, 5.0), 0.12, sides=_q(hq, 5, 3), color="iron")
    mb.tube((-1.2, -3.6, 4.8), (1.5, -6.6, 5.3), 0.09, sides=_q(hq, 4, 3), color="iron")
    mb.tube((1.5, -6.6, 5.3), (1.5, -6.6, 3.8), 0.022, sides=3, color="rope")
    mb.socket("hook", (1.5, -6.6, 3.8))
    for sign, label in ((1, "L"), (-1, "R")):
        nacelle(mb, sign * 4.0, 3.7, 1.5, 1.1, 0.6, hq, label, root_x=sign * 2.5, color="iron_light")
    half_at = lambda _y: 2.72
    broadside(mb, (-2.6, 0.7), 1.65, half_at, 0.75, 0.12, hq)
    base_sockets(mb, 2.8, 2.6, 8.3, 5.2, 6.9)
    mb.socket("lift_core", (0, 0, 1.2))


def smuggler_runner(mb, hq):
    """Jetstream smuggler. Lyra's rescue mission opens with one of these going down in a cyclone."""
    length = 15.0
    stations = []
    for t in cosine_ts(_q(hq, 10, 6)):
        w = 2.1 * max(0.06, math.sin(math.pi * min(1.0, t * 1.03) ** 0.65) ** 0.7)
        stations.append((-length / 2 + t * length, w, 1.2 * abs(2 * t - 1) ** 2.2, 2.3 + 0.7 * (1 - t) ** 3))
    bands = {0: "wood_dark", 1: "faction_c", 2: "faction_a", 3: "wood_light", 4: "faction_b"} if hq else {0: "wood_dark", 1: "faction_a", 2: "faction_b"}
    shell(mb, stations, _q(hq, 5, 3), lambda r: bands[r], power=0.65)
    # Twin slim side-by-side bags: narrow enough to thread storm-gaps.
    r_n = _q(hq, 10, 6)
    s_n = _q(hq, 10, 6)
    z = 8.0
    for sign in (1, -1):
        gasbag(mb, sign * 2.2, 0.3, z, 14.0, 2.2, s_n, r_n, striped("faction_a", "faction_b", "faction_c", r_n), flat=0.9)
        for y in _q(hq, (-3.8, 0.0, 3.8), (-2.5, 2.5)):
            rope(mb, (sign * 1.3, y, 2.4), (sign * 2.0, y, z - 1.85), 0.045, hq)
    mb.box((0, 0.3, 3.4), (3.0, 4.4, 1.9), "wood_mid", top_scale=0.9)
    mb.box((0, 0.3, 4.42), (3.2, 4.6, 0.14), "faction_c")
    if hq:
        for y in (-1.2, 0.3, 1.8):
            for sign in (1, -1):
                mb.box((sign * 1.46, y, 3.5), (0.1, 0.8, 0.65), "lamp")
        # Deck cargo: the reason you'd board this ship at all.
        for x, y in ((-0.8, -3.6), (0.7, -3.7), (0.0, 4.2)):
            mb.box((x, y, 2.72), (0.8, 0.8, 0.8), "wood_light")
    mb.tube((0, -6.8, 3.2), (0, -11.0, 4.0), 0.16, 0.02, sides=_q(hq, 5, 3), color="brass")
    mb.plate([(0, -4.5, 2.6), (0, -7.6, 5.7), (0, -5.5, 6.7)], 0.03, "faction_b")
    for sign, label in ((1, "L"), (-1, "R")):
        wing(mb, sign, sign * 1.9, -2.0, 3.0, 1.3, 3.2, 1.0, hq, color="faction_a", thick=0.06, ribs=1)
        nacelle(mb, sign * 3.2, 5.0, 1.8, 1.0, 0.45, hq, label, root_x=sign * 1.4, color="brass")
    mb.plate([(0, 7.0, 2.2), (0, 8.5, 1.9), (0, 8.6, 0.6), (0, 7.4, 0.5)], 0.08, "wood_dark")
    half_at = lambda _y: 2.05
    broadside(mb, (-1.8, 2.0), 1.65, half_at, 0.75, 0.09, hq, color="brass")
    base_sockets(mb, 2.1, 2.3, z, 5.0, 4.4)
    mb.socket("lift_core", (0, 0, 1.3))
    mb.socket("rescue_point", (0, 0, 4.5))
