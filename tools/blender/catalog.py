"""The asset list, and the entry points used inside Blender.

    prepare("SM_Ship_Sloop_HQ")  empties the scene and builds that one variant, ready for
                                 the mobile-asset-optimizer gate.
    sockets_for(...)             returns its attachment points without touching the scene.
"""
import json

import bpy

import characters
import cinder
import fleet_ships
import fx_catalog
import kit
import palette
import props
import ships
import story_characters
import story_env
import story_props
import story_ships
import story_vfx

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
    # Shattered Skies campaign.
    "SM_Ship_SovereignGale": (_SHIP, story_ships.sovereign_gale),
    "SM_Ship_SovereignGaleWrecked": (_SHIP, story_ships.sovereign_gale_wrecked),
    "SM_Ship_RustWing": (_SHIP, story_ships.rust_wing),
    "SM_Ship_IronMaw": (_SHIP, story_ships.iron_maw),
    "SM_Ship_Mirage": (_SHIP, story_ships.mirage),
    "SM_Ship_Bastion": (_SHIP, story_ships.bastion),
    "SM_Ship_TartarusAloft": (_SHIP, story_ships.tartarus_aloft),
    "SM_Ship_ArmadaCorvette": (_SHIP, story_ships.armada_corvette),
    "SM_Ship_ArmadaFrigate": (_SHIP, story_ships.armada_frigate),
    "SM_Ship_ScrapRaider": (_SHIP, story_ships.scrap_raider),
    "SM_Ship_SmugglerRunner": (_SHIP, story_ships.smuggler_runner),
    "SM_Ship_AssaultGlider": (_SHIP, story_ships.assault_glider),
    "SM_Ship_Lifeboat": (_SHIP, story_ships.lifeboat),
    # Expanded 30-ship airship fleet (elemental, sci-fi, modern battleship, fantastical, outlaw).
    **{name: (_SHIP, fn) for name, fn in fleet_ships.FLEET_SHIPS.items()},
    # Alpha-free effects for devices that can't afford transparent overdraw.
    "SM_VFX_Flame": (_PROP, story_vfx.flame),
    "SM_VFX_Fireball": (_PROP, story_vfx.fireball),
    "SM_VFX_SmokePuff": (_PROP, story_vfx.smoke_puff),
    "SM_VFX_ShockRing": (_PROP, story_vfx.shock_ring),
    "SM_VFX_Plume": (_PROP, story_vfx.plume),
    "SM_Prop_HarpoonWinch": (_PROP, story_props.harpoon_winch),
    "SM_Prop_Harpoon": (_PROP, story_props.harpoon),
    "SM_Prop_KragAnchor": (_PROP, story_props.krag_anchor),
    "SM_Prop_AfterburnerTurbine": (_PROP, story_props.afterburner_turbine),
    "SM_Prop_DeckMortar": (_PROP, story_props.deck_mortar),
    "SM_Prop_SiegeCannon": (_PROP, story_props.siege_cannon),
    "SM_Prop_FlakGun": (_PROP, story_props.flak_gun),
    "SM_Prop_Missile": (_PROP, story_props.missile),
    "SM_Prop_LiftCore": (_PROP, story_props.lift_core),
    "SM_Prop_LiftStone": (_PROP, story_props.lift_stone),
    "SM_Prop_ChainShot": (_PROP, story_props.ammo_chain_shot),
    "SM_Prop_FireShot": (_PROP, story_props.ammo_fire_shot),
    "SM_Prop_Grapeshot": (_PROP, story_props.ammo_grapeshot),
    "SM_Prop_MortarShell": (_PROP, story_props.ammo_mortar_shell),
    "SM_Prop_ScrapPile": (_PROP, story_props.scrap_pile),
    "SM_Prop_WeaponModule": (_PROP, story_props.weapon_module),
    "SM_Prop_CipherKey": (_PROP, story_props.cipher_key),
    "SM_Prop_SaboteurCharge": (_PROP, story_props.saboteur_charge),
    "SM_Prop_RepairKit": (_PROP, story_props.repair_kit),
    "SM_Prop_HelmWheel": (_PROP, story_props.helm_wheel),
    "SM_Prop_AetherComm": (_PROP, story_props.aether_comm),
    "SM_Prop_BountyBoard": (_PROP, story_props.bounty_board),
    "SM_Prop_SkyChartTable": (_PROP, story_props.sky_chart_table),
    "SM_Prop_WinchControls": (_PROP, story_props.winch_controls),
    "SM_Prop_CellDoor": (_PROP, story_props.cell_door),
    "SM_Prop_ArmadaBanner": (_PROP, story_props.armada_banner),
    "SM_Prop_HangingLantern": (_PROP, story_props.hanging_lantern),
    "SM_Prop_RopeCoil": (_PROP, story_props.rope_coil),
    "SM_Prop_WreckChunk": (_PROP, story_props.wreck_chunk),
    "SM_Prop_HookSabre": (_PROP, story_props.boarding_hook_sabre),
    "SM_Prop_RoyalSabre": (_PROP, story_props.royal_sabre),
    "SM_Prop_DuelPistol": (_PROP, story_props.duel_pistol),
    "SM_Prop_AnchorHammer": (_PROP, story_props.anchor_hammer),
    "SM_Prop_TwinScimitar": (_PROP, story_props.twin_scimitar),
    "SM_Prop_CorsairLance": (_PROP, story_props.corsair_lance),
    "SM_Prop_Chainsaw": (_PROP, story_props.chainsaw),
    "SM_Prop_PoisonFlask": (_PROP, story_props.poison_flask),
    "SM_Prop_WardenFlail": (_PROP, story_props.warden_flail),
    "SM_Prop_HandMortar": (_PROP, story_props.hand_mortar),
    "SM_Prop_SableDagger": (_PROP, story_props.sable_dagger),
    "SM_Prop_Spyglass": (_PROP, story_props.spyglass),
    "SM_Prop_BigWrench": (_PROP, story_props.big_wrench),
    "SM_Prop_ShadowStaff": (_PROP, story_props.shadow_staff),
    "SM_Prop_ShadowSpear": (_PROP, story_props.shadow_spear),
    "SM_Prop_GatlingGun": (_PROP, story_props.gatling_gun),
    "SM_Prop_GatlingBarrels": (_PROP, story_props.gatling_barrels),
    "SM_Prop_Bomb": (_PROP, story_props.bomb),
    "SM_Prop_WindBlade": (_PROP, story_props.wind_blade),
    "SM_Prop_MusicNote": (_PROP, story_props.music_note),
    "SM_Prop_Tornado": (_PROP, story_props.tornado),
    "SM_Prop_SableBow": (_PROP, story_props.sable_bow),
    "SM_Prop_PoisonArrow": (_PROP, story_props.poison_arrow),
    "SM_Prop_Fireball": (_PROP, story_props.fireball),
    "SM_Prop_TrapDoor": (_PROP, story_props.trap_door),
    "SM_Prop_TrapDoorLid": (_PROP, story_props.trap_door_lid),
    "SM_Prop_LightningStaff": (_PROP, story_props.lightning_staff),
    "SM_Prop_Linstock": (_PROP, story_props.linstock),
    "SM_Prop_BoneSaw": (_PROP, story_props.bone_saw),
    "SM_Prop_ScrapCutlass": (_PROP, story_props.scrap_cutlass),
    "SM_Prop_CaptainCutlass": (_PROP, story_props.captain_cutlass),
    "SM_Prop_KingCutlass": (_PROP, story_props.king_cutlass),
    "SM_Prop_SwordCane": (_PROP, story_props.sword_cane),
    "SM_Prop_GildedRapier": (_PROP, story_props.gilded_rapier),
    "SM_Prop_FleetCutlass": (_PROP, story_props.fleet_cutlass),
    "SM_Prop_Blunderbuss": (_PROP, story_props.blunderbuss),
    "SM_Prop_RegulatorKey": (_PROP, story_props.regulator_key),
    "SM_Prop_WeatherStaff": (_PROP, story_props.weather_staff),
    "SM_Prop_DriftwoodLyre": (_PROP, story_props.driftwood_lyre),
    "SM_Prop_ArmadaHalberd": (_PROP, story_props.armada_halberd),
    "SM_Prop_ArmadaMusket": (_PROP, story_props.armada_musket),
    "SM_Env_SkyVault": (_ENV, story_env.sky_vault),
    "SM_Env_ScrapIsle": (_ENV, story_env.scrap_isle),
    "SM_Env_LiftMine": (_ENV, story_env.lift_mine),
    "SM_Env_SmugglersHaven": (_ENV, story_env.smugglers_haven),
    "SM_Env_FreeHaven": (_ENV, story_env.free_haven),
    "SM_Env_ToxicCloud": (_ENV, story_env.toxic_cloud),
    "SM_Env_StormCloud": (_ENV, story_env.storm_cloud),
    "SM_Env_StormWall": (_ENV, story_env.storm_wall),
    "SM_Env_LightningBolt": (_ENV, story_env.lightning_bolt),
    "SM_Env_UpdraftColumn": (_ENV, story_env.updraft_column),
    "SM_Env_WindCurrent": (_ENV, story_env.wind_current),
    "SM_Env_UndertowDisc": (_ENV, story_env.undertow_disc),
    "SM_Env_DebrisField": (_ENV, story_env.debris_field),
    "SM_Env_ScrapDeck": (_ENV, story_env.scrap_deck),
    "SM_Env_GaleQuarterdeck": (_ENV, story_env.gale_quarterdeck),
    "SM_Env_HangarHub": (_ENV, story_env.hangar_hub),
    "SM_Env_DreadnoughtDeck": (_ENV, story_env.dreadnought_deck),
    "SM_Env_GunDeck": (_ENV, story_env.gun_deck),
    "SM_Env_CellBlock": (_ENV, story_env.cell_block),
    "SM_Env_WarRoom": (_ENV, story_env.war_room),
    "SM_Env_LiftCoreChamber": (_ENV, story_env.lift_core_chamber),
}
SKELETAL = {
    "SK_PirateCaptain": "PirateCaptain",
    "SK_PirateDeckhand": "PirateDeckhand",
    "SK_PirateGunner": "PirateGunner",
    "SK_PirateBrute": "PirateBrute",
}
# Shattered Skies cast: built by story_characters, same skeleton and clips as the base crew.
STORY_CAST = {f"SK_{name}": name for name in story_characters.CAST}
SKELETAL.update(STORY_CAST)

