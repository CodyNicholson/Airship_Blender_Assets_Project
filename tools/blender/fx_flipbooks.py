"""Flipbook sprite sheets for fire, smoke, explosions and friends.

Painted in the comic style of the portraits: hard colour bands and clean silhouettes, not soft
realistic plumes. It reads at phone size, and its flat bands suit ASTC compression. Each effect is
a function returning (rgb, alpha) for one frame; k runs 0..1 over the animation.

    fx_flipbooks.generate_all()   # inside Blender, which has numpy
"""
import numpy as np

import fx_catalog
from fx_image import downsample, grid, noise2, ramp, smoothstep, write_png
import palette

FIRE = [(0.0, (170, 30, 12)), (0.2, (242, 92, 20)), (0.46, (255, 178, 44)), (0.74, (255, 240, 176))]
PLASMA = [(0.0, (120, 40, 220)), (0.26, (190, 92, 255)), (0.56, (232, 180, 255)), (0.8, (255, 250, 255))]
BLAST = [(0.0, (150, 34, 14)), (0.14, (232, 78, 18)), (0.38, (255, 170, 40)), (0.68, (255, 238, 170)), (1.0, (255, 255, 240))]
BLAST_FLAK = [(0.0, (190, 56, 16)), (0.2, (240, 110, 24)), (0.5, (255, 196, 70)), (0.84, (255, 244, 190))]
LIFT = [(0.0, (18, 110, 150)), (0.3, (72, 224, 232)), (0.68, (214, 252, 250))]
SPARK = [(0.0, (240, 110, 24)), (0.4, (255, 196, 70)), (0.74, (255, 250, 210))]
BOLT = [(0.0, (92, 110, 230)), (0.3, (170, 196, 255)), (0.7, (250, 252, 255))]


def _radial(u, v):
    return np.hypot(u, v), np.arctan2(v, u)


def fire(u, v, k):
    y = np.clip((v + 0.88) / 1.84, 0, 1)
    # Rounded at the root, so it sits on a deck as a flame rather than a cut-off shape.
    width = 0.74 * np.clip(1 - y, 0.001, 1) ** 0.8 * np.clip(y / 0.2, 0.001, 1) ** 0.5
    sway = 0.2 * noise2(u * 0.4, v, 11, k, count=6, freq=(0.6, 1.6), scroll=1.0) * y
    shape = 1 - np.abs(u - sway) / width
    detail = noise2(u, v, 12, k, count=16, freq=(1.8, 6.5), scroll=1.0)
    heat = shape + 0.28 * detail * (0.25 + y) - y * 0.24
    heat = np.where(v < -0.88, -1.0, heat)  # Nothing below the root.
    return ramp(heat, FIRE), smoothstep(0.0, 0.06, heat)


def plume(u, v, k):
    y = (v + 1) / 2
    width = 0.46 * np.clip(1 - y, 0.001, 1) ** 0.72 * np.minimum(1.0, (y + 0.12) / 0.16) ** 0.5
    detail = noise2(u, v, 21, k, count=12, freq=(1.5, 5.0), scroll=2.0)
    heat = 1 - np.abs(u) / width + 0.2 * detail * y - y * 0.14
    return ramp(heat, PLASMA), smoothstep(0.0, 0.08, heat)


def _billow(u, v, seed, scale, lift=0.0, lobes=7):
    """A cluster of round lobes. Returns (height 0..1, lighting). Used by smoke and fireballs alike."""
    rng = np.random.default_rng(seed)
    x, y = u / scale, (v - lift) / scale
    # Only a gentle, low-frequency warp: more than this and the lobes turn into faceted rocks.
    x = x + 0.05 * noise2(u, v, seed + 1, 0.0, count=6, freq=(0.8, 2.2))
    y = y + 0.05 * noise2(u, v, seed + 2, 0.0, count=6, freq=(0.8, 2.2))
    height = np.zeros_like(u)
    lit = np.zeros_like(u)
    for i in range(lobes):
        centre = i == lobes - 1
        a = 2 * np.pi * i / (lobes - 1) + rng.uniform(-0.25, 0.25)
        r = 0.0 if centre else rng.uniform(0.34, 0.5)
        radius = 0.66 if centre else rng.uniform(0.38, 0.5)
        dx, dy = (x - r * np.cos(a)) / radius, (y - r * np.sin(a)) / radius
        h = np.sqrt(np.clip(1 - dx * dx - dy * dy, 0, 1))
        here = h > height
        lit = np.where(here, -dx * 0.5 + dy * 0.72 + h * 0.42, lit)
        height = np.maximum(height, h)
    return height, lit


