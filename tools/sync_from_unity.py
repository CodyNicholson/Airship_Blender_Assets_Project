#!/usr/bin/env python3
"""Syncs assets generated or edited in the Unity project back into the Blender assets project.

    python3 tools/sync_from_unity.py [--portraits] [--unity ../Ransom_Skies_Unity_Project]

Copies new or modified character portraits from Unity into assets/textures/production.
"""
import shutil
import sys
from pathlib import Path

BLENDER_ROOT = Path(__file__).resolve().parents[1]


def main():
    args = sys.argv[1:]
    unity = (BLENDER_ROOT / "../Ransom_Skies_Unity_Project").resolve()
    if "--unity" in args:
        unity = Path(args[args.index("--unity") + 1]).resolve()

    unity_portraits = unity / "Assets/Game/Resources/Art/Portraits"
    blender_textures = BLENDER_ROOT / "assets/textures/production"
    blender_textures.mkdir(parents=True, exist_ok=True)

    if not unity_portraits.exists():
        sys.exit(f"[sync_from_unity] Unity portrait folder missing: {unity_portraits}")

    synced = []
    for src in sorted(unity_portraits.glob("T_Portrait_*.png")):
        dst = blender_textures / src.name
        if not dst.exists() or dst.read_bytes() != src.read_bytes():
            shutil.copy2(src, dst)
            synced.append(src.name)
            print(f"[sync_from_unity] updated {src.name} ({src.stat().st_size:,} bytes)")

    if synced:
        print(f"[sync_from_unity] synced {len(synced)} portraits into {blender_textures.relative_to(BLENDER_ROOT)}")
    else:
        print("[sync_from_unity] all portraits already in sync.")


if __name__ == "__main__":
    main()
