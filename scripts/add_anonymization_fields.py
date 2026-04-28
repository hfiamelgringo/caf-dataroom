"""Add anonymous + anonymized_label fields to every transcript frontmatter (idempotent)."""
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TRANSCRIPTS = REPO / "content_data" / "transcripts"
INDEX = TRANSCRIPTS / "index.json"


def add_fields_to_md(path: Path) -> bool:
    """Insert `anonymous: false` after `topics: ...` if not present. Returns True if modified."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^(---\n)(.*?)(\n---\n)(.*)$", text, flags=re.DOTALL)
    if not m:
        return False
    header_open, frontmatter, header_close, body = m.groups()
    if "anonymous:" in frontmatter:
        return False  # already has it
    # Insert after topics line, or at end of frontmatter if no topics line
    lines = frontmatter.splitlines()
    new_lines = []
    inserted = False
    for line in lines:
        new_lines.append(line)
        if not inserted and line.startswith("topics:"):
            new_lines.append("anonymous: false")
            new_lines.append('anonymized_label: ""')
            inserted = True
    if not inserted:
        new_lines.append("anonymous: false")
        new_lines.append('anonymized_label: ""')
    new_frontmatter = "\n".join(new_lines)
    path.write_text(header_open + new_frontmatter + header_close + body, encoding="utf-8")
    return True


def add_fields_to_index() -> int:
    entries = json.loads(INDEX.read_text(encoding="utf-8"))
    changed = 0
    for e in entries:
        if "anonymous" not in e:
            e["anonymous"] = False
            e["anonymized_label"] = ""
            changed += 1
    if changed:
        INDEX.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    return changed


def main():
    md_files = sorted(TRANSCRIPTS.glob("*.md"))
    md_changed = 0
    for f in md_files:
        if add_fields_to_md(f):
            md_changed += 1
    idx_changed = add_fields_to_index()
    print(f".md files modified: {md_changed} / {len(md_files)}")
    print(f"index.json entries modified: {idx_changed}")


if __name__ == "__main__":
    main()
