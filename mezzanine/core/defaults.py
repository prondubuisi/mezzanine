"""
Default settings for the ``mezzanine.core`` app. Each of these can be
overridden in your project's settings module, just like regular
Django settings. The ``editable`` argument for each controls whether
the setting is editable via Django's admin.

Thought should be given to how a setting is actually used before
making it editable, as it may be inappropriate - for example settings
that are only read during startup shouldn't be editable, since changing
them would require an application reload.
"""
import os

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from mezzanine.conf import register_setting

# Only NONE path after Wave 1 / PR-005b. Must be the string "1".
NOVA_FORCE_RAW_HTML_ENV = "NOVA_FORCE_RAW_HTML"


def nova_force_raw_html():
    """True only when the operator opts into unsanitized HTML via env."""
    return os.environ.get(NOVA_FORCE_RAW_HTML_ENV) == "1"


def resolve_richtext_filter_level(configured):
    """Return the effective filter level.

    ``NOVA_FORCE_RAW_HTML=1`` is the only NONE path. A configured NONE
    without that env is treated as HIGH so a stale settings.py or
    leftover ``Setting`` row cannot disable sanitization.
    """
    if nova_force_raw_html():
        return RICHTEXT_FILTER_LEVEL_NONE
    if configured == RICHTEXT_FILTER_LEVEL_NONE:
        return RICHTEXT_FILTER_LEVEL_HIGH
    return configured


register_setting(
    name="ADMIN_MENU_ORDER",
    description=_("Controls the ordering and grouping of the admin menu."),
    editable=False,
    default=(
        (
            _("Content"),
            (
                "pages.Page",
                "blog.BlogPost",
                "generic.ThreadedComment",
                (_("Media Library"), "media-library"),
            ),
        ),
        (_("Site"), ("sites.Site", "redirects.Redirect", "conf.Setting")),
        (
            _("Users"),
            (
                "auth.User",
                "auth.Group",
            ),
        ),
    ),
)

register_setting(
    name="ADMIN_MENU_COLLAPSED",
    label=_("Collapse the Admin menu"),
    description=_(
        "Controls whether or not the left-hand admin menu is " "collapsed by default."
    ),
    editable=True,
    default=False,
)

register_setting(
    name="ADMIN_REMOVAL",
    description=_(
        "A sequence of Python dotted paths to models "
        "(eg: ``['mezzanine.blog.models.BlogPost',]``) that should be "
        "removed from the admin."
    ),
    editable=False,
    default=(),
)

register_setting(
    name="ADMIN_THUMB_SIZE",
    description=_(
        "Size of thumbnail previews for image fields in the " "admin interface."
    ),
    editable=False,
    default="24x24",
)

register_setting(
    name="AKISMET_API_KEY",
    label=_("Akismet API Key"),
    description=_(
        "Key for http://akismet.com spam filtering service. Used "
        "for filtering comments and forms."
    ),
    editable=True,
    default="",
)

register_setting(
    name="CACHE_SET_DELAY_SECONDS",
    description=_(
        "Mezzanine's caching uses a technique know as mint "
        "caching. This is where the requested expiry for a cache entry "
        "is stored with the cache entry in cache, and the real expiry "
        "used has the ``CACHE_SET_DELAY`` added to it. Then on a cache get, "
        "the store expiry is checked, and if it has passed, the cache entry "
        "is set again, and no entry is returned. This tries to ensure that "
        "cache misses never occur, and if many clients were to get a cache "
        "miss at once, only one would actually need to re-generated the "
        "cache entry."
    ),
    editable=False,
    default=30,
)

if "mezzanine.blog" in settings.INSTALLED_APPS:
    dashboard_tags = (
        ("blog_tags.quick_blog", "mezzanine_tags.app_list"),
        ("comment_tags.recent_comments",),
        ("mezzanine_tags.recent_actions",),
    )
else:
    dashboard_tags = (
        ("mezzanine_tags.app_list",),
        ("mezzanine_tags.recent_actions",),
        (),
    )

register_setting(
    name="DASHBOARD_TAGS",
    description=_(
        "A three item sequence, each containing a sequence of "
        "template tags used to render the admin dashboard."
    ),
    editable=False,
    default=dashboard_tags,
)

register_setting(
    name="FORMS_USE_HTML5",
    description=_("If ``True``, website forms will use HTML5 features."),
    editable=False,
    default=False,
)

