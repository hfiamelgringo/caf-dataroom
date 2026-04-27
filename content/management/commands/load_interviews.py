import json

import markdown
from django.conf import settings
from django.core.management.base import BaseCommand

from content.models import Interview


class Command(BaseCommand):
    help = "Load interview summaries from content_data/interviews.json"

    def handle(self, *args, **options):
        path = settings.BASE_DIR / "content_data" / "interviews.json"
        if not path.exists():
            self.stderr.write(f"Interviews file not found: {path}")
            return

        records = json.loads(path.read_text(encoding="utf-8"))
        md = markdown.Markdown(extensions=["tables", "fenced_code"])
        loaded = 0

        for r in records:
            md.reset()
            body_html = md.convert(r["body_markdown"])

            interview, created = Interview.objects.update_or_create(
                slug=r["slug"],
                defaults={
                    "title": r["title"],
                    "date": r["date"],
                    "country_code": r.get("country_code", ""),
                    "country_label": r.get("country_label", ""),
                    "stakeholder_name": r["stakeholder_name"],
                    "stakeholder_role": r.get("stakeholder_role", ""),
                    "organization": r.get("organization", ""),
                    "topic_tag": r.get("topic_tag", ""),
                    "body_markdown": r["body_markdown"],
                    "body_html": body_html,
                    "is_public": r.get("is_public", True),
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"  {action}: {interview.title}")
            loaded += 1

        self.stdout.write(self.style.SUCCESS(f"\nLoaded {loaded} interviews"))
