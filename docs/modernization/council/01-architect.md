# Mezzanine Content Architecture — Independent Architect Report

**Role:** General ARCHITECT (Byzantine council)
**Repo:** `/Users/prondubuisi/gitrepos/dev/mezzanine`
**Version in tree:** `mezzanine.__version__ = "9999dev0"` (`mezzanine/__init__.py`)
**Stack:** Django 2.2–5.2, Python 3.8–3.14 (`setup.cfg`). Delivery is server-rendered Django templates + Django admin (Grappelli-safe + Filebrowser-safe forks).
**Method:** Read the models, managers, middleware, views, admin, processors, project template, and docs. No speculation from memory.

---

## 1. Exact content-type inheritance

Mezzanine is not a single “post” table with a type column. It is a **stack of tiny abstract mixins** that are composed into two public bases — `Displayable` and `Page` — and then into concrete types. This is documented in `docs/content-architecture.rst` and implemented in `mezzanine/core/models.py` and `mezzanine/pages/models.py`.

### 1.1 Abstract kernel (`mezzanine/core/models.py`)

```
SiteRelated          (FK sites.Site, CurrentSiteManager, auto-assign on first save)
  └── Slugged        (title, slug, generate_unique_slug / get_slug)
        └── Displayable = Slugged + MetaData + TimeStamped
```

| Class | Kind | Fields / behaviour |
|---|---|---|
| `SiteRelated` | abstract | `site` FK (`editable=False`). `save(update_site=False)` stamps `current_site_id()` when the row is new or `update_site=True`. Default manager is `wrapped_manager(CurrentSiteManager)`. |
| `Slugged(SiteRelated)` | abstract | `title` (500), `slug` (2000, blank → auto). `generate_unique_slug()` queries `base_concrete_model(Slugged, self)` so Page subclasses share the Page slug namespace. |
| `MetaData` | abstract | `_meta_title`, `description`, `gen_description`, `keywords = KeywordsField()`. `description_from_content()` walks the first `RichTextField` then `TextField`, runs `richtext_filters`, then cuts at first `</p>` / sentence. |
| `TimeStamped` | abstract | `created`, `updated` (both `editable=False`, set in `save()`). |
| `Displayable(Slugged, MetaData, TimeStamped)` | abstract | Publishing: `status` ∈ {`CONTENT_STATUS_DRAFT=1`, `CONTENT_STATUS_PUBLISHED=2`}, `publish_date`, `expiry_date`, `short_url`, `in_sitemap`. Manager: `DisplayableManager`. `search_fields = {"keywords": 10, "title": 5}`. `published()` is an instance method; `get_absolute_url()` **raises `NotImplementedError`** so every searchable type must define a URL. |
| `RichText` | abstract | `content = RichTextField()`. `search_fields = ("content",)`. |
| `Orderable` | abstract, metaclass `OrderableBase` | `_order = OrderField`. Steals `Meta.order_with_respect_to` onto the class (Django’s own version broke `FK("self")`). `save()` assigns next sibling index; `delete()` decrements later siblings via `F("_order")-1`. |
| `Ownable` | abstract | `user` FK to `AUTH_USER_MODEL`. `is_editable(request)` = superuser or owner. |
| `ContentTyped` | abstract | `content_model` CharField(50, editable=False). `set_content_model()` writes the child class’s lowercase object name. `get_content_model()` does `getattr(self, self.content_model)`. `get_content_models()` returns every registered model that is a **strict subclass of the concrete ContentTyped base**. |

`wrapped_manager(klass)` (`core/models.py:28-37`) optionally mixes `modeltranslation.manager.MultilingualManager` in front of the real manager when `USE_MODELTRANSLATION` is on.

`base_concrete_model(abstract, model)` (`mezzanine/utils/models.py:35-72`) walks `__mro__` and returns the **super-most non-abstract** subclass of `abstract`. This is why `Slugged.generate_unique_slug`, `Orderable.save`, and `Displayable._get_next_or_previous_by_publish_date` all query `Page` (not `RichTextPage` / `Author`) when called on a page subtype.

### 1.2 Page stack (`mezzanine/pages/models.py`)

```
Orderable + Displayable
  └── BasePage          (only exists to attach PageManager so subclasses keep it)
        └── Page(BasePage, ContentTyped)     CONCRETE
              ├── RichTextPage(Page, RichText)
              ├── Link(Page)                 (slug is an external URL)
              ├── Form(Page, RichText)       mezzanine/forms/models.py
              └── Gallery(Page, RichText, BaseGallery)  mezzanine/galleries/models.py
```

`Page` adds:

- `parent` self-FK (`related_name="children"`)
- `in_menus` = `MenusField` (comma-separated IDs from `PAGE_MENU_TEMPLATES`)
- `titles` — denormalized `"Grandparent / Parent / Title"` path, rebuilt in `save()`
- `login_required`
- `Meta.order_with_respect_to = "parent"` so `_order` is per-sibling
- Dynamic perms: `can_add`, `can_change`, `can_delete`, `can_move` (the last raises `PageMoveException`)
- Hierarchical slug: `get_slug()` = `f"{parent.slug}/{slug}"`
- `set_slug(new)` prefix-rewrites every descendant whose slug starts with `self.slug + "/"`
- `set_parent(new)` cycle-checks, then rewrites slug relative to the new parent
- `overridden()` — True when `reverse("page", slug=…)` resolves to a view **other than** `pages.views.page` (i.e. a real Django urlpattern owns this slug)

