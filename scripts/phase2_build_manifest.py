"""Build manifest of accessible records → output filename for Phase 2 scrape."""
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KEEPERS = REPO / "scripts" / "phase1_keepers.json"
MANIFEST = REPO / "scripts" / "phase2_manifest.json"

INACCESSIBLE = {
    "1uID4CZ-UprerYgFWZbloNGw1E9hIxgtYuF_OlMFygWw",  # ITC AC CR
    "1cUY15EMf8UaVCXP2sH-y3u3lnmPqeJvPXnZntPizQ2A",  # ClearLeaf
    "1Yrs_dWDjfT7j8rYUKT_4OoeOskgqQZVIRBbZN90ihNw",  # Rockefeller 03.04
}


def slugify(s: str) -> str:
    s = s.lower()
    # Strip date prefix like "04.06.2026."
    s = re.sub(r"^\s*\d{1,2}\.\d{1,2}(\.\d{2,4})?\.?\s*", "", s)
    # Replace non-alphanum with -
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:60]


keepers = json.loads(KEEPERS.read_text(encoding="utf-8"))
manifest = []
for k in keepers:
    if k["drive_id"] in INACCESSIBLE:
        continue
    slug_part = slugify(k["name"]) or "untitled"
    filename = f"{k['fecha']}-{slug_part}.txt"
    manifest.append({
        "airtable_id": k["airtable_id"],
        "airtable_name": k["name"],
        "fecha": k["fecha"],
        "drive_id": k["drive_id"],
        "transcript_doc_url": k["transcript_doc_url"],
        "output_filename": filename,
        "has_granola_too": k["has_granola_too"],
    })

# Detect collisions
filenames = [m["output_filename"] for m in manifest]
dupes = [f for f in filenames if filenames.count(f) > 1]
if dupes:
    print(f"WARNING: duplicate filenames: {set(dupes)}")

MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote manifest with {len(manifest)} entries to {MANIFEST}")
