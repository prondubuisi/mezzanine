# 06 — Extensibility

**Seat:** General EXTENSIBILITY  
**Question:** How do you extend Mezzanine? Can it ever have a WordPress-scale plugin/theme economy?  
**Repo:** `/Users/prondubuisi/gitrepos/dev/mezzanine`  
**Constraint:** Independent, from code. Do not become WordPress plugin hell.

---

## EXECUTIVE VERDICT

**No. Mezzanine cannot, and must not, grow a WordPress-scale plugin/theme economy.**

Mezzanine already has a *developer* extension model that is honest, small, and Django-native: subclass `Page` / `Displayable`, drop a `page_processors.py` into an `INSTALLED_APP`, register settings in `defaults.py`, override templates, unregister/re-register admin. That is a real platform. It is not a marketplace.

WordPress scale requires a different product: one-click install by a non-developer, global `do_action` / `apply_filters` hooks, a theme JSON contract, and an install-time process that mutates a running site. Mezzanine has none of those, by design. The README states the philosophy in the first screen:

> "Unlike many other platforms that make extensive use of modules or reusable applications, Mezzanine provides most of its functionality by default."  
> — `README.rst`

That sentence is both the reason Mezzanine felt good in 2010 and the reason its third-party list is a cemetery of abandoned GitHub repos. The revolutionary move is **not** to add PHP-style global hooks. It is to keep batteries included, expose a *typed capability surface* (content type, processor, setting, template pack, admin widget), and treat "apps" as reviewed, signed, versioned packages that cannot XSS the admin. Anything else recreates WordPress plugin hell inside a Python process that has no sandbox.

**Can it have a healthy plugin economy?** A small one, yes — Wagtail-sized, not WordPress-sized. Ten to fifty maintained apps. Never sixty thousand. The architecture, the audience, and the language all forbid it.

---

## 1. Extension points today

There is no plugin loader, no package manifest, no install UI, and almost no signal bus. Extension is "write a Django app and wire it by hand." The surface is larger than it first looks, but every hook is *developer-facing*.

### 1.1 Content types (`Page` / `Displayable`)

Primary API. Documented in `docs/content-architecture.rst`.

- Abstract mixins in `mezzanine.core.models`: `SiteRelated`, `Slugged`, `MetaData`, `TimeStamped`, `Displayable`, `Ownable`, `RichText`, `Orderable`.
- `Displayable` = URL + SEO + draft/publish + search. For things that are *not* in the nav tree (blog posts).
- `Page` = `Displayable` + hierarchical tree + `ContentTyped`. For things that *are* the nav tree.
- Ship-with types: `BlogPost`, `RichTextPage`, `Link`, `Form`, `Gallery`.

Custom type:

```python
class Author(Page):
    dob = models.DateField("Date of birth")

admin.site.register(Author, PageAdmin)
```

Discovery is implicit. `ContentTyped.get_content_models()` walks `apps.get_models()` and returns every subclass (`mezzanine/core/models.py`). The admin page tree then lists those types (`mezzanine/pages/admin.py` `PageAdmin.get_content_models()`, ordered by `ADD_PAGE_ORDER`).

Hard limits, documented and enforced:

- **One level of subclassing only.** You cannot subclass `RichTextPage`. Need WYSIWYG? Multiple-inherit `Page` and `RichText`. (`docs/content-architecture.rst`)
- Multi-table inheritance. Access is `page.author` / `page.get_content_model()`. Every custom type is a JOIN.
- `content_model` is a `CharField` stamped on first save and never changes. (`ContentTyped.set_content_model`)

This is a *content-type* plugin model, not a *behavior* plugin model. You add nouns. You do not add verbs except via page processors.

### 1.2 Page processors — the only real hook

`mezzanine/pages/page_processors.py`:

```python
processors = defaultdict(list)

def processor_for(content_model_or_slug, exact_page=False):
    ...
    processors[model_name].insert(0, parts)   # or "slug:%s"
```

Autodiscover copies `django.contrib.admin.autodiscover`: import `<app>.page_processors` for every `INSTALLED_APP`. Called from `mezzanine/pages/urls.py`.

Runtime is `PageMiddleware.process_view` (`mezzanine/pages/middleware.py`):

1. Resolve closest `Page` by slug (so a blog post still carries its parent blog page).
2. Honour `login_required`.
3. Run slug processors, then model processors.
4. Processor may return `dict` (merged into template context) or `HttpResponse` (short-circuits the page view).

The built-in forms app is the canonical consumer (`mezzanine/forms/page_processors.py` `@processor_for(Form)`). It is also the only first-party module that fires custom signals (`form_valid` / `form_invalid` in `mezzanine/forms/signals.py`).

What this is **not**:

- No priority / `before` / `after`. Registration order is `insert(0)` plus INSTALLED_APPS order.
- No disable, no per-site opt-out, no admin toggle.
- No type on the return value beyond "dict or HttpResponse."
- Bare `except:` around import, then re-raise only if the submodule exists. A typo in `page_processors.py` crashes startup; a missing file is silent.
- Processors run in the request process with full Django/ORM/settings access. Zero isolation.

This is Django's "convention module + decorator registry" pattern. It is a hook. It is not a plugin API.

### 1.3 Settings registry (`mezzanine.conf`)

The closest thing Mezzanine has to a plugin configuration API, and it is genuinely good.