register_setting(
    name="EMAIL_FAIL_SILENTLY",
    description=_(
        "If ``True``, failures to send email will happen "
        "silently, otherwise an exception is raised. "
        "Defaults to ``settings.DEBUG``."
    ),
    editable=False,
    default=settings.DEBUG,
)

register_setting(
    name="EXTRA_MODEL_FIELDS",
    description=_(
        "A sequence of fields that will be injected into "
        "Mezzanine's (or any library's) models. Each item in the sequence is "
        "a four item sequence. The first two items are the dotted path to the "
        "model and its field name to be added, and the dotted path to the "
        "field class to use for the field. The third and fourth items are a "
        "sequence of positional args and a dictionary of keyword args, to use "
        "when creating the field instance. When specifying the field class, "
        "the path ``django.models.db.`` can be omitted for regular Django "
        "model fields."
    ),
    editable=False,
    default=(),
)

register_setting(
    name="HOST_THEMES",
    description=_(
        "A sequence mapping host names to themes, allowing "
        "different templates to be served per HTTP host. "
        "Each item in the sequence is a two item sequence, "
        "containing a host such as ``othersite.example.com``, and "
        "the name of an importable Python package for the theme. "
        "If the host is matched for a request, the templates "
        "directory inside the theme package will be first searched "
        "when loading templates."
    ),
    editable=False,
    default=(),
)

register_setting(
    name="ACTIVE_THEME",
    label=_("Active theme"),
    description=_(
        "First-party kit name that supplies the active theme package "
        "(WordPress-style). When set, templates under "
        "mezzanine/kits/<name>/templates/ load before the project's "
        "copied templates. Empty disables runtime theme override. "
        "Requires the kit app (and any theme plugins) in INSTALLED_APPS."
    ),
    editable=True,
    default="",
)

# Theme Customizer (lean WP Customizer analogue) — overrides theme.json colors.
register_setting(
    name="THEME_COLOR_INK",
    label=_("Theme color: ink"),
    description=_("Override active theme ink/primary text color (CSS)."),
    editable=True,
    default="",
)
register_setting(
    name="THEME_COLOR_ACCENT",
    label=_("Theme color: accent"),
    description=_("Override active theme accent color (CSS)."),
    editable=True,
    default="",
)
register_setting(
    name="THEME_COLOR_ACCENT_INK",
    label=_("Theme color: accent ink"),
    description=_("Override secondary accent / link hover color."),
    editable=True,
    default="",
)
register_setting(
    name="THEME_COLOR_CANVAS",
    label=_("Theme color: canvas"),
    description=_("Override page background color."),
    editable=True,
    default="",
)
register_setting(
    name="THEME_COLOR_PAPER",
    label=_("Theme color: paper"),
    description=_("Override surface / card background color."),
    editable=True,
    default="",
)
register_setting(
    name="THEME_LOGO_URL",
    label=_("Theme logo URL"),
    description=_(
        "Optional logo image URL shown in theme chrome when the template "
        "supports it (Customizer)."
    ),
    editable=True,
    default="",
)

register_setting(
    name="INLINE_EDITING_ENABLED",
    description=_("If ``True``, front-end inline editing will be enabled."),
    editable=False,
    default=True,
)

register_setting(
    name="JQUERY_FILENAME",
    label=_("Name of the jQuery file."),
    description=_(
        "Name of the jQuery file found in " "mezzanine/core/static/mezzanine/js/"
    ),
    editable=False,
    default="jquery-3.4.1.js",
)

register_setting(
    name="JQUERY_UI_FILENAME",
    label=_("Name of the jQuery UI file."),
    description=_(
        "Name of the jQuery UI file found in " "mezzanine/core/static/mezzanine/js/"
    ),
    editable=False,
    default="jquery-ui-1.12.1.js",
)

register_setting(
    name="MAX_PAGING_LINKS",
    label=_("Max paging links"),
    description=_("Max number of paging links to display when paginating."),
    editable=True,
    default=10,
)

register_setting(
    name="MEDIA_LIBRARY_PER_SITE",
    label=_("Media library per site"),
    description=_(
        "If ``True``, each site will use its own directory within "
        "the filebrowser media library."
    ),
    editable=False,
    default=False,
)

