from django.contrib import admin
from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ["session_id", "query", "response_time_ms", "created_at"]
    search_fields = ["query", "response"]
    readonly_fields = ["session_id", "query", "response", "sources_used", "response_time_ms", "created_at"]
