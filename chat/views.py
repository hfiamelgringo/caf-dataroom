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


# --- DEV-ONLY: bulk-import endpoint for raw transcripts (Phase 2 scrape) ---
# Receives plain-text POST bodies from a browser tab logged into Google Drive
# and saves them to content_data/raw_transcripts/<filename>.
# Remove this endpoint once Phase 2 is complete.

ALLOWED_FILENAME_RE = re.compile(r"^[a-zA-Z0-9._-]+$")


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def dev_save_transcript(request):
    if request.method == "OPTIONS":
        resp = JsonResponse({"ok": True})
        resp["Access-Control-Allow-Origin"] = "*"
    resp["Access-Control-Allow-Private-Network"] = "true"
        resp["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        resp["Access-Control-Allow-Headers"] = "Content-Type"
        return resp

    filename = request.GET.get("filename", "").strip()
    if not filename or not ALLOWED_FILENAME_RE.match(filename):
        return JsonResponse({"error": "bad filename"}, status=400)

    body = request.body
    if not body:
        return JsonResponse({"error": "empty body"}, status=400)

    out_dir = Path(settings.BASE_DIR) / "content_data" / "raw_transcripts"
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / filename
    target.write_bytes(body)

    resp = JsonResponse({"ok": True, "filename": filename, "bytes": len(body)})
    resp["Access-Control-Allow-Origin"] = "*"
    resp["Access-Control-Allow-Private-Network"] = "true"
    return resp