register_setting(
    name="OWNABLE_MODELS_ALL_EDITABLE",
    description=_(
        "Models that subclass ``Ownable`` and use the "
        "``OwnableAdmin`` have their admin change-list records filtered "
        "down to records owned by the current user. This setting contains a "
        "sequence of models in the format ``app_label.object_name``, that "
        "when subclassing ``Ownable``, will still show all records in the "
        "admin change-list interface, regardless of the current user."
    ),
    editable=False,
    default=(),
)

register_setting(
    name="RICHTEXT_WIDGET_CLASS",
    description=_(
        "Dotted package path and class name of the widget to use "
        "for the ``RichTextField``. Y1.5 default is a plain admin "
        "textarea; set to ``mezzanine.core.forms.TinyMceWidget`` and "
        "enable ``TINYMCE_CDN`` for optional TinyMCE 7."
    ),
    editable=False,
    default="django.contrib.admin.widgets.AdminTextareaWidget",
)

register_setting(
    name="TINYMCE_CDN",
    description=_(
        "When using ``mezzanine.core.forms.TinyMceWidget``, load TinyMCE 7 "
        "from this CDN URL (PR-028). Empty disables the editor scripts."
    ),
    editable=False,
    default="https://cdn.jsdelivr.net/npm/tinymce@7/tinymce.min.js",
)

register_setting(
    name="RICHTEXT_ALLOWED_TAGS",
    description=_(
        "List of HTML tags that won't be stripped from " "``RichTextField`` instances."
    ),
    editable=False,
    default=(
        "a",
        "abbr",
        "acronym",
        "address",
        "area",
        "article",
        "aside",
        "b",
        "bdo",
        "big",
        "blockquote",
        "br",
        "button",
        "caption",
        "center",
        "cite",
        "code",
        "col",
        "colgroup",
        "dd",
        "del",
        "dfn",
        "dir",
        "div",
        "dl",
        "dt",
        "em",
        "fieldset",
        "figure",
        "font",
        "footer",
        "form",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "i",
        "img",
        "input",
        "ins",
        "kbd",
        "label",
        "legend",
        "li",
        "map",
        "menu",
        "nav",
        "ol",
        "optgroup",
        "option",
        "p",
        "pre",
        "q",
        "s",
        "samp",
        "section",
        "select",
        "small",
        "span",
        "strike",
        "strong",
        "sub",
        "sup",
        "table",
        "tbody",
        "td",
        "textarea",
        "tfoot",
        "th",
        "thead",
        "tr",
        "tt",
        "u",
        "ul",
        "var",
        "wbr",
    ),
)

register_setting(
    name="RICHTEXT_ALLOWED_ATTRIBUTES",
    description=_(
        "List of HTML attributes that won't be stripped from "
        "``RichTextField`` instances."
    ),
    editable=False,
    default=(
        "abbr",
        "accept",
        "accept-charset",
        "accesskey",
        "action",
        "align",
        "alt",
        "axis",
        "border",
        "cellpadding",
        "cellspacing",
        "char",
        "charoff",
        "charset",
        "checked",
        "cite",
        "class",
        "clear",
        "cols",
        "colspan",
        "color",
        "compact",
        "coords",
        "datetime",
        "dir",
        "disabled",
        "enctype",
        "for",
        "frame",
        "headers",
        "height",
        "href",
        "hreflang",
        "hspace",
        "id",
        "ismap",
        "label",
        "lang",
        "longdesc",
        "maxlength",
        "media",
        "method",
        "multiple",
        "name",
        "nohref",
        "noshade",
        "nowrap",
        "prompt",
        "readonly",
        "rel",
        "rev",
        "rows",
        "rowspan",
        "rules",
        "scope",
        "selected",
        "shape",
        "size",
        "span",
        "src",
        "start",
        "style",
        "summary",
        "tabindex",
        "target",
        "title",
        "type",
        "usemap",
        "valign",
        "value",
        "vspace",
        "width",
        "xml:lang",
    ),
)

register_setting(
    name="RICHTEXT_ALLOWED_STYLES",
    description=_(
        "List of inline CSS styles that won't be stripped from "
        "``RichTextField`` instances."
    ),
    editable=False,
    default=(
        "border",
        "display",
        "float",
        "list-style-type",
        "margin",
        "margin-bottom",
        "margin-left",
        "margin-right",
        "margin-top",
        "padding-left",
        "text-align",
        "text-decoration",
        "vertical-align",
    ),
)

