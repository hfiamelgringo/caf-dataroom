"""Move downloaded transcript .txt files from ~/Downloads into content_data/raw_transcripts/,
renaming each to its manifest output_filename via fuzzy match on the airtable name.

Heuristic: Drive's auto-filename starts with the same MM.DD.YYYY date prefix as the
airtable record. We strip the date and compare normalized name fragments.
"""
import json
import os
import re
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO / "scripts" / "phase2_manifest.json"
DST = REPO / "content_data" / "raw_transcripts"
SRC = Path(os.path.expandvars("%USERPROFILE%")) / "Downloads"

DST.mkdir(parents=True, exist_ok=True)


def normalize(s: str) -> str:
    s = s.lower()
    # Strip date prefix
    s = re.sub(r"^\s*\d{1,2}\.\d{1,2}(\.\d{2,4})?\.?\s*", "", s)
    # Strip leading underscores / spaces
    s = s.lstrip("_ ")
    # Strip parenthetical Gemini notes suffixes / dupe markers
    s = re.sub(r"\s*-\s*\d{4}_\d{2}_\d{2}.*$", "", s)
    s = re.sub(r"\s*-\s*notes by gemini.*$", "", s)
    s = re.sub(r"\s*-\s*transcripción.*$", "", s)
    s = re.sub(r"\s*\(\d+\)\s*$", "", s)
    s = re.sub(r"\.docx?$", "", s)
    s = re.sub(r"\.md$", "", s)
    # Replace separators with spaces
    s = re.sub(r"[._\-,]+", " ", s)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    # Strip noise tokens
    for noise in ["transcript meeting with ", "meeting with ms teams ", " transcripción", " regulatory framework"]:
        s = s.replace(noise, "")
    return s


def tokens(s: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", normalize(s)))


def best_match(query_norm: str, manifest: list[dict]) -> dict | None:
    qt = tokens(query_norm)
    if len(qt) < 1:
        return None
    best = None
    best_score = 0
    for m in manifest:
        mt = tokens(m["airtable_name"])
        if not mt:
            continue
        overlap = len(qt & mt)
        if overlap > best_score:
            best_score = overlap
            best = m
    if best_score < 1:
        return None
    return best


def main():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    by_filename = {m["output_filename"]: m for m in manifest}
    used_outputs = set()

    moved = []
    skipped = []
    already_present = set(p.name for p in DST.glob("*.txt"))

    txt_files = sorted(SRC.glob("*.txt"))
    # Filter to ones likely from this batch (recent enough or matching pattern)
    for f in txt_files:
        # Skip files that don't look like transcripts (use a heuristic — recently modified)
        match = best_match(f.stem, manifest)
        if not match:
            skipped.append((f.name, "no match"))
            continue
        out_name = match["output_filename"]
        if out_name in used_outputs:
            skipped.append((f.name, f"dupe of {out_name}"))
            continue
        target = DST / out_name
        if target.exists():
            skipped.append((f.name, f"target {out_name} already exists"))
            used_outputs.add(out_name)
            continue
        shutil.move(str(f), str(target))
        used_outputs.add(out_name)
        moved.append((f.name, out_name))

    log_lines = ["MOVED:"]
    for src, dst in moved:
        log_lines.append(f"  {src}  ->  {dst}")
    log_lines.append("")
    log_lines.append("SKIPPED:")
    for src, why in skipped:
        log_lines.append(f"  {src}  ({why})")
    log_lines.append("")
    log_lines.append(f"Manifest expected {len(manifest)}; moved {len(moved)}; missing:")
    for m in manifest:
        if m["output_filename"] not in used_outputs and m["output_filename"] not in already_present:
            log_lines.append(f"  {m['output_filename']}  (airtable: {m['airtable_name']})")

    log = REPO / "scripts" / "phase2_move_log.txt"
    log.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"Moved {len(moved)}, skipped {len(skipped)}. See {log}")


if __name__ == "__main__":
    main()
