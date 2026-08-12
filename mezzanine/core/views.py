import mimetypes
import os
from urllib.parse import urljoin, urlparse

from django.apps import apps
from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.staticfiles import finders
from django.core.exceptions import PermissionDenied
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseNotFound,
    HttpResponseServerError,
    JsonResponse,
)
from django.shortcuts import redirect
from django.template.loader import get_template
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import escape
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.views.decorators.csrf import requires_csrf_token
from django.views.decorators.http import require_http_methods, require_POST

from mezzanine.conf import settings
from mezzanine.core.capabilities import user_can_edit
from mezzanine.core.forms import get_edit_form
from mezzanine.core.models import Displayable, SiteRole
from mezzanine.utils.sites import has_site_permission
from mezzanine.utils.urls import next_url
from mezzanine.utils.views import paginate

mimetypes.init()


@staff_member_required
@require_POST
def set_site(request):
    """
    Put the selected site ID into the session - posted to from
    the "Select site" drop-down in the header of the admin. The
    site ID is then used in favour of the current request's
    domain in ``mezzanine.core.managers.CurrentSiteManager``.
    """
    site_id = int(request.POST["site_id"])
    if not request.user.is_superuser:
        if not SiteRole.objects.filter(user=request.user, site_id=site_id).exists():
            raise PermissionDenied
    request.session["site_id"] = site_id
    admin_url = reverse("admin:index")
    next = next_url(request) or admin_url
    # Don't redirect to a change view for an object that won't exist
    # on the selected site - go to its list view instead.
    if next.startswith(admin_url):
        parts = next.split("/")
        if len(parts) > 4 and parts[4].isdigit():
            next = "/".join(parts[:4])
    return redirect(next)


def direct_to_template(request, template, extra_context=None, **kwargs):
    """
    Replacement for Django's ``direct_to_template`` that uses
    ``TemplateResponse`` via ``mezzanine.utils.views.render``.
    """
    context = extra_context or {}
    context["params"] = kwargs
    for (key, value) in context.items():
        if callable(value):
            context[key] = value()
    return TemplateResponse(request, template, context)


def _edit_source(request):
    return request.GET if request.method == "GET" else request.POST


def _edit_object(request):
    src = _edit_source(request)
    try:
        app = src["app"]
        model_name = src["model"]
        object_id = src["id"]
        field_names = src["fields"]
    except KeyError:
        raise Http404
    try:
        model = apps.get_model(app, model_name)
    except (LookupError, ValueError, TypeError):
        raise Http404
    try:
        obj = model.objects.get(pk=object_id)
    except (model.DoesNotExist, ValueError, TypeError):
        raise Http404
    return model, obj, field_names


def _edit_query(obj, field_names, extra=None):
    params = {
        "app": obj._meta.app_label,
        "model": obj._meta.object_name.lower(),
        "id": obj.pk,
        "fields": field_names,
    }
    if extra:
        params.update(extra)
    return reverse("edit") + "?" + urlencode(params)


def format_editable_value(obj, field_name):
    value = getattr(obj, field_name, "")
    if value is None:
        value = ""
    try:
        field = obj._meta.get_field(field_name)
    except Exception:
        return escape(str(value))
    from mezzanine.core.fields import RichTextField

    if isinstance(field, RichTextField):
        from mezzanine.core.templatetags.mezzanine_tags import richtext_filters

        return richtext_filters(value)
    return escape(str(value))


def editable_inner_html(obj, field_names):
    parts = [format_editable_value(obj, name) for name in field_names.split(",")]
    return mark_safe("".join(parts))


def render_editable_island(request, obj, field_names, original=None):
    if original is None:
        original = editable_inner_html(obj, field_names)
    context = {
        "request": request,
        "editable_obj": obj,
        "field_names": field_names,
        "original": original,
        "edit_url": _edit_query(obj, field_names),
        "display_url": _edit_query(obj, field_names, {"display": "1"}),
    }
    return get_template("includes/editable_island.html").render(context)


def render_editable_form(request, form, obj, field_names, status=200):
    context = {
        "request": request,
        "editable_form": form,
        "editable_obj": obj,
        "field_names": field_names,
        "edit_url": _edit_query(obj, field_names),
        "display_url": _edit_query(obj, field_names, {"display": "1"}),
    }
    html = get_template("includes/editable_form.html").render(context)
    return HttpResponse(html, status=status)


@require_http_methods(["GET", "POST"])
def edit(request):
    """
    HTMX inline editing (design §7.2).

    GET  /edit/?app=&model=&id=&fields=  → form fragment (textarea)
    GET  ...&display=1                   → island (cancel)
    POST /edit/ + HX-Request             → island or 400 form-with-errors
    """
    model, obj, field_names = _edit_object(request)
    if not user_can_edit(request.user, obj):
        raise PermissionDenied

    if request.method == "GET":
        if request.GET.get("display") == "1":
            return HttpResponse(render_editable_island(request, obj, field_names))
        form = get_edit_form(obj, field_names, textarea=True)
        return render_editable_form(request, form, obj, field_names)

    form = get_edit_form(
        obj,
        field_names,
        data=request.POST,
        files=request.FILES,
        textarea=True,
    )
    if form.is_valid():
        form.save()
        model_admin = ModelAdmin(model, admin.site)
        message = model_admin.construct_change_message(request, form, None)
        model_admin.log_change(request, obj, message)
        return HttpResponse(render_editable_island(request, obj, field_names))
    return render_editable_form(request, form, obj, field_names, status=400)


