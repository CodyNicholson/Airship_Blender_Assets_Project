"""What the effects, skies and icons are, as plain data. Imports nothing, so catalog.write_manifest
can publish it and the validator can check it against the files on disk."""

# Atlas layouts, by quality: (grid, cell pixels).
LAYOUTS = {
    "loop": {"HQ": (4, 128), "LQ": (4, 64)},  # 16 frames, seamless.
    "shot": {"HQ": (6, 128), "LQ": (4, 64)},  # One-shots with a long life: LQ plays fewer frames.
    "burst": {"HQ": (4, 128), "LQ": (4, 64)},  # Short one-shots.
    "flash": {"HQ": (2, 128), "LQ": (2, 64)},  # A few frames at most: muzzle flashes, lightning.
    "tile": {"HQ": (1, 256), "LQ": (1, 128)},  # Single wrapping texture.
    "dot": {"HQ": (1, 64), "LQ": (1, 32)},  # Single small sprite.
}

# name: layout, fps, loop, blend, anchor (u, v of the emitter within a frame, v up).
# "premultiplied" keeps smoke solid over bright skies. "additive" is for pure light.
# Colour runs under every transparent pixel, so premultiplying on import can't fringe.
FLIPBOOKS = {
    "Fire": ("loop", 16, True, "premultiplied", (0.5, 0.06)),
    "SmokeDark": ("burst", 12, False, "premultiplied", (0.5, 0.5)),
    "SmokeLight": ("burst", 16, False, "premultiplied", (0.5, 0.5)),
    "GasLeak": ("burst", 16, False, "premultiplied", (0.5, 0.5)),
    "ToxicSmog": ("burst", 8, False, "premultiplied", (0.5, 0.5)),
    "Explosion": ("shot", 24, False, "premultiplied", (0.5, 0.5)),
    "FlakBurst": ("burst", 20, False, "premultiplied", (0.5, 0.5)),
    "MuzzleFlash": ("flash", 30, False, "additive", (0.5, 0.5)),
    "Sparks": ("burst", 30, False, "additive", (0.5, 0.5)),
    "AfterburnerPlume": ("loop", 24, True, "additive", (0.5, 0.06)),
    "LiftBurst": ("burst", 24, False, "additive", (0.5, 0.5)),
    "Shockwave": ("burst", 30, False, "additive", (0.5, 0.5)),
    "LightningFlash": ("flash", 24, False, "additive", (0.5, 0.5)),
    "SlashArc": ("burst", 40, False, "additive", (0.5, 0.5)),
    "Rain": ("tile", 0, True, "additive", (0.5, 0.5)),
    "Ember": ("dot", 0, False, "additive", (0.5, 0.5)),
}

