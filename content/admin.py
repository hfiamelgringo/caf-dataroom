from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import InterviewConsent, Section


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ["title", "section_type", "order", "country_code", "updated_at"]
    list_filter = ["section_type", "country_code"]
    search_fields = ["title", "body_markdown"]
    prepopulated_fields = {"slug": ("title",)}
    ordering = ["order"]


@admin.register(InterviewConsent)
class InterviewConsentAdmin(admin.ModelAdmin):
    list_display = (
        "name", "email", "interview_slug", "status", "manual_outreach",
        "sent_at", "responded_at", "review_link",
    )
    list_filter = ("status", "manual_outreach", "summary_decision")
    search_fields = ("name", "email", "interview_slug", "organization")
    readonly_fields = (
        "recipient_token", "copy_snapshot_html", "copy_snapshot_markdown",
        "sent_at", "responded_at", "created_at", "review_link",
    )
    fieldsets = (
        (None, {"fields": ("name", "email", "organization", "interview_slug", "interview_url")}),
        ("Outreach", {"fields": ("manual_outreach", "sent_at", "review_link")}),
        ("Decisions", {"fields": (
            "status", "participation_consent", "display_attribution",
            "summary_decision", "edited_summary_markdown", "responded_at",
        )}),
        ("Snapshot", {"fields": ("copy_snapshot_markdown", "copy_snapshot_html")}),
        ("Tracking", {"fields": ("recipient_token", "created_at")}),
    )

    def review_link(self, obj):
        if not obj.recipient_token:
            return ""
        url = reverse("content:consent_review", kwargs={"token": obj.recipient_token})
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)
    review_link.short_description = "Review URL"
