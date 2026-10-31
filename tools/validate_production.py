#!/usr/bin/env python3
"""Checks every exported .glb against the budgets, independent of Blender.

Reads the budgets from the gate script, so there is one source of truth. Checks the catalogue
in assets/asset_manifest.json is exactly what is on disk, and that each file really is
what the game code will assume. Exits non-zero on any failure.

    python3 tools/validate_production.py [directory]
"""
import ast
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / ".claude/skills/mobile-blender-pipeline/scripts/enforce_mobile_budget.py"
MANIFEST = ROOT / "assets/asset_manifest.json"
EPS = 0.002


def load_budgets():
    for node in ast.parse(GATE.read_text()).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "BUDGET_TIERS":
            return ast.literal_eval(node.value)
    raise RuntimeError("BUDGET_TIERS not found in the gate script.")


def read_glb(path):
    with path.open("rb") as handle:
        magic, version, _ = struct.unpack("<4sII", handle.read(12))
        if magic != b"glTF" or version != 2:
            raise ValueError("not a glTF 2.0 binary")
        size, _ = struct.unpack("<II", handle.read(8))
        document = json.loads(handle.read(size))
        chunk = handle.read(8)
        binary = handle.read(struct.unpack("<II", chunk)[0]) if chunk else b""
    return document, binary


def png_size(data):
    return struct.unpack(">II", data[16:24])


def _q_mul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    )


def _q_rotate(q, v):
    x, y, z, w = q
    tx = 2 * (y * v[2] - z * v[1])
    ty = 2 * (z * v[0] - x * v[2])
    tz = 2 * (x * v[1] - y * v[0])
    return (
        v[0] + w * tx + y * tz - z * ty,
        v[1] + w * ty + z * tx - x * tz,
        v[2] + w * tz + x * ty - y * tx,
    )


def _check_socket_bones(doc, errors):
    nodes = doc["nodes"]
    parents = {child: i for i, node in enumerate(nodes) for child in node.get("children", [])}
    index = {node.get("name"): i for i, node in enumerate(nodes)}

    def global_rotation(i):
        local = tuple(nodes[i].get("rotation", (0, 0, 0, 1)))
        return _q_mul(global_rotation(parents[i]), local) if i in parents else local

    # An item's length is its local +Y, its top is local +X. Values are in glTF space.
    expected = {"weapon.R": ((0, 0, 1), (0, 1, 0)), "gun.R": ((0, -1, 0), (0, 0, 1))}
    for bone, (length_axis, top_axis) in expected.items():
        if bone not in index:
            errors.append(f"missing socket bone {bone}")
            continue
        q = global_rotation(index[bone])
        for local, want, label in (((0, 1, 0), length_axis, "length"), ((1, 0, 0), top_axis, "top")):
            got = _q_rotate(q, local)
            if sum(a * b for a, b in zip(got, want)) < 0.95:
                errors.append(f"{bone} {label} axis is {tuple(round(c, 2) for c in got)}, expected {want}")


def _check_clips(doc, binary, clips, errors):
    found = {clip["name"]: clip for clip in doc.get("animations", [])}
    missing = sorted(set(clips) - set(found))
    if missing:
        errors.append(f"missing clips {missing}")
    for name, clip in found.items():
        moved = False
        for channel in clip["channels"]:
            if channel["target"]["path"] != "rotation":
                continue
            accessor = doc["accessors"][clip["samplers"][channel["sampler"]]["output"]]
            view = doc["bufferViews"][accessor["bufferView"]]
            start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
            values = struct.unpack_from(f"<{accessor['count'] * 4}f", binary, start)
            first = values[:4]
            if any(abs(values[i] - first[i % 4]) > 1e-3 for i in range(len(values))):
                moved = True
                break
        if not moved:
            errors.append(f"clip {name} never moves a bone")