def _erode(height, u, v, seed, fade):
    """Dissolves a puff from its edges and into wisps as fade runs 0..1."""
    wisps = noise2(u, v, seed + 3, 0.0, count=12, freq=(1.5, 5.5))
    cut = fade * 1.35 - 0.1
    return smoothstep(cut, cut + 0.22, height + 0.16 * wisps + 0.06)


def _puff(u, v, k, seed, bands, grow=(0.34, 0.9), erode_from=0.45):
    scale = grow[0] + (grow[1] - grow[0]) * (1 - (1 - k) ** 2)
    height, lit = _billow(u, v, seed, scale, lift=0.1 * k)
    fade = np.clip((k - erode_from) / (1 - erode_from), 0, 1)
    return ramp(lit, bands, soft=0.03), smoothstep(0.0, 0.1, height) * _erode(height, u, v, seed, fade)


def smoke_dark(u, v, k):
    return _puff(u, v, k, 31, [(-2, (40, 38, 44)), (0.02, (58, 56, 62)), (0.56, (82, 80, 86))])


def smoke_light(u, v, k):
    return _puff(u, v, k, 34, [(-2, (186, 186, 192)), (0.02, (216, 216, 218)), (0.56, (244, 242, 236))], grow=(0.22, 0.86))


def gas_leak(u, v, k):
    return _puff(u, v, k, 37, [(-2, (168, 222, 222)), (0.02, (204, 240, 236)), (0.56, (238, 252, 246))], grow=(0.16, 0.9), erode_from=0.2)


def toxic_smog(u, v, k):
    return _puff(u, v, k, 41, [(-2, (92, 106, 50)), (0.02, (118, 136, 60)), (0.56, (150, 170, 74))], grow=(0.46, 0.94), erode_from=0.3)


def _blast(u, v, k, seed, stops, smoke, cool, reach, spike_until, lobes=7):
    """A fireball that burns out into the same billows as the smoke, cooling from the rim inward."""
    scale = 0.2 + (reach - 0.2) * (1 - (1 - k) ** 4)
    height, lit = _billow(u, v, seed, scale, lift=0.14 * k * k, lobes=lobes)
    temperature = height * 1.25 + lit * 0.2 + 0.25 - k * cool
    hot = ramp(temperature, stops, soft=0.02)
    cold = ramp(lit, smoke, soft=0.03)
    mix = smoothstep(0.0, 0.05, temperature)[..., None]
    colour = cold * (1 - mix) + hot * mix
    fade = np.clip((k - 0.6) / 0.4, 0, 1)
    alpha = smoothstep(0.0, 0.1, height) * _erode(height, u, v, seed, fade)
    # A comic starburst on the first frames only: it's the bang, not the fireball.
    if k < spike_until:
        strength = 1 - k / spike_until
        d, angle = _radial(u, v)
        star = (0.26 + 0.7 * np.abs(np.cos(angle * 4.0 + 0.4)) ** 7) * (0.55 + 0.45 * strength)
        burst = smoothstep(0.0, 0.03, 1 - d / star)
        colour = colour * (1 - burst[..., None]) + np.array((1.0, 0.92, 0.6)) * burst[..., None]
        alpha = np.maximum(alpha, burst)
    return colour, alpha


SMOKE_BLAST = [(-2, (34, 30, 34)), (0.02, (56, 50, 52)), (0.56, (88, 78, 76))]
SMOKE_FLAK = [(-2, (22, 20, 24)), (0.02, (34, 32, 38)), (0.56, (56, 54, 60))]


