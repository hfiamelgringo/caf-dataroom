import re

import markdown
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from content.models import Section

SECTION_TYPE_MAP = {
    "introduction": "intro",
    "executive_summary": "executive_summary",
    "recommendation": "recommendation",
    "insight": "insight",
    "insights": "insight",
    "small_idea": "small_idea",
    "small_ideas": "small_idea",
    "country": "country",
    "country_profile": "country",
    "annex": "annex",
    "annexes": "annex",
    "reference": "reference",
    "references": "reference",
}


def parse_header(content):
    meta = {}
    for match in re.finditer(r"<!--\s*(\w+):\s*(.*?)\s*-->", content):
        meta[match.group(1)] = match.group(2).strip()
    body_start = 0
    for match in re.finditer(r"<!--.*?-->\n?", content):
        body_start = match.end()
    body = content[body_start:].strip()
    return meta, body


class Command(BaseCommand):
    help = "Load markdown section files into the Section model"

    def handle(self, *args, **options):
        sections_dir = settings.BASE_DIR / "content_data" / "sections"
        if not sections_dir.exists():
            self.stderr.write(f"Sections directory not found: {sections_dir}")
            return

        md = markdown.Markdown(extensions=["tables", "toc", "fenced_code"])
        files = sorted(sections_dir.glob("*.md"))
        loaded = 0

        for f in files:
            content = f.read_text(encoding="utf-8")
            meta, body = parse_header(content)

            title = meta.get("title", f.stem.replace("_", " ").title())
            raw_type = meta.get("section_type", "intro")
            section_type = SECTION_TYPE_MAP.get(raw_type, raw_type)
            order = int(meta.get("order", 0))
            country_code = meta.get("country_code", "").strip()

            slug = slugify(title)[:50]

            md.reset()
            body_html = md.convert(body)

            section, created = Section.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "body_markdown": body,
                    "body_html": body_html,
                    "section_type": section_type,
                    "order": order,
                    "country_code": country_code,
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"  {action}: {title} [{section_type}]")
            loaded += 1

        self.stdout.write(self.style.SUCCESS(f"\nLoaded {loaded} sections"))
