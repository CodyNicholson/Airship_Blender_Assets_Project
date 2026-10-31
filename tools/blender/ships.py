"""Airship generator. Bow faces Blender -Y, which is glTF +Z (the glTF model front)."""
import math
from dataclasses import dataclass

from mathutils import Matrix

SHIPS = {}


@dataclass
class ShipSpec:
    length: float
    width: float
    hull_height: float
    envelope_radius: float
    envelope_length: float
    envelopes: int  # 1 is centred; 2 sit side by side.
    masts: int
    cannons_per_side: int
    engines_per_side: int
    stations_hq: int
    stations_lq: int
    fore_castle: bool


SHIPS["Sloop"] = ShipSpec(10, 3.0, 1.9, 1.9, 9.0, 1, 0, 1, 1, 12, 6, False)
SHIPS["Brigantine"] = ShipSpec(16, 4.6, 2.9, 2.9, 14.5, 1, 1, 3, 1, 14, 7, False)
SHIPS["Galleon"] = ShipSpec(24, 6.8, 4.1, 3.2, 20.0, 2, 2, 5, 2, 16, 8, True)


def _hull_width(spec, t):
    half = spec.width / 2
    if t < 0.42:
        return half * max(0.05, math.sqrt(max(0.0, 1 - (1 - t / 0.42) ** 2)))
    if t > 0.72:
        return half * (1 - 0.3 * ((t - 0.72) / 0.28) ** 2)
    return half


def _hull_keel(spec, t):
    if t < 0.32:
        return 0.55 * spec.hull_height * (1 - t / 0.32) ** 2
    if t > 0.7:
        return 0.35 * spec.hull_height * ((t - 0.7) / 0.3) ** 2
    return 0.0


def _hull_deck(spec, t):
    z = spec.hull_height
    if t < 0.35:
        z += 0.3 * spec.hull_height * (1 - t / 0.35) ** 2
    if t > 0.6:
        z += 0.25 * spec.hull_height * ((t - 0.6) / 0.4) ** 2
    return z


def _y_at(spec, t):
    return -spec.length / 2 + t * spec.length


def _hull(mb, spec, hq):
    stations = spec.stations_hq if hq else spec.stations_lq
    rows = 5 if hq else 3
    rings = []
    for i in range(stations + 1):
        t = 0.5 - 0.5 * math.cos(math.pi * i / stations)
        y, w, keel, deck = _y_at(spec, t), _hull_width(spec, t), _hull_keel(spec, t), _hull_deck(spec, t)
        side = []
        for j in range(rows + 1):
            phi = (j / rows) * math.pi / 2
            side.append((w * math.sin(phi) ** 0.75, y, keel + (deck - keel) * (1 - math.cos(phi))))
        port = [(-x, yy, z) for x, yy, z in reversed(side[1:])]
        rings.append(side + port)

    def colour(_i, j):
        if j == rows:
            return "wood_deck"
        row = j if j < rows else 2 * rows - j
        if row == rows - 1:
            return "faction_a"
        if hq and row == rows - 2:
            return "wood_light"
        if row == 0:
            return "wood_dark"
        return "wood_mid" if row % 2 else "wood_dark"

    mb.loft(rings, colour)


def _rails(mb, spec, hq):
    """Bulwark along both deck edges."""
    rail_h = spec.hull_height * 0.17
    count = 10 if hq else 4
    for sign in (1, -1):
        points = []
        for i in range(count + 1):
            t = 0.06 + 0.88 * i / count
            points.append((sign * _hull_width(spec, t) * 0.97, _y_at(spec, t), _hull_deck(spec, t) + rail_h))
        mb.path(points, [rail_h * 0.28] * len(points), 4 if hq else 3, "wood_dark")
        if hq:
            for x, y, z in points:
                mb.tube((x, y, z - rail_h), (x, y, z), rail_h * 0.16, sides=4, color="wood_mid")


