from pathlib import Path

from django.conf import settings
from django.shortcuts import render, get_object_or_404
import markdown as md_lib

from .models import Interview, Section
from . import transcripts as tx

COUNTRY_IMAGE_DIRS = {
    "GT": "guatemala",
    "CR": "costa_rica",
    "DO": "dominican_republic",
    "HN": "honduras",
}


def get_country_images():
    result = {}
    img_root = Path(settings.BASE_DIR) / "static" / "img"
    for code, folder in COUNTRY_IMAGE_DIRS.items():
        folder_path = img_root / folder
        if folder_path.exists():
            files = sorted(
                f.name for f in folder_path.iterdir()
                if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
            )
            result[code] = [f"img/{folder}/{name}" for name in files]
        else:
            result[code] = []
    return result


def home(request):
    sections = Section.objects.all()
    executive_summary = sections.filter(section_type="executive_summary").first()
    recommendations = sections.filter(section_type="recommendation")
    countries = sections.filter(section_type="country", parent__isnull=True).distinct()
    country_images = get_country_images()
    country_list = [
        {"code": "GT", "name": "Guatemala", "images": country_images.get("GT", [])},
        {"code": "CR", "name": "Costa Rica", "images": country_images.get("CR", [])},
        {"code": "DO", "name": "Dominican Republic", "images": country_images.get("DO", [])},
        {"code": "HN", "name": "Honduras", "images": country_images.get("HN", [])},
    ]
    return render(request, "content/home.html", {
        "executive_summary": executive_summary,
        "recommendations": recommendations,
        "countries": countries,
        "nav_sections": sections,
        "country_list": country_list,
    })


def section_detail(request, slug):
    section = get_object_or_404(Section, slug=slug)
    children = section.children.all()
    nav_sections = Section.objects.all()
    return render(request, "content/section.html", {
        "section": section,
        "children": children,
        "nav_sections": nav_sections,
    })


def country_detail(request, country_code):
    sections = Section.objects.filter(country_code=country_code.upper())
    main_section = sections.filter(parent__isnull=True).first()
    if not main_section:
        main_section = sections.first()
    nav_sections = Section.objects.all()
    return render(request, "content/country.html", {
        "country_code": country_code.upper(),
        "main_section": main_section,
        "subsections": sections.exclude(pk=main_section.pk) if main_section else [],
        "nav_sections": nav_sections,
    })


def recommendations(request):
    recs = Section.objects.filter(section_type="recommendation")
    nav_sections = Section.objects.all()
    return render(request, "content/recommendations.html", {
        "recommendations": recs,
        "nav_sections": nav_sections,
    })


def interviews_list(request):
    entries = tx.load_index()
    filters = tx.collect_filter_options(entries)
    nav_sections = Section.objects.all()
    return render(request, "content/interviews_list.html", {
        "entries": entries,
        "filters": filters,
        "nav_sections": nav_sections,
    })


def interview_detail(request, slug):
    entry = tx.load_transcript(slug)
    if entry is None:
        from django.http import Http404
        raise Http404(f"Transcript not found: {slug}")
    body_html = md_lib.markdown(
        entry.get("body", ""),
        extensions=["tables", "fenced_code"],
    )
    nav_sections = Section.objects.all()
    return render(request, "content/interview_detail.html", {
        "entry": entry,
        "body_html": body_html,
        "nav_sections": nav_sections,
    })


def recommendation_detail(request, slug):
    section = get_object_or_404(Section, slug=slug, section_type="recommendation")
    all_recs = list(Section.objects.filter(section_type="recommendation"))
    idx = next((i for i, r in enumerate(all_recs) if r.slug == slug), 0)
    prev_rec = all_recs[idx - 1] if idx > 0 else None
    next_rec = all_recs[idx + 1] if idx < len(all_recs) - 1 else None
    return render(request, "content/recommendation_detail.html", {
        "section": section,
        "prev_rec": prev_rec,
        "next_rec": next_rec,
        "current_num": idx + 1,
        "total_recs": len(all_recs),
    })
