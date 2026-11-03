"""Shared palette atlas for every model in the game.

All meshes UV into an 8x8 grid of colour swatches, so HQ and LQ share UVs and any
faction atlas can be swapped in at runtime without touching the mesh.

Pure standard library. Run with any Python to (re)generate the PNGs:
    python3 tools/blender/palette.py
"""
import random
import struct
import zlib
from pathlib import Path

GRID = 8
HQ_SIZE = 512  # Fits every high-quality tier's atlas limit (prop tier caps at 512).
LQ_SIZE = 128
DEFAULT_FACTION = "Crimson"
TEXTURE_DIR = Path(__file__).resolve().parents[2] / "assets" / "textures" / "production"

# name, sRGB colour, surface detail painted into the HQ atlas.
SWATCHES = [
    ("wood_dark", (58, 38, 28), "wood"),
    ("wood_mid", (106, 68, 40), "wood"),
    ("wood_light", (158, 110, 66), "wood"),
    ("wood_deck", (178, 138, 92), "wood"),
    ("wood_red", (122, 46, 34), "wood"),
    ("iron", (56, 60, 68), "metal"),
    ("iron_light", (108, 114, 122), "metal"),
    ("brass", (186, 142, 62), "metal"),
    ("gold", (244, 190, 58), "metal"),
    ("silver", (190, 198, 206), "metal"),
    ("rope", (176, 146, 98), "cloth"),
    ("canvas", (226, 212, 180), "cloth"),
    ("canvas_dark", (170, 154, 126), "cloth"),
    ("leather", (98, 62, 38), "cloth"),
    ("leather_dark", (48, 34, 30), "cloth"),
    ("faction_a", None, "cloth"),
    ("faction_b", None, "cloth"),
    ("faction_c", None, "cloth"),
    ("skin_light", (236, 188, 150), "soft"),
    ("skin_mid", (196, 138, 96), "soft"),
    ("skin_dark", (122, 78, 54), "soft"),
    ("hair_black", (34, 30, 32), "soft"),
    ("hair_brown", (84, 52, 32), "soft"),
    ("hair_gray", (150, 150, 150), "soft"),
    ("hair_red", (158, 70, 34), "soft"),
    ("cloth_white", (232, 228, 218), "cloth"),
    ("cloth_black", (42, 42, 50), "cloth"),
    ("cloth_blue", (48, 72, 118), "cloth"),
    ("cloth_green", (64, 98, 62), "cloth"),
    ("cloth_brown", (108, 80, 54), "cloth"),
    ("rock", (122, 112, 104), "rock"),
    ("rock_dark", (84, 78, 76), "rock"),
    ("grass", (106, 152, 72), "soft"),
    ("grass_dark", (72, 116, 60), "soft"),
    ("cloud", (246, 248, 252), "flat"),
    ("cloud_shade", (200, 212, 230), "flat"),
    ("glass", (78, 138, 96), "flat"),
    ("amber", (190, 112, 34), "flat"),
    ("gem_red", (196, 36, 60), "flat"),
    ("gem_blue", (44, 110, 206), "flat"),
    ("eye_white", (240, 238, 232), "flat"),
    ("eye_dark", (22, 20, 24), "flat"),
    ("lamp", (255, 190, 90), "flat"),
    # Campaign additions. Appended only: existing swatches must keep their atlas cells.
    ("rust", (150, 78, 42), "metal"),
    ("rust_dark", (92, 52, 36), "metal"),
    ("steel", (70, 84, 104), "metal"),
    ("gold_dark", (172, 128, 44), "metal"),
    ("enamel", (226, 222, 208), "soft"),
    ("navy", (34, 44, 74), "wood"),
    ("liftstone", (72, 224, 232), "flat"),
    ("liftstone_dark", (28, 108, 130), "rock"),
    ("ember", (255, 112, 32), "flat"),
    ("lightning", (214, 232, 255), "flat"),
    ("toxic", (126, 150, 62), "flat"),
    ("toxic_dark", (74, 88, 48), "flat"),
    ("storm", (74, 82, 108), "flat"),
    ("storm_dark", (38, 42, 62), "flat"),
    ("abyss", (20, 18, 36), "flat"),
    ("plasma", (180, 92, 255), "flat"),
    ("velvet", (110, 22, 48), "cloth"),
    ("parchment", (222, 200, 150), "cloth"),
    ("hair_blond", (214, 176, 96), "soft"),
    ("hair_white", (228, 228, 232), "soft"),
    ("wind", (190, 232, 240), "flat"),
]

# These swatches glow: they are lit in the emissive atlas and black everywhere else.
EMISSIVE = {"lamp", "liftstone", "ember", "lightning", "plasma", "wind"}

