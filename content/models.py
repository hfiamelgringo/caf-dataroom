import uuid

from django.db import models
from django.urls import reverse


class Interview(models.Model):
    title = models.CharField(max_length=300)
    slug = models.SlugField(unique=True, max_length=120)
    date = models.DateField()
    country_code = models.CharField(max_length=2, blank=True)
    country_label = models.CharField(max_length=100, blank=True)
    stakeholder_name = models.CharField(max_length=200)
    stakeholder_role = models.CharField(max_length=200, blank=True)
    organization = models.CharField(max_length=200, blank=True)
    topic_tag = models.CharField(max_length=100, blank=True)
    body_markdown = models.TextField()
    body_html = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return self.title


def _new_token() -> str:
    return uuid.uuid4().hex


class InterviewConsent(models.Model):
    """One row per (recipient, interview). All rows for the same recipient share
    a `recipient_token`; the review link in the email uses that token, and
    consent/attribution decisions apply to all of a recipient's rows at once."""

    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_CHANGES = "changes_requested"
    STATUS_DECLINED = "declined"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_CHANGES, "Changes requested"),
        (STATUS_DECLINED, "Declined"),
    ]

    SUMMARY_NOT_SET = ""
    SUMMARY_ACCEPTED = "accepted"
    SUMMARY_EDITED = "edited"
    SUMMARY_CHOICES = [
        (SUMMARY_NOT_SET, "Not yet"),
        (SUMMARY_ACCEPTED, "Accepted as-is"),
        (SUMMARY_EDITED, "Edited"),
    ]

    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    organization = models.CharField(max_length=300, blank=True)
    interview_slug = models.SlugField(max_length=200)
    interview_url = models.URLField(blank=True)

    recipient_token = models.CharField(max_length=32, db_index=True, default=_new_token)

    copy_snapshot_html = models.TextField(blank=True)
    copy_snapshot_markdown = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    participation_consent = models.BooleanField(null=True, blank=True)
    display_attribution = models.CharField(max_length=300, blank=True)
    summary_decision = models.CharField(max_length=20, choices=SUMMARY_CHOICES, default=SUMMARY_NOT_SET, blank=True)
    edited_summary_markdown = models.TextField(blank=True)

    manual_outreach = models.BooleanField(
        default=False,
        help_text="Excluded from bulk email send (handled via WhatsApp etc.). Review URL still works.",
    )

    sent_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["interview_slug"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        return f"{self.name} <{self.email or 'no email'}> — {self.interview_slug}"

    def get_review_url(self) -> str:
        return reverse("content:consent_review", kwargs={"token": self.recipient_token})

    def default_attribution(self) -> str:
        bits = [self.name]
        if self.organization:
            bits.append(self.organization)
        return ", ".join(bits)


class Section(models.Model):
    SECTION_TYPES = [
        ("intro", "Introduction"),
        ("executive_summary", "Executive Summary"),
        ("recommendation", "Macro Recommendation"),
        ("insight", "Insights & Framing"),
        ("small_idea", "Small Idea"),
        ("country", "Country Profile"),
        ("annex", "Annex"),
        ("reference", "Reference"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    body_markdown = models.TextField()
    body_html = models.TextField(blank=True)
    section_type = models.CharField(max_length=30, choices=SECTION_TYPES)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children"
    )
    order = models.IntegerField(default=0)
    country_code = models.CharField(max_length=2, blank=True)
    meta_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title
