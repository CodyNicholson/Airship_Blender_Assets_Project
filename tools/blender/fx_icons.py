"""UI icons, in the same comic ink style as the portraits.

Two kinds, both transparent PNGs:
  * Model icons (ships, items, ammo, modules, weapons) are rendered from the real meshes, so what
    the player picks up is what they see on the deck.
  * Glyph icons (HUD buttons, targeting, hazards, abilities) are drawn from signed distance fields,
    so they stay crisp at both sizes. HUD and target glyphs are near-white: tint them in the UI.

    fx_icons.generate_all(scratch_dir)   # inside Blender
"""
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

import catalog
import fx_catalog
from fx_image import downsample, ink_outline, smoothstep, write_png
import kit
import palette
import portraits

WHITE = (0.97, 0.96, 0.92)
INK = (0.03, 0.02, 0.04)
GOLD = (0.96, 0.75, 0.25)
GOLD_DARK = (0.62, 0.42, 0.12)
RED = (0.84, 0.18, 0.16)
CYAN = (0.28, 0.88, 0.91)
ORANGE = (1.0, 0.56, 0.12)
GREEN = (0.56, 0.68, 0.26)
VIOLET = (0.62, 0.36, 1.0)
STEEL = (0.62, 0.66, 0.72)
BLUE = (0.3, 0.55, 0.92)

# Ability and story glyphs sit on a coloured medal, in their character's portrait colour.
MEDALS = {
    "Ability_RookPrecision": (0.2, 0.28, 0.48),
    "Ability_LyraWinds": (0.16, 0.5, 0.62),
    "Ability_LyraCloudStealth": (0.16, 0.5, 0.62),
    "Ability_SableSabotage": (0.24, 0.1, 0.27),
    "Ability_ThorneOverdrive": (0.12, 0.42, 0.47),
    "Ability_ThornePatch": (0.12, 0.42, 0.47),
    "Ability_MorrowRadar": (0.18, 0.34, 0.26),
    "Choice_PressGang": (0.55, 0.13, 0.15),
    "Hazard_Lightning": (0.13, 0.11, 0.3),
    "Hazard_Updraft": (0.14, 0.42, 0.56),
    "Hazard_ToxicCloud": (0.24, 0.27, 0.13),
    "Hazard_WindCurrent": (0.16, 0.5, 0.62),
}
CHOICE_MEDAL = {"Choice_SeizeHelm": (0.1, 0.24, 0.4), "Choice_ScuttlePlunder": (0.3, 0.13, 0.08)}


class G:
    """Signed-distance shapes on a pixel grid, in units where the icon spans -1..1, y up."""

    def __init__(self, x, y):
        self.x, self.y = x, y

    def circle(self, cx, cy, r):
        return np.hypot(self.x - cx, self.y - cy) - r

    def ring(self, cx, cy, r, t):
        return np.abs(self.circle(cx, cy, r)) - t

    def box(self, cx, cy, hx, hy, rot=0.0, rnd=0.0):
        c, s = np.cos(rot), np.sin(rot)
        dx, dy = self.x - cx, self.y - cy
        qx, qy = np.abs(dx * c + dy * s) - hx + rnd, np.abs(-dx * s + dy * c) - hy + rnd
        return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - rnd

    def line(self, ax, ay, bx, by, r):
        dx, dy = bx - ax, by - ay
        h = np.clip(((self.x - ax) * dx + (self.y - ay) * dy) / (dx * dx + dy * dy), 0, 1)
        return np.hypot(self.x - ax - dx * h, self.y - ay - dy * h) - r

    def poly(self, *points):
        pts = np.array(points, dtype=np.float32)
        d = np.full_like(self.x, 1e9)
        inside = np.zeros_like(self.x, dtype=bool)
        j = len(pts) - 1
        for i in range(len(pts)):
            ex, ey = pts[j] - pts[i]
            wx, wy = self.x - pts[i][0], self.y - pts[i][1]
            h = np.clip((wx * ex + wy * ey) / (ex * ex + ey * ey), 0, 1)
            d = np.minimum(d, (wx - ex * h) ** 2 + (wy - ey * h) ** 2)
            # Even-odd rule, with y-up coordinates on the grid.
            crosses = (self.y >= pts[i][1]) != (self.y >= pts[j][1])
            at_x = (pts[j][0] - pts[i][0]) * (self.y - pts[i][1]) / (pts[j][1] - pts[i][1] + 1e-9) + pts[i][0]
            inside ^= crosses & (self.x < at_x)
            j = i
        return np.sqrt(d) * np.where(inside, -1, 1)

    def star(self, cx, cy, outer, inner, n, rot=0.0):
        pts = []
        for i in range(n * 2):
            a = rot + np.pi * i / n
            r = outer if i % 2 == 0 else inner
            pts.append((cx + r * np.sin(a), cy + r * np.cos(a)))
        return self.poly(*pts)


