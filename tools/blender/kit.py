"""Mesh-building kit: accumulates closed primitives into one palette-mapped mesh."""
import math
from contextlib import contextmanager

import bmesh
import bpy
from mathutils import Matrix, Vector

import palette

CELL = 1.0 / palette.GRID
UV_MARGIN = 0.22 * CELL  # Keeps mip-mapped sampling inside the swatch.
UV_DENSITY = 0.25  # Atlas cells per metre before a face is squeezed to fit.


def V(*args):
    return Vector(args[0] if len(args) == 1 else args)


def _resolve(color, *key):
    return color(*key) if callable(color) else color


class MeshBuilder:
    def __init__(self):
        self.verts = []
        self.vert_bones = []
        self.faces = []  # (indices, swatch, smooth)
        self.sockets = {}
        self.bone = None
        self._matrix = Matrix.Identity(4)

    @contextmanager
    def xf(self, matrix):
        previous = self._matrix
        self._matrix = previous @ matrix
        try:
            yield
        finally:
            self._matrix = previous

    @contextmanager
    def bound_to(self, bone):
        previous = self.bone
        self.bone = bone
        try:
            yield
        finally:
            self.bone = previous

    @property
    def tris(self):
        return sum(len(indices) - 2 for indices, _, _ in self.faces)

    def socket(self, name, position):
        self.sockets[name] = self._matrix @ V(position)

    def _push(self, point):
        self.verts.append(self._matrix @ V(point))
        self.vert_bones.append(self.bone)
        return len(self.verts) - 1

    def loft(self, rings, color, caps=(True, True), smooth=False, closed=True):
        """Skins equal-length rings. color is a swatch or fn(ring_index, side_index)."""
        ids = [[self._push(p) for p in ring] for ring in rings]
        count = len(ids[0])
        sides = count if closed else count - 1
        for i in range(len(ids) - 1):
            for j in range(sides):
                k = (j + 1) % count
                face = (ids[i][j], ids[i][k], ids[i + 1][k], ids[i + 1][j])
                self.faces.append((face, _resolve(color, i, j), smooth))
        cap_color = (lambda: _resolve(color, 0, 0)) if callable(color) else (lambda: color)
        if caps[0]:
            self.faces.append((tuple(reversed(ids[0])), cap_color(), False))
        if caps[1]:
            self.faces.append((tuple(ids[-1]), cap_color(), False))

    def lathe(self, profile, sides, color, smooth=True, caps=(True, True), phase=0.0):
        """Revolves (radius, z) pairs around local Z."""
        rings = []
        for radius, z in profile:
            ring = []
            for j in range(sides):
                a = phase + 2 * math.pi * j / sides
                ring.append((radius * math.cos(a), radius * math.sin(a), z))
            rings.append(ring)
        self.loft(rings, color, caps=caps, smooth=smooth)

    def tube(self, p0, p1, r0, r1=None, sides=6, color="iron", smooth=False, flat=1.0):
        """Tapered prism between two points. flat squashes it across its side axis."""
        p0, p1 = V(p0), V(p1)
        r1 = r0 if r1 is None else r1
        axis = (p1 - p0).normalized()
        ref = V(0, 0, 1) if abs(axis.z) < 0.95 else V(1, 0, 0)
        side = axis.cross(ref).normalized()
        up = side.cross(axis).normalized()
        rings = []
        for centre, radius in ((p0, r0), (p1, r1)):
            ring = []
            for j in range(sides):
                a = 2 * math.pi * (j + 0.5) / sides
                ring.append(centre + side * (math.cos(a) * radius * flat) + up * (math.sin(a) * radius))
            rings.append(ring)
        self.loft(rings, color, smooth=smooth)

    def path(self, points, radii, sides, color, smooth=False):
        """Single skinned tube through several points with per-point radius."""
        points = [V(p) for p in points]
        rings = []
        for i, point in enumerate(points):
            ahead = points[min(i + 1, len(points) - 1)] - points[max(i - 1, 0)]
            axis = ahead.normalized()
            ref = V(0, 0, 1) if abs(axis.z) < 0.95 else V(1, 0, 0)
            side = axis.cross(ref).normalized()
            up = side.cross(axis).normalized()
            ring = []
            for j in range(sides):
                a = 2 * math.pi * (j + 0.5) / sides
                ring.append(point + (side * math.cos(a) + up * math.sin(a)) * radii[i])
            rings.append(ring)
        self.loft(rings, color, smooth=smooth)

    def box(self, centre, size, color, top_scale=1.0):
        """Axis-aligned box in local space, optionally tapered towards +Z."""
        cx, cy, cz = centre
        sx, sy, sz = (s / 2 for s in size)
        rings = []
        for z, scale in ((cz - sz, 1.0), (cz + sz, top_scale)):
            ring = []
            for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                ring.append((cx + dx * sx * scale, cy + dy * sy * scale, z))
            rings.append(ring)
        self.loft(rings, color)

    def plate(self, outline, thickness, color):
        """Extrudes a planar polygon, for sails, fins, blades and flags."""
        outline = [V(p) for p in outline]
        normal = (outline[1] - outline[0]).cross(outline[2] - outline[0])
        normal = normal.normalized() * (thickness / 2)
        self.loft([[p - normal for p in outline], [p + normal for p in outline]], color)

    def sphere(self, centre, radii, sides, rings, color, smooth=True):
        """Ellipsoid with small polar caps. radii may be one float or (x, y, z)."""
        rx, ry, rz = (radii, radii, radii) if isinstance(radii, (int, float)) else radii
        with self.xf(Matrix.Translation(centre) @ Matrix.Diagonal((rx, ry, rz, 1.0))):
            profile = []
            for i in range(rings):
                a = math.pi * (i + 0.5) / rings
                profile.append((math.sin(a), -math.cos(a)))
            self.lathe(profile, sides, color, smooth=smooth)

    # --- output -----------------------------------------------------------------

    def recentre_to_bottom(self):
        """Places the bounding box's bottom-centre at the origin. Returns the offset applied."""
        xs = [v.x for v in self.verts]
        ys = [v.y for v in self.verts]
        zs = [v.z for v in self.verts]
        offset = -V((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs))
        self.verts = [v + offset for v in self.verts]
        self.sockets = {name: p + offset for name, p in self.sockets.items()}
        return offset

    def _face_uvs(self, indices, swatch, salt):
        points = [self.verts[i] for i in indices]
        normal = V(0, 0, 0)
        for i, point in enumerate(points):
            normal += point.cross(points[(i + 1) % len(points)])
        ax, ay, az = abs(normal.x), abs(normal.y), abs(normal.z)
        if az >= ax and az >= ay:
            coords = [(p.x, p.y) for p in points]
        elif ax >= ay:
            coords = [(p.y, p.z) for p in points]
        else:
            coords = [(p.x, p.z) for p in points]

        col, row = palette.swatch_cell(swatch)
        interior = CELL - 2 * UV_MARGIN
        us = [c[0] * UV_DENSITY * CELL * palette.GRID / 2 for c in coords]
        vs = [c[1] * UV_DENSITY * CELL * palette.GRID / 2 for c in coords]
        min_u, min_v = min(us), min(vs)
        span_u, span_v = max(us) - min_u, max(vs) - min_v
        scale_u = min(1.0, interior / span_u) if span_u > 0 else 1.0
        scale_v = min(1.0, interior / span_v) if span_v > 0 else 1.0
        # Slides each face to a stable spot in its cell so grain isn't identical everywhere.
        slack_u = max(0.0, interior - span_u * scale_u)
        slack_v = max(0.0, interior - span_v * scale_v)
        start_u = col * CELL + UV_MARGIN + slack_u * ((salt * 0.618) % 1.0)
        start_v = 1.0 - (row + 1) * CELL + UV_MARGIN + slack_v * ((salt * 0.381) % 1.0)
        return [
            (start_u + (u - min_u) * scale_u, start_v + (v - min_v) * scale_v)
            for u, v in zip(us, vs)
        ]

    def to_object(self, name, material, collection=None):
        mesh = bpy.data.meshes.new(f"{name}_Mesh")
        mesh.from_pydata(
            [tuple(v) for v in self.verts], [], [list(indices) for indices, _, _ in self.faces]
        )
        uv_layer = mesh.uv_layers.new(name="UVMap")
        loop = 0
        for salt, (indices, swatch, smooth) in enumerate(self.faces):
            for uv in self._face_uvs(indices, swatch, salt):
                uv_layer.data[loop].uv = uv
                loop += 1
        mesh.polygons.foreach_set("use_smooth", [smooth for _, _, smooth in self.faces])
        mesh.update()

        solid = bmesh.new()
        solid.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(solid, faces=solid.faces)
        solid.to_mesh(mesh)
        solid.free()
        mesh.materials.append(material)

        obj = bpy.data.objects.new(name, mesh)
        (collection or bpy.context.scene.collection).objects.link(obj)
        bones = sorted({b for b in self.vert_bones if b})
        for bone in bones:
            group = obj.vertex_groups.new(name=bone)
            group.add([i for i, b in enumerate(self.vert_bones) if b == bone], 1.0, "REPLACE")
        return obj


