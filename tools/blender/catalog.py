"""The asset list, and the entry points used inside Blender.

    prepare("SM_Ship_Sloop_HQ")  empties the scene and builds that one variant, ready for
                                 the mobile-asset-optimizer gate.
    sockets_for(...)             returns its attachment points without touching the scene.
"""
import json

import bpy

import characters
import kit
import palette
import props
import ships

_SHIP = "hero"
_CHAR = "hero"
_PROP = "prop"
_ENV = "environment"


def _ship(name):
    return lambda mb, hq: ships.build_ship(mb, name, hq)


# base name: (tier for HQ, builder or character key)
STATIC = {
    "SM_Ship_Sloop": (_SHIP, _ship("Sloop")),
    "SM_Ship_Brigantine": (_SHIP, _ship("Brigantine")),
    "SM_Ship_Galleon": (_SHIP, _ship("Galleon")),
    "SM_Ship_Propeller": (_PROP, props.propeller),
    "SM_Prop_Cannon": (_PROP, props.cannon),
    "SM_Prop_Cannonball": (_PROP, props.cannonball),
    "SM_Prop_GrapplingHook": (_PROP, props.grappling_hook),
    "SM_Prop_TreasureChest": (_PROP, props.treasure_chest),
    "SM_Prop_TreasureChestOpen": (_PROP, props.treasure_chest_open),
    "SM_Prop_GoldPile": (_PROP, props.gold_pile),
    "SM_Prop_Barrel": (_PROP, props.barrel),
    "SM_Prop_Crate": (_PROP, props.crate),
    "SM_Prop_Cutlass": (_PROP, props.cutlass),
    "SM_Prop_Flintlock": (_PROP, props.flintlock),
    "SM_Prop_BoardingAxe": (_PROP, props.boarding_axe),
    "SM_Prop_RumBottle": (_PROP, props.rum_bottle),
    "SM_Env_BoardingDeck": (_ENV, props.boarding_deck),
    "SM_Env_SkyIsland": (_ENV, props.sky_island),
    "SM_Env_Cloud": (_ENV, props.cloud),
}
SKELETAL = {
    "SK_PirateCaptain": "PirateCaptain",
    "SK_PirateDeckhand": "PirateDeckhand",
    "SK_PirateGunner": "PirateGunner",
    "SK_PirateBrute": "PirateBrute",
}


def all_variants():
    """Every exportable asset: (asset_name, gate_tier)."""
    variants = []
    for base, (tier, _) in STATIC.items():
        variants += [(f"{base}_HQ", tier), (f"{base}_LQ", f"{tier}_low")]
    for base in SKELETAL:
        variants += [(f"{base}_HQ", _CHAR), (f"{base}_LQ", f"{_CHAR}_low")]
    return variants


def _split(asset_name):
    base, _, quality = asset_name.rpartition("_")
    if quality not in ("HQ", "LQ"):
        raise ValueError(f"{asset_name!r} must end in _HQ or _LQ.")
    return base, quality == "HQ"


def _gltf(position):
    """Blender Z-up to the Y-up coordinates the .glb is exported in."""
    return [round(position.x, 4), round(position.z, 4), round(-position.y, 4)]


def build(asset_name):
    """Fills a MeshBuilder. Returns (builder, bone joints or None), recentred on the pivot."""
    base, hq = _split(asset_name)
    mb = kit.MeshBuilder()
    joints = None
    if base in SKELETAL:
        joints = characters.build_character(mb, SKELETAL[base], hq)
    else:
        STATIC[base][1](mb, hq)
    offset = mb.recentre_to_bottom()
    return mb, joints, offset


def prepare(asset_name):
    """Leaves only this asset in the scene. Returns triangle count and sockets for the log."""
    kit.clear_scene()
    _, hq = _split(asset_name)
    mb, joints, offset = build(asset_name)
    obj = mb.to_object(asset_name, kit.palette_material(hq))
    if joints:
        arm = characters.create_armature(asset_name, joints, offset)
        characters.add_clips(arm)
        obj.parent = arm
        modifier = obj.modifiers.new("Armature", "ARMATURE")
        modifier.object = arm
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    return {"asset": asset_name, "tris": mb.tris, "verts": len(mb.verts)}


def sockets_for(asset_name):
    mb, _, _ = build(asset_name)
    return {name: _gltf(p) for name, p in sorted(mb.sockets.items())}


def write_manifest():
    """Writes assets/asset_manifest.json, the data the game loads instead of hard-coding offsets."""
    assets = {}
    for name, tier in all_variants():
        base, hq = _split(name)
        mb, _, _ = build(name)
        asset = assets.setdefault(base, {"variants": {}, "sockets": {}})
        quality = "HQ" if hq else "LQ"
        asset["variants"][quality] = {"tier": tier, "tris": mb.tris}
        asset["sockets"][quality] = {key: _gltf(p) for key, p in sorted(mb.sockets.items())}
    manifest = {
        "units": "metres",
        "coordinates": "glTF: +Y up, +Z is the model's front. Socket positions are relative to the pivot.",
        "clips": characters.clip_table(),
        "fps": characters.FPS,
        "skeleton": list(characters.BONE_PARENTS),
        "held_item_bones": {"weapon.R": ["SM_Prop_Cutlass", "SM_Prop_BoardingAxe"], "gun.R": ["SM_Prop_Flintlock"]},
        "palette_atlases": {
            faction: {"HQ": f"T_Palette_{faction}_HQ.png", "LQ": f"T_Palette_{faction}_LQ.png"}
            for faction in palette.FACTIONS
        },
        "assets": assets,
    }
    path = palette.TEXTURE_DIR.parents[1] / "asset_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    return str(path)


def tri_budget_table():
    """Triangle counts for every variant, without touching the scene."""
    return {name: build(name)[0].tris for name, _ in all_variants()}
