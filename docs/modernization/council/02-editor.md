# Mezzanine Authoring Experience Audit

**Council role:** General EDITOR  
**Repo:** `/Users/prondubuisi/gitrepos/dev/mezzanine`  
**Method:** Independent opinion from shipped code only. No marketing. No imagined features.  
**Comparators:** WordPress Gutenberg / Full Site Editing, Wagtail StreamField, Sanity Studio.

This is not a Django-admin-vs-Gutenberg beauty contest. It is an inventory of what an author actually gets when they log in, click a field, try to draft, try to preview, and try to place media — then a verdict on how far that is from a 2026 editor.

---

## 1. What the admin actually is

**Mezzanine does not ship its own CMS admin.** It is Django's `django.contrib.admin`, skinned by a frozen Grappelli fork (`grappelli_safe`), then overlaid with Mezzanine templates, CSS, and jQuery.

### The skin: Grappelli fork, not Django admin vanilla

`setup.cfg` hard-requires:

```49:61:/Users/prondubuisi/gitrepos/dev/mezzanine/setup.cfg
install_requires =
    django-contrib-comments >= 2.0
    django >= 2.2, <6
    ...
    filebrowser_safe >= 1.1.1
    grappelli_safe >= 1.1.1
```

The project template names the forks explicitly because upstream moved on:

```275:278:/Users/prondubuisi/gitrepos/dev/mezzanine/mezzanine/project_template/project_name/settings.py
# Store these package names here as they may change in the future since
# at the moment we are using custom forks of them.
PACKAGE_NAME_FILEBROWSER = "filebrowser_safe"
PACKAGE_NAME_GRAPPELLI = "grappelli_safe"
```

Docs are honest about why (`docs/frequently-asked-questions.rst`): Grappelli and Filebrowser had packaging issues in 2010; forks were cut; packaging got fixed; Mezzanine kept the forks because upstream added features Mezzanine did not want, and because the forks accumulated Mezzanine-specific patches. They are "stable, and have relatively low activity."

That last sentence is the whole admin story: **a 2010-era Grappelli skin, pinned, lightly patched, still the chrome around Django ModelAdmin.**

`mezzanine.utils.conf` detects the skin and forces app order so Grappelli templates lose to Mezzanine, then Django admin loses to both:

```172:180:/Users/prondubuisi/gitrepos/dev/mezzanine/mezzanine/utils/conf.py
    # Ensure Grappelli is after Mezzanine in app order so that
    # admin templates are loaded in the correct order.
    grappelli_name = s.get("PACKAGE_NAME_GRAPPELLI")
    ...
        s["GRAPPELLI_INSTALLED"] = True
```

`window.__grappelli_installed` is then threaded through almost every admin JS file so selectors can target `.items` (Grappelli) vs `tbody` (stock Django). See `dynamic_inline.js`, `keywords_field.js`, `page_tree.js`. The admin is not "Grappelli or Django." It is "both, with runtime if-branches."

### The site object: `LazyAdminSite`

`mezzanine/boot/lazy_admin.py` replaces Django's `AdminSite` with `LazyAdminSite`. It exists for one reason: `EXTRA_MODEL_FIELDS` injects fields at import time, so `register()`/`unregister()` must be deferred until autodiscover. It also:

- Mounts filebrowser at `/admin/media-library/` (filebrowser itself has no root URL; Mezzanine adds a redirect so `ADMIN_MENU_ORDER` can highlight it).
- Names the user password-change URL so i18n admin can reverse it.
- Parks Mezzanine-only admin URLs under `/admin/` for SSL middleware compatibility: keywords submit, `asset_proxy` (TinyMCE static proxy), `displayable_links.js`, page-tree AJAX ordering.

This is a **Django admin site with extra URL hooks**, not a custom CMS shell.

### What authors actually see

`mezzanine/core/templates/admin/base_site.html` is the real shell:

- Loads **Mezzanine's** jQuery (`settings.JQUERY_FILENAME` → `jquery-3.4.1.js`), not Django's.
- Injects a pile of globals: CSRF, filebrowser URL, TinyMCE CSS, Grappelli flag, collapsed-menu flag, language code, displayable link-list URL, static proxy.
- Always renders `{% admin_dropdown_menu %}` — a persistent left nav built from `ADMIN_MENU_ORDER` (`mezzanine/core/templates/admin/includes/dropdown_menu.html`).
- Adds Chosen 0.9.12 on every non-popup admin page for `<select>` widgets.
- Adds `navigation.js` (side-panel hide/show via `localStorage['panel_hidden']`, current-section highlight, "View site" link injected into `#user-tools`).
- Adds `ajax_csrf.js`.
- Hides delete / slug / "save and add another" with CSS flags set by `PageAdmin` and `SingletonAdmin`.

Login is a custom `admin/login.html` with an **Admin vs Site** radio. Middleware `AdminLoginInterfaceSelectorMiddleware` (`mezzanine/core/middleware.py`) intercepts a successful login: `admin` stays in admin; `site` redirects to `/` so the author lands on the front end with inline-edit chrome. That radio is the product's only "which surface am I on?" decision.

### What it is not

- Not Wagtail's custom admin (no explorer, no choosers, no snippet UI, no workflow chrome).
- Not Sanity Studio (no desk structure, no real-time documents, no portable text).
- Not Gutenberg (no block canvas, no inspector, no list view of blocks).
- Not even modern Django admin: Grappelli's CSS/JS assumptions (`.collapse-closed`, `#header` height 40px, IE7 padding in `index.html`) are from a different decade.