- Each app ships `defaults.py` calling `register_setting(...)`.
- `mezzanine/conf/__init__.py` autoloads `defaults` from every `INSTALLED_APP` (mezzanine apps last, so project/third-party can win / `append=True`).
- `editable=True` settings persist in `mezzanine.conf.models.Setting` and are edited as **one form** in admin (`mezzanine/conf/admin.py` `SettingsAdmin` — add/change redirect to changelist).
- `mezzanine.conf.settings` is a drop-in for `django.conf.settings`: registered → Django settings.py → DB → default.

Constraints that kill a plugin marketplace:

- Editable values are only `str` / `int` / `bool`. No JSON, no lists, no secrets vault.
- If the name exists in `settings.py`, `editable` is forced `False`. Project file always wins. Correct for ops; fatal for "install plugin, configure in UI."
- AppConfig `ready()` is **not** auto-imported (`docs/configuration.rst`). Modern Django apps that only use AppConfig must remember to import `defaults` by hand. Easy to miss.
- Settings are process-global. Multi-tenant `HOST_THEMES` does not give per-theme settings.

`register_setting(..., append=True)` is the documented way for an external app to extend an existing setting (e.g. grow `ADMIN_MENU_ORDER` or `RICHTEXT_FILTERS`). CHANGELOG: "Added hook for third-party apps to extend existing settings." That is the entire composition story.

### 1.4 Template overrides and "themes"

There is no theme package format.

What exists:

1. **Django template override.** Project `templates/` first, then app directories. `collecttemplates` (`mezzanine/core/management/commands/collecttemplates.py`) copies Mezzanine/Cartridge templates into the project so you can edit them. Default app filter: `a.split(".")[0] in ("mezzanine", "cartridge")`.
2. **Per-page template resolution** (`mezzanine/pages/views.py`). For slug `authors/dr-seuss` of type `author`, the view builds a candidate list: exact slug, `get_template_name()`, parent/type combinations, `pages/author.html`, `pages/page.html`. Powerful for designers who live in the repo. Useless as a marketplace SKU.
3. **`HOST_THEMES`** (`mezzanine/core/defaults.py`, loader `mezzanine/template/loaders/host_themes.py`, helper `mezzanine/utils/sites.py:host_theme_path`). A sequence of `(hostname, importable_python_package)`. The loader prepends `<package>/templates`. Documented as "theme inheritance" in `docs/multi-tenancy.rst`: a "base" theme app with models + `base.html`, child theme apps that only ship `templates/pages/index.html`. Themes are **Django apps**. They go in `INSTALLED_APPS`. They can (and the docs encourage them to) define models, admin, templatetags.

`README.rst` advertises a "Free Themes Marketplace." The link is `https://github.com/thecodinghouse/mezzanine-themes` — a GitHub repo, not a store. CHANGELOG 1.4.11 (Aug 2013) added "mezzatheme themes marketplace" to the features list. That marketplace is gone. What remains is "put a Python package on `INSTALLED_APPS` and hope the templates match this year's `base.html` blocks."

No `theme.json`. No style tokens. No guaranteed block names. Override `base.html` and you own the upgrade.

### 1.5 Admin

Mezzanine treats the admin as the CMS. Extension is Django admin, plus a few registries.

| Hook | Where | What it does |
|---|---|---|
| `PageAdmin` / `ContentTypedAdmin` | `pages/admin.py`, `core/admin.py` | Register a `Page` subclass; extra fields are auto-inserted into fieldsets if you don't define your own |
| `admin.site.unregister` + subclass | `docs/model-customization.rst` | Official way to add a field to `BlogPostAdmin`: `deepcopy(fieldsets)`, `insert`, re-register |
| `ADMIN_MENU_ORDER` | `core/defaults.py` | Group/order the persistent left nav; can inject `(title, named_url)` pairs |
| `DASHBOARD_TAGS` | `core/defaults.py` | Three columns of inclusion tags. CHANGELOG: "Initial version of admin dashboard plugin system" — it is just template tag names |
| `ADMIN_REMOVAL` | `boot/lazy_admin.py` | Dotted paths to hide from admin after autodiscover |
| `LazyAdminSite` | `mezzanine/boot/lazy_admin.py` | Defers unregister so `EXTRA_MODEL_FIELDS` exist before custom ModelAdmins load; also swallows `AlreadyRegistered` / `NotRegistered` |
| `has_module_permission` | `docs/admin-customization.rst` | Hide a ModelAdmin from the menu unless listed in `ADMIN_MENU_ORDER` |
| `SingletonAdmin` | `mezzanine/utils/admin.py` | One-row models |
| `RICHTEXT_WIDGET_CLASS` / `TINYMCE_SETUP_JS` | admin-customization | Swap the editor |
| Filebrowser / Grappelli | `PACKAGE_NAME_FILEBROWSER`, `PACKAGE_NAME_GRAPPELLI` | Hard-forked optional skins, auto-appended via `OPTIONAL_APPS` |

`mezzanine.boot` is forced to index 0 of `INSTALLED_APPS` (`utils/conf.py:set_dynamic_settings`). It exists *only* to inject fields and patch `admin.site`. That is load-order magic, not an extension API.