**Documented hard limit** (`docs/content-architecture.rst:162-170`): *“When creating custom content types, you must inherit directly from the `Page` model. Further levels of subclassing are currently not supported.”* You cannot subclass `RichTextPage`. To get a WYSIWYG you mixin `RichText` alongside `Page`.

Custom types are Django **multi-table inheritance**. `Page.content_model` is the OneToOne related name (`"richtextpage"`, `"form"`, `"gallery"`, `"link"`, `"author"`, …). `page.author` / `page.get_content_model()` is how templates and admin reach the subtype.

### 1.3 Non-page content (`mezzanine/blog/models.py`)

```
Displayable + Ownable + RichText + AdminThumbMixin
  └── BlogPost          CONCRETE  (NOT a Page)

Slugged
  └── BlogCategory      CONCRETE
```

`BlogPost` has `categories` M2M → `BlogCategory`, `allow_comments`, `comments = CommentsField()`, `rating = RatingField()`, `featured_image = FileField`, `related_posts` M2M to self. URLs are **not** in the page tree: `get_absolute_url()` reverses `blog_post_detail` / `_year` / `_month` / `_day` depending on `BLOG_URLS_DATE_FORMAT`.

This is the CMS’s fundamental split, stated plainly in the docs: **`Displayable` = addressable published content that is not navigation. `Page` = Displayable that is a node in the nav tree.** Blog is a regular Django app whose list URL is usually also a Page, so breadcrumbs/menus still light up (see §2.5).

### 1.4 Generic attachments (`mezzanine/generic/`)

These are **not** content types. They hang off any model via `GenericForeignKey`:

| Model | Attached by | Notes |
|---|---|---|
| `Keyword(Slugged)` | `KeywordsField` → `AssignedKeyword` | Site-scoped tags. `KeywordManager.get_or_create_iexact`, `delete_unused`. |
| `AssignedKeyword(Orderable)` | GFK `(content_type, object_pk)` | `order_with_respect_to = "content_object"`. |
| `ThreadedComment` | `CommentsField` | Subclasses `django_comments.Comment` (which already has its own `site` FK, so it cannot inherit `SiteRelated`). `replied_to` self-FK, `by_author`, `rating`. |
| `Rating` | `RatingField` | `value` must be in `settings.RATINGS_RANGE`. |

`BaseGenericRelation` (`generic/fields.py`) is the clever bit: on `contribute_to_class` it **injects denormalized columns** onto the host (`keywords_string`, `comments_count`, `rating_count` / `_sum` / `_average`) and reconnects `post_save`/`post_delete` to recompute them. Search then hits `keywords_string`, not the GFK.

### 1.5 Everything else that looks like content

- `mezzanine.conf.models.Setting(SiteRelated)` — per-site editable settings (`name`, `value`).
- `mezzanine.core.models.SitePermission` — OneToOne user → M2M sites. Replaces raw `is_staff` for admin/inline-edit access.
- `mezzanine.forms.models.Field` / `FormEntry` / `FieldEntry` — form-builder rows, not Displayable.
- `mezzanine.galleries.models.GalleryImage(Orderable)` — images under a Gallery page; zip import lives on `BaseGallery.save()`.
- `mezzanine.utils.models.ModelMixin` — metaclass for injecting fields/methods onto third-party models. **Comment in source: “This currently isn’t used anywhere.”**

### 1.6 Field injection (the unofficial third inheritance path)

`mezzanine/boot/__init__.py` parses `EXTRA_MODEL_FIELDS` and calls `field.contribute_to_class(sender, name)` via `apps.lazy_model_operation`. Combined with `LazyAdminSite`, this lets a project splice columns onto `BlogPost` or `Page` without subclassing. `docs/model-customization.rst` itself warns that Django migrations then “belong” to `mezzanine.blog` / `mezzanine.pages` and you must relocate them with `MIGRATION_MODULES`. This is not an inheritance system. It is a load-time monkeypatch.

---

## 2. How page trees, slugs, sites, publishing, and drafts actually work

### 2.1 Tree

The tree is a **parent FK + integer sibling order + two denormalized paths**:

- `parent_id` / `children`
- `_order` (from `Orderable`, scoped by `order_with_respect_to = "parent"`)
- `slug` stored as the **full path** (`about/team/mike`), not the leaf
- `titles` stored as `"About / Team / Mike"`

There is **no** nested-set, materialized path, `ltree`, or `MP_Node`. Depth is computed in Python.

`PageManager.with_ascendants_for_slug(slug)` (`pages/managers.py:31-93`) is the only optimized tree read:

1. Split slug into prefixes: `['about', 'about/team', 'about/team/mike']`
2. One `filter(slug__in=slugs).order_by("-slug")`
3. Verify `pages[i].parent_id == pages[i+1].id`
4. On success, stash `pages[0]._ascendants = pages[1:]`

If any ancestor used a **custom slug** that does not prefix-match, the chain is invalid and `Page.get_ascendants()` falls back to walking `parent` one query at a time (`pages/models.py:125-133`).

Writes:

- `Page.save()` rebuilds `titles` by walking parents, then `set_content_model()`.
- `Page.set_slug(new)` does `Page.objects.filter(slug__startswith=old+"/")` and rewrites every descendant (skipping `overridden()` pages).
- `Page.set_parent(new)` cycle-checks, saves, then `set_slug` relative to the new parent (special case: `Link` with `http…` slug is left alone).
- Admin drag-and-drop: `pages.views.admin_page_ordering` (staff-only) calls `can_move` → `set_parent` → rewrites `_order` for old siblings and the posted `siblings[]` list. JS is `mezzanine/js/admin/page_tree.js` + `jquery.mjs.nestedSortable.js`. The changelist **is** the tree: `pages/templates/admin/pages/page/change_list.html` renders `{% page_menu "pages/menus/admin.html" %}`.