# Ready-made emitters. Sockets are shell-style globs, tried in order: the first that matches anything
# on an asset wins, and every match gets an emitter, so older ships fall back to what they do have.
# NON_SOCKET_ANCHORS are positions your game supplies at runtime, not sockets on a model.
# depth_test False is for sockets inside a hull, like lift_core: tested normally, the hull hides them.
# rate is particles per second (0 = a single burst of `burst`). max_particles caps it per emitter,
# per quality. fallback_mesh is the alpha-free model to use when a device can't afford overdraw.
NON_SOCKET_ANCHORS = ("hit_point", "camera")
PRESETS = {
    "HullFire": {"flipbook": "Fire", "sockets": ["fire_*", "deck_centre"], "size_m": 2.4, "lifetime_s": 1.0, "rate": 3, "max_particles": {"HQ": 4, "LQ": 1}, "velocity_mps": [0, 0.3, 0], "fallback_mesh": "SM_VFX_Flame", "used_for": "Burning decks: Prologue mutiny, Fire-shot hits, Act IV corvette"},
    "DamageSmoke": {"flipbook": "SmokeDark", "sockets": ["smoke_vent"], "size_m": 4.0, "lifetime_s": 2.6, "rate": 3, "max_particles": {"HQ": 8, "LQ": 3}, "velocity_mps": [0, 2.4, 0], "fallback_mesh": "SM_VFX_SmokePuff", "used_for": "Ship below half hull; the wake of the falling Sovereign Gale"},
    "CannonFire": {"flipbook": "MuzzleFlash", "sockets": ["muzzle*", "siege_muzzle", "harpoon_muzzle"], "size_m": 1.8, "lifetime_s": 0.13, "rate": 0, "burst": 1, "max_particles": {"HQ": 1, "LQ": 1}, "velocity_mps": [0, 0, 0], "follow_up": "CannonSmoke", "used_for": "Every broadside shot"},
    "CannonSmoke": {"flipbook": "SmokeLight", "sockets": ["muzzle*", "siege_muzzle", "harpoon_muzzle"], "size_m": 1.8, "lifetime_s": 1.0, "rate": 0, "burst": 1, "max_particles": {"HQ": 2, "LQ": 1}, "velocity_mps": [0, 0.6, 0], "used_for": "Lingers after a muzzle flash"},
    "EnvelopeHit": {"flipbook": "GasLeak", "sockets": ["envelope_centre"], "size_m": 3.2, "lifetime_s": 1.0, "rate": 5, "max_particles": {"HQ": 5, "LQ": 2}, "velocity_mps": [0, 1.4, 0], "used_for": "Leaking Lift-Gas, including the Rust-Wing in Act I. Offset to the hit point"},
    "HullImpact": {"flipbook": "Sparks", "sockets": ["hit_point"], "size_m": 2.0, "lifetime_s": 0.5, "rate": 0, "burst": 1, "max_particles": {"HQ": 2, "LQ": 1}, "velocity_mps": [0, 0, 0], "used_for": "Cannonball hits. hit_point comes from your collision, not a socket"},
    "ShipExplosion": {"depth_test": False, "flipbook": "Explosion", "sockets": ["lift_core", "deck_centre"], "size_m": 14.0, "lifetime_s": 1.5, "rate": 0, "burst": 1, "max_particles": {"HQ": 3, "LQ": 1}, "velocity_mps": [0, 0.8, 0], "fallback_mesh": "SM_VFX_Fireball", "follow_up": "ShipShockwave", "used_for": "Ship destroyed. Spawn SM_Prop_WreckChunk debris with it. Scale size_m with hull length"},
    "ShipShockwave": {"depth_test": False, "flipbook": "Shockwave", "sockets": ["lift_core", "deck_centre"], "size_m": 26.0, "lifetime_s": 0.53, "rate": 0, "burst": 1, "max_particles": {"HQ": 1, "LQ": 0}, "velocity_mps": [0, 0, 0], "fallback_mesh": "SM_VFX_ShockRing", "used_for": "Ring that follows a ship explosion"},
    "FlakBurst": {"flipbook": "FlakBurst", "sockets": ["hit_point"], "size_m": 3.5, "lifetime_s": 0.8, "rate": 0, "burst": 1, "max_particles": {"HQ": 6, "LQ": 3}, "velocity_mps": [0, 0, 0], "used_for": "Rook's heavy flak, and bursts clearing Assault Gliders"},
    "MortarImpact": {"flipbook": "Explosion", "sockets": ["hit_point"], "size_m": 6.0, "lifetime_s": 1.0, "rate": 0, "burst": 1, "max_particles": {"HQ": 2, "LQ": 1}, "velocity_mps": [0, 0.5, 0], "fallback_mesh": "SM_VFX_Fireball", "used_for": "Act III mortar and siege shells, Sable's charges"},
    "LiftCoreSabotage": {"depth_test": False, "flipbook": "LiftBurst", "sockets": ["lift_core", "charge_slot", "glow"], "size_m": 7.0, "lifetime_s": 0.67, "rate": 2, "max_particles": {"HQ": 3, "LQ": 1}, "velocity_mps": [0, 0, 0], "used_for": "Morrow's sabotage, Thorne's Overdrive, Sable's charges counting down"},
    "AfterburnerBoost": {"flipbook": "AfterburnerPlume", "sockets": ["afterburner_*", "exhaust"], "size_m": 4.0, "lifetime_s": 0.67, "rate": 0, "burst": 1, "max_particles": {"HQ": 1, "LQ": 1}, "velocity_mps": [0, 0, 0], "fallback_mesh": "SM_VFX_Plume", "attached": True, "used_for": "The Mirage's boost. Stays attached and aims along the ship's +Y exhaust axis"},
    "EngineExhaust": {"flipbook": "SmokeLight", "sockets": ["propeller_*"], "size_m": 1.4, "lifetime_s": 1.0, "rate": 2, "max_particles": {"HQ": 3, "LQ": 0}, "velocity_mps": [0, 0.3, -2], "used_for": "Engine trails at high throttle"},
    "ThrusterTrail": {"flipbook": "Fire", "sockets": ["thruster"], "size_m": 1.1, "lifetime_s": 1.0, "rate": 0, "burst": 1, "max_particles": {"HQ": 1, "LQ": 1}, "velocity_mps": [0, 0, 0], "attached": True, "used_for": "Assault Gliders diving at your deck"},
    "SmogVent": {"flipbook": "ToxicSmog", "sockets": ["smog_*", "centre"], "size_m": 9.0, "lifetime_s": 2.0, "rate": 1, "max_particles": {"HQ": 6, "LQ": 2}, "velocity_mps": [0.4, 1.2, 0], "used_for": "Scrap-Winds stacks on SM_Env_ScrapIsle, and the edge of SM_Env_ToxicCloud"},
    "LightningStrike": {"flipbook": "LightningFlash", "sockets": ["lightning_?", "lightning_strike_*", "strike"], "size_m": 30.0, "lifetime_s": 0.17, "rate": 0, "burst": 1, "max_particles": {"HQ": 2, "LQ": 1}, "velocity_mps": [0, 0, 0], "follow_up": "HullImpact", "used_for": "Flash with SM_Env_LightningBolt in Act IV, and on StormCloud sockets"},
    "MeleeSlash": {"flipbook": "SlashArc", "sockets": ["trail_tip"], "size_m": 1.8, "lifetime_s": 0.4, "rate": 0, "burst": 1, "max_particles": {"HQ": 1, "LQ": 1}, "velocity_mps": [0, 0, 0], "used_for": "AttackMelee, timed to frames 9-14. Faces the camera"},
    "BladeClash": {"flipbook": "Sparks", "sockets": ["trail_tip", "centre_stage"], "size_m": 1.1, "lifetime_s": 0.5, "rate": 0, "burst": 1, "max_particles": {"HQ": 2, "LQ": 1}, "velocity_mps": [0, 0, 0], "used_for": "Block, and duels in the arenas"},
    "WinchSparks": {"flipbook": "Sparks", "sockets": ["winch", "hook_tether_*", "rope"], "size_m": 1.6, "lifetime_s": 0.5, "rate": 6, "max_particles": {"HQ": 4, "LQ": 1}, "velocity_mps": [0, 0, 0], "used_for": "Krag's winch reeling you in"},
    "EmberDrift": {"flipbook": "Ember", "sockets": ["fire_*", "rupture_*", "fire"], "size_m": 0.22, "lifetime_s": 2.2, "rate": 7, "max_particles": {"HQ": 14, "LQ": 0}, "velocity_mps": [0, 1.6, 0], "used_for": "Drifts off every fire; rupture sockets in the Lift-Core chamber"},
    "RainSheet": {"flipbook": "Rain", "sockets": ["camera"], "size_m": 0, "lifetime_s": 0, "rate": 0, "max_particles": {"HQ": 1, "LQ": 1}, "velocity_mps": [0, 0, 0], "used_for": "Full-screen quad, scrolled down, over Act IV and the upper-deck brawl"},
}

