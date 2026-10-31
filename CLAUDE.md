## 3D Art & Blender MCP Rules
- **Never export directly from Blender to `assets/models/production/`.**
- Whenever creating, importing (via Hyper3D/Rodin/PolyHaven), or modifying a 3D mesh in Blender, you MUST delegate final optimization, UV unwrapping, pivot normalization, and `.glb` export to the `mobile-asset-optimizer` subagent.
- Naming convention: `SM_<Category>_<Name>.glb` for static meshes (e.g., `SM_Prop_HealthCrate.glb`) and `SK_<Name>.glb` for skeletal meshes.
