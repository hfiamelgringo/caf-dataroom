"""Build a flat-file transcript library from Airtable Meeting Notes + public Granola share URLs.

Pipeline per record:
  1. Filter Airtable Meeting Notes (drop Internal / CAF-direct / Rigo<>Nati)
  2. If Granola URL, scrape public share page → extract curated notes
  3. Resolve country/stakeholder/institution links via Airtable lookups
  4. Call Anthropic API to generate skill-style frontmatter (description, topics)
  5. Write content_data/transcripts/<slug>.md
  6. Append to index.json

Drive URLs and unmatched records → content_data/transcripts/_unmatched.txt
"""
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

import requests
from anthropic import Anthropic
from pyairtable import Api

# --- Config ---
BASE_ID = "appVMgNUokH0882lO"
MEETING_NOTES_TABLE = "tblK16rZogch6Rq7S"
COUNTRIES_TABLE = "tblMm0KwvqdZvN7sf"

REPO = Path(__file__).resolve().parent.parent
KEYS = REPO / "keys.env"
OUT_DIR = REPO / "content_data" / "transcripts"
INDEX_PATH = OUT_DIR / "index.json"
UNMATCHED_PATH = OUT_DIR / "_unmatched.txt"

EXCLUDE_PATTERNS = [
    re.compile(r"\binternal\b", re.I),
    re.compile(r"rigo\s*<>\s*nati", re.I),
    re.compile(r"\bcaf\b", re.I),  # CAF-direct calls (CABEI, CINDE, etc. are kept)
]

# CAF is excluded but legitimate stakeholder orgs that contain "caf" substrings should pass.
# We also keep CABEI explicitly:
KEEP_OVERRIDES = [re.compile(r"\bCABEI\b", re.I)]


def load_env():
    for line in KEYS.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()


def should_keep(name: str) -> bool:
    if any(p.search(name) for p in KEEP_OVERRIDES):
        return True
    if any(p.search(name) for p in EXCLUDE_PATTERNS):
        return False
    return True


def slugify(s: str, max_len: int = 70) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s[:max_len]


def fetch_share(url: str) -> str | None:
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; caf-dataroom)"},
            timeout=30,
            allow_redirects=True,
        )
        return resp.text
    except requests.RequestException as e:
        print(f"  fetch failed: {e}")
        return None


def parse_share(html: str) -> dict:
    title_m = re.search(r"<title[^>]*>([^<]+)</title>", html)
    desc_m = re.search(r'name="description"\s+content="([^"]+)"', html)
    og_desc_m = re.search(r'og:description"\s+content="([^"]+)"', html)
    date_m = re.search(r"date=([^&\\]+?)(?:\\u0026|&|\\\\)", html)
    date_str = unquote(date_m.group(1).replace("+", " ")) if date_m else ""

    text_chunks = []
    seen = set()
    pattern = re.compile(r'\\"text\\":\\"((?:[^"\\]|\\\\.)*?)\\"')
    for m in pattern.finditer(html):
        raw = m.group(1)
        try:
            decoded = json.loads('"' + raw + '"')
        except json.JSONDecodeError:
            decoded = (
                raw.replace("\\\\n", "\n")
                .replace('\\\\"', '"')
                .replace("\\\\u003c", "<")
                .replace("\\\\u003e", ">")
                .replace("\\\\u0026", "&")
                .replace("\\\\", "")
            )
        decoded = decoded.strip()
        if len(decoded) < 4 or decoded in seen:
            continue
        seen.add(decoded)
        text_chunks.append(decoded)

    return {
        "page_title": title_m.group(1) if title_m else "",
        "author": desc_m.group(1) if desc_m else "",
        "summary_preview": og_desc_m.group(1) if og_desc_m else "",
        "date_str": date_str,
        "bullets": text_chunks,
    }