def union(*shapes):
    out = shapes[0]
    for shape in shapes[1:]:
        out = np.minimum(out, shape)
    return out


def cut(a, b):
    return np.maximum(a, -b)


def clip(a, b):
    return np.maximum(a, b)


def _brackets(g):
    """The targeting frame shared by every Target_ icon."""
    e, n, t = 0.92, 0.3, 0.055
    parts = []
    for sx in (1, -1):
        for sy in (1, -1):
            parts.append(g.line(sx * e, sy * e, sx * (e - n), sy * e, t))
            parts.append(g.line(sx * e, sy * e, sx * e, sy * (e - n), t))
    return union(*parts)


def _chevron(g, cx, cy, size, up=True, t=0.11):
    s = 1 if up else -1
    return union(g.line(cx - size, cy - s * size * 0.55, cx, cy + s * size * 0.45, t), g.line(cx + size, cy - s * size * 0.55, cx, cy + s * size * 0.45, t))


def _side_chevron(g, cx, cy, size, right=True, t=0.11):
    s = 1 if right else -1
    return union(g.line(cx - s * size * 0.55, cy - size, cx + s * size * 0.45, cy, t), g.line(cx - s * size * 0.55, cy + size, cx + s * size * 0.45, cy, t))


def _skull(g, cx=0.0, cy=0.1, s=1.0):
    head = union(g.circle(cx, cy + 0.08 * s, 0.52 * s), g.box(cx, cy - 0.38 * s, 0.3 * s, 0.2 * s, rnd=0.06 * s))
    holes = union(g.circle(cx - 0.2 * s, cy + 0.04 * s, 0.14 * s), g.circle(cx + 0.2 * s, cy + 0.04 * s, 0.14 * s), g.poly((cx, cy - 0.04 * s), (cx + 0.07 * s, cy - 0.2 * s), (cx - 0.07 * s, cy - 0.2 * s)))
    teeth = union(g.box(cx - 0.11 * s, cy - 0.46 * s, 0.018 * s, 0.13 * s), g.box(cx + 0.11 * s, cy - 0.46 * s, 0.018 * s, 0.13 * s), g.box(cx, cy - 0.46 * s, 0.018 * s, 0.13 * s))
    return cut(cut(head, holes), teeth)


