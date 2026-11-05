#!/usr/bin/env python3
"""One review image per asset: HQ over LQ, each as front / three-quarter / back, plus a mid-walk pose for
rigged characters. Prints triangle counts against the tier budget. Builds from the builders, exports nothing.

    python3 tools/review_sheet.py SK_Ivo SM_Prop_LightningStaff [--out DIR] [--hq-only] [--verbose]

Open the printed sheet path once per iteration; that's the whole review.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from blender_launch import ROOT, ensure_blender, script_args  # noqa: E402

ensure_blender(__file__, tags=("[review]",))

import importlib.util  # noqa: E402

import bpy  # noqa: E402

import catalog  # noqa: E402
import review  # noqa: E402


def budgets():
    script = ROOT / ".claude/skills/mobile-blender-pipeline/scripts/enforce_mobile_budget.py"
    spec = importlib.util.spec_from_file_location("enforce_mobile_budget", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.BUDGET_TIERS


def main():
    args = script_args()
    out = Path(tempfile.gettempdir()) / "asset_review"
    if "--out" in args:
        out = Path(args[args.index("--out") + 1])
        del args[args.index("--out"):args.index("--out") + 2]
    qualities = ("HQ",) if "--hq-only" in args else ("HQ", "LQ")
    bases = [a.rsplit("_", 1)[0] if a.endswith(("_HQ", "_LQ")) else a for a in args if not a.startswith("--")]
    if not bases:
        sys.exit(__doc__)
    tiers = dict(catalog.all_variants())
    limits = budgets()
    for base in dict.fromkeys(bases):
        rows = []
        for quality in qualities:
            name = f"{base}_{quality}"
            if name not in tiers:
                sys.exit(f"[review] unknown asset {name}: add it to catalog.STATIC or story_characters.CAST")
            info = catalog.prepare(name)
            tier = tiers[name]
            cap = limits[tier]["max_tris"]
            flag = "OK" if info["tris"] <= cap else "OVER BUDGET"
            print(f"[review] {name}: {info['tris']} / {cap} tris ({tier}) {flag}")
            scene = bpy.context.scene
            meshes = [o for o in scene.objects if o.type == "MESH"]
            armature = next((o for o in scene.objects if o.type == "ARMATURE"), None)
            rows.append(review.render_row(meshes, armature))
        path = review.write_sheet(rows, out / f"{base}.png")
        print(f"[review] sheet: {path}")


main()
