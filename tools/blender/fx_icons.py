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

# Deck battle skill buttons. The medal says what kind of skill it is, so a glance tells hit from heal.
BROWN = (0.55, 0.34, 0.17)
BROWN_DARK = (0.38, 0.22, 0.11)
IRON = (0.42, 0.44, 0.5)
IRON_DARK = (0.24, 0.25, 0.3)
BRASS = (0.88, 0.66, 0.28)
EMBER = (1.0, 0.42, 0.1)
FLAME = (1.0, 0.84, 0.32)
MINT = (0.52, 0.92, 0.68)
PALE = (0.98, 0.9, 0.64)
SMOKE = (0.72, 0.74, 0.78)
SPARK = (1.0, 0.9, 0.36)
GLASS = (0.62, 0.84, 0.9)
BORE = (0.08, 0.06, 0.08)
SKILL_PHYSICAL = (0.46, 0.13, 0.12)
SKILL_MAGIC = (0.2, 0.16, 0.46)
SKILL_HEAL = (0.09, 0.38, 0.3)
SKILL_COMPANION = (0.5, 0.22, 0.07)
SKILL_MEDALS = {
    "Skill_Cleave": SKILL_PHYSICAL, "Skill_CrushingBlow": SKILL_PHYSICAL, "Skill_HookSwing": SKILL_PHYSICAL,
    "Skill_AimedShot": SKILL_PHYSICAL, "Skill_CinderFlame": SKILL_COMPANION, "Skill_HeavyFlak": SKILL_PHYSICAL,
    "Skill_LightningBolt": SKILL_MAGIC, "Skill_Squall": SKILL_MAGIC, "Skill_Tailwind": SKILL_HEAL,
    "Skill_Backstab": SKILL_PHYSICAL, "Skill_SmokeBomb": SKILL_MAGIC, "Skill_SetCharge": SKILL_PHYSICAL,
    "Skill_DarkMending": SKILL_HEAL, "Skill_VeilOfLife": SKILL_HEAL, "Skill_RaiseTheFallen": SKILL_HEAL,
    "Skill_Scattershot": SKILL_PHYSICAL, "Skill_MarkWeakPoint": SKILL_PHYSICAL, "Skill_BelayingPin": SKILL_PHYSICAL,
    "Skill_QuickDraw": SKILL_PHYSICAL, "Skill_PatchUp": SKILL_HEAL, "Skill_Rally": SKILL_HEAL,
    "Skill_SmellingSalts": SKILL_HEAL, "Skill_StaticSnare": SKILL_MAGIC,
    "Skill_ShadowSpear": SKILL_MAGIC, "Skill_Necromancy": SKILL_MAGIC,
    "Skill_CutlassFury": SKILL_PHYSICAL, "Skill_AirSupport": SKILL_COMPANION, "Skill_PiratesWrath": SKILL_PHYSICAL,
    "Skill_GatlingGun": SKILL_PHYSICAL, "Skill_BombCharge": SKILL_PHYSICAL,
    "Skill_GaleSlash": SKILL_MAGIC, "Skill_EnergySong": SKILL_HEAL, "Skill_StormBallad": SKILL_MAGIC,
    "Skill_PoisonArrows": SKILL_PHYSICAL, "Skill_DaggerDance": SKILL_PHYSICAL,
    "Skill_Fireball": SKILL_MAGIC, "Skill_ElectricCyclone": SKILL_MAGIC,
    "Skill_Gunslinger": SKILL_PHYSICAL, "Skill_HiddenCannon": SKILL_PHYSICAL, "Skill_Mutiny": SKILL_PHYSICAL,
}
MEDALS.update(SKILL_MEDALS)


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