def check_file(path, entry, budget, clips):
    errors = []
    doc, binary = read_glb(path)

    tris = 0
    bounds = None
    for mesh in doc.get("meshes", []):
        for primitive in mesh["primitives"]:
            if primitive.get("mode", 4) != 4:
                errors.append("non-triangle primitive")
            tris += doc["accessors"][primitive["indices"]]["count"] // 3
            position = doc["accessors"][primitive["attributes"]["POSITION"]]
            if bounds is None:
                bounds = [list(position["min"]), list(position["max"])]
            else:
                bounds[0] = [min(a, b) for a, b in zip(bounds[0], position["min"])]
                bounds[1] = [max(a, b) for a, b in zip(bounds[1], position["max"])]
            sets = [k for k in primitive["attributes"] if k.startswith("TEXCOORD_")]
            if sets != ["TEXCOORD_0"]:
                errors.append(f"UV sets {sets}")

    if tris > budget["max_tris"]:
        errors.append(f"{tris} tris over {budget['max_tris']}")
    if tris != entry["tris"]:
        errors.append(f"{tris} tris differs from the authored {entry['tris']}; the gate altered the mesh")
    materials = len(doc.get("materials", []))
    if materials > budget["max_materials"]:
        errors.append(f"{materials} materials over {budget['max_materials']}")
    if any(material.get("doubleSided") for material in doc.get("materials", [])):
        errors.append("double-sided material")

    for image in doc.get("images", []):
        view = doc["bufferViews"][image["bufferView"]]
        size = png_size(binary[view.get("byteOffset", 0):view.get("byteOffset", 0) + 24])
        if max(size) > budget["tex_size"]:
            errors.append(f"texture {size} over {budget['tex_size']}")

    if bounds:
        low, high = bounds
        if abs(low[1]) > EPS:
            errors.append(f"bottom at y={low[1]:.4f}, expected 0")
        if abs(low[0] + high[0]) / 2 > EPS or abs(low[2] + high[2]) / 2 > EPS:
            errors.append("pivot is not at the bounding box's bottom-centre")

    nodes = doc["nodes"]
    children = {child for node in nodes for child in node.get("children", [])}
    for i, node in enumerate(nodes):
        if i in children:
            continue
        if any(abs(c) > EPS for c in node.get("translation", (0, 0, 0))):
            errors.append(f"root node {node.get('name')} is offset {node['translation']}")
        scale = node.get("scale", (1, 1, 1))
        if any(not math.isclose(c, 1, abs_tol=EPS) for c in scale):
            errors.append(f"root node {node.get('name')} has scale {scale}")

    skins = doc.get("skins", [])
    bones = max((len(skin["joints"]) for skin in skins), default=0)
    if bones > budget["max_bones"]:
        errors.append(f"{bones} bones over {budget['max_bones']}")
    if path.name.startswith("SK_"):
        if not skins:
            errors.append("skeletal asset has no skin")
        _check_clips(doc, binary, clips, errors)
        _check_socket_bones(doc, errors)
    elif skins or doc.get("animations"):
        errors.append("static asset has a skin or animation")
    return tris, bones, path.stat().st_size, errors


def main():
    directory = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "assets/models/production"
    budgets = load_budgets()
    manifest = json.loads(MANIFEST.read_text())
    expected = {}
    for base, asset in manifest["assets"].items():
        for quality, variant in asset["variants"].items():
            expected[f"{base}_{quality}.glb"] = variant

    on_disk = {path.name for path in directory.glob("*.glb")}
    failures = []
    for name in sorted(on_disk - set(expected)):
        failures.append(f"{name}: not in the manifest")
    for name in sorted(set(expected) - on_disk):
        failures.append(f"{name}: missing from {directory}")

    totals = {"HQ": 0, "LQ": 0}
    print(f"{'asset':38}{'tier':17}{'tris':>11}{'bones':>7}{'KB':>7}")
    for name in sorted(on_disk & set(expected)):
        entry = expected[name]
        budget = budgets[entry["tier"]]
        try:
            tris, bones, size, errors = check_file(directory / name, entry, budget, manifest["clips"])
        except (ValueError, KeyError, struct.error) as error:
            failures.append(f"{name}: unreadable: {error}")
            continue
        totals["HQ" if "_HQ." in name else "LQ"] += size
        print(f"{name[:-4]:38}{entry['tier']:17}{f'{tris}/' + str(budget['max_tris']):>11}{bones:>7}{size / 1024:>7.0f}")
        failures += [f"{name}: {error}" for error in errors]

    print(f"\nTotal: HQ {totals['HQ'] / 1048576:.2f} MB, LQ {totals['LQ'] / 1048576:.2f} MB, {len(on_disk)} files")
    if failures:
        print(f"\nFAILED ({len(failures)}):")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