def parse_iso_date(date_str: str) -> str:
    """Normalize 'Wed, March 11, 2026' or '2026-03-11' to ISO 'YYYY-MM-DD'."""
    if not date_str:
        return ""
    if re.match(r"^\d{4}-\d{2}-\d{2}", date_str):
        return date_str[:10]
    for fmt in ("%a, %B %d, %Y", "%A, %B %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str


def parse_title(name: str) -> tuple[str, str]:
    """Best-effort: split 'MM.DD.YYYY. Stakeholder - Organization' into (stakeholder, org)."""
    # Strip leading date prefix
    cleaned = re.sub(r"^\s*\d{2}\.\d{2}(\.\d{2,4})?\.?\s*", "", name).strip()
    if " - " in cleaned:
        parts = cleaned.split(" - ", 1)
        return parts[0].strip(), parts[1].strip()
    return cleaned, ""


def enrich_with_llm(client: Anthropic, meta: dict, bullets: list[str]) -> dict:
    """Use Claude to produce skill-style frontmatter (description, topics, narrative context)."""
    bullet_text = "\n".join(f"- {b}" for b in bullets[:60])
    prompt = f"""You are organizing a flat-file library of stakeholder interview notes for a CAF (Latin American development bank) consulting project on innovation and venture strategy in small Latin American countries (Costa Rica, Honduras, Guatemala, Dominican Republic).

Each interview becomes one markdown file with skill-style routing frontmatter. The `description` field is what an LLM scans at retrieval time to decide whether to load this file for a given user question — write it as a *trigger description*, listing concrete topics/questions/themes this file covers.

Interview metadata:
- Stakeholder (best guess from title): {meta.get('stakeholder','')}
- Organization (best guess): {meta.get('organization','')}
- Date: {meta.get('date','')}
- Country links (Airtable): {meta.get('countries_raw','')}
- Project tag: {meta.get('project','')}
- Page title: {meta.get('page_title','')}

Curated notes (Granola AI summary by Natasha):
{bullet_text}

Output ONLY a JSON object with these keys (no other text, no markdown fences):
{{
  "stakeholder": "Best name (correct if title parsing was off)",
  "role": "Role at org (or empty)",
  "organization": "Org name (or empty)",
  "countries": ["CR", "HN", "GT", "DO", or "regional", or specific country names],
  "topics": ["3-6 lowercase-kebab-case topic tags"],
  "description": "Trigger description: 'When the user asks about X, Y, or Z — load this. Covers <stakeholder> from <org> on <date> discussing <one-line topic>.' Be concrete and don't overlap with what other interviews would cover.",
  "context": "1-2 sentence narrative context for the start of the file: who, what was discussed, why it matters."
}}"""
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text.strip()
    # Strip code fences if model added them
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Last-resort fallback
        return {
            "stakeholder": meta.get("stakeholder", ""),
            "role": "",
            "organization": meta.get("organization", ""),
            "countries": [],
            "topics": [],
            "description": f"Notes from interview with {meta.get('stakeholder','')} on {meta.get('date','')}.",
            "context": "(LLM enrichment failed; raw notes below.)",
        }


def write_file(path: Path, frontmatter: dict, context: str, bullets: list[str], source_url: str) -> None:
    fm_lines = ["---"]
    fm_lines.append(f"name: {frontmatter['name']}")
    fm_lines.append(f"description: {frontmatter['description']}")
    fm_lines.append(f"date: {frontmatter['date']}")
    fm_lines.append(f"stakeholder: {frontmatter['stakeholder']}")
    if frontmatter.get("role"):
        fm_lines.append(f"role: {frontmatter['role']}")
    if frontmatter.get("organization"):
        fm_lines.append(f"organization: {frontmatter['organization']}")
    fm_lines.append(f"countries: {json.dumps(frontmatter.get('countries', []))}")
    fm_lines.append(f"topics: {json.dumps(frontmatter.get('topics', []))}")
    fm_lines.append(f"source_url: {source_url}")
    fm_lines.append("---")
    fm_lines.append("")
    fm_lines.append("## Context")
    fm_lines.append(context)
    fm_lines.append("")
    fm_lines.append("## Notes")
    for b in bullets:
        fm_lines.append(f"- {b}")
    path.write_text("\n".join(fm_lines), encoding="utf-8")


def main():
    load_env()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    api = Api(os.environ["AIRTABLE_PAT"])
    mn = api.table(BASE_ID, MEETING_NOTES_TABLE)
    countries_table = api.table(BASE_ID, COUNTRIES_TABLE)

    # Build Country lookup: record_id -> name
    country_lookup = {}
    for c in countries_table.all(fields=["Name"]):
        country_lookup[c["id"]] = c["fields"].get("Name", "")

    # Fetch all Meeting Notes
    records = mn.all(fields=["Name", "Granola", "Fecha", "Project", "Project.", "Countries", "Stakeholders"])

    print(f"Total Meeting Notes: {len(records)}")

    keep = []
    skip_filter = []
    no_url = []
    for r in records:
        f = r["fields"]
        name = f.get("Name", "")
        if not name:
            continue
        if not f.get("Granola"):
            no_url.append(name)
            continue
        if not should_keep(name):
            skip_filter.append(name)
            continue
        keep.append(r)

    print(f"After filter: {len(keep)} kept, {len(skip_filter)} excluded by name, {len(no_url)} no Granola URL")

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    index_entries = []
    unmatched = []

    for i, r in enumerate(keep, 1):
        f = r["fields"]
        name = f["Name"]
        url = f["Granola"]
        fecha = f.get("Fecha", "")
        country_ids = f.get("Countries", []) or []
        country_names = [country_lookup.get(cid, "") for cid in country_ids if cid]
        project = f.get("Project") or f.get("Project.") or ""

        print(f"\n[{i}/{len(keep)}] {name}")
        print(f"  URL: {url}")

        # Drive URLs need separate handling
        if "docs.google.com" in url or "drive.google.com" in url:
            unmatched.append(f"{fecha}  {name}  (Google Doc — needs Drive API)  {url}")
            print("  -> Google Doc, skipping")
            continue

        if "notes.granola.ai" not in url:
            unmatched.append(f"{fecha}  {name}  (unknown URL host)  {url}")
            print(f"  -> unknown host, skipping")
            continue

        html = fetch_share(url)
        if not html:
            unmatched.append(f"{fecha}  {name}  (fetch failed)  {url}")
            continue

        parsed = parse_share(html)
        if len(parsed["bullets"]) < 5:
            unmatched.append(f"{fecha}  {name}  (no/few content chunks: {len(parsed['bullets'])})  {url}")
            print(f"  -> only {len(parsed['bullets'])} chunks, skipping")
            continue

        stakeholder_guess, org_guess = parse_title(name)
        date_iso = parse_iso_date(fecha) or parse_iso_date(parsed["date_str"])

        meta = {
            "stakeholder": stakeholder_guess,
            "organization": org_guess,
            "date": date_iso,
            "countries_raw": ", ".join(country_names),
            "project": str(project),
            "page_title": parsed["page_title"],
        }

        try:
            enriched = enrich_with_llm(client, meta, parsed["bullets"])
        except Exception as e:
            print(f"  LLM enrichment failed: {e}")
            unmatched.append(f"{fecha}  {name}  (LLM error: {e})  {url}")
            continue

        slug = f"{date_iso}-{slugify(enriched['stakeholder'] or stakeholder_guess)}"
        slug = slug.strip("-")
        out_path = OUT_DIR / f"{slug}.md"

        frontmatter = {
            "name": slug,
            "description": enriched["description"],
            "date": date_iso,
            "stakeholder": enriched["stakeholder"],
            "role": enriched.get("role", ""),
            "organization": enriched.get("organization", ""),
            "countries": enriched.get("countries", country_names),
            "topics": enriched.get("topics", []),
        }
        write_file(out_path, frontmatter, enriched["context"], parsed["bullets"], url)
        print(f"  -> wrote {out_path.name}")

        index_entries.append({
            "file": out_path.name,
            **{k: v for k, v in frontmatter.items() if k != "name"},
            "name": slug,
        })

        time.sleep(0.5)  # gentle on Granola + Anthropic

    # Sort index by date desc
    index_entries.sort(key=lambda e: e["date"], reverse=True)
    INDEX_PATH.write_text(json.dumps(index_entries, indent=2, ensure_ascii=False), encoding="utf-8")

    if unmatched:
        UNMATCHED_PATH.write_text("\n".join(unmatched), encoding="utf-8")

    print(f"\nDone. Wrote {len(index_entries)} files to {OUT_DIR}")
    print(f"Index: {INDEX_PATH}")
    if unmatched:
        print(f"Unmatched: {len(unmatched)} (see {UNMATCHED_PATH})")


if __name__ == "__main__":
    main()