The `deepcopy(BlogPostAdmin.fieldsets)` dance is the official customization story. It is brittle across upgrades: any upstream fieldset edit silently conflicts. A plugin that does this against `BlogPost` will break on the next Mezzanine release. There is no `ModelAdmin` hook point, no `contrib` registry, no `get_fieldsets` override convention beyond "subclass and pray."

### 1.6 Field injection (`EXTRA_MODEL_FIELDS`)

`mezzanine/boot/__init__.py` parses a four-tuple setting and calls `field.contribute_to_class` via `apps.lazy_model_operation`. This is how a project adds `BlogPost.image` without subclassing.

The docs are unusually honest (`docs/model-customization.rst`, "Field Injection Caveats"):

- Django `makemigrations` wants to write the migration into `mezzanine.blog`.
- Workaround: `MIGRATION_MODULES` for the injected app *and every subclass app* (`pages`, `forms`, `galleries`, …).
- "Be warned that over time this approach will almost certainly require some manual intervention by way of editing migrations, or modifying the database manually."

They then recommend the alternative: a `OneToOneField` sidecar model + admin inline. Extra query, but you own the migrations.

A plugin economy cannot be built on either path. Injection fights the migration system. Sidecars fight the query planner. Both require a developer.

### 1.7 Generic relations — comments, keywords, ratings

`mezzanine.generic.fields` (`KeywordsField`, `CommentsField`, `RatingField`) is the mixin-style extension: drop a field on *any* model, get denormalized `*_count` / `*_string` / `*_average` columns plus template tags. Documented in `docs/utilities.rst`. The blog is the reference implementation.

This is actually a clean capability: "this model is commentable / taggable / rateable." It is the closest the codebase comes to typed capabilities. It is not discoverable as a plugin; you edit the model.

### 1.8 Search

Any `Displayable` / `Page` subclass is searchable. `search_fields` on the model (tuple or `{field: weight}`). `SEARCH_MODEL_CHOICES` and `{% search_form %}` control the public UI. Third-party models work if they subclass `Displayable`. Cartridge's `shop.Product` is the documented example (`docs/search-engine.rst`).

No search-backend plugin. No indexer interface. SQLite/MySQL/Postgres `LIKE` / `SearchableManager`.

### 1.9 Rich-text pipeline

`RICHTEXT_FILTERS` is a list of dotted callables, "like Django's middleware or context processors" (`docs/admin-customization.rst`). `RICHTEXT_WIDGET_CLASS` swaps TinyMCE for Markdown or nothing. Sanitize level via `RICHTEXT_FILTER_LEVEL` + bleach allowlists (`mezzanine/utils/html.py`).

A plugin that wants Markdown registers a filter and a widget. That is a real, small capability.

### 1.10 Accounts / profiles

`ACCOUNTS_PROFILE_MODEL = "myapp.MyProfile"`. OneToOne to User. `post_save` on `AUTH_USER_MODEL` creates the row (`mezzanine/accounts/models.py`). Form class / exclude fields are settings. Not a plugin; a setting.

### 1.11 Optional apps and project scaffold

`OPTIONAL_APPS` in the project template (`mezzanine/project_template/project_name/settings.py`): if the package imports, it is appended to `INSTALLED_APPS`. Used for `debug_toolbar`, `django_extensions`, `compressor`, `filebrowser_safe`, `grappelli_safe`. This is "optional dependency detection," not a plugin loader. No version pin, no capability declaration, no uninstall.

`mezzanine-project --alternate PACKAGE` (`mezzanine/bin/management/commands/mezzanine_project.py`) re-runs startproject against `PACKAGE/project_template` and overlays files. Comment in source: "Eg cartridge, drum." First-party siblings get a blessed project template. Third parties do not.

`set_dynamic_settings` then mutates `INSTALLED_APPS` / `MIDDLEWARE` (force `mezzanine.boot` first, admin/staticfiles last, auto-add `mezzanine.generic` + `django_comments` if blog is present, auto-add LocaleMiddleware, etc.). Implicit coupling: install blog, get comments whether you wanted them or not.

### 1.12 Signals — almost none

Repo-wide custom signals:

| Signal | Location | Purpose |
|---|---|---|
| `form_valid` / `form_invalid` | `mezzanine/forms/signals.py` | After form-page submit |
| `post_save` on User | `accounts/models.py` | Create profile |
| `post_save` / `post_delete` | `generic/fields.py` | Denormalize counts |
| `comment_was_posted` | `generic/forms.py` | Upstream django-comments |

That is the entire hook bus. No `page_saved`, no `menu_items`, no `admin_ready`, no `render_content`. A WordPress plugin author looking for `the_content` will not find it. A Django developer will use model inheritance, processors, and template overrides — which is the point.

### 1.13 Third-party Django apps under a Page URL

`docs/content-architecture.rst` "Integrating Third-party Apps with Pages": create a `Page` whose slug matches the app's urlpattern. `PageMiddleware` attaches `request.page` so nav/breadcrumbs light up. The blog is implemented this way (it is *not* a `Page` subclass).

This is the blessed "I already have a Django app" path. It is integration, not a plugin contract.

---

## 2. Cartridge ecommerce relationship

Cartridge is not a plugin. It is a **sibling product** that cannot exist without Mezzanine.

Evidence:

