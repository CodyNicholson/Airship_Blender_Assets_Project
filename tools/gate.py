#!/usr/bin/env python3
"""The mobile asset gate, headless, for any number of assets in one run. For each HQ and LQ variant:
build it alone in a clean scene, check nothing else is visible, run the deterministic budget enforcer
(which exports to assets/models/production only if every gate passes), retry once after an atlas bake on
a material violation, then render ONE review sheet per asset of what was exported (rest views plus a
mid-walk pose for rigged assets). Prints only the gate blocks and the sheet path.

    python3 tools/gate.py SK_Ivo SM_Prop_LightningStaff [--verbose]

The caller still opens each sheet and fills in the Visual Check: a defect there fails the gate even
though the enforcer passed (delete that .glb and report it).
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from blender_launch import ROOT, ensure_blender, script_args  # noqa: E402

ensure_blender(__file__, tags=("[gate]",))

import importlib.util  # noqa: E402

import bpy  # noqa: E402

import catalog  # noqa: E402
import review  # noqa: E402

EXPORT_DIR = "assets/models/production"


def enforcer():
    script = ROOT / ".claude/skills/mobile-blender-pipeline/scripts/enforce_mobile_budget.py"
    spec = importlib.util.spec_from_file_location("enforce_mobile_budget", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def gate_variant(emb, name, tier):
    catalog.prepare(name)
    scene = bpy.context.scene
    visible = [o for o in scene.objects if o.type == "MESH" and o.visible_get()]
    if len(visible) != 1:
        return {"passed": False, "violations": [f"scene holds {len(visible)} visible meshes, expected 1: {[o.name for o in visible]}"]}, None
    report = emb.optimize_and_validate_asset(asset_name=name, tier=tier, export_dir=EXPORT_DIR)
    if not report["passed"] and any("material" in v.lower() for v in report["violations"]):
        print(f"[gate] {name}: material violation, baking an atlas and retrying")
        emb.bake_materials_to_atlas(name, tier=tier)
        report = emb.optimize_and_validate_asset(asset_name=name, tier=tier, export_dir=EXPORT_DIR)
    meshes = [o for o in scene.objects if o.type == "MESH"]
    armature = next((o for o in scene.objects if o.type == "ARMATURE"), None)
    row = review.render_row(meshes, armature) if meshes else None
    return report, row


def print_block(name, tier, report):
    status = "PASS" if report.get("passed") else "FAIL"
    print(f"[gate] [MOBILE ASSET GATE: {status}]")
    print(f"[gate] - Asset: {name}.glb (Tier: {tier})")
    if "initial_tris" in report:
        print(f"[gate] - Triangles: {report['initial_tris']} -> {report['final_tris']} / {report['max_tris']}")
        print(f"[gate] - Materials: {report.get('materials_count')}  UV maps: {report.get('uv_layers')}  Bones: {report.get('bones')}")
    for violation in report.get("violations") or []:
        print(f"[gate] - Violation: {violation}")
    print(f"[gate] - Output Path: {report.get('export_path') or 'BLOCKED'}")


def main():
    bases = [a.rsplit("_", 1)[0] if a.endswith(("_HQ", "_LQ")) else a for a in script_args() if not a.startswith("--")]
    if not bases:
        sys.exit(__doc__)
    emb = enforcer()
    tiers = dict(catalog.all_variants())
    out = Path(tempfile.gettempdir()) / "asset_gate"
    for base in dict.fromkeys(bases):
        rows = []
        for quality in ("HQ", "LQ"):
            name = f"{base}_{quality}"
            if name not in tiers:
                print(f"[gate] unknown asset {name}: not in the catalog")
                continue
            report, row = gate_variant(emb, name, tiers[name])
            print_block(name, tiers[name], report)
            if row:
                rows.append(row)
        if rows:
            print(f"[gate] Sheet: {review.write_sheet(rows, out / f'{base}.png')}")


main()
