"""
Test object factories.

Callables, not factory_boy — keep the testing extra lean. Wave 3 tests
(PR-019+) should build on these instead of ``Model.objects.create``.
Page/BlogPost factories default to Published; the model default is Draft.
"""

from itertools import count

_user_seq = count(1)
_page_seq = count(1)
_blog_seq = count(1)

DEFAULT_PASSWORD = "test"


def UserFactory(*, password=DEFAULT_PASSWORD, **kwargs):
    """Create a user. ``password`` is the raw password (hashed on save)."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    is_superuser = kwargs.pop("is_superuser", False)
    is_staff = kwargs.pop("is_staff", is_superuser)
    n = next(_user_seq)
    username = kwargs.pop("username", f"user-{n}")
    email = kwargs.pop("email", f"{username}@example.com")
    if is_superuser:
        return User.objects.create_superuser(
            username, email, password, is_staff=True, **kwargs
        )
    return User.objects.create_user(
        username, email, password, is_staff=is_staff, is_superuser=False, **kwargs
    )


def SuperUserFactory(*, password=DEFAULT_PASSWORD, **kwargs):
    """Create a superuser (the historic TestCase default)."""
    kwargs.setdefault("is_superuser", True)
    kwargs.setdefault("is_staff", True)
    return UserFactory(password=password, **kwargs)


def AuthorFactory(*, password=DEFAULT_PASSWORD, site_id=None, **kwargs):
    """
    Non-superuser staff user with a ``SiteRole`` of ``author`` on
    the current site.
    """
    kwargs.setdefault("is_staff", True)
    kwargs.setdefault("is_superuser", False)
    kwargs.setdefault("username", f"author-{next(_user_seq)}")
    user = UserFactory(password=password, **kwargs)
    grant_site_permission(user, site_id=site_id, role="author")
    return user


def EditorFactory(*, password=DEFAULT_PASSWORD, site_id=None, **kwargs):
    """Staff user with an ``editor`` SiteRole."""
    kwargs.setdefault("is_staff", True)
    kwargs.setdefault("is_superuser", False)
    kwargs.setdefault("username", f"editor-{next(_user_seq)}")
    user = UserFactory(password=password, **kwargs)
    grant_site_permission(user, site_id=site_id, role="editor")
    return user


def PublisherFactory(*, password=DEFAULT_PASSWORD, site_id=None, **kwargs):
    """Staff user with a ``publisher`` SiteRole (can issue preview tokens)."""
    kwargs.setdefault("is_staff", True)
    kwargs.setdefault("is_superuser", False)
    kwargs.setdefault("username", f"publisher-{next(_user_seq)}")
    user = UserFactory(password=password, **kwargs)
    grant_site_permission(user, site_id=site_id, role="publisher")
    return user


def grant_site_permission(user, site_id=None, role="editor"):
    """Attach a ``SiteRole`` for ``site_id`` (default: current site)."""
    from django.contrib.sites.models import Site

    from mezzanine.core.models import SiteRole
    from mezzanine.utils.sites import current_site_id

    if site_id is None:
        site_id = current_site_id()
    site = Site.objects.get(pk=site_id)
    role_row, _created = SiteRole.objects.get_or_create(
        user=user, site=site, defaults={"role": role}
    )
    return role_row


def PageFactory(**kwargs):
    from mezzanine.core.models import CONTENT_STATUS_PUBLISHED
    from mezzanine.pages.models import Page

    kwargs.setdefault("title", f"Page {next(_page_seq)}")
    kwargs.setdefault("status", CONTENT_STATUS_PUBLISHED)
    return Page.objects.create(**kwargs)


def RichTextPageFactory(**kwargs):
    from mezzanine.core.models import CONTENT_STATUS_PUBLISHED
    from mezzanine.pages.models import RichTextPage

    kwargs.setdefault("title", f"Rich text page {next(_page_seq)}")
    kwargs.setdefault("content", "<p>Content</p>")
    kwargs.setdefault("status", CONTENT_STATUS_PUBLISHED)
    return RichTextPage.objects.create(**kwargs)


def BlogPostFactory(**kwargs):
    from mezzanine.blog.models import BlogPost
    from mezzanine.core.models import CONTENT_STATUS_PUBLISHED

    kwargs.setdefault("title", f"Blog post {next(_blog_seq)}")
    kwargs.setdefault("content", "<p>Content</p>")
    kwargs.setdefault("status", CONTENT_STATUS_PUBLISHED)
    if "user" not in kwargs:
        kwargs["user"] = UserFactory()
    return BlogPost.objects.create(**kwargs)