`page_menu` (`pages/templatetags/pages_tags.py`) loads **the entire published tree** once (`Page.objects.published(…).select_related(*all_content_model_names)`), groups by `parent_id` in a `defaultdict`, and recurses in the template. Fine for hundreds of pages. Not a strategy for tens of thousands.

### 2.2 Slugs

- Generated by `slugify` (`utils/urls.py`), default `slugify_unicode` (allows CJK / Cyrillic).
- Uniqueness is **application-level only**. `unique_slug(qs, "slug", slug)` loops `get()` and appends `-1`, `-2`, … There is **no** `unique=True` and **no** `UniqueConstraint` on `(site, slug)` in any pages/blog/core migration I read. The only `unique=True` in `mezzanine/**/migrations` is `SitePermission.user`. Concurrent creates can collide.
- Uniqueness is **per concrete model × current site**, because `CurrentSiteManager` is on the queryset `unique_slug` uses. A `BlogPost` slug does not collide with a `Page` slug at the DB level. A `RichTextPage` slug **does** collide with a `Gallery` slug, because both go through `base_concrete_model(Slugged, …) → Page`.
- Homepage is the magic slug `"/"` (`Page.get_absolute_url` → `reverse("home")`). `path_to_slug()` strips language code, `SITE_PREFIX`, and `PAGES_SLUG`.
- Catch-all route: `pages/urls.py` is `path("<path:slug>", views.page, name="page")`. `mezzanine/urls.py` mounts this **last**, after blog/accounts/core. The project template (`project_template/project_name/urls.py`) warns in all-caps: URL patterns added *below* `include("mezzanine.urls")` will never match.

### 2.3 Sites

Every `Slugged` (hence every `Displayable` / `Page` / `BlogPost` / `Keyword`) carries `site_id`. The default manager **always** filters to `current_site_id()` (`core/managers.py:391-412`). There is no “all sites” manager on these models. `CurrentSiteManager.use_in_migrations = False`.

`current_site_id()` (`mezzanine/utils/sites.py:15-66`) is a pipeline:

1. `override_current_site_id` thread-local (cannot nest — raises `RecursionError`)
2. `request.site_id` cache
3. `request.session["site_id"]` (admin site switcher, `core.views.set_site`)
4. `Site.objects.get(domain__iexact=request.get_host())` (cached)
5. `os.environ["MEZZANINE_SITE_ID"]` (management commands, `manage.py --site=ID`)
6. `settings.SITE_ID`

The request itself is stashed in a **thread-local** by `mezzanine.core.request.CurrentRequestMiddleware`. Site resolution, `get_absolute_url_with_host`, bit.ly short URLs, and host-theme loading all depend on it.

### 2.4 Publishing and drafts

Constants (`core/models.py:228-233`):

```
CONTENT_STATUS_DRAFT = 1
CONTENT_STATUS_PUBLISHED = 2
```

That is the entire workflow. No pending review, no private, no password, no “future” as a separate state (scheduling is a datetime on a Published row).

`PublishedManager.published(for_user=None)` (`core/managers.py:56-70`):

- If `for_user is not None and for_user.is_staff`: **return everything** (drafts, expired, future).
- Else: `status=PUBLISHED` AND (`publish_date <= now` OR null) AND (`expiry_date >= now` OR null).

`PageManager.published` then additionally excludes `login_required=True` for unauthenticated users unless `PAGES_PUBLISHED_INCLUDE_LOGIN_REQUIRED` or the caller passes `include_login_required=True` (PageMiddleware does, so it can still enforce the login redirect).

`Displayable.save()` default-fills `publish_date = now()` if null — so a freshly created “Published” item is live immediately. The quick-blog admin form (`blog/forms.py`) forces `CONTENT_STATUS_DRAFT`.

**“Preview drafts” in the README is this staff bypass.** There is no preview token, no unsigned public URL, no “preview as anonymous”, no draft-specific route. If you are staff and you know the slug, `get_object_or_404(BlogPost.objects.published(for_user=request.user), slug=slug)` returns the draft. If you are not staff, it 404s.

`Displayable.published()` (instance method) is the same date/status test **without** the staff bypass — used for “is this item currently public?”.

### 2.5 Routing: middleware + processors + template cascade

This is the most distinctive piece of the architecture.

`PageMiddleware.process_view` (`pages/middleware.py:57-121`):

1. `pages = Page.objects.with_ascendants_for_slug(path_to_slug(path), for_user=…, include_login_required=True)`
2. Deepest match → `request.page`. Even `/blog/my-post/` matches the `/blog/` Page, so menus/breadcrumbs/`login_required` still work for non-page apps. This is how Blog is “in” the tree without being a Page.
3. If `page.login_required` and anonymous → `redirect_to_login`.
4. If the matched view is **not** `pages.views.page`, call it; on `Http404`, if the page slug equals the request slug, swallow the 404 and fall through to the page view. That is how a Page at `/blog/about/` can exist even though the blog urlconf owns `/blog/<slug>/`.
5. Run page processors (slug-specific first, then model-specific). A processor may return `HttpResponse` (replaces the view) or a `dict` (merged into context).
6. Call `pages.views.page`.

