"""Sensitivity audit over the published interview summaries.

Goal: find every passage where a stakeholder criticizes a NAMED person or
organization, so a human can decide whether to keep, soften, or cut it
before showing the dataroom to CAF.

Two passes (split so each can be reviewed before continuing):

  scan        — Pass 1. Per-file Haiku classifier. Emits raw findings to
                audit/pass1_findings.json and a human-readable
                audit/pass1_review.md.

  adjudicate  — Pass 2. Sonnet groups findings by target and recommends
                keep / soften / cut for each. Emits audit/pass2_review.md.
                Run AFTER reviewing pass 1.

  apply       — Apply human decisions from audit/pass2_decisions.json
                to the source .md files. NOT YET IMPLEMENTED — wait until
                after pass 2 review.

Usage:
  python scripts/sensitivity_audit.py scan
  python scripts/sensitivity_audit.py adjudicate
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KEYS = REPO / "keys.env"
TRANSCRIPTS_DIR = REPO / "content_data" / "transcripts"
INDEX = TRANSCRIPTS_DIR / "index.json"
AUDIT_DIR = REPO / "audit"

SCAN_MODEL = "claude-haiku-4-5-20251001"
ADJUDICATE_MODEL = "claude-sonnet-4-6"


def load_env():
    if not KEYS.exists():
        return
    for line in KEYS.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()


SCAN_SYSTEM = """You are a sensitivity reviewer for a consulting deliverable. \
You receive a STAKEHOLDER INTERVIEW SUMMARY that quotes or paraphrases the \
stakeholder's views. Your job is to find every passage where the stakeholder \
criticizes, complains about, or portrays NEGATIVELY a NAMED person or \
NAMED organization (not vague "VCs" or "the government" — actual names).

Return ONLY a JSON array. Each item:
{
  "quote": "<verbatim or near-verbatim sentence(s) from the summary>",
  "target_name": "<person or organization being criticized>",
  "target_type": "person" | "org",
  "severity": "mild" | "moderate" | "sharp",
  "category": "competence" | "integrity" | "performance" | "behavior" | "other",
  "is_caf": true | false
}

Rules:
- Include institutional criticism that's directional / substantive, not just personal.
- Include criticism of CAF itself; mark with is_caf=true.
- Do NOT include praise, neutral description, or generic complaints with no named target.
- Do NOT include the stakeholder criticizing their OWN org or themselves.
- "mild" = factual gap or limitation. "moderate" = clear negative judgment.
- "sharp" = personal attack, accusation of dishonesty/incompetence, or anything \
that would embarrass the target if read aloud.
- If nothing qualifies, return [].
- Output ONLY the JSON array, no prose, no markdown fences."""


ADJUDICATE_SYSTEM = """You are advising a consultant preparing to share a \
stakeholder-interview library with CAF (Latin American development bank). \
You receive a list of criticism passages found across the library, grouped by target.

For each TARGET, recommend one of:
  KEEP    — defensible, substantive, the kind of analytic content CAF needs to hear.
  SOFTEN  — substance is fine but tone/specificity should be reworded.
  CUT     — gossip, ad hominem, or otherwise indefensible. Remove from the summary.
  REVIEW  — borderline; the consultant should read it themselves.

Output a markdown document with one section per target. Use this format:

## <Target name> (<n> mention(s))

**Recommendation:** KEEP | SOFTEN | CUT | REVIEW
**Reasoning:** <one sentence>

- [<source slug>] severity: <mild|moderate|sharp> — "<quote>"
- ...

Sort sections by severity (sharp first, then moderate, then mild). \
Within each section, sort entries by source slug.

Open with a one-paragraph executive summary: how many targets, how many CUT/SOFTEN \
recommendations, any patterns worth flagging (e.g. "three stakeholders independently \
criticize Org X — the criticism may be load-bearing")."""


def list_summary_files():
    return sorted(p for p in TRANSCRIPTS_DIR.glob("*.md"))


def extract_body(md_text: str) -> str:
    """Strip frontmatter — return only the body the chat router will quote."""
    m = re.match(r"^---\s*\n.*?\n---\s*\n?(.*)$", md_text, flags=re.DOTALL)
    return m.group(1).strip() if m else md_text.strip()


def stakeholder_label(md_text: str) -> str:
    """Pull stakeholder name from frontmatter for context."""
    m = re.search(r"^stakeholder:\s*(.+)$", md_text, flags=re.MULTILINE)
    return m.group(1).strip().strip('"\'') if m else "?"


def organization_label(md_text: str) -> str:
    m = re.search(r"^organization:\s*(.+)$", md_text, flags=re.MULTILINE)
    return m.group(1).strip().strip('"\'') if m else ""


def parse_json_strict(text: str):
    """Parse Claude's output, tolerating a trailing/leading code fence."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE).strip()
    return json.loads(cleaned)


