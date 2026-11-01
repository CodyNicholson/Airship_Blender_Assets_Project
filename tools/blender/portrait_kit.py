"""Portrait studio: illustration-grade busts for the dialogue scenes.

The game models all share one head, so nothing that renders them can give a character a face of their
own. These busts exist only to be drawn. They are never exported, so they have no triangle budget, and
they never pass through the mesh gate. Each face is three things stacked:

    sculpt   a dense skull pushed around by a height field: jaw, nose, brow, cheekbones.
    paint    a front-projected texture drawn with numpy: eyes, brows, lips, scars, stubble, tattoos.
    ink      a stepped comic shader with halftone falloff, a coloured rim and inverted-hull outlines.

Head space: +X is image right, -Y faces the camera, +Z is up. The crown is near z=1, the chin near z=-1.2.
Colours are sRGB tuples in 0..1 unless a function says otherwise.
"""
import math

import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

TEX_SIZE = 2048
TEX_X = (-1.3, 1.3)
TEX_Z = (-1.5, 1.1)
EYE_SCALE = 1.22  # Eyes are drawn big: the face has to read at 108 px on the comms bar.


def rgb(*value):
    """Accepts 0-255 ints or a hex string, gives sRGB floats."""
    if len(value) == 1 and isinstance(value[0], str):
        h = value[0].lstrip("#")
        return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return tuple(c / 255 for c in value)


