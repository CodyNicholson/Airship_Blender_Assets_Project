## Git Commit Rules
- **Never include Claude or any other AI agent, software, or model as an author, committer, or co-author on any git commit.**
- Do not add `Co-Authored-By:` trailers, AI attribution lines, or model names (e.g., Claude, Anthropic, OpenAI, Gemini, Copilot, Cursor, etc.) in commit messages or git metadata. All commits must be authored solely by the repository owner (`Cody Nicholson <codynicholson96@gmail.com>`).

## 3D Art & Blender MCP Rules
- **Never export directly from Blender to `assets/models/production/`.**
- Whenever creating, importing (via Hyper3D/Rodin/PolyHaven), or modifying a 3D mesh in Blender, you MUST delegate final optimization, UV unwrapping, pivot normalization, and `.glb` export to the `mobile-asset-optimizer` subagent.
- Naming convention: `SM_<Category>_<Name>.glb` for static meshes (e.g., `SM_Prop_HealthCrate.glb`) and `SK_<Name>.glb` for skeletal meshes.

## Asset reference: read this instead of exploring the code

Every asset is procedural Python in `tools/blender/`, built into a `kit.MeshBuilder` (`mb`) and registered in
`catalog.py`. Don't read whole modules to learn the conventions below; `grep -n "def <helper>"` for the one
helper you need. Unity game project: `../Ransom_Skies_Unity_Project`.

**Space.** Z up, metres. **−Y is the front** (faces, ship bows, the camera side of arenas). A character's **left
is +X**, so "his right arm" is −X / `*.R`. After the gate the pivot is bottom-centre of the bounding box,
so anything that sticks out (a dock, a tail) shifts every socket: environments are positioned in Unity by
their `centre_stage` socket, not the pivot. Unity rotates environments 180°, so Blender +Y is away from the camera.

**Budgets** (`.claude/skills/mobile-blender-pipeline/scripts/enforce_mobile_budget.py`, max triangles HQ / LQ):
hero (characters, ships) 4500 / 1500 · environment 1500 / 600 · prop 800 / 250. One material each.
Finished characters sit at 2200–3900 HQ, 850–1400 LQ. Use `_q(hq, high, low)` / `q[...]` for detail counts.

**Palette** (`palette.py`, `mb.<shape>(..., "swatch")`). Woods `wood_dark|mid|light|deck|red`; metals
`iron iron_light brass gold gold_dark silver steel rust rust_dark` (rust reads as copper); cloth `canvas
canvas_dark leather leather_dark cloth_white|black|blue|green|brown navy enamel velvet parchment rope`; skin
`skin_light|mid|dark`; hair `hair_black|brown|gray|red|blond|white`; misc `glass amber gem_red gem_blue
rock grass cloud storm storm_dark abyss toxic eye_white eye_dark`. **Glowing:** `lamp liftstone ember
lightning plasma wind`. `faction_a|b|c` take the asset's faction atlas (Crimson Azure Emerald Obsidian Gilded
Scrap Syndicate Warden Sorcerer Nomad Bosun Shadow); set the default in `catalog.DEFAULT_FACTIONS`.

**Mesh calls** (`kit.py`): `box(centre, size, c)`, `tube(p0, p1, r0, r1, sides, c, flat=)` (r1=0 is a cone),
`path(points, radii, sides, c)`, `sphere(centre, radii, sides, rings, c, smooth=)`, `lathe([(r, z)...], sides, c)`
(around local Z), `loft(rings, c)`, `plate(outline, thickness, c)`, `socket(name, pos)`,
`with mb.bound_to("bone"):` (skinning), `with mb.xf(Matrix):` (transform).

### Character (`SK_<Name>`, `story_characters.py`)
1. Add `CAST["Name"] = Hero(...)`: `scale width girth arm_bulk leg_bulk skin hair top legs boots belt sleeve
   forearm glove brow (+angry, −worried) iris sclera eye_scale singed_brow mouth features=[("fn", args...)]`.
   Registering in `CAST` makes `SK_<Name>` exist; add `catalog.DEFAULT_FACTIONS["SK_<Name>"]`.