- FAQ (`docs/frequently-asked-questions.rst`): "Can I use Cartridge without Mezzanine? **No.** … it is implemented as an advanced example of a Mezzanine content type, where each shop category is a page in Mezzanine's navigation tree."
- `createdb` (`mezzanine/core/management/commands/createdb.py`) has a first-class `create_shop` step gated on `"cartridge.shop" in INSTALLED_APPS`, loading `cartridge_required.json` / `cartridge_optional.json`.
- `collecttemplates` treats `cartridge` as a peer of `mezzanine`.
- Search docs mention `shop.Product` next to `pages.Page`.
- `mezzanine-project --alternate cartridge` overlays Cartridge's `project_template`.
- README feature list: "Ecommerce / Shopping cart module (Cartridge)" — linked off-repo, `http://cartridge.jupo.org/`.
- Accounts docs: purchases are a Cartridge feature, not Mezzanine.

Architectural reading: Cartridge is the existence proof that the *content-type + page processor + settings + templates* model can grow a large feature. It is also the existence proof that the model does **not** produce a plugin economy. Cartridge needed its own project, own docs, own fixtures, own scaffold overlay, and a hardcoded `create_shop` branch inside Mezzanine's `createdb`. That is vendor integration, not `pip install` + activate.

Drum (Hacker News clone) is the same pattern: listed next to Cartridge in `mezzanine_project.py`'s comment, own `project_template`, not a plugin.

When the core stalls, the sibling stalls. There is no plugin API version that would have let Cartridge survive a Mezzanine rewrite. They share models, admin, templates, and `Displayable`.

---

## 3. Why the plugin ecosystem died

Both code evidence and architecture. Not a mystery.

### 3.1 Code evidence

**The project told people not to build a module economy.**

`README.rst`: most functionality ships by default; the contrast class is "platforms that make extensive use of modules." The feature list is batteries (blog, forms, galleries, comments, accounts, TinyMCE, search, Bootstrap). A site owner who needs "CMS + blog + forms + gallery + comments" never reaches for a plugin. WordPress's economy exists *because* WordPress core is empty. Mezzanine core is full.

**The "marketplace" is a pull request against this repo.**

`docs/overview.rst` "Third-Party Plug-Ins": ~70 entries, added by emailing the mailing list or PRing the RST file. Also "add it to the Mezzanine Grid on djangopackages.com." There is no registry in code, no `entry_points`, no `mezzanine.plugins` namespace. Discovery is a documentation page that bitrots at the speed of GitHub.

CHANGELOG is a graveyard of those additions (mezzanine-polls, mezzanine-events, mezzanine-shortcodes, mezzanine-slideshows, mezzatheme, …). Almost all target Django 1.6–1.11 / Mezzanine 3.x–4.x. None can install themselves.

**There is no install surface.**

Grep for plugin install, marketplace, package verify, capability: nothing. Activation is:

1. `pip install mezzanine-whatever`
2. Add to `INSTALLED_APPS`
3. Maybe add urls
4. Maybe `register_setting` / `page_processors.py` / `admin.site.register`
5. `migrate`
6. Restart

A WordPress user does this in a UI, on a running site, without a shell. A Mezzanine user is a Django developer. Those are different markets. The second market does not produce 60,000 plugins.

**The extension APIs are upgrade-hostile.**

- `deepcopy(PageAdmin.fieldsets)` — private structure as public API.
- `EXTRA_MODEL_FIELDS` — "will almost certainly require some manual intervention."
- Single-level `Page` subclassing — "currently not supported" for further levels.
- `page_processors` `insert(0)` — last importer wins, no conflict resolver.
- `HOST_THEMES` themes own `base.html` — every Mezzanine template change is a theme break.
- `grappelli_safe` / `filebrowser_safe` are **forks pinned in `setup.cfg`**. Third-party admin skins must target the fork, not upstream Grappelli. `PACKAGE_NAME_*` settings exist because "they may change in the future." They did not become a stable driver API; they became a couple of string constants.

**Signals were never grown.**

Four custom send sites in the whole tree. A plugin author cannot hook "page about to render" or "menu items" without replacing middleware or a template tag. The alternative — fork the template — is what people did, and forks do not compose.

**Django version drag killed the long tail.**

`docs/overview.rst` still advertises Python 3.7–3.10 / Django 2.2–4.0. `setup.cfg` has been stretched to Django `<6` and Python 3.14 classifiers, but the *documented* world a plugin author reads is years behind. Third-party apps compiled against Mezzanine 4 + Django 1.11 never got a migration path because there was no versioned plugin API to migrate *to*. They just stopped importing.

**Optional-app magic hides breakage.**

`OPTIONAL_APPS` silently skips `ImportError`. A site can "have" filebrowser in the list and not have filebrowser. Fine for compressor. Fatal as a plugin mechanism: install success is not observable.

**`mezzanine.boot` load-order hack.**

An entire app exists to run first and patch `admin.site`. Plugins that also need to run first enter a knife-fight over `INSTALLED_APPS[0]`. WordPress solved this (badly) with priority integers. Mezzanine did not solve it.

### 3.2 Architectural reasons

1. **Audience mismatch.** WordPress plugins are written for site owners. Mezzanine extensions are written for people who are comfortable with `INSTALLED_APPS`, migrations, and `deepcopy`. The second group is two orders of magnitude smaller and would rather write the 80 lines themselves than depend on `mezzanine-events==0.4.2`.

