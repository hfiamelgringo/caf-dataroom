"""Convert content_data/interviews.json (3 polished hand-written summaries) into flat
markdown files in content_data/transcripts/, with skill-style frontmatter, and append
to index.json.

Idempotent: skips entries already present in index.json by name.
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "content_data" / "interviews.json"
DST = REPO / "content_data" / "transcripts"
INDEX = DST / "index.json"

DESCRIPTIONS = {
    "procomer-costa-rica-vc-ecosystem": (
        "When the user asks about Costa Rica's investment-promotion model, PROCOMER's structure "
        "and KPIs, the Acá Global credit-bridge program, the Silicon Valley OPI office, the ~700 "
        "multinationals clustered in Alajuela/Grecia/Cartago, Costa Rican banking regulation gaps "
        "(consumer-banking bias, no ticket-size differentiation), the absence of a startup law, "
        "or comparing Costa Rica to Ireland or Korea on human-capital strategy — load this. "
        "Hand-written summary of Efraín Torrentes Guillén (PROCOMER, Encadenamientos) on 2026-04-08."
    ),
    "ruta-n-medellin-vc-strategy": (
        "When the user asks about Medellín's city-level VC strategy as a peer model for CAF, "
        "the Medellín Venture Capital three-pronged program (formation / community / fund-of-funds), "
        "the 97% foreign / 3% local capital data point, the Mei Capital syndicate origin story, "
        "the Bancoldex / Sima Fintech Plus investment cascade, the Israeli Yozma / Mexican FdF / "
        "Peruvian COFIDE / Chilean CORFO reference set, the Inversómetro and Startia open-data tools, "
        "or 'money follows the money' as a local-investment thesis — load this. "
        "Hand-written summary of Santiago Henao (Director, Medellín Venture Capital at Ruta N) on 2026-04-09."
    ),
    "petra-secondaries-latam-liquidity": (
        "When the user asks about LatAm VC secondary markets, the Petra Secondaries brokerage thesis, "
        "the supply-demand mismatch (200 inbound seller offers vs. ~8 deals in 6 weeks), why $30M+ "
        "secondary positions can't clear locally, the proposed $500M closed-end LatAm VC vehicle modeled "
        "on Pershing Square, the 70% foreign / 30% local capital flow data, or DPI pressure on Fund 1/2 LPs — "
        "load this. Hand-written summary of Fabricio Zabala (Founder, Petra Secondaries) on 2026-04-17."
    ),
}

TOPICS = {
    "procomer-costa-rica-vc-ecosystem": [
        "investment-promotion", "costa-rica", "banking-regulation", "multinationals",
        "talent-policy", "ireland-peer-model"
    ],
    "ruta-n-medellin-vc-strategy": [
        "fund-of-funds", "local-capital-flywheel", "ecosystem-data", "ruta-n",
        "venture-capital", "peer-model"
    ],
    "petra-secondaries-latam-liquidity": [
        "secondary-markets", "exits", "liquidity", "fund-vehicle-design",
        "capital-flows", "dpi"
    ],
}

NEW_SLUGS = {
    "procomer-costa-rica-vc-ecosystem": "2026-04-08-efrain-torrentes-procomer",
    "ruta-n-medellin-vc-strategy": "2026-04-09-santiago-henao-ruta-n-summary",
    "petra-secondaries-latam-liquidity": "2026-04-17-fabricio-zabala-petra",
}


def main():
    src_records = json.loads(SRC.read_text(encoding="utf-8"))
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    existing_names = {e["name"] for e in index}

    added = 0
    for r in src_records:
        old_slug = r["slug"]
        new_slug = NEW_SLUGS.get(old_slug)
        if not new_slug:
            print(f"SKIP unrecognized slug: {old_slug}")
            continue
        if new_slug in existing_names:
            print(f"SKIP already in index: {new_slug}")
            continue

        countries = []
        if r.get("country_code"):
            countries.append(r["country_code"])
        country_label = r.get("country_label", "")
        if country_label and country_label not in countries:
            countries.append(country_label)

        topics = TOPICS.get(old_slug, [])
        description = DESCRIPTIONS.get(old_slug, "")

        # Build frontmatter
        fm_lines = [
            "---",
            f"name: {new_slug}",
            f"description: {description}",
            f"date: {r['date']}",
            f"stakeholder: {r['stakeholder_name']}",
            f"role: {r.get('stakeholder_role', '')}",
            f"organization: {r.get('organization', '')}",
            f"countries: {json.dumps(countries, ensure_ascii=False)}",
            f"topics: {json.dumps(topics, ensure_ascii=False)}",
            "anonymous: false",
            'anonymized_label: ""',
            "source: hand-written-summary",
            "source_url: ",
            "---",
            "",
        ]
        body = r["body_markdown"].strip() + "\n"
        out_path = DST / f"{new_slug}.md"
        out_path.write_text("\n".join(fm_lines) + body, encoding="utf-8")
        print(f"wrote {out_path.name}")

        index.append({
            "file": f"{new_slug}.md",
            "description": description,
            "date": r["date"],
            "stakeholder": r["stakeholder_name"],
            "role": r.get("stakeholder_role", ""),
            "organization": r.get("organization", ""),
            "countries": countries,
            "topics": topics,
            "anonymous": False,
            "anonymized_label": "",
            "source": "hand-written-summary",
            "name": new_slug,
        })
        added += 1

    # Sort by date desc
    index.sort(key=lambda e: e["date"], reverse=True)
    INDEX.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nAdded {added} entries; total {len(index)} in index.json")


if __name__ == "__main__":
    main()
