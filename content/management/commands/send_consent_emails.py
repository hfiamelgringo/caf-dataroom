"""Send consent-review emails for InterviewConsent rows.

Targets rows with email set, sent_at IS NULL, and manual_outreach=False.
Dedupes by recipient_token so multi-interview recipients still receive only
one email — but those are flagged manual_outreach=True by the seeder anyway,
so they're skipped here too.

Idempotent — once sent_at is stamped on a row, it's skipped on subsequent runs
unless --resend-pending is used.
"""
from datetime import date, timedelta

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone

from content.models import InterviewConsent


class Command(BaseCommand):
    help = "Send consent-review emails to interviewees"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true",
                            help="Print what would be sent; don't send or stamp")
        parser.add_argument("--only-email", default="",
                            help="Send to a single email address (e.g. for self-test)")
        parser.add_argument("--include-manual-outreach", action="store_true",
                            help="Override the manual_outreach flag and send to those rows too")
        parser.add_argument("--resend-pending", action="store_true",
                            help="Re-send to rows that are still 'pending' even if sent_at is set")
        parser.add_argument("--deadline-days", type=int, default=7,
                            help="Days from today shown as the response deadline (default 7)")
        parser.add_argument("--reply-to", default="",
                            help="Reply-To header (defaults to DEFAULT_FROM_EMAIL)")

    def handle(self, *args, **opts):
        qs = InterviewConsent.objects.exclude(email="")
        if not opts["include_manual_outreach"]:
            qs = qs.exclude(manual_outreach=True)
        if opts["only_email"]:
            qs = qs.filter(email=opts["only_email"])
        if opts["resend_pending"]:
            qs = qs.filter(status=InterviewConsent.STATUS_PENDING)
        else:
            qs = qs.filter(sent_at__isnull=True)

        # Dedupe by recipient_token — one email per recipient even if they have multiple rows
        seen_tokens = set()
        recipients = []
        for c in qs.order_by("recipient_token", "interview_slug"):
            if c.recipient_token in seen_tokens:
                continue
            seen_tokens.add(c.recipient_token)
            recipients.append(c)

        deadline = (date.today() + timedelta(days=opts["deadline_days"])).strftime("%B %d, %Y")
        from_email = settings.DEFAULT_FROM_EMAIL
        reply_to = opts["reply_to"] or from_email
        site_url = settings.SITE_URL.rstrip("/")

        sent = 0
        for c in recipients:
            review_url = f"{site_url}{c.get_review_url()}"
            interview_count = InterviewConsent.objects.filter(recipient_token=c.recipient_token).count()
            body = render_to_string("content/consent_email.txt", {
                "name": c.name,
                "review_url": review_url,
                "deadline": deadline,
                "interview_count": interview_count,
            })
            subject = "Quick sign-off: how should we credit you in our CAF report?"

            if opts["dry_run"]:
                self.stdout.write(f"--- DRY RUN: would send to {c.email} ({c.name}) — {interview_count} interview(s)")
                self.stdout.write(f"    review_url: {review_url}")
            else:
                msg = EmailMessage(
                    subject=subject, body=body,
                    from_email=from_email, to=[c.email], reply_to=[reply_to],
                )
                msg.send(fail_silently=False)
                # Stamp sent_at on every row for this recipient
                InterviewConsent.objects.filter(
                    recipient_token=c.recipient_token, sent_at__isnull=True
                ).update(sent_at=timezone.now())
                self.stdout.write(self.style.SUCCESS(f"  sent → {c.email} ({c.name})"))
            sent += 1

        skipped_no_email = InterviewConsent.objects.filter(email="").count()
        skipped_manual = InterviewConsent.objects.filter(manual_outreach=True).count()
        already_sent = InterviewConsent.objects.exclude(email="").filter(sent_at__isnull=False).count()

        action = "Would send" if opts["dry_run"] else "Sent"
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"{action}: {sent} email(s)"))
        self.stdout.write(f"Skipped (no email yet): {skipped_no_email}")
        self.stdout.write(f"Skipped (manual_outreach): {skipped_manual}")
        self.stdout.write(f"Rows already stamped sent_at: {already_sent}")