def scan(client, only: list[str] | None = None) -> dict:
    files = list_summary_files()
    if only:
        only_set = set(only)
        files = [f for f in files if f.stem in only_set]

    findings_by_file = {}
    for i, path in enumerate(files, 1):
        slug = path.stem
        text = path.read_text(encoding="utf-8")
        body = extract_body(text)
        speaker = stakeholder_label(text)
        org = organization_label(text)

        prompt = f"""<source_slug>{slug}</source_slug>
<stakeholder>{speaker}</stakeholder>
<stakeholder_organization>{org}</stakeholder_organization>

<summary_body>
{body}
</summary_body>"""

        print(f"[{i}/{len(files)}] {slug} …", end="", flush=True)
        msg = client.messages.create(
            model=SCAN_MODEL,
            max_tokens=2000,
            system=SCAN_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text
        try:
            findings = parse_json_strict(raw)
            if not isinstance(findings, list):
                findings = []
        except json.JSONDecodeError:
            print(f" PARSE FAIL — raw saved")
            findings_by_file[slug] = {"_parse_error": raw}
            continue

        # Skip self-criticism (stakeholder criticizing their own org)
        own_org = (org or "").lower().strip()
        kept = []
        for f in findings:
            if not isinstance(f, dict):
                continue
            target = (f.get("target_name") or "").lower().strip()
            if own_org and (target == own_org or target in own_org or own_org in target):
                continue
            kept.append(f)

        findings_by_file[slug] = {
            "stakeholder": speaker,
            "organization": org,
            "findings": kept,
        }
        print(f" {len(kept)} finding(s)")

    return findings_by_file


def write_pass1_outputs(findings_by_file: dict):
    AUDIT_DIR.mkdir(exist_ok=True)
    json_path = AUDIT_DIR / "pass1_findings.json"
    md_path = AUDIT_DIR / "pass1_review.md"

    json_path.write_text(json.dumps(findings_by_file, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Sensitivity Audit — Pass 1 (raw findings)",
        "",
        "Per-file scan by Claude Haiku. Each entry is a passage flagged as named-person",
        "or named-org criticism. Review this BEFORE running pass 2.",
        "",
        "Counts:",
    ]
    total_findings = 0
    files_with_findings = 0
    sharp_count = 0
    caf_count = 0
    for slug, data in findings_by_file.items():
        if "_parse_error" in data:
            continue
        n = len(data["findings"])
        total_findings += n
        if n:
            files_with_findings += 1
        for f in data["findings"]:
            if f.get("severity") == "sharp":
                sharp_count += 1
            if f.get("is_caf"):
                caf_count += 1

    lines += [
        f"- Files scanned: {len(findings_by_file)}",
        f"- Files with at least one finding: {files_with_findings}",
        f"- Total findings: {total_findings}",
        f"- Sharp severity: {sharp_count}",
        f"- Mentions CAF: {caf_count}",
        "",
        "---",
        "",
    ]

    for slug in sorted(findings_by_file.keys()):
        data = findings_by_file[slug]
        if "_parse_error" in data:
            lines.append(f"## {slug}\n\n_Parse error — see pass1_findings.json for raw output._\n")
            continue
        if not data["findings"]:
            continue
        speaker = data.get("stakeholder", "?")
        org = data.get("organization", "")
        header = f"## {slug}\n\n**Speaker:** {speaker}"
        if org:
            header += f" — {org}"
        lines.append(header)
        lines.append("")
        for f in data["findings"]:
            sev = f.get("severity", "?")
            cat = f.get("category", "?")
            target = f.get("target_name", "?")
            ttype = f.get("target_type", "?")
            caf = " (CAF)" if f.get("is_caf") else ""
            quote = (f.get("quote") or "").strip().replace("\n", " ")
            lines.append(f"- **{target}** [{ttype}{caf}] · {sev} · {cat}")
            lines.append(f"  > {quote}")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nPass 1 complete:")
    print(f"  {json_path.relative_to(REPO)}")
    print(f"  {md_path.relative_to(REPO)}")


def adjudicate(client) -> None:
    json_path = AUDIT_DIR / "pass1_findings.json"
    if not json_path.exists():
        sys.exit("pass1_findings.json not found — run `scan` first.")
    findings_by_file = json.loads(json_path.read_text(encoding="utf-8"))

    flat = []
    for slug, data in findings_by_file.items():
        if "_parse_error" in data:
            continue
        for f in data.get("findings", []):
            flat.append({
                "source_slug": slug,
                "speaker": data.get("stakeholder", ""),
                **f,
            })

    if not flat:
        print("No findings to adjudicate.")
        return

    prompt = f"""<findings_count>{len(flat)}</findings_count>

<findings>
{json.dumps(flat, indent=2, ensure_ascii=False)}
</findings>"""

    print(f"Sending {len(flat)} finding(s) to {ADJUDICATE_MODEL} …")
    msg = client.messages.create(
        model=ADJUDICATE_MODEL,
        max_tokens=8000,
        system=ADJUDICATE_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    out = msg.content[0].text
    md_path = AUDIT_DIR / "pass2_review.md"
    md_path.write_text(out, encoding="utf-8")
    print(f"Pass 2 complete: {md_path.relative_to(REPO)}")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_scan = sub.add_parser("scan", help="Pass 1: per-file Haiku classifier")
    p_scan.add_argument("--only", nargs="*", help="Optional: limit to these slugs (no .md)")

    sub.add_parser("adjudicate", help="Pass 2: Sonnet groups + recommends per target")

    args = parser.parse_args()

    load_env()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY not set (checked keys.env and env).")
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    if args.cmd == "scan":
        findings = scan(client, only=args.only)
        write_pass1_outputs(findings)
    elif args.cmd == "adjudicate":
        adjudicate(client)


if __name__ == "__main__":
    main()