2. **Django apps are not plugins.** An app is a Python package with models. It owns migrations, import time, and the process. You cannot safely enable it without a deploy. You cannot disable it without a reverse migration. You cannot run two versions. You cannot sandbox it. This is a *composition* model, not an *install* model.

3. **Batteries included cannibalize demand.** Blog, forms, galleries, comments, ratings, keywords, accounts, search, TinyMCE, multi-site, inline editing — the first ten WordPress plugins a beginner installs are already in the tree. What remains is vertical (events, recipes, podcasts, FIT files). Vertical apps do not sustain a marketplace; they sustain a GitHub search.

4. **No stable public API boundary.** The documented extension points leak internals (`fieldsets` tuples, `content_model` string, `Page.content_model` attribute access, TinyMCE JS paths, Grappelli template names). Without a versioned surface, every Mezzanine minor is a potential plugin break. Authors stop publishing.

5. **Multi-table inheritance does not compose.** Two plugins that both want to be "the" `Page` subclass for a URL cannot share a row. One page, one `content_model`. WordPress pages can run twenty plugins at once against the same post. Mezzanine pages cannot. Processors can stack, but types cannot.

6. **Themes are code, not assets.** A WordPress theme can be a folder of PHP/CSS with a header comment. A Mezzanine theme is a Python package that may define models (see `docs/multi-tenancy.rst` `HomePage`). Installing a theme can require `migrate`. That is an app, wearing a costume.

7. **The one successful extension (Cartridge) escaped the plugin model.** When the extension got large, it became a separate distribution with a scaffold overlay and hooks *into Mezzanine's management commands*. That is the opposite of a plugin architecture: the core grew knowledge of the plugin.

8. **Community gravity left.** Wagtail offered a better admin and a clearer page-model story. Django CMS offered apphooks and a plugin-in-placeholder model (closer to WordPress, still tiny). The remaining Mezzanine audience was "people who like this admin and this tree," not "people who want an ecosystem."

9. **Python packaging culture.** PyPI + semver + yanked releases + wheels is hostile to "click install on production." WordPress's `wp-content/plugins` is a writable directory on the server. Mezzanine's install path is a virtualenv owned by a deploy user. Different physics.

---

## 4. WordPress plugin model vs Django apps — honest comparison

| Dimension | WordPress | Mezzanine / Django apps |
|---|---|---|
| **Unit of extension** | Plugin directory + header comment; theme directory | Python package on `INSTALLED_APPS` |
| **Install** | Admin UI, zip upload, 1-click; mutates running site | `pip`, edit settings, `migrate`, restart |
| **Who installs** | Site owner | Developer / ops |
| **Hook style** | `add_action` / `add_filter` — global, string-named, priority int, anyone can clobber `the_content` | Decorator registries (`processor_for`, `register_setting`) + inheritance + template names. Almost no filters |
| **Composition** | 20 plugins on one post; last-registered-wins; "plugin hell" is real | One `content_model` per page; processors stack; apps compose at import time |
| **Isolation** | None. Full PHP, full `$wpdb`, full admin XSS | None. Full Python, full ORM, full admin XSS |
| **API stability** | Implicit social contract + "we'll break you in 5.0"; huge surface (`wp-includes`) | Undocumented internals (`fieldsets`, boot order); smaller surface, still unstable |
| **Data model** | `wp_posts` + `wp_postmeta` soup; plugins add tables or meta keys | Real models, migrations, multi-table inheritance |
| **Themes** | PHP templates + `style.css` header; customizer; now `theme.json` | Django templates + optional models; `HOST_THEMES`; no schema |
| **Admin UI for plugins** | First-class. Activate / deactivate / update / delete | None |
| **Security review** | Directory review is theater; supply chain is a dumpster fire | PyPI is also a dumpster fire, but fewer civilians click "install" |
| **Scale** | ~60k plugins because the core is a runtime and the users are civilians | ~70 listed apps because the core is a framework and the users are developers |
| **Failure mode** | White screen of death; plugin conflicts; malware admin users | `ImproperlyConfigured` at boot; migration fight; silent `ImportError` in `OPTIONAL_APPS` |

**What WordPress got right (and Mezzanine should steal the *shape* of, not the implementation):**

- A named, versioned hook *surface* people can document.
- An install/activate lifecycle.
- Themes as a product, with a contract (`theme.json`, template hierarchy).
- A directory with search, ratings, and (aspirational) review.

**What WordPress got wrong (and Mezzanine must not copy):**

- Global mutable hooks with string names. Untyped. Unauditable. `remove_action` wars.
- Plugins run as the application. Any plugin can create an admin user, inject JS into `/wp-admin`, or alter SQL.
- Site-owner install on the production filesystem.
- Core-as-empty-runtime, which *forces* a plugin economy and then drowns in it.

**What Django apps got right:**

- Models are real. Migrations are real. Conflicts are visible.
- Composition is explicit (`INSTALLED_APPS` order).
- The unit of trust is a deploy, not a zip upload.
- You can read the code; it is not a 4,000-filter soup.

**What Django apps got wrong for a CMS marketplace:**

- No capability declaration. An app can do anything.
- No sandbox. Same process, same credentials.
- No UI. The "app store" is `requirements.txt`.
- No theme contract. Template overrides are a fork.

Mezzanine sits in the Django-app world and borrowed *one* WordPress feeling (the admin tree, the "just works" batteries). It never borrowed the plugin runtime, and that was correct.

---