def _linear(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def _smooth(edge0, edge1, x):
    t = np.clip((x - edge0) / (edge1 - edge0), 0, 1)
    return t * t * (3 - 2 * t)


def _gauss(x, z, cx, cz, sx, sz):
    return np.exp(-(((x - cx) / sx) ** 2 + ((z - cz) / sz) ** 2))


# ---- the comic shader --------------------------------------------------------------------------

class Inks:
    """Materials for one portrait, so the shadow and rim colours are shared across the character."""

    def __init__(self, shadow, rim, rim_dir, dots=290.0):
        self.shadow, self.rim, self.rim_dir, self.dots = shadow, rim, rim_dir, dots
        self.cache = {}
        self.outline = self._outline()
        self.made = [self.outline]

    def _outline(self):
        mat = bpy.data.materials.new("PortraitInk")
        mat.use_nodes = True
        tree = mat.node_tree
        tree.nodes.clear()
        out = tree.nodes.new("ShaderNodeOutputMaterial")
        em = tree.nodes.new("ShaderNodeEmission")
        em.inputs[0].default_value = (*_linear(rgb(14, 10, 18)), 1)
        # The hull sits outside the skin, so it must not cast: it would put the whole face in shadow.
        path = tree.nodes.new("ShaderNodeLightPath")
        clear = tree.nodes.new("ShaderNodeBsdfTransparent")
        mix = tree.nodes.new("ShaderNodeMixShader")
        tree.links.new(path.outputs[1], mix.inputs[0])
        tree.links.new(em.outputs[0], mix.inputs[1])
        tree.links.new(clear.outputs[0], mix.inputs[2])
        tree.links.new(mix.outputs[0], out.inputs[0])
        mat.use_backface_culling = True
        mat.use_backface_culling_shadow = True if hasattr(mat, "use_backface_culling_shadow") else False
        if hasattr(mat, "use_transparent_shadow"):
            mat.use_transparent_shadow = True
        return mat

    def get(self, color, gloss=0.0, image=None, halftone=0.34, rim=True, flat=False):
        key = (color, gloss, image.name if image else None, halftone, rim, flat)
        if key not in self.cache:
            self.cache[key] = self._make(color, gloss, image, halftone, rim, flat)
            self.made.append(self.cache[key])
        return self.cache[key]

    def _make(self, color, gloss, image, halftone, rim, flat):
        mat = bpy.data.materials.new("PortraitCel")
        mat.use_nodes = True
        t = mat.node_tree
        t.nodes.clear()
        n, l = t.nodes.new, t.links.new

        def math_node(op, a, b=None):
            node = n("ShaderNodeMath")
            node.operation = op
            for i, v in enumerate((a, b)):
                if v is None:
                    continue
                if isinstance(v, (int, float)):
                    node.inputs[i].default_value = v
                else:
                    l(v, node.inputs[i])
            return node.outputs[0]

        if image is not None:
            tex = n("ShaderNodeTexImage")
            tex.image = image
            tex.extension = "EXTEND"
            base = tex.outputs[0]
            l(n("ShaderNodeUVMap").outputs[0], tex.inputs[0])
        else:
            node = n("ShaderNodeRGB")
            node.outputs[0].default_value = (*_linear(color), 1)
            base = node.outputs[0]

        emit = n("ShaderNodeEmission")
        out = n("ShaderNodeOutputMaterial")
        l(emit.outputs[0], out.inputs[0])
        if flat:
            l(base, emit.inputs[0])
            return mat

        diffuse = n("ShaderNodeBsdfDiffuse")
        to_rgb = n("ShaderNodeShaderToRGB")
        l(diffuse.outputs[0], to_rgb.inputs[0])
        bw = n("ShaderNodeRGBToBW")
        l(to_rgb.outputs[0], bw.inputs[0])
        light = bw.outputs[0]

        # Printed-comic falloff: the terminator breaks up into dots rather than a gradient.
        window = n("ShaderNodeTexCoord").outputs[5]
        sep = n("ShaderNodeSeparateXYZ")
        l(window, sep.inputs[0])
        sx = math_node("SINE", math_node("MULTIPLY", math_node("ADD", sep.outputs[0], sep.outputs[1]), self.dots))
        sy = math_node("SINE", math_node("MULTIPLY", math_node("SUBTRACT", sep.outputs[0], sep.outputs[1]), self.dots))
        pattern = math_node("MULTIPLY", sx, sy)
        lit = math_node("GREATER_THAN", math_node("ADD", light, math_node("MULTIPLY", pattern, halftone * 0.3)), 0.26)

        mix = n("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        shade = n("ShaderNodeMix")
        shade.data_type = "RGBA"
        l(base, mix.inputs[6])
        mix.inputs[7].default_value = (*_linear(self.shadow), 1)
        mix.inputs[0].default_value = 1.0
        l(lit, shade.inputs[0])
        l(mix.outputs[2], shade.inputs[6])
        l(base, shade.inputs[7])
        result = shade.outputs[2]

        if gloss > 0:
            # Hard specular stamp for metal, leather and glass.
            shiny = n("ShaderNodeBsdfGlossy")
            shiny.inputs[1].default_value = 0.28
            spec_rgb = n("ShaderNodeShaderToRGB")
            l(shiny.outputs[0], spec_rgb.inputs[0])
            spec_bw = n("ShaderNodeRGBToBW")
            l(spec_rgb.outputs[0], spec_bw.inputs[0])
            spec = math_node("GREATER_THAN", spec_bw.outputs[0], 0.34)
            add = n("ShaderNodeMix")
            add.data_type = "RGBA"
            l(math_node("MULTIPLY", spec, gloss), add.inputs[0])
            l(result, add.inputs[6])
            add.inputs[7].default_value = (1, 1, 1, 1)
            result = add.outputs[2]

        if rim:
            # A faction-coloured edge light from one side: the character pops off any background.
            geo = n("ShaderNodeNewGeometry")
            weight = n("ShaderNodeLayerWeight")
            weight.inputs[0].default_value = 0.5
            dot = n("ShaderNodeVectorMath")
            dot.operation = "DOT_PRODUCT"
            l(geo.outputs[1], dot.inputs[0])
            dot.inputs[1].default_value = self.rim_dir
            edge = math_node("GREATER_THAN", weight.outputs[1], 0.8)
            side = math_node("GREATER_THAN", dot.outputs[1], 0.12)
            add = n("ShaderNodeMix")
            add.data_type = "RGBA"
            l(math_node("MULTIPLY", math_node("MULTIPLY", edge, side), 0.92), add.inputs[0])
            l(result, add.inputs[6])
            add.inputs[7].default_value = (*_linear(self.rim), 1)
            result = add.outputs[2]

        l(result, emit.inputs[0])
        return mat


# ---- the face painter ----------------------------------------------------------------------------

class Paint:
    """A front-projected canvas addressed in head units, so a feature's paint and sculpt share coordinates."""

    def __init__(self, base, size=TEX_SIZE):
        self.size = size
        xs = np.linspace(TEX_X[0], TEX_X[1], size)
        zs = np.linspace(TEX_Z[1], TEX_Z[0], size)
        self.x, self.z = np.meshgrid(xs, zs)
        self.rgb = np.ones((size, size, 3), dtype=np.float32) * np.array(base, dtype=np.float32)

    def tint(self, mask, color, alpha=1.0):
        a = np.clip(mask * alpha, 0, 1)[..., None]
        self.rgb = self.rgb * (1 - a) + np.array(color, dtype=np.float32) * a

    def blob(self, cx, cz, rx, rz, color, alpha=1.0, soft=1.0):
        """A soft ellipse. soft=1 fades over the whole radius, small values give a hard edge."""
        d = np.hypot((self.x - cx) / rx, (self.z - cz) / rz)
        self.tint(1 - _smooth(1 - soft, 1.0, d) if soft > 0 else (d < 1), color, alpha)

    def line(self, points, widths, color, alpha=1.0, edge=0.004):
        """A variable-width ink stroke through head-space (x, z) points."""
        pts = _spline(np.array(points, dtype=float), 14)
        if np.isscalar(widths):
            w = np.full(len(pts), widths, dtype=float)
        else:
            w = np.interp(np.linspace(0, 1, len(pts)), np.linspace(0, 1, len(widths)), widths)
        scale = self.size / (TEX_X[1] - TEX_X[0])
        pad = w.max() + edge * 2
        i0 = int((pts[:, 0].min() - pad - TEX_X[0]) * scale)
        i1 = int((pts[:, 0].max() + pad - TEX_X[0]) * scale) + 2
        j0 = int((TEX_Z[1] - pts[:, 1].max() - pad) * scale)
        j1 = int((TEX_Z[1] - pts[:, 1].min() + pad) * scale) + 2
        i0, i1, j0, j1 = max(i0, 0), min(i1, self.size), max(j0, 0), min(j1, self.size)
        if i0 >= i1 or j0 >= j1:
            return
        x, z = self.x[j0:j1, i0:i1], self.z[j0:j1, i0:i1]
        mask = np.zeros_like(x)
        for k in range(len(pts) - 1):
            ax, az = pts[k]
            dx, dz = pts[k + 1] - pts[k]
            denom = dx * dx + dz * dz + 1e-9
            t = np.clip(((x - ax) * dx + (z - az) * dz) / denom, 0, 1)
            d = np.hypot(x - (ax + t * dx), z - (az + t * dz))
            r = w[k] + (w[k + 1] - w[k]) * t
            mask = np.maximum(mask, 1 - _smooth(r - edge, r + edge, d))
        a = np.clip(mask * alpha, 0, 1)[..., None]
        region = self.rgb[j0:j1, i0:i1]
        self.rgb[j0:j1, i0:i1] = region * (1 - a) + np.array(color, dtype=np.float32) * a

    def stubble(self, mask_fn, color, count=4200, seed=1, size=0.005):
        rng = np.random.default_rng(seed)
        mask = np.zeros_like(self.x, dtype=np.float32)
        ix = rng.integers(0, self.size, count)
        iz = rng.integers(0, self.size, count)
        keep = rng.random(count) < mask_fn(self.x[iz, ix], self.z[iz, ix])
        radius = max(1, int(size * self.size / 2.6))
        for j, i in zip(iz[keep], ix[keep]):
            mask[max(j - radius, 0):j + radius, max(i - radius, 0):i + radius] = 1
        self.tint(mask, color, 0.75)

    def to_image(self, name):
        img = bpy.data.images.new(name, self.size, self.size, alpha=True)
        px = np.ones((self.size, self.size, 4), dtype=np.float32)
        px[..., :3] = np.clip(self.rgb[::-1], 0, 1)
        img.pixels.foreach_set(px.ravel())
        img.update()
        return img


def _spline(points, per_segment):
    """Catmull-Rom through points of any dimension."""
    points = np.asarray(points, dtype=float)
    if len(points) < 3:
        t = np.linspace(0, 1, per_segment + 1)[:, None]
        return points[0] + (points[-1] - points[0]) * t
    p = np.vstack([2 * points[0] - points[1], points, 2 * points[-1] - points[-2]])
    out = []
    for i in range(1, len(p) - 2):
        t = np.linspace(0, 1, per_segment, endpoint=False)[:, None]
        a, b, c, d = p[i - 1], p[i], p[i + 1], p[i + 2]
        out.append(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t ** 2 + (3 * b - a - 3 * c + d) * t ** 3))
    out.append(points[-1][None])
    return np.vstack(out)


# ---- the skull --------------------------------------------------------------------------------------

DEFAULT_SHAPE = dict(
    # Half-widths down the head.
    crown=0.72, temple=0.78, cheek=0.78, jaw=0.7, chin=0.4,
    chin_z=-1.08, top_z=1.0, depth=0.92,
    # Face height field.
    brow_ridge=0.05, socket=0.05, cheekbone=0.05, hollow=0.02,
    nose_len=0.42, nose_bridge=0.20, nose_tip=0.20, nose_width=0.12, nose_hook=0.0, nose_snub=0.0, nose_skew=0.0,
    lip_top=0.022, lip_low=0.03, mouth_w=0.27, mouth_z=-0.62, smile=0.0, smirk=0.0,
    chin_jut=0.05, chin_cleft=0.0, jaw_corner=0.0, eye_z=0.03, eye_x=0.33, eye_bulge=0.03, forehead=0.03,
)


def surface_y(shape, x, z):
    """Depth of the undeformed skull's front at (x, z), so paint can sit on it when it needs to."""
    w = np.interp(z, *_profile(shape, "width"))
    d = np.interp(z, *_profile(shape, "depth"))
    return -d * np.sqrt(np.clip(1 - (x / np.maximum(w, 1e-3)) ** 2, 0, 1))


def _profile(s, kind):
    zb, zt = s["chin_z"], s["top_z"]
    if kind == "width":
        z = [zb, zb + 0.06, zb + 0.24, -0.58, -0.25, 0.1, 0.55, zt - 0.18, zt]
        v = [0.02, s["chin"] * 0.86, s["chin"] * 1.42, s["jaw"], s["cheek"], s["temple"], s["crown"], s["crown"] * 0.7, 0.02]
    else:
        d = s["depth"]
        z = [zb, zb + 0.08, -0.7, -0.25, 0.2, 0.6, zt - 0.14, zt]
        v = [0.02, d * 0.52, d * 0.8, d * 0.95, d, d * 0.92, d * 0.6, 0.02]
    # A dense, smoothed lookup keeps the skull free of bands at the control points.
    zz = np.linspace(zb, zt, 400)
    vv = np.interp(zz, z, v)
    kernel = np.hanning(31)
    kernel /= kernel.sum()
    pad = np.r_[np.full(15, vv[0]), vv, np.full(15, vv[-1])]
    vv = np.convolve(pad, kernel, mode="valid")
    return zz, vv


def _mouth_z(s, x):
    t = np.clip(x / s["mouth_w"], -1.4, 1.4)
    return s["mouth_z"] + s["smile"] * t * t * s["mouth_w"] + s["smirk"] * t * s["mouth_w"]


def face_height(s, x, z):
    """Forward displacement of the face at each (x, z). All the character is in these numbers."""
    h = np.zeros_like(x)
    ex, ez = s["eye_x"], s["eye_z"]
    nose_top, nose_tip = ez + 0.07, ez - s["nose_len"]
    h += s["forehead"] * _gauss(x, z, 0, 0.5, 0.55, 0.3)
    for sign in (-1, 1):
        h += s["brow_ridge"] * _gauss(x, z, sign * (ex - 0.03), ez + 0.2, 0.3, 0.075)
        h -= s["socket"] * _gauss(x, z, sign * ex, ez + 0.0, 0.2, 0.12)
        h += s["eye_bulge"] * _gauss(x, z, sign * ex, ez, 0.14, 0.075)
        h += s["cheekbone"] * _gauss(x, z, sign * 0.5, ez - 0.27, 0.22, 0.13)
        h -= s["hollow"] * _gauss(x, z, sign * 0.5, s["mouth_z"] + 0.1, 0.17, 0.2)
        h += s["jaw_corner"] * _gauss(x, z, sign * 0.62, -0.72, 0.17, 0.2)

    # Nose: a ridge along z with an optional hook and sideways break, ending in a ball and two wings.
    skew = s["nose_skew"] * _smooth(nose_top, nose_tip, z)
    t = np.clip((nose_top - z) / max(nose_top - nose_tip, 1e-3), 0, 1)
    ridge = s["nose_bridge"] * (t ** 0.8) + s["nose_hook"] * np.sin(np.clip(t * 1.4, 0, 1) * math.pi)
    tip_up = s["nose_snub"]
    w = 0.05 + (s["nose_width"] * 0.6 - 0.05) * t
    h += ridge * np.exp(-((x - skew) / w) ** 2) * _smooth(nose_tip - 0.06, nose_tip + 0.04, z) * _smooth(nose_top + 0.08, nose_top - 0.04, z)
    h += s["nose_tip"] * _gauss(x, z, s["nose_skew"], nose_tip + tip_up, s["nose_width"] * 0.62, 0.075)
    for sign in (-1, 1):
        h += s["nose_tip"] * 0.42 * _gauss(x, z, s["nose_skew"] + sign * s["nose_width"], nose_tip - 0.015, 0.06, 0.05)
    h -= 0.035 * _gauss(x, z, s["nose_skew"], nose_tip - 0.1, s["nose_width"] * 1.2, 0.035)

    # Mouth: lips follow the same curve the painter uses for the mouth line.
    m = _mouth_z(s, x)
    across = np.exp(-(x / (s["mouth_w"] * 0.95)) ** 4)
    h += s["lip_top"] * across * _gauss(0 * x, z, 0, m + 0.035, 1, 0.032)
    h += s["lip_low"] * across * _gauss(0 * x, z, 0, m - 0.045, 1, 0.042)
    h -= 0.018 * across * _gauss(0 * x, z, 0, m - 0.115, 1, 0.03)
    h += 0.02 * _gauss(x, z, 0, s["mouth_z"] + 0.02, s["mouth_w"] * 1.5, 0.15)

    # Chin.
    chin_z = s["chin_z"] + 0.24
    h += s["chin_jut"] * _gauss(x, z, 0, chin_z, 0.24, 0.13)
    if s["chin_cleft"]:
        h -= s["chin_cleft"] * _gauss(x, z, 0, chin_z, 0.03, 0.09)
    return h


def _grid_mesh(name, positions, closed_u=True, uv=None):
    """Quads over a (rows, cols, 3) grid. Rows run bottom to top, cols wrap when closed_u."""
    rows, cols = positions.shape[:2]
    idx = np.arange(rows * cols).reshape(rows, cols)
    a = idx[:-1, :]
    b = np.roll(idx, -1, axis=1)[:-1, :]
    c = np.roll(idx, -1, axis=1)[1:, :]
    d = idx[1:, :]
    if not closed_u:
        a, b, c, d = a[:, :-1], b[:, :-1], c[:, :-1], d[:, :-1]
    faces = np.stack([a, b, c, d], axis=-1).reshape(-1, 4)
    return _mesh(name, positions.reshape(-1, 3), faces, uv.reshape(-1, 2) if uv is not None else None)


def _mesh(name, verts, faces, uv=None):
    mesh = bpy.data.meshes.new(name)
    mesh.vertices.add(len(verts))
    mesh.vertices.foreach_set("co", np.asarray(verts, dtype=np.float32).ravel())
    n_faces = len(faces)
    mesh.loops.add(n_faces * 4)
    mesh.polygons.add(n_faces)
    mesh.polygons.foreach_set("loop_start", np.arange(0, n_faces * 4, 4))
    mesh.loops.foreach_set("vertex_index", np.asarray(faces, dtype=np.int32).ravel())
    if uv is not None:
        layer = mesh.uv_layers.new(name="UVMap")
        layer.data.foreach_set("uv", np.asarray(uv, dtype=np.float32)[np.asarray(faces).ravel()].ravel())
    mesh.update(calc_edges=True)
    mesh.validate(clean_customdata=False)
    mesh.shade_smooth()
    return mesh


# ---- the portrait ----------------------------------------------------------------------------------

class Portrait:
    """One character's bust. Cast functions call these in order, then the studio renders the scene."""

    def __init__(self, collection, inks, shape, skin, turn=0.0, tilt=0.0, pitch=0.0, body_turn=0.0, outline=0.02):
        self.collection = collection
        self.inks = inks
        self.outline_w = outline
        self.skin = skin
        self.s = {**DEFAULT_SHAPE, **shape}
        self.paint = Paint(skin)
        self.head_root = bpy.data.objects.new("HeadRoot", None)
        self.body_root = bpy.data.objects.new("BodyRoot", None)
        collection.objects.link(self.head_root)
        collection.objects.link(self.body_root)
        # The head pivots at the top of the neck, so a tilt reads as attitude rather than a rotated image.
        self.neck_pivot = Vector((0, 0.18, -0.9))
        rot = Euler((pitch, tilt, turn), "XYZ").to_matrix().to_4x4()
        self.head_root.matrix_world = Matrix.Translation(self.neck_pivot) @ rot @ Matrix.Translation(-self.neck_pivot)
        self.body_root.rotation_euler = (0, 0, body_turn)
        self.body_root.location = (0, 0, 0.22)  # Sits the head down into the shoulders.

    # -- object plumbing

    def _add(self, mesh, material, root=None, outline=None):
        obj = bpy.data.objects.new(mesh.name, mesh)
        self.collection.objects.link(obj)
        obj.parent = root or self.head_root
        mesh.materials.append(material)
        width = self.outline_w if outline is None else outline
        if width > 0:
            mesh.materials.append(self.inks.outline)
            mod = obj.modifiers.new("Ink", "SOLIDIFY")
            mod.thickness = width
            mod.offset = 1.0
            mod.use_flip_normals = True
            mod.use_rim = False
            mod.material_offset = 1
        return obj

    def mat(self, color, gloss=0.0, **kw):
        return self.inks.get(tuple(color), gloss, **kw)

    # -- the head

    def skull(self):
        s = self.s
        rows, cols = 460, 620
        lat = np.linspace(-math.pi / 2, math.pi / 2, rows)
        lon = np.linspace(0, 2 * math.pi, cols, endpoint=False)
        la, lo = np.meshgrid(lat, lon, indexing="ij")
        z = s["chin_z"] + (np.sin(la) * 0.5 + 0.5) * (s["top_z"] - s["chin_z"])
        zw, vw = _profile(s, "width")
        zd, vd = _profile(s, "depth")
        w, d = np.interp(z, zw, vw), np.interp(z, zd, vd)
        x = np.cos(lo) * w
        y = np.sin(lo) * d
        front = _smooth(0.22, -0.28, y / np.maximum(d, 1e-3))
        y = y - face_height(s, x, z) * front
        # The back of the skull bulges, so the head isn't a mask from the side.
        back = _smooth(0.0, 0.8, y / s["depth"]) * _gauss(0 * x, z, 0, 0.32, 1, 0.55)
        y = y + back * 0.14
        pos = np.stack([x, y, z], axis=-1)
        u = (x - TEX_X[0]) / (TEX_X[1] - TEX_X[0])
        v = (z - TEX_Z[0]) / (TEX_Z[1] - TEX_Z[0])
        self.head_mesh = (pos, np.stack([u, v], axis=-1))
        return self

    def finish_skull(self):
        """Call after painting, because the skin material needs the finished canvas."""
        pos, uv = self.head_mesh
        mesh = _grid_mesh("Skull", pos, uv=uv)
        self.image = self.paint.to_image("PortraitFace")
        self._add(mesh, self.inks.get(self.skin, 0.0, image=self.image, halftone=0.3))
        return self

    def base_skin(self, shadow, blush, warm=None):
        """Under-painting that gives a flat skin some form before the features go on top."""
        p, s = self.paint, self.s
        ez = s["eye_z"]
        for sign in (-1, 1):
            p.blob(sign * 0.48, ez - 0.36, 0.26, 0.17, blush, 0.3)
            p.blob(sign * s["eye_x"], ez + 0.0, 0.24, 0.13, shadow, 0.45)
        p.blob(s["nose_skew"], ez - s["nose_len"], s["nose_width"] * 1.2, 0.09, blush, 0.3)
        return self

    def nostrils(self, color):
        s = self.s
        tip = s["eye_z"] - s["nose_len"]
        for sign in (-1, 1):
            x = s["nose_skew"] + sign * s["nose_width"] * 0.42
            self.paint.line([(x - sign * 0.025, tip - 0.055), (x + sign * 0.025, tip - 0.04)], 0.011, color)
        return self

    def nose_line(self, color, side=1):
        """A single ink stroke down the shadow side of the nose. A little goes a long way."""
        s = self.s
        tip = s["eye_z"] - s["nose_len"]
        x = s["nose_skew"] + side * s["nose_width"] * 0.95
        self.paint.line([(x, tip + 0.05), (x + side * 0.03, tip - 0.015), (x - side * 0.025, tip - 0.05)], [0.003, 0.008, 0.004], color)
        return self

    def eye(self, side, iris, ink=(0.07, 0.04, 0.05), w=0.135, up=0.078, low=0.04, tilt=0.0, gaze=(0.0, 0.0),
            lid=0.0, white=(0.95, 0.92, 0.87), crease=True, lash=0.016, iris_r=0.066, bags=0.0, skin_shade=None):
        """Almond eye. tilt>0 lifts the outer corner, lid (0..1) drops the upper lid for a hooded look."""
        p, s = self.paint, self.s
        cx, cz = side * s["eye_x"], s["eye_z"]
        k = EYE_SCALE
        w, up, low, iris_r, lash = w * k, up * k, low * k, iris_r * k, lash * k

        def arcs(t):
            base = cz + tilt * t
            top = base + up * (1 - np.abs(t) ** 2.2) * (1 - lid) ** 1.0
            bottom = base - low * (1 - np.abs(t) ** 2.0)
            return top, bottom

        t = (p.x - cx) / w
        top, bottom = arcs(t * side)
        inside = (np.abs(t) < 1) & (p.z < top) & (p.z > bottom)
        p.tint(inside.astype(np.float32), white)
        # Shadow cast by the upper lid.
        shade = inside & (p.z > top - 0.024)
        p.tint(shade.astype(np.float32), [c * 0.72 for c in white], 0.75)
        ix, iz = cx + gaze[0], cz + gaze[1] + 0.008
        d = np.hypot(p.x - ix, p.z - iz)
        p.tint(((d < iris_r) & inside).astype(np.float32), ink)
        p.tint(((d < iris_r * 0.9) & inside).astype(np.float32), iris)
        p.tint(((d < iris_r * 0.9) & inside & (p.z > iz + 0.008)).astype(np.float32), [c * 0.62 for c in iris], 0.7)
        p.tint(((d < iris_r * 0.46) & inside).astype(np.float32), (0.03, 0.02, 0.03))
        hd = np.hypot(p.x - (ix - 0.018), p.z - (iz + 0.022))
        p.tint(((hd < iris_r * 0.26) & inside).astype(np.float32), (1, 1, 1))

        ts = np.linspace(-1, 1, 24)
        def curve(values):
            return [(cx + side * a * w, float(b)) for a, b in zip(ts, values)]
        tops = np.array([arcs(a)[0] for a in ts])
        lows = np.array([arcs(a)[1] for a in ts])
        p.line(curve(tops), [lash * 0.45, lash, lash * 1.25, lash], ink)
        # Wing past the outer corner, so the eye has a direction.
        outer = (cx + side * w, float(arcs(1.0)[0]))
        p.line([outer, (outer[0] + side * 0.035, outer[1] - 0.008 + tilt * 0.3)], [lash * 0.9, 0.002], ink)
        p.line(curve(lows), lash * 0.32, ink, 0.85)
        if crease:
            p.line([(cx + side * a * w * 1.02, float(arcs(a)[0]) + 0.034 + 0.02 * lid) for a in np.linspace(-0.8, 0.9, 10)], 0.0045, ink, 0.6)
        if bags:
            p.line([(cx + side * a * w, float(arcs(a)[1]) - 0.03 - 0.016 * (1 - a * a)) for a in np.linspace(-0.85, 0.85, 8)], 0.004, skin_shade or ink, bags)
        return self

    def brow(self, side, color, inner=0.11, outer=0.1, thick=0.028, arch=0.03, length=0.21, offset=0.0, thin_end=True, gap=None):
        """inner/outer are heights above the eye line. Low inner and high outer is fury; the reverse is worry."""
        s = self.s
        cx = side * s["eye_x"] + side * offset
        cz = s["eye_z"]
        points = [
            (cx - side * length * 0.72, cz + inner),
            (cx - side * length * 0.18, cz + (inner * 0.6 + outer * 0.4) + arch),
            (cx + side * length * 0.42, cz + (inner * 0.25 + outer * 0.75) + arch * 0.9),
            (cx + side * length * 0.82, cz + outer - 0.025),
        ]
        self.paint.line(points, [thick * 0.9, thick * 1.05, thick * 0.8, 0.003 if thin_end else thick * 0.5], color)
        return self

    def mouth(self, ink, lip=None, width=None, teeth=False, open_amt=0.0, lip_alpha=0.75, line=0.011):
        p, s = self.paint, self.s
        mw = width or s["mouth_w"]
        xs = np.linspace(-mw, mw, 26)
        mz = _mouth_z(s, xs)
        if lip is not None:
            top = [(x, float(z) + 0.035 * (1 - (x / mw) ** 2) ** 0.8 + 0.018 * np.exp(-((abs(x) - mw * 0.25) / (mw * 0.22)) ** 2) * 0.9) for x, z in zip(xs, mz)]
            bottom = [(x, float(z) - 0.065 * (1 - (x / mw) ** 2) ** 0.7) for x, z in zip(xs, mz)]
            t = np.clip(p.x / mw, -1, 1)
            centre = _mouth_z(s, p.x)
            lip_mask = (np.abs(p.x) < mw) & (p.z < centre + 0.042 * (1 - t * t) ** 0.8) & (p.z > centre - 0.062 * (1 - t * t) ** 0.7)
            p.tint(lip_mask.astype(np.float32), lip, lip_alpha)
            p.line(bottom[3:-3], 0.003, ink, 0.45)
        if open_amt > 0:
            t = np.clip(p.x / mw, -1, 1)
            centre = _mouth_z(s, p.x)
            hole = (np.abs(p.x) < mw * 0.86) & (p.z < centre + 0.005) & (p.z > centre - open_amt * (1 - (t / 0.86) ** 2))
            p.tint(hole.astype(np.float32), (0.11, 0.03, 0.05))
            if teeth:
                band = hole & (p.z > centre - open_amt * 0.46)
                p.tint(band.astype(np.float32), (0.94, 0.9, 0.82))
        p.line(list(zip(xs, mz)), [line * 0.4, line, line * 1.2, line, line * 0.4], ink)
        # Corners tuck in: the smallest thing that makes a mouth look deliberate.
        for sign in (-1, 1):
            cz = float(_mouth_z(s, np.array(sign * mw)))
            p.line([(sign * mw * 0.97, cz + 0.008), (sign * mw * 1.08, cz + 0.002 + s["smile"] * 0.05)], [line * 0.6, 0.002], ink)
        return self

    def under_lip(self, color):
        s = self.s
        self.paint.line([(-0.08, s["mouth_z"] - 0.105), (0, s["mouth_z"] - 0.115), (0.08, s["mouth_z"] - 0.105)], [0.002, 0.009, 0.002], color, 0.65)
        return self

    def ear(self, side, color, shadow, size=1.0, z=-0.06, stick=0.0):
        """A shell around a dark bowl, so it survives the cel shader as a recognisable ear."""
        s = self.s
        x0 = np.interp(z, *_profile(s, "width"))
        hull = _ellipsoid((side * (x0 + 0.015 + stick), 0.1, z), (0.055 * size, 0.13 * size, 0.2 * size), 48, 32)
        self._add(hull, self.mat(color))
        bowl = _ellipsoid((side * (x0 + 0.05 + stick), 0.075, z - 0.005), (0.03 * size, 0.08 * size, 0.135 * size), 24, 16)
        self._add(bowl, self.mat(shadow), outline=0.0)
        return self

    def neck(self, color, width=0.42, depth=0.42, top=-0.72, bottom=-1.95, flare=1.25):
        zs = np.linspace(bottom, top, 16)
        t = (zs - bottom) / (top - bottom)
        factor = 1 + (flare - 1) * (1 - t) ** 2.4
        rings = [[(width * f * math.cos(a), 0.2 + depth * f * math.sin(a), z) for a in np.linspace(0, 2 * math.pi, 48, endpoint=False)] for f, z in zip(factor, zs)]
        self._add(_grid_mesh("Neck", np.array(rings)), self.mat(color), root=self.body_root)
        return self

    # -- generic geometry, for hair, hats and costume

    def sweep(self, points, widths, color, depth=None, gloss=0.0, root=None, outline=None, sides=14, seg=10, roll=0.0, halftone=0.34):
        """A tapered tube or ribbon along points. depth/width < 1 flattens it into a lock or a strap."""
        self._add(sweep_mesh(points, widths, depth, sides, seg, roll), self.mat(color, gloss, halftone=halftone), root=root, outline=outline)
        return self

    def loft(self, rings, color, gloss=0.0, root=None, outline=None, cap=True, halftone=0.34):
        self._add(loft_mesh(rings, cap), self.mat(color, gloss, halftone=halftone), root=root, outline=outline)
        return self

    def ball(self, centre, radii, color, gloss=0.0, root=None, outline=None, rot=None):
        mesh = _ellipsoid(centre, radii, 40, 24, rot)
        self._add(mesh, self.mat(color, gloss), root=root, outline=outline)
        return self

    def ring(self, centre, major, minor, color, gloss=0.0, normal=(0, -1, 0), root=None, outline=None, squash=1.0):
        self._add(_torus(centre, major, minor, normal, squash), self.mat(color, gloss), root=root, outline=outline)
        return self

    def disc(self, centre, radius, color, normal=(0, -1, 0), gloss=0.0, root=None, outline=0.0, flat=False):
        self._add(_disc(centre, radius, normal), self.mat(color, gloss, flat=flat), root=root, outline=outline)
        return self

    def plate(self, outline_points, thickness, color, gloss=0.0, root=None, outline=None, halftone=0.34):
        """Extrudes a 3D polygon along its average normal: lapels, buckles, badges."""
        self._add(plate_mesh(outline_points, thickness), self.mat(color, gloss, halftone=halftone), root=root, outline=outline)
        return self

    def cap(self, color, keep, inflate=0.035, gloss=0.0):
        """Hair or a fitted hood: the unsculpted skull, slightly inflated, trimmed by keep(x, y, z)."""
        s = self.s
        rows, cols = 220, 300
        lat = np.linspace(-math.pi / 2, math.pi / 2, rows)
        lon = np.linspace(0, 2 * math.pi, cols, endpoint=False)
        la, lo = np.meshgrid(lat, lon, indexing="ij")
        z = s["chin_z"] + (np.sin(la) * 0.5 + 0.5) * (s["top_z"] - s["chin_z"])
        w, d = np.interp(z, *_profile(s, "width")), np.interp(z, *_profile(s, "depth"))
        x = np.cos(lo) * w
        y = np.sin(lo) * d
        back = _smooth(0.0, 0.8, y / s["depth"]) * _gauss(0 * x, z, 0, 0.32, 1, 0.55)
        y = y + back * 0.14
        y = y - s["forehead"] * _gauss(x, z, 0, 0.5, 0.55, 0.3) * (y < 0)
        r = np.stack([x, y, z - 0.05], axis=-1)
        unit = r / np.maximum(np.linalg.norm(r, axis=-1, keepdims=True), 1e-4)
        pos = np.stack([x, y, z], axis=-1) + unit * inflate
        mask = keep(x, y, z)
        idx = np.arange(rows * cols).reshape(rows, cols)
        a, b = idx[:-1, :], np.roll(idx, -1, axis=1)[:-1, :]
        c, e = np.roll(idx, -1, axis=1)[1:, :], idx[1:, :]
        faces = np.stack([a, b, c, e], axis=-1).reshape(-1, 4)
        flat = mask.ravel()
        faces = faces[flat[faces].all(axis=1)]
        used, inverse = np.unique(faces, return_inverse=True)
        mesh = _mesh("Cap", pos.reshape(-1, 3)[used], inverse.reshape(-1, 4))
        self._add(mesh, self.mat(color, gloss))
        return self


def _frame(tangent, up_hint=(0.0, -1.0, 0.0)):
    n = np.cross(tangent, up_hint)
    if np.linalg.norm(n) < 1e-4:
        n = np.cross(tangent, (1.0, 0.0, 0.0))
    n = n / np.linalg.norm(n)
    b = np.cross(n, tangent)
    return n, b / np.linalg.norm(b)


def sweep_mesh(points, widths, depth=None, sides=14, seg=10, roll=0.0):
    pts = _spline(np.asarray(points, dtype=float), seg)
    if np.isscalar(widths):
        widths = [widths, widths]
    w = np.interp(np.linspace(0, 1, len(pts)), np.linspace(0, 1, len(widths)), widths)
    flatten = 1.0 if depth is None else depth
    rings = []
    angles = np.linspace(0, 2 * math.pi, sides, endpoint=False)
    for i, p in enumerate(pts):
        tangent = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]
        tangent = tangent / max(np.linalg.norm(tangent), 1e-6)
        n, b = _frame(tangent)
        c, s = math.cos(roll), math.sin(roll)
        n, b = n * c + b * s, b * c - n * s
        rings.append([p + n * (w[i] * math.cos(a)) + b * (w[i] * flatten * math.sin(a)) for a in angles])
    return loft_mesh(rings, True, "Sweep")


