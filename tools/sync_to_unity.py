#!/usr/bin/env python3
"""Hands finished assets to the Unity project, safely even while its editor is open.

    python3 tools/sync_to_unity.py SK_Ivo SM_Prop_LightningStaff --textures T_Portrait_Ivo T_Icon_Weapon_LightningStaff
        [--unity ../Ransom_Skies_Unity_Project] [--keep-clone]

1. Copies <asset>_HQ/_LQ.glb, each texture's _HQ/_LQ.png and asset_manifest.json into the Unity project.
2. Bakes prefabs in a copy-on-write clone of the project (Airships/Import Art Kit, batch mode), so the open
   editor is never touched.
3. Copies back only what the bake made for these assets: each .glb's .meta, each prefab and its .meta,
   each new texture's .meta, and art_data.json if it changed. The prefabs reference the clone's .meta
   GUIDs, so those always travel together.
Then it lists what changed in the Unity project.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BLENDER_ROOT = Path(__file__).resolve().parents[1]
TEXTURE_DIRS = {
    "T_Portrait_": "Resources/Art/Portraits",
    "T_Icon_": "Resources/Art/Icons",
    "T_Sky_": "Resources/Art/Sky",
    "T_VFX_": "Resources/Art/Vfx",
    "T_Palette_": "Resources/Art/Textures",
    "T_Emissive": "Resources/Art/Textures",
}


def fail(message):
    sys.exit(f"[sync] {message}")


def texture_dir(name):
    for prefix, folder in TEXTURE_DIRS.items():
        if name.startswith(prefix):
            return folder
    fail(f"don't know where {name} goes in Unity; add its prefix to TEXTURE_DIRS")


def unity_binary(unity):
    version = re.search(r"m_EditorVersion:\s*(\S+)", (unity / "ProjectSettings/ProjectVersion.txt").read_text()).group(1)
    path = Path(f"/Applications/Unity/Hub/Editor/{version}/Unity.app/Contents/MacOS/Unity")
    if not path.exists():
        fail(f"Unity {version} isn't installed at {path}")
    return path


def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main():
    args = sys.argv[1:]
    unity = (BLENDER_ROOT / "../Ransom_Skies_Unity_Project").resolve()
    if "--unity" in args:
        unity = Path(args[args.index("--unity") + 1]).resolve()
        del args[args.index("--unity"):args.index("--unity") + 2]
    keep = "--keep-clone" in args
    textures = []
    if "--textures" in args:
        at = args.index("--textures")
        textures = [a for a in args[at + 1:] if not a.startswith("--")]
        args = args[:at]
    assets = [a for a in args if not a.startswith("--")]
    if not assets and not textures:
        sys.exit(__doc__)

    production = BLENDER_ROOT / "assets"
    game = unity / "Assets/Game"
    files = []  # (source in Blender, destination in Unity)
    for asset in assets:
        for quality in ("HQ", "LQ"):
            glb = production / f"models/production/{asset}_{quality}.glb"
            if not glb.exists():
                fail(f"{glb.name} isn't exported yet: run tools/gate.py {asset}")
            files.append((glb, game / f"Art/Kit/Models/{glb.name}"))
    for texture in textures:
        for quality in ("HQ", "LQ"):
            png = production / f"textures/production/{texture}_{quality}.png"
            if not png.exists():
                fail(f"{png.name} doesn't exist: run tools/make_art.py")
            files.append((png, game / texture_dir(texture) / png.name))
    files.append((production / "asset_manifest.json", game / "Art/Kit/asset_manifest.json"))
    for src, dst in files:
        copy(src, dst)
    print(f"[sync] copied {len(files)} files into {unity.name}")

    # Bake in a clone. cp -c makes copy-on-write clones on APFS, so Library costs no disk.
    clone = Path(tempfile.mkdtemp(prefix="unity_sync_"))
    for part in ("Assets", "Packages", "ProjectSettings", "Library"):
        subprocess.run(["cp", "-c", "-R", str(unity / part), str(clone / part)], check=True)
    log = clone / "import.log"
    subprocess.run([str(unity_binary(unity)), "-batchmode", "-quit", "-projectPath", str(clone),
                    "-executeMethod", "Airships.EditorTools.ArtKitImport.ImportAll", "-logFile", str(log)], check=False)
    baked = re.findall(r"\[Art\] Baked .*", log.read_text(errors="ignore"))
    if not baked:
        fail(f"the import didn't finish; see {log} (kept)")
    print(f"[sync] {baked[-1]}")

    clone_game = clone / "Assets/Game"
    back = []
    for asset in assets:
        for quality in ("HQ", "LQ"):
            back += [f"Art/Kit/Models/{asset}_{quality}.glb.meta", f"Resources/Art/{asset}_{quality}.prefab", f"Resources/Art/{asset}_{quality}.prefab.meta"]
    for texture in textures:
        for quality in ("HQ", "LQ"):
            back.append(f"{texture_dir(texture)}/{texture}_{quality}.png.meta")
    back.append("Resources/Art/art_data.json")
    for rel in back:
        src, dst = clone_game / rel, game / rel
        if not src.exists():
            fail(f"the bake didn't produce {rel}")
        if dst.exists() and dst.read_bytes() == src.read_bytes():
            continue
        if rel.endswith(".glb.meta") and dst.exists():
            print(f"[sync] note: the open editor had already made {dst.name}; replacing it with the baked one so the prefab's GUID matches")
        copy(src, dst)
        print(f"[sync] updated {rel}")

    if keep:
        print(f"[sync] clone kept at {clone}")
    else:
        shutil.rmtree(clone)
    status = subprocess.run(["git", "status", "--short", "--", "Assets/Game"], cwd=unity, capture_output=True, text=True).stdout
    print("[sync] Unity changes:\n" + (status or "  none"))


main()
