"""One-off cleanup: remove specified interview slugs from index.json + filesystem."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPTS = ROOT / "content_data" / "transcripts"
INDEX = TRANSCRIPTS / "index.json"

REMOVE = {
    "2026-02-12-louis-prouvost-level-up",
    "2026-01-14-lyana-latorre-rockfound",
    "2026-01-14-rockefeller-foundation-latam",
    "2026-02-11-rockefeller",
    "2026-02-13-ady-beitler-nilus",
}

# 1. Filter index.json
data = json.loads(INDEX.read_text(encoding="utf-8"))
before = len(data)
data = [e for e in data if e.get("name") not in REMOVE]
after = len(data)
INDEX.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"index.json: {before} → {after} entries (removed {before - after})")

# 2. Delete the .md files
for slug in REMOVE:
    p = TRANSCRIPTS / f"{slug}.md"
    if p.exists():
        p.unlink()
        print(f"  deleted {p.name}")
    else:
        print(f"  (already gone) {p.name}")
