import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
data = json.loads((REPO / "audit" / "pass1_findings.json").read_text(encoding="utf-8"))

for slug, entry in data.items():
    if "_parse_error" in entry:
        continue
    for f in entry.get("findings", []):
        if f.get("severity") == "sharp":
            print(f"--- {slug}")
            print(f"target: {f.get('target_name')}  ({f.get('target_type')})")
            print(f"category: {f.get('category')}  is_caf: {f.get('is_caf')}")
            print(f"quote: {f.get('quote')}")
            print()
