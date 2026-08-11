from contextvars import ContextVar

from django.utils.deprecation import MiddlewareMixin

_current_request = ContextVar("mezzanine_current_request", default=None)


def current_request():
    """
    Retrieves the request from the current context.
    """
    return _current_request.get()


class _RequestLocal:
    """Attribute facade over the request ContextVar.

    Tests historically assigned ``_thread_local.request``. Storage is a
    ContextVar so the same API works under threads and async tasks.
    """

    def __getattr__(self, name):
        if name == "request":
            value = _current_request.get()
            if value is None:
                raise AttributeError(name)
            return value
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if name == "request":
            _current_request.set(value)
            return
        raise AttributeError(name)

    def __delattr__(self, name):
        if name == "request":
            _current_request.set(None)
            return
        raise AttributeError(name)


_thread_local = _RequestLocal()


class CurrentRequestMiddleware(MiddlewareMixin):
    """
    Stores the request in a ContextVar for global access.

    ``process_response`` and ``process_exception`` both reset so the
    value does not leak across requests.
    """

    def process_request(self, request):
        request._mezzanine_request_token = _current_request.set(request)

    def process_response(self, request, response):
        self._reset_request(request)
        return response

    def process_exception(self, request, exception):
        self._reset_request(request)

    @staticmethod
    def _reset_request(request):
        token = getattr(request, "_mezzanine_request_token", None)
        if token is not None:
            _current_request.reset(token)
            del request._mezzanine_request_token
