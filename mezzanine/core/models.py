import hashlib
import hmac
import secrets
from datetime import timedelta

from django.apps import apps
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.db import models
from django.db.models.base import ModelBase
from django.template.defaultfilters import truncatewords_html
from django.utils.html import format_html, strip_tags
from django.utils.timesince import timesince
from django.utils.timezone import now
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from mezzanine.conf import settings
from mezzanine.core.fields import OrderField, RichTextField
from mezzanine.core.managers import CurrentSiteManager, DisplayableManager
from mezzanine.generic.fields import KeywordsField
from mezzanine.utils.html import TagCloser
from mezzanine.utils.models import base_concrete_model, get_user_model_name
from mezzanine.utils.sites import current_request, current_site_id
from mezzanine.utils.urls import admin_url, slugify, unique_slug

user_model_name = get_user_model_name()


def wrapped_manager(klass):
    if settings.USE_MODELTRANSLATION:
        from modeltranslation.manager import MultilingualManager

        class Mgr(MultilingualManager, klass):
            pass

        return Mgr()
    else:
        return klass()


class SiteRelated(models.Model):
    """
    Abstract model for all things site-related. Adds a foreignkey to
    Django's ``Site`` model, and filters by site with all querysets.
    See ``mezzanine.utils.sites.current_site_id`` for implementation
    details.
    """

    objects = wrapped_manager(CurrentSiteManager)

    class Meta:
        abstract = True

    site = models.ForeignKey("sites.Site", on_delete=models.CASCADE, editable=False)

    def save(self, update_site=False, *args, **kwargs):
        """
        Set the site to the current site when the record is first
        created, or the ``update_site`` argument is explicitly set
        to ``True``.
        """
        if update_site or (self.id is None and self.site_id is None):
            self.site_id = current_site_id()
        super().save(*args, **kwargs)


