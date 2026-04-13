from django.contrib import admin
from .models import Section


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ["title", "section_type", "order", "country_code", "updated_at"]
    list_filter = ["section_type", "country_code"]
    search_fields = ["title", "body_markdown"]
    prepopulated_fields = {"slug": ("title",)}
    ordering = ["order"]
