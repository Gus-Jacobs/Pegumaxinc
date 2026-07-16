# pegumax_project/views.py
from django.conf import settings
from django.http import Http404, FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, render # Import render
from django.template.loader import render_to_string
import os
from django.views.static import serve as django_serve_static

# --- Custom 404 and 500 views ---
# Rendered WITHOUT a request/context-processors so they can't fail — a 500 caused
# by (say) a database hiccup must never make the error page itself 500. The
# templates are self-contained (no base.html, no DB access).
def custom_404_view(request, exception):
    return HttpResponse(render_to_string('404.html'), status=404)

def custom_500_view(request):
    try:
        return HttpResponse(render_to_string('500.html'), status=500)
    except Exception:
        # Absolute last resort — plain text, no templates.
        return HttpResponse("Something went wrong on our end. Please try again.",
                            status=500, content_type="text/plain")
# --- END ---


def serve_flutter_asset(request, path):
    """
    Custom view to serve static files from the Flutter build directory.
    This uses Django's built-in serve which handles MIME types correctly.
    """
    document_root = settings.STATIC_ROOT / 'frontend' / 'student-suite-web'
    full_path = document_root / path

    # Basic security check: ensure path doesn't try to escape document_root
    if not os.path.normpath(full_path).startswith(os.path.normpath(document_root)):
        raise Http404("Path is outside allowed directory")

    # Use Django's internal serve mechanism for files.
    # This automatically handles MIME types and checks for file existence.
    return django_serve_static(request, path, document_root=document_root)