# The atlas each campaign asset embeds, so it looks right on import. The game can still swap at runtime.
DEFAULT_FACTIONS = {
    "SK_Morrow": "Emerald",
    "SK_Thorne": "Sorcerer",
    "SK_Lyra": "Nomad",
    "SK_Brill": "Bosun",
    "SK_Ivo": "Azure",
    "SK_Hask": "Crimson",
    "SK_Wren": "Emerald",
    "SK_Vane": "Crimson",
    "SK_VaneCaptain": "Crimson",
    "SK_VaneKing": "Crimson",
    "SK_Gorse": "Scrap",
    "SK_Ashgrave": "Syndicate",
    "SK_Thrace": "Emerald",
    "SK_Ria": "Crimson",
    "SK_Mirren": "Crimson",
    "SK_Odessa": "Emerald",
    "SK_Tobin": "Azure",
    "SK_Hale": "Gilded",
    "SK_Sable": "Shadow",
    "SK_SkeletonPirate": "Sorcerer",
    "SK_RookBombSuit": "Crimson",
    "SK_SableHooded": "Shadow",
    "SM_Prop_SableDagger": "Shadow",
    "SM_Prop_ShadowStaff": "Sorcerer",
    "SM_Prop_ShadowSpear": "Sorcerer",
    "SM_Prop_GatlingGun": "Crimson",
    "SM_Prop_GatlingBarrels": "Crimson",
    "SM_Prop_Bomb": "Crimson",
    "SM_Prop_WindBlade": "Nomad",
    "SM_Prop_MusicNote": "Nomad",
    "SM_Prop_Tornado": "Nomad",
    "SM_Prop_SableBow": "Shadow",
    "SM_Prop_PoisonArrow": "Shadow",
    "SM_Prop_Fireball": "Azure",
    "SM_Prop_TrapDoor": "Emerald",
    "SM_Prop_TrapDoorLid": "Emerald",
    "SM_Prop_LightningStaff": "Azure",
    "SM_Prop_Linstock": "Crimson",
    "SM_Prop_BoneSaw": "Emerald",
    "SM_Prop_ScrapCutlass": "Crimson",
    "SM_Prop_CaptainCutlass": "Crimson",
    "SM_Prop_KingCutlass": "Crimson",
    "SM_Prop_SwordCane": "Syndicate",
    "SM_Prop_GildedRapier": "Emerald",
    "SM_Prop_FleetCutlass": "Crimson",
    "SM_Prop_Blunderbuss": "Crimson",
    "SM_Prop_RegulatorKey": "Emerald",
    "SM_Prop_WeatherStaff": "Azure",
    "SM_Ship_RustWing": "Scrap",
    "SM_Ship_IronMaw": "Scrap",
    "SM_Ship_ScrapRaider": "Scrap",
    "SM_Ship_Mirage": "Syndicate",
    "SM_Ship_SmugglerRunner": "Syndicate",
    "SM_Ship_Bastion": "Warden",
    "SM_Ship_TartarusAloft": "Warden",
    "SM_Ship_ArmadaCorvette": "Gilded",
    "SM_Ship_ArmadaFrigate": "Gilded",
    "SM_Ship_AssaultGlider": "Gilded",
    "SM_Prop_SiegeCannon": "Gilded",
    "SM_Prop_Missile": "Gilded",
    "SM_Prop_ArmadaBanner": "Gilded",
    "SM_Prop_ArmadaHalberd": "Gilded",
    "SM_Prop_TwinScimitar": "Syndicate",
    "SM_Prop_CipherKey": "Syndicate",
    "SM_Env_SkyVault": "Gilded",
    "SM_Env_SmugglersHaven": "Syndicate",
    "SM_Env_DreadnoughtDeck": "Gilded",
    "SM_Env_CellBlock": "Warden",
    "SM_Env_WarRoom": "Gilded",
    "SM_Env_LiftCoreChamber": "Gilded",
    "SM_Env_ScrapDeck": "Scrap",
    "SK_ArmadaSoldier": "Gilded",
    "SK_ArmadaOfficer": "Gilded",
    "SK_RoyalGuard": "Gilded",
    "SK_CassianAdmiral": "Gilded",
    "SK_Krag": "Scrap",
    "SK_Vex": "Syndicate",
    "SK_Vesper": "Syndicate",
    "SK_Roxanne": "Syndicate",
    "SK_May": "Gilded",
    "SK_Gimble": "Scrap",
    "SM_Prop_CorsairLance": "Syndicate",
    "SM_Prop_Chainsaw": "Emerald",
    "SM_Prop_PoisonFlask": "Emerald",
    "SK_Malakor": "Warden",
    **fleet_ships.FLEET_FACTIONS,
}


