"""Dialogue portraits: one illustrated bust per speaking character, written as T_Portrait_<Name>_<HQ|LQ>.png.

The designs live in portrait_cast.py and the drawing tools in portrait_kit.py. These are 2D images, so
nothing here goes through the mesh budget gate, and the busts are thrown away after each render.

    portraits.render_all()              # inside Blender
    portraits.render_all(["Lyra"])      # just one

Everything is built in a temporary scene, so whatever is open in Blender is left alone.
_setup_render and restore_scene also serve the icon renderer in fx_icons.py.
"""
import tempfile
from pathlib import Path

import bpy
import numpy as np

import palette
import portrait_cast
import portrait_kit as kit

HQ_SIZE = 512
LQ_SIZE = 256
RENDER_SIZE = 1536  # Three times HQ, for clean ink and halftone at phone size.
FRAME_INK = 0.02
ZOOM = 0.88  # Tight on the face: at 108 px on the comms bar, the face is all a player has.


def _setup_render(path, size):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.color_type = "TEXTURE"
    shading.show_cavity = True
    shading.cavity_type = "BOTH"
    shading.curvature_ridge_factor = 1.0
    shading.curvature_valley_factor = 1.0
    shading.show_object_outline = True
    shading.object_outline_color = (0.02, 0.015, 0.03)
    shading.show_shadows = True
    shading.shadow_intensity = 0.55
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.filepath = str(path)
    scene.display_settings.display_device = "sRGB"
    scene.view_settings.view_transform = "Standard"


def restore_scene(engine, transparent):
    """Puts back what _setup_render changed, so viewport material previews keep working afterwards."""
    bpy.context.scene.render.engine = engine
    bpy.context.scene.render.film_transparent = transparent
    bpy.context.scene.camera = None


def paint(name, scratch, size=RENDER_SIZE):
    """Renders a character over their backdrop, framed, as a float RGB array."""
    spec = portrait_cast.CAST[name]
    studio = kit.Studio(size)
    try:
        side = spec["key_side"]
        studio.light((side * 0.42, -0.82, 0.62))
        span = spec["span"]
        target = spec["target"]
        # Zooming in keeps the head's position by moving up a little, since the crop mostly takes the chest.
        studio.camera(target=(0, 0, target[2] + span * (1 - ZOOM) * 0.3), span=span * ZOOM)
        inks = kit.Inks(spec["shadow"], spec["rim"], (-side * 0.85, 0.25, 0.25))
        portrait = kit.Portrait(studio.scene.collection, inks, spec.get("shape", {}), (0.8, 0.6, 0.45),
                                turn=spec["turn"], tilt=spec["tilt"], pitch=spec["pitch"], body_turn=spec["body_turn"])
        spec["build"](portrait)
        figure = studio.render(Path(scratch) / f"{name}.png")
    finally:
        studio.close()
    back = kit.backdrop(size, spec["dark"], spec["light"], spec.get("motif"), sum(map(ord, name)))
    alpha = figure[..., 3:4]
    out = figure[..., :3] * alpha + back * (1 - alpha)
    frame = max(6, size // 64)
    out[:frame, :] = out[-frame:, :] = FRAME_INK
    out[:, :frame] = out[:, -frame:] = FRAME_INK
    return out


def _downsample(image, factor):
    h, w = image.shape[:2]
    return image.reshape(h // factor, factor, w // factor, factor, image.shape[2]).mean(axis=(1, 3))


def render_all(names=None, scratch=None):
    """Writes HQ and LQ for each name, defaulting to the whole cast. Returns the paths written."""
    written = []
    with tempfile.TemporaryDirectory() as temp:
        for name in names or portrait_cast.CAST:
            image = paint(name, scratch or temp)
            for quality, target in (("HQ", HQ_SIZE), ("LQ", LQ_SIZE)):
                final = _downsample(image, RENDER_SIZE // target)
                data = (np.clip(final, 0, 1) * 255 + 0.5).astype(np.uint8)
                dest = palette.TEXTURE_DIR / f"T_Portrait_{name}_{quality}.png"
                palette._write_png(dest, target, data.tobytes())
                written.append(str(dest))
    return written