## 5. What a modern plugin system would actually need

If this council decided to build an ecosystem anyway, the minimum viable *safe* system is not `add_action`. It is a product.

### 5.1 Capability sandbox

Every package declares what it is allowed to do. Examples of capabilities Mezzanine already *implicitly* has, which should become explicit:

| Capability | Today's implicit form | Sandbox meaning |
|---|---|---|
| `content_type` | Subclass `Page` / `Displayable` | May register a type; may not patch existing types' tables |
| `page_processor` | `@processor_for` | May add context or return a response for listed types/slugs |
| `settings` | `defaults.py` | May register namespaced settings (`myapp.*` only) |
| `templates` | app `templates/` | May override *its own* namespace; may not replace `admin/` unless `admin_ui` |
| `admin_ui` | `admin.py` | May register ModelAdmins for *its* models |
| `richtext_filter` | `RICHTEXT_FILTERS` append | Pure function, `str → str`, no ORM |
| `search_source` | `search_fields` | Read-only contribution to search |
| `generic_field` | `CommentsField` et al. | Opt-in on the site owner's models, not injected |
| `menu_item` | `ADMIN_MENU_ORDER` append | Add a nav entry, not reorder core |
| `theme` | `HOST_THEMES` package | Templates + static + `theme.json` only. No models. |

A package that asks for `admin_ui` + `page_processor` is reviewed differently from one that asks for `theme`. A package that asks for "full Python" is not a plugin; it is a vendor app and should go through the Cartridge door.

### 5.2 Signed packages

- PyPI is not enough. The CMS needs its own index or a signed overlay: `mezzanine-plugin` dist-info with an Ed25519 signature over the wheel + capability manifest.
- Install only from that index, or from a pinned hash in the project (lockfile).
- Revocation list for compromised packages.
- No zip-upload-to-production. Ever. The install target is a **build**, not the running worker.

### 5.3 Versioned APIs

Publish `mezzanine.plugins.v1` as a **small** Python package the core promises not to break:

```text
mezzanine.plugins.v1
  register_content_type(...)
  register_processor(...)
  register_setting(...)      # namespaced
  register_richtext_filter(...)
  register_search_source(...)
  register_admin_widget(...)
  register_theme(...)
```

Internals (`fieldsets` tuples, `LazyAdminSite._deferred`, `boot.add_extra_model_fields`) stay private. `EXTRA_MODEL_FIELDS` is deprecated, not blessed. Cartridge-style siblings depend on `v1` plus explicit "vendor" status.

Semver the capability surface independently of the CMS release when possible. A plugin built against `v1.4` must run on `v1.9`.

### 5.4 Admin UI for install — carefully

A catalog UI that:

- lists *reviewed* packages and their capabilities;
- writes a proposed change to `requirements` / a plugin lockfile;
- kicks a **CI/deploy** ("apply on next release"), not `pip install` inside gunicorn;
- shows "this plugin needs `content_type` + `migrate`; downtime window: yes."

What it must not do: mutate `INSTALLED_APPS` at runtime, run `migrate` from a web worker, or download a wheel into `site-packages` of a live process.

If that feels too heavy to be "WordPress-like," good. That feeling is the point.

### 5.5 WASM or isolated Python?

Honest options:

| Isolation | Verdict for Mezzanine |
|---|---|
| **None (today)** | Unacceptable for third-party admin code |
| **Separate process / microservice** | Right for heavy things (video transcode, search). Wrong for `page_processor` latency |
| **Restricted Python (RestrictedPython, seccomp, gVisor per plugin)** | Expensive. Fights the ORM. The moment a plugin needs a model, you are back to trusting it |
| **WASM (extism / wasmtime) for filters and theme helpers** | Right for `richtext_filter`, template functions, validators. Typed I/O. No ORM. Cannot XSS if it cannot emit raw admin HTML |
| **Iframe + CSP for admin UI extensions** | Right for dashboards/widgets. Plugin JS never shares the admin origin |

**Recommendation:** do not run untrusted Python in-process. Split the world:

- **Trusted vendor apps** (Cartridge-class): normal Django apps, reviewed, signed, full process. Few of these.
- **Untrusted plugins**: WASM (pure transforms) + iframe admin widgets + declarative content types described in a manifest, *materialized by the core* (the core creates the table from a schema, the plugin does not ship models.py).

Shipping models.py is the original sin. A plugin that brings a `models.py` is an app. Treat it as one.

### 5.6 Theme JSON

Replace "theme = Django app" with a contract:

```json
{
  "name": "harbor",
  "engine": "mezzanine.themes.v1",
  "templates": { "page": "page.html", "blog_post": "post.html" },
  "blocks": ["title", "meta", "nav", "main", "aside", "footer"],
  "tokens": { "color.bg": "#0b1020", "font.body": "Source Serif" },
  "menus": [1, 3],
  "capabilities": ["theme"]
}
```

Core provides the HTML landmarks. Theme provides CSS tokens + a few templates that fill named blocks. **No models in a theme.** If you need a `HomePage` type, that is a `content_type` package, not a theme. `HOST_THEMES` stays as host → theme-id mapping, but the loader reads the JSON, not an importable module with side effects.

`collecttemplates` becomes "vendor a starter theme," not "fork the entire CMS template tree."

---

## 6. Revolutionary: typed capabilities, not PHP hooks

