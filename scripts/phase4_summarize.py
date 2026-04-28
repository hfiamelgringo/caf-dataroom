"""Generate standardized summaries from raw transcripts.

Filters out PFA/HF team voices (Jonathan, Mark, Natasha, Rigoberto, Geoffrey)
and intro sections. Outputs to content_data/transcripts_v1/<slug>.md with
skill-style frontmatter for the chat router.

Usage:
  python scripts/phase4_summarize.py [raw_transcript_filename ...]

If no filenames given, summarizes all .txt in content_data/raw_transcripts/.
"""
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KEYS = REPO / "keys.env"
RAW_DIR = REPO / "content_data" / "raw_transcripts"
OUT_DIR = REPO / "content_data" / "transcripts_v1"
MANIFEST = REPO / "scripts" / "phase2_manifest.json"


def load_env():
    for line in KEYS.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()


SYSTEM_PROMPT = """You are summarizing verbatim stakeholder interview transcripts for a CAF \
(Latin American development bank) consulting project on innovation and venture-strategy in four \
small countries: Costa Rica, Honduras, Guatemala, Dominican Republic.

CRITICAL FILTERING RULES:
- The transcripts include voices from the PFA / HF Capital team: Jonathan Nelson, Mark Lopes, \
Natasha Ibarra, Rigoberto Romero, Geoffrey Kirkman. **Do NOT** summarize what they said. They \
are the interviewers; their context-setting, framing questions, and PFA/HF perspective should \
NOT appear in the summary.
- Skip introduction sections (the first ~5–10 minutes of every interview where everyone \
introduces themselves and the project). Start substantively at the actual interview content.
- The summary must reflect ONLY the external stakeholder's perspective — their observations, \
analysis, recommendations, data points, and direct quotes.
- For meetings with multiple external participants, summarize the substantive contributions \
from all non-PFA voices.

QUALITY RULES:
- Each Key Finding must be 50–80 words: a bold headline + 2–3 sentences with specific data \
points (numbers, named programs, dates, dollar figures). Avoid generic 10-word bullets.
- The `description` field is a routing trigger — list concrete questions/topics this transcript \
can answer. Be specific so the chat LLM can pick this transcript over others.

LANGUAGE RULE — ENGLISH ONLY, NO SPANGLISH:
- The entire output must be in fluent English. NO Spanish phrases, NO "(translated from \
Spanish)" annotations, NO bilingual gloss.
- Translate ALL Spanish quotes faithfully into natural English and present them as English \
quotes. The reader should not be able to tell the original was Spanish.
- Translate program / law / institution names into clear English (e.g. Securities Market Law, \
National Commission for Banking and Insurance, Mutual Guarantee Society). Do NOT include the \
Spanish original in parentheses.
- Keep proper nouns (person names, organization names that are brands like "Pomona Impact", \
"Geometría Argentina", "Ruta N", "PROCOMER", "CNBS", "Banco Central") in their established \
form — these are names, not Spanish words to translate.

OUTPUT FORMAT — strict markdown with YAML frontmatter:

---
name: <kebab-case-slug-matching-input-filename-without-extension>
description: When the user asks about <specific topics, named programs, data points> — load this. Covers <stakeholder> from <org> on <date>, discussing <one-line topic>.
date: YYYY-MM-DD
stakeholder: Full Name (or "Multiple stakeholders" if applicable)
role: Their role
organization: Their org
countries: ["CR", "HN", "GT", "DO", "regional", or specific country names]
topics: ["3-7 lowercase-kebab-case tags"]
anonymous: false
anonymized_label: ""
source: drive-transcript
---

## Executive Summary
2–3 paragraph narrative, 150–200 words. The "what they said and why it matters for CAF" version.

## Stakeholder Background
1 paragraph: career arc, current role, why their perspective is relevant.

## Key Findings

### Finding 1: <punchy headline>
<2–3 sentences with specifics: numbers, named programs, dates, $$ figures. 50–80 words.>

### Finding 2: <punchy headline>
...

(Aim for 5–8 findings.)

## Regulatory & Structural Observations
<Same paragraph format. Omit this section entirely if regulation wasn't discussed.>

## Recommendations & Insights
<What this stakeholder thinks should happen — for CAF or the ecosystem.>

## Notable Quotes

> "<English-only quote 1>" — context

> "<English-only quote 2>" — context

(3–5 quotes, all in English. If the speaker was speaking Spanish, the quote here must be a \
clean English translation — do NOT mark it as translated and do NOT include the Spanish original.)

## Connections to Other Interviews
<1–2 sentences cross-referencing related transcripts in the library — e.g. "Echoes Henao on \
local capital flywheel" or "Conflicts with Granada's view on family offices". Skip if no clear \
connection.>

OUTPUT ONLY THE MARKDOWN. No preamble, no code fences, no commentary."""


def summarize_one(client, raw_text: str, slug: str, manifest_entry: dict | None) -> str:
    user_prompt = f"""<input_filename>{slug}.txt</input_filename>
<airtable_record>{manifest_entry['airtable_name'] if manifest_entry else '(unknown)'}</airtable_record>
<fecha>{manifest_entry['fecha'] if manifest_entry else '(unknown)'}</fecha>
<source_url>{manifest_entry['transcript_doc_url'] if manifest_entry else ''}</source_url>

<transcript>
{raw_text}
</transcript>"""

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return msg.content[0].text.strip()


def main():
    load_env()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    from anthropic import Anthropic

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_filename = {m["output_filename"]: m for m in manifest}

    if len(sys.argv) > 1:
        targets = [RAW_DIR / fn for fn in sys.argv[1:]]
    else:
        targets = sorted(RAW_DIR.glob("*.txt"))

    for raw_path in targets:
        if not raw_path.exists():
            print(f"  MISSING: {raw_path.name}")
            continue
        slug = raw_path.stem  # strip .txt
        out_path = OUT_DIR / f"{slug}.md"
        if out_path.exists():
            print(f"  SKIP (exists): {slug}")
            continue
        raw = raw_path.read_text(encoding="utf-8", errors="replace")
        manifest_entry = by_filename.get(raw_path.name)

        print(f"  summarizing: {raw_path.name} ({len(raw)} chars)")
        try:
            md = summarize_one(client, raw, slug, manifest_entry)
        except Exception as e:
            print(f"    ERROR: {e}")
            continue
        # Strip code fences if model added them
        md = re.sub(r"^```(?:markdown)?\s*\n", "", md)
        md = re.sub(r"\n```\s*$", "", md)
        out_path.write_text(md, encoding="utf-8")
        print(f"    -> {out_path.name} ({len(md)} chars)")


if __name__ == "__main__":
    main()