`pages.views.page` refuses to run unless `PageMiddleware` (or a subclass) is installed. Template selection, most-specific first:

```
<Page.get_template_name()>
pages/<slug>.html                  (homepage → pages/index.html)
pages/<slug>/<content_model>.html
pages/<each-ascendant-slug>/<content_model>.html
pages/<content_model>.html
pages/page.html
```

Processors are registered by `@processor_for(Model | "app.Model" | "some/slug")` in any `INSTALLED_APPS` module named `page_processors.py`, autodiscovered from `pages/urls.py`. The stock example is `@processor_for(Form)` in `mezzanine/forms/page_processors.py` — it builds `FormForForm`, handles POST, spam, email, signals, and either redirects or returns `{"form": form}`.

### 2.6 Admin for types

- `DisplayableAdmin` — status radio, publish/expiry, collapsed metadata (slug, description, keywords, sitemap).
- `ContentTypedAdmin` — hides subclasses from the admin index; `change_view` on a raw `Page` redirects to the subtype admin; `changelist_view` exposes `content_models` for the “Add …” dropdown.
- `PageAdmin(ContentTypedAdmin, DisplayableAdmin)` — slug-change propagation via `_old_slug`; `?parent=` for creating under a node; `ADD_PAGE_ORDER` sorts the add dropdown; `can_*` enforced.
- Subtype admins are **not listed in the admin index**. They only appear as types you can add from the page tree. That is the entire “custom content type UI”.

---

## 3. Multi-site / multi-tenancy today

What exists is **Django sites, turned always-on, with host-based resolution, plus per-site staff ACL and per-host themes.** It is not schema isolation, not a separate process per site, and not WordPress Multisite.

### What you get

- One running process, many `django.contrib.sites.Site` rows.
- Almost all content is `SiteRelated` and silently partitioned by `CurrentSiteManager`.
- Admin users switch sites via session (`core.views.set_site`); the admin stays on one domain.
- `SitePermission` + `SitePermissionMiddleware`: a staff user without a row for the current site is logged out of `/admin/` and shown `no_site_permission`. Superusers bypass. `has_site_permission(user)` is the public check; inline editing uses it too.
- `HOST_THEMES = [(host, 'theme_package'), …]` + `mezzanine.template.loaders.host_themes.Loader` (the old `TemplateForHostMiddleware` is deprecated). Themes are Django apps whose `templates/` win for that host. `docs/multi-tenancy.rst` describes a “base theme + thin overlays” pattern and notes that **content types defined in the base theme are shared across sites**.
- `conf.models.Setting` is per-site, so editable settings (Analytics ID, etc.) vary by tenant.
- Redirects (`SiteRedirectAdmin`) are filtered and stamped with `current_site_id()`.
- Cache keys go through `cache_key_prefix`, which itself calls `current_site_id()` — per-site cache, with a careful exception inside `current_site_id` to avoid recursion.

### What you do not get

- Isolated media. The docs say it out loud: *“these sites will share some resources, such as the media library.”* Filebrowser-safe is a filesystem browser over `MEDIA_ROOT`, not a site-scoped asset table.
- Isolated users. One `auth.User` table. Isolation is `SitePermission.sites`.
- Isolated content types. A `HomePage(Page)` registered in theme A is available in the add-page dropdown of site B.
- Isolated search indexes, isolated comment stores beyond the `site` FK, isolated file storage backends.
- Tenant-specific installed apps, middleware, or URLConfs (except whatever you branch on `current_site_id()` yourself).
- Row-level security. Forget `CurrentSiteManager` once (raw `Page._base_manager`, a report query, a migration, a management command without `--site`) and you see every tenant.
- Request isolation compatible with async/ASGI. Site identity lives on `threading.local()`.

This is **good multi-site for a single organisation with several domains and one editorial team**. It is not a SaaS tenancy model.

---

## 4. What’s missing vs WordPress

I am comparing against the product surface that made WordPress the default CMS, not against Django’s own strengths.