HELD_MELEE = ["SM_Prop_Cutlass", "SM_Prop_BoardingAxe", "SM_Prop_HookSabre", "SM_Prop_RoyalSabre", "SM_Prop_AnchorHammer", "SM_Prop_TwinScimitar", "SM_Prop_CorsairLance", "SM_Prop_Chainsaw", "SM_Prop_WardenFlail", "SM_Prop_SableDagger", "SM_Prop_Spyglass", "SM_Prop_BigWrench", "SM_Prop_ArmadaHalberd", "SM_Prop_ShadowStaff", "SM_Prop_DriftwoodLyre", "SM_Prop_LightningStaff", "SM_Prop_Linstock", "SM_Prop_BoneSaw", "SM_Prop_ScrapCutlass", "SM_Prop_CaptainCutlass", "SM_Prop_KingCutlass", "SM_Prop_SwordCane", "SM_Prop_GildedRapier", "SM_Prop_FleetCutlass", "SM_Prop_RegulatorKey", "SM_Prop_WeatherStaff", "SM_Prop_Bomb"]
HELD_GUNS = ["SM_Prop_Flintlock", "SM_Prop_DuelPistol", "SM_Prop_HandMortar", "SM_Prop_ArmadaMusket", "SM_Prop_Blunderbuss", "SM_Prop_GatlingGun"]


