"""LLM-router chat for the CAF transcript library.

Two-step flow:
  1. Router pass — scan index.json descriptions, pick 2-4 most relevant slugs.
  2. Answer pass — load picked .md bodies (anonymization applied by tx.load_transcript),
     send to Claude with a system prompt that requires citations.

Falls back to the existing Section corpus (via TF-IDF) for non-interview questions
about the broader report — that path still serves the report content sections.
"""
import json
import re

from anthropic import Anthropic
from django.conf import settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from content import transcripts as tx
from content.models import Section

ROUTER_MODEL = "claude-haiku-4-5-20251001"  # Fast, cheap routing
ANSWER_MODEL = "claude-sonnet-4-6"  # Higher-quality answer generation
MAX_INTERVIEWS_LOADED = 4

ROUTER_SYSTEM = """You are a routing assistant for a stakeholder-interview library. \
Given a user question and a list of interview entries (with `name`, `stakeholder`, `organization`, \
`description`), pick which interviews are most likely to contain the answer.

Output ONLY a JSON array of `name` slugs, e.g. ["2026-04-09-santiago-henao-ruta-n-summary"]. \
Pick 1-4 entries. Pick fewer if only one is clearly relevant. Pick zero (empty array) \
if no interview is relevant — the question is then about the broader report, not the \
interview library."""

ANSWER_SYSTEM = """You are an expert analyst for the CAF (Development Bank of Latin America \
and the Caribbean) venture capital strategy project. You answer questions using the provided \
stakeholder interview summaries and report sections.

Rules:
- Keep answers SHORT — 2-4 sentences max for a first response.
- Give the key takeaway upfront.
- End with a prompt like "Want me to go deeper on [specific aspect]?" to invite follow-up.
- Cite sources inline using the format [stakeholder name, organization] OR [section title].
- The frontend will turn citations into clickable links; you just need to use the format consistently.
- If asked to "go deeper", expand with bullets and specifics.
- Use only the provided context. If the answer isn't there, say so.
- For interviews marked anonymous, refer to the stakeholder by their anonymized label only."""


def _router_prompt(query: str, index_entries: list[dict]) -> str:
    items = []
    for e in index_entries:
        items.append({
            "name": e["name"],
            "stakeholder": e.get("stakeholder", ""),
            "organization": e.get("organization", ""),
            "countries": e.get("countries", []),
            "description": e.get("description", ""),
        })
    return f"""<question>{query}</question>

<library>
{json.dumps(items, ensure_ascii=False, indent=2)}
</library>"""


def _route_to_interviews(client: Anthropic, query: str) -> list[dict]:
    index = tx.load_index()  # already anonymized
    if not index:
        return []
    msg = client.messages.create(
        model=ROUTER_MODEL,
        max_tokens=300,
        system=ROUTER_SYSTEM,
        messages=[{"role": "user", "content": _router_prompt(query, index)}],
    )
    text = msg.content[0].text.strip()
    # Strip code fences
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    try:
        names = json.loads(text)
    except json.JSONDecodeError:
        return []
    if not isinstance(names, list):
        return []
    names = names[:MAX_INTERVIEWS_LOADED]
    interviews = []
    for n in names:
        entry = tx.load_transcript(n)
        if entry:
            interviews.append(entry)
    return interviews


def _section_corpus_match(query: str, top_k: int = 4) -> list:
    """TF-IDF fallback over the broader report sections (executive summary, recommendations, etc.)."""
    sections = list(Section.objects.all())
    if not sections:
        return []
    corpus = [f"{s.title} {s.body_markdown}" for s in sections]
    corpus.append(query)
    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    matrix = vectorizer.fit_transform(corpus)
    scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
    ranked = sorted(zip(sections, scores), key=lambda x: x[1], reverse=True)
    return [s for s, score in ranked[:top_k] if score > 0.05]


def _build_context(interviews: list[dict], sections: list) -> tuple[str, list[dict]]:
    """Return (context_xml, source_metadata)."""
    parts = []
    sources = []
    for iv in interviews:
        sources.append({
            "type": "interview",
            "slug": iv["name"],
            "title": f"{iv.get('stakeholder', '')} — {iv.get('organization', '')}",
            "stakeholder": iv.get("stakeholder", ""),
            "organization": iv.get("organization", ""),
            "url": f"/interviews/{iv['name']}/",
        })
        header = f"Interview with {iv.get('stakeholder', '?')}"
        if iv.get("role"):
            header += f", {iv['role']}"
        if iv.get("organization"):
            header += f" at {iv['organization']}"
        if iv.get("date"):
            header += f" ({iv['date']})"
        parts.append(
            f'<interview slug="{iv["name"]}">\n{header}\n\n{iv.get("body", "")}\n</interview>'
        )
    for s in sections:
        sources.append({
            "type": "section",
            "slug": s.slug,
            "title": s.title,
            "url": f"/section/{s.slug}/",
        })
        parts.append(
            f'<section slug="{s.slug}" title="{s.title}">\n{s.body_markdown}\n</section>'
        )
    return "\n\n".join(parts), sources


def ask_claude(query: str) -> dict:
    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    interviews = _route_to_interviews(client, query)
    sections = [] if interviews else _section_corpus_match(query)

    if not interviews and not sections:
        return {
            "answer": "I don't have content loaded that addresses this question. Try a more specific question, or ask about a stakeholder, country, or recommendation.",
            "sources": [],
        }

    context, sources = _build_context(interviews, sections)

    msg = client.messages.create(
        model=ANSWER_MODEL,
        max_tokens=600,
        system=ANSWER_SYSTEM,
        messages=[{
            "role": "user",
            "content": f"<context>\n{context}\n</context>\n\n<question>{query}</question>",
        }],
    )
    answer = msg.content[0].text
    return {
        "answer": answer,
        "sources": [s["title"] for s in sources],
        "source_links": sources,  # full metadata for the frontend to render clickable links
    }