def loft_mesh(rings, cap=True, name="Loft"):
    rings = np.asarray(rings, dtype=float)
    rows, cols = rings.shape[:2]
    verts = rings.reshape(-1, 3)
    idx = np.arange(rows * cols).reshape(rows, cols)
    a, b = idx[:-1, :], np.roll(idx, -1, axis=1)[:-1, :]
    c, d = np.roll(idx, -1, axis=1)[1:, :], idx[1:, :]
    faces = np.stack([a, b, c, d], axis=-1).reshape(-1, 4)
    if cap:
        # A centre point fan, written as degenerate quads so every polygon stays four-sided.
        centres = np.array([rings[0].mean(axis=0), rings[-1].mean(axis=0)])
        base = len(verts)
        verts = np.vstack([verts, centres])
        bottom = np.stack([np.roll(idx[0], -1), idx[0], np.full(cols, base), np.full(cols, base)], axis=-1)
        top = np.stack([idx[-1], np.roll(idx[-1], -1), np.full(cols, base + 1), np.full(cols, base + 1)], axis=-1)
        return _mesh_mixed(name, verts, faces, bottom, top)
    return _mesh(name, verts, faces)


def _mesh_mixed(name, verts, quads, *fans):
    """Quads plus triangle fans whose last two indices repeat."""
    tris = np.vstack([f[:, :3] for f in fans]) if fans else np.zeros((0, 3), dtype=int)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(np.asarray(verts).tolist(), [], [tuple(q) for q in quads.tolist()] + [tuple(t) for t in tris.tolist()])
    mesh.update()
    mesh.shade_smooth()
    return mesh


