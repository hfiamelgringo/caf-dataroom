"""Append the 3 Drive-sourced transcripts to index.json."""
import json
from pathlib import Path

INDEX = Path(__file__).resolve().parent.parent / "content_data" / "transcripts" / "index.json"

new_entries = [
    {
        "file": "2026-04-09-santiago-henao-ruta-n-transcript.md",
        "description": "When the user wants verbatim Spanish-language quotes from the Ruta N Medellín conversation — exact phrasing on the Medellín Venture Capital fund-of-funds program, the 97/3 local-vs-foreign capital data point, the Bancoldex / Sima Fintech investment specifics, or the \"money follows the money\" narrative — load this. Verbatim transcript of Santiago Henao (Director, Medellín Venture Capital at Ruta N) on 2026-04-09. Companion to the bullet-summary version; use this when citing direct quotes is important.",
        "date": "2026-04-09",
        "stakeholder": "Santiago Henao",
        "role": "Director, Medellín Venture Capital",
        "organization": "Ruta N (Medellín)",
        "countries": ["Colombia", "regional"],
        "topics": ["fund-of-funds", "local-capital-flywheel", "ecosystem-data", "ruta-n", "venture-capital", "verbatim-quotes"],
        "source": "drive-transcript",
        "name": "2026-04-09-santiago-henao-ruta-n-transcript",
    },
    {
        "file": "2026-03-24-christian-marin-muller-speratum.md",
        "description": "When the user asks about Speratum Biopharma, Costa Rica biotech founders, Christian Marín-Müller's background (Baylor College of Medicine, Case Western Ventures), or PFA / CAF outreach to Costa Rican biotech entrepreneurs — load this. Note: this Drive doc is thin (mostly intros, transcription cut off at ~6 minutes); useful primarily for confirming the meeting happened and the participant background.",
        "date": "2026-03-24",
        "stakeholder": "Christian Marín-Müller",
        "role": "Founder",
        "organization": "Speratum",
        "countries": ["CR"],
        "topics": ["biotech", "costa-rica", "founder-introductions", "speratum"],
        "source": "drive-gemini-notes-english",
        "name": "2026-03-24-christian-marin-muller-speratum",
    },
    {
        "file": "2026-01-14-rockefeller-andrea-acevedo-detailed.md",
        "description": "When the user asks about Rockefeller Foundation's regional strategy in Latin America, the three thematic lines (energy, health, food systems), the $100M / 100-million-children School Meals \"big bet\", climate-migration as a Central America-specific differentiator, the Honduras heat-and-health project at sugarcane mills, Rockefeller's \"no open calls / scale existing initiatives\" funding philosophy, the proposed Central America climate-migration convening (Guatemala, Q2-2026), or PFA's relationships with FAO / Secretaría de Agricultura / COEP in Honduras — load this. Detailed Gemini-structured Spanish notes from a meeting between PFA and Rockefeller Foundation regional leadership (Andrea Acevedo + Lyana Latorre) on 2026-01-14.",
        "date": "2026-01-14",
        "stakeholder": "Andrea Acevedo",
        "role": "Regional Office Lead, Latin America & Caribbean",
        "organization": "Rockefeller Foundation",
        "countries": ["regional", "GT", "HN", "CR", "Colombia", "Brazil"],
        "topics": ["climate-migration", "school-meals", "regenerative-agriculture", "energy-access", "philanthropic-strategy", "convening-model", "private-sector-partnership"],
        "source": "drive-gemini-notes-spanish",
        "name": "2026-01-14-rockefeller-andrea-acevedo-detailed",
    },
]

existing = json.loads(INDEX.read_text(encoding="utf-8"))

# Avoid dupes by name
existing_names = {e["name"] for e in existing}
added = 0
for e in new_entries:
    if e["name"] in existing_names:
        continue
    existing.append(e)
    added += 1

# Sort by date desc
existing.sort(key=lambda e: e["date"], reverse=True)

INDEX.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Added {added} entries; total {len(existing)} in index.json")
