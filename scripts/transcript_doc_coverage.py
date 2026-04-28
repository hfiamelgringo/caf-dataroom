"""Audit the 'Transcript (.doc)' column in Airtable Meeting Notes."""
import json
import os
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / "keys.env"
for line in env_path.read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip()

from pyairtable import Api

api = Api(os.environ["AIRTABLE_PAT"])
table = api.table("appVMgNUokH0882lO", "tblK16rZogch6Rq7S")

records = table.all(fields=["Name", "Granola", "Transcript (.doc)", "Fecha", "Project", "Project."])
total = len(records)
with_granola = [r for r in records if r["fields"].get("Granola")]
with_transcript_doc = [r for r in records if r["fields"].get("Transcript (.doc)")]
with_both = [r for r in records if r["fields"].get("Granola") and r["fields"].get("Transcript (.doc)")]
with_only_doc = [r for r in records if r["fields"].get("Transcript (.doc)") and not r["fields"].get("Granola")]

out = [
    f"Total Meeting Notes: {total}",
    f"With Granola URL:           {len(with_granola)} ({100*len(with_granola)/total:.0f}%)",
    f"With Transcript (.doc):     {len(with_transcript_doc)} ({100*len(with_transcript_doc)/total:.0f}%)",
    f"With both:                  {len(with_both)}",
    f"With only Transcript (.doc) (no Granola): {len(with_only_doc)}",
    "",
    "Sample Transcript (.doc) URLs (first 25, sorted by date desc):",
]
sorted_records = sorted(
    with_transcript_doc,
    key=lambda r: r["fields"].get("Fecha", ""),
    reverse=True,
)
for r in sorted_records[:25]:
    f = r["fields"]
    out.append(f"  {f.get('Fecha','?'):10s}  {f.get('Name','')[:55]:55s}  {f.get('Transcript (.doc)')}")

Path(__file__).resolve().parent.joinpath("transcript_doc_coverage.txt").write_text("\n".join(out), encoding="utf-8")
print("Wrote scripts/transcript_doc_coverage.txt")
