"""Sample a few Meeting Notes records to see what fields are populated."""
import os
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / "keys.env"
for line in env_path.read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

from pyairtable import Api

api = Api(os.environ["AIRTABLE_PAT"])
table = api.table("appVMgNUokH0882lO", "tblK16rZogch6Rq7S")  # Meeting Notes

records = table.all(max_records=5)

out_path = Path(__file__).resolve().parent / "sample_meeting_notes.txt"
lines = [f"Fetched {len(records)} sample records.", ""]

for r in records:
    lines.append(f"--- Record {r['id']} ---")
    fields = r.get("fields", {})
    for key, val in fields.items():
        if isinstance(val, str):
            preview = val.replace("\n", " ")
            preview = (preview[:300] + "...") if len(preview) > 300 else preview
            lines.append(f"  {key:40s} [str, {len(val)} chars]  {preview}")
        elif isinstance(val, list):
            lines.append(f"  {key:40s} [list, {len(val)} items]  {str(val[:2])[:200]}")
        else:
            lines.append(f"  {key:40s} {type(val).__name__}  {val}")
    lines.append("")

out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {out_path}")
