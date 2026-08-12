from django.contrib.admin.widgets import AdminTextareaWidget
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models
from django.forms import MultipleChoiceField
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from mezzanine.core.forms import OrderWidget
from mezzanine.utils.html import escape
from mezzanine.utils.importing import import_dotted_path


class OrderField(models.IntegerField):
    def formfield(self, **kwargs):
        kwargs.update({"widget": OrderWidget, "required": False})
        return super().formfield(**kwargs)


class RichTextField(models.TextField):
    """
    TextField that stores HTML.
    """

    def formfield(self, **kwargs):
        """
        Apply the widget class defined by the
        ``RICHTEXT_WIDGET_CLASS`` setting.
        """
        default = kwargs.get("widget", None) or AdminTextareaWidget
        if default is AdminTextareaWidget:
            from mezzanine.conf import settings

            richtext_widget_path = settings.RICHTEXT_WIDGET_CLASS
            try:
                widget_class = import_dotted_path(richtext_widget_path)
            except ImportError:
                raise ImproperlyConfigured(
                    _(
                        "Could not import the value of "
                        "settings.RICHTEXT_WIDGET_CLASS: "
                        "%s" % richtext_widget_path
                    )
                )
            kwargs["widget"] = widget_class()
        kwargs.setdefault("required", False)
        formfield = super().formfield(**kwargs)
        return formfield

    def clean(self, value, model_instance):
        """
        Remove potentially dangerous HTML tags and attributes.
        """
        return escape(value)


class MultiChoiceField(models.CharField):
    """
    Charfield that stores multiple choices selected as a comma
    separated string. Based on http://djangosnippets.org/snippets/2753/
    """

    def formfield(self, *args, **kwargs):
        from mezzanine.core.forms import CheckboxSelectMultiple

        defaults = {
            "required": not self.blank,
            "label": capfirst(self.verbose_name),
            "help_text": self.help_text,
            "choices": self.choices,
            "widget": CheckboxSelectMultiple,
            "initial": self.get_default() if self.has_default() else None,
        }
        defaults.update(kwargs)
        return MultipleChoiceField(**defaults)

    def get_db_prep_value(self, value, connection, **kwargs):
        if isinstance(value, (tuple, list)):
            value = ",".join(str(i) for i in value)
        return value

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def to_python(self, value):
        if isinstance(value, str):
            value = value.split(",")
        return value

    def validate(self, value, instance):
        choices = [str(choice[0]) for choice in self.choices]
        if set(value) - set(choices):
            error = self.error_messages["invalid_choice"] % {"value": value}
            raise ValidationError(error)

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return ",".join(value)


# Historically ``FileField`` subclassed filebrowser's ``FileBrowseField``
# when that package was importable. Filebrowser is now an optional admin
# extra (PR-030); Nova ships a media chooser at ``/_nova/media/chooser/``.
# Always use Django's FileField + ``MediaChooserFormField`` so brochure
# installs work without filebrowser_safe. FileBrowseField kwargs
# (format / extensions / directory) are accepted and ignored for
# migration/call-site compatibility.
class FileField(models.FileField):
    """Django FileField with Nova media-library chooser in admin forms."""

    def __init__(self, *args, **kwargs):
        for fb_arg in ("format", "extensions", "directory"):
            kwargs.pop(fb_arg, None)
        # FileBrowseField used directory= in place of upload_to; keep a
        # sensible default when callers only passed directory=.
        kwargs.setdefault("max_length", 255)
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        from mezzanine.core.forms import MediaChooserFormField

        defaults = {"form_class": MediaChooserFormField}
        defaults.update(kwargs)
        return super().formfield(**defaults)
