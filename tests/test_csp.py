"""Content-Security-Policy middleware (default + strict)."""

from django.http import HttpResponse
from django.test import RequestFactory, override_settings

from mezzanine.core.middleware import ContentSecurityPolicyMiddleware


def _run(mw, path="/"):
    rf = RequestFactory()
    request = rf.get(path)
    mw.process_request(request)
    response = HttpResponse("ok")
    return mw.process_response(request, response), request


def test_default_csp_allows_unsafe_inline_scripts():
    mw = ContentSecurityPolicyMiddleware(lambda r: HttpResponse())
    response, request = _run(mw)
    csp = response["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    assert "'unsafe-inline'" in csp
    assert getattr(request, "csp_nonce", None)


@override_settings(NOVA_CSP_STRICT=True)
def test_strict_csp_uses_nonce_for_scripts():
    mw = ContentSecurityPolicyMiddleware(lambda r: HttpResponse())
    response, request = _run(mw)
    csp = response["Content-Security-Policy"]
    nonce = request.csp_nonce
    assert f"'nonce-{nonce}'" in csp
    assert "script-src 'self' 'nonce-" in csp
    # Strict drops unsafe-inline on scripts (style may keep it).
    script_part = [p for p in csp.split(";") if "script-src" in p][0]
    assert "'unsafe-inline'" not in script_part
    assert "form-action 'self'" in csp


@override_settings(
    CONTENT_SECURITY_POLICY="default-src 'none'; script-src 'nonce-{nonce}'"
)
def test_custom_policy_placeholder():
    mw = ContentSecurityPolicyMiddleware(lambda r: HttpResponse())
    response, request = _run(mw)
    csp = response["Content-Security-Policy"]
    assert request.csp_nonce in csp
    assert "{nonce}" not in csp
