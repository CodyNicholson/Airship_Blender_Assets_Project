"""Lets a tools/ script be run with plain `python3`: if bpy isn't available it re-runs itself inside
headless Blender, and keeps only its own tagged output ([review], [gate], ...) plus any errors, so a
run costs a few lines instead of Blender's full log. Pass --verbose to see everything.

    from blender_launch import ensure_blender
    ensure_blender(__file__, tags=("[review]",))   # returns only when already inside Blender
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLENDER = os.environ.get("BLENDER", "/Applications/Blender.app/Contents/MacOS/Blender")
ERROR_MARKS = ("Traceback", "Error", "error:", "Exception")


def in_blender():
    try:
        import bpy  # noqa: F401
        return True
    except ImportError:
        return False


def script_args():
    """The script's own arguments, inside or outside Blender."""
    argv = sys.argv
    return argv[argv.index("--") + 1:] if "--" in argv else argv[1:]


def ensure_blender(script, tags):
    if in_blender():
        sys.path.insert(0, str(ROOT / "tools" / "blender"))
        sys.path.insert(0, str(ROOT / "tools"))
        return
    args = sys.argv[1:]
    verbose = "--verbose" in args
    args = [a for a in args if a != "--verbose"]
    cmd = [BLENDER, "-b", "--factory-startup", "--python", str(Path(script).resolve()), "--", *args]
    proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    in_traceback = False
    for line in proc.stdout:
        keep = verbose or line.startswith(tags) or any(mark in line for mark in ERROR_MARKS)
        # Keep a whole Python traceback once one starts.
        if line.startswith("Traceback"):
            in_traceback = True
        elif in_traceback and not line.startswith((" ", "\t")) and line.strip():
            print(line, end="")
            in_traceback = False
            continue
        if keep or in_traceback:
            print(line, end="")
    sys.exit(proc.wait())
