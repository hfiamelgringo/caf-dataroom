"""One-shot rename of "Multiple stakeholders" entries.

Updates stakeholder, role, and (optionally) organization in both
content_data/transcripts/index.json AND each file's YAML-style frontmatter.
"""
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TX = REPO / "content_data" / "transcripts"
INDEX = TX / "index.json"

RENAMES = {
    "2026-04-22-cnbs-honduras": {
        "stakeholder": "CNBS Honduras",
        "role": "Betsabe Franco, Superintendent of Pensions and Securities; Benjamín Santos, Securities Supervision",
        # keep organization as-is
    },
    "2026-03-17-central-american-vc-roundtable": {
        "stakeholder": "Central American VC roundtable (4 funds)",
        "role": "Gallot · Abigail & Charles (Ara Impact Capital) · Guillermo (Amador)",
        # keep organization as-is
    },
    "2026-03-11-albedo-solar": {
        "stakeholder": "Albedo Solar",
        "role": "Alex Macfarlan & Jacob Stern, Co-founders",
        "organization": "",
    },
    "2026-02-12-louis-prouvost-level-up": {
        "stakeholder": "Level Up",
        "role": "Louis Prouvost & Jose, Co-founders",
        "organization": "",
    },
    "2026-02-11-rockefeller": {
        "stakeholder": "Rockefeller Foundation",
        "role": "Andrea (Program Officer) & Natalia, Bogotá regional office",
        "organization": "",
    },
    "2026-02-03-jorge-vargas-venture-do": {
        "stakeholder": "Venture.do",
        "role": "Jorge Vargas, Michael & Carolle, Co-founders",
        "organization": "",
    },
    "2026-01-14-rockefeller-foundation-latam": {
        "stakeholder": "Rockefeller Foundation",
        "role": "Liana (Regional Director) & Andrea Acevedo (Program Operations)",
        "organization": "",
    },
}


def update_index():
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    changed = 0
    for entry in data:
        name = entry.get("name")
        if name in RENAMES:
            for k, v in RENAMES[name].items():
                entry[k] = v
            changed += 1
    INDEX.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"index.json: updated {changed} entries")


def update_frontmatter():
    for slug, fields in RENAMES.items():
        path = TX / f"{slug}.md"
        text = path.read_text(encoding="utf-8")
        m = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n?)(.*)$", text, flags=re.DOTALL)
        if not m:
            print(f"  SKIP {slug} — no frontmatter found")
            continue
        head, fm, tail_marker, body = m.groups()
        for key, value in fields.items():
            # quote value if it contains special chars or is empty
            quoted = f'"{value}"' if (value == "" or any(c in value for c in ":#")) else value
            line_re = re.compile(rf"^{re.escape(key)}\s*:.*$", flags=re.MULTILINE)
            replacement = f"{key}: {quoted}"
            if line_re.search(fm):
                fm = line_re.sub(replacement, fm)
            else:
                # append at end of frontmatter
                fm = fm.rstrip() + f"\n{replacement}"
        path.write_text(head + fm + tail_marker + body, encoding="utf-8")
        print(f"  updated {slug}")


if __name__ == "__main__":
    update_index()
    update_frontmatter()