class Slugged(SiteRelated):
    """
    Abstract model that handles auto-generating slugs. Each slugged
    object is also affiliated with a specific site object.
    """

    title = models.CharField(_("Title"), max_length=500)
    slug = models.CharField(
        _("URL"),
        max_length=2000,
        blank=True,
        help_text=_("Leave blank to have the URL auto-generated from " "the title."),
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        If no slug is provided, generates one before saving.
        """
        if not self.slug:
            self.slug = self.generate_unique_slug()
        super().save(*args, **kwargs)

    def generate_unique_slug(self):
        """
        Create a unique slug by passing the result of get_slug() to
        utils.urls.unique_slug, which appends an index if necessary.
        """
        # For custom content types, use the ``Page`` instance for
        # slug lookup.
        concrete_model = base_concrete_model(Slugged, self)
        slug_qs = concrete_model.objects.exclude(id=self.id)
        return unique_slug(slug_qs, "slug", self.get_slug())

    def get_slug(self):
        """
        Allows subclasses to implement their own slug creation logic.
        """
        attr = "title"
        if settings.USE_MODELTRANSLATION:
            from modeltranslation.utils import build_localized_fieldname

            attr = build_localized_fieldname(attr, settings.LANGUAGE_CODE)
        # Get self.title_xx where xx is the default language, if any.
        # Get self.title otherwise.
        return slugify(getattr(self, attr, None) or self.title)

    def admin_link(self):
        return format_html(
            "<a href='{}'>{}</a>", self.get_absolute_url(), gettext("View on site")
        )

    admin_link.short_description = ""


class MetaData(models.Model):
    """
    Abstract model that provides meta data for content.
    """

    _meta_title = models.CharField(
        _("Title"),
        null=True,
        blank=True,
        max_length=500,
        help_text=_(
            "Optional title to be used in the HTML title tag. "
            "If left blank, the main title field will be used."
        ),
    )
    description = models.TextField(_("Description"), blank=True)
    gen_description = models.BooleanField(
        _("Generate description"),
        help_text=_(
            "If checked, the description will be automatically "
            "generated from content. Uncheck if you want to manually "
            "set a custom description."
        ),
        default=True,
    )
    keywords = KeywordsField(verbose_name=_("Keywords"))

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
        Set the description field on save.
        """
        if self.gen_description:
            self.description = strip_tags(self.description_from_content())
        super().save(*args, **kwargs)

    def meta_title(self):
        """
        Accessor for the optional ``_meta_title`` field, which returns
        the string version of the instance if not provided.
        """
        return self._meta_title or getattr(self, "title", str(self))

    def description_from_content(self):
        """
        Returns the first block or sentence of the first content-like
        field.
        """
        description = ""
        # Use the first RichTextField, or TextField if none found.
        for field_type in (RichTextField, models.TextField):
            if not description:
                for field in self._meta.get_fields():
                    if isinstance(field, field_type) and field.name != "description":
                        description = getattr(self, field.name)
                        if description:
                            from mezzanine.core.templatetags.mezzanine_tags import (
                                richtext_filters,
                            )

                            description = richtext_filters(description)
                            break
        # Fall back to the title if description couldn't be determined.
        if not description:
            description = str(self)
        # Strip everything after the first block or sentence.
        ends = ("</p>", "<br />", "<br/>", "<br>", "</ul>", "\n", ". ", "! ", "? ")
        for end in ends:
            pos = description.lower().find(end)
            if pos > -1:
                description = TagCloser(description[:pos]).html
                break
        else:
            description = truncatewords_html(description, 100)
        try:
            description = unicode(description)
        except NameError:
            pass  # Python 3.
        return description


class TimeStamped(models.Model):
    """
    Provides created and updated timestamps on models.
    """

    class Meta:
        abstract = True

    created = models.DateTimeField(null=True, editable=False)
    updated = models.DateTimeField(null=True, editable=False)

    def save(self, *args, **kwargs):
        _now = now()
        self.updated = _now
        if not self.id:
            self.created = _now
        super().save(*args, **kwargs)


CONTENT_STATUS_DRAFT = 1
CONTENT_STATUS_PUBLISHED = 2
CONTENT_STATUS_CHOICES = (
    (CONTENT_STATUS_DRAFT, _("Draft")),
    (CONTENT_STATUS_PUBLISHED, _("Published")),
)

SHORT_URL_UNSET = "unset"


class Displayable(Slugged, MetaData, TimeStamped):
    """
    Abstract model that provides features of a visible page on the
    website such as publishing fields. Basis of Mezzanine pages,
    blog posts, and Cartridge products.
    """

    status = models.IntegerField(
        _("Status"),
        choices=CONTENT_STATUS_CHOICES,
        default=CONTENT_STATUS_DRAFT,
        help_text=_(
            "With Draft chosen, the public URL returns 404 unless a "
            "preview token is used."
        ),
    )
    publish_date = models.DateTimeField(
        _("Published from"),
        help_text=_("With Published chosen, won't be shown until this time"),
        blank=True,
        null=True,
        db_index=True,
    )
    expiry_date = models.DateTimeField(
        _("Expires on"),
        help_text=_("With Published chosen, won't be shown after this time"),
        blank=True,
        null=True,
    )
    short_url = models.URLField(blank=True, null=True)
    in_sitemap = models.BooleanField(_("Show in sitemap"), default=True)
    # KD20 / PR-058: typed custom field values keyed by FieldSchema.name.
    custom_fields = models.JSONField(_("Custom fields"), default=dict, blank=True)

    objects = wrapped_manager(DisplayableManager)
    search_fields = {"keywords": 10, "title": 5}

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
        Set default for ``publish_date``. We can't use ``auto_now_add`` on
        the field as it will be blank when a blog post is created from
        the quick blog form in the admin dashboard.
        """
        if self.publish_date is None:
            self.publish_date = now()
        if self.custom_fields is None:
            self.custom_fields = {}
        super().save(*args, **kwargs)

    def get_custom_field(self, name, default=None):
        """Return a value from ``custom_fields`` by schema name."""
        data = self.custom_fields or {}
        return data.get(name, default)

    def set_custom_field(self, name, value, *, save=False):
        """Set a custom field value. Optionally persist immediately."""
        data = dict(self.custom_fields or {})
        data[name] = value
        self.custom_fields = data
        if save:
            self.save(update_fields=["custom_fields"])
        return self

    def get_admin_url(self):
        return admin_url(self, "change", self.id)

    def publish_date_since(self):
        """
        Returns the time since ``publish_date``.
        """
        return timesince(self.publish_date)

    publish_date_since.short_description = _("Published from")

    def published(self):
        """
        Return True when status is published and the publish/expiry
        dates (when set) contain now.

        This instance method does not inspect the requesting user.
        Drafts on the public slug 404 unless a ``preview`` token
        unions that object in ``PublishedManager.published``. This
        method stays date/status-only.
        """
        return (
            self.status == CONTENT_STATUS_PUBLISHED
            and (self.publish_date is None or self.publish_date <= now())
            and (self.expiry_date is None or self.expiry_date >= now())
        )

    def get_absolute_url(self):
        """
        Raise an error if called on a subclass without
        ``get_absolute_url`` defined, to ensure all search results
        contains a URL.
        """
        name = self.__class__.__name__
        raise NotImplementedError(
            "The model %s does not have " "get_absolute_url defined" % name
        )

    def get_absolute_url_with_host(self):
        """
        Returns host + ``get_absolute_url`` - used by the various
        ``short_url`` mechanics below.

        Technically we should use ``self.site.domain``, here, however
        if we were to invoke the ``short_url`` mechanics on a list of
        data (eg blog post list view), we'd trigger a db query per
        item. Using ``current_request`` should provide the same
        result, since site related data should only be loaded based
        on the current host anyway.
        """
        return current_request().build_absolute_uri(self.get_absolute_url())

    def set_short_url(self):
        """
        Ensure ``short_url`` is available for templates.

        No shortening service is called. A stored value is kept; the
        legacy ``"unset"`` marker (previously written when bit.ly was
        unavailable) is treated as empty. Otherwise the full absolute
        URL is used in memory and is not persisted.
        """
        if self.short_url and self.short_url != SHORT_URL_UNSET:
            return
        generated = self.generate_short_url()
        if generated and generated != SHORT_URL_UNSET:
            self.short_url = generated
            self.save()
        else:
            self.short_url = self.get_absolute_url_with_host()

    def generate_short_url(self):
        """
        Return a shortened URL, or ``None``.

        Previously called bit.ly. No network request is made. Subclasses
        may override. The ``"unset"`` sentinel is no longer written.
        """
        return None

    def _get_next_or_previous_by_publish_date(self, is_next, **kwargs):
        """
        Retrieves next or previous object by publish date. We implement
        our own version instead of Django's so we can hook into the
        published manager and concrete subclasses.
        """
        arg = "publish_date__gt" if is_next else "publish_date__lt"
        order = "publish_date" if is_next else "-publish_date"
        lookup = {arg: self.publish_date}
        concrete_model = base_concrete_model(Displayable, self)
        try:
            queryset = concrete_model.objects.published
        except AttributeError:
            queryset = concrete_model.objects.all
        try:
            return queryset(**kwargs).filter(**lookup).order_by(order)[0]
        except IndexError:
            pass

    def get_next_by_publish_date(self, **kwargs):
        """
        Retrieves next object by publish date.
        """
        return self._get_next_or_previous_by_publish_date(True, **kwargs)

    def get_previous_by_publish_date(self, **kwargs):
        """
        Retrieves previous object by publish date.
        """
        return self._get_next_or_previous_by_publish_date(False, **kwargs)


class RichText(models.Model):
    """
    Provides a Rich Text field for managing general content and making
    it searchable.
    """

    content = RichTextField(_("Content"))

    search_fields = ("content",)

    class Meta:
        abstract = True


class DocumentBody(models.Model):
    """
    Y1.5 JSON document body (PR-025 / KD7).

    Concrete RichText models also inherit this. ``content`` is the HTML
    projection of ``body`` (version N: wrap on first save).
    """

    body = models.JSONField(_("Body"), default=dict, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        from mezzanine.core.document import sync_content_from_body

        sync_content_from_body(self)
        super().save(*args, **kwargs)


def _media_upload_to(instance, filename):
    """Site-prefixed storage path (PR-026)."""
    site_id = getattr(instance, "site_id", None) or current_site_id()
    # Keep basename only to avoid path traversal.
    base = filename.replace("\\", "/").rsplit("/", 1)[-1] or "file.bin"
    return "media/site-%s/%s" % (site_id, base)


class Media(SiteRelated):
    """
    Site-scoped media asset (PR-026 / KD11).

    Not Displayable in Y1.5: no public URL tree, not in sitemaps/search.
    ``alt`` is required. File path is site-prefixed under MEDIA_ROOT.
    """

    title = models.CharField(_("Title"), max_length=500, blank=True)
    file = models.FileField(_("File"), upload_to=_media_upload_to, max_length=255)
    alt = models.CharField(
        _("Alt text"),
        max_length=255,
        help_text=_("Required accessible description of the file."),
    )
    # KD11: still SiteRelated (not Displayable). When True, metadata is
    # readable without staff auth at /_nova/media/<pk>/public/ — file bytes
    # remain on the storage URL. Not in sitemaps/search.
    is_public = models.BooleanField(
        _("Public"),
        default=False,
        help_text=_(
            "Allow unauthenticated clients to read metadata for this asset. "
            "Does not put the file in the page tree or sitemap."
        ),
    )
    created = models.DateTimeField(_("Created"), auto_now_add=True)
    updated = models.DateTimeField(_("Updated"), auto_now=True)

    class Meta:
        verbose_name = _("Media")
        verbose_name_plural = _("Media")
        ordering = ("-created",)

    def __str__(self):
        return self.title or self.alt or str(self.pk)

    def get_absolute_url(self):
        # Staff private path under /_nova/media/<pk>/ — not the storage URL.
        from django.urls import reverse

        if self.is_public:
            return reverse("nova_media_public", kwargs={"pk": self.pk})
        return reverse("nova_media_detail", kwargs={"pk": self.pk})


class OrderableBase(ModelBase):
    """
    Checks for ``order_with_respect_to`` on the model's inner ``Meta``
    class and if found, copies it to a custom attribute and deletes it
    since it will cause errors when used with ``ForeignKey("self")``.
    Also creates the ``ordering`` attribute on the ``Meta`` class if
    not yet provided.
    """

    def __new__(cls, name, bases, attrs):
        if "Meta" not in attrs:

            class Meta:
                pass

            attrs["Meta"] = Meta
        if hasattr(attrs["Meta"], "order_with_respect_to"):
            order_field = attrs["Meta"].order_with_respect_to
            attrs["order_with_respect_to"] = order_field
            del attrs["Meta"].order_with_respect_to
        if not hasattr(attrs["Meta"], "ordering"):
            setattr(attrs["Meta"], "ordering", ("_order",))
        return super().__new__(cls, name, bases, attrs)


class Orderable(models.Model, metaclass=OrderableBase):
    """
    Abstract model that provides a custom ordering integer field
    similar to using Meta's ``order_with_respect_to``, since to
    date (Django 1.2) this doesn't work with ``ForeignKey("self")``,
    or with Generic Relations. We may also want this feature for
    models that aren't ordered with respect to a particular field.
    """

    _order = OrderField(_("Order"), null=True)

    class Meta:
        abstract = True

    def with_respect_to(self):
        """
        Returns a dict to use as a filter for ordering operations
        containing the original ``Meta.order_with_respect_to`` value
        if provided. If the field is a Generic Relation, the dict
        returned contains names and values for looking up the
        relation's ``ct_field`` and ``fk_field`` attributes.
        """
        try:
            name = self.order_with_respect_to
            value = getattr(self, name)
        except AttributeError:
            # No ``order_with_respect_to`` specified on the model.
            return {}
        # Support for generic relations. Django 6 binds GFKs as
        # GenericForeignKeyDescriptor on the class; the field lives on .field.
        field = getattr(self.__class__, name)
        gfk = (
            field
            if isinstance(field, GenericForeignKey)
            else getattr(field, "field", None)
        )
        if isinstance(gfk, GenericForeignKey):
            names = (gfk.ct_field, gfk.fk_field)
            return {n: getattr(self, n) for n in names}
        return {name: value}

    def save(self, *args, **kwargs):
        """
        Set the initial ordering value.
        """
        if self._order is None:
            lookup = self.with_respect_to()
            lookup["_order__isnull"] = False
            concrete_model = base_concrete_model(Orderable, self)
            self._order = concrete_model.objects.filter(**lookup).count()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Update the ordering values for siblings.
        """
        lookup = self.with_respect_to()
        lookup["_order__gte"] = self._order
        concrete_model = base_concrete_model(Orderable, self)
        after = concrete_model.objects.filter(**lookup)
        after.update(_order=models.F("_order") - 1)
        super().delete(*args, **kwargs)

    def _get_next_or_previous_by_order(self, is_next, **kwargs):
        """
        Retrieves next or previous object by order. We implement our
        own version instead of Django's so we can hook into the
        published manager, concrete subclasses and our custom
        ``with_respect_to`` method.
        """
        lookup = self.with_respect_to()
        lookup["_order"] = self._order + (1 if is_next else -1)
        concrete_model = base_concrete_model(Orderable, self)
        try:
            queryset = concrete_model.objects.published
        except AttributeError:
            queryset = concrete_model.objects.filter
        try:
            return queryset(**kwargs).get(**lookup)
        except concrete_model.DoesNotExist:
            pass

    def get_next_by_order(self, **kwargs):
        """
        Retrieves next object by order.
        """
        return self._get_next_or_previous_by_order(True, **kwargs)

    def get_previous_by_order(self, **kwargs):
        """
        Retrieves previous object by order.
        """
        return self._get_next_or_previous_by_order(False, **kwargs)


class Ownable(models.Model):
    """
    Abstract model that provides ownership of an object for a user.
    """

    user = models.ForeignKey(
        user_model_name,
        on_delete=models.CASCADE,
        verbose_name=_("Author"),
        related_name="%(class)ss",
    )

    class Meta:
        abstract = True

    def is_editable(self, request):
        """
        Author: owner only. Editor+ on this site: any object.
        Superuser: always.
        """
        from mezzanine.core.capabilities import user_can_edit

        return user_can_edit(request.user, self)


class ContentTyped(models.Model):
    """
    Mixin for models that can be subclassed to create custom types. In order to use
    them:

    - Inherit model from ContentTyped.
    - Call the set_content_model() method in the model's save() method.
    - Inherit that model's ModelAdmin from ContentTypesAdmin.
    - Include "admin/includes/content_typed_change_list.html" in the change_list.html
      template.
    """

    content_model = models.CharField(editable=False, max_length=50, null=True)

    class Meta:
        abstract = True

    @classmethod
    def get_content_model_name(cls):
        """
        Return the name of the OneToOneField django automatically creates for
        child classes in multi-table inheritance.
        """
        return cls._meta.object_name.lower()

    @classmethod
    def get_content_models(cls):
        """Return all subclasses of the concrete model."""
        concrete_model = base_concrete_model(ContentTyped, cls)
        return [
            m
            for m in apps.get_models()
            if m is not concrete_model and issubclass(m, concrete_model)
        ]

    def set_content_model(self):
        """
        Set content_model to the child class's related name, or None if this is
        the base class.
        """
        if not self.content_model:
            is_base_class = base_concrete_model(ContentTyped, self) == self.__class__
            self.content_model = (
                None if is_base_class else self.get_content_model_name()
            )

    def get_content_model(self):
        """
        Return content model, or if this is the base class return it.
        """
        return getattr(self, self.content_model) if self.content_model else self


ROLE_AUTHOR = "author"
ROLE_EDITOR = "editor"
ROLE_PUBLISHER = "publisher"
ROLE_ADMIN = "admin"
SITE_ROLE_CHOICES = (
    (ROLE_AUTHOR, _("Author")),
    (ROLE_EDITOR, _("Editor")),
    (ROLE_PUBLISHER, _("Publisher")),
    (ROLE_ADMIN, _("Admin")),
)


# KD20 / PR-058 — generic content model (ACF-equivalent schema rows).
FIELD_TYPE_TEXT = "text"
FIELD_TYPE_RICHTEXT = "richtext"
FIELD_TYPE_NUMBER = "number"
FIELD_TYPE_BOOLEAN = "boolean"
FIELD_TYPE_CHOICE = "choice"
FIELD_TYPE_REFERENCE = "reference"
FIELD_TYPE_CHOICES = (
    (FIELD_TYPE_TEXT, _("Text")),
    (FIELD_TYPE_RICHTEXT, _("RichText")),
    (FIELD_TYPE_NUMBER, _("Number")),
    (FIELD_TYPE_BOOLEAN, _("Boolean")),
    (FIELD_TYPE_CHOICE, _("Choice")),
    (FIELD_TYPE_REFERENCE, _("Reference")),
)


class FieldSchema(models.Model):
    """
    One custom field definition, scoped to a content type (and optionally a kit).

    Values live on each Displayable as ``custom_fields`` JSON keyed by ``name``.
    Kits declare groups in ``fields.json``; activation syncs rows (PR-059).
    """

    kit = models.CharField(max_length=64, blank=True, default="")
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="field_schemas",
        verbose_name=_("Content type"),
    )
    name = models.CharField(max_length=64)
    label = models.CharField(max_length=128)
    field_type = models.CharField(
        max_length=16, choices=FIELD_TYPE_CHOICES, default=FIELD_TYPE_TEXT
    )
    required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    options = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("Field schema")
        verbose_name_plural = _("Field schemas")
        ordering = ("order", "name")
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "name"],
                name="nova_fieldschema_ct_name",
            ),
        ]

    def __str__(self):
        return "%s.%s (%s)" % (self.content_type, self.name, self.field_type)

    def clean_value(self, value):
        """
        Coerce / validate a raw value for this field type.

        Returns the cleaned value, or raises ``ValueError``.
        """
        if value is None or value == "":
            if self.required:
                raise ValueError("%s is required" % self.name)
            return None if self.field_type == FIELD_TYPE_NUMBER else value

        if self.field_type == FIELD_TYPE_BOOLEAN:
            if isinstance(value, bool):
                return value
            if isinstance(value, str) and value.lower() in ("true", "1", "yes"):
                return True
            if isinstance(value, str) and value.lower() in ("false", "0", "no"):
                return False
            raise ValueError("%s must be a boolean" % self.name)

        if self.field_type == FIELD_TYPE_NUMBER:
            try:
                if isinstance(value, bool):
                    raise ValueError
                if isinstance(value, (int, float)):
                    return value
                if isinstance(value, str) and "." in value:
                    return float(value)
                return int(value)
            except (TypeError, ValueError) as exc:
                raise ValueError("%s must be a number" % self.name) from exc

        if self.field_type == FIELD_TYPE_CHOICE:
            choices = (self.options or {}).get("choices") or []
            if choices and value not in choices:
                raise ValueError("%s must be one of %s" % (self.name, choices))
            return value

        if self.field_type in (
            FIELD_TYPE_TEXT,
            FIELD_TYPE_RICHTEXT,
            FIELD_TYPE_REFERENCE,
        ):
            return value if not isinstance(value, str) else value

        return value