register_setting(
    name="RICHTEXT_FILTERS",
    description=_(
        "List of dotted paths to functions, called in order, on a "
        "``RichTextField`` value before it is rendered to the template. "
        "The default pipeline thumbnails images, then sanitizes with "
        "bleach (``mezzanine.utils.html.escape``) so unsafe HTML is "
        "stripped on read after any BeautifulSoup rewrite."
    ),
    editable=False,
    default=(
        "mezzanine.utils.html.thumbnails",
        "mezzanine.utils.html.escape",
    ),
)

RICHTEXT_FILTER_LEVEL_HIGH = 1
RICHTEXT_FILTER_LEVEL_LOW = 2
RICHTEXT_FILTER_LEVEL_NONE = 3
# Admin / registry choices. NONE is not listed — it is only available
# via NOVA_FORCE_RAW_HTML=1 (see resolve_richtext_filter_level).
RICHTEXT_FILTER_LEVELS = (
    (RICHTEXT_FILTER_LEVEL_HIGH, _("High")),
    (RICHTEXT_FILTER_LEVEL_LOW, _("Low (allows video, iframe, Flash, etc)")),
)

register_setting(
    name="RICHTEXT_FILTER_LEVEL",
    label=_("Rich Text filter level"),
    description=_(
        "Level of HTML filtering applied to Rich Text fields on save and "
        "render. This setting is not editable in the admin.\n\n"
        "HIGH (default) strips unsafe tags and attributes. LOW allows extra "
        "tags used for embedded video (iframe, embed, etc).\n\n"
        "No filtering (NONE) is only available by setting the environment "
        "variable NOVA_FORCE_RAW_HTML=1 and restarting. That disables all "
        "sanitization and allows script tags. A configured NONE without "
        "that variable is ignored and treated as HIGH."
    ),
    editable=False,
    choices=RICHTEXT_FILTER_LEVELS,
    default=RICHTEXT_FILTER_LEVEL_HIGH,
)

register_setting(
    name="SEARCH_MODEL_CHOICES",
    description=_(
        "Sequence of models that will be provided by default as "
        "choices in the search form. Each model should be in the format "
        "``app_label.model_name``. Only models that subclass "
        "``mezzanine.core.models.Displayable`` should be used."
    ),
    editable=False,
    default=("pages.Page", "blog.BlogPost"),
)

register_setting(
    name="SEARCH_PER_PAGE",
    label=_("Search results per page"),
    description=_("Number of results shown in the search results page."),
    editable=True,
    default=10,
)

register_setting(
    name="SEARCH_AGE_SCALE_FACTOR",
    label=_("Emphasis to put on age when ranking search results"),
    description=_(
        "The amount of emphasis to put on age when ranking search "
        "results. A higher number gives more emphasis to age, "
        "ranking newer results higher with less regard to their "
        "ordinary score. Setting this to zero disables weighing "
        "search results by age."
    ),
    editable=False,
    default=1.5,
)

register_setting(
    name="SEARCH_MAX_RESULTS",
    label=_("Maximum search results to materialize"),
    description=_(
        "Upper bound on rows materialized when scoring search results "
        "and when unioning matches across models. Prevents unbounded "
        "Python materialization of the matching queryset."
    ),
    editable=False,
    default=200,
)

register_setting(
    name="SEARCH_USE_POSTGRES_FTS",
    description=_(
        "When True and the database is PostgreSQL, searchable querysets "
        "use SearchVector/SearchRank on simple (non-relation) fields. "
        "Other databases keep the icontains + annotate_scores path."
    ),
    editable=False,
    default=True,
)

register_setting(
    name="SITE_PREFIX",
    description=_(
        "A URL prefix for mounting all of Mezzanine's urlpatterns "
        "under. When using this, you'll also need to manually apply it to "
        "your project's root ``urls.py`` module. The root ``urls.py`` module "
        "provided by Mezzanine's ``mezzanine-project`` command contains an "
        "example of this towards its end."
    ),
    editable=False,
    default="",
)

register_setting(
    name="SITE_TITLE",
    label=_("Site Title"),
    description=_(
        "Title that will display at the top of the site, and be "
        "appended to the content of the HTML title tags on every page."
    ),
    editable=True,
    default="Mezzanine",
    translatable=True,
)

register_setting(
    name="SITE_TAGLINE",
    label=_("Tagline"),
    description=_("A tag line that will appear at the top of all pages."),
    editable=True,
    default=_("An open source content management platform."),
    translatable=True,
)