def search(request, template="search_results.html", extra_context=None):
    """
    Display search results. Takes an optional "contenttype" GET parameter
    in the form "app-name.ModelName" to limit search results to a single model.
    """
    query = request.GET.get("q", "")
    page = request.GET.get("page", 1)
    per_page = settings.SEARCH_PER_PAGE
    max_paging_links = settings.MAX_PAGING_LINKS
    try:
        parts = request.GET.get("type", "").split(".", 1)
        search_model = apps.get_model(*parts)
        search_model.objects.search  # Attribute check
    except (ValueError, TypeError, LookupError, AttributeError):
        search_model = Displayable
        search_type = _("Everything")
    else:
        search_type = search_model._meta.verbose_name_plural.capitalize()
    results = search_model.objects.search(query, for_user=request.user)
    paginated = paginate(results, page, per_page, max_paging_links)
    context = {"query": query, "results": paginated, "search_type": search_type}
    context.update(extra_context or {})
    return TemplateResponse(request, template, context)


@staff_member_required
def static_proxy(request):
    """
    Serves TinyMCE plugins inside the inline popups and the uploadify
    SWF, as these are normally static files, and will break with
    cross-domain JavaScript errors if ``STATIC_URL`` is an external
    host. URL for the file is passed in via querystring in the inline
    popup plugin template, and we then attempt to pull out the relative
    path to the file, so that we can serve it locally via Django.
    """
    normalize = lambda u: ("//" + u.split("://")[-1]) if "://" in u else u
    url = normalize(request.GET["u"])
    host = "//" + request.get_host()
    static_url = normalize(settings.STATIC_URL)
    for prefix in (host, static_url, "/"):
        if url.startswith(prefix):
            url = url.replace(prefix, "", 1)
    response = ""
    (content_type, encoding) = mimetypes.guess_type(url)
    if content_type is None:
        content_type = "application/octet-stream"
    path = finders.find(url)
    if path:
        if isinstance(path, (list, tuple)):
            path = path[0]
        if url.endswith(".htm"):
            # Inject <base href="{{ STATIC_URL }}"> into TinyMCE
            # plugins, since the path static files in these won't be
            # on the same domain.
            static_url = settings.STATIC_URL + os.path.split(url)[0] + "/"
            if not urlparse(static_url).scheme:
                static_url = urljoin(host, static_url)
            base_tag = "<base href='%s'>" % static_url
            with open(path) as f:
                response = f.read().replace("<head>", "<head>" + base_tag)
        else:
            try:
                with open(path, "rb") as f:
                    response = f.read()
            except OSError:
                return HttpResponseNotFound()
    return HttpResponse(response, content_type=content_type)


@staff_member_required
def displayable_links_js(request):
    """
    Renders a list of url/title pairs for all ``Displayable`` subclass
    instances into JSON that's used to populate a list of links in
    TinyMCE.
    """
    if not has_site_permission(request.user):
        raise PermissionDenied
    links = []
    if "mezzanine.pages" in settings.INSTALLED_APPS:
        from mezzanine.pages.models import Page

        is_page = lambda obj: isinstance(obj, Page)
    else:
        is_page = lambda obj: False
    # For each item's title, we use its model's verbose_name, but in the
    # case of Page subclasses, we just use "Page", and then sort the items
    # by whether they're a Page subclass or not, then by their URL.
    for url, obj in Displayable.objects.url_map(for_user=request.user).items():
        title = getattr(obj, "titles", obj.title)
        real = hasattr(obj, "id")
        page = is_page(obj)
        if real:
            verbose_name = _("Page") if page else obj._meta.verbose_name
            title = f"{verbose_name}: {title}"
        links.append((not page and real, {"title": str(title), "value": url}))
    sorted_links = sorted(links, key=lambda link: (link[0], link[1]["value"]))
    return JsonResponse([link[1] for link in sorted_links], safe=False)


@requires_csrf_token
def page_not_found(request, *args, **kwargs):
    """
    Mimics Django's 404 handler but with a different template path.
    """
    context = {
        "STATIC_URL": settings.STATIC_URL,
        "request_path": request.path,
    }
    t = get_template(kwargs.get("template_name", "errors/404.html"))
    return HttpResponseNotFound(t.render(context, request))


@requires_csrf_token
def server_error(request, template_name="errors/500.html"):
    """
    Mimics Django's error handler but adds ``STATIC_URL`` to the
    context.
    """
    context = {"STATIC_URL": settings.STATIC_URL}
    t = get_template(template_name)
    return HttpResponseServerError(t.render(context, request))
