from pathlib import Path

from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import markdown as md_lib

from .models import Interview, InterviewConsent, Section
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


# ------------------------------------------------------------------ consent flow

import markdown as _md
from django.http import HttpResponseBadRequest


def _recipient_rows(token):
    """Return all consent rows for a recipient_token, oldest interview first."""
    rows = list(
        InterviewConsent.objects.filter(recipient_token=token).order_by("interview_slug")
    )
    if not rows:
        from django.http import Http404
        raise Http404("Review link not found.")
    return rows


def _recipient_state(rows):
    """Compute the current step from a recipient's row set.

    Returns one of: 'consent', 'declined', 'name', 'summary', 'done'.
    """
    primary = rows[0]
    if primary.participation_consent is None:
        return "consent"
    if primary.participation_consent is False:
        return "declined"
    if not primary.display_attribution:
        return "name"
    if any(r.summary_decision == InterviewConsent.SUMMARY_NOT_SET for r in rows):
        return "summary"
    return "done"


def _ctx(rows, **extra):
    primary = rows[0]
    ctx = {
        "rows": rows,
        "primary": primary,
        "is_multi": len(rows) > 1,
        "token": primary.recipient_token,
    }
    ctx.update(extra)
    return ctx


def _next_undecided(rows):
    """Return (target_row, active_index) — first undecided row, or (rows[0], 0)."""
    for i, r in enumerate(rows):
        if r.summary_decision == InterviewConsent.SUMMARY_NOT_SET:
            return r, i
    return rows[0], 0


def _recompute_status(rows):
    """Re-derive status on every row based on consent + each row's summary decision."""
    primary = rows[0]
    if primary.participation_consent is False:
        target = InterviewConsent.STATUS_DECLINED
        for r in rows:
            r.status = target
            r.responded_at = r.responded_at or timezone.now()
            r.save(update_fields=["status", "responded_at"])
        return
    # else: per-row status depends on whether attribution or summary was edited
    name_was_edited = primary.display_attribution.strip() != primary.default_attribution()
    for r in rows:
        if r.summary_decision == InterviewConsent.SUMMARY_NOT_SET:
            continue  # not yet decided
        if r.summary_decision == InterviewConsent.SUMMARY_EDITED or name_was_edited:
            r.status = InterviewConsent.STATUS_CHANGES
        else:
            r.status = InterviewConsent.STATUS_APPROVED
        r.responded_at = timezone.now()
        r.save(update_fields=["status", "responded_at"])


def consent_review(request, token):
    rows = _recipient_rows(token)
    state = _recipient_state(rows)
    extra = {"state": state, "step_template": f"content/_step_{state}.html"}
    if state == "summary":
        target_row, active_index = _next_undecided(rows)
        extra["target_row"] = target_row
        extra["active_index"] = active_index
    return render(request, "content/consent_review.html", _ctx(rows, **extra))


@require_http_methods(["GET"])
def consent_step_back(request, token, step):
    """Re-render any step's read-mode partial without changing persisted data.

    Allows the user to revisit Step 1 or Step 2 from a later step. If they then
    submit a different answer, downstream state is reconciled by the save view
    (e.g. switching consent yes→no marks the recipient declined).
    """
    rows = _recipient_rows(token)
    if step == "consent":
        return render(request, "content/_step_consent.html", _ctx(rows))
    if step == "name":
        return render(request, "content/_step_name.html", _ctx(rows))
    if step == "summary":
        target_row, active_index = _next_undecided(rows)
        return render(request, "content/_step_summary.html",
                      _ctx(rows, target_row=target_row, active_index=active_index))
    return HttpResponseBadRequest("Unknown step.")


@require_http_methods(["POST"])
def consent_reset(request, token):
    rows = _recipient_rows(token)
    for r in rows:
        r.participation_consent = None
        r.display_attribution = ""
        r.summary_decision = InterviewConsent.SUMMARY_NOT_SET
        r.edited_summary_markdown = ""
        r.status = InterviewConsent.STATUS_PENDING
        r.responded_at = None
        r.save(update_fields=[
            "participation_consent", "display_attribution",
            "summary_decision", "edited_summary_markdown",
            "status", "responded_at",
        ])
    return render(request, "content/_step_consent.html", _ctx(rows))


