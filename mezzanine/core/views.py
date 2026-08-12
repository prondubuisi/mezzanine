import logging

from django.apps import apps
from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.db import connection
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
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from mezzanine.conf import settings
from mezzanine.core.capabilities import user_can_edit
from mezzanine.core.forms import get_edit_form
from mezzanine.core.logging import structured_log
from mezzanine.core.models import Displayable, SiteRole
from mezzanine.utils.sites import has_site_permission
from mezzanine.utils.urls import next_url
from mezzanine.utils.views import paginate

_health_logger = logging.getLogger("nova.health")


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


@require_GET
def healthz(request):
    """Liveness/readiness JSON for ops (PR-036b). No auth."""
    db_ok = False
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception as exc:  # noqa: BLE001 — surface as degraded
        structured_log(
            _health_logger,
            logging.ERROR,
            "healthz.db_error",
            error=str(exc),
        )
    payload = {
        "status": "ok" if db_ok else "degraded",
        "db": db_ok,
        "service": "nova-cms",
    }
    structured_log(
        _health_logger,
        logging.INFO if db_ok else logging.WARNING,
        "healthz.check",
        **payload,
    )
    return JsonResponse(payload, status=200 if db_ok else 503)


def _media_payload(asset):
    return {
        "id": asset.pk,
        "title": asset.title,
        "alt": asset.alt,
        "file": asset.file.url if asset.file else "",
        "is_public": bool(getattr(asset, "is_public", False)),
    }


@require_GET
def media_list(request):
    """Staff media library listing for current site (WP media-library parity)."""
    from mezzanine.core.models import Media
    from mezzanine.utils.sites import current_site_id

    _require_staff_site(request)
    qs = Media.objects.filter(site_id=current_site_id()).order_by("-created")[:200]
    return JsonResponse({"ok": True, "results": [_media_payload(a) for a in qs]})


@require_GET
def media_chooser(request):
    """
    Popup media picker (WP media-modal parity without filebrowser).

    Staff only. Used by TinyMCE file_picker_callback and optional field fills.
    """
    from django.db.models import Q

    from mezzanine.core.models import Media
    from mezzanine.utils.sites import current_site_id

    _require_staff_site(request)
    q = (request.GET.get("q") or "").strip()
    qs = Media.objects.filter(site_id=current_site_id()).order_by("-created")
    if q:
        qs = qs.filter(
            Q(title__icontains=q) | Q(alt__icontains=q) | Q(file__icontains=q)
        )
    return TemplateResponse(
        request,
        "admin/media_chooser.html",
        {"assets": list(qs[:100]), "q": q},
    )


@require_GET
def media_detail(request, pk):
    """
    Staff-only media metadata endpoint (PR-026).

    Returns JSON for the site-scoped Media row — not a public CDN path.
    """
    from mezzanine.core.models import Media
    from mezzanine.utils.sites import current_site_id

    _require_staff_site(request)
    try:
        asset = Media.objects.get(pk=pk, site_id=current_site_id())
    except Media.DoesNotExist:
        raise Http404 from None
    return JsonResponse(_media_payload(asset))


@require_GET
def media_public(request, pk):
    """
    Public metadata for Media rows marked ``is_public`` (KD11 promotion path).

    Not Displayable: no sitemap/search. File bytes remain on the storage URL.
    """
    from mezzanine.core.models import Media
    from mezzanine.utils.sites import current_site_id

    try:
        asset = Media.objects.get(
            pk=pk, site_id=current_site_id(), is_public=True
        )
    except Media.DoesNotExist:
        raise Http404 from None
    return JsonResponse(_media_payload(asset))


def _require_staff_site(request):
    if not request.user.is_authenticated or not (
        request.user.is_staff or request.user.is_superuser
    ):
        raise Http404
    if not request.user.is_superuser and not has_site_permission(request.user):
        raise PermissionDenied


