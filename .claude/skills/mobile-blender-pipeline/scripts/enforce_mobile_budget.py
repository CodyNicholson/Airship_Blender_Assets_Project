# .claude/skills/mobile-blender-pipeline/scripts/enforce_mobile_budget.py
import bpy
import os
import math
from pathlib import Path
from mathutils import Matrix, Vector

# Relative export paths resolve against the repo, not Blender's working directory.
REPO_ROOT = Path(__file__).resolve().parents[4]

# ==============================================================================
# MOBILE ASSET BUDGET THRESHOLDS
# ==============================================================================
BUDGET_TIERS = {
    "hero": {"max_tris": 4500, "max_materials": 2, "tex_size": 1024, "max_bones": 60},
    "prop": {"max_tris": 800,  "max_materials": 1, "tex_size": 512,  "max_bones": 0},
    "environment": {"max_tris": 1500, "max_materials": 1, "tex_size": 1024, "max_bones": 0},
    # Low-quality variants (*_LQ assets) for older devices.
    "hero_low": {"max_tris": 1500, "max_materials": 1, "tex_size": 256, "max_bones": 24},
    "prop_low": {"max_tris": 250, "max_materials": 1, "tex_size": 128, "max_bones": 0},
    "environment_low": {"max_tris": 600, "max_materials": 1, "tex_size": 256, "max_bones": 0},
}

PIVOT_TOLERANCE = 0.001

def get_triangle_count(obj) -> int:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    mesh.calc_loop_triangles()
    tri_count = len(mesh.loop_triangles)
    eval_obj.to_mesh_clear()
    return tri_count

def get_armature(obj):
    for mod in obj.modifiers:
        if mod.type == 'ARMATURE' and mod.object:
            return mod.object
    return None

def get_bottom_center(obj) -> Vector:
    bpy.context.view_layer.update()
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return Vector((
        sum(corner.x for corner in corners) / 8.0,
        sum(corner.y for corner in corners) / 8.0,
        min(corner.z for corner in corners),
    ))

def set_origin_to_bottom_center(obj):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    armature = get_armature(obj)
    bottom_center = get_bottom_center(obj)

    # The rig has to travel with the mesh or the skin binding is offset.
    if armature:
        armature.matrix_world = Matrix.Translation(-bottom_center) @ armature.matrix_world

    # A mesh parented to its rig has just moved with it; otherwise bake the
    # offset into the mesh data so bottom-center sits at (0,0,0) local space.
    if obj.parent is not armature or armature is None:
        offset = bottom_center - obj.matrix_world.translation
        obj.data.transform(Matrix.Translation(-offset))
        obj.location = (0.0, 0.0, 0.0)

def has_image_textures(obj) -> bool:
    for slot in obj.material_slots:
        if slot.material and slot.material.node_tree:
            if any(node.type == 'TEX_IMAGE' and node.image for node in slot.material.node_tree.nodes):
                return True
    return False

def enforce_uv_and_seams(obj, island_margin=0.02) -> bool:
    """Returns True if the mesh was re-unwrapped, False if its UVs were kept."""
    bpy.context.view_layer.objects.active = obj

    # Image textures are painted against the current UVs (imported assets, or a
    # previous bake pass), so re-projecting would scramble them.
    keep_existing = bool(obj.data.uv_layers) and has_image_textures(obj)

    # Ensure UV map exists and is named consistently for game engines
    if not obj.data.uv_layers:
        obj.data.uv_layers.new(name="UVMap")
    else:
        keep_name = obj.data.uv_layers.active.name
        for layer in [l for l in obj.data.uv_layers if l.name != keep_name]:
            obj.data.uv_layers.remove(layer)
        obj.data.uv_layers.active.name = "UVMap"

    if keep_existing:
        return False

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')

    # Smart UV Project with mobile bleed margin to prevent mipmap bleeding
    bpy.ops.uv.smart_project(
        angle_limit=math.radians(66.0),
        island_margin=island_margin,
        area_weight=0.0,
        correct_aspect=True,
        scale_to_bounds=False
    )
    bpy.ops.object.mode_set(mode='OBJECT')
    return True

