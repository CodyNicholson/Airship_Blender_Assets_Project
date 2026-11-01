"""Image helpers for effects, skies and icons. numpy only, so it runs in Blender's own Python."""
import struct
import zlib

import numpy as np


def write_png(path, image):
    """image: float array in 0..1, (h, w, 3) or (h, w, 4). Uses the Up filter, which keeps smooth
    gradients small."""
    data = (np.clip(image, 0, 1) * 255 + 0.5).astype(np.uint8)
    h, w, channels = data.shape
    above = np.zeros_like(data)
    above[1:] = data[:-1]
    filtered = (data.astype(np.int16) - above) % 256
    raw = np.zeros((h, w * channels + 1), dtype=np.uint8)
    raw[:, 0] = 2
    raw[:, 1:] = filtered.reshape(h, -1)

    def chunk(tag, payload):
        return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)

    color_type = {3: 2, 4: 6}[channels]
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, color_type, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw.tobytes(), 9))
        + chunk(b"IEND", b"")
    )


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def ramp(value, stops, soft=0.012):
    """Posterised colour ramp: hard-ish steps between bands give the comic, cel-painted look.
    stops: [(threshold, (r, g, b) in 0..255), ...] ascending; the first threshold is ignored."""
    out = np.broadcast_to(np.array(stops[0][1], dtype=np.float32) / 255.0, value.shape + (3,)).copy()
    for threshold, color in stops[1:]:
        mix = smoothstep(threshold - soft, threshold + soft, value)[..., None]
        out = out * (1 - mix) + np.array(color, dtype=np.float32) / 255.0 * mix
    return out


def downsample(image, factor):
    if factor == 1:
        return image
    h, w = image.shape[:2]
    return image.reshape(h // factor, factor, w // factor, factor, -1).mean(axis=(1, 3)).squeeze()


def noise2(u, v, seed, k=0.0, count=14, freq=(1.0, 5.0), scroll=0.0, boil=1):
    """Sum of plane waves, about unit variance. With a whole-number time term it loops perfectly when
    k runs 0..1. scroll > 0 makes the pattern travel towards +v, like rising flame."""
    rng = np.random.default_rng(seed)
    total = np.zeros_like(u, dtype=np.float32)
    energy = 0.0
    for _ in range(count):
        f = rng.uniform(*freq)
        angle = rng.uniform(0, 2 * np.pi)
        kx, ky = f * np.cos(angle), f * np.sin(angle)
        phase = rng.uniform(0, 2 * np.pi)
        if scroll > 0:
            ky = abs(ky) + 0.5
            cycles = max(1, int(round(ky * scroll)))
        else:
            cycles = int(rng.integers(-boil, boil + 1))
        amp = 1.0 / f
        total += amp * np.cos(np.pi * (kx * u + ky * v) - 2 * np.pi * cycles * k + phase)
        energy += amp * amp / 2
    return total / np.sqrt(energy)


def noise3(x, y, z, seed, count=24, freq=(1.0, 6.0)):
    """The same wave noise on 3D positions. Sampling a sky on the unit sphere this way has no seam at
    the panorama's edge and no pinching at the poles."""
    rng = np.random.default_rng(seed)
    total = np.zeros_like(x, dtype=np.float32)
    energy = 0.0
    for _ in range(count):
        f = rng.uniform(*freq)
        direction = rng.normal(size=3)
        direction = direction / np.linalg.norm(direction) * f
        phase = rng.uniform(0, 2 * np.pi)
        amp = 1.0 / f
        total += amp * np.cos(2 * np.pi * (direction[0] * x + direction[1] * y + direction[2] * z) + phase)
        energy += amp * amp / 2
    return total / np.sqrt(energy)


def grid(size):
    """Pixel centres in -1..1, with +v up the image."""
    axis = (np.arange(size, dtype=np.float32) + 0.5) / size * 2 - 1
    u, v = np.meshgrid(axis, -axis)
    return u, v


def ink_outline(alpha, radius):
    """Dilates a coverage mask by radius pixels, for a comic ink line. Soft, and needs no scipy."""
    out = alpha.copy()
    steps = 12
    for i in range(steps):
        a = 2 * np.pi * i / steps
        dy, dx = int(round(np.sin(a) * radius)), int(round(np.cos(a) * radius))
        out = np.maximum(out, np.roll(np.roll(alpha, dy, 0), dx, 1))
    half = radius // 2
    if half:
        for i in range(steps):
            a = 2 * np.pi * i / steps
            dy, dx = int(round(np.sin(a) * half)), int(round(np.cos(a) * half))
            out = np.maximum(out, np.roll(np.roll(alpha, dy, 0), dx, 1))
    return out
