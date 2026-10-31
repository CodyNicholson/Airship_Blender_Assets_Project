---
name: mobile-blender-pipeline
description: Mobile game asset budgets and the deterministic bpy enforcer script (triangle, material, UV, pivot, and bone gates plus GLB export). Use when optimizing or validating a Blender mesh for assets/models/production/.
---

# Mobile Blender Pipeline

`scripts/enforce_mobile_budget.py` runs inside Blender and exposes:

- `optimize_and_validate_asset(asset_name, tier, export_dir, preview_path)`: joins visible meshes, cleans, decimates, snaps the pivot, enforces a single `UVMap`, audits materials and bones, and exports a `.glb` only if every gate passes. Returns a report dict.
- `bake_materials_to_atlas(asset_name, tier)`: merges all materials into one baked albedo atlas. Run it after a material violation, then re-run the optimizer. The existing UVs are kept on that re-run because the material now uses an image texture.

Tiers and limits live in `BUDGET_TIERS` in the script. Final export goes through the `mobile-asset-optimizer` subagent, per `CLAUDE.md`.

The optimizer edits the open scene destructively: every visible mesh is joined into one object and decimation is applied. Keep only the asset being processed visible.