def plate_mesh(points, thickness):
    pts = np.asarray(points, dtype=float)
    c = pts.mean(axis=0)
    normal = np.zeros(3)
    for i in range(len(pts)):
        normal += np.cross(pts[i] - c, pts[(i + 1) % len(pts)] - c)
    normal /= max(np.linalg.norm(normal), 1e-6)
    return loft_mesh([pts + normal * thickness * 0.5, pts - normal * thickness * 0.5], True, "Plate")


def _ellipsoid(centre, radii, sides, rows, rot=None):
    if np.isscalar(radii):
        radii = (radii, radii, radii)
    lat = np.linspace(-math.pi / 2 + 1e-3, math.pi / 2 - 1e-3, rows)
    lon = np.linspace(0, 2 * math.pi, sides, endpoint=False)
    la, lo = np.meshgrid(lat, lon, indexing="ij")
    pos = np.stack([np.cos(la) * np.cos(lo) * radii[0], np.cos(la) * np.sin(lo) * radii[1], np.sin(la) * radii[2]], axis=-1)
    if rot is not None:
        pos = pos @ np.array(Euler(rot, "XYZ").to_matrix()).T
    return loft_mesh(pos + np.array(centre), True, "Ball")


def _torus(centre, major, minor, normal, squash):
    n = np.array(normal, dtype=float)
    n /= np.linalg.norm(n)
    u, v = _frame(n, (0.0, 0.0, 1.0))
    rings = []
    for a in np.linspace(0, 2 * math.pi, 56, endpoint=False):
        rad = u * math.cos(a) + v * math.sin(a) * squash
        rings.append([np.array(centre) + rad * major + (rad / max(np.linalg.norm(rad), 1e-6)) * minor * math.cos(b) + n * minor * math.sin(b) for b in np.linspace(0, 2 * math.pi, 12, endpoint=False)])
    rings = np.array(rings)
    rows, cols = rings.shape[:2]
    idx = np.arange(rows * cols).reshape(rows, cols)
    a, b = idx, np.roll(idx, -1, axis=1)
    c, d = np.roll(b, -1, axis=0), np.roll(idx, -1, axis=0)
    return _mesh("Ring", rings.reshape(-1, 3), np.stack([a, b, c, d], axis=-1).reshape(-1, 4))


