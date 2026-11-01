"""Art review helpers. Nothing here exports: lay assets out in one scene and look at them."""
import bpy

import catalog
import kit


def lay_out(entries, gap=4.0, columns=99):
    """entries: names or (name, faction). Clears the scene and places them in rows. Returns tri counts."""
    kit.clear_scene()
    x = y = depth = 0.0
    counts = {}
    for i, entry in enumerate(entries):
        name, faction = entry if isinstance(entry, tuple) else (entry, None)
        hq = name.endswith("_HQ")
        mb, _, _ = catalog.build(name)
        base = name.rpartition("_")[0]
        chosen = faction or catalog.DEFAULT_FACTIONS.get(base, kit.palette.DEFAULT_FACTION)
        material = kit.palette_material(hq, chosen)
        obj = mb.to_object(f"{name}.{faction or ''}", material)
        xs = [v.x for v in mb.verts]
        ys = [v.y for v in mb.verts]
        width = max(xs) - min(xs)
        if i and i % columns == 0:
            x = 0.0
            y += depth + gap
            depth = 0.0
        obj.location = (x + width / 2, y, 0)
        x += width + gap
        depth = max(depth, max(ys) - min(ys))
        counts[name] = mb.tris
    return counts
