import json
import re
import time
import uuid
from pathlib import Path

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_http_methods

from .claude_client import ask_claude
from .models import ChatMessage


@csrf_exempt
@require_POST
def chat_api(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    query = data.get("query", "").strip()
    if not query:
        return JsonResponse({"error": "No query provided"}, status=400)

    session_id = data.get("session_id") or str(uuid.uuid4())

    start = time.time()
    result = ask_claude(query)
    elapsed_ms = int((time.time() - start) * 1000)

    ChatMessage.objects.create(
        session_id=session_id,
        query=query,
        response=result["answer"],
        sources_used=result["sources"],
        response_time_ms=elapsed_ms,
    )

    return JsonResponse({
        "answer": result["answer"],
        "sources": result["sources"],
        "source_links": result.get("source_links", []),
        "response_time_ms": elapsed_ms,
        "session_id": session_id,
    })