# Accent colours that change per faction. Only these three swatches differ between atlases.
FACTIONS = {
    "Crimson": {"faction_a": (168, 38, 40), "faction_b": (238, 222, 190), "faction_c": (70, 30, 32)},
    "Azure": {"faction_a": (36, 92, 168), "faction_b": (226, 232, 240), "faction_c": (24, 40, 76)},
    "Emerald": {"faction_a": (34, 130, 92), "faction_b": (232, 224, 180), "faction_c": (20, 60, 50)},
    "Obsidian": {"faction_a": (46, 44, 56), "faction_b": (180, 40, 40), "faction_c": (20, 20, 24)},
    # Campaign factions: the Gilded Armada, Scrap-Winds salvagers, Jetstream Syndicate, Tartarus wardens.
    "Gilded": {"faction_a": (30, 46, 96), "faction_b": (238, 226, 192), "faction_c": (196, 150, 52)},
    "Scrap": {"faction_a": (138, 70, 36), "faction_b": (152, 142, 112), "faction_c": (54, 44, 36)},
    "Syndicate": {"faction_a": (86, 38, 128), "faction_b": (60, 196, 190), "faction_c": (30, 22, 50)},
    "Warden": {"faction_a": (70, 74, 82), "faction_b": (190, 160, 60), "faction_c": (30, 30, 36)},
    # Dr. Thorne alone: purple clothes, a vivid green for his eyes and staff, and near-black trim.
    "Sorcerer": {"faction_a": (92, 40, 148), "faction_b": (70, 255, 120), "faction_c": (18, 14, 26)},
}

SWATCH_INDEX = {name: i for i, (name, _, _) in enumerate(SWATCHES)}
assert len(SWATCHES) <= GRID * GRID


def swatch_cell(name):
    """Returns (column, row) with row 0 at the top of the image."""
    i = SWATCH_INDEX[name]
    return i % GRID, i // GRID


def _write_png(path, size, pixels):
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + pixels[y * size * 3:(y + 1) * size * 3] for y in range(size))
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def _detail(kind, x, y, cell, rng_row, rng_blotch):
    """Brightness multiplier for one texel. Coarse steps keep the PNG small."""
    if kind == "wood":
        return 0.88 + 0.24 * rng_row[y * 12 // cell]
    if kind == "metal":
        return 0.9 + 0.2 * rng_blotch[(y * 6 // cell) * 6 + x * 6 // cell]
    if kind == "cloth":
        return 0.96 if (x // 2 + y // 2) % 2 else 1.03
    if kind == "rock":
        return 0.82 + 0.34 * rng_blotch[(y * 6 // cell) * 6 + x * 6 // cell]
    if kind == "soft":
        return 0.95 + 0.1 * rng_blotch[(y * 6 // cell) * 6 + x * 6 // cell]
    return 1.0


def build_atlas(faction, size, detailed):
    cell = size // GRID
    colours = {name: rgb for name, rgb, _ in SWATCHES}
    colours.update(FACTIONS[faction])
    pixels = bytearray(size * size * 3)
    # Seeded per swatch, so factions differ only in the accent swatches.
    for index, (name, _, kind) in enumerate(SWATCHES):
        rng = random.Random(index)
        rng_row = [rng.random() for _ in range(12)]
        rng_blotch = [rng.random() for _ in range(36)]
        col, row = index % GRID, index // GRID
        r, g, b = colours[name]
        for y in range(cell):
            for x in range(cell):
                k = _detail(kind, x, y, cell, rng_row, rng_blotch) if detailed else 1.0
                offset = ((row * cell + y) * size + col * cell + x) * 3
                pixels[offset] = min(255, int(r * k))
                pixels[offset + 1] = min(255, int(g * k))
                pixels[offset + 2] = min(255, int(b * k))
    return bytes(pixels)


def build_emissive_atlas(size):
    """Same grid as the colour atlas, so the mesh UVs address both."""
    cell = size // GRID
    pixels = bytearray(size * size * 3)
    for index, (name, rgb, _) in enumerate(SWATCHES):
        if name not in EMISSIVE:
            continue
        col, row = index % GRID, index // GRID
        for y in range(cell):
            start = ((row * cell + y) * size + col * cell) * 3
            pixels[start:start + cell * 3] = bytes(rgb) * cell
    return bytes(pixels)


def emissive_path(hq):
    return TEXTURE_DIR / f"T_Emissive_{'HQ' if hq else 'LQ'}.png"


def atlas_path(faction, hq):
    return TEXTURE_DIR / f"T_Palette_{faction}_{'HQ' if hq else 'LQ'}.png"


def generate_all():
    TEXTURE_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for faction in FACTIONS:
        for hq, size in ((True, HQ_SIZE), (False, LQ_SIZE)):
            path = atlas_path(faction, hq)
            _write_png(path, size, build_atlas(faction, size, hq))
            written.append(path)
    for hq, size in ((True, HQ_SIZE), (False, LQ_SIZE)):
        path = emissive_path(hq)
        _write_png(path, size, build_emissive_atlas(size))
        written.append(path)
    return written


if __name__ == "__main__":
    for written_path in generate_all():
        print(written_path, written_path.stat().st_size)