def all_variants():
    """Every exportable asset: (asset_name, gate_tier)."""
    variants = []
    for base, (tier, _) in STATIC.items():
        variants += [(f"{base}_HQ", tier), (f"{base}_LQ", f"{tier}_low")]
    for base in SKELETAL:
        variants += [(f"{base}_HQ", _CHAR), (f"{base}_LQ", f"{_CHAR}_low")]
    variants += [(f"{cinder.ASSET}_HQ", _CHAR), (f"{cinder.ASSET}_LQ", f"{_CHAR}_low")]
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
    if base == cinder.ASSET:
        joints = cinder.build(mb, hq)
    elif base in STORY_CAST:
        joints = story_characters.build(mb, STORY_CAST[base], hq)
    elif base in SKELETAL:
        joints = characters.build_character(mb, SKELETAL[base], hq)
    else:
        STATIC[base][1](mb, hq)
    offset = mb.recentre_to_bottom()
    return mb, joints, offset


def prepare(asset_name):
    """Leaves only this asset in the scene. Returns triangle count and sockets for the log."""
    kit.clear_scene()
    base, hq = _split(asset_name)
    mb, joints, offset = build(asset_name)
    faction = DEFAULT_FACTIONS.get(base, palette.DEFAULT_FACTION)
    obj = mb.to_object(asset_name, kit.palette_material(hq, faction))
    if joints:
        if base == cinder.ASSET:
            arm = characters.create_armature(asset_name, joints, offset, cinder.BONE_PARENTS)
            characters.add_clips(arm, cinder.CLIPS, cinder.BONE_PARENTS)
        else:
            arm = characters.create_armature(asset_name, joints, offset)
            extra = story_characters.EXTRA_CLIPS.get(STORY_CAST.get(base), {})
            characters.add_clips(arm, {**characters.CLIPS, **extra})
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