def _skill_layers(name, g):
    """The deck battle's skill buttons, one picture per skill. None for anything else."""
    if name == "Hud_Attack":
        return [(union(_sword(g, -0.72, -0.72, 0.84, 0.84), g.circle(-0.76, -0.76, 0.11)), WHITE)]
    if name == "Skill_Cleave":
        trail = clip(cut(g.circle(0.05, -0.15, 0.86), g.circle(0.24, -0.34, 0.78)), g.box(0, 0.35, 1.0, 0.62))
        return [(trail, PALE), (_sword(g, -0.62, -0.72, 0.62, 0.6), WHITE)]
    if name == "Skill_CrushingBlow":
        return [(g.star(-0.4, -0.44, 0.52, 0.2, 8, 0.2), ORANGE), (g.star(-0.4, -0.44, 0.26, 0.1, 8, 0.2), FLAME),
                (g.line(-0.05, 0.0, 0.7, 0.75, 0.08), BROWN),
                (g.box(-0.12, -0.07, 0.46, 0.24, rot=-0.785, rnd=0.06), STEEL),
                (g.box(-0.12, -0.07, 0.08, 0.26, rot=-0.785), IRON_DARK)]
    if name == "Skill_HookSwing":
        hook = union(g.line(0.15, 0.52, 0.15, -0.32, 0.075), clip(g.ring(0.15, -0.2, 0.36, 0.075), g.box(0.15, -0.5, 0.5, 0.3)),
                     g.poly((-0.21, -0.18), (-0.34, 0.08), (-0.1, -0.06)), g.poly((0.51, -0.18), (0.64, 0.08), (0.4, -0.06)),
                     g.ring(0.15, 0.62, 0.11, 0.045))
        motion = union(g.line(-0.82, 0.08, -0.4, 0.08, 0.04), g.line(-0.76, -0.18, -0.46, -0.18, 0.04))
        return [(motion, PALE), (g.line(-0.86, 0.86, 0.06, 0.68, 0.045), BROWN), (hook, WHITE)]
    if name == "Skill_AimedShot":
        trails = union(g.line(-0.82, -0.82, 0.05, 0.05, 0.05), g.line(-0.86, -0.42, -0.26, 0.18, 0.035), g.line(-0.42, -0.86, 0.18, -0.26, 0.035))
        bullet = g.line(0.18, 0.18, 0.46, 0.46, 0.15)
        return [(trails, PALE), (g.ring(0.42, 0.42, 0.4, 0.06), RED), (bullet, BRASS), (clip(bullet, g.circle(0.52, 0.52, 0.16)), STEEL)]
    if name == "Skill_CinderFlame":
        # Rook's hound Cinder, face on: an iron head, blade ears, ember eyes and a brass barrel for a snout.
        ears = union(g.poly((-0.5, 0.3), (-0.8, 0.94), (-0.16, 0.5)), g.poly((0.5, 0.3), (0.8, 0.94), (0.16, 0.5)))
        flames = g.poly((-0.42, -0.5), (-0.32, -0.96), (-0.02, -0.72), (0.14, -1.0), (0.38, -0.7), (0.48, -0.48))
        core = g.poly((-0.22, -0.56), (-0.14, -0.86), (0.04, -0.7), (0.15, -0.9), (0.3, -0.58))
        eyes = union(g.circle(-0.25, 0.14, 0.1), g.circle(0.25, 0.14, 0.1))
        glints = union(g.circle(-0.22, 0.17, 0.035), g.circle(0.28, 0.17, 0.035))
        return [(ears, IRON_DARK), (g.box(0, 0.08, 0.56, 0.46, rnd=0.32), IRON), (g.box(0, 0.3, 0.5, 0.08, rnd=0.04), IRON_DARK),
                (flames, ORANGE), (core, FLAME), (g.circle(0, -0.3, 0.3), BRASS), (g.circle(0, -0.3, 0.18), BORE),
                (g.circle(0, -0.3, 0.08), EMBER), (eyes, EMBER), (glints, FLAME)]
    if name == "Skill_HeavyFlak":
        puffs = union(g.circle(-0.38, 0.3, 0.36), g.circle(-0.6, 0.12, 0.2), g.circle(0.38, 0.42, 0.3), g.circle(0.6, 0.28, 0.17),
                      g.circle(0.05, -0.38, 0.4), g.circle(-0.26, -0.56, 0.22), g.circle(0.36, -0.56, 0.22))
        stars = union(g.star(-0.38, 0.3, 0.3, 0.12, 8), g.star(0.38, 0.42, 0.24, 0.1, 8, 0.3), g.star(0.05, -0.38, 0.34, 0.14, 9, 0.1))
        cores = union(g.circle(-0.38, 0.3, 0.09), g.circle(0.38, 0.42, 0.07), g.circle(0.05, -0.38, 0.11))
        return [(puffs, IRON_DARK), (stars, ORANGE), (cores, FLAME)]
    if name == "Skill_LightningBolt":
        sparks = union(g.star(-0.21, -0.87, 0.24, 0.07, 4), g.star(0.62, 0.62, 0.18, 0.05, 4), g.star(-0.62, 0.38, 0.14, 0.04, 4))
        return [(_bolt(g, 0.95), SPARK), (sparks, WHITE)]
    if name == "Skill_Squall":
        rain = union(g.line(-0.45, -0.08, -0.6, -0.5, 0.055), g.line(-0.12, -0.12, -0.27, -0.54, 0.055), g.line(0.42, -0.08, 0.27, -0.5, 0.055))
        bolt = g.poly((0.14, -0.02), (-0.08, -0.46), (0.06, -0.46), (-0.04, -0.9), (0.28, -0.34), (0.12, -0.34), (0.26, -0.02))
        return [(rain, CYAN), (bolt, SPARK), (_cloud(g, 0.32), SMOKE)]
    if name == "Skill_Tailwind":
        lines = union(g.line(-0.86, 0.36, -0.22, 0.36, 0.06), g.line(-0.92, 0.0, -0.32, 0.0, 0.06), g.line(-0.86, -0.36, -0.22, -0.36, 0.06))
        chevrons = union(_side_chevron(g, 0.06, 0, 0.46, True, t=0.11), _side_chevron(g, 0.52, 0, 0.46, True, t=0.11))
        return [(lines, CYAN), (chevrons, WHITE)]
    if name == "Skill_Backstab":
        drop = union(g.circle(-0.56, -0.7, 0.12), g.poly((-0.56, -0.42), (-0.675, -0.66), (-0.445, -0.66)))
        moon = cut(g.circle(-0.5, 0.5, 0.28), g.circle(-0.38, 0.6, 0.24))
        return [(moon, PALE), (_sword(g, 0.64, 0.72, -0.38, -0.36), WHITE), (drop, RED)]
    if name == "Skill_SmokeBomb":
        puffs = union(g.circle(-0.52, -0.42, 0.3), g.circle(-0.12, -0.56, 0.32), g.circle(0.34, -0.44, 0.32), g.circle(-0.66, -0.12, 0.2), g.circle(0.62, -0.14, 0.2))
        stars = union(g.star(-0.52, 0.56, 0.18, 0.07, 5), g.star(0.56, 0.52, 0.18, 0.07, 5))
        return [(g.line(0.1, 0.12, 0.28, 0.4, 0.04), STEEL), (g.circle(-0.04, -0.06, 0.38), IRON_DARK), (g.circle(-0.16, 0.06, 0.08), STEEL),
                (puffs, SMOKE), (g.star(0.32, 0.48, 0.22, 0.08, 6), ORANGE), (stars, GOLD)]
    if name == "Skill_SetCharge":
        sticks = union(g.box(-0.3, -0.16, 0.14, 0.5, rnd=0.07), g.box(0.0, -0.16, 0.14, 0.5, rnd=0.07), g.box(0.3, -0.16, 0.14, 0.5, rnd=0.07))
        return [(sticks, RED), (g.box(0, -0.06, 0.5, 0.08), IRON_DARK), (g.line(0.0, 0.34, 0.24, 0.6, 0.035), STEEL),
                (g.star(0.32, 0.68, 0.26, 0.09, 6), ORANGE), (g.circle(0.32, 0.68, 0.08), FLAME)]
    if name == "Skill_DarkMending":
        ring = g.ring(0, 0, 0.74, 0.06)
        motes = union(*(g.circle(0.74 * np.sin(a), 0.74 * np.cos(a), 0.09) for a in (0.4, 2.0, 3.6, 5.2)))
        cross = union(g.box(0, 0, 0.2, 0.56, rnd=0.06), g.box(0, 0, 0.56, 0.2, rnd=0.06))
        core = union(g.box(0, 0, 0.08, 0.42), g.box(0, 0, 0.42, 0.08))
        return [(ring, VIOLET), (motes, WHITE), (cross, WHITE), (core, VIOLET)]
    if name == "Skill_VeilOfLife":
        veil = clip(g.ring(0, -0.24, 0.86, 0.07), g.box(0, 0.4, 1.0, 0.64))
        plus = union(g.box(0, 0.78, 0.05, 0.15), g.box(0, 0.78, 0.15, 0.05))
        return [(veil, MINT), (plus, MINT), (_bust(g, -0.42, 0.6), STEEL), (_bust(g, 0.42, 0.6), STEEL), (_bust(g, 0, 0.78), WHITE)]
    if name == "Skill_RaiseTheFallen":
        arrow = union(g.line(0, -0.48, 0, 0.42, 0.09), _chevron(g, 0, 0.52, 0.34, t=0.1))
        sparkles = union(g.star(-0.5, 0.3, 0.18, 0.06, 4), g.star(0.5, 0.0, 0.14, 0.05, 4), g.star(0.42, 0.62, 0.11, 0.04, 4))
        return [(g.box(0, -0.62, 0.72, 0.07, rnd=0.03), STEEL), (_skull(g, -0.46, -0.36, 0.34), STEEL), (arrow, WHITE), (sparkles, MINT)]
    if name == "Skill_Scattershot":
        trails = union(g.line(-0.62, -0.62, 0.6, 0.06, 0.035), g.line(-0.62, -0.62, 0.42, 0.42, 0.035), g.line(-0.62, -0.62, 0.06, 0.6, 0.035))
        pellets = union(g.circle(0.62, 0.06, 0.14), g.circle(0.44, 0.44, 0.14), g.circle(0.06, 0.62, 0.14))
        return [(trails, PALE), (g.star(-0.62, -0.62, 0.34, 0.13, 7), ORANGE), (pellets, BRASS)]
    if name == "Skill_MarkWeakPoint":
        # A red reticle on a cracked shield: the armour's weak spot, found and marked.
        shield = g.poly((-0.2, 0.62), (0.34, 0.44), (0.3, -0.18), (-0.2, -0.8), (-0.7, -0.18), (-0.74, 0.44))
        crack = union(g.line(-0.2, 0.62, -0.3, 0.2, 0.04), g.line(-0.3, 0.2, -0.12, -0.04, 0.04), g.line(-0.12, -0.04, -0.28, -0.4, 0.04))
        ticks = union(g.line(0.3, 0.86, 0.3, 0.6, 0.05), g.line(0.3, -0.06, 0.3, 0.2, 0.05), g.line(0.64, 0.4, 0.88, 0.4, 0.05), g.line(-0.04, 0.4, -0.28, 0.4, 0.05))
        return [(shield, STEEL), (crack, IRON_DARK), (union(g.ring(0.3, 0.4, 0.28, 0.06), ticks), RED), (g.circle(0.3, 0.4, 0.07), RED)]
    if name == "Skill_BelayingPin":
        body = union(g.line(-0.3, -0.3, 0.34, 0.34, 0.17), g.circle(0.38, 0.38, 0.2))
        stars = union(g.star(-0.42, 0.52, 0.2, 0.08, 5), g.star(0.1, 0.74, 0.15, 0.06, 5), g.star(0.62, -0.26, 0.17, 0.07, 5))
        return [(stars, GOLD), (g.line(-0.78, -0.78, -0.32, -0.32, 0.08), BROWN_DARK), (g.circle(-0.36, -0.36, 0.13), BROWN_DARK), (body, BROWN)]
    if name == "Skill_QuickDraw":
        speed = union(g.line(-0.92, 0.5, -0.46, 0.5, 0.04), g.line(-0.86, 0.26, -0.52, 0.26, 0.04))
        grip = g.box(-0.32, -0.2, 0.15, 0.34, rot=-0.35, rnd=0.07)
        guard = clip(g.ring(-0.06, -0.06, 0.16, 0.04), g.box(-0.06, -0.24, 0.24, 0.18))
        return [(speed, PALE), (g.star(0.7, 0.24, 0.3, 0.11, 7), ORANGE), (grip, BROWN), (guard, IRON), (g.box(0.12, 0.24, 0.52, 0.12, rnd=0.04), IRON)]
    if name == "Skill_PatchUp":
        pad = g.box(0, 0, 0.2, 0.16, rot=0.6, rnd=0.04)
        cross = union(g.box(0, 0, 0.06, 0.15), g.box(0, 0, 0.15, 0.06))
        return [(g.box(0, 0, 0.7, 0.28, rot=0.6, rnd=0.13), PALE), (pad, WHITE), (cross, RED)]
    if name == "Skill_Rally":
        bugle = union(g.poly((0.22, 0.28), (0.7, 0.62), (0.7, -0.32), (0.22, 0.0)), g.line(-0.7, 0.14, 0.28, 0.14, 0.08), g.circle(-0.72, 0.14, 0.09))
        loop = clip(g.ring(-0.18, -0.12, 0.24, 0.06), g.box(-0.18, -0.3, 0.4, 0.2))
        arcs = union(clip(g.ring(0.66, 0.15, 0.24, 0.035), g.box(0.98, 0.15, 0.2, 0.6)), clip(g.ring(0.66, 0.15, 0.36, 0.035), g.box(1.06, 0.15, 0.24, 0.6)))
        plus = union(g.box(-0.4, 0.62, 0.05, 0.16), g.box(-0.4, 0.62, 0.16, 0.05))
        return [(arcs, WHITE), (plus, MINT), (loop, BRASS), (bugle, BRASS)]
    if name == "Skill_SmellingSalts":
        bottle = union(g.box(0, -0.28, 0.36, 0.4, rnd=0.14), g.box(0, 0.22, 0.13, 0.16))
        liquid = clip(g.box(0, -0.28, 0.28, 0.32, rnd=0.1), g.box(0, -0.48, 0.4, 0.22))
        wisps = union(g.line(0.06, 0.56, 0.3, 0.84, 0.045), g.line(-0.08, 0.56, -0.34, 0.86, 0.045), g.line(0.0, 0.6, 0.02, 0.92, 0.04))
        return [(wisps, PALE), (bottle, GLASS), (liquid, MINT), (g.box(0, 0.42, 0.16, 0.08, rnd=0.03), BROWN), (g.circle(-0.14, -0.08, 0.06), WHITE)]
    if name == "Skill_StaticSnare":
        points = [(0.66 * np.sin(a), 0.66 * np.cos(a)) for a in np.arange(6) * np.pi / 3]
        web = union(g.ring(0, 0, 0.66, 0.04), g.ring(0, 0, 0.36, 0.035), *(g.line(0, 0, x, y, 0.035) for x, y in points))
        nodes = union(*(g.circle(x, y, 0.08) for x, y in points))
        return [(web, CYAN), (nodes, WHITE), (_bolt(g, 0.42), SPARK)]
    if name == "Skill_ShadowSpear":
        # Dr. Thorne's black spear in flight, its barbed head edged in violet light.
        def along(t, side=0.0):
            """A point t of the way from butt to tip, side across the shaft."""
            return (-0.82 + 1.64 * t - side * 0.7071, -0.82 + 1.64 * t + side * 0.7071)
        head = g.poly(along(1.02), along(0.7, 0.26), along(0.6, 0.15), along(0.56, 0.0), along(0.6, -0.15), along(0.7, -0.26))
        core = g.poly(along(0.92), along(0.7, 0.15), along(0.62, 0.0), along(0.7, -0.15))
        barbs = union(g.poly(along(0.6, 0.12), along(0.5, 0.26), along(0.56, 0.06)), g.poly(along(0.6, -0.12), along(0.5, -0.26), along(0.56, -0.06)))
        glow = g.line(*along(0.0), *along(0.6), 0.13)
        shaft = g.line(*along(0.0), *along(0.6), 0.07)
        wisps = union(g.line(*along(0.1, 0.18), *along(0.3, 0.12), 0.03), g.line(*along(0.2, -0.2), *along(0.42, -0.13), 0.03))
        sparks = union(g.star(-0.5, 0.42, 0.16, 0.05, 4), g.star(0.46, -0.48, 0.13, 0.04, 4))
        return [(glow, VIOLET), (wisps, VIOLET), (sparks, WHITE), (shaft, BORE), (head, VIOLET), (barbs, BORE), (core, BORE)]
    if name == "Skill_CutlassFury":
        # Three cuts in a row: three slash trails stacked across a cutlass.
        trails = union(*(clip(cut(g.circle(0.1, cy - 0.5, 0.9), g.circle(0.24, cy - 0.66, 0.84)), g.box(0.1, cy + 0.15, 0.95, 0.3)) for cy in (0.42, 0.04, -0.34)))
        return [(trails, PALE), (_sword(g, -0.66, -0.74, 0.66, 0.66), WHITE), (g.star(0.62, 0.62, 0.2, 0.07, 4), GOLD)]
    if name == "Skill_AirSupport":
        # A gunship overhead with its broadside going off, and the shot falling.
        flashes = union(g.star(-0.42, 0.06, 0.2, 0.08, 7), g.star(0.0, 0.02, 0.2, 0.08, 7, 0.2), g.star(0.42, 0.06, 0.2, 0.08, 7, 0.1))
        trails = union(g.line(-0.42, -0.1, -0.56, -0.62, 0.03), g.line(0.0, -0.12, -0.06, -0.66, 0.03), g.line(0.42, -0.1, 0.48, -0.62, 0.03))
        balls = union(g.circle(-0.58, -0.7, 0.09), g.circle(-0.06, -0.74, 0.09), g.circle(0.5, -0.7, 0.09))
        return [(_ship(g, 0.16), STEEL), (g.box(0, 0.78, 0.56, 0.05), IRON_DARK), (trails, PALE), (flashes, ORANGE), (balls, IRON_DARK)]
    if name == "Skill_PiratesWrath":
        # Two thrown blades spinning in, then the third swung straight up in a great arc.
        arc = clip(cut(g.circle(-0.1, -0.2, 0.86), g.circle(-0.22, -0.2, 0.76)), g.box(0.4, 0.1, 0.5, 0.9))
        motion = union(g.line(-0.98, 0.5, -0.76, 0.56, 0.03), g.line(-0.98, -0.04, -0.76, 0.0, 0.03))
        return [(arc, PALE), (motion, PALE), (_sword(g, -0.78, 0.5, 0.06, 0.8), STEEL), (_sword(g, -0.78, -0.06, 0.02, 0.2), STEEL),
                (_sword(g, 0.32, -0.86, 0.54, 0.82), WHITE), (g.star(0.6, 0.8, 0.18, 0.06, 4), GOLD)]
    if name == "Skill_GatlingGun":
        # A gatling side on, barrels blazing, a stream of shots spraying out wide.
        barrels = union(g.box(0.18, 0.12, 0.42, 0.035), g.box(0.18, 0.0, 0.42, 0.035), g.box(0.18, -0.12, 0.42, 0.035))
        clamps = union(g.box(-0.05, 0.0, 0.035, 0.17), g.box(0.42, 0.0, 0.035, 0.17))
        body = union(g.box(-0.42, 0.0, 0.2, 0.17, rnd=0.04), g.line(-0.5, -0.12, -0.62, -0.48, 0.07))
        drum = g.circle(-0.42, 0.3, 0.15)
        shots = union(*(g.line(0.66 + 0.06 * k, 0.08 * (k - 1.5), 0.92, 0.26 * (k - 1.5), 0.025) for k in range(4)))
        return [(shots, PALE), (g.star(0.64, 0.0, 0.26, 0.1, 8), ORANGE), (g.star(0.64, 0.0, 0.13, 0.05, 8), FLAME),
                (drum, BRASS), (body, IRON), (barrels, STEEL), (clamps, BRASS)]
    if name == "Skill_BombCharge":
        # A lit bomb over a blast, with the gold visor of the fireproof suit behind it.
        helmet = union(g.circle(0.34, 0.32, 0.4), g.box(0.34, 0.0, 0.4, 0.22, rnd=0.1))
        visor = g.box(0.3, 0.32, 0.24, 0.14, rnd=0.04)
        bomb_body = g.circle(-0.22, -0.2, 0.42)
        cap = g.box(-0.04, 0.18, 0.1, 0.07, rot=-0.6)
        fuse = union(g.line(0.0, 0.24, 0.08, 0.42, 0.03), g.line(0.08, 0.42, 0.04, 0.58, 0.03))
        return [(g.star(-0.2, -0.24, 0.92, 0.5, 10, 0.15), ORANGE), (helmet, STEEL), (visor, GOLD), (bomb_body, IRON_DARK),
                (g.circle(-0.36, -0.06, 0.08), IRON), (cap, BRASS), (fuse, BROWN), (g.star(0.04, 0.6, 0.16, 0.06, 6), FLAME)]
    if name == "Skill_GaleSlash":
        # Three crescent blades of wind, one behind another, cutting in from the left.
        blades = [clip(cut(g.circle(cx, cy, 0.62), g.circle(cx - 0.2, cy, 0.56)), g.box(cx + 0.4, cy, 0.4, 0.62)) for cx, cy in ((-0.38, 0.0), (-0.02, 0.0), (0.34, 0.0))]
        trails = union(g.line(-0.92, 0.42, -0.55, 0.42, 0.03), g.line(-0.95, 0.0, -0.6, 0.0, 0.03), g.line(-0.92, -0.42, -0.55, -0.42, 0.03))
        return [(trails, CYAN), (blades[0], CYAN), (blades[1], CYAN), (blades[2], WHITE)]
    if name == "Skill_EnergySong":
        # A lyre singing out notes that rise as a doubled arrow: two turns for the next ally.
        lyre = union(clip(g.ring(-0.36, -0.12, 0.38, 0.07), g.box(-0.36, 0.06, 0.45, 0.32)), g.box(-0.36, -0.36, 0.3, 0.07), g.box(-0.36, 0.26, 0.38, 0.05))
        strings = union(g.line(-0.5, -0.32, -0.5, 0.24, 0.015), g.line(-0.36, -0.32, -0.36, 0.24, 0.015), g.line(-0.22, -0.32, -0.22, 0.24, 0.015))
        note = union(g.circle(0.12, 0.2, 0.1), g.line(0.2, 0.22, 0.2, 0.62, 0.03), g.poly((0.2, 0.62), (0.36, 0.48), (0.2, 0.52)))
        arrows = union(_chevron(g, 0.52, -0.06, 0.24, t=0.08), _chevron(g, 0.52, -0.36, 0.24, t=0.08))
        return [(lyre, BRASS), (strings, PALE), (note, GOLD), (arrows, WHITE)]
    if name == "Skill_StormBallad":
        # A tornado of wind with music notes caught spinning in it.
        bands = union(*(g.box(x, y, half, 0.075, rnd=0.07) for x, y, half in ((0.0, 0.6, 0.62), (0.1, 0.36, 0.5), (-0.04, 0.12, 0.4), (0.08, -0.12, 0.3), (-0.02, -0.34, 0.2), (0.06, -0.54, 0.11))))
        notes = union(g.circle(-0.56, 0.16, 0.08), g.line(-0.5, 0.18, -0.5, 0.46, 0.025), g.circle(0.5, -0.14, 0.08), g.line(0.56, -0.12, 0.56, 0.16, 0.025), g.poly((0.56, 0.16), (0.68, 0.06), (0.56, 0.08)))
        return [(bands, CYAN), (notes, GOLD)]
    if name == "Skill_PoisonArrows":
        # A volley of green-fletched arrows raining down to the right, venom dripping from the heads.
        shafts, heads, fletches = [], [], []
        for k, (x, y) in enumerate(((-0.62, 0.62), (-0.3, 0.74), (-0.66, 0.24), (-0.3, 0.36), (0.02, 0.48))):
            ex, ey = x + 0.62, y - 0.62
            shafts.append(g.line(x, y, ex, ey, 0.03))
            heads.append(g.poly((ex + 0.16, ey - 0.16), (ex - 0.1, ey + 0.02), (ex - 0.02, ey - 0.02), (ex + 0.02, ey + 0.1 - 0.12)))
            heads.append(g.poly((ex + 0.16, ey - 0.16), (ex - 0.02, ey + 0.1), (ex - 0.02, ey - 0.02)))
            fletches.append(g.poly((x, y), (x - 0.14, y + 0.02), (x - 0.04, y - 0.06)))
            fletches.append(g.poly((x, y), (x - 0.02, y + 0.14), (x + 0.06, y + 0.04)))
        drops = union(g.circle(0.5, -0.5, 0.06), g.circle(0.16, -0.62, 0.05))
        return [(union(*fletches), GREEN), (union(*shafts), PALE), (union(*heads), MINT), (drops, MINT)]
    if name == "Skill_DaggerDance":
        # A hooded shadow with burning red eyes, a dagger flashing at each side of it.
        hood = union(g.poly((0.0, 0.86), (0.42, 0.24), (0.36, -0.36), (-0.36, -0.36), (-0.42, 0.24)), g.circle(0, 0.06, 0.4))
        face = g.circle(0, 0.02, 0.26)
        eyes = union(g.box(-0.11, 0.06, 0.07, 0.03, rot=-0.3), g.box(0.11, 0.06, 0.07, 0.03, rot=0.3))
        return [(_sword(g, -0.86, -0.7, -0.5, 0.2), STEEL), (_sword(g, 0.86, -0.7, 0.5, 0.2), STEEL), (hood, IRON_DARK), (face, INK), (eyes, RED)]
    if name == "Skill_Fireball":
        # A ball of fire streaking up and to the right, its flames trailing behind it.
        tail = union(g.poly((0.3, 0.3), (-0.86, -0.5), (-0.5, -0.86)), g.poly((0.22, 0.38), (-0.7, -0.2), (-0.3, -0.1)), g.poly((0.38, 0.22), (-0.2, -0.7), (-0.1, -0.3)))
        inner = union(g.poly((0.3, 0.3), (-0.56, -0.36), (-0.36, -0.56)))
        return [(tail, ORANGE), (inner, FLAME), (g.circle(0.3, 0.3, 0.38), ORANGE), (g.circle(0.34, 0.34, 0.26), FLAME), (g.circle(0.38, 0.38, 0.12), WHITE)]
    if name == "Skill_ElectricCyclone":
        # A storm cloud swirling over three bolts.
        cloud = union(g.circle(-0.42, 0.42, 0.3), g.circle(0.0, 0.56, 0.38), g.circle(0.44, 0.42, 0.28), g.box(0, 0.28, 0.66, 0.16, rnd=0.15))
        swirl = clip(g.ring(0.0, 0.42, 0.2, 0.05), g.box(0.0, 0.52, 0.3, 0.12))
        bolts = union(*(g.poly((x + 0.06, 0.16), (x - 0.12, -0.3), (x + 0.0, -0.3), (x - 0.1, -0.86), (x + 0.16, -0.2), (x + 0.04, -0.2), (x + 0.16, 0.16)) for x in (-0.46, 0.0, 0.44)))
        return [(bolts, SPARK), (cloud, IRON), (swirl, CYAN)]
    if name == "Skill_Gunslinger":
        # Two pistols crossed muzzles-out, both firing.
        def pistol(sign):
            barrel = g.box(sign * 0.12, 0.3, 0.42, 0.075, rot=sign * 0.5, rnd=0.03)
            grip = g.box(sign * -0.27, -0.06, 0.1, 0.22, rot=sign * 0.75, rnd=0.05)
            return barrel, grip
        rb, rg = pistol(1)
        lb, lg = pistol(-1)
        flashes = union(g.star(0.62, 0.62, 0.24, 0.09, 7), g.star(-0.62, 0.62, 0.24, 0.09, 7, 0.2))
        return [(flashes, ORANGE), (union(rg, lg), BROWN), (union(rb, lb), STEEL), (union(g.circle(0.62, 0.62, 0.08), g.circle(-0.62, 0.62, 0.08)), FLAME)]
    if name == "Skill_HiddenCannon":
        # A cannon rising out of an open trap door, firing.
        hatch = g.box(0, -0.6, 0.7, 0.14, rnd=0.03)
        hole = g.box(0, -0.6, 0.56, 0.08)
        lid = g.box(-0.62, -0.2, 0.06, 0.42, rot=0.25, rnd=0.02)
        barrel = union(g.line(-0.18, -0.38, 0.42, 0.22, 0.13), g.circle(-0.2, -0.4, 0.15))
        mouth = g.circle(0.44, 0.24, 0.12)
        return [(g.star(0.6, 0.4, 0.34, 0.14, 8), ORANGE), (g.star(0.6, 0.4, 0.17, 0.07, 8), FLAME), (hatch, BROWN), (hole, INK), (lid, BROWN),
                (barrel, IRON), (mouth, IRON_DARK)]
    if name == "Skill_Mutiny":
        # Two cutlasses clashing over a trap door: the crew turned on itself.
        hatch = union(g.box(0, -0.66, 0.6, 0.12, rnd=0.03))
        return [(hatch, BROWN), (g.box(0, -0.66, 0.48, 0.07), INK), (_sword(g, -0.72, -0.4, 0.5, 0.74), WHITE), (_sword(g, 0.72, -0.4, -0.5, 0.74), STEEL),
                (g.star(0, 0.34, 0.24, 0.08, 8), GOLD), (g.box(0.66, 0.5, 0.05, 0.16, rnd=0.02), RED), (g.circle(0.66, 0.24, 0.05), RED)]
    if name == "Skill_Necromancy":
        # Three dead pirates rising out of a violet mist, eyes lit green, the middle one in a tricorn.
        mist = union(g.circle(-0.56, -0.72, 0.22), g.circle(-0.2, -0.78, 0.26), g.circle(0.2, -0.78, 0.26), g.circle(0.56, -0.72, 0.22))
        layers = []
        for cx, cy, s in ((-0.55, 0.02, 0.42), (0.55, 0.02, 0.42)):
            layers += [(_skull(g, cx, cy, s), PALE), (union(g.circle(cx - 0.2 * s, cy + 0.04 * s, 0.07 * s), g.circle(cx + 0.2 * s, cy + 0.04 * s, 0.07 * s)), MINT)]
        cx, cy, s = 0.0, -0.12, 0.62
        # Front on, a tricorn is a low crown between two brim points cocked up at the sides.
        hat = g.poly((-0.72, 0.58), (-0.36, 0.2), (0.0, 0.13), (0.36, 0.2), (0.72, 0.58), (0.42, 0.42), (0.22, 0.58), (0.0, 0.64), (-0.22, 0.58), (-0.42, 0.42))
        trim = union(g.line(-0.68, 0.54, -0.36, 0.2, 0.03), g.line(-0.36, 0.2, 0.0, 0.14, 0.03), g.line(0.0, 0.14, 0.36, 0.2, 0.03), g.line(0.36, 0.2, 0.68, 0.54, 0.03))
        layers += [(_skull(g, cx, cy, s), WHITE), (union(g.circle(cx - 0.2 * s, cy + 0.04 * s, 0.07 * s), g.circle(cx + 0.2 * s, cy + 0.04 * s, 0.07 * s)), MINT),
                   (hat, IRON_DARK), (trim, GOLD), (mist, VIOLET)]
        return layers
    return None


def glyph_layers(name, g):
    """Painter's order list of (sdf, colour)."""
    skill = _skill_layers(name, g)
    if skill is not None:
        return skill
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
