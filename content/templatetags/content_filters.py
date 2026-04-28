import re
import markdown as _markdown
from django import template
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def excerpt(html, word_count=25):
    """Strip HTML tags and headings, return first N words of body text."""
    text = strip_tags(html)
    # Remove lines that look like headings (short lines followed by longer content)
    lines = text.split('\n')
    body_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip short lines that are likely headings (under 60 chars, no period)
        if len(line) < 60 and not line.endswith('.'):
            continue
        body_lines.append(line)
    body = ' '.join(body_lines)
    words = body.split()
    if len(words) > word_count:
        return ' '.join(words[:word_count]) + ' ...'
    return body


@register.filter
def render_markdown(md_text):
    """Render a markdown string to HTML."""
    if not md_text:
        return ""
    return mark_safe(_markdown.markdown(md_text, extensions=["tables", "fenced_code"]))


@register.filter
def strip_leading_headings(html):
    """Remove all heading tags that appear before the first non-heading content."""
    result = re.sub(r'^\s*(<h[123][^>]*>.*?</h[123]>\s*)+', '', html.strip(), count=1, flags=re.DOTALL)
    return mark_safe(result)