def _effects_table():
    table = {}
    for name, (layout, fps, loop, blend, anchor) in fx_catalog.FLIPBOOKS.items():
        entry = {"fps": fps, "loop": loop, "blend": blend, "anchor": list(anchor), "variants": {}}
        for quality, (columns, cell) in fx_catalog.LAYOUTS[layout].items():
            entry["variants"][quality] = {"file": f"T_VFX_{name}_{quality}.png", "columns": columns, "rows": columns, "frames": columns * columns, "size": columns * cell}
        table[name] = entry
    return table


def _skies_table():
    return {
        name: {**sky, "variants": {q: {"file": f"T_Sky_{name}_{q}.png", "width": w, "height": h} for q, (w, h) in fx_catalog.SKY_SIZES.items()}}
        for name, sky in fx_catalog.SKIES.items()
    }


def _icons_table():
    sources = dict(fx_catalog.MODEL_ICONS)
    sources.update({name: None for name in fx_catalog.GLYPH_ICONS})
    return {
        name: {"source_model": base, "variants": {q: {"file": f"T_Icon_{name}_{q}.png", "size": size} for q, size in fx_catalog.ICON_SIZES.items()}}
        for name, base in sorted(sources.items())
    }


def write_manifest():
    """Writes assets/asset_manifest.json, the data the game loads instead of hard-coding offsets."""
    assets = {}
    for name, tier in all_variants():
        base, hq = _split(name)
        mb, _, _ = build(name)
        asset = assets.setdefault(base, {"variants": {}, "sockets": {}})
        if base in DEFAULT_FACTIONS:
            asset["default_faction"] = DEFAULT_FACTIONS[base]
        quality = "HQ" if hq else "LQ"
        asset["variants"][quality] = {"tier": tier, "tris": mb.tris}
        if base == cinder.ASSET:
            # Not the crew's skeleton: its own bones and clips.
            asset["variants"][quality]["clips"] = characters.clip_table(cinder.CLIPS)
            asset["skeleton"] = list(cinder.BONE_PARENTS)
        if STORY_CAST.get(base) in story_characters.EXTRA_CLIPS:
            # The crew's clips, plus a few of their own.
            asset["extra_clips"] = characters.clip_table(story_characters.EXTRA_CLIPS[STORY_CAST[base]])
        asset["sockets"][quality] = {key: _gltf(p) for key, p in sorted(mb.sockets.items())}
    manifest = {
        "units": "metres",
        "coordinates": "glTF: +Y up, +Z is the model's front. Socket positions are relative to the pivot.",
        "clips": characters.clip_table(),
        "fps": characters.FPS,
        "skeleton": list(characters.BONE_PARENTS),
        "held_item_bones": {"weapon.R": HELD_MELEE, "weapon.L": HELD_MELEE, "gun.R": HELD_GUNS, "gun.L": HELD_GUNS},
        "palette_atlases": {
            faction: {"HQ": f"T_Palette_{faction}_HQ.png", "LQ": f"T_Palette_{faction}_LQ.png"}
            for faction in palette.FACTIONS
        },
        "emissive_atlas": {"HQ": "T_Emissive_HQ.png", "LQ": "T_Emissive_LQ.png"},
        "effects": _effects_table(),
        "effect_presets": fx_catalog.PRESETS,
        "skies": _skies_table(),
        "icons": _icons_table(),
        "assets": assets,
    }
    path = palette.TEXTURE_DIR.parents[1] / "asset_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    return str(path)


def gate_batch(names, gate):
    """For the mobile-asset-optimizer: prepares each asset, then runs it through the budget gate
    (the enforce_mobile_budget module, passed in). Returns one compact report per asset."""
    tiers = dict(all_variants())
    reports = []
    for name in names:
        prepare(name)
        report = gate.optimize_and_validate_asset(asset_name=name, tier=tiers[name], export_dir="assets/models/production")
        reports.append({key: report[key] for key in ("asset", "tier", "passed", "initial_tris", "final_tris", "max_tris", "materials_count", "uv_layers", "bones", "violations", "export_path")})
    return reports


def tri_budget_table():
    """Triangle counts for every variant, without touching the scene."""
    return {name: build(name)[0].tris for name, _ in all_variants()}
