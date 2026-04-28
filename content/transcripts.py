"""Flat-file transcript library reader.

Source of truth: content_data/transcripts/index.json + content_data/transcripts/*.md.

This module is intentionally Django-light — only uses settings.BASE_DIR — so it stays
portable if the project moves to a static-site generator or serverless setup.

Uses a custom minimal frontmatter parser because some values (descriptions) contain
unquoted colons that break PyYAML. The structure of our .md files is fixed and known,
so a regex-based reader is more robust here than a general YAML parser.
"""
import json
import re
from pathlib import Path

from django.conf import settings


def _parse_frontmatter_value(value: str):
    v = value.strip()
    if v == "":
        return ""
    if v.lower() == "true":
        return True
    if v.lower() == "false":
        return False
    if v.startswith("[") and v.endswith("]"):
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            pass
    # Strip surrounding quotes if present
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    return v


def _parse_md(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, flags=re.DOTALL)
    if not m:
        return {}, text
    fm_block, body = m.group(1), m.group(2)
    metadata: dict = {}
    for line in fm_block.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        # Match `key: rest-of-line` (only the FIRST colon is the key separator)
        km = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$", line)
        if not km:
            continue
        key, value = km.group(1), km.group(2)
        metadata[key] = _parse_frontmatter_value(value)
    return metadata, body


def transcripts_dir() -> Path:
    return Path(settings.BASE_DIR) / "content_data" / "transcripts"


def index_path() -> Path:
    return transcripts_dir() / "index.json"


def _apply_anonymization(entry: dict) -> dict:
    """If anonymous=True, replace identifying fields with the anonymized label.

    The real name stays in the source .md file as a private reference but is
    never returned by this loader to view code or chat code.
    """
    if not entry.get("anonymous"):
        return entry
    label = (entry.get("anonymized_label") or "Anonymous stakeholder").strip()
    sanitized = {**entry}
    sanitized["stakeholder"] = label
    sanitized["role"] = ""
    sanitized["organization"] = ""
    return sanitized


def _extract_teaser(slug: str, max_chars: int = 320) -> str:
    """Pull the first paragraph after `## Executive Summary` from the .md body."""
    path = transcripts_dir() / f"{slug}.md"
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"##\s*Executive Summary\s*\n+(.+?)(?=\n##|\Z)", text, flags=re.DOTALL | re.IGNORECASE)
    if not m:
        return ""
    para = m.group(1).strip().split("\n\n", 1)[0].strip()
    para = re.sub(r"\s+", " ", para)
    if len(para) > max_chars:
        cut = para[:max_chars].rsplit(" ", 1)[0]
        return cut + "…"
    return para


def _last_name_key(entry: dict) -> tuple:
    """Sort key: last name of the BASE stakeholder (before any " — " topic suffix),
    then session number for multi-session interviews. Empty names sort last."""
    name = (entry.get("stakeholder") or "").strip()
    if not name:
        return (1, "", "", 0, "")
    base = re.split(r"\s+—\s+", name, maxsplit=1)[0].strip() or name
    last = base.split()[-1].lower()
    session_match = re.search(r"\((\d+)\s+of\s+\d+\s+interviews?\)", name)
    session = int(session_match.group(1)) if session_match else 0
    return (0, last, base.lower(), session, name.lower())


def load_index() -> list[dict]:
    """Return all index.json entries with anonymization applied. Sorted alphabetically by stakeholder last name."""
    entries = json.loads(index_path().read_text(encoding="utf-8"))
    entries = [_apply_anonymization(e) for e in entries]
    for e in entries:
        e["teaser"] = _extract_teaser(e.get("name", ""))
    entries.sort(key=_last_name_key)
    return entries


def load_transcript(slug: str) -> dict | None:
    """Read one transcript .md by slug. Returns dict with frontmatter + 'body' field, or None."""
    path = transcripts_dir() / f"{slug}.md"
    if not path.exists():
        return None
    metadata, body = _parse_md(path.read_text(encoding="utf-8"))
    entry = dict(metadata)
    entry["name"] = entry.get("name", slug)
    entry["body"] = body
    return _apply_anonymization(entry)


def collect_filter_options(entries: list[dict], min_topic_count: int = 2) -> dict:
    """Build filter values for chips.

    Topics are noisy (LLM-generated; many one-offs). Show only topics that appear
    in at least `min_topic_count` entries to keep the filter row scannable.
    Countries and sources are always shown when present.
    """
    from collections import Counter
    countries = set()
    topic_counts = Counter()
    sources = set()
    for e in entries:
        for c in e.get("countries", []) or []:
            if c:
                countries.add(c)
        for t in e.get("topics", []) or []:
            if t:
                topic_counts[t] += 1
        if e.get("source"):
            sources.add(e["source"])
    common_topics = sorted(t for t, n in topic_counts.items() if n >= min_topic_count)
    return {
        "countries": sorted(countries),
        "topics": common_topics,
        "sources": sorted(sources),
        "topic_total": len(topic_counts),
        "topic_shown": len(common_topics),
        "topic_hidden": len(topic_counts) - len(common_topics),
    }