def _sword(g, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    n = np.hypot(dx, dy)
    ux, uy = dx / n, dy / n
    px, py = -uy, ux
    gx, gy = ax + ux * 0.32, ay + uy * 0.32
    blade = g.poly((gx + px * 0.075, gy + py * 0.075), (bx - ux * 0.25 + px * 0.07, by - uy * 0.25 + py * 0.07), (bx, by), (bx - ux * 0.25 - px * 0.05, by - uy * 0.25 - py * 0.05), (gx - px * 0.075, gy - py * 0.075))
    hilt = union(g.line(ax, ay, gx, gy, 0.05), g.line(gx + px * 0.2, gy + py * 0.2, gx - px * 0.2, gy - py * 0.2, 0.055))
    return union(blade, hilt)


def _bolt(g, s=1.0):
    return g.poly((0.12 * s, 0.92 * s), (-0.48 * s, -0.06 * s), (-0.08 * s, -0.06 * s), (-0.22 * s, -0.92 * s), (0.5 * s, 0.2 * s), (0.08 * s, 0.2 * s), (0.34 * s, 0.92 * s))


def _bust(g, cx=0.0, s=1.0):
    return union(g.circle(cx, 0.32 * s, 0.32 * s), clip(g.circle(cx, -0.72 * s, 0.72 * s), g.box(cx, -0.45 * s, 1.0 * s, 0.5 * s)))


def _ship(g, cy=0.0):
    return union(
        g.poly((-0.86, 0.08 + cy), (0.86, 0.08 + cy), (0.56, -0.42 + cy), (-0.56, -0.42 + cy)),
        g.box(0, 0.62 + cy, 0.56, 0.3, rnd=0.28),
        g.line(-0.3, 0.1 + cy, -0.26, 0.36 + cy, 0.035),
        g.line(0.3, 0.1 + cy, 0.26, 0.36 + cy, 0.035),
    )


def _cloud(g, cy=0.0):
    return union(g.circle(-0.42, cy, 0.3), g.circle(0.0, 0.18 + cy, 0.42), g.circle(0.44, -0.02 + cy, 0.28), g.box(0, -0.17 + cy, 0.62, 0.16, rnd=0.15))


def _propeller(g):
    blades = [g.poly((0, 0), (0.14 * np.sin(a + 0.55), 0.14 * np.cos(a + 0.55)), (0.58 * np.sin(a + 0.32), 0.58 * np.cos(a + 0.32)), (0.62 * np.sin(a - 0.06), 0.62 * np.cos(a - 0.06))) for a in (0.2, 2.3, 4.4)]
    return union(*blades, g.circle(0, 0, 0.13))


def _gear(g):
    teeth = [g.box(0, 0, 0.14, 0.82, rot=np.pi * i / 4) for i in range(4)]
    return cut(union(g.circle(0, 0, 0.62), *teeth), g.circle(0, 0, 0.26))


def _swirl(g, offset=0.0):
    a = g.line(-0.78, 0.2 + offset, 0.28, 0.2 + offset, 0.075)
    b = g.line(-0.78, -0.32 + offset, 0.42, -0.32 + offset, 0.075)
    tip = clip(g.ring(0.28, 0.42 + offset, 0.22, 0.075), g.box(0.45, 0.42 + offset, 0.25, 0.4))
    tip2 = clip(g.ring(0.42, -0.08 + offset, 0.24, 0.075), g.box(0.6, -0.08 + offset, 0.26, 0.4))
    return union(a, b, tip, tip2)


def _crystal(g, s=1.0, cy=0.0):
    return g.poly((0, 0.86 * s + cy), (0.42 * s, 0.32 * s + cy), (0.3 * s, -0.5 * s + cy), (0, -0.84 * s + cy), (-0.3 * s, -0.5 * s + cy), (-0.42 * s, 0.32 * s + cy))


def glyph_layers(name, g):
    """Painter's order list of (sdf, colour)."""
    if name == "Hud_FireBroadside":
        barrel = g.poly((-0.72, -0.06), (-0.6, -0.28), (0.5, 0.24), (0.42, 0.42))
        return [(g.star(0.68, 0.46, 0.34, 0.14, 7, 0.2), ORANGE), (union(barrel, g.line(0.52, 0.18, 0.4, 0.46, 0.05)), WHITE), (g.circle(-0.34, -0.5, 0.27), STEEL), (g.circle(-0.34, -0.5, 0.09), INK)]
    if name == "Hud_Grapple":
        arm = lambda sign: union(g.line(0, -0.42, sign * 0.5, -0.5, 0.07), g.line(sign * 0.5, -0.5, sign * 0.68, -0.08, 0.055), g.poly((sign * 0.68, 0.14), (sign * 0.8, -0.14), (sign * 0.56, -0.14)))
        return [(union(g.line(0, 0.62, 0, -0.42, 0.075), arm(1), arm(-1), g.ring(0, 0.76, 0.12, 0.05), g.poly((0, -0.84), (-0.11, -0.42), (0.11, -0.42))), WHITE)]
    if name == "Hud_Board":
        return [(_sword(g, -0.78, -0.78, 0.82, 0.82), WHITE), (_sword(g, 0.78, -0.78, -0.82, 0.82), WHITE)]
    if name == "Hud_Defend":
        shield = g.poly((0, 0.9), (0.72, 0.64), (0.66, -0.06), (0, -0.92), (-0.66, -0.06), (-0.72, 0.64))
        return [(shield, WHITE), (union(g.box(0, 0.12, 0.1, 0.46), g.box(0, 0.22, 0.34, 0.1)), STEEL)]
    if name == "Hud_Repair":
        head = cut(g.circle(0.46, 0.46, 0.38), g.poly((0.46, 0.46), (0.98, 0.72), (0.72, 0.98)))
        return [(union(g.line(-0.6, -0.6, 0.3, 0.3, 0.15), head, g.circle(-0.62, -0.62, 0.21)), WHITE), (g.circle(-0.62, -0.62, 0.08), INK)]
    if name in ("Hud_AltitudeUp", "Hud_AltitudeDown"):
        up = name == "Hud_AltitudeUp"
        s = 1 if up else -1
        balloon = union(g.circle(0, s * -0.02 - (0.22 if not up else 0.22), 0.42), g.poly((-0.26, -0.56), (0.26, -0.56), (0.15, -0.8), (-0.15, -0.8)))
        return [(union(_chevron(g, 0, 0.68, 0.34, up=up, t=0.09), _chevron(g, 0, 0.38, 0.28, up=up, t=0.08)), WHITE), (balloon, STEEL)]
    if name in ("Hud_ThrottleUp", "Hud_ThrottleDown"):
        right = name == "Hud_ThrottleUp"
        return [(union(_side_chevron(g, -0.44, 0, 0.52, right), _side_chevron(g, 0.12, 0, 0.52, right), _side_chevron(g, 0.66, 0, 0.3, right, t=0.08) if right else _side_chevron(g, -0.82, 0, 0.3, right, t=0.08)), WHITE)]
    if name == "Hud_Hull":
        return [(_ship(g, -0.28), WHITE)]
    if name == "Hud_Crew":
        return [(_bust(g, -0.46, 0.76), STEEL), (_bust(g, 0.46, 0.76), STEEL), (_bust(g, 0, 1.0), WHITE)]
    if name == "Hud_Comms":
        bubble = union(g.box(0, 0.16, 0.84, 0.58, rnd=0.24), g.poly((-0.44, -0.3), (-0.08, -0.3), (-0.44, -0.84)))
        wave = union(g.box(-0.42, 0.16, 0.06, 0.12, rnd=0.05), g.box(-0.14, 0.16, 0.06, 0.28, rnd=0.05), g.box(0.14, 0.16, 0.06, 0.2, rnd=0.05), g.box(0.42, 0.16, 0.06, 0.34, rnd=0.05))
        return [(bubble, WHITE), (wave, INK)]
    if name == "Hud_Timer":
        return [(union(g.circle(0, -0.08, 0.76), g.box(0, 0.84, 0.2, 0.09)), WHITE), (g.circle(0, -0.08, 0.58), INK), (union(g.line(0, -0.08, 0, 0.32, 0.07), g.line(0, -0.08, 0.26, -0.24, 0.07)), WHITE)]
    if name == "Hud_Map":
        sheet = g.poly((-0.86, 0.68), (-0.28, 0.84), (0.28, 0.66), (0.86, 0.84), (0.86, -0.68), (0.28, -0.84), (-0.28, -0.66), (-0.86, -0.84))
        return [(sheet, WHITE), (union(g.line(-0.28, 0.76, -0.28, -0.6, 0.02), g.line(0.28, 0.6, 0.28, -0.76, 0.02)), STEEL), (union(g.line(0.34, 0.34, 0.58, 0.1, 0.05), g.line(0.58, 0.34, 0.34, 0.1, 0.05)), RED)]
    if name == "Hud_Pause":
        return [(union(g.box(-0.32, 0, 0.2, 0.72, rnd=0.05), g.box(0.32, 0, 0.2, 0.72, rnd=0.05)), WHITE)]
    if name == "Hud_Settings":
        return [(_gear(g), WHITE)]
    if name == "Hud_Close":
        return [(union(g.line(-0.62, -0.62, 0.62, 0.62, 0.16), g.line(-0.62, 0.62, 0.62, -0.62, 0.16)), WHITE)]
    if name == "Hud_Back":
        return [(union(g.line(-0.5, 0, 0.72, 0, 0.14), g.line(-0.6, 0, -0.04, 0.56, 0.14), g.line(-0.6, 0, -0.04, -0.56, 0.14)), WHITE)]
    if name == "Hud_Locked":
        return [(union(g.box(0, -0.28, 0.62, 0.54, rnd=0.1), clip(g.ring(0, 0.28, 0.38, 0.1), g.box(0, 0.6, 0.6, 0.34))), WHITE), (union(g.circle(0, -0.2, 0.12), g.box(0, -0.42, 0.05, 0.16)), INK)]
    if name == "Target_Engine":
        return [(_brackets(g), WHITE), (_propeller(g), WHITE)]
    if name == "Target_Guns":
        return [(_brackets(g), WHITE), (union(g.poly((-0.6, -0.04), (-0.52, -0.22), (0.46, 0.18), (0.38, 0.34)), g.line(0.46, 0.14, 0.36, 0.38, 0.04)), WHITE), (g.circle(-0.22, -0.34, 0.2), STEEL)]
    if name == "Target_Sails":
        sail = g.poly((-0.46, 0.46), (0.46, 0.46), (0.36, -0.42), (0, -0.28), (-0.36, -0.42))
        return [(_brackets(g), WHITE), (union(sail, g.line(0, 0.6, 0, -0.6, 0.04), g.line(-0.56, 0.5, 0.56, 0.5, 0.04)), WHITE)]
    if name == "Target_Envelope":
        bag = g.box(0, 0.02, 0.58, 0.32, rnd=0.31)
        seams = union(g.line(-0.28, 0.32, -0.28, -0.3, 0.018), g.line(0.0, 0.34, 0.0, -0.32, 0.018), g.line(0.28, 0.32, 0.28, -0.3, 0.018))
        return [(_brackets(g), WHITE), (bag, WHITE), (seams, STEEL)]
    if name == "Target_LiftCore":
        return [(_brackets(g), WHITE), (_crystal(g, 0.62), CYAN)]
    if name == "Target_Reticle":
        ticks = union(g.line(0, 0.92, 0, 0.4, 0.05), g.line(0, -0.92, 0, -0.4, 0.05), g.line(0.92, 0, 0.4, 0, 0.05), g.line(-0.92, 0, -0.4, 0, 0.05))
        return [(union(g.ring(0, 0, 0.62, 0.05), ticks, g.circle(0, 0, 0.07)), WHITE)]
    if name == "Marker_WeakPoint":
        return [(g.ring(0, 0, 0.7, 0.06), RED), (g.star(0, 0, 0.92, 0.2, 4, 0.0), RED), (g.circle(0, 0, 0.14), WHITE)]
    if name == "Marker_Objective":
        return [(g.poly((0, 0.9), (0.72, 0), (0, -0.9), (-0.72, 0)), GOLD), (g.poly((0, 0.5), (0.4, 0), (0, -0.5), (-0.4, 0)), WHITE)]
    if name == "Marker_Waypoint":
        return [(union(g.circle(0, 0.26, 0.56), g.poly((-0.5, 0.04), (0.5, 0.04), (0, -0.9))), GOLD), (g.circle(0, 0.26, 0.24), INK)]
    if name == "Marker_EnemyFleet":
        ships = union(*(g.poly((cx - 0.3, cy), (cx + 0.3, cy), (cx + 0.18, cy - 0.16), (cx - 0.18, cy - 0.16)) for cx, cy in ((0, 0.1), (-0.5, -0.46), (0.5, -0.46))))
        bags = union(*(g.box(cx, cy + 0.24, 0.2, 0.11, rnd=0.1) for cx, cy in ((0, 0.1), (-0.5, -0.46), (0.5, -0.46))))
        return [(union(ships, bags), RED)]
    if name == "Hazard_Lightning":
        return [(_bolt(g), (0.86, 0.9, 1.0))]
    if name == "Hazard_Updraft":
        return [(union(g.line(-0.5, -0.76, -0.5, 0.3, 0.09), _chevron(g, -0.5, 0.38, 0.22, t=0.09)), CYAN), (union(g.line(0, -0.76, 0, 0.6, 0.09), _chevron(g, 0, 0.68, 0.22, t=0.09)), WHITE), (union(g.line(0.5, -0.76, 0.5, 0.3, 0.09), _chevron(g, 0.5, 0.38, 0.22, t=0.09)), CYAN)]
    if name == "Hazard_ToxicCloud":
        drips = union(g.line(-0.3, -0.42, -0.3, -0.64, 0.07), g.line(0.0, -0.42, 0.0, -0.8, 0.07), g.line(0.3, -0.42, 0.3, -0.62, 0.07))
        return [(drips, (0.76, 0.86, 0.34)), (_cloud(g, 0.1), GREEN)]
    if name == "Hazard_WindCurrent":
        return [(_swirl(g), (0.86, 0.96, 1.0))]
    if name == "Story_Surrender":
        flag = g.poly((-0.46, 0.8), (0.74, 0.66), (0.5, 0.36), (0.74, 0.04), (-0.46, 0.16))
        return [(g.line(-0.5, 0.86, -0.5, -0.86, 0.065), GOLD_DARK), (flag, WHITE)]
    if name == "Story_Bounty":
        bones = union(g.line(-0.8, -0.8, 0.8, 0.0, 0.07), g.line(0.8, -0.8, -0.8, 0.0, 0.07))
        return [(bones, STEEL), (_skull(g, 0, 0.26, 0.95), WHITE)]
    if name == "Story_Nemesis":
        blade = lambda sign: g.poly((sign * 0.34, 0.5), (sign * 0.84, 0.92), (sign * 0.66, 0.3))
        return [(union(blade(1), blade(-1)), RED), (_skull(g, 0, 0.0, 1.0), WHITE), (union(g.line(-0.36, 0.18, -0.08, 0.04, 0.04), g.line(0.36, 0.18, 0.08, 0.04, 0.04)), RED)]
    if name == "Story_Loyalty":
        heart = union(g.circle(-0.34, 0.26, 0.42), g.circle(0.34, 0.26, 0.42), g.poly((-0.73, 0.1), (0.73, 0.1), (0, -0.84)))
        return [(heart, RED), (g.circle(-0.34, 0.36, 0.11), WHITE)]
    if name == "Choice_PressGang":
        cuff = clip(g.ring(0, -0.42, 0.42, 0.075), g.box(0, -0.8, 0.8, 0.46))
        return [(_bust(g, 0, 0.95), WHITE), (union(g.circle(-0.44, -0.58, 0.14), g.circle(0.44, -0.58, 0.14), cuff), GOLD)]
    if name == "Ability_RookPrecision":
        return [(g.ring(0, 0, 0.56, 0.07), WHITE), (union(g.line(0, 0.86, 0, 0.3, 0.06), g.line(0, -0.86, 0, -0.3, 0.06), g.line(0.86, 0, 0.3, 0, 0.06), g.line(-0.86, 0, -0.3, 0, 0.06)), WHITE), (g.circle(0, 0, 0.16), ORANGE)]
    if name == "Ability_LyraWinds":
        return [(_swirl(g), WHITE)]
    if name == "Ability_LyraCloudStealth":
        slash = g.line(-0.68, -0.62, 0.68, 0.62, 0.075)
        return [(cut(_cloud(g, 0.0), g.line(-0.68, -0.62, 0.68, 0.62, 0.15)), WHITE), (slash, CYAN)]
    if name == "Ability_SableSabotage":
        return [(g.circle(-0.12, -0.2, 0.56), STEEL), (g.circle(-0.28, -0.04, 0.12), WHITE), (union(g.box(0.22, 0.3, 0.14, 0.14, rot=0.75), g.line(0.26, 0.34, 0.5, 0.56, 0.035)), WHITE), (g.star(0.58, 0.64, 0.28, 0.1, 6), ORANGE)]
    if name == "Ability_ThorneOverdrive":
        return [(_crystal(g, 0.86, -0.04), CYAN), (union(_chevron(g, 0, 0.1, 0.22, t=0.07), _chevron(g, 0, -0.26, 0.22, t=0.07)), WHITE)]
    if name == "Ability_ThornePatch":
        plate = g.box(0, 0, 0.66, 0.6, rot=0.12, rnd=0.08)
        rivets = union(*(g.circle(x, y, 0.08) for x, y in ((-0.48, 0.34), (0.42, 0.46), (0.48, -0.34), (-0.42, -0.46))))
        return [(plate, STEEL), (rivets, WHITE), (union(g.box(0, 0, 0.28, 0.08), g.box(0, 0, 0.08, 0.28)), CYAN)]
    if name == "Ability_MorrowRadar":
        sweep = g.poly((0, 0), (0.08, 0.9), (0.84, 0.3))
        return [(clip(sweep, g.circle(0, 0, 0.8)), (0.44, 0.9, 0.56)), (union(g.ring(0, 0, 0.8, 0.045), g.ring(0, 0, 0.42, 0.035)), WHITE), (union(g.circle(0.34, 0.5, 0.075), g.circle(-0.4, -0.22, 0.075)), RED), (g.circle(0, 0, 0.07), WHITE)]
    raise KeyError(name)


def _medal(g, colour):
    return [(g.circle(0, 0, 0.98), GOLD_DARK), (g.circle(0, 0, 0.91), GOLD), (g.circle(0, 0, 0.8), colour)]


def render_glyph(name, size):
    samples = 2
    px = size * samples
    axis = (np.arange(px, dtype=np.float32) + 0.5) / px * 2 - 1
    x, y = np.meshgrid(axis, -axis)
    full = G(x, y)
    medal = MEDALS.get(name)
    scale = 0.64 if medal else 0.88  # Leaves room for the ink line and any medal rim.
    inner = G(x / scale, y / scale)
    aa = 2.0 / px * 1.2
    layers = [(sdf * scale, colour) for sdf, colour in glyph_layers(name, inner)]
    base = _medal(full, medal) if medal else []
    image = np.zeros((px, px, 3), dtype=np.float32)
    # Ink first, then every shape in order. The ink follows the union of the whole glyph.
    ink_width = 0.05
    if medal:
        outer = np.minimum.reduce([s for s, _ in base])
        coverage = smoothstep(aa, -aa, outer - 0.0)
        image[...] = INK
    else:
        outer = np.minimum.reduce([s for s, _ in layers])
        coverage = smoothstep(aa, -aa, outer - ink_width)
        image[...] = INK
    for sdf, colour in base:
        mask = smoothstep(aa, -aa, sdf)[..., None]
        image = image * (1 - mask) + np.array(colour, dtype=np.float32) * mask
    if medal:
        # The glyph's own ink line inside the medal.
        glyph_all = np.minimum.reduce([s for s, _ in layers])
        mask = smoothstep(aa, -aa, glyph_all - 0.035)[..., None]
        image = image * (1 - mask) + np.array(INK, dtype=np.float32) * mask
    for sdf, colour in layers:
        mask = smoothstep(aa, -aa, sdf)[..., None]
        # One hard shadow band on the lower part of each shape, for the comic look.
        shade = 1 - 0.13 * smoothstep(-0.01, 0.01, -(y + 0.3 * scale) - 0.02 * np.sin(x * 9))[..., None]
        painted = np.array(colour, dtype=np.float32) * shade
        image = image * (1 - mask) + painted * mask
    out = np.dstack((image, coverage))
    return downsample(out, samples)


# ---- model icons -----------------------------------------------------------------------------

def _view_for(icon):
    """Camera direction in Blender space, from the model towards the camera."""
    group = icon.split("_")[0]
    if group == "Ship":
        return Vector((-0.78, -1.0, 0.3))
    if group == "Weapon":
        return Vector((0.0, -1.0, 0.0))
    if group == "Module":
        return Vector((-0.8, -1.0, 0.5))
    return Vector((-0.6, -1.0, 0.55))


def _lay_flat(icon):
    """Long weapons are stood on a diagonal, so they fill the square."""
    return icon.startswith("Weapon_") or icon in ("Ammo_Harpoon", "Ammo_Missile")


def _render_model(icon, base, path, size):
    from mathutils import Matrix

    kit.clear_scene()
    asset = f"{base}_HQ"
    mb, _, _ = catalog.build(asset)
    faction = catalog.DEFAULT_FACTIONS.get(base, palette.DEFAULT_FACTION)
    obj = mb.to_object(asset, kit.palette_material(True, faction))
    if _lay_flat(icon):
        obj.matrix_world = Matrix.Rotation(np.radians(-45), 4, "Y")
    bpy.context.view_layer.update()
    view = _view_for(icon).normalized()
    data = bpy.data.cameras.new("IconCam")
    data.type = "ORTHO"
    cam = bpy.data.objects.new("IconCam", data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    rotation = (-view).to_track_quat("-Z", "Y")
    right = rotation @ Vector((1, 0, 0))
    up = rotation @ Vector((0, 1, 0))
    world = [obj.matrix_world @ v.co for v in obj.data.vertices]
    xs = [p.dot(right) for p in world]
    ys = [p.dot(up) for p in world]
    zs = [p.dot(view) for p in world]
    mid = right * ((min(xs) + max(xs)) / 2) + up * ((min(ys) + max(ys)) / 2)
    data.ortho_scale = max(max(xs) - min(xs), max(ys) - min(ys)) * 1.14
    data.clip_end = (max(zs) - min(zs)) * 3 + 10
    cam.location = mid + view * (max(zs) + 2)
    cam.rotation_euler = rotation.to_euler()
    portraits._setup_render(path, size)
    bpy.ops.render.render(write_still=True)


def _compose_model(icon, path, sizes):
    img = bpy.data.images.load(str(path))
    size = img.size[0]
    rgba = np.array(img.pixels[:], dtype=np.float32).reshape(size, size, 4)[::-1]
    bpy.data.images.remove(img)
    alpha = rgba[:, :, 3]
    ink = ink_outline(alpha, max(2, size // 90))
    # Lifted well above the in-game look: icons are small and must pop off a busy HUD.
    lifted = np.clip(rgba[:, :, :3], 0, 1) ** 0.72 * 1.12
    rgb = lifted * alpha[..., None] + np.array(INK, dtype=np.float32) * (1 - alpha[..., None])
    coverage = ink
    medal = CHOICE_MEDAL.get(icon)
    if medal:
        axis = (np.arange(size, dtype=np.float32) + 0.5) / size * 2 - 1
        x, y = np.meshgrid(axis, -axis)
        g = G(x, y)
        aa = 2.0 / size
        back = np.zeros((size, size, 3), dtype=np.float32)
        back[...] = INK
        for sdf, colour in _medal(g, medal):
            m = smoothstep(aa, -aa, sdf)[..., None]
            back = back * (1 - m) + np.array(colour, dtype=np.float32) * m
        cover = smoothstep(aa, -aa, g.circle(0, 0, 0.98))
        # The model sits inside the medal at 76 percent, centred.
        inset = np.zeros_like(rgba)
        new = int(size * 0.76)
        step = (np.arange(new) * size / new).astype(int)
        small = np.dstack((rgb, ink))[step][:, step]
        off = (size - new) // 2
        inset[off:off + new, off:off + new] = small
        m = inset[..., 3:4]
        rgb = back * (1 - m) + inset[..., :3] * m
        coverage = np.maximum(cover, inset[..., 3])
    out = np.dstack((rgb, coverage))
    written = []
    for quality, target in sizes.items():
        dest = icon_path(icon, quality)
        write_png(dest, downsample(out, size // target))
        written.append(dest)
    return written


def icon_path(name, quality):
    return palette.TEXTURE_DIR / f"T_Icon_{name}_{quality}.png"


def generate_glyphs():
    written = []
    for name in fx_catalog.GLYPH_ICONS:
        for quality, size in fx_catalog.ICON_SIZES.items():
            path = icon_path(name, quality)
            write_png(path, render_glyph(name, size))
            written.append(str(path))
    return written


def generate_model_icons(scratch, names=None):
    scene = bpy.context.scene
    engine, transparent = scene.render.engine, scene.render.film_transparent
    written = []
    for icon, base in fx_catalog.MODEL_ICONS.items():
        if names and icon not in names:
            continue
        path = Path(scratch) / f"icon_{icon}.png"
        _render_model(icon, base, path, 512)
        written += [str(p) for p in _compose_model(icon, path, fx_catalog.ICON_SIZES)]
    kit.clear_scene()
    portraits.restore_scene(engine, transparent)
    return written


def generate_all(scratch):
    return generate_glyphs() + generate_model_icons(scratch)
