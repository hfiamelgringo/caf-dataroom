"""Promote content_data/transcripts_v1/ -> content_data/transcripts/ and rebuild index.json."""
import json
import re
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "content_data" / "transcripts_v1"
DST = REPO / "content_data" / "transcripts"
INDEX_OUT = DST / "index.json"

COUNTRY_MAP = {
    "costa rica": "CR", "cr": "CR",
    "honduras": "HN", "hn": "HN",
    "guatemala": "GT", "gt": "GT",
    "dominican republic": "DO", "do": "DO",
    "el salvador": "SV", "sv": "SV",
    "colombia": "Colombia", "colombia (peer model)": "Colombia",
    "mexico": "Mexico", "méxico": "Mexico",
    "brazil": "Brazil", "brasil": "Brazil",
    "chile": "Chile", "argentina": "Argentina",
    "uruguay": "Uruguay", "peru": "Peru", "perú": "Peru",
    "united states": "US", "united states of america": "US", "usa": "US", "us": "US",
    "regional": "regional", "latam regional": "regional", "latam": "regional",
    "central america": "regional", "centroamerica": "regional", "centroamérica": "regional",
}


def normalize_country(v: str) -> str:
    return COUNTRY_MAP.get(v.strip().lower(), v.strip())


def parse_md(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, flags=re.DOTALL)
    if not m:
        return {}, text
    fm_block, body = m.group(1), m.group(2)
    metadata: dict = {}
    for line in fm_block.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        km = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$", line)
        if not km:
            continue
        key, value = km.group(1), km.group(2)
        v = value.strip()
        if v.lower() == "true":
            metadata[key] = True
        elif v.lower() == "false":
            metadata[key] = False
        elif v.startswith("[") and v.endswith("]"):
            try:
                metadata[key] = json.loads(v)
            except json.JSONDecodeError:
                metadata[key] = v
        elif (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            metadata[key] = v[1:-1]
        else:
            metadata[key] = v
    return metadata, body


def write_md_with_normalized_countries(path: Path, dst_path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    md_match = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n)(.*)$", text, flags=re.DOTALL)
    if not md_match:
        dst_path.write_text(text, encoding="utf-8")
        meta, _ = parse_md(text)
        return meta
    opener, fm_block, closer, body = md_match.groups()
    new_lines = []
    for line in fm_block.splitlines():
        m = re.match(r'^(\s*countries\s*:\s*)(\[.*\])\s*$', line)
        if m:
            try:
                arr = json.loads(m.group(2))
                norm = []
                seen = set()
                for c in arr:
                    cc = normalize_country(c)
                    if cc and cc not in seen:
                        seen.add(cc)
                        norm.append(cc)
                line = f"{m.group(1)}{json.dumps(norm, ensure_ascii=False)}"
            except json.JSONDecodeError:
                pass
        new_lines.append(line)
    new_text = opener + "\n".join(new_lines) + closer + body
    dst_path.write_text(new_text, encoding="utf-8")
    meta, _ = parse_md(new_text)
    return meta


def main():
    if not SRC.exists():
        print(f"ERROR: {SRC} does not exist")
        return

    # Wipe DST except keep the directory
    if DST.exists():
        for p in DST.glob("*"):
            if p.is_file():
                p.unlink()
    DST.mkdir(parents=True, exist_ok=True)

    moved = 0
    index_entries = []
    for src in sorted(SRC.glob("*.md")):
        dst = DST / src.name
        meta = write_md_with_normalized_countries(src, dst)
        moved += 1
        # Build index entry — strip body, keep metadata
        entry = {
            "file": src.name,
            "name": meta.get("name", src.stem),
            "description": meta.get("description", ""),
            "date": meta.get("date", ""),
            "stakeholder": meta.get("stakeholder", ""),
            "role": meta.get("role", ""),
            "organization": meta.get("organization", ""),
            "countries": meta.get("countries", []),
            "topics": meta.get("topics", []),
            "anonymous": meta.get("anonymous", False),
            "anonymized_label": meta.get("anonymized_label", ""),
            "source": meta.get("source", ""),
        }
        index_entries.append(entry)

    # Sort desc by date
    index_entries.sort(key=lambda e: e.get("date", ""), reverse=True)
    INDEX_OUT.write_text(json.dumps(index_entries, indent=2, ensure_ascii=False), encoding="utf-8")

    # Remove the now-empty staging dir
    for p in SRC.glob("*"):
        if p.is_file():
            p.unlink()
    SRC.rmdir()

    countries = sorted({c for e in index_entries for c in (e.get("countries") or [])})
    print(f"Moved {moved} files; index has {len(index_entries)} entries.")
    print(f"Unique countries ({len(countries)}): {countries}")


if __name__ == "__main__":
    main()