2. Write one `def <name>_<role>(ctx)` feature (see `stormcaller_trainee`, `bosun_build`), add it to `FEATURES`.
   `ctx.mb ctx.s (scale) ctx.w ctx.g (width, girth) ctx.hq ctx.q ctx.hero ctx.joints[bone] -> (head, tail)`.
   Body heights are unscaled metres times `s`: hips 0.8–0.94, spine to 1.08, chest to 1.32, neck to 1.38,
   head centre 1.56 (`_at(ctx, x, y, z)` is head-relative; face plane y ≈ −0.17, head radius ≈ 0.2).
   Reuse: `hair_cap long_coat short_jacket bandolier tool_harness high_collar scarf cape sash goggles_up
   _boot_cuffs`; `copy.copy(ctx)` with bigger `w`/`g` makes oversized clothing.
3. Skeleton (shared, 22 bones): `root hips spine chest neck head upper_arm/lower_arm/hand/weapon/gun.L|R
   thigh/shin/foot.L|R`. Clips (shared): Idle Walk AttackMelee AttackRanged Hit Block Death Victory Run
   Grapple Talk Work Surrender Taunt.
4. Portrait: `portrait_cast.py`, `def <name>(p)` + `CAST["Name"] = _spec(...)`. Paint skin with
   `p.paint.blob/line(x, z...)` **before** `finish()`; +x is the viewer's right (the character's left).
   Clothes are `p.sweep/plate/ball(..., root=p.body_root)` with y ≈ −0.6 to −1.0, z −1.2 to −2.9.

### Prop (`SM_Prop_<Name>`, `story_props.py`)
`def <name>(mb, hq)`, Z up from the base. Held items need `grip` (and `trail_tip`) sockets. Register in
`catalog.STATIC` with `_PROP`, `DEFAULT_FACTIONS`, and `HELD_MELEE` or `HELD_GUNS`. Weapon icons: add
`"Weapon_<Name>": "SM_Prop_<Name>"` to `fx_catalog.MODEL_ICONS` (Unity looks up `Weapon_` + prop name).

### Environment (`SM_Env_<Name>`, `story_env.py`)
`def <name>(mb, hq)`, `_ENV` tier. Keep the camera side (−Y) open; arenas call `_combat_slots(mb, floor)`
(party/enemy slots, `centre_stage`). Hubs keep the `station_<crew>` sockets.

## Workflow: one command per step, one image per review
1. Build, then review: `python3 tools/review_sheet.py SK_Name SM_Prop_X`. Prints tris vs budget and ONE sheet
   per asset (HQ row over LQ row: front, ¾, back, + mid-walk pose for rigs). Open only that sheet, once per iteration.
2. Gate and export: delegate to `mobile-asset-optimizer` (it runs `python3 tools/gate.py <assets…>`).
3. 2D art: `python3 tools/make_art.py icons Weapon_X` · `portraits Name` · `glyphs` · `appicon <dir>`.
4. Manifest: `tools/refresh_manifest.sh` (regenerates, diffs against HEAD, validates production).
5. Unity: `python3 tools/sync_to_unity.py SK_Name SM_Prop_X --textures T_Portrait_Name T_Icon_Weapon_X`
   (copies, bakes prefabs in a clone so the open editor is safe, copies back only the new files). Then point
   the game at it in `Assets/Game/Resources/game_content.json` (`looks`: `asset`, `weaponR`, `faction`).
   A look can change with the story: add a look with `"variantOf": "<base id>", "fromAct": N` (Vane: `vane` Act 0–1,
   `vane_captain` from 2, `vane_king` from 4). `Content.Look(id)` picks the playing mission's act, else the story's progress.
6. Unity tests and builds run in a clone too (the editor is usually open): `Unity -batchmode -projectPath
   <clone> -runTests -testPlatform EditMode` then `-executeMethod Airships.EditorTools.ProjectSetup.BuildApk`;
   install with the SDK's `adb install -r` (`PlaybackEngines/AndroidPlayer/SDK/platform-tools`).

Every named character has a bespoke model. `SK_PirateCaptain/Deckhand/Gunner/Brute` remain only for generic crews and enemies.
