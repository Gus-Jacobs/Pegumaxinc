# pegumax_project/views.py
from django.conf import settings
from django.http import Http404, FileResponse
from django.shortcuts import get_object_or_404
from django.views.static import serve as django_serve_static # Renaming to avoid conflict
import os

def serve_flutter_asset(request, path):
    """
    Custom view to serve static files from the Flutter build directory
    mimicking django.views.static.serve.
    This is intended for production use with custom URLs where WhiteNoise might not pick it up.
    """
    document_root = settings.STATIC_ROOT / 'frontend' / 'student-suite-web'
    full_path = document_root / path

    # Basic security check: ensure path doesn't try to escape document_root
    if not os.path.normpath(full_path).startswith(os.path.normpath(document_root)):
        raise Http404("Path is outside allowed directory")

    # Use Django's internal serve mechanism for files
    # This automatically handles MIME types and range requests.
    try:
        response = django_serve_static(request, path, document_root=document_root)
        return response
    except Http404:
        # If the specific asset is not found, let the TemplateView (for index.html) handle it.
        # This is for paths like /software-center/student-suite/dashboard where Flutter handles routing.
        # We'll rely on the URL resolver order for this.
        raise Http404("Flutter asset not found.")