The mistake every "let's be WordPress" revival makes is to add `do_action('mezzanine_page_render')`. That produces an untyped event bus, plugin order wars, and XSS. Mezzanine should do the opposite.

### 6.1 Plugins as typed capabilities

A plugin is a **value**, not a process:

```text
PluginManifest {
  id:           "events.calendar"
  api:          "v1"
  capabilities: [ContentType("Event", fields=[...]),
                 Processor("Event", fn_wasm=...),
                 Setting("events.per_page", int, default=10),
                 Templates("events/*")]
  signature:    ...
}
```

The core *interprets* the manifest. It creates the content type. It mounts the processor in a WASM runtime with `(request_ctx, page_dto) -> {context} | Redirect`. It registers the setting under the plugin's namespace. It loads templates from a sealed directory.

The plugin never imports `django.contrib.admin`. It never sees `settings.SECRET_KEY`. It never gets a cursor.

That is the revolution: **the CMS remains the only process that can touch the database and the admin DOM.** Plugins propose; the core disposes.

### 6.2 Marketplace with security review

- Human review of capability requests. `theme` is rubber-stamped. `content_type` gets a schema review. `admin_ui` (if ever allowed for trusted vendors) gets a full audit.
- Automated checks: no `eval`, no `subprocess`, no undeclared network, WASM imports allowlist, template CSP (`{% autoescape %}`, no `|safe` on plugin-provided strings).
- SBOMs and signed provenance (Sigstore).
- Forced 2FA + attested builds for publishers.
- A kill switch that disables a plugin id cluster-wide by manifest id, without waiting for PyPI yank.

Review does not scale to 60k. It scales to 50. That is the correct size.

### 6.3 Apps that cannot XSS the admin

Admin HTML is the crown jewels. Rules:

- Plugin template packs for the *public* site are escaped by default; `|safe` is a capability (`unsafe_html`) that requires review.
- Admin extensions, if any, render in a sandboxed iframe with a `postMessage` schema (`v1.admin_widget`). No shared cookies beyond a scoped token. No access to TinyMCE's DOM.
- `RICHTEXT_FILTERS` contributed by plugins run in WASM and return text; the core bleaches again at `RICHTEXT_FILTER_LEVEL`.
- `DASHBOARD_TAGS` stops executing arbitrary inclusion tags from settings. Widgets are registered typed objects.

Today a hostile `defaults.py` or a hostile dashboard tag runs as the CMS user. That is WordPress. Kill it.

### 6.4 Keep the Cartridge door

Some things (a shop, a full LMS) are applications. They should remain trusted Django apps with a documented vendor contract: `mezzanine-project --alternate`, `createdb` hooks replaced by a **registration** (`register_vendor_app(...)`) instead of hardcoded `["cartridge.shop"]` lists. Two or three of these in the world is a healthy ecosystem. Two or three hundred is a support nightmare.

---

## 7. Keep batteries included — do not become plugin hell

This is the non-negotiable.

Mezzanine's comparative advantage *is* the integrated default: tree + blog + forms + gallery + comments + search + a single admin. The moment those become plugins, you inherit WordPress's onboarding ("which form plugin? which SEO plugin? they conflict") and lose the reason to pick this CMS over Wagtail + a pile of packages.

**Rules of engagement:**

1. **Core stays whole.** Pages, rich text, blog, forms, galleries, comments, ratings, keywords, search, accounts, settings, inline editing — remain first-party. Improve them. Do not extract them to prove modularity.
2. **No plugin is required to launch a site.** `mezzanine-project` + `createdb` still produces a finished CMS.
3. **Plugins may not replace core types.** You may add `Event`. You may not shadow `RichTextPage`.
4. **`OPTIONAL_APPS` is not a plugin system.** Keep it for true optionals (compressor, debug_toolbar). Do not grow it.
5. **Deprecate `EXTRA_MODEL_FIELDS`** for third parties. It is a clever hack that eats migrations. First-party may keep it for one release cycle; then sidecar models or real fields in core.
6. **Deprecate `deepcopy(fieldsets)` as the documented API.** Give `ContentTypedAdmin` an explicit `extra_fieldsets` / `extra_inlines` hook in `v1` so upgrades stop breaking.
7. **Themes cannot ship models.** The multi-tenancy doc that teaches `HomePage` inside `example_theme` is the original sin of theme-as-app. Split it.
8. **One marketplace, curated.** Fifty packages, reviewed, signed. If it cannot be reviewed, it is not in the catalog. Developers can still `pip install` anything — that is Django — but the *product* does not bless it.
9. **Measure success by time-to-first-publish, not plugin count.** WordPress counts plugins because core is empty. Mezzanine should count *sites that never needed one*.

---

## Capability map (today vs. should-be)

```
TODAY (implicit, in-process, unversioned)
────────────────────────────────────────
  Page subclass ────────── content types
  @processor_for ───────── request hooks
  defaults.py ──────────── settings
  templates/ + HOST_THEMES  themes (are apps)
  admin unregister ─────── admin UI
  EXTRA_MODEL_FIELDS ───── schema mutation
  OPTIONAL_APPS ────────── maybe-install
  Cartridge/Drum overlay ─ vendor siblings
  RST plugin list ──────── "marketplace"

SHOULD-BE (explicit, versioned, split-trust)
────────────────────────────────────────────
  mezzanine.plugins.v1 ─── typed capabilities
  WASM filters/processors  untrusted compute
  iframe admin widgets ─── untrusted UI
  theme.json ───────────── untrusted presentation
  signed catalog ───────── reviewed ≤50
  vendor apps ──────────── trusted, few, Cartridge-class
  core batteries ───────── not plugins
```