def limit_bone_influences(obj, max_influences=4):
    if obj.vertex_groups:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
        bpy.ops.object.vertex_group_limit_total(limit=max_influences)
        bpy.ops.object.vertex_group_clean(group_select_mode='ALL', limit=0.01)
        bpy.ops.object.mode_set(mode='OBJECT')

def ensure_object_mode():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

def bake_materials_to_atlas(asset_name: str, tier: str = "prop") -> dict:
    """Bakes every material's albedo into one atlas material on the active UVMap.

    Run after optimize_and_validate_asset has reported a material violation (that
    pass creates the UVMap), then run optimize_and_validate_asset again. Only
    albedo survives: metallic/roughness variation between source materials is lost.
    """
    if tier not in BUDGET_TIERS:
        raise ValueError(f"Unknown tier '{tier}'. Expected one of {sorted(BUDGET_TIERS)}.")
    obj = bpy.data.objects.get(asset_name)
    if obj is None or obj.type != 'MESH':
        raise ValueError(f"No mesh object named '{asset_name}'.")
    if not obj.data.uv_layers:
        raise ValueError(f"'{asset_name}' has no UV map. Run optimize_and_validate_asset first.")

    ensure_object_mode()
    size = BUDGET_TIERS[tier]["tex_size"]
    image = bpy.data.images.new(f"{asset_name}_Atlas", width=size, height=size, alpha=False)

    # Cycles bakes into whichever image node is active in each source material.
    source_materials = [slot.material for slot in obj.material_slots if slot.material]
    for mat in source_materials:
        mat.use_nodes = True
        node = mat.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = image
        mat.node_tree.nodes.active = node

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    scene = bpy.context.scene
    previous_engine = scene.render.engine
    scene.render.engine = 'CYCLES'
    previous_samples = scene.cycles.samples
    scene.cycles.samples = 4
    try:
        bpy.ops.object.bake(
            type='DIFFUSE',
            pass_filter={'COLOR'},
            margin=max(4, size // 64),
            margin_type='EXTEND',
            use_clear=True
        )
    finally:
        scene.cycles.samples = previous_samples
        scene.render.engine = previous_engine
    image.pack()

    baked = bpy.data.materials.new(f"{asset_name}_Mat")
    baked.use_nodes = True
    nodes = baked.node_tree.nodes
    bsdf = next(node for node in nodes if node.type == 'BSDF_PRINCIPLED')
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = image
    baked.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])

    obj.data.materials.clear()
    obj.data.materials.append(baked)
    return {"material": baked.name, "atlas": image.name, "size": size, "merged": len(source_materials)}

