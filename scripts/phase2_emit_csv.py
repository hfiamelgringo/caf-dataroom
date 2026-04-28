"""Emit a CSV of the 42 Drive transcript URLs that need to be downloaded."""
import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "scripts" / "phase2_manifest.json"
OUT = REPO / "scripts" / "phase2_urls_to_download.csv"

manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

with OUT.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["fecha", "airtable_name", "drive_id", "transcript_doc_url", "export_url", "save_as_filename"])
    for m in manifest:
        export_url = f"https://docs.google.com/document/d/{m['drive_id']}/export?format=txt"
        w.writerow([m["fecha"], m["airtable_name"], m["drive_id"], m["transcript_doc_url"], export_url, m["output_filename"]])

print(f"Wrote {OUT} ({len(manifest)} rows)")
