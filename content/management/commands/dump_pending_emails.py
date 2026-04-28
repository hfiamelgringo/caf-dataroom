"""Dump JSON of consent emails pending to be drafted/sent.

Used to drive the Gmail MCP create_draft workflow:
- Filters: email != "", manual_outreach=False, sent_at IS NULL
- Dedupes by recipient_token (one entry per recipient even if they have
  multiple interview rows)
- Renders the email body using `consent_email.txt`
- Outputs JSON array to stdout: [{token, name, email, subject, body, review_url}, ...]

Does NOT mark anything sent — that's `mark_sent`'s job, run after the user
confirms drafts have been sent from Gmail.
"""
import json
from datetime import date, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from content.models import InterviewConsent


class Command(BaseCommand):
    help = "Dump JSON of consent emails ready to be drafted via the Gmail MCP"

    def add_arguments(self, parser):
        parser.add_argument("--only-email", default="",
                            help="Restrict to a single email address (test mode)")
        parser.add_argument("--include-manual-outreach", action="store_true",
                            help="Override the manual_outreach flag and include those rows too")
        parser.add_argument("--deadline-days", type=int, default=7,
                            help="Days from today shown as the response deadline (default 7)")

    def handle(self, *args, **opts):
        qs = InterviewConsent.objects.exclude(email="").filter(sent_at__isnull=True)
        if not opts["include_manual_outreach"]:
            qs = qs.exclude(manual_outreach=True)
        if opts["only_email"]:
            qs = qs.filter(email=opts["only_email"])

        seen = set()
        recipients = []
        for c in qs.order_by("recipient_token", "interview_slug"):
            if c.recipient_token in seen:
                continue
            seen.add(c.recipient_token)
            recipients.append(c)

        deadline = (date.today() + timedelta(days=opts["deadline_days"])).strftime("%B %d, %Y")
        site_url = settings.SITE_URL.rstrip("/")
        subject = "Quick sign-off: how should we credit you in our CAF report?"

        out = []
        for c in recipients:
            review_url = f"{site_url}{c.get_review_url()}"
            interview_count = InterviewConsent.objects.filter(
                recipient_token=c.recipient_token
            ).count()
            body = render_to_string("content/consent_email.txt", {
                "name": c.name,
                "review_url": review_url,
                "deadline": deadline,
                "interview_count": interview_count,
            })
            out.append({
                "token": c.recipient_token,
                "name": c.name,
                "email": c.email,
                "subject": subject,
                "body": body,
                "review_url": review_url,
                "interview_count": interview_count,
            })

        self.stdout.write(json.dumps(out, indent=2, ensure_ascii=False))
