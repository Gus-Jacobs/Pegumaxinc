# pegumax_project/views.py
from django.conf import settings
from django.http import Http404, FileResponse
from django.shortcuts import get_object_or_404, render # Import render
import os
from django.views.static import serve as django_serve_static

# --- NEW: Custom 404 and 500 views ---
def custom_404_view(request, exception):
    """
    Custom 404 handler.
    Django passes the 'exception' argument, so it must be accepted here.
    """
    return render(request, '404.html', status=404)

def custom_500_view(request):
    """
    Custom 500 handler.
    Django does NOT pass an 'exception' argument to the 500 handler.
    """
    return render(request, '500.html', status=500)
# --- END NEW ---


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
