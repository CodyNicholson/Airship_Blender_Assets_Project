"""Sky panoramas for each act: equirectangular, wrapping horizontally, painted in flat cloud bands to
match the comic portraits and flipbooks.

Everything samples the view direction on a sphere, so there's no seam or pole pinch. Image centre looks
along glTF +Z. fx_catalog.SKIES holds matching sun, ambient and fog values, so ships sit in their sky.

    fx_skies.generate_all()   # inside Blender, which has numpy
"""
import numpy as np

import fx_catalog
from fx_image import downsample, noise3, ramp, smoothstep, write_png
import palette


def _rgb(c):
    return np.array(c, dtype=np.float32) / 255.0


def _directions(width, height):
    lon = (np.arange(width, dtype=np.float32) + 0.5) / width * 2 * np.pi - np.pi
    lat = np.pi / 2 - (np.arange(height, dtype=np.float32) + 0.5) / height * np.pi
    lon, lat = np.meshgrid(lon, lat)
    return np.cos(lat) * np.sin(lon), np.sin(lat), np.cos(lat) * np.cos(lon)


def _gradient(y, stops):
    """Smooth vertical colour: stops are (sin(elevation), colour), ascending."""
    out = np.zeros(y.shape + (3,), dtype=np.float32)
    levels = np.array([s[0] for s in stops], dtype=np.float32)
    for channel in range(3):
        out[..., channel] = np.interp(y, levels, [s[1][channel] / 255.0 for s in stops])
    return out


def _paint(image, colour, alpha):
    image[...] = image * (1 - alpha[..., None]) + colour * alpha[..., None]


def _glow(image, cos_sun, colour, tightness, strength):
    amount = np.clip(cos_sun, 0, 1) ** tightness * strength
    _paint(image, _rgb(colour), np.clip(amount, 0, 1))


def _disc(image, cos_sun, size_deg, colour):
    edge = np.cos(np.radians(size_deg))
    _paint(image, _rgb(colour), smoothstep(edge - 0.00025, edge + 0.00025, cos_sun))


def _stars(image, y, width, height, seed, density, fade_below):
    rng = np.random.default_rng(seed)
    # Density is per output pixel. Each star is drawn as a 2x2 block, so it survives the reduction.
    count = int(width * height * density / 4)
    rows = rng.integers(0, height - 1, count)
    cols = rng.integers(0, width, count)
    # Thin out towards the poles, where a panorama stretches each pixel sideways.
    keep = rng.random(count) < np.cos((rows + 0.5) / height * np.pi - np.pi / 2)
    rows, cols = rows[keep], cols[keep]
    bright = rng.uniform(0.35, 1.0, rows.shape) * smoothstep(fade_below, fade_below + 0.25, y[rows, cols])
    for dy, dx in ((0, 0), (0, 1), (1, 0), (1, 1)):
        r, c = rows + dy, (cols + dx) % width
        image[r, c] = image[r, c] * (1 - bright[:, None]) + np.array((1.0, 0.98, 0.92)) * bright[:, None]


def _sea(image, x, y, z, seed, bands, scale, haze, sun, top=-0.015):
    """Cloud deck below the horizon, seen in perspective: the top of the Undertow's weather."""
    below = np.maximum(-y, 0.012)
    px, pz = x / below, z / below
    zero = np.zeros_like(px)
    # Broad swells with fine billows only at their crests. Quiet on purpose: ships are the subject.
    fine = noise3(px * scale * 1.5, zero, pz * scale * 1.5, seed, count=24, freq=(1.0, 6.0))
    broad = noise3(px * scale * 0.42, zero, pz * scale * 0.42, seed + 1, count=14, freq=(0.5, 2.5))
    sx, sz = sun[0] * 0.09, sun[2] * 0.09
    relit = noise3((px + sx) * scale * 1.5, zero, (pz + sz) * scale * 1.5, seed, count=24, freq=(1.0, 6.0))
    value = 0.78 * broad + 0.22 * fine + (fine - relit) * 0.9
    # Shadows sit close to the midtone, so the deck never turns into a high-contrast pattern.
    shadow = tuple(0.5 * a + 0.5 * b for a, b in zip(bands[0][1], bands[1][1]))
    bands = [(bands[0][0], shadow)] + list(bands[1:])
    colour = ramp(value, bands, soft=0.07)
    # Near the horizon the waves would alias, so they melt into the haze colour.
    distant = smoothstep(0.012, 0.16, -y)
    colour = colour * distant[..., None] + _rgb(haze) * (1 - distant[..., None])
    _paint(image, colour, smoothstep(top + 0.008, top - 0.008, y))


