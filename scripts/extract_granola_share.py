"""Extract title + body text from a public Granola share URL.

Granola share pages are public (no auth) but content is embedded in escaped
ProseMirror-like JSON inside HTML. We pull all `"text":"..."` values that look
like real prose (skip the noise) and reconstruct paragraphs.

Usage: python scripts/extract_granola_share.py <granola_url>
"""
import json
import re
import sys

import requests


def fetch(url: str) -> str:
    # Granola returns 500 on share pages but the body still contains full content
    resp = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; caf-dataroom)"},
        timeout=30,
        allow_redirects=True,
    )
    return resp.text


def parse_share(html: str) -> dict:
    title_m = re.search(r"<title[^>]*>([^<]+)</title>", html)
    title = title_m.group(1) if title_m else ""

    desc_m = re.search(r'name="description"\s+content="([^"]+)"', html)
    desc = desc_m.group(1) if desc_m else ""

    og_desc_m = re.search(r'og:description"\s+content="([^"]+)"', html)
    og_desc = og_desc_m.group(1) if og_desc_m else ""

    # Date is encoded in the og:image URL — stop at the first & (escaped &)
    date_m = re.search(r"date=([^&\\]+?)(?:\\u0026|&|\\\\)", html)
    date = ""
    if date_m:
        from urllib.parse import unquote
        date = unquote(date_m.group(1).replace("+", " "))

    # Body content: scan for "text":"..." patterns inside ProseMirror JSON.
    # These appear unescaped (\" is literal backslash-quote) inside the
    # outer escaped JSON in self.__next_f.push, which itself sits inside HTML.
    # The content also appears in ProseMirror format with HTML entities (< etc.)
    # Strategy: collect all unique substantive "text":"..." matches.
    text_chunks = []
    seen = set()
    # In the page source, JSON is escaped once: \"text\":\"...\"
    # The content between escaped quotes can contain \\" (escaped escaped quote)
    # or other backslash escapes. We capture lazily, then JSON-decode.
    pattern = re.compile(r'\\"text\\":\\"((?:[^"\\]|\\\\.)*?)\\"')
    for m in pattern.finditer(html):
        raw = m.group(1)
        # Un-escape one level: \\\\ -> \\, \\" -> ", \\n -> \n, \\u00xx -> char
        try:
            decoded = json.loads('"' + raw.replace("\\\\", "\\\\").replace('\\"', '\\"') + '"')
        except json.JSONDecodeError:
            # Fallback: strip backslashes from common escapes
            decoded = (
                raw.replace("\\\\n", "\n")
                .replace("\\\\\"", '"')
                .replace("\\\\u003c", "<")
                .replace("\\\\u003e", ">")
                .replace("\\\\u0026", "&")
                .replace("\\\\", "")
            )
        decoded = decoded.strip()
        # Skip very short, non-prose noise
        if len(decoded) < 4:
            continue
        if decoded in seen:
            continue
        seen.add(decoded)
        text_chunks.append(decoded)

    return {
        "title": title,
        "description_meta": desc,
        "summary_preview": og_desc,
        "date": date,
        "body_chunks": text_chunks,
    }


def main():
    url = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else "scripts/extract_test.txt"
    html = fetch(url)
    parsed = parse_share(html)
    lines = [
        f"TITLE: {parsed['title']}",
        f"DATE:  {parsed['date']}",
        f"AUTHOR: {parsed['description_meta']}",
        f"SUMMARY PREVIEW: {parsed['summary_preview'][:300]}",
        f"BODY CHUNKS: {len(parsed['body_chunks'])}",
        "",
        "=== RECONSTRUCTED BODY ===",
    ]
    for c in parsed["body_chunks"]:
        lines.append(f"- {c}")
    from pathlib import Path
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path} ({len(parsed['body_chunks'])} body chunks)")


if __name__ == "__main__":
    main()