| WordPress capability | Mezzanine today | Gap |
|---|---|---|
| **Revisions / autosave** | `TimeStamped.updated` only. Saving overwrites the row. | Total absence. No `wp_posts.post_parent` revision chain, no autosave, no “compare / restore”. |
| **Custom post types UI** | Code-first: write a model subclassing `Page` or `Displayable`, migrate, register `PageAdmin`. Dropdown is built from `ContentTyped.get_content_models()`. | Editors cannot create types. Devs cannot create types without MTI + migration. One-level inheritance only. |
| **Taxonomies** | `Keyword` (flat, generic, JS widget) + `BlogCategory` (flat, blog-only M2M). No hierarchical taxonomy, no shared vocabularies, no term meta, no UI to attach a new taxonomy to an existing type. | Keywords are a good *tag* implementation. They are not a taxonomy system. |
| **Media library** | `filebrowser_safe` (fork of django-filebrowser) over the filesystem. `FileField` in `core/fields.py` aliases `FileBrowseField` if the package imported, else Django `FileField`. Galleries are a Page type with zip import. Featured images are a path string on `BlogPost`. | No first-class media *content* (no site, slug, publish, keywords, alt, focal point, usage tracking). Media is not in `Displayable.objects.url_map`. Shared across tenants. |
| **Block / structured content** | One `RichTextField` (HTML `TextField`) with TinyMCE (`RICHTEXT_WIDGET_CLASS`) and bleach/`utils.html.escape` sanitization. | The body is an opaque HTML blob. No blocks, no inner content, no reusable patterns, no editor that can target a JSON document. Gutenberg cannot be bolted onto this column. |
| **REST / GraphQL** | No DRF, no serializers, no `wp-json`. Public HTTP surface is HTML views + `/search/` + `/edit/` (staff POST) + `/rating/` + `/comment/` + RSS/Atom for blog + `displayable_links_js` (TinyMCE link list). | Headless, mobile apps, Gutenberg-class editors, and JS frontends have nothing to talk to. |
| **Preview tokens** | Staff session + `PublishedManager` bypass. | Cannot share a draft with a client. Cannot preview as anonymous. Token-in-URL does not exist anywhere in `mezzanine/**/*.py`. |
| **Roles / capabilities** | Django perms + `Page.can_*` + `OwnableAdmin` queryset filter + `SitePermission`. | No capability map, no “editor vs author vs contributor”, no per-type role UI. Ownable is “superuser or owner”. |
| **Workflow** | Draft / Published + publish_date / expiry_date. | No pending review, no scheduled-as-revision, no notes, no assigned reviewer. |
| **Multisite as a product** | Host-matched Site FK. | No domain-mapped super-admin the way WP Multisite does, no per-site plugins, shared media, shared types. |
| **Plugin / theme ecosystem** | Django apps + `page_processors` + `HOST_THEMES` + `EXTRA_MODEL_FIELDS`. Cartridge (ecommerce) is a sister project. | No install-from-admin, no hook index, no stable public extension API beyond “subclass Page and decorate a processor”. |
| **Search** | `SearchableQuerySet.search`: tokenize, then one `__icontains` Q per (term × field), then `annotate_scores()` materializes **all** rows into a Python list and counts substring occurrences, then divides by `age ** SEARCH_AGE_SCALE_FACTOR`. `SearchableManager.search` unions every leaf `Displayable` subclass in Python and `sorted(..., reverse=True)`. | Will not survive a mid-size catalogue. No stemming, no ranking index, no Postgres FTS, no ES. |
| **Comments** | Present (`ThreadedComment`, Disqus option, Akismet hook). | One of the few WP-class features that actually exists. |
| **i18n** | Optional `django-modeltranslation` (`USE_MODELTRANSLATION`). `core/translation.py` translates `title`, `_meta_title`, `description`, `content`. Admin gets tabbed translation JS. | Field-level, not WPML-style translation sets / independent permalink trees. |

Mezzanine **does** have things WP does not: real Django models per type, page processors, host-based single-process multi-site, scheduled expiry, inline front-end editing (`editable` template tag + `/edit/`), a forms builder that is a Page type, and a search API that any `Displayable` subclass joins automatically. Those are not enough to call it WordPress-class.

---

## 5. What is genuinely elegant and MUST be kept

These are not nostalgic. They are the reason a rewrite that starts from Wagtail/django-cms would be a downgrade in specific ways.

1. **The mixin kernel.** `SiteRelated` / `Slugged` / `MetaData` / `TimeStamped` / `Displayable` / `RichText` / `Orderable` / `Ownable` / `ContentTyped` are small, independently useful, and compose. `Displayable` as “anything with a URL, meta, and a publish window” is the right grain. Keep the names, the responsibilities, and the `search_fields` inheritance convention.

2. **The Page / Displayable split.** Navigation-shaped content (`Page`) and stream-shaped content (`BlogPost`) share publishing/search/site/SEO but do not share a tree. WordPress collapsed both into `wp_posts` and has been apologising with `exclude_from_search` / `show_in_nav` ever since. Do not collapse this.

3. **`content_model` + `get_content_model()` + `ContentTypedAdmin`.** A stored discriminator that points at the MTI child, plus admin that hides subtypes from the index and redirects `Page` change views to the real type, plus an “Add …” dropdown built from registered subclasses. The *idea* is the CPT registry. The MTI implementation is disposable; the API is not.

4. **Page processors.** `@processor_for(Form)` returning either a context dict or an `HttpResponse` is the best extension point in the codebase. It lets a type own its POST cycle without replacing `pages.views.page` and without a plugin framework. Forms, and any future “this page *does* something”, should keep this exact contract.

5. **PageMiddleware’s “app under a page” rule.** Matching the deepest page prefix, honouring `login_required`, marking the nav node active, and only falling through to the page view on a swallowed `Http404` is how a real Django app (blog, shop, docs) lives inside a CMS tree. This is more honest than WP’s “a page whose template is `archive-product.php`”.

6. **`with_ascendants_for_slug` assuming slug path == tree path.** One query for the breadcrumb, the template cascade, and the current page. Combined with `set_slug` / `set_parent` maintaining the invariant, this is a correctly denormalized tree. Keep the invariant; make it stricter.

7. **`current_site_id()` pipeline + `override_current_site_id` + `SitePermission`.** Session-switch in admin, host match in public, env var in CLI, setting as last resort, and a context manager for cross-site work. This is a complete, documented, testable multi-site story. Keep the pipeline; move it off thread-locals.

8. **`BaseGenericRelation` denormalising into real columns.** Search and list pages do not JOIN comments/keywords/ratings. Signals keep a `*_string` / `*_count` / `*_average` in sync. This pattern should be the template for any new “attached” concern (taxonomies, relations, translations).

9. **Template cascade and `get_template_name()`.** Per-page, per-section, per-type templates with no configuration object. Combined with `HOST_THEMES`, a designer can skin one page, one section, one type, or one hostname.