def _bank(image, x, y, z, seed, bands, top, sun=None, sun_lit=None, base=-0.02):
    """A cumulus skyline on the horizon: an outline over longitude, so towers have real silhouettes."""
    flat = np.maximum(np.sqrt(x * x + z * z), 1e-3)
    hx, hz = x / flat, z / flat
    zero = np.zeros_like(hx)
    # Towers, then scallops on the towers for the puffy edge.
    towers = noise3(hx * 0.8, zero, hz * 0.8, seed, count=14, freq=(0.8, 3.5))
    puffs = np.abs(noise3(hx * 3.2, zero, hz * 3.2, seed + 1, count=14, freq=(1.0, 4.0)))
    ridge = top * np.clip(0.42 + 0.34 * towers + 0.22 * puffs, 0.04, 1.3)
    field = (ridge - y) / max(top, 1e-3)
    shade = field + 0.12 * noise3(x * 5, y * 16, z * 5, seed + 2, count=16, freq=(1.0, 5.0))
    colour = ramp(shade, bands, soft=0.03)
    if sun is not None and sun_lit is not None:
        cos_sun = np.clip(hx * sun[0] + hz * sun[2], 0, 1) ** 4
        _paint(colour, _rgb(sun_lit), cos_sun * smoothstep(0.32, 0.06, shade) * 0.85)
    _paint(image, colour, smoothstep(0.0, 0.012, field) * smoothstep(base - 0.01, base + 0.01, y))


def _cirrus(image, x, y, z, seed, color, amount, stretch=(0.35, 3.2), low=0.2, opacity=0.8, freq=(0.8, 4.5), axis=0.0):
    """High wisps overhead: stretched noise on a plane above the viewer, with soft trailing edges.
    Strongest overhead and fading well before the horizon, where the plane's perspective bunches up."""
    up = np.maximum(y, 0.05)
    px, pz = x / up, z / up
    ca, sa = np.cos(axis), np.sin(axis)
    a, b = px * ca - pz * sa, px * sa + pz * ca
    field = noise3(a * stretch[0], np.zeros_like(a), b * stretch[1], seed, count=20, freq=freq)
    mask = smoothstep(amount, amount + 0.75, field) * smoothstep(low, low + 0.3, y) * opacity
    _paint(image, _rgb(color), mask)


def _twist(x, y, z, turns):
    """Rotates directions about the vertical by an amount that grows towards the zenith: the vortex."""
    angle = turns * np.clip(y, -1, 1)
    c, s = np.cos(angle), np.sin(angle)
    return x * c - z * s, y, x * s + z * c


def cloud_break(image, x, y, z, sun, w, h):
    cos_sun = x * sun[0] + y * sun[1] + z * sun[2]
    image[...] = _gradient(y, [(-1, (250, 196, 130)), (0.0, (255, 214, 150)), (0.08, (255, 190, 134)), (0.24, (190, 188, 204)), (0.55, (96, 142, 206)), (1, (46, 92, 170))])
    _glow(image, cos_sun, (255, 238, 180), 32, 0.75)
    _cirrus(image, x, y, z, 104, (255, 232, 214), 0.55, stretch=(0.4, 1.6), opacity=0.7, axis=0.5)
    _disc(image, cos_sun, 2.6, (255, 250, 226))
    _glow(image, cos_sun, (255, 246, 210), 700, 0.85)
    _bank(image, x, y, z, 102, [(-1, (255, 230, 196)), (0.28, (250, 196, 158)), (0.7, (232, 164, 142))], 0.2, sun=sun, sun_lit=(255, 246, 206))
    _sea(image, x, y, z, 101, [(-3, (226, 164, 150)), (-0.32, (242, 190, 164)), (0.3, (255, 220, 184))], 0.5, (255, 214, 170), sun)


def scrap_winds(image, x, y, z, sun, w, h):
    cos_sun = x * sun[0] + y * sun[1] + z * sun[2]
    image[...] = _gradient(y, [(-1, (58, 56, 34)), (0.0, (134, 128, 74)), (0.2, (152, 148, 88)), (0.55, (122, 128, 84)), (1, (84, 94, 72))])
    _glow(image, cos_sun, (226, 214, 124), 8, 0.55)
    _disc(image, cos_sun, 3.4, (240, 232, 170))
    _cirrus(image, x, y, z, 204, (96, 94, 58), 0.1, stretch=(0.7, 1.2), low=0.08, opacity=0.6, axis=1.1)
    # Two banks of smog: the Scrap-Winds close in from every side.
    _bank(image, x, y, z, 203, [(-1, (126, 124, 68)), (0.3, (108, 106, 58)), (0.8, (92, 92, 48))], 0.3)
    _bank(image, x, y, z, 202, [(-1, (112, 112, 58)), (0.3, (86, 86, 46)), (0.8, (66, 64, 38))], 0.2, sun=sun, sun_lit=(170, 166, 90))
    _sea(image, x, y, z, 201, [(-3, (50, 46, 30)), (-0.3, (68, 66, 36)), (0.32, (92, 96, 46))], 0.6, (120, 116, 66), sun)