register_setting(
    name="SLUGIFY",
    description=_(
        "Dotted Python path to the callable for converting "
        "strings into URL slugs. Defaults to "
        "``mezzanine.utils.urls.slugify_unicode`` which allows for non-ascii "
        "URLs. Change to ``django.template.defaultfilters.slugify`` to use "
        "Django's slugify function, or something of your own if required."
    ),
    editable=False,
    default="mezzanine.utils.urls.slugify_unicode",
)

register_setting(
    name="SPAM_FILTERS",
    description=_(
        "Sequence of dotted Python paths to callable functions "
        "used for checking posted content (such as forms or comments) is "
        "spam. Each function should accept three arguments: the request "
        "object, the form object, and the URL that was posted from. "
        "Defaults to ``mezzanine.utils.views.is_spam_akismet`` which will "
        "use the http://akismet.com spam filtering service when the "
        "``AKISMET_API_KEY`` setting is configured."
    ),
    editable=False,
    default=("mezzanine.utils.views.is_spam_akismet",),
)

register_setting(
    name="STOP_WORDS",
    description=_("List of words which will be stripped from search queries."),
    editable=False,
    default=(
        "a",
        "about",
        "above",
        "above",
        "across",
        "after",
        "afterwards",
        "again",
        "against",
        "all",
        "almost",
        "alone",
        "along",
        "already",
        "also",
        "although",
        "always",
        "am",
        "among",
        "amongst",
        "amoungst",
        "amount",
        "an",
        "and",
        "another",
        "any",
        "anyhow",
        "anyone",
        "anything",
        "anyway",
        "anywhere",
        "are",
        "around",
        "as",
        "at",
        "back",
        "be",
        "became",
        "because",
        "become",
        "becomes",
        "becoming",
        "been",
        "before",
        "beforehand",
        "behind",
        "being",
        "below",
        "beside",
        "besides",
        "between",
        "beyond",
        "bill",
        "both",
        "bottom",
        "but",
        "by",
        "call",
        "can",
        "cannot",
        "cant",
        "co",
        "con",
        "could",
        "couldnt",
        "cry",
        "de",
        "describe",
        "detail",
        "do",
        "done",
        "down",
        "due",
        "during",
        "each",
        "eg",
        "eight",
        "either",
        "eleven",
        "else",
        "elsewhere",
        "empty",
        "enough",
        "etc",
        "even",
        "ever",
        "every",
        "everyone",
        "everything",
        "everywhere",
        "except",
        "few",
        "fifteen",
        "fifty",
        "fill",
        "find",
        "fire",
        "first",
        "five",
        "for",
        "former",
        "formerly",
        "forty",
        "found",
        "four",
        "from",
        "front",
        "full",
        "further",
        "get",
        "give",
        "go",
        "had",
        "has",
        "hasnt",
        "have",
        "he",
        "hence",
        "her",
        "here",
        "hereafter",
        "hereby",
        "herein",
        "hereupon",
        "hers",
        "herself",
        "him",
        "himself",
        "his",
        "how",
        "however",
        "hundred",
        "ie",
        "if",
        "in",
        "inc",
        "indeed",
        "interest",
        "into",
        "is",
        "it",
        "its",
        "itself",
        "keep",
        "last",
        "latter",
        "latterly",
        "least",
        "less",
        "ltd",
        "made",
        "many",
        "may",
        "me",
        "meanwhile",
        "might",
        "mill",
        "mine",
        "more",
        "moreover",
        "most",
        "mostly",
        "move",
        "much",
        "must",
        "my",
        "myself",
        "name",
        "namely",
        "neither",
        "never",
        "nevertheless",
        "next",
        "nine",
        "no",
        "nobody",
        "none",
        "noone",
        "nor",
        "not",
        "nothing",
        "now",
        "nowhere",
        "of",
        "off",
        "often",
        "on",
        "once",
        "one",
        "only",
        "onto",
        "or",
        "other",
        "others",
        "otherwise",
        "our",
        "ours",
        "ourselves",
        "out",
        "over",
        "own",
        "part",
        "per",
        "perhaps",
        "please",
        "put",
        "rather",
        "re",
        "same",
        "see",
        "seem",
        "seemed",
        "seeming",
        "seems",
        "serious",
        "several",
        "she",
        "should",
        "show",
        "side",
        "since",
        "sincere",
        "six",
        "sixty",
        "so",
        "some",
        "somehow",
        "someone",
        "something",
        "sometime",
        "sometimes",
        "somewhere",
        "still",
        "such",
        "system",
        "take",
        "ten",
        "than",
        "that",
        "the",
        "their",
        "them",
        "themselves",
        "then",
        "thence",
        "there",
        "thereafter",
        "thereby",
        "therefore",
        "therein",
        "thereupon",
        "these",
        "they",
        "thickv",
        "thin",
        "third",
        "this",
        "those",
        "though",
        "three",
        "through",
        "throughout",
        "thru",
        "thus",
        "to",
        "together",
        "too",
        "top",
        "toward",
        "towards",
        "twelve",
        "twenty",
        "two",
        "un",
        "under",
        "until",
        "up",
        "upon",
        "us",
        "very",
        "via",
        "was",
        "we",
        "well",
        "were",
        "what",
        "whatever",
        "when",
        "whence",
        "whenever",
        "where",
        "whereafter",
        "whereas",
        "whereby",
        "wherein",
        "whereupon",
        "wherever",
        "whether",
        "which",
        "while",
        "whither",
        "who",
        "whoever",
        "whole",
        "whom",
        "whose",
        "why",
        "will",
        "with",
        "within",
        "without",
        "would",
        "yet",
        "you",
        "your",
        "yours",
        "yourself",
        "yourselves",
        "the",
    ),
)