def _sterncastle(mb, spec, hq):
    t0, t1 = 0.74, 0.985
    y0, y1 = _y_at(spec, t0), _y_at(spec, t1)
    half = _hull_width(spec, (t0 + t1) / 2) * 0.86
    base = _hull_deck(spec, t0)
    height = spec.hull_height * 0.72
    mb.box((0, (y0 + y1) / 2, base + height / 2 - 0.1), (half * 2, y1 - y0, height), "wood_red", top_scale=0.92)
    mb.box((0, (y0 + y1) / 2, base + height + 0.02), (half * 2.1, (y1 - y0) * 1.05, height * 0.1), "wood_dark")
    if hq:
        panes = max(2, int(spec.width))
        for i in range(panes):
            x = (i + 0.5 - panes / 2) * (half * 1.5 / panes)
            size = (half * 1.1 / panes, 0.1, height * 0.42)
            mb.box((x, y1 + 0.02, base + height * 0.5), size, "lamp")
            for sign in (1, -1):
                side_y = y0 + (i + 0.5) * (y1 - y0) / panes
                mb.box((sign * half * 0.97, side_y, base + height * 0.5), (0.1, size[0], height * 0.38), "glass")
    if spec.fore_castle:
        fy0, fy1 = _y_at(spec, 0.12), _y_at(spec, 0.27)
        half_f = _hull_width(spec, 0.2) * 0.8
        z = _hull_deck(spec, 0.27)
        mb.box((0, (fy0 + fy1) / 2, z + height * 0.22), (half_f * 2, fy1 - fy0, height * 0.55), "wood_red", top_scale=0.85)


def _bow(mb, spec, hq):
    z = _hull_deck(spec, 0.02)
    start = (0, _y_at(spec, 0.03), z - spec.hull_height * 0.2)
    tip = (0, _y_at(spec, 0.0) - spec.length * 0.16, z + spec.hull_height * 0.4)
    mb.tube(start, tip, spec.hull_height * 0.09, spec.hull_height * 0.02, sides=6 if hq else 3, color="brass" if hq else "wood_dark")
    if hq:
        ram_y = _y_at(spec, 0.0)
        ram_z = _hull_keel(spec, 0.04) + 0.1 * spec.hull_height
        mb.tube((0, ram_y + spec.length * 0.08, ram_z), (0, ram_y - spec.length * 0.05, ram_z - 0.05), spec.hull_height * 0.11, 0.02, sides=6, color="iron_light")


def _envelope(mb, spec, hq, x_offset, z_centre):
    sides = 16 if hq else 8
    rings = 12 if hq else 6
    r = spec.envelope_radius
    half = spec.envelope_length / 2

    def colour(i, j):
        if i == 0 or i == rings - 1:
            return "faction_c"
        return "faction_a" if j % 2 else "faction_b"

    profile = []
    for i in range(rings):
        # Cosine spacing packs rings at the tips, so the ends close to a point instead of a flat disc.
        s = 0.5 - 0.5 * math.cos(math.pi * (i + 0.5) / rings)
        # Nose towards -Y is fuller than the tail, which reads as a fast teardrop.
        radius = r * max(0.08, math.sin(math.pi * s ** 0.85) ** 0.72)
        profile.append((radius, -half + 2 * half * s))
    to_y = Matrix.Translation((x_offset, 0, z_centre)) @ Matrix.Rotation(-math.pi / 2, 4, "X")
    with mb.xf(to_y):
        mb.lathe(profile, sides, colour, smooth=True, phase=math.pi / sides)
        if hq:
            for s in (0.3, 0.7):
                radius = r * max(0.08, math.sin(math.pi * s ** 0.85) ** 0.72)
                z = -half + 2 * half * s
                band = [(radius * 0.99, z - 0.1), (radius * 1.025, z - 0.07), (radius * 1.025, z + 0.07), (radius * 0.99, z + 0.1)]
                mb.lathe(band, sides, "leather_dark", smooth=False, caps=(False, False), phase=math.pi / sides)

    # Tail fins on the envelope.
    tail_y = half * 0.62
    fin_len = spec.envelope_length * 0.2
    fin_span = r * 0.95
    fin_thick = 0.08 + spec.length * 0.004
    top = z_centre + r * 0.45
    mb.plate(
        [(x_offset, tail_y, top), (x_offset, tail_y + fin_len, top + fin_span), (x_offset, tail_y + fin_len, top), (x_offset, tail_y + fin_len * 0.55, top - 0.1)],
        fin_thick,
        "faction_c",
    )
    for sign in (1, -1):
        root = x_offset + sign * r * 0.45
        mb.plate(
            [(root, tail_y, z_centre), (root + sign * fin_span, tail_y + fin_len, z_centre), (root, tail_y + fin_len, z_centre), (root - sign * 0.1, tail_y + fin_len * 0.55, z_centre)],
            fin_thick,
            "faction_c",
        )


