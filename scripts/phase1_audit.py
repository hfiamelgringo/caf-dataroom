"""Phase 1: filter Airtable Meeting Notes to records with Transcript (.doc) URLs,
apply the keep-list filter (drop Internal / Rigo<>Nati / CAF-direct), and emit
both the raw filtered list (for Drive access audit by Claude in this session) and
a coverage summary.
"""
import json
import os
import re
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / "keys.env"
for line in env_path.read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip()

from pyairtable import Api

EXCLUDE_PATTERNS = [
    re.compile(r"\binternal\b", re.I),
    re.compile(r"rigo\s*<>\s*nati", re.I),
    re.compile(r"\bcaf\b", re.I),  # CAF-direct (CABEI passes since substring isn't word-bounded "caf")
]


def should_keep(name: str) -> bool:
    if any(p.search(name) for p in EXCLUDE_PATTERNS):
        return False
    return True


def extract_drive_id(url: str) -> str | None:
    if not url:
        return None
    m = re.search(r"/document/d/([a-zA-Z0-9_-]+)", url)
    if m:
        return m.group(1)
    m = re.search(r"/file/d/([a-zA-Z0-9_-]+)", url)
    if m:
        return m.group(1)
    return None


api = Api(os.environ["AIRTABLE_PAT"])
table = api.table("appVMgNUokH0882lO", "tblK16rZogch6Rq7S")

records = table.all(fields=["Name", "Granola", "Transcript (.doc)", "Fecha"])
total = len(records)

with_doc = [r for r in records if r["fields"].get("Transcript (.doc)")]
keep = []
excluded = []
for r in with_doc:
    name = r["fields"].get("Name", "")
    if not name:
        continue
    if should_keep(name):
        keep.append(r)
    else:
        excluded.append(name)

# Sort by date desc
keep.sort(key=lambda r: r["fields"].get("Fecha", ""), reverse=True)

# Build keeper records with extracted Drive IDs
keeper_records = []
for r in keep:
    f = r["fields"]
    url = f["Transcript (.doc)"]
    drive_id = extract_drive_id(url)
    keeper_records.append({
        "airtable_id": r["id"],
        "name": f.get("Name", ""),
        "fecha": f.get("Fecha", ""),
        "transcript_doc_url": url,
        "drive_id": drive_id,
        "has_granola_too": bool(f.get("Granola")),
    })

out_dir = Path(__file__).resolve().parent
(out_dir / "phase1_keepers.json").write_text(
    json.dumps(keeper_records, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

summary = [
    f"Total Meeting Notes: {total}",
    f"With Transcript (.doc): {len(with_doc)}",
    f"  Excluded by name filter: {len(excluded)}",
    f"  Kept (stakeholder interviews): {len(keeper_records)}",
    f"  Of those, also have Granola: {sum(1 for k in keeper_records if k['has_granola_too'])}",
    "",
    "Excluded titles:",
]
for n in excluded:
    summary.append(f"  - {n}")
summary.append("")
summary.append("Kept titles (sorted by date desc):")
for k in keeper_records:
    drive_marker = "?" if not k["drive_id"] else "✓"
    summary.append(f"  {k['fecha']:10s}  [{drive_marker}]  {k['name']}")

(out_dir / "phase1_summary.txt").write_text("\n".join(summary), encoding="utf-8")
print(f"Kept: {len(keeper_records)} records")
print(f"Wrote {out_dir / 'phase1_keepers.json'}")
print(f"Wrote {out_dir / 'phase1_summary.txt'}")