def optimize_and_validate_asset(
    asset_name: str,
    tier: str = "prop",
    export_dir: str = "assets/models/production",
    preview_path: str = "/tmp/mobile_asset_audit_preview.png"
) -> dict:
    if tier not in BUDGET_TIERS:
        raise ValueError(f"Unknown tier '{tier}'. Expected one of {sorted(BUDGET_TIERS)}.")
    budget = BUDGET_TIERS[tier]
    report = {
        "asset": asset_name,
        "tier": tier,
        "passed": False,
        "initial_tris": 0,
        "final_tris": 0,
        "max_tris": budget["max_tris"],
        "materials_count": 0,
        "max_materials": budget["max_materials"],
        "uv_layers": 0,
        "bones": 0,
        "violations": [],
        "actions_taken": [],
        "export_path": None,
        "preview_image": None
    }

    ensure_object_mode()

    # 1. Gather all visible mesh objects and join if fragmented
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.visible_get()]
    if not meshes:
        report["violations"].append("No visible MESH objects found in scene.")
        return report

    bpy.ops.object.select_all(action='DESELECT')
    for m in meshes:
        m.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
        report["actions_taken"].append(f"Joined {len(meshes)} fragmented mesh parts into single draw call.")

    target = bpy.context.view_layer.objects.active
    target.name = asset_name
    target.data.name = f"{asset_name}_Mesh"

    # 2. Clean loose geometry & merge by distance
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.0001)
    bpy.ops.mesh.delete_loose()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    # 3. Triangle Budget Enforcement
    initial_tris = get_triangle_count(target)
    report["initial_tris"] = initial_tris

    if initial_tris > budget["max_tris"]:
        ratio = max(0.05, (budget["max_tris"] * 0.95) / float(initial_tris))
        # Existing modifiers (e.g. Subdivision) must be applied before the
        # Decimate that was sized for their evaluated triangle count. The
        # Armature modifier stays: it is the skin binding.
        for mod in list(target.modifiers):
            if mod.type != 'ARMATURE':
                bpy.ops.object.modifier_apply(modifier=mod.name)
        dec_mod = target.modifiers.new(name="MobileDecimate", type='DECIMATE')
        dec_mod.decimate_type = 'COLLAPSE'
        dec_mod.ratio = ratio
        dec_mod.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=dec_mod.name)
        report["actions_taken"].append(f"Applied Decimate modifier (ratio={ratio:.3f}).")

    final_tris = get_triangle_count(target)
    report["final_tris"] = final_tris
    if final_tris > budget["max_tris"]:
        report["violations"].append(
            f"Triangle budget exceeded: {final_tris} tris (Max allowed for '{tier}': {budget['max_tris']})."
        )

    # 4. Pivot & Transform Sanity
    set_origin_to_bottom_center(target)
    if get_bottom_center(target).length > PIVOT_TOLERANCE:
        report["violations"].append(f"Pivot check failed: bottom-center is at {tuple(get_bottom_center(target))}.")
    else:
        report["actions_taken"].append("Applied transforms and snapped origin to bottom-center (Z=0).")

    # 5. UV Unwrap & Single UV Layer Enforcement
    if enforce_uv_and_seams(target):
        report["actions_taken"].append("Enforced single UVMap with 0.02 island bleed margin.")
    else:
        report["actions_taken"].append("Kept existing UVMap because materials use image textures.")
    report["uv_layers"] = len(target.data.uv_layers)

    # 6. Material Slot Audit
    # Remove unused material slots
    bpy.context.view_layer.objects.active = target
    if target.material_slots:
        bpy.ops.object.material_slot_remove_unused()
    mat_count = len(target.material_slots)
    report["materials_count"] = mat_count
    if mat_count > budget["max_materials"]:
        report["violations"].append(
            f"Material draw-call budget exceeded: {mat_count} materials (Max allowed: {budget['max_materials']}). Bake into single atlas."
        )

    # 7. Mobile Skinning Gate (Max 4 bone weights per vertex)
    limit_bone_influences(target, max_influences=4)
    armature = get_armature(target)
    if armature:
        report["bones"] = len(armature.data.bones)
        if report["bones"] > budget["max_bones"]:
            report["violations"].append(
                f"Bone budget exceeded: {report['bones']} bones (Max allowed for '{tier}': {budget['max_bones']})."
            )

    # 8. Render Workbench Diagnostic Preview for Claude Multimodal Inspection
    # preview_image stays None without a camera, so a stale file is never mistaken for this asset.
    if bpy.context.scene.camera:
        bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
        bpy.context.scene.display.shading.light = 'MATCAP'
        bpy.context.scene.display.shading.color_type = 'MATERIAL'
        bpy.context.scene.render.resolution_x = 1024
        bpy.context.scene.render.resolution_y = 1024
        bpy.context.scene.render.filepath = preview_path
        bpy.ops.render.render(write_still=True)
        report["preview_image"] = preview_path

    # 9. Gate Decision & GLB Export
    if len(report["violations"]) == 0:
        report["passed"] = True
        out_dir = REPO_ROOT / export_dir
        os.makedirs(out_dir, exist_ok=True)
        out_file = str(out_dir / f"{asset_name}.glb")
        bpy.ops.object.select_all(action='DESELECT')
        target.select_set(True)
        if armature:
            armature.select_set(True)
        bpy.ops.export_scene.gltf(
            filepath=out_file,
            use_selection=True,
            export_format='GLB',
            export_apply=True,
            export_yup=True,
            export_texcoords=True,
            export_normals=True,
            export_materials='EXPORT'
        )
        report["export_path"] = out_file

    return report
