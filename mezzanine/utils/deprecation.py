"""
Small compatibility helpers. Django 1.9 / 1.10 / 2.2 branches are gone;
the helpers stay so existing call sites keep working.
"""
from functools import wraps

from django.conf import settings


def request_is_ajax(request):
    """
    request.is_ajax() is deprecated. Check the content_type

    Returns true if request CONTENT_TYPE is "application/json"
    """
    return request.META.get("CONTENT_TYPE") == "application/json"


def get_middleware_setting_name():
    """
    Returns the name of the middleware setting.
    """
    return "MIDDLEWARE"


def get_middleware_setting():
    """
    Returns the middleware setting.
    """
    return getattr(settings, get_middleware_setting_name())


def is_authenticated(user):
    """
    Returns True if the user is authenticated.
    """
    return user.is_authenticated


def get_related_model(field):
    """
    Returns the model on a relation field.
    """
    try:
        return field.remote_field.model
    except AttributeError:
        pass


def mark_safe(s):
    from django.utils.safestring import mark_safe as django_safe

    if callable(s):

        @wraps(s)
        def wrapper(*args, **kwargs):
            return django_safe(s(*args, **kwargs))

        return wrapper
    return django_safe(s)
