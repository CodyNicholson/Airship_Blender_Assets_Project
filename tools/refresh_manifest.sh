#!/bin/zsh
# Regenerates assets/asset_manifest.json from the builders, validates production, and prints a short diff
# against the last commit: which assets were added, removed or changed, and which other sections moved.
#   tools/refresh_manifest.sh
set -e
ROOT="${0:A:h:h}"
BLENDER="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
cd "$ROOT"
"$BLENDER" -b --factory-startup --python-expr "import sys; sys.path.insert(0, 'tools/blender'); import catalog; print('[manifest] wrote', catalog.write_manifest())" 2>&1 | grep -E "^\[manifest\]|Traceback|Error" || true
python3 - <<'EOF'
import json, subprocess
try:
    before = json.loads(subprocess.run(["git", "show", "HEAD:assets/asset_manifest.json"], capture_output=True, text=True, check=True).stdout)
except subprocess.CalledProcessError:
    before = {"assets": {}}
after = json.load(open("assets/asset_manifest.json"))
a, b = before.get("assets", {}), after["assets"]
print("[manifest] assets added:", sorted(set(b) - set(a)) or "none")
print("[manifest] assets removed:", sorted(set(a) - set(b)) or "none")
print("[manifest] assets changed:", [k for k in a if k in b and a[k] != b[k]] or "none")
moved = [k for k in after if k != "assets" and before.get(k) != after[k]]
print("[manifest] other sections changed:", moved or "none")
EOF
python3 tools/validate_production.py 2>&1 | tail -1
