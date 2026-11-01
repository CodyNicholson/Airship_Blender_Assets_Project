"""Aether-Comms portraits: comic-style character busts rendered from the real models.

The design delivers most of its drama through portraits at the top of the screen, so these are
rendered from the same meshes the player fights, in a single consistent style: faction-coloured
halftone burst, heavy outline, thick panel border.

    portraits.render_all()   # inside Blender; writes T_Portrait_<Name>_<HQ|LQ>.png

Not a mesh: nothing here goes through the budget gate. Run it on an otherwise disposable scene.
"""
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

import catalog
import kit
import palette
import story_characters

HQ_SIZE = 512
LQ_SIZE = 256
RENDER_SIZE = 1024  # Supersampled, then reduced, for clean outlines on any phone.

# Burst colours (sRGB) follow allegiance, so a bark's source reads before the name does.
ALLEGIANCE = {
    "Vane": ((196, 52, 44), (240, 170, 70)),
    "CassianPirate": ((150, 34, 38), (236, 196, 110)),
    "CassianAdmiral": ((30, 46, 96), (226, 186, 90)),
    "Morrow": ((48, 86, 66), (214, 200, 150)),
    "Rook": ((44, 62, 104), (214, 150, 66)),
    "Lyra": ((46, 128, 158), (206, 236, 240)),
    "Sable": ((58, 28, 64), (170, 60, 90)),
    "Thorne": ((36, 110, 120), (130, 226, 226)),
    "Krag": ((110, 56, 30), (190, 150, 60)),
    "Vex": ((70, 30, 110), (196, 120, 250)),
    "Vesper": ((22, 92, 96), (70, 206, 196)),
    "Malakor": ((40, 40, 50), (240, 110, 40)),
    "ArmadaSoldier": ((30, 46, 96), (160, 176, 210)),
    "ArmadaOfficer": ((30, 46, 96), (226, 186, 90)),
    "RoyalGuard": ((120, 26, 40), (226, 186, 90)),
}
# Tall hats and helmets need the frame to back off, or they crop against the panel.
HEADROOM = {"CassianAdmiral": 0.32, "ArmadaSoldier": 0.34, "Malakor": 0.24, "RoyalGuard": 0.26, "Vane": 0.1, "Krag": 0.12}
# Portrait side: rivals look left at the player's crew, who look right. Comms dialogue reads as a duel.
RIVALS = {"CassianAdmiral", "Morrow", "Krag", "Vex", "Vesper", "Malakor", "ArmadaSoldier", "ArmadaOfficer", "RoyalGuard"}


def _camera_side(name):
    """Camera X sign. The model faces -Y, so a camera at -X shows it looking towards screen right."""
    return 1 if name in RIVALS else -1


def _build_scene(name):
    kit.clear_scene()
    asset = f"SK_{name}_HQ"
    base = f"SK_{name}"
    mb, _, _ = catalog.build(asset)
    faction = catalog.DEFAULT_FACTIONS.get(base, palette.DEFAULT_FACTION)
    obj = mb.to_object(asset, kit.palette_material(True, faction))
    look_at = mb.sockets["portrait_look_at"]
    return obj, look_at


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


def _camera(name, look_at):
    side = _camera_side(name)
    data = bpy.data.cameras.new("PortraitCam")
    data.lens = 85
    cam = bpy.data.objects.new("PortraitCam", data)
    bpy.context.scene.collection.objects.link(cam)
    scale = story_characters.CAST[name].scale
    target = look_at + Vector((0, 0, HEADROOM.get(name, 0.0) * 0.5 - 0.1 * scale))
    distance = (2.55 + HEADROOM.get(name, 0.0) * 1.1) * scale * (1.0 + 0.1 * (story_characters.CAST[name].width - 1.0))
    direction = Vector((side * 0.42, -1.0, 0.04)).normalized()
    cam.location = target + direction * distance
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    return cam


def _burst(size, dark, light, side):
    """Radial speed-lines plus a halftone falloff, in plain arrays so it stays dependency free."""
    grid = np.linspace(0, 1, size)
    xs, ys = np.meshgrid(grid, grid)
    cx, cy = 0.5 - side * 0.08, 0.42
    dx, dy = xs - cx, ys - cy
    angle = np.arctan2(dy, dx)
    radius = np.hypot(dx, dy)
    rays = (np.sin(angle * 18 + np.sin(angle * 5) * 1.2) > 0.25).astype(float)
    # Rays fade before the panel edge and stay well under the light colour, so the face leads.
    mix = np.clip(rays * (0.72 - radius * 1.05), 0, 0.6)
    # Halftone dots grow towards the panel edge.
    cycles = 54.0
    dots = (np.sin(xs * cycles * 2 * np.pi) * np.sin(ys * cycles * 2 * np.pi)) > (1.05 - radius * 1.5)
    out = np.zeros((size, size, 3))
    for i in range(3):
        channel = dark[i] + (light[i] - dark[i]) * mix
        out[:, :, i] = np.where(dots, channel * 0.8, channel)
    return out / 255.0


def _downsample(image, factor):
    h, w = image.shape[:2]
    return image.reshape(h // factor, factor, w // factor, factor, image.shape[2]).mean(axis=(1, 3))


def _compose(path, name, sizes):
    img = bpy.data.images.load(str(path))
    size = img.size[0]
    rgba = np.array(img.pixels[:], dtype=np.float32).reshape(size, size, 4)[::-1]
    bpy.data.images.remove(img)
    dark, light = ALLEGIANCE[name]
    side = _camera_side(name)
    back = _burst(size, dark, light, side)
    alpha = rgba[:, :, 3:4]
    # Workbench outlines only appear against other geometry, so draw the outer ink from the alpha mask.
    solid = (rgba[:, :, 3] > 0.5)
    ink = solid.copy()
    radius = max(2, size // 120)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)):
        ink |= np.roll(np.roll(solid, dy * radius, 0), dx * radius, 1)
    out = back.copy()
    out[ink] = (0.03, 0.02, 0.04)
    out = rgba[:, :, :3] * alpha + out * (1 - alpha)
    # Thick comic panel frame.
    frame = max(6, size // 64)
    out[:frame, :] = out[-frame:, :] = 0.02
    out[:, :frame] = out[:, -frame:] = 0.02
    written = []
    for quality, target in sizes.items():
        final = _downsample(out, size // target)
        data = (np.clip(final, 0, 1) * 255 + 0.5).astype(np.uint8)
        dest = palette.TEXTURE_DIR / f"T_Portrait_{name}_{quality}.png"
        palette._write_png(dest, target, data.tobytes())
        written.append(dest)
    return written


def render_one(name, scratch):
    obj, look_at = _build_scene(name)
    _camera(name, look_at)
    path = Path(scratch) / f"{name}.png"
    _setup_render(path, RENDER_SIZE)
    bpy.ops.render.render(write_still=True)
    return _compose(path, name, {"HQ": HQ_SIZE, "LQ": LQ_SIZE})


def restore_scene(engine, transparent):
    """Puts back what _setup_render changed, so viewport material previews keep working afterwards."""
    bpy.context.scene.render.engine = engine
    bpy.context.scene.render.film_transparent = transparent
    bpy.context.scene.camera = None


def render_all(scratch):
    scene = bpy.context.scene
    engine, transparent = scene.render.engine, scene.render.film_transparent
    written = []
    for name in story_characters.CAST:
        written += render_one(name, scratch)
    kit.clear_scene()
    restore_scene(engine, transparent)
    return [str(p) for p in written]