def _disc(centre, radius, normal):
    n = np.array(normal, dtype=float)
    n /= np.linalg.norm(n)
    u, v = _frame(n, (0.0, 0.0, 1.0))
    ring = [np.array(centre) + (u * math.cos(a) + v * math.sin(a)) * radius for a in np.linspace(0, 2 * math.pi, 48, endpoint=False)]
    verts = np.array([np.array(centre)] + ring)
    tris = [(0, i + 1, (i + 1) % 48 + 1) for i in range(48)]
    mesh = bpy.data.meshes.new("Disc")
    mesh.from_pydata(verts.tolist(), [], tris)
    mesh.update()
    mesh.shade_smooth()
    return mesh


# ---- the backdrop --------------------------------------------------------------------------------

def backdrop_base(size, dark, light):
    """Faction colour with a pale glow behind the head and a printed dot falloff to the corners."""
    grid = np.linspace(0, 1, size)
    x, y = np.meshgrid(grid, grid)
    r = np.hypot(x - 0.5, y - 0.42)
    glow = np.clip(1.05 - r * 1.9, 0, 1) ** 1.4
    out = np.zeros((size, size, 3), dtype=np.float32)
    for i in range(3):
        out[..., i] = dark[i] + (light[i] - dark[i]) * glow * 0.55
    # Dots grow toward the corners.
    cycles = size / 13.0
    pattern = np.sin((x + y) * cycles * math.pi) * np.sin((x - y) * cycles * math.pi)
    dots = pattern > (1.1 - r * 1.25)
    out[dots] *= 0.74
    return out, x, y, r


