"""Stamp sent_at on consent rows after drafts have been actually sent from Gmail.

Use after sending the drafts created via the Gmail MCP. Idempotent.

  python manage.py mark_sent --token abc123def456
  python manage.py mark_sent --token a,b,c          # comma-separated
  python manage.py mark_sent --all-pending          # stamp every row that has email + no sent_at
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from content.models import InterviewConsent


class Command(BaseCommand):
    help = "Stamp sent_at on consent rows after drafts have been sent"

    def add_arguments(self, parser):
        parser.add_argument("--token", default="",
                            help="recipient_token (or comma-separated tokens) to mark sent")
        parser.add_argument("--all-pending", action="store_true",
                            help="Mark every row with email != '' and sent_at IS NULL")
        parser.add_argument("--include-manual-outreach", action="store_true",
                            help="Override the manual_outreach exclusion (rare)")

    def handle(self, *args, **opts):
        if not opts["token"] and not opts["all_pending"]:
            self.stderr.write("Provide --token <token>[,<token>...] or --all-pending")
            return

        qs = InterviewConsent.objects.filter(sent_at__isnull=True).exclude(email="")
        if not opts["include_manual_outreach"]:
            qs = qs.exclude(manual_outreach=True)

        if opts["token"]:
            tokens = [t.strip() for t in opts["token"].split(",") if t.strip()]
            qs = qs.filter(recipient_token__in=tokens)

        now = timezone.now()
        # Stamp every pending row for the matched recipients
        recipient_tokens = set(qs.values_list("recipient_token", flat=True))
        n = InterviewConsent.objects.filter(
            recipient_token__in=recipient_tokens, sent_at__isnull=True
        ).update(sent_at=now)
        self.stdout.write(self.style.SUCCESS(
            f"Stamped sent_at on {n} row(s) across {len(recipient_tokens)} recipient(s)"
        ))