**Verdict on identity:** Django ModelAdmin + `grappelli_safe` skin + Mezzanine chrome (left nav, dashboard tags, page tree, TinyMCE widget, inline-edit overlay). A competent 2012 CMS admin. Not a 2026 authoring product.

---

## 2. TinyMCE / WYSIWYG stack, versions, inline editing

### Versions (vendored, frozen)

| Asset | Path | Version / date |
|---|---|---|
| TinyMCE | `mezzanine/core/static/mezzanine/tinymce/tinymce.min.js` | **4.1.10 (2015-05-05)** |
| TinyMCE theme | `tinymce/themes/modern/` | TinyMCE 4 "modern" |
| TinyMCE skin | `tinymce/skins/lightgray/` | includes `skin.ie7.min.css` |
| TinyMCE jQuery plugin | `tinymce/jquery.tinymce.min.js` | 4.x |
| jQuery | `mezzanine/js/jquery-3.4.1.js` | **3.4.1** (2019) |
| jQuery UI | `mezzanine/js/jquery-ui-1.12.1.js` | **1.12.1** (2016) |
| jQuery Form | `mezzanine/js/jquery.form.js` | **3.51.0 (2014-06-20)** |
| jQuery Tools Overlay | `mezzanine/js/jquery.tools.overlay.js` | jQuery Tools, plus a `jQuery.browser` polyfill dated 2013 |
| jQuery Tools Expose | `mezzanine/js/jquery.tools.toolbox.expose.js` | same era |
| Chosen | `mezzanine/chosen/chosen-0.9.12.jquery.js` | **0.9.12** |
| nestedSortable | `pages/static/.../jquery.mjs.nestedSortable.js` | **2.1a / 2016-02-04** |

TinyMCE 4.1.10 is eleven years old. Current TinyMCE is 7.x. TinyMCE 4 is end-of-life. The tree still contains `plugins/media/moxieplayer.swf`, `plugins/example/`, `plugins/layer/`, `plugins/bbcode/`, `plugins/fullpage/`, `plugins/legacyoutput/`, and an IE7 skin. This is not "a bit behind." It is an archaeological layer.

### How the editor is wired

`RichTextField` (`mezzanine/core/fields.py`) is a `TextField` whose `formfield()` swaps the widget for whatever `RICHTEXT_WIDGET_CLASS` points at. Default: `mezzanine.core.forms.TinyMceWidget`.

`TinyMceWidget` (`mezzanine/core/forms.py`):

- Adds CSS class `mceEditor`.
- Media: `tinymce.min.js`, `jquery.tinymce.min.js`, `settings.TINYMCE_SETUP_JS` (default `mezzanine/js/tinymce_setup.js`).
- Disables HTML5 `required` because TinyMCE does not write back into the `<textarea>` until `triggerSave()`.

`tinymce_setup.js` config is a 2015 default toolbar:

```63:84:/Users/prondubuisi/gitrepos/dev/mezzanine/mezzanine/core/static/mezzanine/js/tinymce_setup.js
    var tinymce_config = {
        height: '500px',
        language: language_codes[window.__language_code] || 'en',
        plugins: [
            "advlist autolink lists link image charmap print preview anchor",
            "searchreplace visualblocks code fullscreen",
            "insertdatetime media table contextmenu paste"
        ],
        link_list: window.__link_list_url,
        relative_urls: false,
        browser_spellcheck: true,
        convert_urls: false,
        menubar: false,
        statusbar: false,
        toolbar: ("insertfile undo redo | styleselect | bold italic | " +
                  "alignleft aligncenter alignright alignjustify | " +
                  "bullist numlist outdent indent | link image table | " +
                  "code fullscreen"),
        file_browser_callback: custom_file_browser,
        content_css: window.__tinymce_css,
        valid_elements: "*[*]"  // Don't strip anything since this is handled by bleach.
    };
```

Notable:

- **No autosave** in the enabled plugin list (the `autosave` plugin is vendored, unused).
- **No image editing** (`imagetools` vendored, unused).
- **`valid_elements: "*[*]"`** — TinyMCE is told to keep everything. Sanitization is server-side via `RichTextField.clean()` → `mezzanine.utils.html.escape` → bleach, gated by `RICHTEXT_FILTER_LEVEL`.
- Internal link picker is `link_list: window.__link_list_url` → `displayable_links_js` (`core/views.py`), which dumps every `Displayable` URL/title as JSON.
- Media picker is `file_browser_callback` opening `window.__filebrowser_url + '?pop=5&type=' + type` in a TinyMCE `windowManager` popup (800×500). Classic Filebrowser popup protocol, not a modern media modal.
- `formset:added` re-inits TinyMCE on dynamically added Django inlines. That is the only "dynamic editor" story.

Swap-the-widget is real: `RICHTEXT_WIDGET_CLASS` and `TINYMCE_SETUP_JS` are documented extension points (`docs/admin-customization.rst`). `RICHTEXT_FILTERS` is a post-process pipeline (e.g. markdown → HTML). This is a **single HTML blob with a pluggable textarea widget**, not a content schema.

Content types that get this blob:

- `RichText` abstract model → `content = RichTextField` (`core/models.py`).
- `RichTextPage` (default page type).
- `BlogPost.content`.
- `Form.content` / `Form.response`.
- Anything a developer adds as `RichTextField`.

There are **no blocks, no embeds-as-objects, no typed embeds**. A gallery is a separate page type with inlines. A form is a separate page type with inlines. An image inside a blog post is an `<img src="...">` that TinyMCE inserted.

### Inline editing — how it actually works

This is Mezzanine's distinctive authoring feature. It is also the most fragile.

