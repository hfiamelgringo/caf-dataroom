"""Produce two CSVs the team can act on:

  audit/mailmerge_contacts.csv — every interviewee with name, email (blank
                                   if not found yet), interview info, and
                                   the source the email came from.
  audit/missing_emails_request.csv — the subset where email is still blank,
                                       formatted to send to Mark/Rigo as the
                                       gap list to fill from their calendars.
"""
import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
AUDIT = REPO / "audit"
EMAIL_STATUS = AUDIT / "email_status.json"
DATAROOM_BASE = "https://discerning-mindfulness-production-a5fa.up.railway.app/interviews/"

# Emails we recovered from the user's Google Calendar (Airtable was missing them).
# Keyed by lowercase Person name as it appears in Airtable's "People" table.
CALENDAR_FINDS: dict[str, str] = {
    "betsabe franco": "betsabe.franco@cnbs.gob.hn",
    "daniel granada": "daniel@pomonaimpact.com",
    "daniel gallo": "dgallo@gunder.com",
    "jacob stern": "jacob@albedo-solar.com",
    "alex macfarlan": "alex@albedo-solar.com",
    "dan gray": "dan@joinodin.com",
    "israel garcía ballesteros": "ig@startuplinks.world",
    "israel garcia ballesteros": "ig@startuplinks.world",
    "peter walker": "peter.walker@carta.com",
    "aline murlick": "aline.m@startse.com",
    "iyinoluwa aboyeji": "e@future.africa",
    "patrick menendez": "patrick.menendez@femsa.com",
    "samuel hernandez stanford": "samuel.hernandez@colmex.mx",
    "samuel hernandez": "samuel.hernandez@colmex.mx",
    "agostina martino": "agostina.martino@technologywithpurpose.org",
    "santiago zavala": "santiago@500.co",
    "michael jacobo": "michael@venture.do",
    "barnaby dorfman": "bdorfman@gmail.com",
}

# Interviews where Airtable had no Stakeholders linked but we found participants on the calendar.
# Each entry produces an additional row in the contacts CSV.
EXTRA_PARTICIPANTS: dict[str, list[dict]] = {
    "2026-04-09-ruta-medellin": [
        {"name": "Santiago Henao", "email": "direccion.negocios@rutanmedellin.org", "source": "calendar"},
    ],
}


def main():
    AUDIT.mkdir(exist_ok=True)
    data = json.loads(EMAIL_STATUS.read_text(encoding="utf-8"))

    contacts_rows = []
    missing_rows = []

    for r in data:
        slug = r["slug"]
        date = slug[:10]
        url = f"{DATAROOM_BASE}{slug}/"
        label = r.get("stakeholder_label", "")
        org = r.get("organization", "")
        anonymous = r.get("anonymous", False)

        rows_for_this = []
        for p in r.get("people", []):
            airtable_email = (p.get("email") or "").strip()
            cal_email = CALENDAR_FINDS.get((p.get("name") or "").lower().strip(), "")
            email = airtable_email or cal_email
            source = "airtable" if airtable_email else ("calendar" if cal_email else "")
            rows_for_this.append({
                "name": p.get("name", ""),
                "email": email,
                "source": source,
                "interview_date": date,
                "interview_slug": slug,
                "interview_url": url,
                "stakeholder_label": label,
                "organization": org,
                "anonymous": anonymous,
                "linkedin": p.get("linkedin", ""),
            })

        for extra in EXTRA_PARTICIPANTS.get(slug, []):
            rows_for_this.append({
                "name": extra["name"],
                "email": extra.get("email", ""),
                "source": extra.get("source", ""),
                "interview_date": date,
                "interview_slug": slug,
                "interview_url": url,
                "stakeholder_label": label,
                "organization": org,
                "anonymous": anonymous,
                "linkedin": "",
            })

        if not rows_for_this:
            # Interview with no resolved participants at all
            rows_for_this.append({
                "name": "(no participants resolved)",
                "email": "",
                "source": "",
                "interview_date": date,
                "interview_slug": slug,
                "interview_url": url,
                "stakeholder_label": label,
                "organization": org,
                "anonymous": anonymous,
                "linkedin": "",
            })

        for row in rows_for_this:
            contacts_rows.append(row)
            if not row["email"]:
                missing_rows.append(row)

    fieldnames = [
        "name", "email", "source",
        "interview_date", "interview_slug", "interview_url",
        "stakeholder_label", "organization", "anonymous", "linkedin",
    ]

    contacts_path = AUDIT / "mailmerge_contacts.csv"
    with contacts_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(contacts_rows)

    missing_path = AUDIT / "missing_emails_request.csv"
    with missing_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(missing_rows)

    have_email = sum(1 for r in contacts_rows if r["email"])
    print(f"Wrote {contacts_path.relative_to(REPO)} — {len(contacts_rows)} rows ({have_email} with email)")
    print(f"Wrote {missing_path.relative_to(REPO)} — {len(missing_rows)} rows still missing email")


if __name__ == "__main__":
    main()