# Sky panoramas: equirectangular, +Y at the top, wrap horizontally. glTF axes for directions.
# sun_dir points towards the sun; use it with the colours below so ships match their sky.
SKY_SIZES = {"HQ": (2048, 1024), "LQ": (1024, 512)}
SKIES = {
    "CloudBreak": {"used_for": "Prologue: the taste of power, at sunrise", "sun_dir": [0.55, 0.38, 0.74], "sun_color": [1.0, 0.86, 0.62], "sun_intensity": 2.6, "ambient_color": [0.62, 0.68, 0.82], "fog_color": [0.96, 0.76, 0.58], "fog_start_m": 180, "fog_end_m": 700},
    "ScrapWinds": {"used_for": "Act I: hunted in the toxic junk-clouds", "sun_dir": [-0.35, 0.72, 0.6], "sun_color": [0.95, 0.9, 0.62], "sun_intensity": 1.5, "ambient_color": [0.58, 0.6, 0.42], "fog_color": [0.56, 0.56, 0.34], "fog_start_m": 70, "fog_end_m": 320},
    "Jetstream": {"used_for": "Act II: fast, bright, high-altitude intrigue", "sun_dir": [0.3, 0.82, -0.48], "sun_color": [1.0, 0.98, 0.9], "sun_intensity": 2.8, "ambient_color": [0.6, 0.76, 0.96], "fog_color": [0.62, 0.83, 0.96], "fog_start_m": 220, "fog_end_m": 900},
    "CirrusCitadel": {"used_for": "Act III: cold moonlit approach to Tartarus Aloft", "sun_dir": [-0.5, 0.62, 0.6], "sun_color": [0.72, 0.8, 1.0], "sun_intensity": 1.3, "ambient_color": [0.3, 0.32, 0.52], "fog_color": [0.2, 0.2, 0.38], "fog_start_m": 130, "fog_end_m": 560},
    "Maelstrom": {"used_for": "Act IV: inside the hyper-storm's eye", "sun_dir": [0.0, 1.0, 0.0], "sun_color": [0.66, 0.68, 0.96], "sun_intensity": 1.1, "ambient_color": [0.27, 0.25, 0.4], "fog_color": [0.11, 0.1, 0.2], "fog_start_m": 90, "fog_end_m": 420},
    "HangarDusk": {"used_for": "Hub: warm, safe evening in the crew's hangar", "sun_dir": [-0.72, 0.16, 0.67], "sun_color": [1.0, 0.66, 0.42], "sun_intensity": 2.1, "ambient_color": [0.62, 0.46, 0.6], "fog_color": [0.86, 0.48, 0.42], "fog_start_m": 150, "fog_end_m": 620},
    "FreeDawn": {"used_for": "Ending: the storm breaks after Cassian's defeat", "sun_dir": [0.6, 0.24, -0.76], "sun_color": [1.0, 0.92, 0.78], "sun_intensity": 2.5, "ambient_color": [0.68, 0.72, 0.86], "fog_color": [1.0, 0.86, 0.74], "fog_start_m": 240, "fog_end_m": 1000},
}

