"""Append topic + (N of M interviews) to stakeholder names with multiple sessions."""
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TX = REPO / "content_data" / "transcripts"
INDEX = TX / "index.json"

# Per-slug topic suffix. Slugs are listed in date order within each cluster.
RENAMES = {
    "Dave McClure": [
        ("2026-03-05-dave-mcclure-practical-vc", "Fund-of-funds & angel incentives"),
        ("2026-03-16-dave-mcclure-practical-vc", "Engineering a VC ecosystem"),
    ],
    "Francisco Meneses": [
        ("2026-03-05-francisco-meneses-corfo", "Corfo fund-of-funds"),
        ("2026-03-19-francisco-meneses", "Regional fund design"),
    ],
    "José Kont": [
        ("2026-02-05-jos-kont-cuantico", "Guatemala ecosystem"),
        ("2026-02-19-jos-kont-cuantico", "Central America VC gaps"),
        ("2026-04-21-jos-kont", "Startup law for Central America"),
    ],
    "Rockefeller Foundation": [
        ("2026-01-14-rockefeller-foundation-latam", "LatAm regional strategy"),
        ("2026-02-11-rockefeller", "Food systems in Central America"),
    ],
}


def build_new_label(base: str, topic: str, n: int, total: int) -> str:
    return f"{base} — {topic} ({n} of {total} interviews)"


def update_index(plan: dict[str, str]):
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    changed = 0
    for entry in data:
        slug = entry.get("name")
        if slug in plan:
            entry["stakeholder"] = plan[slug]
            changed += 1
    INDEX.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"index.json: updated {changed} entries")


def update_frontmatter(plan: dict[str, str]):
    for slug, new_label in plan.items():
        path = TX / f"{slug}.md"
        text = path.read_text(encoding="utf-8")
        m = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n?)(.*)$", text, flags=re.DOTALL)
        if not m:
            print(f"  SKIP {slug}")
            continue
        head, fm, tail_marker, body = m.groups()
        # quote because the value contains punctuation
        replacement = f'stakeholder: "{new_label}"'
        fm = re.sub(r"^stakeholder\s*:.*$", replacement, fm, flags=re.MULTILINE)
        path.write_text(head + fm + tail_marker + body, encoding="utf-8")
        print(f"  {slug} → {new_label}")


def main():
    plan = {}
    for base, sessions in RENAMES.items():
        total = len(sessions)
        for n, (slug, topic) in enumerate(sessions, start=1):
            plan[slug] = build_new_label(base, topic, n, total)
    update_index(plan)
    update_frontmatter(plan)


if __name__ == "__main__":
    main()
