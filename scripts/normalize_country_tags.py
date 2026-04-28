"""Normalize country values across all transcript .md frontmatters and index.json.

Avoids YAML round-tripping (some descriptions have unquoted colons that break YAML).
Operates directly on the `countries:` line via regex.
"""
import json
import re
from collections import OrderedDict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DST = REPO / "content_data" / "transcripts"
INDEX = DST / "index.json"

COUNTRY_MAP = {
    "costa rica": "CR",
    "cr": "CR",
    "honduras": "HN",
    "hn": "HN",
    "guatemala": "GT",
    "gt": "GT",
    "dominican republic": "DO",
    "do": "DO",
    "república dominicana": "DO",
    "republica dominicana": "DO",
    "el salvador": "SV",
    "sv": "SV",
    "colombia": "Colombia",
    "colombia (peer model)": "Colombia",
    "mexico": "Mexico",
    "méxico": "Mexico",
    "brazil": "Brazil",
    "brasil": "Brazil",
    "chile": "Chile",
    "argentina": "Argentina",
    "uruguay": "Uruguay",
    "peru": "Peru",
    "perú": "Peru",
    "united states": "US",
    "united states of america": "US",
    "usa": "US",
    "us": "US",
    "regional": "regional",
    "latam regional": "regional",
    "latam": "regional",
    "central america": "regional",
    "centroamerica": "regional",
    "centroamérica": "regional",
}


def normalize_one(value: str) -> str:
    return COUNTRY_MAP.get(value.strip().lower(), value.strip())


def normalize_list(values: list[str]) -> list[str]:
    out = OrderedDict()
    for v in values:
        canon = normalize_one(v)
        if canon and canon not in out:
            out[canon] = True
    return list(out.keys())


def parse_json_array_line(line: str) -> list[str] | None:
    """Parse a JSON array off a 'key: ["a","b"]' frontmatter line."""
    m = re.match(r'^\s*countries:\s*(\[.*\])\s*$', line)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def main():
    md_files = sorted(DST.glob("*.md"))
    md_changed = 0
    for f in md_files:
        text = f.read_text(encoding="utf-8")
        m = re.match(r"^(---\n)(.*?)(\n---\n)(.*)$", text, flags=re.DOTALL)
        if not m:
            continue
        opener, frontmatter, closer, body = m.groups()
        new_lines = []
        line_changed = False
        for line in frontmatter.splitlines():
            arr = parse_json_array_line(line)
            if arr is not None:
                normalized = normalize_list(arr)
                if normalized != arr:
                    line = f"countries: {json.dumps(normalized, ensure_ascii=False)}"
                    line_changed = True
            new_lines.append(line)
        if line_changed:
            f.write_text(opener + "\n".join(new_lines) + closer + body, encoding="utf-8")
            md_changed += 1

    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    idx_changed = 0
    for e in idx:
        original = e.get("countries") or []
        normalized = normalize_list(original)
        if normalized != original:
            e["countries"] = normalized
            idx_changed += 1
    if idx_changed:
        INDEX.write_text(json.dumps(idx, indent=2, ensure_ascii=False), encoding="utf-8")

    all_countries = set()
    for e in idx:
        for c in e.get("countries") or []:
            all_countries.add(c)

    print(f".md files normalized: {md_changed} / {len(md_files)}")
    print(f"index.json entries normalized: {idx_changed}")
    print(f"\nUnique countries after normalization ({len(all_countries)}): {sorted(all_countries)}")


if __name__ == "__main__":
    main()