10. **`DisplayableManager.url_map()`.** One call produces the sitemap *and* the TinyMCE link picker *and* (in a future world) a site-graph API. It already knows about publish state, staff, and http(s) Link slugs.

11. **Instance-level `can_add` / `can_move`.** Tree constraints (“an Author may have at most one child”, “cannot become top-level”) expressed on the model, enforced in the AJAX reorder endpoint, surfaced as a Django message via `PageMoveException`. This is better than capability strings for hierarchical content.

12. **Inline editing.** `editable` / `endeditable` wrapping any model field, `/edit/` POST, `Ownable.is_editable` + `has_site_permission`. Front-end edit without a separate builder is a product advantage. Keep the idea even if the jQuery implementation is replaced.

---

## 6. Hard architectural dead ends

These cannot be evolved into WordPress-class behaviour without replacing the mechanism. Decorating them will waste years.

### 6.1 Multi-table inheritance as the content-type system

Every custom type is a Django subclass, a new table, a OneToOne to `pages_page`, a migration in that app, and an admin class. `ContentTyped.get_content_models()` literally does `apps.get_models()` + `issubclass`. Consequences:

- Editors will never create types.
- You cannot version a type independently of a deploy.
- Second-level subclassing is explicitly unsupported.
- `page_menu` `select_related`s every subtype name on every menu render (`pages_tags.py:49-52`).
- `EXTRA_MODEL_FIELDS` exists *because* people did not want another JOIN — and it breaks migrations (`docs/model-customization.rst:76-118`).

Wagtail escaped this with `page_ptr` still MTI but a single rich StreamField; WP escaped it with one table + `post_type`. Mezzanine is stuck in the worst middle: a table per type *and* an unstructured HTML body.

### 6.2 HTML blob as the body

`RichText.content` is a sanitized HTML string. There is no document model. Any block editor, any structured field, any headless renderer, any per-block permission or revision, requires a new column (or a new table) and a dual-write/migration story. TinyMCE + bleach is a finished design, not a starting point.

### 6.3 Thread-local request as a platform bus

`CurrentRequestMiddleware` (`core/request.py`) puts `request` on `_thread_local`. `current_site_id`, `current_request().build_absolute_uri`, host themes, short URLs, and cache prefixes all read it. This is incompatible with:

- Django ASGI / async views
- `sync_to_async` thread hops
- management commands that forget `--site`
- any worker that handles two sites in one process without the context manager

You can keep the *pipeline*. You cannot keep the storage.

### 6.4 Search that materializes the world

`SearchableManager.search` builds a Python list of every matching row of every leaf model and sorts it. `annotate_scores` iterates fields in Python and does `str.count`. This is a demo. It cannot be “tuned”. The *API* (`search_fields` on the model, `objects.search(query, for_user=)`, `SEARCH_MODEL_CHOICES`) is keepable. The engine is not.

### 6.5 Catch-all HTML routing as the only delivery

`pages/urls.py` is a single `<path:slug>` pattern. Middleware may intercept other views’ 404s. There is no resource identifier other than the path, no content negotiation, no API mount. A headless or hybrid future cannot be “a new urlconf on the side” without also inventing IDs, serializers, and a preview channel — i.e. a second CMS.

### 6.6 Application-level slug uniqueness + denormalized path that can lie

No DB constraint. `unique_slug` is check-then-insert. Custom slugs break `with_ascendants_for_slug`, which then N+1s. `Link` slugs are URLs in the same column. `set_slug` prefix-rewrites with string surgery. This will not survive a move to predictable preview URLs, translation-specific slugs, or an API that keys by path.

### 6.7 Admin-as-CMS, via two third-party forks

`PACKAGE_NAME_FILEBROWSER = "filebrowser_safe"` and `PACKAGE_NAME_GRAPPELLI = "grappelli_safe"` are hard-wired in the project template. The page tree is a Grappelli changelist with nestedSortable. Stacked dynamic inlines *require* Grappelli (`core/admin.py:234-237`). Media is a file browser. This couples the product to two personally-forked admin skins. A Gutenberg-class editor, a media library, and a CPT UI cannot be built on this surface; they would be a second admin.

### 6.8 `EXTRA_MODEL_FIELDS` / `ModelMixin`

Load-time contribution of fields onto someone else’s model is how you get un-ownable migrations and mysterious `_meta` state. The docs already recommend a OneToOne “customizations” model instead. Treat field injection as deprecated. Do not build types on it.

### 6.9 Draft = “staff can see it”

`PublishedManager.published` short-circuits on `is_staff`. Every staff user is a preview user for every draft on the site. There is no hook to plug a token into. Preview-as-anonymous and shareable drafts require a new manager path, not a flag.

### 6.10 Shared media + shared types under multi-site

The tenancy model partitions *rows that inherited `SiteRelated`*. It does not partition files, type registries, or users. Promoting this to SaaS without a storage and registry rethink will leak.

---

## 7. Independent verdict: evolve vs extract vs rewrite

**Extract the kernel. Evolve the apps that already sit on it. Replace the content-body and type-registry implementations. Do not rewrite the CMS, and do not try to become WordPress by growing `RichTextField` and MTI.**

Reasons, from the code:

