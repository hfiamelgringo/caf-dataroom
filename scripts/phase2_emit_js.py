"""Emit a JS array literal for use in the Chrome console: skip docs already saved."""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "scripts" / "phase2_manifest.json"
SAVED_DIR = REPO / "content_data" / "raw_transcripts"

manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
already_saved = {p.name for p in SAVED_DIR.glob("*.txt")}

slim = []
for m in manifest:
    fn = m["output_filename"]
    if fn in already_saved:
        continue
    slim.append({"id": m["drive_id"], "fn": fn})

js_array = json.dumps(slim, ensure_ascii=False)
out = REPO / "scripts" / "phase2_js_payload.js"
out.write_text(f"const MANIFEST = {js_array};\n", encoding="utf-8")
print(f"Emitted {len(slim)} entries (skipped {len(manifest) - len(slim)} already saved)")
print(f"Wrote {out}")