class SiteRole(models.Model):
    """
    Per-(user, site) role. Replaces ``SitePermission`` (OneToOne + M2M).

    Superuser is cross-site break-glass and does not need a row.
    """

    user = models.ForeignKey(
        user_model_name,
        on_delete=models.CASCADE,
        verbose_name=_("User"),
        related_name="siteroles",
    )
    site = models.ForeignKey(
        "sites.Site",
        on_delete=models.CASCADE,
        verbose_name=_("Site"),
        related_name="siteroles",
    )
    role = models.CharField(
        max_length=16, choices=SITE_ROLE_CHOICES, default=ROLE_EDITOR
    )

    class Meta:
        verbose_name = _("Site role")
        verbose_name_plural = _("Site roles")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "site"], name="nova_siterole_user_site"
            ),
        ]

    def __str__(self):
        return "%s @ %s (%s)" % (self.user, self.site, self.role)


PREVIEW_ROLE_ANON = "anon"
PREVIEW_ROLE_STAFF = "staff"
PREVIEW_ROLE_CHOICES = (
    (PREVIEW_ROLE_ANON, "anon"),
    (PREVIEW_ROLE_STAFF, "staff"),
)
# Query-param name for opaque preview tokens (reader + admin issuer).
PREVIEW_TOKEN_PARAM = "preview"