def explosion(u, v, k):
    return _blast(u, v, k, 51, BLAST, SMOKE_BLAST, cool=2.15, reach=0.84, spike_until=0.09)


def flak(u, v, k):
    return _blast(u, v, k, 55, BLAST_FLAK, SMOKE_FLAK, cool=2.7, reach=0.7, spike_until=0.13)


def muzzle(u, v, k):
    frame = int(k * 4)
    scale = (0.72, 1.0, 0.82, 0.46)[frame]
    twist = (0.2, 0.75, 1.3, 1.9)[frame]
    d, angle = _radial(u, v)
    reach = scale * (0.26 + 0.72 * np.abs(np.cos(angle * 3.5 + twist)) ** 5)
    heat = 1 - d / reach
    return ramp(heat, SPARK), smoothstep(0.0, 0.08, heat)


def _streaks(u, v, k, seed, count, travel, length, width):
    """A coverage mask of radial streaks flying outward, with their ages for colouring."""
    rng = np.random.default_rng(seed)
    mask = np.zeros_like(u)
    for _ in range(count):
        a = rng.uniform(0, 2 * np.pi)
        speed = rng.uniform(0.55, 1.0)
        head = 0.1 + travel * speed * (1 - (1 - k) ** 2)
        tail = max(0.02, head - length * (1 - k * 0.65) * speed)
        ax, ay, bx, by = tail * np.cos(a), tail * np.sin(a), head * np.cos(a), head * np.sin(a)
        dx, dy = bx - ax, by - ay
        h = np.clip(((u - ax) * dx + (v - ay) * dy) / (dx * dx + dy * dy + 1e-6), 0, 1)
        dist = np.hypot(u - ax - dx * h, v - ay - dy * h)
        thick = width * (0.25 + 0.75 * h) * (1 - k * 0.55)
        mask = np.maximum(mask, 1 - dist / np.maximum(thick, 1e-3))
    return mask


def sparks(u, v, k):
    mask = _streaks(u, v, k, 61, 16, 0.86, 0.5, 0.05)
    return ramp(mask - k * 0.25, SPARK), smoothstep(0.0, 0.3, mask) * smoothstep(1.0, 0.72, k)


def lift_burst(u, v, k):
    mask = _streaks(u, v, k, 65, 12, 0.72, 0.42, 0.075)
    d, _ = _radial(u, v)
    ring_at = 0.1 + 0.8 * (1 - (1 - k) ** 2)
    ring = 1 - np.abs(d - ring_at) / np.maximum(0.06 * (1 - k), 0.005)
    core = (0.36 * (1 - k) ** 2 - d) / 0.36
    all_ = np.maximum(np.maximum(mask, ring), core * 2)
    return ramp(all_, LIFT), smoothstep(0.0, 0.12, all_) * smoothstep(1.0, 0.76, k)


def shockwave(u, v, k):
    d, _ = _radial(u, v)
    ring_at = 0.08 + 0.84 * (1 - (1 - k) ** 2.2)
    band = np.maximum(0.15 * (1 - k) ** 1.3, 0.008)
    ring = 1 - np.abs(d - ring_at) / band
    alpha = smoothstep(0.0, 0.45, ring) * (1 - k) ** 0.8
    return ramp(ring, [(0.0, (130, 190, 255)), (0.55, (250, 252, 255))]), alpha