def jetstream(image, x, y, z, sun, w, h):
    cos_sun = x * sun[0] + y * sun[1] + z * sun[2]
    image[...] = _gradient(y, [(-1, (88, 176, 214)), (0.0, (206, 240, 248)), (0.1, (160, 222, 246)), (0.42, (70, 160, 238)), (1, (24, 92, 200))])
    _glow(image, cos_sun, (255, 255, 240), 40, 0.5)
    # Long jet-stream streaks, all running one way: the act's sense of speed.
    _cirrus(image, x, y, z, 303, (255, 255, 255), 0.5, stretch=(0.1, 1.9), opacity=0.85, axis=0.25)
    _cirrus(image, x, y, z, 306, (222, 244, 255), 0.55, stretch=(0.07, 1.3), low=0.12, opacity=0.7, axis=0.25)
    _disc(image, cos_sun, 2.4, (255, 255, 244))
    _glow(image, cos_sun, (255, 255, 240), 500, 0.8)
    _bank(image, x, y, z, 302, [(-1, (255, 255, 255)), (0.3, (222, 240, 250)), (0.75, (170, 216, 240))], 0.14)
    _sea(image, x, y, z, 301, [(-3, (150, 208, 234)), (-0.3, (198, 232, 244)), (0.28, (248, 252, 255))], 0.42, (214, 240, 250), sun)


def cirrus_citadel(image, x, y, z, sun, w, h):
    cos_sun = x * sun[0] + y * sun[1] + z * sun[2]
    image[...] = _gradient(y, [(-1, (20, 18, 44)), (0.0, (64, 58, 110)), (0.12, (52, 46, 104)), (0.42, (26, 26, 70)), (1, (8, 10, 34))])
    _stars(image, y, w, h, 404, 0.0016, 0.1)
    _glow(image, cos_sun, (150, 170, 240), 60, 0.5)
    _cirrus(image, x, y, z, 403, (92, 98, 164), 0.55, stretch=(0.2, 1.4), opacity=0.5, axis=-0.6)
    _disc(image, cos_sun, 4.2, (232, 238, 255))
    # Maria on the moon: keeps it from being a flat white dot in the most atmospheric act.
    maria = noise3(x * 30, y * 30, z * 30, 405, count=10, freq=(0.6, 2.0))
    _paint(image, _rgb((190, 202, 232)), smoothstep(np.cos(np.radians(4.0)) - 0.0002, np.cos(np.radians(4.0)) + 0.0002, cos_sun) * smoothstep(0.1, 0.4, maria))
    _bank(image, x, y, z, 402, [(-1, (98, 100, 164)), (0.26, (58, 56, 112)), (0.7, (38, 36, 84))], 0.14, sun=sun, sun_lit=(176, 190, 244))
    _sea(image, x, y, z, 401, [(-3, (24, 24, 56)), (-0.3, (38, 38, 80)), (0.32, (70, 74, 132))], 0.5, (62, 58, 110), sun)


def maelstrom(image, x, y, z, sun, w, h):
    image[...] = _gradient(y, [(-1, (8, 6, 18)), (-0.05, (34, 28, 58)), (0.2, (42, 36, 76)), (0.8, (58, 50, 110)), (0.96, (150, 146, 226)), (1, (226, 228, 255))])
    # The vortex wall: storm bands that climb and spiral towards the eye.
    tx, ty, tz = _twist(x, y, z, 5.4)
    field = noise3(tx * 0.6, ty * 3.6, tz * 0.6, 502, count=28, freq=(0.8, 6.0))
    inside_eye = smoothstep(0.985, 0.9, y)
    colour = ramp(field, [(-3, (24, 20, 44)), (-0.5, (44, 38, 76)), (0.15, (72, 66, 122)), (0.9, (116, 112, 178))], soft=0.05)
    _paint(image, colour, inside_eye * smoothstep(-0.02, 0.02, y + 0.03))
    # Lightning light inside the wall: broad blooms that give the storm depth and a place to look.
    bloom = noise3(x * 0.9, y * 1.2, z * 0.9, 505, count=10, freq=(0.6, 2.0))
    light = smoothstep(0.35, 1.4, bloom) * smoothstep(0.0, 0.14, y) * inside_eye * 0.8
    _paint(image, ramp(field, [(-3, (84, 62, 170)), (0.0, (136, 110, 224)), (0.7, (206, 202, 255))], soft=0.05), light)
    # The eye's lit rim.
    rim = smoothstep(0.8, 0.9, y) * smoothstep(0.985, 0.93, y) * smoothstep(-0.3, 0.8, field)
    _paint(image, _rgb((176, 172, 240)), rim * 0.75)
    # Black storm towers close in along the horizon.
    _bank(image, x, y, z, 506, [(-1, (58, 50, 100)), (0.2, (32, 28, 58)), (0.6, (16, 14, 32))], 0.3)
    _sea(image, x, y, z, 501, [(-3, (10, 8, 20)), (-0.3, (22, 18, 40)), (0.36, (48, 38, 86))], 0.6, (30, 26, 52), sun)


