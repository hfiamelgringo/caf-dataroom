"""Count Meeting Notes records that have a Granola URL."""
import os
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / "keys.env"
for line in env_path.read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

from pyairtable import Api

api = Api(os.environ["AIRTABLE_PAT"])
table = api.table("appVMgNUokH0882lO", "tblK16rZogch6Rq7S")

records = table.all(fields=["Name", "Granola", "Fecha", "Project", "Project.", "Meeting Notes", "Notes"])
total = len(records)
with_granola = [r for r in records if r["fields"].get("Granola")]
with_summary = [r for r in records if r["fields"].get("Meeting Notes") or r["fields"].get("Notes")]

out = [
    f"Total Meeting Notes records: {total}",
    f"With Granola URL:           {len(with_granola)} ({100*len(with_granola)/total:.0f}%)",
    f"With Meeting Notes/Notes:   {len(with_summary)} ({100*len(with_summary)/total:.0f}%)",
    "",
    "All Granola URLs (sorted by date desc):",
]
sorted_records = sorted(
    with_granola,
    key=lambda r: r["fields"].get("Fecha", ""),
    reverse=True,
)
for r in sorted_records:
    f = r["fields"]
    out.append(f"  {f.get('Fecha','?'):10s}  {f.get('Name','')[:55]:55s}  {f.get('Granola')}")

Path(__file__).resolve().parent.joinpath("granola_coverage.txt").write_text("\n".join(out), encoding="utf-8")
print("Wrote granola_coverage.txt")