def lightning_flash(u, v, k):
    frame = int(k * 4)
    strength = (1.0, 0.45, 0.85, 0.22)[frame]
    d, _ = _radial(u, v)
    wander = 0.26 * noise2(v * 1.0 + frame // 2, v * 0.0, 71 + frame // 2, 0.0, count=10, freq=(1.0, 7.0))
    bolt = 1 - np.abs(u - wander) / (0.018 + 0.05 * (1 - np.abs(v)))
    glow = np.clip(1 - d * 1.02, 0, 1) ** 1.6 * 0.5 * strength
    alpha = np.maximum(smoothstep(0.0, 0.4, bolt) * strength, glow)
    return ramp(np.maximum(bolt, glow * 0.5), BOLT), np.clip(alpha, 0, 1)


def slash(u, v, k):
    """Crescent that sweeps over the frame then thins out."""
    d, angle = _radial(u, v)
    head = -2.1 + 4.2 * smoothstep(0.0, 0.42, np.asarray(k))
    tail = -2.1 + 4.2 * smoothstep(0.26, 0.96, np.asarray(k))
    along = np.clip((angle - tail) / max(head - tail, 1e-3), 0, 1)
    inside = (angle >= tail) & (angle <= head)
    thick = 0.17 * np.sin(np.pi * along) ** 0.7 * (1 - k * 0.3)
    arc = 1 - np.abs(d - 0.72) / np.maximum(thick, 1e-3)
    value = np.where(inside, arc, -1.0)
    return ramp(value, [(-1, (120, 170, 230)), (0.3, (205, 228, 255)), (0.6, (255, 255, 255))]), smoothstep(0.0, 0.18, value)


def rain(u, v, _k):
    rng = np.random.default_rng(81)
    alpha = np.zeros_like(u)
    height = u.shape[0]
    for _ in range(46):
        x0, y0 = rng.uniform(-1, 1), rng.uniform(-1, 1)
        length = rng.uniform(0.1, 0.26)
        dy = (v - y0 + 1) % 2 - 1
        dx = (u - x0 - dy * 0.1 + 1) % 2 - 1
        streak = (1 - np.abs(dx) / (2.6 / height)) * (np.abs(dy) < length)
        alpha = np.maximum(alpha, np.clip(streak, 0, 1) * rng.uniform(0.35, 0.8))
    return np.broadcast_to(np.array((0.8, 0.88, 1.0)), u.shape + (3,)).copy(), alpha


def ember(u, v, _k):
    d, _ = _radial(u, v)
    heat = 1 - d
    return ramp(heat, [(0.0, (240, 90, 20)), (0.3, (255, 180, 60)), (0.68, (255, 250, 220))]), smoothstep(0.0, 0.7, heat)


PAINTERS = {
    "Fire": fire, "SmokeDark": smoke_dark, "SmokeLight": smoke_light, "GasLeak": gas_leak, "ToxicSmog": toxic_smog,
    "Explosion": explosion, "FlakBurst": flak, "MuzzleFlash": muzzle, "Sparks": sparks,
    "AfterburnerPlume": plume, "LiftBurst": lift_burst, "Shockwave": shockwave, "LightningFlash": lightning_flash,
    "SlashArc": slash, "Rain": rain, "Ember": ember,
}


def flipbook_path(name, quality):
    return palette.TEXTURE_DIR / f"T_VFX_{name}_{quality}.png"


def build(name, quality):
    layout, _fps, looping, _blend, _anchor = fx_catalog.FLIPBOOKS[name]
    columns, cell = fx_catalog.LAYOUTS[layout][quality]
    frames = columns * columns
    samples = 2  # Painted at double size then reduced: clean edges even at 64 px cells.
    u, v = grid(cell * samples)
    border = smoothstep(1.0, 0.95, np.maximum(np.abs(u), np.abs(v)))
    atlas = np.zeros((columns * cell, columns * cell, 4), dtype=np.float32)
    painter = PAINTERS[name]
    tile = layout == "tile"
    for frame in range(frames):
        # A loop's last frame must lead back to its first; a one-shot's last frame reaches the end.
        k = frame / frames if looping else frame / max(1, frames - 1)
        if layout == "flash":
            k = frame / frames
        rgb, alpha = painter(u, v, float(k))
        if not tile:
            alpha = alpha * border  # Keeps neighbouring frames from bleeding when mip-mapped.
        image = np.dstack((rgb, alpha))
        row, col = frame // columns, frame % columns
        atlas[row * cell:(row + 1) * cell, col * cell:(col + 1) * cell] = downsample(image, samples)
    return atlas


def generate(name):
    written = []
    for quality in ("HQ", "LQ"):
        path = flipbook_path(name, quality)
        write_png(path, build(name, quality))
        written.append(path)
    return written


def generate_all():
    return [str(p) for name in fx_catalog.FLIPBOOKS for p in generate(name)]
