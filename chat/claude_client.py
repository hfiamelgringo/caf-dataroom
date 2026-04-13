from django.conf import settings
from anthropic import Anthropic
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from content.models import Section

SYSTEM_PROMPT = """You are an expert analyst for the CAF (Development Bank of Latin America and the Caribbean) venture capital strategy project. You answer questions based ONLY on the provided document sections.

Rules:
- Keep answers SHORT — 2-4 sentences max for a first response
- Give the key takeaway upfront, not the full analysis
- End with a prompt like "Want me to go deeper on [specific aspect]?" to invite follow-up
- Answer using ONLY information from the provided <context> sections
- Cite which section(s) your answer draws from by name
- If the information is not in the provided sections, say so clearly
- If the user asks to "go deeper" or wants more detail, then expand with bullet points and specifics
- You may synthesize across sections, but do not invent information"""


def get_relevant_sections(query, top_k=6):
    sections = list(Section.objects.all())
    if not sections:
        return []

    corpus = [f"{s.title} {s.body_markdown}" for s in sections]
    corpus.append(query)

    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(corpus)

    query_vec = tfidf_matrix[-1]
    section_vecs = tfidf_matrix[:-1]
    scores = cosine_similarity(query_vec, section_vecs).flatten()

    ranked = sorted(zip(sections, scores), key=lambda x: x[1], reverse=True)
    return [s for s, score in ranked[:top_k] if score > 0.01]


def build_context(sections):
    parts = []
    for s in sections:
        parts.append(f'<section title="{s.title}" slug="{s.slug}">\n{s.body_markdown}\n</section>')
    return "\n\n".join(parts)


def ask_claude(query):
    sections = get_relevant_sections(query)

    if not sections:
        return {
            "answer": "No content has been loaded yet. Please run the load_content management command first.",
            "sources": [],
        }

    context = build_context(sections)
    source_titles = [s.title for s in sections]

    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"<context>\n{context}\n</context>\n\n<question>{query}</question>",
            }
        ],
    )

    answer = message.content[0].text
    return {"answer": answer, "sources": source_titles}