**Enable flag:** `INLINE_EDITING_ENABLED = True` (`core/defaults.py`).

**Template contract** (`docs/inline-editing.rst`):

1. `{% include "includes/footer_scripts.html" %}` before `</body>` → `{% editable_loader %}`.
2. Wrap fields: `{% editable page.title %}...{% endeditable %}`. Multiple fields on the same instance can share one tag.

**Server path:**

- `editable` tag (`mezzanine_tags.py`) parses `instance.field`, checks `is_editable(obj, request)` (change perm + site permission), builds a ModelForm via `get_edit_form()` for the listed fields, renders `includes/editable_form.html`.
- `editable_loader` renders the toolbar HTML into `window.__toolbar_html`, dumps TinyMCE media, and loads overlay + form + `editable.js`.
- POST hits `core.views.edit` (`@staff_member_required`): reconstructs the model, rebinds the form, saves, writes a Django admin log entry, returns `""` on success or the first error string.

**Client path (`editable.js`):**

1. Inject toolbar into `body`.
2. Bind `.editable-form` submit → `tinyMCE.triggerSave()` → `jquery.form` `ajaxSubmit` → **`location.reload()`** on empty response.
3. For each `.editable-original`, position an "Edit" link and a highlight box, then attach **jQuery Tools Overlay** with a 90% black expose.
4. Toolbar open/closed is a cookie `mezzanine-admin-toolbar`.

The overlay is a yellow (`#fffcc3`) modal floating at 50%/50% with `!important` CSS everywhere because it is injected into arbitrary front-end themes (`editable.css` says this out loud). TinyMCE inside that overlay is forced to `min-width: 770px`. Cancel is a `:button` close. There is no dirty check, no conflict detection, no partial DOM update. Save = full page reload.

**What inline editing is not:**

- Not contenteditable-on-the-page (you do not type in the live heading).
- Not a side panel.
- Not Gutenberg's "edit the block in place."
- Not Wagtail's live preview pane.
- It is: hover → Edit icon → modal form (sometimes TinyMCE) → AJAX POST → reload.

It was a 2011 "don't make the author leave the site" idea. The instinct is still correct. The implementation is a jQuery Tools museum.

### Static proxy — a CDN scar

`core.views.static_proxy` exists because TinyMCE plugin HTML dialogs and "the uploadify SWF" break when `STATIC_URL` is on another host (cross-domain JS). The view rewrites the URL, finds the file via staticfiles, and for `.htm` injects `<base href>`. The comment still mentions **Uploadify**, a Flash uploader. The proxy is still mounted at `/admin/asset_proxy/`. That is how old this stack is.

---

## 3. Draft / preview / schedule UX

README claims: *"Save as draft and preview on site"* and *"Scheduled publishing."* Both are true in the narrowest possible sense.

### Data model (`Displayable` in `core/models.py`)

```228:265:/Users/prondubuisi/gitrepos/dev/mezzanine/mezzanine/core/models.py
CONTENT_STATUS_DRAFT = 1
CONTENT_STATUS_PUBLISHED = 2
CONTENT_STATUS_CHOICES = (
    (CONTENT_STATUS_DRAFT, _("Draft")),
    (CONTENT_STATUS_PUBLISHED, _("Published")),
)
...
    status = models.IntegerField(..., default=CONTENT_STATUS_PUBLISHED, ...)
    publish_date = models.DateTimeField(_("Published from"), ..., blank=True, null=True)
    expiry_date = models.DateTimeField(_("Expires on"), ..., blank=True, null=True)
```

Two states. Default is **Published**, not Draft. `publish_date` auto-fills to `now()` on first save if empty. `expiry_date` is optional unpublish.

`DisplayableAdmin` exposes this as:

- Horizontal radio for status.
- `(publish_date, expiry_date)` on the same row.
- List: `title`, `status` (list-editable), `admin_link` ("View on site").
- `date_hierarchy = "publish_date"` unless modeltranslation is on (disabled because of a modeltranslation bug).

`DisplayableAdminForm.clean_content` requires `content` if status is Published. That is the only "you cannot publish an empty body" check. It only fires if the form has a `content` field.

### "Preview"

There is **no preview view, no preview token, no draft URL, no iframe, no shareable unpublished link**.

What exists:

- `PublishedManager.published(for_user=)` returns **everything** if `for_user.is_staff`, else filters `status=PUBLISHED` and date window (`core/managers.py`).
- `Displayable.published()` is the same rule.
- `admin_link` is `get_absolute_url()` with the text "View on site."