def palette_material(hq=True, faction=palette.DEFAULT_FACTION):
    # Each faction embeds its own atlas; the base kit's Crimson keeps its original material name.
    tag = "" if faction == palette.DEFAULT_FACTION else f"{faction}_"
    name = f"M_Palette_{tag}{'HQ' if hq else 'LQ'}"
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    path = palette.atlas_path(faction, hq)
    glow_path = palette.emissive_path(hq)
    if not path.exists() or not glow_path.exists():
        palette.generate_all()
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    # Exports doubleSided=false: every mesh is closed, so back faces never need shading.
    material.use_backface_culling = True
    nodes = material.node_tree.nodes
    bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(path), check_existing=True)
    material.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    # Lets lanterns, lift-stone and lightning read as light sources with no real-time lights.
    glow = nodes.new("ShaderNodeTexImage")
    glow.image = bpy.data.images.load(str(glow_path), check_existing=True)
    material.node_tree.links.new(glow.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 0.85
    bsdf.inputs["Metallic"].default_value = 0.0
    return material


def clear_scene():
    """Empties the scene and orphan data so one asset at a time is visible and exportable."""
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj)
    for store in (bpy.data.meshes, bpy.data.armatures, bpy.data.actions, bpy.data.materials, bpy.data.images):
        for item in list(store):
            if item.users == 0:
                store.remove(item)
