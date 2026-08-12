from copy import deepcopy

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from mezzanine.blog.models import BlogCategory, BlogPost
from mezzanine.conf import settings
from mezzanine.core.admin import (
    BaseTranslationModelAdmin,
    DisplayableAdmin,
    OwnableAdmin,
    extend_fieldsets,
)

_blogpost_insertions = [
    (1, "categories"),
    "content",
    "allow_comments",
]
blogpost_list_display = ["title", "user", "status", "admin_link", "view_draft_link"]
if settings.BLOG_USE_FEATURED_IMAGE:
    _blogpost_insertions.append((-2, "featured_image"))
    blogpost_list_display.insert(0, "admin_thumb")
_blogpost_insertions.append(
    (
        1,
        (
            _("Other posts"),
            {"classes": ("collapse-closed",), "fields": ("related_posts",)},
        ),
    )
)
blogpost_fieldsets = extend_fieldsets(
    DisplayableAdmin.fieldsets, _blogpost_insertions
)
blogpost_list_filter = deepcopy(DisplayableAdmin.list_filter) + ("categories",)


class BlogPostAdmin(DisplayableAdmin, OwnableAdmin):
    """
    Admin class for blog posts.
    """

    fieldsets = blogpost_fieldsets
    list_display = blogpost_list_display
    list_filter = blogpost_list_filter
    filter_horizontal = (
        "categories",
        "related_posts",
    )

    def save_form(self, request, form, change):
        """
        Super class ordering is important here - user must get saved first.
        """
        OwnableAdmin.save_form(self, request, form, change)
        return DisplayableAdmin.save_form(self, request, form, change)


class BlogCategoryAdmin(BaseTranslationModelAdmin):
    """
    Admin class for blog categories. Hides itself from the admin menu
    unless explicitly specified.
    """

    fieldsets = ((None, {"fields": ("title",)}),)

    def has_module_permission(self, request):
        """
        Hide from the admin menu unless explicitly set in ``ADMIN_MENU_ORDER``.
        """
        for (name, items) in settings.ADMIN_MENU_ORDER:
            if "blog.BlogCategory" in items:
                return True
        return False


admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(BlogCategory, BlogCategoryAdmin)