@require_GET
def demo_sites_index(request):
    """
    Local IA site-clone lab (no auth while pre-public).

    Switch content via POST to ``demo_sites_switch`` or CLI
    ``seed_site_clone --site=… --flush``. Gate this before any public deploy.
    """
    from mezzanine.demos.site_profiles import PROFILES

    current = request.session.get("nova_demo_site", "")
    sites = [
        {
            "slug": slug,
            "name": meta.get("display_name", slug),
            "inspired_by": meta.get("inspired_by", ""),
            "tagline": meta.get("tagline", ""),
            "pages": [p[0] for p in meta.get("pages", [])],
            "post_count": len(meta.get("posts", [])),
            "active": slug == current,
        }
        for slug, meta in sorted(PROFILES.items())
    ]
    return TemplateResponse(
        request,
        "admin/demo_sites.html",
        {
            "title": "Site clone lab",
            "sites": sites,
            "current": current,
            "switch_hint": "just demo-clone <slug> --flush",
        },
    )


@require_POST
def demo_sites_switch(request):
    """Load a named IA clone (no auth while pre-public). Gate before deploy."""
    from django.contrib import messages
    from django.core.management import call_command
    from django.http import HttpResponseRedirect

    from mezzanine.demos.site_profiles import get_profile

    slug = (request.POST.get("site") or "").strip()
    try:
        get_profile(slug)
    except KeyError:
        raise Http404 from None
    call_command("seed_site_clone", site=slug, flush=True, verbosity=0)
    request.session["nova_demo_site"] = slug
    messages.success(
        request,
        "Switched demo content to %s. Hard-refresh if needed." % slug,
    )
    return HttpResponseRedirect("/")


@require_GET
def api_openapi(request):
    """Minimal OpenAPI 3 skeleton for private Nova API (PR-036)."""
    _require_staff_site(request)
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "Nova private API",
            "version": "0.1.0",
            "description": "Staff-only endpoints under /_nova/.",
        },
        "paths": {
            "/_nova/healthz": {
                "get": {
                    "summary": "Health check",
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/_nova/api/resolve": {
                "get": {
                    "summary": "Resolve a path or URL to a Displayable",
                    "parameters": [
                        {
                            "name": "path",
                            "in": "query",
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {"description": "Resolved object"},
                        "404": {"description": "Not found"},
                    },
                }
            },
            "/_nova/media/": {
                "get": {
                    "summary": "List media for current site",
                    "responses": {"200": {"description": "Media list"}},
                }
            },
            "/_nova/media/chooser/": {
                "get": {
                    "summary": "HTML media chooser popup",
                    "responses": {"200": {"description": "Chooser UI"}},
                }
            },
            "/_nova/media/{pk}/": {
                "get": {
                    "summary": "Media metadata (staff)",
                    "parameters": [
                        {
                            "name": "pk",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {"200": {"description": "Media row"}},
                }
            },
            "/_nova/media/{pk}/public/": {
                "get": {
                    "summary": "Public media metadata (is_public only)",
                    "parameters": [
                        {
                            "name": "pk",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {"description": "Public media row"},
                        "404": {"description": "Not public or missing"},
                    },
                }
            },
        },
    }
    return JsonResponse(spec)


@require_GET
def api_resolve(request):
    """
    Resolve a site path to a published Displayable (PR-036).

    Staff-only. Query ``?path=/about/`` (absolute path on current site).
    """
    _require_staff_site(request)
    raw = (request.GET.get("path") or request.GET.get("url") or "").strip()
    if not raw:
        return JsonResponse(
            {"ok": False, "error": "path required"}, status=400
        )
    # Accept absolute URLs; use path component only.
    if "://" in raw:
        from urllib.parse import urlparse

        raw = urlparse(raw).path or "/"
    if not raw.startswith("/"):
        raw = "/" + raw
    url_map = Displayable.objects.url_map(for_user=request.user)
    # url_map keys are typically absolute paths or full paths.
    obj = url_map.get(raw)
    if obj is None:
        # Try with/without trailing slash.
        alt = raw.rstrip("/") or "/"
        if alt != raw:
            obj = url_map.get(alt)
        if obj is None and not raw.endswith("/"):
            obj = url_map.get(raw + "/")
    if obj is None or not hasattr(obj, "id"):
        raise Http404
    return JsonResponse(
        {
            "ok": True,
            "id": obj.pk,
            "title": str(getattr(obj, "titles", None) or obj.title),
            "model": f"{obj._meta.app_label}.{obj._meta.model_name}",
            "path": raw,
            "status": getattr(obj, "status", None),
        }
    )
