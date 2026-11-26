import threading

_thread_locals = threading.local()

def get_current_user():
    """Retrieve the current user from thread-local storage."""
    return getattr(_thread_locals, 'user', None)

class CurrentUserMiddleware:
    """
    Middleware that captures the currently authenticated user in thread-local storage
    so that AuditedModel can automatically populate created_by and updated_by fields.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = getattr(request, 'user', None) if request.user.is_authenticated else None
        try:
            response = self.get_response(request)
        finally:
            _thread_locals.user = None
        return response