- The abstract models, site pipeline, page tree invariant, processors, middleware “app under page” rule, `DisplayableManager.url_map`, and GenericRelation denormalisation are small, coherent, and better than the equivalent pieces in several larger CMSs. Throwing them away to “just use Wagtail” discards the only original architecture.
- The things that make a CMS WordPress-class — revisions, CPT UI, taxonomies, media-as-content, blocks, REST, preview tokens — are **absent**, not “present but weak”. They do not have a fork-point inside `RichTextPage.content` or `PageAdmin`. They need new models that *implement the existing abstract APIs*.
- Evolving in place (add django-reversion, add DRF on `Page`, swap TinyMCE for a block editor writing HTML) produces a Frankenstein that still has MTI types, thread-locals, icontains search, and a filesystem media library. That is how projects die: every missing WP feature is shimmed onto the dead end that prevented it.
- A greenfield rewrite will re-litigate the Page/Displayable split, the processor contract, and host-based multi-site, and will probably get them worse. The project template, 35+ locale trees, forms builder, galleries, accounts, and inline editing are also real product, not debris.

### What “extract kernel” means in this repo

Promote a documented, import-stable kernel:

```
mezzanine.core.models   SiteRelated, Slugged, MetaData, TimeStamped,
                        Displayable, RichText, Orderable, Ownable, ContentTyped
mezzanine.core.managers DisplayableManager (site + published + search interface)
mezzanine.utils.sites   current_site_id pipeline (request-scoped, not thread-local)
mezzanine.pages.models  Page tree + content_model discriminator
mezzanine.pages.page_processors  processor_for + autodiscover
mezzanine.pages.middleware       PageMiddleware contract
mezzanine.generic.fields         BaseGenericRelation pattern
```

Freeze their behavioural contracts with tests. Then, *beside* them (not inside `RichTextField.clean`):

- a type registry that does not require MTI
- a document/block column with a plaintext projection for search
- a `Revisable` mixin and signed preview tokens that plug into `published(for_user=)`
- a Taxonomy model that generalises `Keyword`/`AssignedKeyword`
- a `Media` Displayable that replaces filebrowser as the source of truth
- a read API that serialises `url_map` + the tree

Blog, forms, galleries, accounts stay as apps on the kernel. Cartridge stays a sister app. Grappelli/Filebrowser become optional skins, not the CMS.

### What success is *not*

Success is not “feature-complete with WordPress.” Success is a Django-native CMS whose **content kernel** is as good as WP’s `wp_posts` + taxonomies + REST, while keeping Mezzanine’s actual advantages (typed models, processors, host multi-site, Page/Displayable split, inline edit). If the goal is “non-developers install plugins and invent post types in a UI, with Gutenberg,” extract the kernel and put a new editorial app on it — or stop and use WordPress. Pretending `PageAdmin` + TinyMCE will grow into that UI is how this codebase stays 2012 forever.

---

## 8. Revolutionary but implementable ideas (on Mezzanine’s strengths)

Each of these reuses a named abstraction that already exists. None of them require throwing the tree away.

### 8.1 Registry types without MTI (“CPT UI” that still feels like Page)

Keep `ContentTyped.content_model` as the discriminator and `Page` / `Displayable` as the row. Add a `ContentTypeDef` model (name, slug, kind=`page|displayable`, JSON schema or field spec, template, processor dotted-path, menu flag). `get_content_model()` returns either the MTI child **or** a `TypedPayload` row (`OneToOne` + `JSONField`) for registry types. `ContentTypedAdmin.get_content_models()` already builds the add dropdown from a list of objects with `add_url` and `meta_verbose_name` — it does not care how the class got there. Editors get “Add type” in admin; developers keep real models for Form/Gallery. One-level MTI remains for built-ins; user types stop paying a JOIN per type.

### 8.2 `RichText` becomes a document, not HTML

Do not add a parallel body field and hope. Change the *contract* of `RichText`:

- `content` stores a JSON block stream (heading, rich-text, image, embed, form, raw HTML).
- `content_html` / `content_text` are generated projections (`search_fields` already accepts any TextField; `description_from_content()` already hunts for a `RichTextField` then a `TextField` — point it at `content_text`).
- TinyMCE remains one block type, so existing pages migrate as a single `raw_html` block.

Page processors, inline `editable` on `content`, and `DisplayableAdminForm.clean_content` keep working. Gutenberg-class editing becomes a JS app against a documented schema, not a rewrite of `Page`.

### 8.3 `Revisable` mixin + tokens that plug into `published(for_user=)`

Add `Revisable` next to `TimeStamped`: on save, snapshot the concrete row (and `get_content_model()` payload) as JSON keyed by `(content_type, object_pk, n)`. A signed preview token carries `{model, pk, rev, site_id, as: "anon"|"staff"}`. A thin middleware or a `for_user` stand-in makes `PublishedManager.published` accept that token the same way it today accepts `is_staff`. Shareable drafts, compare, restore, and “preview as public” fall out of the manager that already exists. Do **not** adopt django-reversion’s generic object dump as the product — it does not know about `content_model` or site.

### 8.4 Taxonomy kernel, extracted from `Keyword` + `BlogCategory`

`AssignedKeyword` is already a GFK with order. Promote:

```
Taxonomy(Slugged)          # "Tags", "Blog categories", "Topics"; hierarchical?
Term(Slugged)              # parent FK if taxonomy.hierarchical
TermAssignment(Orderable)  # GFK + term FK   (== today’s AssignedKeyword)
```

`KeywordsField` becomes a `TermsField(taxonomy="keywords")`. `BlogPost.categories` becomes a `TermsField(taxonomy="blog-category")`. Any Displayable can grow a vocabulary without a new M2M table. This is the WP taxonomy model implemented with Mezzanine’s existing GenericRelation denormalisation (`terms_string` for search).

### 8.5 Site-graph API from `url_map` + the tree