class PreviewToken(models.Model):
    """
    Opaque, hashed preview capability for a single Displayable.

    The raw token is returned once from ``issue()`` and never stored.
    Presentation compares with ``hmac.compare_digest`` on the sha256 hex.
    """

    token_hash = models.CharField(max_length=64, unique=True)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="preview_tokens"
    )
    object_pk = models.TextField()
    site = models.ForeignKey(
        Site, on_delete=models.CASCADE, related_name="preview_tokens"
    )
    as_role = models.CharField(
        max_length=8, choices=PREVIEW_ROLE_CHOICES, default=PREVIEW_ROLE_ANON
    )
    created_by = models.ForeignKey(
        user_model_name,
        on_delete=models.CASCADE,
        related_name="preview_tokens",
    )
    expires_at = models.DateTimeField()
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Preview token")
        verbose_name_plural = _("Preview tokens")

    def __str__(self):
        return "%s:%s" % (self.content_type, self.object_pk)

    def covers(self, model):
        """True when this token's content type matches ``model``.

        Tokens are issued against the base concrete ``Displayable``
        (``Page`` for every page type). A ``RichTextPage`` queryset
        is therefore covered by a ``Page`` token.
        """
        token_model = self.content_type.model_class()
        if token_model is None or model is None:
            return False
        if token_model is model:
            return True
        try:
            return issubclass(model, token_model) or issubclass(token_model, model)
        except TypeError:
            return False

    @staticmethod
    def hash_token(raw):
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def issue(
        cls, obj, created_by, as_role=PREVIEW_ROLE_ANON, expires_at=None, site=None
    ):
        """
        Persist a sha256 of a fresh token and return the raw secret once.
        """
        if as_role not in (PREVIEW_ROLE_ANON, PREVIEW_ROLE_STAFF):
            raise ValueError(
                f"as_role must be {PREVIEW_ROLE_ANON!r} or {PREVIEW_ROLE_STAFF!r}"
            )
        raw = secrets.token_urlsafe(32)
        if expires_at is None:
            expires_at = now() + timedelta(seconds=settings.PREVIEW_TOKEN_TTL_SECONDS)
        if site is None:
            site_id = getattr(obj, "site_id", None) or current_site_id()
            site = Site.objects.get(pk=site_id)
        if isinstance(obj, Displayable):
            model = base_concrete_model(Displayable, obj)
        else:
            model = obj.__class__
        cls.objects.create(
            token_hash=cls.hash_token(raw),
            content_type=ContentType.objects.get_for_model(model),
            object_pk=str(obj.pk),
            site=site,
            as_role=as_role,
            created_by=created_by,
            expires_at=expires_at,
        )
        return raw

    @classmethod
    def lookup(cls, raw):
        """
        Hash ``raw`` and return the matching row, or ``None``.

        Uses ``hmac.compare_digest`` on the hex even after the unique
        lookup so presentation never does a raw ``==`` on the secret.
        """
        if not raw:
            return None
        incoming_hash = cls.hash_token(raw)
        try:
            token = cls.objects.select_related("content_type", "site").get(
                token_hash=incoming_hash
            )
        except cls.DoesNotExist:
            return None
        try:
            if not hmac.compare_digest(token.token_hash, incoming_hash):
                return None
        except (TypeError, ValueError):
            return None
        return token