def _lift_rig(mb, spec, hq, x_offset, z_centre):
    """Struts tying the hull to the envelope's belly."""
    r = spec.envelope_radius
    samples = (0.2, 0.42, 0.62, 0.8) if hq else (0.28, 0.72)
    for t in samples:
        y = _y_at(spec, t)
        env_y = y * 0.85
        for sign in (1, -1):
            hull_x = sign * _hull_width(spec, t) * 0.92
            if spec.envelopes == 2 and sign * x_offset < 0:
                hull_x = sign * _hull_width(spec, t) * 0.15  # Inner strut of a twin envelope.
            env_x = x_offset + sign * r * 0.4
            bottom = (hull_x, y, _hull_deck(spec, t))
            top = (env_x, env_y, z_centre - r * 0.86)
            mb.tube(bottom, top, spec.length * 0.0045 + 0.012, sides=4 if hq else 3, color="rope")


def _wings(mb, spec, hq):
    """Fixed side fins, which give the ship its flying silhouette."""
    y0, y1 = _y_at(spec, 0.33), _y_at(spec, 0.6)
    z = spec.hull_height * 0.72
    span = spec.width * 0.82
    for sign in (1, -1):
        root = sign * _hull_width(spec, 0.45) * 0.85
        tip = root + sign * span
        outline = [(root, y0, z), (tip, y0 + (y1 - y0) * 0.55, z + span * 0.3), (tip, y1, z + span * 0.26), (root, y1, z - 0.08)]
        mb.plate(outline, 0.07 + spec.length * 0.002, "faction_a")
        mb.tube((root, y0, z), (tip, y0 + (y1 - y0) * 0.55, z + span * 0.3), 0.05 + spec.length * 0.0035, sides=5 if hq else 3, color="wood_dark")
        if hq:
            for rib in (0.35, 0.68):
                ry = y0 + (y1 - y0) * (0.55 + 0.45 * rib)
                front = (root + sign * span * rib, y0 + (y1 - y0) * 0.55 * rib, z + span * 0.3 * rib)
                back = (root, ry, z)
                mb.tube(front, back, 0.03 + spec.length * 0.002, sides=3, color="wood_dark")


def _rudder(mb, spec, hq):
    y = _y_at(spec, 0.995)
    z1 = _hull_deck(spec, 0.97)
    z0 = _hull_keel(spec, 1.0) - spec.hull_height * 0.18
    depth = spec.length * 0.055
    outline = [(0, y, z1 - spec.hull_height * 0.3), (0, y + depth * 0.55, z1 - spec.hull_height * 0.45), (0, y + depth, z0 + spec.hull_height * 0.2), (0, y + depth * 0.7, z0), (0, y, z0 + spec.hull_height * 0.1)]
    mb.plate(outline, 0.08 + spec.length * 0.003, "wood_dark")
    if hq:
        band = (0.04 + spec.length * 0.006, depth * 0.8, 0.1)
        mb.box((0, y + depth * 0.42, (z0 + z1) / 2), band, "iron")


def _engines(mb, spec, hq):
    for index in range(spec.engines_per_side):
        t = 0.76 - index * 0.28
        y = _y_at(spec, t)
        z = spec.hull_height * (0.62 + 0.28 * index)
        for sign, label in ((1, "L"), (-1, "R")):
            hull_x = sign * _hull_width(spec, t) * 0.92
            x = hull_x + sign * spec.width * 0.34
            nacelle_len = spec.length * 0.09
            r = spec.hull_height * 0.17
            mb.tube((hull_x, y, z), (x, y, z), r * 0.32, sides=4 if hq else 3, color="iron")
            if hq:
                mb.path(
                    [(x, y - nacelle_len, z), (x, y - nacelle_len * 0.5, z), (x, y + nacelle_len * 0.5, z), (x, y + nacelle_len, z)],
                    [r * 0.35, r, r, r * 0.55],
                    8,
                    "brass",
                    smooth=True,
                )
            else:
                mb.tube((x, y - nacelle_len, z), (x, y + nacelle_len, z), r * 0.75, r * 0.6, sides=5, color="brass")
            mb.socket(f"propeller_{label}{index}", (x, y + nacelle_len + 0.02, z))


def _cannons(mb, spec, hq):
    count = spec.cannons_per_side
    if count == 0:
        return
    for i in range(count):
        t = 0.32 + 0.38 * (i + 0.5) / count
        y = _y_at(spec, t)
        z = _hull_deck(spec, t) - spec.hull_height * 0.32
        half = _hull_width(spec, t)
        r = 0.09 + spec.length * 0.006
        barrel = 0.5 + spec.length * 0.03
        for sign, label in ((1, "L"), (-1, "R")):
            x0 = sign * (half * 0.9)
            x1 = x0 + sign * barrel
            if hq:
                mb.box((x0, y, z), (0.16, r * 3.4, r * 3.4), "wood_dark")
                mb.path(
                    [(x0, y, z), (x1 - sign * 0.12, y, z), (x1 - sign * 0.1, y, z), (x1, y, z)],
                    [r, r * 0.8, r * 1.15, r * 1.15],
                    8,
                    "iron",
                )
            else:
                mb.tube((x0, y, z), (x1, y, z), r, r, sides=5, color="iron")
            mb.socket(f"muzzle_{label}{i}", (x1, y, z))