---

## File index (cited)

| Path | Why it matters |
|---|---|
| `README.rst` | Batteries-included philosophy; "Free Themes Marketplace" link; Cartridge as a feature |
| `docs/content-architecture.rst` | Official extension story: subclass `Page`, page processors, one-level inheritance, third-party app URL overlay |
| `docs/model-customization.rst` | `EXTRA_MODEL_FIELDS` + migration caveats + `deepcopy` admin |
| `docs/packages.rst` | Package map; `page_processors` and `conf` as first-class |
| `docs/admin-customization.rst` | `ADMIN_MENU_ORDER`, `DASHBOARD_TAGS`, richtext widget/filters |
| `docs/configuration.rst` | `register_setting` contract; AppConfig footgun |
| `docs/overview.rst` | Static third-party plugin list (PR to be listed) |
| `docs/frequently-asked-questions.rst` | Cartridge cannot run without Mezzanine |
| `docs/multi-tenancy.rst` | `HOST_THEMES`; themes as apps that may define models |
| `docs/search-engine.rst` | Search as inherit-`Displayable`; Cartridge `Product` example |
| `docs/utilities.rst` | Generic fields as the mixin capability |
| `docs/user-accounts.rst` | Profile model via setting |
| `mezzanine/pages/page_processors.py` | The hook: decorator + autodiscover + global dict |
| `mezzanine/pages/middleware.py` | Processor runtime; `HttpResponse` short-circuit |
| `mezzanine/pages/views.py` | Template candidate list (the "theme hierarchy") |
| `mezzanine/pages/admin.py` | Content-type discovery in the tree; `ADD_PAGE_ORDER` |
| `mezzanine/pages/models.py` | `Page` + `ContentTyped`; one `content_model` |
| `mezzanine/pages/defaults.py` | `ADD_PAGE_ORDER`, `PAGE_MENU_TEMPLATES` |
| `mezzanine/core/models.py` | `ContentTyped.get_content_models()` |
| `mezzanine/core/defaults.py` | `EXTRA_MODEL_FIELDS`, `HOST_THEMES`, `ADMIN_*`, `DASHBOARD_TAGS` |
| `mezzanine/core/admin.py` | `ContentTypedAdmin` auto-fieldset insertion |
| `mezzanine/core/management/commands/createdb.py` | Hardcoded Cartridge `create_shop` |
| `mezzanine/core/management/commands/collecttemplates.py` | mezzanine+cartridge as the template universe |
| `mezzanine/conf/__init__.py` | Settings registry + `defaults.py` autoload |
| `mezzanine/conf/admin.py` | Single-form editable settings |
| `mezzanine/boot/__init__.py` | Field injection; patches `admin.site` |
| `mezzanine/boot/lazy_admin.py` | Deferred register; `ADMIN_REMOVAL`; filebrowser URLs |
| `mezzanine/utils/conf.py` | `OPTIONAL_APPS`, boot-first, implicit blog→comments |
| `mezzanine/utils/importing.py` | `import_dotted_path`, `get_app_name_list` |
| `mezzanine/utils/sites.py` | `host_theme_path()` — theme = importable package |
| `mezzanine/template/loaders/host_themes.py` | Theme loader |
| `mezzanine/template/__init__.py` | Tag helpers; `as_tag` deprecated |
| `mezzanine/forms/page_processors.py` | Canonical processor + only custom signals |
| `mezzanine/forms/signals.py` | `form_valid` / `form_invalid` |
| `mezzanine/generic/fields.py` | Comments/keywords/ratings capability fields |
| `mezzanine/accounts/models.py` | Profile `post_save` |
| `mezzanine/bin/management/commands/mezzanine_project.py` | `--alternate` for Cartridge/Drum |
| `mezzanine/project_template/project_name/settings.py` | The install surface a developer actually edits |
| `mezzanine/urls.py` | Conditional includes by `INSTALLED_APPS` |
| `setup.cfg` | `filebrowser_safe` / `grappelli_safe` hard deps; no plugin extras |
| `CHANGELOG` | Marketplace mention (2013); third-party list as the ecosystem |

---

## EXECUTIVE VERDICT (repeat, short)

Mezzanine extends like a **Django project**, not like a **CMS runtime**. The extension points are real and, for a developer, pleasant: content types, page processors, a settings registry, template hierarchy, admin registries, generic fields. They are not a plugin economy, and the code never grew the machinery (manifest, sandbox, versioned API, install UI, theme contract) that an economy requires.

Cartridge proves the ceiling of the current model: a sibling application hard-wired into `createdb` and the scaffold, not a plugin.

A WordPress-scale store is unreachable and undesirable. Python has no cheap sandbox, the audience is developers, and the product's soul is batteries included. The revolutionary path is **typed capabilities + signed reviewed catalog + WASM/iframe isolation + theme JSON**, with core kept whole. Fifty apps. Zero plugin hell.

If this council wants WordPress, it should fork WordPress. If it wants Mezzanine, it should version `mezzanine.plugins.v1` and refuse to let plugins become the product.