@require_http_methods(["POST"])
def consent_step_consent(request, token):
    rows = _recipient_rows(token)
    decision = request.POST.get("decision", "")
    if decision not in {"yes", "no"}:
        return HttpResponseBadRequest("Pick yes or no.")
    consent = (decision == "yes")
    for r in rows:
        r.participation_consent = consent
        r.save(update_fields=["participation_consent"])
    if not consent:
        _recompute_status(rows)
        return render(request, "content/_step_declined.html", _ctx(rows))
    return render(request, "content/_step_name.html", _ctx(rows))


@require_http_methods(["GET"])
def consent_step_name_edit(request, token):
    rows = _recipient_rows(token)
    return render(request, "content/_step_name_edit.html", _ctx(rows))


@require_http_methods(["GET"])
def consent_step_name_show(request, token):
    rows = _recipient_rows(token)
    return render(request, "content/_step_name.html", _ctx(rows))


@require_http_methods(["POST"])
def consent_step_name_save(request, token):
    rows = _recipient_rows(token)
    primary = rows[0]
    accept_default = request.POST.get("accept_default") == "1"
    if accept_default:
        attribution = primary.default_attribution()
    else:
        attribution = request.POST.get("attribution", "").strip() or primary.default_attribution()
    for r in rows:
        r.display_attribution = attribution
        r.save(update_fields=["display_attribution"])
    target_row, active_index = _next_undecided(rows)
    return render(request, "content/_step_summary.html",
                  _ctx(rows, active_index=active_index, target_row=target_row))


@require_http_methods(["GET"])
def consent_step_summary_show(request, token, row_id):
    rows = _recipient_rows(token)
    target = next((r for r in rows if r.id == row_id), None)
    if target is None:
        return HttpResponseBadRequest("Unknown row.")
    return render(request, "content/_summary_panel.html", _ctx(rows, target=target))


@require_http_methods(["GET"])
def consent_step_summary_edit(request, token, row_id):
    rows = _recipient_rows(token)
    target = next((r for r in rows if r.id == row_id), None)
    if target is None:
        return HttpResponseBadRequest("Unknown row.")
    return render(request, "content/_summary_panel_edit.html", _ctx(rows, target=target))


@require_http_methods(["POST"])
def consent_step_summary_save(request, token, row_id):
    rows = _recipient_rows(token)
    target = next((r for r in rows if r.id == row_id), None)
    if target is None:
        return HttpResponseBadRequest("Unknown row.")
    decision = request.POST.get("decision", "")
    if decision == "accept":
        target.summary_decision = InterviewConsent.SUMMARY_ACCEPTED
        target.edited_summary_markdown = ""
    elif decision == "edit":
        edited = request.POST.get("edited_markdown", "").strip()
        target.summary_decision = InterviewConsent.SUMMARY_EDITED
        target.edited_summary_markdown = edited
    else:
        return HttpResponseBadRequest("Pick accept or edit.")
    target.save(update_fields=["summary_decision", "edited_summary_markdown"])
    _recompute_status(rows)

    rows = _recipient_rows(token)  # reload
    if all(r.summary_decision != InterviewConsent.SUMMARY_NOT_SET for r in rows):
        return render(request, "content/_step_done.html", _ctx(rows, just_saved=target))
    # Multi-interview: re-render the whole summary step with checkmarks + jump to next undecided
    target_row, active_index = _next_undecided(rows)
    just_saved_idx = next((i for i, r in enumerate(rows) if r.id == target.id), None)
    return render(request, "content/_step_summary.html",
                  _ctx(rows, target_row=target_row, active_index=active_index,
                       just_saved=target, just_saved_index=just_saved_idx))


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
