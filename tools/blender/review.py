"""Contact sheets for reviewing assets: every view of an asset in ONE small image, so a review or a gate
check costs one image instead of four to six. Workbench render with palette colours, nothing exported.

    review.render_row(objects, armature=None)  -> list of view images for what's in the scene
    review.write_sheet(rows, path)             -> stacks rows (e.g. HQ over LQ) into one PNG
"""
import math
import tempfile
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

from fx_image import write_png

CELL = 600  # Pixels per view: enough to judge shape and colour, small enough to stay cheap.
VIEWS = (("front", 0.0), ("three_quarter", -38.0), ("back", 180.0))
POSE_YAW = -38.0
GAP = 6
BACKGROUND = (0.82, 0.84, 0.88)


def _setup(scene):
    scene.render.engine = "BLENDER_WORKBENCH"
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.color_type = "TEXTURE"
    shading.show_shadows = False
    shading.show_cavity = True
    shading.background_type = "VIEWPORT"
    shading.background_color = BACKGROUND
    scene.render.film_transparent = False
    scene.render.resolution_x = scene.render.resolution_y = CELL
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"


def _bounds(objects):
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    low = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    high = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return low, high


def _load(path):
    image = bpy.data.images.load(str(path), check_existing=False)
    w, h = image.size
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]
    bpy.data.images.remove(image)
    return pixels


def _walk_action():
    actions = list(bpy.data.actions)
    for key in ("walk", "attack", ""):
        found = [a for a in actions if key in a.name.lower()]
        if found:
            return found[0]
    return None


def render_row(objects, armature=None):
    """Front, three-quarter and back at rest, plus a mid-walk three-quarter when there's a rig."""
    scene = bpy.context.scene
    _setup(scene)
    low, high = _bounds(objects)
    centre = (low + high) / 2
    reach = max(high.z - low.z, math.hypot(high.x - low.x, high.y - low.y)) * 1.08
    data = bpy.data.cameras.new("ReviewCam")
    data.type = "ORTHO"
    data.ortho_scale = reach
    data.clip_end = reach * 20
    camera = bpy.data.objects.new("ReviewCam", data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    scratch = Path(tempfile.mkdtemp(prefix="review_"))

    def shoot(name, yaw):
        a = math.radians(yaw)
        camera.location = centre + Vector((math.sin(a), -math.cos(a), 0.12)) * reach * 3
        camera.rotation_euler = (centre - camera.location).to_track_quat("-Z", "Y").to_euler()
        path = scratch / f"{name}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        return _load(path)

    row = [shoot(name, yaw) for name, yaw in VIEWS]
    if armature is not None and armature.animation_data is not None:
        action = _walk_action()
        if action is not None:
            start, end = action.frame_range
            armature.animation_data.action = action
            scene.frame_set(int(start + (end - start) * 0.5))
            bpy.context.view_layer.update()
            row.append(shoot("pose", POSE_YAW))
            print(f"[review] posed: {action.name} frame {scene.frame_current}")
            armature.animation_data.action = None
            scene.frame_set(int(start))
    bpy.data.objects.remove(camera)
    return row


def write_sheet(rows, path):
    """Rows of views stacked into one PNG, with thin gaps between cells."""
    columns = max(len(r) for r in rows)
    height = len(rows) * CELL + (len(rows) - 1) * GAP
    width = columns * CELL + (columns - 1) * GAP
    sheet = np.ones((height, width, 4), dtype=np.float32)
    sheet[..., :3] = 1.0
    for i, row in enumerate(rows):
        for j, cell in enumerate(row):
            y, x = i * (CELL + GAP), j * (CELL + GAP)
            sheet[y:y + CELL, x:x + CELL] = cell[:CELL, :CELL]
    sheet[..., 3] = 1.0
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_png(path, sheet)
    return path
