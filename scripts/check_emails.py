"""Build an email-status report for the 42 published interviews.

For each interview, we:
  1. find its Airtable Meeting Note via scripts/phase2_manifest.json
  2. pull the linked Stakeholders (People records)
  3. report per-person: name, email (yes/no), org

Output: audit/email_status.md (human-scannable) + audit/email_status.json
(machine-readable for downstream outreach scripts).
"""
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KEYS = REPO / "keys.env"
MANIFEST = REPO / "scripts" / "phase2_manifest.json"
INDEX = REPO / "content_data" / "transcripts" / "index.json"
OUT_DIR = REPO / "audit"
OUT_DIR.mkdir(exist_ok=True)


def load_env():
    for line in KEYS.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def main():
    load_env()
    from pyairtable import Api

    api = Api(os.environ["AIRTABLE_PAT"])
    base = api.base("appVMgNUokH0882lO")

    # --- Pull all People once and index by record id
    people = base.table("People").all(
        fields=["Name", "Mail", "Linkedin", "Phone Number", "Status"]
    )
    people_by_id = {p["id"]: p["fields"] for p in people}
    print(f"Loaded {len(people_by_id)} People")

    # --- Pull all Meeting Notes once and index by record id
    notes = base.table("Meeting Notes").all(
        fields=["Name", "Stakeholders", "Fecha"]
    )
    notes_by_id = {n["id"]: n["fields"] for n in notes}
    print(f"Loaded {len(notes_by_id)} Meeting Notes")

    # --- Manifest: slug-prefix → airtable note id
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    # Map output_filename (without .txt) → airtable_id
    fn_to_aid = {m["output_filename"].rsplit(".", 1)[0]: m["airtable_id"] for m in manifest}
    # Also map by date prefix as a fallback
    date_to_aids: dict[str, list[str]] = {}
    for m in manifest:
        date_to_aids.setdefault(m["fecha"], []).append(m["airtable_id"])

    # --- Walk our published index and resolve each transcript to its airtable note
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    report = []

    for entry in index:
        slug = entry["name"]
        date_prefix = slug[:10]  # YYYY-MM-DD
        stakeholder_label = entry.get("stakeholder", "")
        organization = entry.get("organization", "")
        anonymous = bool(entry.get("anonymous"))

        # Resolve airtable_id
        aid = None
        # Try direct slug match (some slugs share prefix with output_filename)
        for fn, candidate_aid in fn_to_aid.items():
            if fn.startswith(date_prefix):
                # Take first match — refine if multiple same-date
                if aid is None:
                    aid = candidate_aid
                # If our slug clearly matches (substring overlap), prefer it
                slug_keywords = set(slug[11:].split("-"))
                fn_keywords = set(fn[11:].split("-"))
                if slug_keywords & fn_keywords:
                    aid = candidate_aid
                    break

        people_for_this = []
        if aid and aid in notes_by_id:
            stake_ids = notes_by_id[aid].get("Stakeholders") or []
            for pid in stake_ids:
                pfields = people_by_id.get(pid, {})
                people_for_this.append({
                    "id": pid,
                    "name": pfields.get("Name", "(unnamed)"),
                    "email": pfields.get("Mail", ""),
                    "linkedin": pfields.get("Linkedin", ""),
                    "status": pfields.get("Status", ""),
                })

        report.append({
            "slug": slug,
            "stakeholder_label": stakeholder_label,
            "organization": organization,
            "anonymous": anonymous,
            "airtable_id": aid,
            "stakeholders_resolved": len(people_for_this),
            "people": people_for_this,
        })

    # --- Write JSON
    json_path = OUT_DIR / "email_status.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    # --- Write markdown
    lines = ["# Interviewee email status\n"]
    n_total = len(report)
    n_no_aid = sum(1 for r in report if not r["airtable_id"])
    n_no_people = sum(1 for r in report if not r["people"])
    n_anon = sum(1 for r in report if r["anonymous"])
    all_people = [p for r in report for p in r["people"]]
    n_with_email = sum(1 for p in all_people if p["email"])
    n_without_email = sum(1 for p in all_people if not p["email"])

    lines += [
        f"- Interviews: **{n_total}**  · anonymous: **{n_anon}**",
        f"- Could not resolve Airtable Meeting Note: **{n_no_aid}**",
        f"- Resolved but no linked Stakeholders: **{n_no_people}**",
        f"- Total stakeholder People resolved: **{len(all_people)}**",
        f"- Have email on file: **{n_with_email}**",
        f"- Missing email: **{n_without_email}**",
        "",
        "---",
        "",
    ]

    for r in sorted(report, key=lambda x: x["slug"]):
        lines.append(f"## {r['slug']}")
        lines.append(f"**Listed as:** {r['stakeholder_label']}  \n**Org:** {r['organization'] or '(none)'}  \n**Anonymous:** {r['anonymous']}")
        if not r["airtable_id"]:
            lines.append(f"\n_⚠ no Airtable Meeting Note resolved_\n")
        elif not r["people"]:
            lines.append(f"\n_⚠ Meeting Note found ({r['airtable_id']}) but no Stakeholders linked_\n")
        else:
            lines.append("")
            for p in r["people"]:
                tag = "✓" if p["email"] else "✗ no email"
                lines.append(f"- **{p['name']}** — {tag} {p['email']}")
            lines.append("")
        lines.append("---\n")

    md_path = OUT_DIR / "email_status.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {json_path.relative_to(REPO)}")
    print(f"Wrote {md_path.relative_to(REPO)}")
    print(f"Summary: {n_with_email}/{len(all_people)} stakeholders have email; {n_no_aid} interviews unresolved")


if __name__ == "__main__":
    main()
