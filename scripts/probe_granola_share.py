"""Probe a Granola share URL to see what content is recoverable from the public HTML."""
import re
import sys
from pathlib import Path

html_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/granola_probe.html"
html = Path(html_path).read_text(encoding="utf-8", errors="replace")

# Title + og description
title = re.search(r"<title[^>]*>([^<]+)</title>", html)
og_desc = re.search(r'og:description"\s+content="([^"]+)"', html)
print(f"TITLE: {title.group(1) if title else '?'}")
print(f"OG_DESC: {og_desc.group(1)[:300] if og_desc else '?'}")
print()

# Next.js streams content in self.__next_f.push([1, "..."]) calls
chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, flags=re.DOTALL)
print(f"chunks: {len(chunks)}, total chars: {sum(len(c) for c in chunks)}")
print()

# Find long chunks that look like note body
for i, c in enumerate(chunks):
    if len(c) < 3000:
        continue
    try:
        decoded = c.encode().decode("unicode_escape")
    except UnicodeDecodeError:
        decoded = c
    # Heuristic: real note text contains many words, mixed Spanish/English
    words = re.findall(r"\b[a-zA-ZáéíóúñÁÉÍÓÚÑ]{4,}\b", decoded)
    if len(words) > 200:
        print(f"--- chunk {i} ({len(c)} chars, {len(words)} words) ---")
        print(decoded[:3000])
        print("...")
        print()
        break