def _masts(mb, spec, hq, z_centre):
    """A single envelope sits over the mast, so the rig fits in the gap; twins leave it open above."""
    for i in range(spec.masts):
        t = 0.3 + 0.3 * i if spec.masts > 1 else 0.44
        y = _y_at(spec, t)
        base = _hull_deck(spec, t)
        belly = z_centre - spec.envelope_radius * 0.92
        height = (belly - base) if spec.envelopes == 1 else (z_centre + spec.envelope_radius * 1.25 - base)
        r = spec.length * 0.012
        x = 0.0
        mb.tube((x, y, base - 0.1), (x, y, base + height), r, r * 0.55, sides=6 if hq else 4, color="wood_mid")
        spar_z = base + height * 0.86
        spar = spec.width * 0.42
        mb.tube((-spar, y, spar_z), (spar, y, spar_z), r * 0.5, sides=4 if hq else 3, color="wood_dark")
        drop = height * 0.62
        mb.plate([(-spar, y + 0.02, spar_z), (spar, y + 0.02, spar_z), (spar * 0.85, y - 0.18, spar_z - drop), (-spar * 0.85, y - 0.18, spar_z - drop)], 0.05, "canvas")
        if hq and spec.envelopes > 1:
            mb.lathe([(r * 2.6, base + height * 0.9), (r * 3.4, base + height * 0.96)], 8, "wood_dark", smooth=False)
        if spec.envelopes > 1:
            top = base + height
            flag = spec.width * 0.28
            mb.plate([(0, y, top), (0, y + flag, top - flag * 0.22), (0, y, top - flag * 0.45)], 0.03, "faction_a")


def _deck_dressing(mb, spec):
    """HQ only: hatch, wheel and lantern that sell the scale when the camera is near."""
    y = _y_at(spec, 0.56)
    z = _hull_deck(spec, 0.56)
    size = spec.width * 0.2
    mb.box((0, y, z + 0.03), (size, size * 1.3, 0.1), "iron")
    wheel_y = _y_at(spec, 0.7)
    wheel_z = _hull_deck(spec, 0.7)
    mb.tube((0, wheel_y, wheel_z), (0, wheel_y, wheel_z + 0.7), 0.06, sides=4, color="wood_dark")
    with mb.xf(Matrix.Translation((0, wheel_y - 0.08, wheel_z + 0.85)) @ Matrix.Rotation(math.pi / 2, 4, "X")):
        mb.lathe([(0.3, -0.03), (0.3, 0.03)], 8, "wood_light", smooth=False)
    for sign in (1, -1):
        x = sign * _hull_width(spec, 0.93) * 0.75
        lamp_y = _y_at(spec, 0.99)
        lamp_z = _hull_deck(spec, 0.9) + spec.hull_height * 0.78
        mb.sphere((x, lamp_y + 0.15, lamp_z), 0.13, 6, 4, "lamp")


def build_ship(mb, name, hq):
    spec = SHIPS[name]
    _hull(mb, spec, hq)
    _rails(mb, spec, hq)
    _sterncastle(mb, spec, hq)
    _bow(mb, spec, hq)

    z_centre = spec.hull_height + spec.envelope_radius * 1.75
    offsets = (0.0,) if spec.envelopes == 1 else (spec.envelope_radius * 1.02, -spec.envelope_radius * 1.02)
    for x_offset in offsets:
        _envelope(mb, spec, hq, x_offset, z_centre)
        _lift_rig(mb, spec, hq, x_offset, z_centre)

    _wings(mb, spec, hq)
    _rudder(mb, spec, hq)
    _engines(mb, spec, hq)
    _cannons(mb, spec, hq)
    _masts(mb, spec, hq, z_centre)
    if hq:
        _deck_dressing(mb, spec)

    deck_z = _hull_deck(spec, 0.5)
    half = _hull_width(spec, 0.5)
    mb.socket("deck_centre", (0, 0, deck_z))
    mb.socket("boarding_L", (half, 0, deck_z))
    mb.socket("boarding_R", (-half, 0, deck_z))
    mb.socket("smoke_vent", (0, _y_at(spec, 0.8), deck_z + spec.hull_height))
    mb.socket("envelope_centre", (0, 0, z_centre))