def _stamp_ring(mask, x, y, cx, cy, r, w):
    d = np.hypot(x - cx, y - cy)
    mask |= np.abs(d - r) < w


def motif(kind, x, y, rng):
    """One recognisable idea per character, as a mask. Kept behind the head and out towards the edges."""
    m = np.zeros_like(x, dtype=bool)
    if kind == "rays":
        a = np.arctan2(y - 0.42, x - 0.5)
        m = np.sin(a * 16) > 0.35
    elif kind == "wind":
        for k in range(11):
            y0 = rng.uniform(0.02, 0.98)
            wave = y0 + 0.035 * np.sin(x * 7 + k) + (x - 0.5) * -0.16
            m |= (np.abs(y - wave) < 0.006 + 0.005 * np.sin(x * 3 + k)) & (np.sin(x * 2.2 + k * 1.9) > -0.35)
    elif kind == "isobars":
        field = np.sin(x * 5 + 1.2 * np.sin(y * 4)) + np.cos(y * 6 + 1.4 * np.sin(x * 3))
        m = np.abs((field * 3.4) % 1 - 0.5) < 0.05
    elif kind == "gears":
        for cx, cy, r, teeth in ((0.1, 0.16, 0.2, 12), (0.92, 0.3, 0.17, 10), (0.08, 0.86, 0.18, 11), (0.95, 0.9, 0.24, 14), (0.3, -0.02, 0.1, 8)):
            d = np.hypot(x - cx, y - cy)
            a = np.arctan2(y - cy, x - cx)
            outer = r * (1 + 0.1 * (np.sin(a * teeth) > 0))
            m |= (d < outer) & (d > r * 0.72)
            m |= (d < r * 0.26) & (d > r * 0.12)
            m |= (d < r * 0.74) & (np.abs(np.sin(a * 2)) < 0.14) & (d > r * 0.22)
    elif kind == "rust":
        n = np.sin(x * 37 + 4 * np.sin(y * 11)) * np.sin(y * 41 + 3 * np.sin(x * 13)) + np.sin((x + y) * 23)
        m = n > 0.92
        for ly in (0.14, 0.86):
            m |= np.abs(y - ly) < 0.006
        for ly in (0.14, 0.86):
            for lx in np.arange(0.03, 1.0, 0.09):
                m |= np.hypot(x - lx, y - ly) < 0.014
    elif kind == "flak":
        for _ in range(9):
            cx, cy = rng.uniform(0, 1), rng.uniform(0, 1)
            r = rng.uniform(0.05, 0.11)
            d = np.hypot(x - cx, y - cy)
            a = np.arctan2(y - cy, x - cx)
            m |= (d < r * (0.74 + 0.26 * (np.sin(a * 9 + cx * 9) > 0))) & (d > r * 0.34 + 0.01 * np.sin(a * 5))
    elif kind == "fuse":
        # A clock face, ticking: her charges are always on a timer.
        d = np.hypot(x - 0.5, y - 0.42)
        a = np.arctan2(y - 0.42, x - 0.5)
        m = (np.abs(d - 0.56) < 0.006) | (np.abs(d - 0.46) < 0.003)
        m |= (d > 0.47) & (d < 0.55) & (((a + np.pi) * 30 / (2 * np.pi)) % 1 < 0.14)
    elif kind == "chart":
        for k in np.arange(0.0, 1.1, 0.125):
            m |= np.abs(x - k) < 0.0016
            m |= np.abs(y - k) < 0.0016
        pts = rng.uniform(0, 1, (11, 2))
        for k in range(len(pts)):
            m |= np.hypot(x - pts[k, 0], y - pts[k, 1]) < 0.009
            if k:
                ax, ay = pts[k - 1]
                dx, dy = pts[k] - pts[k - 1]
                t = np.clip(((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy), 0, 1)
                m |= np.hypot(x - ax - t * dx, y - ay - t * dy) < 0.0028
    elif kind in ("slash_l", "slash_r"):
        sign = 1 if kind == "slash_l" else -1
        u = x * sign + y * 0.55
        for k, w in ((0.0, 0.008), (0.18, 0.024), (0.3, 0.006), (0.62, 0.03), (0.78, 0.008), (1.02, 0.016)):
            offset = (0.5 - 0.5 * sign)
            m |= np.abs(u - k - 0.02 + offset * 1.0) < w
    elif kind == "bars":
        for k in np.arange(0.05, 1.0, 0.13):
            m |= np.abs(x - k) < 0.024
        m |= np.abs(y - 0.12) < 0.018
        m |= np.abs(y - 0.88) < 0.018
    elif kind == "clouds":
        for cx, cy, r in ((0.08, 0.9, 0.16), (0.24, 0.98, 0.14), (0.0, 0.76, 0.1), (0.9, 0.86, 0.17), (1.0, 0.72, 0.12), (0.75, 1.0, 0.12), (0.94, 0.12, 0.1), (0.84, 0.17, 0.08), (0.05, 0.22, 0.08), (0.14, 0.18, 0.07)):
            m |= np.hypot(x - cx, y - cy) < r
    elif kind == "current":
        for k in np.arange(-0.2, 1.3, 0.11):
            wave = k + 0.09 * np.sin(x * 7.0 + k * 3) + (x - 0.5) * 0.3
            m |= np.abs(y - wave) < 0.012
    elif kind == "storm":
        for k, (x0, y0) in enumerate(((0.1, 0.0), (0.88, 0.0), (0.04, 0.5), (0.97, 0.44))):
            pts = [(x0, y0)]
            for _ in range(5):
                pts.append((pts[-1][0] + rng.uniform(-0.07, 0.07), pts[-1][1] + 0.11))
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                dx, dy = bx - ax, by - ay
                t = np.clip(((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy), 0, 1)
                m |= np.hypot(x - ax - t * dx, y - ay - t * dy) < 0.009 * (1.3 - t * 0.3)
    return m


def backdrop(size, dark, light, kind, seed):
    out, x, y, r = backdrop_base(size, dark, light)
    if kind:
        m = motif(kind, x, y, np.random.default_rng(seed))
        fade = np.clip(0.35 + r * 1.1, 0, 1)[..., None]
        ink = np.array(light, dtype=np.float32) * 0.5 + np.array(dark, dtype=np.float32) * 0.5
        out = np.where(m[..., None], out * (1 - 0.6 * fade) + ink * 0.6 * fade, out)
    # A dark vignette: the corners stay quiet and the eye goes to the face.
    return out * np.clip(1.16 - r * 0.62, 0.55, 1)[..., None]


# ---- studio ------------------------------------------------------------------------------------------

class Studio:
    """Works in its own scene, so the user's scene, render settings and selection stay untouched."""

    def __init__(self, resolution=1536):
        self.res = resolution
        self.scene = bpy.data.scenes.new("PortraitStudio")
        self.world = bpy.data.worlds.new("PortraitWorld")
        self.scene.world = self.world
        self.world.use_nodes = True
        for node in self.world.node_tree.nodes:
            if node.type == "BACKGROUND":
                node.inputs[1].default_value = 0.0
        scene = self.scene
        try:
            scene.render.engine = "BLENDER_EEVEE"
        except TypeError as err:
            raise RuntimeError(f"Portraits need EEVEE: {err}")
        scene.render.resolution_x = scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        scene.render.film_transparent = True
        scene.render.filter_size = 0.6
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGBA"
        scene.display_settings.display_device = "sRGB"
        scene.view_settings.view_transform = "Standard"
        scene.view_settings.look = "None"
        scene.eevee.taa_render_samples = 16
        scene.eevee.use_shadows = True
        self.objects = []

    def light(self, key_dir=(-0.6, -0.55, 0.65)):
        sun = bpy.data.lights.new("Key", "SUN")
        sun.energy = 3.14
        sun.angle = math.radians(1.2)
        sun.use_shadow = True
        if hasattr(sun, "use_shadow_jitter"):
            sun.use_shadow_jitter = False
        obj = bpy.data.objects.new("Key", sun)
        self.scene.collection.objects.link(obj)
        obj.rotation_euler = Vector(key_dir).to_track_quat("Z", "Y").to_euler()
        return obj

    def camera(self, target=(0, 0, -0.42), span=3.9, side=-0.0):
        data = bpy.data.cameras.new("PortraitCam")
        data.lens = 70
        data.sensor_width = 36
        data.clip_start = 0.1
        data.clip_end = 100
        distance = span * data.lens / data.sensor_width
        cam = bpy.data.objects.new("PortraitCam", data)
        self.scene.collection.objects.link(cam)
        t = Vector(target)
        cam.location = t + Vector((side, -1.0, 0.04)).normalized() * distance
        cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
        self.scene.camera = cam
        return cam

    def render(self, path):
        self.scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True, scene=self.scene.name)
        img = bpy.data.images.load(str(path), check_existing=False)
        w, h = img.size
        px = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        bpy.data.images.remove(img)
        return px.reshape(h, w, 4)[::-1]

    def close(self):
        scene = self.scene
        for obj in list(scene.collection.all_objects):
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
            elif isinstance(data, bpy.types.Light):
                bpy.data.lights.remove(data)
            elif isinstance(data, bpy.types.Camera):
                bpy.data.cameras.remove(data)
        bpy.data.scenes.remove(scene)
        bpy.data.worlds.remove(self.world)
        for mat in [m for m in bpy.data.materials if m.name.startswith(("PortraitCel", "PortraitInk")) and m.users == 0]:
            bpy.data.materials.remove(mat)
        for img in [i for i in bpy.data.images if i.name.startswith("PortraitFace")]:
            bpy.data.images.remove(img)
