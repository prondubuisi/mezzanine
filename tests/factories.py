"""
Test object factories.

Callables, not factory_boy — keep the testing extra lean. Wave 3 tests
(PR-019+) should build on these instead of ``Model.objects.create``.
Do not rewrite the existing unittest suite onto them in this PR.
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
    Non-superuser staff user with ``SitePermission`` on the current site.

    This is the Wave 3 "author" stand-in until ``SiteRole`` exists (PR-023a).
    """
    kwargs.setdefault("is_staff", True)
    kwargs.setdefault("is_superuser", False)
    kwargs.setdefault("username", f"author-{next(_user_seq)}")
    user = UserFactory(password=password, **kwargs)
    grant_site_permission(user, site_id=site_id)
    return user


def grant_site_permission(user, site_id=None):
    """Attach ``SitePermission`` for ``site_id`` (default: current site)."""
    from mezzanine.core.models import SitePermission
    from mezzanine.utils.sites import current_site_id

    if site_id is None:
        site_id = current_site_id()
    perm, _created = SitePermission.objects.get_or_create(user=user)
    perm.sites.add(site_id)
    return perm


def PageFactory(**kwargs):
    from mezzanine.pages.models import Page

    kwargs.setdefault("title", f"Page {next(_page_seq)}")
    return Page.objects.create(**kwargs)


def RichTextPageFactory(**kwargs):
    from mezzanine.pages.models import RichTextPage

    kwargs.setdefault("title", f"Rich text page {next(_page_seq)}")
    kwargs.setdefault("content", "<p>Content</p>")
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