def quarterdeck_dusk(image, x, y, z, sun, w, h):
    cos_sun = x * sun[0] + y * sun[1] + z * sun[2]
    image[...] = _gradient(y, [(-1, (84, 44, 88)), (0.0, (250, 150, 96)), (0.09, (246, 132, 104)), (0.28, (172, 92, 140)), (0.62, (72, 62, 130)), (1, (30, 32, 90))])
    _stars(image, y, w, h, 604, 0.0005, 0.45)
    _glow(image, cos_sun, (255, 196, 110), 16, 0.65)
    _cirrus(image, x, y, z, 603, (250, 150, 130), 0.55, stretch=(0.3, 1.5), opacity=0.66, axis=0.9)
    _disc(image, cos_sun, 3.4, (255, 226, 150))
    _glow(image, cos_sun, (255, 214, 130), 420, 0.8)
    _bank(image, x, y, z, 602, [(-1, (236, 132, 108)), (0.26, (170, 84, 118)), (0.72, (112, 62, 112))], 0.15, sun=sun, sun_lit=(255, 206, 122))
    _sea(image, x, y, z, 601, [(-3, (92, 50, 96)), (-0.3, (136, 70, 112)), (0.32, (222, 122, 106))], 0.5, (238, 136, 104), sun)


def free_dawn(image, x, y, z, sun, w, h):
    cos_sun = x * sun[0] + y * sun[1] + z * sun[2]
    image[...] = _gradient(y, [(-1, (188, 214, 234)), (0.0, (255, 236, 198)), (0.1, (255, 222, 176)), (0.32, (168, 212, 232)), (0.68, (94, 170, 232)), (1, (50, 128, 216))])
    _glow(image, cos_sun, (255, 244, 200), 22, 0.75)
    _cirrus(image, x, y, z, 703, (255, 244, 226), 0.65, stretch=(0.32, 1.3), opacity=0.62, axis=-0.3)
    _disc(image, cos_sun, 3.0, (255, 254, 236))
    _glow(image, cos_sun, (255, 252, 226), 550, 0.9)
    _bank(image, x, y, z, 702, [(-1, (255, 252, 240)), (0.28, (250, 222, 204)), (0.72, (222, 190, 186))], 0.18, sun=sun, sun_lit=(255, 250, 214))
    _sea(image, x, y, z, 701, [(-3, (204, 208, 224)), (-0.3, (234, 228, 224)), (0.28, (255, 248, 230))], 0.45, (255, 234, 204), sun)


PAINTERS = {
    "CloudBreak": cloud_break, "ScrapWinds": scrap_winds, "Jetstream": jetstream, "CirrusCitadel": cirrus_citadel,
    "Maelstrom": maelstrom, "QuarterdeckDusk": quarterdeck_dusk, "FreeDawn": free_dawn,
}


def sky_path(name, quality):
    return palette.TEXTURE_DIR / f"T_Sky_{name}_{quality}.png"


def build(name, quality):
    width, height = fx_catalog.SKY_SIZES[quality]
    # Painted at twice the size then reduced. A sky is magnified several times on a phone, and without
    # real edge anti-aliasing its hard cloud bands turn into visible stair-steps.
    samples = 2
    w, h = width * samples, height * samples
    x, y, z = _directions(w, h)
    image = np.zeros((h, w, 3), dtype=np.float32)
    sun = np.array(fx_catalog.SKIES[name]["sun_dir"], dtype=np.float32)
    sun = sun / np.linalg.norm(sun)
    PAINTERS[name](image, x, y, z, sun, w, h)
    return np.clip(downsample(image, samples), 0, 1)


def generate(name):
    written = []
    for quality in ("HQ", "LQ"):
        path = sky_path(name, quality)
        write_png(path, build(name, quality))
        written.append(path)
    return written


def generate_all():
    return [str(p) for name in fx_catalog.SKIES for p in generate(name)]