ICON_SIZES = {"HQ": 256, "LQ": 128}

# Icons rendered from the real models: icon name: model base name.
MODEL_ICONS = {
    "Ship_SovereignGale": "SM_Ship_SovereignGale",
    "Ship_RustWing": "SM_Ship_RustWing",
    "Ship_IronMaw": "SM_Ship_IronMaw",
    "Ship_Mirage": "SM_Ship_Mirage",
    "Ship_Bastion": "SM_Ship_Bastion",
    "Ship_TartarusAloft": "SM_Ship_TartarusAloft",
    "Ship_ArmadaCorvette": "SM_Ship_ArmadaCorvette",
    "Ship_ArmadaFrigate": "SM_Ship_ArmadaFrigate",
    "Ship_ScrapRaider": "SM_Ship_ScrapRaider",
    "Ship_SmugglerRunner": "SM_Ship_SmugglerRunner",
    "Ship_AssaultGlider": "SM_Ship_AssaultGlider",
    "Ship_Lifeboat": "SM_Ship_Lifeboat",
    "Item_Gold": "SM_Prop_GoldPile",
    "Item_Scrap": "SM_Prop_ScrapPile",
    "Item_LiftStone": "SM_Prop_LiftStone",
    "Item_CipherKey": "SM_Prop_CipherKey",
    "Item_Treasure": "SM_Prop_TreasureChestOpen",
    "Item_RepairKit": "SM_Prop_RepairKit",
    "Item_WeaponModule": "SM_Prop_WeaponModule",
    "Item_Rum": "SM_Prop_RumBottle",
    "Item_SaboteurCharge": "SM_Prop_SaboteurCharge",
    "Ammo_Round": "SM_Prop_Cannonball",
    "Ammo_ChainShot": "SM_Prop_ChainShot",
    "Ammo_FireShot": "SM_Prop_FireShot",
    "Ammo_Grapeshot": "SM_Prop_Grapeshot",
    "Ammo_MortarShell": "SM_Prop_MortarShell",
    "Ammo_Harpoon": "SM_Prop_Harpoon",
    "Ammo_Missile": "SM_Prop_Missile",
    "Module_HarpoonWinch": "SM_Prop_HarpoonWinch",
    "Module_Afterburner": "SM_Prop_AfterburnerTurbine",
    "Module_DeckMortar": "SM_Prop_DeckMortar",
    "Module_SiegeCannon": "SM_Prop_SiegeCannon",
    "Module_FlakGun": "SM_Prop_FlakGun",
    "Module_LiftCore": "SM_Prop_LiftCore",
    "Weapon_HookSabre": "SM_Prop_HookSabre",
    "Weapon_RoyalSabre": "SM_Prop_RoyalSabre",
    "Weapon_DuelPistol": "SM_Prop_DuelPistol",
    "Weapon_AnchorHammer": "SM_Prop_AnchorHammer",
    "Weapon_TwinScimitar": "SM_Prop_TwinScimitar",
    "Weapon_WardenFlail": "SM_Prop_WardenFlail",
    "Weapon_HandMortar": "SM_Prop_HandMortar",
    "Weapon_SableDagger": "SM_Prop_SableDagger",
    "Weapon_BigWrench": "SM_Prop_BigWrench",
    "Weapon_Halberd": "SM_Prop_ArmadaHalberd",
    "Weapon_Musket": "SM_Prop_ArmadaMusket",
    "Weapon_Cutlass": "SM_Prop_Cutlass",
    # The Davy Jones' Choice: real models on a gold medal, so the choice reads as the object you win.
    "Choice_SeizeHelm": "SM_Prop_HelmWheel",
    "Choice_ScuttlePlunder": "SM_Prop_TreasureChestOpen",
}

