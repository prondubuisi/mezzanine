import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.management import CommandError
from django.http import HttpResponse
from django.test import RequestFactory, override_settings

import mezzanine
from mezzanine.core.management.commands.createdb import (
    DEFAULT_PASSWORD,
    DEFAULT_USERNAME,
)
from mezzanine.core.management.commands.createdb import (
    Command as CreateDBCommand,
)
from mezzanine.core.middleware import ContentSecurityPolicyMiddleware

User = get_user_model()
REPO_ROOT = Path(mezzanine.__file__).resolve().parent.parent


def _createdb_command(interactive=False):
    cmd = CreateDBCommand()
    cmd.verbosity = 0
    cmd.interactive = interactive
    return cmd


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_createdb_refuses_default_account_when_debug_false():
    User.objects.all().delete()
    with pytest.raises(CommandError, match="DEBUG=False"):
        _createdb_command(interactive=False).create_user()
    assert not User.objects.filter(username=DEFAULT_USERNAME).exists()


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_createdb_creates_default_account_when_debug_true():
    User.objects.all().delete()
    _createdb_command(interactive=False).create_user()
    user = User.objects.get(username=DEFAULT_USERNAME)
    assert user.check_password(DEFAULT_PASSWORD)
    assert user.is_superuser


def test_csp_sets_nonce_and_default_header():
    middleware = ContentSecurityPolicyMiddleware(lambda request: HttpResponse("ok"))
    request = RequestFactory().get("/")
    response = middleware(request)
    assert getattr(request, "csp_nonce", None)
    policy = response["Content-Security-Policy"]
    assert "default-src 'self'" in policy
    assert "object-src 'none'" in policy


def test_csp_does_not_overwrite_existing_header():
    def view(request):
        response = HttpResponse("ok")
        response["Content-Security-Policy"] = "default-src 'none'"
        return response

    middleware = ContentSecurityPolicyMiddleware(view)
    response = middleware(RequestFactory().get("/"))
    assert response["Content-Security-Policy"] == "default-src 'none'"


@override_settings(CONTENT_SECURITY_POLICY="script-src 'nonce-{nonce}'")
def test_csp_custom_policy_substitutes_nonce():
    middleware = ContentSecurityPolicyMiddleware(lambda request: HttpResponse("ok"))
    request = RequestFactory().get("/")
    response = middleware(request)
    assert response["Content-Security-Policy"] == (
        "script-src 'nonce-%s'" % request.csp_nonce
    )


def test_command_source_has_no_imp_or_distutils():
    source = (
        REPO_ROOT / "mezzanine/bin/management/commands/mezzanine_project.py"
    ).read_text()
    assert re.search(r"^import imp\b", source, re.M) is None
    assert "distutils" not in source
    assert "copytree" in source


def test_template_settings_has_no_imp():
    source = (
        REPO_ROOT / "mezzanine/project_template/project_name/settings.py"
    ).read_text()
    assert re.search(r"^    import imp\b", source, re.M) is None
    assert "from .local_settings import *" in source
    assert "SecurityMiddleware" in source
    assert "ContentSecurityPolicyMiddleware" in source
    assert "AUTH_PASSWORD_VALIDATORS" in source
    assert "NEVERCACHE_KEY" in source
    assert "if not DEBUG:" in source
    debug_block = source.split("from .local_settings import *", 1)[1]
    assert "if not DEBUG:" in debug_block
    assert "SECURE_SSL_REDIRECT = True" in debug_block


def test_template_ships_asgi():
    asgi = REPO_ROOT / "mezzanine/project_template/project_name/asgi.py"
    assert asgi.is_file()
    assert "get_asgi_application" in asgi.read_text()


def test_ssl_redirect_middleware_removed():
    source = (REPO_ROOT / "mezzanine/core/middleware.py").read_text()
    assert "class SSLRedirectMiddleware" not in source
    assert "class ContentSecurityPolicyMiddleware" in source


def test_ssl_settings_unregistered():
    from mezzanine.conf import registry

    for name in (
        "SSL_ENABLED",
        "SSL_FORCE_HOST",
        "SSL_FORCE_URL_PREFIXES",
        "SSL_FORCED_PREFIXES_ONLY",
    ):
        assert name not in registry


def test_nova_project_writes_hardened_project(tmp_path):
    env = os.environ.copy()
    env.pop("DJANGO_SETTINGS_MODULE", None)
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "sys.argv = ['nova-project', 'mysite']; "
                "from mezzanine.bin.mezzanine_project import create_project; "
                "create_project()"
            ),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    project_app = tmp_path / "mysite" / "mysite"
    assert (project_app / "asgi.py").is_file()
    assert (project_app / "wsgi.py").is_file()
    assert (project_app / "local_settings.py").is_file()
    settings_text = (project_app / "settings.py").read_text()
    assert "import imp" not in settings_text
    assert "SecurityMiddleware" in settings_text
    assert "ContentSecurityPolicyMiddleware" in settings_text
    assert "AUTH_PASSWORD_VALIDATORS" in settings_text
    local_path = project_app / "local_settings.py"
    local_text = local_path.read_text()
    assert "SESSION_COOKIE_SECURE = False" not in local_text
    assert "SECURE_SSL_REDIRECT = False" not in local_text
    assert "if not DEBUG:" in settings_text
    match = re.search(r'NEVERCACHE_KEY = "([^"]+)"', local_text)
    assert match, local_text
    assert len(match.group(1)) == 50
    assert "{{" not in match.group(1)

    probe = (
        "import sys; sys.path.insert(0, '.'); "
        "from mysite import settings; "
        "print(settings.DEBUG, "
        "settings.SESSION_COOKIE_SECURE, "
        "settings.SECURE_SSL_REDIRECT)"
    )
    debug_true = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=tmp_path / "mysite",
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert debug_true.returncode == 0, debug_true.stderr
    assert debug_true.stdout.strip() == "True False False"

    local_path.write_text(
        re.sub(r"^DEBUG = True$", "DEBUG = False", local_text, count=1, flags=re.M)
    )
    debug_false = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=tmp_path / "mysite",
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert debug_false.returncode == 0, debug_false.stderr
    assert debug_false.stdout.strip() == "False True True"
