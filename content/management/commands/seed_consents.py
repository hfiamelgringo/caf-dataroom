"""Seed InterviewConsent rows from audit/mailmerge_contacts.csv.

For each CSV row:
- Find the interview transcript markdown (content_data/transcripts/<slug>.md)
- Snapshot the full publishable body (Executive Summary, Stakeholder Background,
  Key Findings, Recommendations, Key Takeaways) — both the markdown source
  (used to prefill the editor) and the rendered HTML (used to display).
- Idempotent: keyed on (email, interview_slug); rows with no email are
  keyed on (name, interview_slug) so missing-email entries are tracked.

Recipient grouping:
- All rows for the same email share a `recipient_token`. The review URL uses
  that token, so multi-interview people see all their interviews on one page.
- Anyone with >1 row for the same email is auto-flagged `manual_outreach=True`
  so they're excluded from the bulk email send (handled via WhatsApp etc.).
  Their review URL still works.

Run again after Mark/Rodrigo provide missing emails — it'll fill in the
email field on existing rows and re-group recipient_tokens accordingly.
"""
import csv
import uuid
from collections import defaultdict
from pathlib import Path

import markdown as md_lib
from django.conf import settings
from django.core.management.base import BaseCommand

from content.models import InterviewConsent
from content import transcripts as tx


class Command(BaseCommand):
    help = "Seed InterviewConsent rows from audit/mailmerge_contacts.csv"

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            default=str(Path(settings.BASE_DIR) / "audit" / "mailmerge_contacts.csv"),
            help="Path to the contacts CSV (default: audit/mailmerge_contacts.csv)",
        )
        parser.add_argument(
            "--refresh-snapshots",
            action="store_true",
            help="Re-render copy_snapshot_html/markdown from transcripts even on existing rows",
        )

    def handle(self, *args, **opts):
        csv_path = Path(opts["csv"])
        if not csv_path.exists():
            self.stderr.write(f"CSV not found: {csv_path}")
            return

        # Pass 1: read CSV, count emails to identify multi-interview recipients
        rows_data = []
        email_count = defaultdict(int)
        with csv_path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                name = (row.get("name") or "").strip()
                email = (row.get("email") or "").strip()
                slug = (row.get("interview_slug") or "").strip()
                if not name or not slug or name.startswith("("):
                    continue
                org = (row.get("organization") or "").strip()
                # Multi-stakeholder sessions often leave `organization` empty and
                # put the company in `stakeholder_label` (e.g. the Venture.do row
                # for the joint session). Fall back to the label when the
                # organization column is empty and the label isn't just the
                # person's own name.
                if not org:
                    label = (row.get("stakeholder_label") or "").strip()
                    if label and label.lower() != name.lower():
                        org = label
                rows_data.append({
                    "name": name,
                    "email": email,
                    "slug": slug,
                    "organization": org,
                    "interview_url": (row.get("interview_url") or "").strip(),
                })
                if email:
                    email_count[email] += 1

        # Pass 2: build/update consent rows
        created = updated = skipped_no_transcript = 0
        missing_email = []
        missing_summary = []

        # Resolve recipient_token per email: re-use any existing token for that email
        token_by_email = {}
        for email in email_count:
            existing = (
                InterviewConsent.objects.filter(email=email)
                .exclude(recipient_token="")
                .values_list("recipient_token", flat=True)
                .first()
            )
            token_by_email[email] = existing or uuid.uuid4().hex

        for d in rows_data:
            entry = tx.load_transcript(d["slug"])
            if entry is None:
                self.stderr.write(f"  ! transcript missing for slug={d['slug']} ({d['name']})")
                skipped_no_transcript += 1
                continue

            body_md = (entry.get("body") or "").strip()
            if not body_md:
                missing_summary.append(f"{d['name']} ({d['slug']})")
                summary_html = ""
                summary_md = ""
            else:
                summary_md = body_md
                summary_html = md_lib.markdown(body_md, extensions=["tables", "fenced_code"])

            email = d["email"]
            is_multi = email and email_count[email] > 1
            recipient_token = token_by_email.get(email) or uuid.uuid4().hex

            lookup = {"interview_slug": d["slug"]}
            if email:
                lookup["email"] = email
            else:
                lookup["name"] = d["name"]
                lookup["email"] = ""

            consent = InterviewConsent.objects.filter(**lookup).first()
            if consent is None:
                InterviewConsent.objects.create(
                    name=d["name"],
                    email=email,
                    organization=d["organization"],
                    interview_slug=d["slug"],
                    interview_url=d["interview_url"],
                    recipient_token=recipient_token,
                    copy_snapshot_html=summary_html,
                    copy_snapshot_markdown=summary_md,
                    manual_outreach=bool(is_multi),
                )
                created += 1
            else:
                fields = []
                if not consent.email and email:
                    consent.email = email
                    fields.append("email")
                if consent.name != d["name"]:
                    consent.name = d["name"]
                    fields.append("name")
                if consent.organization != d["organization"]:
                    consent.organization = d["organization"]
                    fields.append("organization")
                if consent.interview_url != d["interview_url"]:
                    consent.interview_url = d["interview_url"]
                    fields.append("interview_url")
                if email and consent.recipient_token != recipient_token:
                    consent.recipient_token = recipient_token
                    fields.append("recipient_token")
                if consent.manual_outreach != bool(is_multi):
                    consent.manual_outreach = bool(is_multi)
                    fields.append("manual_outreach")
                if opts["refresh_snapshots"]:
                    if consent.copy_snapshot_html != summary_html:
                        consent.copy_snapshot_html = summary_html
                        fields.append("copy_snapshot_html")
                    if consent.copy_snapshot_markdown != summary_md:
                        consent.copy_snapshot_markdown = summary_md
                        fields.append("copy_snapshot_markdown")
                if fields:
                    consent.save(update_fields=fields)
                    updated += 1

            if not email:
                missing_email.append(f"{d['name']} ({d['slug']})")

        # Backfill copy_snapshot_markdown on rows that don't have it yet (older data)
        # Done above as part of the per-row update.

        self.stdout.write(self.style.SUCCESS(f"Created: {created}"))
        self.stdout.write(self.style.SUCCESS(f"Updated: {updated}"))
        multi_count = sum(1 for c in email_count.values() if c > 1)
        if multi_count:
            self.stdout.write(self.style.WARNING(
                f"Multi-interview recipients (auto-flagged manual_outreach=True): {multi_count}"
            ))
            for e, n in email_count.items():
                if n > 1:
                    self.stdout.write(f"  - {e} ({n} interviews)")
        if missing_email:
            self.stdout.write(self.style.WARNING(f"Rows with no email ({len(missing_email)}):"))
            for m in missing_email:
                self.stdout.write(f"  - {m}")
        if missing_summary:
            self.stdout.write(self.style.WARNING(f"Rows missing transcript body ({len(missing_summary)}):"))
            for m in missing_summary:
                self.stdout.write(f"  - {m}")
        if skipped_no_transcript:
            self.stdout.write(self.style.WARNING(f"Skipped (transcript file not found): {skipped_no_transcript}"))