So "preview drafts" means: log in as staff, click "View on site," see the live template with the draft object because the queryset did not filter it out. Front-end caches must not serve that to anonymous users (Mezzanine's cache middleware has staff/nevercache exceptions; that is a separate concern). There is no "preview this revision as an anonymous user." There is no "send the editor a preview link."

Docs (`content-architecture.rst`) call this "Draft/published status with the ability to preview drafts." That is the feature. It is a queryset exception, not a preview product.

### "Schedule"

`publish_date` / `expiry_date` are just columns the published manager filters on. There is no celery beat, no "goes live in 3 hours" UI, no timezone picker beyond Django's datetime widget, no "scheduled" status (a future `publish_date` with `status=Published` is the schedule). Authors must understand that Published + future date = hidden. The help text says so. The UI does not visualize a timeline.

### What is missing vs every modern CMS

| Capability | Mezzanine | Gutenberg | Wagtail | Sanity |
|---|---|---|---|---|
| Draft vs published | Binary int field | Revision + status | Workflow + revisions | Draft vs published dataset |
| Autosave | No (plugin unused) | Yes | Yes | Yes (real-time) |
| Revisions / history | Django admin log only (who changed, not what) | Full revisions | Revisions + compare | Transaction log / history |
| Dedicated preview | Staff-sees-draft on live URL | Preview + Gutenberg canvas | Live preview pane | Presentation panes |
| Preview-as-anonymous / share link | No | Preview links | Yes (optional) | Yes |
| Scheduled publish | Datetime columns | Yes | Yes | Yes (scheduled actions) |
| Unpublish schedule | `expiry_date` | Yes | Yes | Yes |
| Workflow / review | No | Plugin territory | Built-in | Plans / roles |
| Collaboration | Last-write-wins, no lock | Presence in Gutenberg | Locking, comments | Real-time CRDT |
| Default new object | **Published** | Draft | Draft | Draft |

Quick Blog is the one place that forces draft: `BlogPostForm` sets `status = CONTENT_STATUS_DRAFT` and posts to `admin:blog_blogpost_add` (`blog/forms.py`, `blog/templates/admin/includes/quick_blog.html`). It also does a client-side `\n` → `<p>`/`<br>` conversion because the dashboard field is a plain textarea, not TinyMCE. That is the entire "fast authoring" path.

`TweetableAdminMixin` can tweet on save if `python-twitter` is installed and a "Send to Twitter" checkbox (hacked into the status widget HTML) is checked. That is 2012 social, not editorial workflow.

---

## 4. Dashboard widgets

The dashboard is Django admin's `index.html`, restyled, with **three columns of inclusion tags**.

`mezzanine/core/templates/admin/index.html`:

```19:26:/Users/prondubuisi/gitrepos/dev/mezzanine/mezzanine/core/templates/admin/index.html
{% block content %}<div id="content-main">{% dashboard_column 0 %}</div>{% endblock %}
{% block sidebar %}
    <div id="content-related" class="dashboard1">{% dashboard_column 2 %}</div>
    ...
    <div id="content-related" class="dashboard2">{% dashboard_column 1 %}</div>
```

`DASHBOARD_TAGS` (`core/defaults.py`):

```python
# with blog installed:
(
    ("blog_tags.quick_blog", "mezzanine_tags.app_list"),
    ("comment_tags.recent_comments",),
    ("mezzanine_tags.recent_actions",),
)
```

`dashboard_column` (`mezzanine_tags.py`) does `{% load tag_lib %}{% tag_name %}` for each dotted path. That is the widget API: **write an inclusion tag, add its name to a setting.** No widget class, no user-configurable dashboard, no per-user layout, no charts, no unpublished-count, no "what's scheduled this week."

Shipped widgets:

1. **Quick Blog** — title + plaintext content → save as draft. Permission-gated.
2. **App list** — grouped ModelAdmin links with Add/Change, ordered by `ADMIN_MENU_ORDER`. This is Django's app index, reused.
3. **Recent comments** — from `mezzanine.generic` (when blog is installed).
4. **Recent actions** — Django's `{% get_admin_log 10 %}` (`admin/includes/recent_actions.html`).

There is also a **Settings** changelist (`mezzanine/conf/admin.py`) that is not a dashboard widget: it redirects add/change to a single form of every `editable=True` `register_setting()` value, grouped. That is a useful "site options" screen. It is a big POST form, not a design-token or site-editor surface.

`ADMIN_MENU_ORDER` is the other information-architecture win: named groups, optional custom titles, optional named URLs (Media Library). `BlogCategoryAdmin.has_module_permission` hides itself unless explicitly listed. `ContentTypedAdmin.has_module_permission` hides page subclasses so only `Page` appears in the menu. These are good ModelAdmin tricks. They are not a dashboard product.

IE7 comment in `index.html`: `<!--[if IE 7]><style>.dashboard #content {padding-top: 80px;}</style><![endif]-->`. The dashboard still carries IE7 padding.

---

## 5. Media / filebrowser

Media is **not in this repo.** It is `filebrowser_safe`, mounted by `LazyAdminSite`:

```63:81:/Users/prondubuisi/gitrepos/dev/mezzanine/mezzanine/boot/lazy_admin.py
        # Filebrowser admin media library.
        fb_name = getattr(settings, "PACKAGE_NAME_FILEBROWSER", "")
        if fb_name in settings.INSTALLED_APPS:
            ...
                re_path(r"^media-library/$", lambda r: redirect("fb_browse"), name="media-library"),
                re_path(r"^media-library/", include(fb_urls)),
```

Default menu entry: `(_("Media Library"), "media-library")`.

`FileField` in `core/fields.py` is an alias: if `filebrowser_safe` imports, use its `FileBrowseField` (directory = `upload_to`); else fall back to Django `FileField` and drop `format`/`extensions` kwargs.

Integration points:

- TinyMCE `custom_file_browser` → `fb_browse?pop=5&type=...`
- Front-end inline editor gets the same `window.__filebrowser_url`
- Docs describe a `browseMediaLibrary` JS helper in `filebrowser/js/filebrowser-popup.js` (lives in the fork, not here) that custom widgets can call
- `MEDIA_LIBRARY_PER_SITE` puts each site in its own directory
- Galleries (`galleries/admin.py`) are `TabularDynamicInlineAdmin` of images, CSS-only extra
- `ADMIN_THUMB_SIZE = "24x24"` for list-display thumbs (`admin_thumb` mixin in `utils/models.py`; blog featured image uses it)
- Middleware still has a comment about "the handler for the flash file uploader in filebrowser"

What authors get: a **filesystem browser** (folders, upload, rename) in a popup or a dedicated admin section. Not a DAM. Not focal-point cropping (beyond whatever filebrowser_safe still has). Not renditions as first-class objects (Mezzanine generates `.thumbnails` on the fly). Not asset metadata, not collections, not "this image is used on 12 pages."

Wagtail's image chooser + renditions, Sanity's asset pipeline, and WP's Media Library + block bindings are all a generation ahead. Mezzanine's media story is "browse the uploads directory."

---

## 6. How far behind Gutenberg, FSE, real-time collab, block bindings

Measure in **product capabilities**, not stars on GitHub.

### Content model

Mezzanine content is:

- A **page tree of Django models** (`Page` + `ContentTyped` subclasses: `RichTextPage`, `Link`, `Form`, `Gallery`, plus whatever you register).
- Or a **flat Displayable** (`BlogPost`).
- Body = **one HTML string**.

That last fact is the entire gap.

Gutenberg: body is a block list (attributes + innerBlocks), serialized as HTML comments or as the block editor document. FSE: templates and template parts are block documents. Block bindings: a block attribute can bind to a post meta / pattern override / dynamic source.

Wagtail: `StreamField` is a typed sequence of StructBlocks, with nesting, choosers, and a React editor. Page types are models (this part Mezzanine already has, and it is the one place Mezzanine is closer to Wagtail than to WP).

Sanity: documents are JSON with Portable Text (typed spans + marks + block types). Real-time. Studio is a separate app.

Mezzanine: `RichTextField` → TinyMCE 4 → bleach → `{{ page.content|richtext_filters }}`. The "block" is a `<p>`. The "binding" is a Django template tag a developer wrote.

### Site editing / theming

FSE lets a non-dev edit headers, footers, templates. Painful, slow, nested-block hell — but it exists.

Mezzanine theming is Django templates. `pages/richtextpage.html` is:

```1:11:/Users/prondubuisi/gitrepos/dev/mezzanine/mezzanine/pages/templates/pages/richtextpage.html
{% extends "pages/page.html" %}
{% load mezzanine_tags %}
{% block main %}{{ block.super }}
{% editable page.richtextpage.content %}
{{ page.richtextpage.content|richtext_filters }}
{% endeditable %}
{% endblock %}
```

A developer owns layout. An author owns a blob and some SEO fields. There is no template part editor, no global styles UI (except `conf.Setting` key-values), no `theme.json`, no pattern library.

`HOST_THEMES` can swap template packages per hostname. That is multi-site theming for developers, not FSE.

### Real-time collaboration

Zero. No presence, no Yjs, no locks, no "Sarah is editing this." `edit` view is `form.save()` and reload. Two staff on the same draft: last POST wins. Django admin is the same.

### Block bindings / dynamic sources

None. Related posts on `BlogPost` are an M2M with `filter_horizontal`. Categories are M2M. Keywords are a `KeywordsField` with a click-to-toggle chip UI (`keywords_field.js`) that AJAX-saves keyword IDs. Those are relations, not bindings. You cannot drop a "latest 3 posts" *object* into a page body; you write a template tag or a custom page type.

### Page tree (the one place Mezzanine still feels like a CMS)

This is the best authoring surface in the repo.

`pages/admin.py` + `admin/pages/page/change_list.html` + `page_tree.js` + `jquery.mjs.nestedSortable.js`:

- Changelist is **not** a Django result table. It is a nested `<ol>` from `{% page_menu "pages/menus/admin.html" %}`.
- Drag to reparent/reorder → POST `/admin/admin_page_ordering/` → updates `_order` and parent.
- Per-node "Add …" `<select>` of registered content types, with `?parent=`.
- Expand/collapse persisted in cookie `mezzanine-admin-tree`.
- Custom `can_delete` / `can_move` / `overridden()` permissions.
- Slug changes propagate down the tree (`PageAdmin.save_model` + `_old_slug`).

This is closer to Wagtail's explorer (tree of page types) than to WP's page list. It is also jQuery UI sortable from 2016, GIF arrows, and a `<select>` to add a child. It works. It is not a 2026 IA tool (no search-in-tree, no bulk move, no locale trees, no preview-on-hover).

### Forms builder

`forms/admin.py`: `FieldAdmin(TabularDynamicInlineAdmin)` — add fields, drag order, export entries CSV. This is a real authoring tool and still useful. It is not Gravity Forms / Typeform / Wagtail FormBuilder 2024, but it is more than Gutenberg gives you out of the box.

### Distance score (editorial, not engineering)

If Gutenberg 2026 is 100:

| Surface | Mezzanine | Note |
|---|---|---|
| Body editing | 12 | TinyMCE 4 HTML blob |
| Layout / FSE | 5 | Dev templates only; inline edit is a modal |
| Typed content | 25 | Page *types* exist; in-page *blocks* do not |
| Preview | 18 | Staff-sees-live-URL |
| Schedule / workflow | 20 | Two dates, two statuses |
| Media | 22 | Filesystem browser |
| Collab | 0 | — |
| Dashboard | 20 | Three inclusion-tag columns |
| Tree / IA | 45 | Best part of the product |
| Extensibility for devs | 55 | ModelAdmin + settings + widget swap — this is the Django advantage |

Mezzanine is **not "a bit behind Gutenberg."** It never entered the block era. It is a strong 2012 Django CMS that gained Django version bumps and almost no authoring evolution.

---

## 7. What a 2026+ editor would look like that is BETTER than Gutenberg

Gutenberg's known failures (from a decade of WP):

- Nested blocks (Group → Columns → Group → Columns) destroy UX and performance.
- Everything is a block, so chrome, content, and data fight for the same tree.
- Theme.json / FSE is a non-dev theming system that developers also hate.
- Block bindings arrived late and feel bolted on.
- The canvas *is* the document; structured data is an afterthought (post meta, block attrs as JSON-in-HTML).
- Performance falls off a cliff on long posts.
- Collaboration is still not the product.

Do **not** clone Gutenberg on Django. Do **not** clone Wagtail's StreamField 1:1 either (nested StreamBlocks recreate the same soup). Steal Sanity's document model and Wagtail's page types, then reject both UIs.

### Design constraints (non-negotiable)

1. **Content is typed data, not HTML.** A page body is a list of typed blocks with JSON attributes. HTML is a render target.
2. **Nesting depth max = 2.** Section → items. No group-in-group-in-column. Layout is a *property of a section* (grid/stack/split), not a recursive block.
3. **Two surfaces, one document.** Outline (structure, like Sanity desk + a block list) and Canvas (visual, like a constrained Webflow). Never one recursive tree trying to be both.
4. **The live Django template is the preview.** Mezzanine's only remaining advantage. Do not invent a React replica of the front end. Stream the same template with a preview context (anonymous, mobile, scheduled-at).
5. **Page types stay models.** `Page` / `ContentTyped` is the right skeleton. Blocks live *inside* a type, they do not replace types.
6. **Bindings are first-class.** A block attribute can be literal, or bound to a model field, a queryset, a setting, or a function. That is how you beat Gutenberg's bindings and Sanity's references without FSE.
7. **Authors never see a sidebar with 40 controls.** One inspector, contextual, 5–7 controls. Advanced is behind a disclosure. Gutenberg's inspector is why civilians bounce.
8. **Default is draft. Autosave. Revisions. Optional presence.** Table stakes. Not differentiators.

### Architecture sketch

```
Displayable / Page          ← keep (status, dates, SEO, tree, site)
  └── body: BlockStream     ← replace RichTextField for new types
        ├── Section(layout=stack|split|grid, region=main)
        │     ├── RichText(portable text, not TinyMCE HTML)
        │     ├── Figure(asset ref, alt, caption, crop)
        │     ├── PullQuote
        │     ├── Embed(provider, url)
        │     └── Query(bind: BlogPost.published[:3])   ← binding
        └── Section(...)
```

Portable text (Sanity-style) for prose: spans, marks, annotations that point at internal objects (a link *is* a `Displayable` ref, not an href string). Render through Django templates per block type. A designer (or a very small theme package) ships block templates. An author never edits HTML.

**Visual layout without Gutenberg complexity:**

- Sections are the only layout primitive. Each section has a layout enum and a slot list of fixed cardinality (split = 2 slots, grid = 2–4). You cannot nest a section in a slot.
- Tokens (space, type scale, color) come from `conf.Setting` / a design-token JSON the theme owns. Authors pick `emphasis: quiet|normal|loud`, not `padding-top: 37px`.
- The canvas is the *real page* with contenteditable islands for portable text and drag handles on sections. Not an iframe of a fake editor stylesheet, and not a modal (`editable.js` dies).

**Why this beats Gutenberg:**

- No nested-block performance death: the tree is shallow by construction.
- Non-dev theming is tokens + section layouts, not a site editor that reimplements CSS.
- Structured content is queryable (Sanity win) *and* preview is the real site (Mezzanine/Wagtail win).
- Bindings mean "latest posts" is data, not a frozen HTML embed.
- Devs still write Python page types and Django templates — Mezzanine's actual constituency.

---

## 8. Keep vs kill list — current admin JS/CSS

### KEEP (concept, often not the file)

| Item | Path | Why |
|---|---|---|
| Page tree IA | `pages/templates/admin/pages/page/change_list.html`, `pages/menus/admin.html` | Best authoring surface. Rebuild the JS; keep the model. |
| `admin_page_ordering` | `pages/views.py` | Correct AJAX contract. |
| `ContentTyped` + add-type `<select>` | `core/admin.py`, `content_typed_change_list.html` | Page types are the right abstraction. |
| `Displayable` fields | status, dates, SEO fieldset | Right model, weak UX. |
| `ADMIN_MENU_ORDER` + dropdown | `defaults.py`, `dropdown_menu.html` | Persistent IA. Restyle. |
| `DASHBOARD_TAGS` *idea* | inclusion-tag columns | Keep the hook; replace the widgets. |
| `RichTextField` widget swap | `fields.py`, `RICHTEXT_WIDGET_CLASS` | Keep the *seam*; change the default. |
| `RICHTEXT_FILTERS` + bleach | `utils/html.py` | Server-side sanitization stays even if the editor changes. |
| `FileField` alias | `core/fields.py` | Keep the abstraction; replace filebrowser later. |
| `editable` template tag contract | `mezzanine_tags.editable` | Keep `{% editable obj.field %}` as the opt-in. Replace the overlay. |
| `is_editable` / site permission | `utils/views.py`, `SitePermission` | Correct access model. |
| `SingletonAdmin` | `utils/admin.py` | Still useful. |
| `OwnableAdmin` | `core/admin.py` | Correct for multi-author blogs. |
| Forms builder inlines | `forms/admin.py` | Keep; restyle. |
| Settings single form | `conf/admin.py` | Keep; this is the token/settings home. |
| `displayable_links_js` | `core/views.py` | Keep as the internal-link source for a new editor. |
| `LazyAdminSite` deferral | `boot/lazy_admin.py` | Needed while EXTRA_MODEL_FIELDS exists. |
| Keywords chip idea | `keywords_field.js` | Rebuild as a tag input; kill the `+/-` text toggle. |
| Gallery inlines | `galleries/admin.py` | Keep as a page type. |

### KILL (files / stacks)

| Item | Path | Why |
|---|---|---|
| Entire TinyMCE 4.1.10 tree | `core/static/mezzanine/tinymce/` (~90 JS files, IE7 skin, SWF, example plugins) | EOL, XSS surface, Flash leftover. |
| `tinymce_setup.js` as default | `core/static/mezzanine/js/tinymce_setup.js` | Goes with TinyMCE. |
| `jquery.tinymce.min.js` | same tree | — |
| jQuery Tools Overlay + Expose | `jquery.tools.overlay.js`, `jquery.tools.toolbox.expose.js` | Unmaintained; `jQuery.browser` polyfill. |
| jQuery Form 3.51 | `jquery.form.js` | 2014; replace with `fetch`. |
| `editable.js` as written | `js/editable.js` | Modal + reload. Keep the tag, not this file. |
| `editable.css` yellow modal | `css/editable.css` | `!important` theme-fighting. |
| Chosen 0.9.12 | `chosen/` | Native `<select>` / a modern combobox. |
| jQuery UI 1.12.1 (admin-wide) | `js/jquery-ui-1.12.1.js` + `css/smoothness/` | Only nestedSortable needs it; replace both. |
| `jquery.mjs.nestedSortable.js` | `pages/static/...` | Replace with a small dnd-kit/Sortable or native DnD. |
| `dynamic_inline.js` Grappelli branch | `js/admin/dynamic_inline.js` | Rewrite against Django 4/5 inline events only. |
| `collapse.js` | `core/static/admin/js/collapse.js` | Grappelli fieldset class toggling; Django has its own. |
| IE7 / IE hacks | `index.html` IE7 comment; `skin.ie7.min.css`; `html5shiv.js`; `respond.min.js` | Docs already drop IE. |
| `moxieplayer.swf` | TinyMCE media plugin | Flash is dead. |
| `static_proxy` for TinyMCE `.htm` | `core/views.py` `static_proxy` | Dies with TinyMCE popups. Revisit only if a new editor has the same CDN issue. |
| Uploadify references | comments in `views.py`, `middleware.py` | Dead product. |
| Tweet-on-save mixin | `twitter/admin.py` | Not editorial. |
| Quick Blog `\n`→HTML script | `quick_blog.html` | Symptom of no editor on the dashboard. |
| `login.js` breadcrumb hack | `js/admin/login.js` | Tiny; fold into a new shell. |
| `tabbed_translation_fields.js` (as a one-off) | if modeltranslation stays, use its admin or a real i18n desk | Custom jQuery UI tabs for locales is 2013. |
| `grappelli_safe` as a *hard* identity | dependency | Skin can remain until a new shell ships; do not design new features against `__grappelli_installed`. |
| Default `status=PUBLISHED` | `Displayable.status` | Kill the default. New objects are drafts. |

### TRANSITIONAL (keep until the new editor ships)

- `jquery-3.4.1.js` — Django admin still speaks jQuery; pin, don't build on it.
- `navigation.js` + `global.css` + `dashboard.css` + `rtl.css` — the chrome. Replace with the new shell, don't restyle forever.
- `ajax_csrf.js` — until everything is `fetch` + cookie CSRF.
- `filebrowser_safe` — keep as the media backend until a DAM/chooser exists; hide the Flash paths.
- `TinyMceWidget` — leave as an *opt-in* `RICHTEXT_WIDGET_CLASS` for sites that refuse to migrate blobs. Do not load it by default.

### Front-end JS that is not admin (do not confuse)

`core/static/js/bootstrap.js`, `bootstrap-extras.js`, `html5shiv.js`, `respond.min.js` are the public theme, not the editor. Kill html5shiv/respond with the theme refresh. Out of scope for the editor rewrite except that `base.html` always loads jQuery 3.4.1 for everyone, including anonymous visitors, because inline editing *might* load. That is a performance bug: staff-only JS is not staff-only on the parent page.

---

## 9. Revolutionary editor ideas

These are the ideas worth building. They are not "add Gutenberg." They are how a Django CMS in 2026 takes the crown Gutenberg dropped.

### 9.1 Typed blocks + structured content + visual layout (the core bet)

One document, three projections:

1. **Data** — JSON list of typed blocks (schema in Python, validated on save).
2. **Outline** — a calm list (like Notion's left edge, not Gutenberg's block list). Reorder, drop, bind.
3. **Canvas** — the real template, with section handles and portable-text islands.

Authors switch Outline ↔ Canvas. Developers never implement a third React theme.

### 9.2 Sections, not groups

Kill nested layout blocks. A `Section` has `layout: stack | split | grid | banner` and N slots. Slots hold *content* blocks only. This is how you get visual layout without Gutenberg's recursion tax. Think: constrained Webflow, or Apple Pages sections, not WP Groups.

### 9.3 Bindings as the query language authors can touch

A Query block: pick a content type, a published filter, a limit, a template. Stored as `{bind: "blog.BlogPost", filter: "published", limit: 3, card: "teaser"}`. Rendered by Django. Editors cannot break it by nesting a column in a query in a group.

This is Gutenberg block bindings done as a product, not a 6.5 footnote.

### 9.4 Portable text, not TinyMCE, not Markdown-only

Prose is a typed span tree. Annotations are objects (`InternalLink{id}`, `Footnote{id}`, `Term{id}`). You get Sanity's queryability and Mezzanine's `displayable_links_js` as the link source. Markdown can *import* into portable text. It should not be the storage format (you lose annotations).

### 9.5 Preview is the site, with roles

Keep the 2011 instinct (staff sees the page). Add:

- Preview bar: Anonymous / Staff / Custom role.
- Time-travel: render as of `publish_date`.
- Share token: unsigned-in preview for 24h.
- Device frames that hit the real responsive CSS (you already have a real front end; FSE does not).

Inline editing becomes: click a bound field on the canvas → inspector, or type in a portable-text island. **No yellow modal. No reload.** PATCH the block. Morphdom/htmx the section.

### 9.6 htmx/Django-first editor runtime

Do not start with a SPA. The outline and inspector can be Django fragments. Portable text needs a small isolated editor (TipTap / ProseMirror) mounted on islands. Canvas DnD is one library. This matches the team that actually maintains Mezzanine (Python, not a WP Gutenberg JS army).

Wagtail went React for StreamField and now owns a JS platform. That is a staffing decision. Mezzanine cannot staff a Gutenberg.

### 9.7 Presence later, locking now

Ship `updated` + a `editing_lock` (user, timestamp, heartbeat) before you ship Yjs. Most Mezzanine sites are 1–3 editors. Locking is the 80%. Real-time is a later mode on the same JSON document.

### 9.8 AI as a filler of typed fields, not a slot in the toolbar

Because content is typed, an "assist" can propose a `Figure.alt`, a `MetaData.description`, a section outline, a translation. Gutenberg's AI is "write more HTML." Structured assist is a product advantage Sanity is already playing. Mezzanine can do it server-side.

### 9.9 Kill the Admin/Site login radio by making one chrome

The radio exists because the admin and the site are different planets. The 2026 editor is a bar on the site (outline + inspector + preview roles) plus a *data* admin (users, settings, comments, form entries, media) that can stay Django admin. Authors almost never open ModelAdmin for pages/posts.

### 9.10 Migration path for the HTML blob

Do not require a flag day. `RichTextField` remains. A management command wraps existing HTML in a single `LegacyHTML` block. Authors can "explode" a legacy blob into typed blocks (server-side HTML → portable text + figures). Sites that refuse stay on `TinyMceWidget`.

---

## File map (this audit's primary sources)

| Concern | Files |
|---|---|
| Admin classes | `mezzanine/core/admin.py`, `pages/admin.py`, `blog/admin.py`, `forms/admin.py`, `galleries/admin.py`, `conf/admin.py`, `twitter/admin.py`, `utils/admin.py` |
| Admin site | `mezzanine/boot/lazy_admin.py`, `utils/conf.py` |
| Admin templates | `core/templates/admin/{base_site,index,login}.html`, `includes/{dropdown_menu,app_list,recent_actions,content_typed_change_list}.html`, `pages/templates/admin/pages/page/change_list.html`, `blog/templates/admin/includes/quick_blog.html`, `conf/templates/admin/conf/setting/change_list.html` |
| Editor JS/CSS | `core/static/mezzanine/js/{tinymce_setup,editable}.js`, `js/admin/*`, `tinymce/`, `chosen/`, `css/{editable.css,tinymce.css,admin/*}` |
| Inline edit | `core/views.py` `edit`, `core/forms.py` `get_edit_form`, `templatetags/mezzanine_tags.py` `editable` / `editable_loader`, `templates/includes/editable_{form,loader,toolbar}.html` |
| Publish model | `core/models.py` `Displayable`, `core/managers.py` `PublishedManager` |
| Media seam | `core/fields.py` `FileField`, `boot/lazy_admin.py` media-library URLs |
| Docs | `docs/admin-customization.rst`, `docs/inline-editing.rst`, `docs/content-architecture.rst`, `docs/frequently-asked-questions.rst`, `README.rst` |

---

## EXECUTIVE VERDICT

1. The admin is Django ModelAdmin wearing a frozen `grappelli_safe` skin, not a CMS editor; Mezzanine adds a left nav, dashboard tags, a page tree, and a TinyMCE textarea.
2. The WYSIWYG is TinyMCE **4.1.10 (2015)** with an IE7 skin, a Flash player, and `valid_elements: "*[*]"`; bleach is the real sanitizer.
3. Inline editing is a 2011 overlay: jQuery Tools modal + TinyMCE + `jquery.form` + full reload — right instinct, dead implementation.
4. Draft/preview/schedule is a boolean plus two datetimes; "preview" means staff are exempt from the published queryset; default status is Published.
5. Dashboard widgets are three columns of inclusion tags (Quick Blog, app list, comments, admin log). There is no editorial command center.
6. Media is `filebrowser_safe` — a filesystem browser in a popup — not a DAM, not bindings, not renditions-as-objects.
7. Versus Gutenberg/FSE/collab/bindings: Mezzanine never entered the block era; distance is a generation, except the page-type tree, which is closer to Wagtail and worth keeping.
8. Do not port Gutenberg. Gutenberg's nested-block UX, theme-json theming, and performance are the things to beat, not copy.
9. Keep: `Displayable`, page types, tree, `{% editable %}` contract, widget/filter seams, settings form, bleach. Kill: TinyMCE 4 tree, jQuery Tools, Chosen, jQuery UI smoothness, Grappelli as identity, yellow modal.
10. The 2026 editor is typed blocks + portable text + sections (max nest 2) + bindings, previewed on the real Django template, edited with islands + inspector — structured like Sanity, typed like Wagtail, visual without FSE, and finally better than Gutenberg because it refuses to be a recursive block tree.