register_setting(
    name="TAG_CLOUD_SIZES",
    label=_("Tag Cloud Sizes"),
    description=_("Number of different sizes for tags when shown as a cloud."),
    editable=True,
    default=4,
)

register_setting(
    name="TEMPLATE_ACCESSIBLE_SETTINGS",
    description=_("Sequence of setting names available within templates."),
    editable=False,
    append=True,
    default=(
        "ACCOUNTS_APPROVAL_REQUIRED",
        "ACCOUNTS_VERIFICATION_REQUIRED",
        "ADMIN_MENU_COLLAPSED",
        "BLOG_USE_FEATURED_IMAGE",
        "COMMENTS_NUM_LATEST",
        "COMMENTS_USE_RATINGS",
        "DEV_SERVER",
        "FORMS_USE_HTML5",
        "GRAPPELLI_INSTALLED",
        "JQUERY_FILENAME",
        "JQUERY_UI_FILENAME",
        "LOGIN_URL",
        "LOGOUT_URL",
        "SITE_TITLE",
        "SITE_TAGLINE",
        "ACTIVE_THEME",
        "THEME_LOGO_URL",
        "USE_L10N",
        "USE_MODELTRANSLATION",
    ),
)

register_setting(
    name="THUMBNAILS_DIR_NAME",
    description=_(
        "Directory name to store thumbnails in, that will be "
        "created relative to the original image's directory."
    ),
    editable=False,
    default=".thumbnails",
)

register_setting(
    name="TINYMCE_SETUP_JS",
    description=_(
        "URL for the JavaScript file (relative to ``STATIC_URL``) "
        "that handles configuring TinyMCE when the default "
        "``RICHTEXT_WIDGET_CLASS`` is used."
    ),
    editable=False,
    default="mezzanine/js/tinymce_setup.js",
)

register_setting(
    name="UPLOAD_TO_HANDLERS",
    description=_(
        "Dict mapping file field names in the format "
        "``app_label.model_name.field_name`` to the Python dotted path "
        "to function names that will be used for the file field's "
        "``upload_to`` argument."
    ),
    editable=False,
    default={},
)

# The following settings are defined here for documentation purposes
# as this file is used to auto-generate the documentation for all
# available settings. They are Mezzanine specific, but their values
# are *always* overridden by the project's settings or local_settings
# modules, so the default values defined here will never be used.

register_setting(
    name="USE_MODELTRANSLATION",
    description=_(
        "If ``True``, the django-modeltranslation application will "
        "be automatically added to the ``INSTALLED_APPS`` setting."
    ),
    editable=False,
    default=False,
)

register_setting(
    name="NEVERCACHE_KEY",
    description=_(
        "Unique random string like ``SECRET_KEY``, but used for "
        "two-phased cache responses. Like ``SECRET_KEY``, should be "
        "automatically generated by the ``nova-project`` / "
        "``mezzanine-project`` command."
    ),
    editable=False,
    default="",
)
