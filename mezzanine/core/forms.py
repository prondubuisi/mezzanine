from datetime import datetime
from uuid import uuid4

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.forms.utils import to_current_timezone
from django.forms.widgets import SelectDateWidget
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from mezzanine.conf import settings
from mezzanine.utils.static import static_lazy as static


class Html5Mixin:
    """
    Mixin for form classes. Adds HTML5 features to forms for client
    side validation by the browser, like a "required" attribute and
    "email" and "url" input types.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, "fields"):
            first_field = None

            for name, field in self.fields.items():
                # Autofocus first non-hidden field
                if not first_field and not field.widget.is_hidden:
                    first_field = field
                    first_field.widget.attrs["autofocus"] = ""
                if settings.FORMS_USE_HTML5:
                    if isinstance(field, forms.EmailField):
                        self.fields[name].widget.input_type = "email"
                    elif isinstance(field, forms.URLField):
                        self.fields[name].widget.input_type = "url"
                if field.required:
                    self.fields[name].widget.attrs["required"] = ""


class TinyMceWidget(forms.Textarea):
    """
    Optional TinyMCE 7 widget (PR-028).

    Vendored TinyMCE 4 was removed. When ``TINYMCE_CDN`` is set, scripts
    load from that URL; otherwise this is a plain textarea.
    """

    @property
    def media(self):
        cdn = getattr(settings, "TINYMCE_CDN", "") or ""
        js = []
        if cdn:
            js.append(cdn)
            # Optional project setup if present under STATIC.
            setup = getattr(settings, "TINYMCE_SETUP_JS", "") or ""
            if setup:
                try:
                    js.append(static(setup))
                except Exception:  # noqa: BLE001 — setup is best-effort
                    pass
        return forms.Media(js=js)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs["class"] = "mceEditor"

    def use_required_attribute(self, initial):
        # TinyMCE does not put content back into the <textarea>, so we want to
        # allow it to submit when empty.
        return False


class OrderWidget(forms.HiddenInput):
    """
    Add up and down arrows for ordering controls next to a hidden
    form field.
    """

    @property
    def is_hidden(self):
        return False

    def render(self, *args, **kwargs):
        rendered = super().render(*args, **kwargs)
        arrows = [
            "<img src='%sadmin/img/admin/arrow-%s.gif' />"
            % (settings.STATIC_URL, arrow)
            for arrow in ("up", "down")
        ]
        arrows = "<span class='ordering'>%s</span>" % "".join(arrows)
        return rendered + mark_safe(arrows)


def _normalize_media_path(value: str) -> str:
    """Turn a chooser URL or storage path into a storage-relative name."""
    value = (value or "").strip()
    if not value:
        return ""
    media_url = settings.MEDIA_URL or "/media/"
    if value.startswith(media_url):
        value = value[len(media_url) :]
    # Absolute site URL that ends with MEDIA_URL path
    if "://" in value:
        from urllib.parse import urlparse

        path = urlparse(value).path or ""
        if media_url and media_url in path:
            value = path.split(media_url, 1)[-1]
        else:
            value = path.lstrip("/")
    return value.lstrip("/")


class MediaChooserFileWidget(forms.ClearableFileInput):
    """
    File input plus a Nova media-library browse button (no filebrowser).

    Selecting a library asset fills a companion hidden path field; the
    form field accepts that path when no new upload is present.
    """

    template_name = "admin/widgets/media_chooser_file.html"

    class Media:
        js = (static("mezzanine/js/admin/media_chooser_field.js"),)
        css = {"all": (static("mezzanine/css/admin/media_chooser_field.css"),)}

    def value_from_datadict(self, data, files, name):
        upload = super().value_from_datadict(data, files, name)
        if upload:
            return upload
        # ClearableFileInput returns False when the clear checkbox is set.
        if upload is False:
            return False
        path = data.get(f"{name}_nova_path") or data.get(f"{name}_nova_url")
        if path:
            return _normalize_media_path(path)
        return upload

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        path = ""
        url = ""
        if value and hasattr(value, "url"):
            try:
                url = value.url
            except ValueError:
                url = ""
            path = getattr(value, "name", "") or ""
        elif isinstance(value, str):
            path = value
            if value:
                try:
                    url = default_storage.url(value)
                except Exception:  # noqa: BLE001 — storage backends vary
                    url = settings.MEDIA_URL + value
        context["widget"]["nova_path"] = path
        context["widget"]["nova_url"] = url
        context["widget"]["nova_path_name"] = f"{name}_nova_path"
        return context


class MediaChooserFormField(forms.FileField):
    """
    FileField that also accepts an existing MEDIA_ROOT-relative path from
    the Nova media chooser (see ``MediaChooserFileWidget``).
    """

    widget = MediaChooserFileWidget

    def to_python(self, data):
        if isinstance(data, str):
            path = _normalize_media_path(data)
            if not path:
                return None
            if not default_storage.exists(path):
                raise ValidationError(
                    _("Selected media file was not found in storage: %s") % path,
                    code="missing_media",
                )
            return path
        return super().to_python(data)

    def clean(self, data, initial=None):
        # Mirror FileField: False means "clear".
        if data is False:
            if not self.required:
                return False
            data = None
        if isinstance(data, str):
            return self.to_python(data)
        return super().clean(data, initial=initial)


class DynamicInlineAdminForm(forms.ModelForm):
    """
    Form for ``DynamicInlineAdmin`` that can be collapsed and sorted
    with drag and drop using ``OrderWidget``.
    """

    class Media:
        js = [
            # Ensure Django's noConflict jQuery has loaded BEFORE our scripts
            "admin/js/jquery.init.js",
            static("mezzanine/js/%s" % settings.JQUERY_UI_FILENAME),
            static("mezzanine/js/admin/dynamic_inline.js"),
        ]


class SplitSelectDateTimeWidget(forms.SplitDateTimeWidget):
    """
    Combines Django's ``SelectDateTimeWidget`` and ``SelectDateWidget``.
    """

    def __init__(self, attrs=None, date_format=None, time_format=None):
        date_widget = SelectDateWidget(attrs=attrs)
        time_widget = forms.TimeInput(attrs=attrs, format=time_format)
        forms.MultiWidget.__init__(self, (date_widget, time_widget), attrs)

    def decompress(self, value):
        if isinstance(value, str):
            return value.split(" ", 1)
        elif isinstance(value, datetime):
            value = to_current_timezone(value)
            return [value.date(), value.time().replace(microsecond=0)]
        return [None, None]

    def value_from_datadict(self, data, files, name):
        return " ".join(
            x or ""
            for x in super(SplitSelectDateTimeWidget, self).value_from_datadict(
                data, files, name
            )
        )


class CheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    """
    Wraps render with a CSS class for styling.
    """

    dont_use_model_field_default_for_empty_data = True

    def render(self, *args, **kwargs):
        rendered = super().render(*args, **kwargs)
        return mark_safe("<span class='multicheckbox'>%s</span>" % rendered)


def get_edit_form(obj, field_names, data=None, files=None, textarea=False):
    """
    Returns the in-line editing form for editing a single model field.

    ``textarea=True`` forces visible widgets to ``forms.Textarea``
    (HTMX island; TinyMCE stays in admin).
    """

    # Map these form fields to their types defined in the forms app so
    # we can make use of their custom widgets.
    from mezzanine.forms import fields

    widget_overrides = {
        forms.DateField: fields.DATE,
        forms.DateTimeField: fields.DATE_TIME,
        forms.EmailField: fields.EMAIL,
    }

    class EditForm(forms.ModelForm):
        """
        In-line editing form for editing a single model field.
        """

        app = forms.CharField(widget=forms.HiddenInput)
        model = forms.CharField(widget=forms.HiddenInput)
        id = forms.CharField(widget=forms.HiddenInput)
        fields = forms.CharField(widget=forms.HiddenInput)

        class Meta:
            model = obj.__class__
            fields = field_names.split(",")

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.uuid = str(uuid4())
            for f in self.fields.keys():
                field_class = self.fields[f].__class__
                if textarea and not self.fields[f].widget.is_hidden:
                    self.fields[f].widget = forms.Textarea()
                else:
                    try:
                        widget = fields.WIDGETS[widget_overrides[field_class]]
                    except KeyError:
                        pass
                    else:
                        self.fields[f].widget = widget()
                css_class = self.fields[f].widget.attrs.get("class", "")
                css_class += " " + field_class.__name__.lower()
                self.fields[f].widget.attrs["class"] = css_class
                self.fields[f].widget.attrs["id"] = f"{f}-{self.uuid}"
                if settings.FORMS_USE_HTML5 and self.fields[f].required:
                    self.fields[f].widget.attrs["required"] = ""

    initial = {
        "app": obj._meta.app_label,
        "id": obj.id,
        "fields": field_names,
        "model": obj._meta.object_name.lower(),
    }
    return EditForm(instance=obj, initial=initial, data=data, files=files)
