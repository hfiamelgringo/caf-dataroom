from django.db import models


class ChatMessage(models.Model):
    session_id = models.CharField(max_length=64)
    query = models.TextField()
    response = models.TextField()
    sources_used = models.JSONField(default=list)
    response_time_ms = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.session_id}: {self.query[:50]}"