`DisplayableManager.url_map(for_user=)` plus `Page.objects.published().order_by("_order")` plus `with_ascendants_for_slug` already know every public URL, its object, and its nav position. Expose:

- `GET /api/site` — current site, menus (the same `PAGE_MENU_TEMPLATES` IDs), tree
- `GET /api/resolve?path=` — what PageMiddleware does, as JSON (`page`, `content_model`, `payload`, `ascendants`)
- `GET /api/search?q=` — same `objects.search` interface

This is headless **without** inventing a second permission/publish/site stack. The first client is a replacement for `displayable_links_js` and the sitemap. The second is a Next/Astro frontend that still honours `login_required` and drafts via the token in 8.3.

### 8.6 Processors as the plugin protocol

Formalise what `forms/page_processors.py` already does:

```python
@processor_for(Form, exact_page=True, provides=["form"], cache="never")
def form_processor(request, page): ...
```

Declare provided context keys, whether the processor may return a response, whether it is preview-safe, whether it is cacheable (`nevercache` already exists in the cache middleware). Auto-generate a plugin list in admin. Third-party apps then extend Mezzanine the way they already do — a `page_processors.py` — but the CMS can reason about them. This is a plugin system that does not become WP’s `add_action('init', ...)`.

### 8.7 Make the slug-path invariant real (ltree / path column)

`with_ascendants_for_slug` is correct only when slug prefixes equal parent chains. Add a `path` (or Postgres `ltree`) and `depth` maintained in `Page.save` / `set_parent` / `set_slug`, and a DB `UniqueConstraint(site, slug)`. Reject (or specially mark) custom slugs that break prefixing — `Link` already has a `content_model == "link"` escape hatch. Menus and breadcrumbs become `path__descendants` queries instead of “load the entire tree into a defaultdict”. This is the scalability fix for the one tree algorithm the codebase actually has.

### 8.8 Media as `Displayable`

Replace filebrowser-as-source-of-truth with:

```
class Media(Displayable):  # title, slug, site, publish, keywords, in_sitemap
    file = FileField(...)
    kind = ...  # image/doc/video
    alt, focal, width, height, checksum
```

`url_map` then includes media; search finds it; multi-site partitions it; TinyMCE and the block editor pick from `/api/resolve` instead of a filesystem tree; galleries become `TermAssignment`s or ordered GFKs to `Media` instead of a parallel `GalleryImage` file column. Filebrowser can remain a UI over `Media` rows. This also closes the tenancy leak the multi-tenancy doc admits.

---

## Sources (read, not remembered)

- `mezzanine/core/models.py` — SiteRelated, Slugged, MetaData, TimeStamped, Displayable, RichText, Orderable, Ownable, ContentTyped, SitePermission
- `mezzanine/core/managers.py` — PublishedManager, SearchableQuerySet/Manager, CurrentSiteManager, DisplayableManager
- `mezzanine/core/fields.py` — RichTextField, MultiChoiceField, FileField
- `mezzanine/core/admin.py` — DisplayableAdmin, ContentTypedAdmin, OwnableAdmin, SitePermissionUserAdmin
- `mezzanine/core/views.py` — set_site, edit, search, displayable_links_js
- `mezzanine/core/middleware.py` — SitePermissionMiddleware, cache pair, RedirectFallbackMiddleware
- `mezzanine/core/request.py` — thread-local CurrentRequestMiddleware
- `mezzanine/pages/models.py` — BasePage, Page, RichTextPage, Link, PageMoveException
- `mezzanine/pages/managers.py` — PageManager.published, with_ascendants_for_slug
- `mezzanine/pages/middleware.py` — PageMiddleware
- `mezzanine/pages/views.py` — admin_page_ordering, page
- `mezzanine/pages/admin.py` — PageAdmin, LinkAdmin
- `mezzanine/pages/page_processors.py` — processor_for, autodiscover
- `mezzanine/pages/templatetags/pages_tags.py` — page_menu
- `mezzanine/pages/fields.py` — MenusField
- `mezzanine/blog/models.py`, `views.py`, `admin.py`, `urls.py`
- `mezzanine/generic/models.py`, `fields.py`, `managers.py`
- `mezzanine/forms/models.py`, `page_processors.py`
- `mezzanine/galleries/models.py`
- `mezzanine/boot/__init__.py` — EXTRA_MODEL_FIELDS
- `mezzanine/utils/sites.py`, `utils/urls.py`, `utils/models.py`
- `mezzanine/urls.py`, `project_template/project_name/{settings,urls}.py`
- `docs/content-architecture.rst`, `model-customization.rst`, `multi-tenancy.rst`, `search-engine.rst`, `inline-editing.rst`, `multi-lingual-sites.rst`

---

## EXECUTIVE VERDICT

Mezzanine is a coherent Django CMS kernel wrapped in a 2012 product, not a failed WordPress.
Keep Displayable vs Page, the mixin stack, processors, host-site pipeline, and the slug-path tree.
Do not keep MTI-as-CPT, HTML-as-body, thread-local site, icontains search, or filebrowser-as-media.
WordPress-class features (revisions, CPT UI, taxonomies, blocks, REST, preview tokens) are absent, not unfinished — they need new models behind old interfaces.
Evolve-in-place will shim those features onto the dead ends that prevent them.
A greenfield rewrite will re-lose the Page/Displayable split and the processor contract.
Extract the kernel, replace type registry + document + media + preview, leave blog/forms/galleries as apps.
That is the only path that becomes a modern CMS without discarding the architecture that is actually good.
