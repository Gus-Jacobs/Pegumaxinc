from django.utils.deprecation import MiddlewareMixin

class CsrfExemptAPIMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path == '/bot-api/receive-logs/' and request.method == 'POST':
            # Mark CSRF as processed for this specific API endpoint
            # This should prevent CsrfViewMiddleware from rejecting it
            setattr(request, '_dont_enforce_csrf_checks', True)
