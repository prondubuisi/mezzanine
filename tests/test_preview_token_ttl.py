"""PR-040: PREVIEW_TOKEN_TTL_SECONDS setting (DESIGN.md Amendment 2, H1).

Default TTL is 24h via the registered setting; override_settings is honored;
an explicit expires_at still wins.
"""

from datetime import timedelta

import pytest
from django.test import override_settings
from django.utils.timezone import now

from mezzanine.conf import settings
from mezzanine.core.models import PreviewToken
from tests.factories import RichTextPageFactory

pytestmark = pytest.mark.django_db


def test_preview_token_ttl_setting_default():
    """Characterization: registered default is 86400 (24h)."""
    assert settings.PREVIEW_TOKEN_TTL_SECONDS == 86400


def test_issue_default_ttl_is_24_hours(author_user):
    page = RichTextPageFactory(title="TTL Default")
    before = now()
    PreviewToken.issue(page, created_by=author_user)
    after = now()
    token = PreviewToken.objects.get()
    # expires_at is between before+ttl and after+ttl (clock skew bound)
    assert token.expires_at >= before + timedelta(seconds=86400) - timedelta(seconds=2)
    assert token.expires_at <= after + timedelta(seconds=86400) + timedelta(seconds=2)


@override_settings(PREVIEW_TOKEN_TTL_SECONDS=120)
def test_issue_respects_preview_token_ttl_seconds(author_user):
    page = RichTextPageFactory(title="TTL Override")
    before = now()
    PreviewToken.issue(page, created_by=author_user)
    after = now()
    token = PreviewToken.objects.get()
    assert token.expires_at >= before + timedelta(seconds=120) - timedelta(seconds=2)
    assert token.expires_at <= after + timedelta(seconds=120) + timedelta(seconds=2)
    # Must not still use the 24h default
    assert token.expires_at < before + timedelta(hours=1)


def test_issue_explicit_expires_at_wins(author_user):
    page = RichTextPageFactory(title="TTL Explicit")
    explicit = now() + timedelta(minutes=15)
    PreviewToken.issue(page, created_by=author_user, expires_at=explicit)
    token = PreviewToken.objects.get()
    assert abs((token.expires_at - explicit).total_seconds()) < 1
