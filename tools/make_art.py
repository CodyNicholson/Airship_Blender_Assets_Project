#!/usr/bin/env python3
"""2D art from the builders, written straight to assets/textures/production (no mesh gate: nothing exported
is a mesh). Prints the files written.

    python3 tools/make_art.py icons Weapon_LightningStaff Ship_Mirage   # model icons named in fx_catalog.MODEL_ICONS
    python3 tools/make_art.py glyphs                                    # every glyph icon (HUD, skills, abilities)
    python3 tools/make_art.py portraits Ivo Hask                        # portrait_cast.CAST names
    python3 tools/make_art.py appicon <out_dir>                         # the app icon layers (fx_appicon)
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from blender_launch import ensure_blender, script_args  # noqa: E402

ensure_blender(__file__, tags=("[art]",))


def main():
    args = script_args()
    if not args:
        sys.exit(__doc__)
    kind, names = args[0], [a for a in args[1:] if not a.startswith("--")]
    if kind == "icons":
        import fx_catalog
        import fx_icons
        unknown = [n for n in names if n not in fx_catalog.MODEL_ICONS]
        if unknown or not names:
            sys.exit(f"[art] add these to fx_catalog.MODEL_ICONS first: {unknown or 'no names given'}")
        written = fx_icons.generate_model_icons(tempfile.mkdtemp(prefix="icons_"), names)
    elif kind == "glyphs":
        import fx_icons
        written = fx_icons.generate_glyphs()
    elif kind == "portraits":
        import portraits
        written = portraits.render_all(names or None)
    elif kind == "appicon":
        import fx_appicon
        written = fx_appicon.generate(names[0] if names else ".")
    else:
        sys.exit(__doc__)
    for path in written or []:
        print(f"[art] wrote {path}")
    if not written:
        print("[art] done")


main()