# Icons drawn as vector glyphs, grouped by how the game uses them.
GLYPH_ICONS = (
    "Hud_FireBroadside", "Hud_Grapple", "Hud_Board", "Hud_Defend", "Hud_Repair",
    "Hud_AltitudeUp", "Hud_AltitudeDown", "Hud_ThrottleUp", "Hud_ThrottleDown",
    "Hud_Hull", "Hud_Crew", "Hud_Comms", "Hud_Timer", "Hud_Map", "Hud_Pause", "Hud_Settings", "Hud_Close", "Hud_Back", "Hud_Locked",
    "Target_Engine", "Target_Guns", "Target_Sails", "Target_Envelope", "Target_LiftCore", "Target_Reticle",
    "Marker_WeakPoint", "Marker_Objective", "Marker_Waypoint", "Marker_EnemyFleet",
    "Hazard_Lightning", "Hazard_Updraft", "Hazard_ToxicCloud", "Hazard_WindCurrent",
    "Story_Surrender", "Story_Bounty", "Story_Nemesis", "Story_Loyalty",
    "Choice_PressGang",
    "Ability_RookPrecision", "Ability_LyraWinds", "Ability_LyraCloudStealth", "Ability_SableSabotage", "Ability_ThorneOverdrive", "Ability_ThornePatch", "Ability_MorrowRadar",
    # The deck battle's round attack button and one button per crew skill.
    "Hud_Attack",
    "Skill_Cleave", "Skill_CrushingBlow", "Skill_HookSwing", "Skill_AimedShot", "Skill_CinderFlame", "Skill_HeavyFlak",
    "Skill_LightningBolt", "Skill_Squall", "Skill_Tailwind", "Skill_Backstab", "Skill_SmokeBomb", "Skill_SetCharge",
    "Skill_DarkMending", "Skill_VeilOfLife", "Skill_RaiseTheFallen", "Skill_Scattershot", "Skill_MarkWeakPoint",
    "Skill_BelayingPin", "Skill_QuickDraw", "Skill_PatchUp", "Skill_Rally", "Skill_SmellingSalts", "Skill_StaticSnare",
)
