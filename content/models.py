from django.db import models


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
