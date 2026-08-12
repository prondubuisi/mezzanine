# 03 — Frontend, Templates, Theming

**Auditor:** General FRONTEND (Byzantine council, independent, from code)
**Repo:** `/Users/prondubuisi/gitrepos/dev/mezzanine`
**Question:** Can Mezzanine compete with WordPress block themes / Full Site Editing?
**Answer, up front:** No. Not as shipped. The theming model is a competent 2013 Django site, frozen on Bootstrap 3.2 / TinyMCE 4.1 / Glyphicons / GIF spinners. WordPress shipped `theme.json`, block templates, and a visual site editor years ago. Mezzanine shipped "copy `base.html` into your project and edit the HTML." That was a feature in 2012. It is a liability in 2026.

This is salvageable as a **server-rendered theme SDK** — Django templates plus design tokens plus islands — but only if the vendored 2013–2015 asset pile is treated as unsalvageable and the "theme = Django app that shadows templates" contract is formalized instead of implied.

---

## 0. What is actually on disk

### Static tree (`mezzanine/core/static`)

```
mezzanine/core/static/
  admin/img/admin/          arrow-up.gif, arrow-down.gif, icon_deletelink.gif
  admin/js/collapse.js
  css/
    bootstrap.css           Bootstrap v3.2.0 (2014)
    bootstrap-theme.css     Bootstrap v3.2.0
    bootstrap-rtl.css       bootstrap-rtl 3.3.2-rc1 (2015)
    mezzanine.css           project chrome, ~490 lines, no custom properties
  fonts/
    glyphicons-halflings-regular.{eot,svg,ttf,woff}   NO woff2
  img/favicon.ico
  js/
    bootstrap.js            Bootstrap v3.2.0
    bootstrap-extras.js     hover-intent dropdowns + touch open
    html5shiv.js            HTML5 Shiv 3.7.3 (IE < 9)
    respond.min.js          Respond.js v1.3.0 (IE8 media-query polyfill)
  mezzanine/
    chosen/                 Chosen 0.9.12 (Harvest, 2011–2013)
    css/admin/              dashboard, global, rtl, tabbed_translation_fields
    css/editable.css
    css/smoothness/         jQuery UI CSS Framework 1.8.24 (2012)
    css/tinymce.css
    img/loadingAnimation.gif
    js/
      jquery-3.4.1.js
      jquery-ui-1.12.1.js
      jquery.form.js        3.51.0-2014.06.20
      jquery.tools.overlay.js          @VERSION (unreleased Flowplayer Tools)
      jquery.tools.toolbox.expose.js   @VERSION
      editable.js
      tinymce_setup.js
      admin/*.js
    tinymce/                TinyMCE 4.1.10 (2015-05-05)
      themes/modern/
      skins/lightgray/      includes skin.ie7.min.css
      plugins/media/moxieplayer.swf    FLASH PLAYER
      plugins/emoticons/img/*.gif      16 smiley GIFs
      plugins/example/                 leftover demo plugin
  robots.txt
  test/                     gallery.zip, image.jpg
```

Other apps add more of the same vintage:

| App | Extra static |
|---|---|
| `galleries` | Magnific Popup **v0.9.6 (2013-09-29)** + `admin/gallery.css` |
| `forms` | `admin/form.css`, `form_entries.css`, `form_entries.js` |
| `pages` | `page_tree.css`, `page_tree.js`, **nestedSortable v2.1a (2016-02-04)** |
| `conf` | `admin/settings.css`, `tabbed_translatable_settings.js` |

`project_template/` ships **zero** templates and **zero** theme static. A new project inherits everything from the installed package.

### Template inventory (public + admin)

| App | Public templates | Admin / email |
|---|---|---|
| `core` | `base.html`, `index.html`, `search_results.html`, `errors/{404,500}.html`, 10 includes | 7 admin, 2 email |
| `pages` | `pages/{page,richtextpage,index}.html`, 8 menus | 3 admin |
| `blog` | `blog/{blog_post_list,blog_post_detail}.html` + filter panel | 1 admin include |
| `galleries` | `pages/gallery.html` | — |
| `forms` | `pages/form.html` | 2 admin, 4 email |
| `accounts` | 6 account pages + 2 includes | 1 admin, 12 email |
| `generic` | comments / rating / disqus includes | 1 admin, 2 email |
| `twitter` | `twitter/tweets.html` | — |

There is no `theme.json`, no block catalog, no slot map, no style variation, no pattern library. The entire "theme" is Django template inheritance plus a Bootstrap 3 stylesheet.

---

## 1. Template inheritance and theming model

### The contract

Mezzanine's frontend is a **single-root Django template tree**. Everything extends `mezzanine/core/templates/base.html`. That file is the theme. It hard-codes:

- Bootstrap 3 navbar / 2-7-3 column grid (`col-md-2` / `col-md-7` / `col-md-3`)
- `{% compress css %}` / `{% compress js %}` wrappers (no-ops unless django-compressor is installed — `mezzanine/core/templatetags/mezzanine_tags.py`)
- jQuery + Bootstrap JS loaded in `<head>` (not deferred, not modular)
- IE conditional comments for html5shiv + respond.js
- `{% page_menu %}` calls for dropdown, breadcrumb, tree, footer
- Inline editing hook via `{% include "includes/footer_scripts.html" %}`
- A "Theme by Bootstrap" footer credit
- Cartridge shop CSS if that package happens to be installed

Child pages fill named blocks: `meta_title`, `meta_keywords`, `meta_description`, `extra_css`, `extra_js`, `extra_head`, `navbar_title`, `navbar_search_form`, `navbar_dropdown_menu`, `title`, `breadcrumb_menu`, `left_panel`, `main`, `right_panel`, `footer_js`.

```
base.html
├── index.html                          (static congratulations page)
├── search_results.html
├── errors/404.html, 500.html
├── accounts/account_form.html          → login / signup / password / profile
├── blog/blog_post_list.html
│   └── blog/blog_post_detail.html      (extends the LIST, not page.html)
└── pages/page.html                     (SEO + {% editable page.title %})
    ├── pages/richtextpage.html
    ├── pages/gallery.html
    └── pages/form.html
```

This is classic Django and it is genuinely good at what Django is good at: a developer copies a template, changes a block, ships. It is not a theming system. There is no theme API, no declared block contract, no style tokens, no way for a non-developer to change a color.

### How you "install a theme"

Documented in `docs/frequently-asked-questions.rst` ("How do I create/install a theme?"):

1. Prior to Mezzanine 1.0 there *was* a theming feature. It was **removed** when Django staticfiles landed. The docs say the theming features "became redundant."
2. A theme is now "a standard Django app" with `templates/` and `static/`.
3. You **copy** HTML/CSS/JS out of Mezzanine into the app.
4. You put the app **first** in `INSTALLED_APPS` so its templates win.
5. You optionally publish it on PyPI and email the mailing list.

That is the entire first-party story. There is no `mezzanine-theme` package metadata, no theme manifest, no screenshot convention, no preview URL, no customizer, no parent-theme declaration beyond "list the base theme first."

`collecttemplates` (`mezzanine/core/management/commands/collecttemplates.py`) is the official on-ramp: walk Mezzanine/Cartridge apps, copy templates into `TEMPLATES[0]["DIRS"][0]`, prompt on overwrite. After that, those copies are **pinned** — upgrades to Mezzanine templates never reach the site. The FAQ warns about this and then offers no better alternative.

### Page / blog template resolution (the one sophisticated piece)

This is the part that still looks like a CMS.

`mezzanine.pages.views.page` builds a template candidate list, most-specific first:

1. `Page.get_template_name()` if a subclass implements it
2. `pages/<slug>.html` (homepage slug → `pages/index.html`)
3. `pages/<slug>/<content_model>.html`
4. `pages/<parent-slug>/<content_model>.html` for every ascendant
5. `pages/<content_model>.html` (e.g. `pages/richtextpage.html`, `pages/gallery.html`)
6. `pages/page.html`

Blog does a smaller version of the same thing (`mezzanine/blog/views.py`):

- list: `blog/blog_post_list_<category-slug>.html` or `blog/blog_post_list_<username>.html`, then `blog/blog_post_list.html`
- detail: `blog/blog_post_detail_<slug>.html`, then `blog/blog_post_detail.html`

A developer can restyle one page, one section, or one content type without a visual editor. WordPress block themes do this with `templates/` + `parts/` + `patterns/` and a GUI. Mezzanine does it with filesystem convention. Fine for engineers. Invisible to authors.

### Menus are templates, not objects

`PAGE_MENU_TEMPLATES` (`mezzanine/pages/defaults.py`) is a tuple of `(id, label, path)`:

```
(1, "Top navigation bar", "pages/menus/dropdown.html")
(2, "Left-hand tree",     "pages/menus/tree.html")
(3, "Footer",             "pages/menus/footer.html")
```

Editors pick which menus a page appears in. The templates themselves are Bootstrap 3 markup (`nav navbar-nav`, `dropdown-submenu`, `nav-list`, `list-unstyled`). `primary.html` still uses Bootstrap **2** classes (`nav pull-right`, `divider-vertical`) and is not in the default menu tuple — leftover. `mobile.html` is an orphan of the deleted device-detection system; nothing in `base.html` includes it.

### Host themes (multi-tenant skins)

`mezzanine.template.loaders.host_themes.Loader` + `HOST_THEMES` setting + `mezzanine.utils.sites.host_theme_path()`:

- Map `hostname → python.package`
- Loader returns `[package/templates]` for the matching host
- Sits first in the project's `TEMPLATES["OPTIONS"]["loaders"]`

This is real multi-tenant theming and it is better than WordPress's "one theme per site" default. It is also just another Django template directory. No per-host CSS tokens, no per-host component registry.

`TemplateForHostMiddleware` and `TemplateForDeviceMiddleware` remain in `mezzanine/core/middleware.py` as deprecated stubs that only `warnings.warn`. Device detection was **removed in 4.3** (`CHANGELOG`: "Remove all device-detection features"). Cache keys still comment that they "used to indicate the device type" (`mezzanine/utils/cache.py`).

### Template tag library

`mezzanine/template/__init__.py` extends `django.template.Library` with `as_tag` (deprecated; warns anyone outside the `mezzanine` package), `render_tag`, `to_end_tag`. `mezzanine/template/loader_tags.py` is an empty leftover: "TODO: Remove this file a couple releases after Mezzanine 5."

Useful public tags: `{% editable %}`, `{% editable_loader %}`, `{% nevercache %}`, `{% compress %}`, `{% ifinstalled %}`, `{% page_menu %}`, `{% pagination_for %}`, `{% thumbnail %}`, `{% richtext_filters %}`. These are the actual theme API. They are undocumented as such.

### Inline editing is the "block editor"

`{% editable page.title %}…{% endeditable %}` wraps a field, injects a hidden form + "Edit" link + yellow highlight. Staff get jQuery Tools overlay + expose + `jquery.form` ajaxSubmit + TinyMCE, then `location.reload()`. Loading state is `mezzanine/img/loadingAnimation.gif`. Toolbar HTML is stuffed into `window.__toolbar_html` as an escaped string.

This is field-level, not layout-level. You cannot add a block, reorder sections, or change the template from the front. You can edit the title string that is already on the page. Compared to Gutenberg / FSE this is a 2009 "click-to-edit" overlay.

Docs (`docs/inline-editing.rst`) still tell implementers to load **`jquery-1.8.3.min.js`**, a file that does not exist in the tree. The shipped file is `jquery-3.4.1.js`.

---

## 2. Asset versions (read from the files, not from marketing)

| Asset | Path | Version in file | Released | Current (2026) |
|---|---|---|---|---|
| Bootstrap CSS/JS/theme | `core/static/css/bootstrap*.css`, `js/bootstrap.js` | **3.2.0** | 2014-06 | 5.3.x |
| bootstrap-rtl | `css/bootstrap-rtl.css` | **3.3.2-rc1** | 2015-03 | n/a (BS5 has RTL) |
| normalize.css (bundled in BS) | `css/bootstrap.css` | **3.0.1** | 2014 | 8.x |
| Glyphicons Halflings | `fonts/glyphicons-halflings-regular.*` | BS3 set, **no woff2** | 2014 | abandoned |
| jQuery | `mezzanine/js/jquery-3.4.1.js` (`JQUERY_FILENAME` default) | **3.4.1** | 2019-05 | 3.7.x |
| jQuery UI JS | `mezzanine/js/jquery-ui-1.12.1.js` (`JQUERY_UI_FILENAME`) | **1.12.1** (2016-09-14) | 2016 | 1.13.x / dead |
| jQuery UI CSS | `mezzanine/css/smoothness/jquery-ui.css` | **1.8.24** | 2012 | **MISMATCHED** with the JS |
| jQuery Form | `mezzanine/js/jquery.form.js` | **3.51.0-2014.06.20** | 2014 | unmaintained |
| jQuery Tools Overlay / Expose | `jquery.tools.overlay.js`, `jquery.tools.toolbox.expose.js` | **`@VERSION` / `@DATE`** (never substituted) | ~2010–2013, Flowplayer abandoned | dead |
| Chosen | `chosen/chosen-0.9.12.jquery.js` | **0.9.12** | ~2013 | 1.8.x (also stale) |
| TinyMCE | `tinymce/tinymce.min.js` first line | **4.1.10 (2015-05-05)** | 2015 | 7.x |
| TinyMCE theme | `tinymce/themes/modern/` | 4.x "modern" | 2014–15 | "silver" / "oxide" |
| TinyMCE jQuery plugin | `tinymce/jquery.tinymce.min.js` | 4.x | 2015 | dropped upstream |
| Magnific Popup | `galleries/.../magnific-popup.js` | **0.9.6 (2013-09-29)** | 2013 | 1.1.0 (2016) then dead |
| nestedSortable | `pages/.../jquery.mjs.nestedSortable.js` | **2.1a / 2016-02-04** | 2016 | unmaintained |
| HTML5 Shiv | `js/html5shiv.js` | **3.7.3** | 2015 | irrelevant |
| Respond.js | `js/respond.min.js` | **1.3.0** | 2013 | irrelevant |
| Google Analytics | `includes/footer_scripts.html` | **analytics.js** (`ga('create'…)`) | UA, sunset 2023 | gtag / GA4 |
| Flash | `tinymce/plugins/media/moxieplayer.swf` | Moxieplayer | ~2013 | browsers refuse it |

Settings that pin versions (`mezzanine/core/defaults.py`):

- `JQUERY_FILENAME = "jquery-3.4.1.js"`
- `JQUERY_UI_FILENAME = "jquery-ui-1.12.1.js"`
- `TINYMCE_SETUP_JS = "mezzanine/js/tinymce_setup.js"`
- `RICHTEXT_WIDGET_CLASS = "mezzanine.core.forms.TinyMceWidget"`

`CHANGELOG` shows the last Bootstrap bump was **3.1.1 → 3.2.0** (Nik Nyby). jQuery in the changelog still talks about 1.7 / 1.8.3; 3.4.1 landed later without a corresponding frontend refresh. TinyMCE was upgraded to 4, then **rolled back 4.2 → 4.1** "due to image insertion conflict," and stuck there.

`docs/admin-customization.rst` still documents loading `filebrowser/js/jquery-ui-1.8.24.min.js` for the media library popup. The admin skin is grappelli-safe (a Grappelli fork), not Django's current admin.

### What `base.html` actually loads on every public page

```
css/bootstrap.css
css/mezzanine.css
css/bootstrap-theme.css
[+ css/bootstrap-rtl.css if LANGUAGE_BIDI]
[+ cartridge.css if cartridge.shop installed]
mezzanine/js/jquery-3.4.1.js
js/bootstrap.js
js/bootstrap-extras.js
<!--[if lt IE 9]> html5shiv.js + respond.min.js
includes/footer_scripts.html → editable_loader + Universal Analytics
```

There is no ES module, no import map, no Vite/webpack config, no `package.json` in the project template, no CSS custom properties, no source maps checked in (only comments pointing at missing `.map` files).

---

## 3. `mezzanine.mobile` — what is it

A tombstone.

```
mezzanine/mobile/__init__.py
    warnings.warn(
        "mezzanine.mobile has been deprecated. Please remove it from your "
        "INSTALLED_APPS.",
        FutureWarning,
    )

mezzanine/mobile/models.py
    # Required for INSTALLED_APPS.
```

No templates, no static, no views, no device detection. The mobile story used to be:

- `TemplateForDeviceMiddleware` injecting device-specific templates
- jQuery Mobile (CHANGELOG: "Update jquery to 1.7.2, jquery-mobile to 1.2.1")
- `pages/menus/mobile.html`

Device detection was deleted in 4.3. The middleware class remains as a warn-and-noop. `mobile.html` remains, unused by `base.html`. Responsive behavior is now entirely Bootstrap 3's grid plus four `@media` rules in `mezzanine.css`.

There is no PWA manifest, no service worker, no `theme-color`, no apple-touch-icon beyond a lone `favicon.ico`.

---

## 4. Accessibility, responsive, modern CSS

### Responsive

**Exists, circa 2014.** `viewport` meta is correct. Bootstrap 3.2 grid + navbar-collapse + `img-responsive` / `img-thumbnail`. `mezzanine.css` adds:

```
@media (min-width: 768px)  { dropdowns open on hover }
.tree { display: none }
@media (min-width: 992px)  { .tree { display: block } }
.navbar .container { width: 100% }
@media (min-width: 992px)  { width: 970px }
@media (min-width: 1200px) { width: 1170px }
```

The left tree menu is **display:none below 992px** with no substitute. Mobile users get the hamburger dropdown only. `visible-lg` hides the tagline on anything smaller than Bootstrap's `lg`. There is no container-query, no fluid type, no `clamp()`, no mobile-first custom layout.

`bootstrap-extras.js` implements a 250 ms hover-intent on `li.dropdown` and a one-finger touch handler that `preventDefault`s the first tap. That is the entire interaction layer.

### Accessibility

Token effort, not a system.

Present:

- `role="navigation"` on the navbar (redundant in 2026; should be `<nav>`)
- `role="search"` on the search form
- `sr-only` "Toggle Navigation" on the hamburger
- `aria-hidden="true"` on the alert close ×
- `lang="{{ LANGUAGE_CODE }}"` and `dir="rtl"` when `LANGUAGE_BIDI`
- form fields have `<label for="…">` via `includes/form_fields.html`

Missing / broken:

- Almost no `aria-*` anywhere else (grep across `*.html` finds **six** hits, three of which are the ones above)
- Featured images, gallery thumbs, blog thumbs have **no `alt`** (`blog_post_list.html`, `blog_post_detail.html`, `gallery.html`)
- Gallery links use obsolete `rel="#image-{{ id }}"` instead of a dialog / `aria-haspopup`
- Dropdown toggles use `class="dropdown-toggle disabled"` — the `disabled` class on an `<a href>` is a Bootstrap 3 hack that still leaves the link in the tab order and does not set `aria-expanded`
- Multi-level menus (`dropdown-submenu`) open on **CSS `:hover` only** — keyboard and touch users cannot reach nested items reliably
- Pagination prev/next are bare `←` / `→` with no accessible name
- Skip-to-content link: none
- Landmark structure: no `<main>`, no `<nav>` elements; a `<div class="col-md-7 middle">` wrapping `{% block main %}`
- Focus management on the inline-edit overlay: none (jQuery Tools)
- Color contrast: Bootstrap 3 defaults + `#aaa !important` tagline + yellow (`#fffcc3`) edit toolbar
- Motion / `prefers-reduced-motion`: none
- Chosen 0.9.12 replaces `<select>` with an inaccessible custom widget in admin

### Modern CSS

`mezzanine.css` is 490 lines of element/class selectors, hex colors, `float`, `display: table` footer columns, `!important` on the tagline, and vendor-prefixed `box-shadow` / `transition`. Zero CSS custom properties. Zero `flex` / `grid` in first-party CSS (Bootstrap 3's float grid does the layout). Zero `@layer`. Zero `color-mix`. The form field rules **re-copy Bootstrap 3 `.form-control`** because Django widgets cannot be given classes easily — the comment in the file admits this.

Admin `editable.css` is "littered with `!important` declarations" (its own comment) specifically because the edit chrome is injected into arbitrary layouts. That is the opposite of a design-token system.

Fonts: Glyphicons only, served as eot/svg/ttf/woff. No system font stack beyond Bootstrap's Helvetica Neue / Helvetica / Arial. No `font-display`. SVG font is an IE / old-iOS artifact.

---

## 5. Theme marketplace reality

README feature list, item 15:

> * `Free Themes` Marketplace

The link is `https://github.com/thecodinghouse/mezzanine-themes`.

That repository is **four Bootstrap 3 skins** (flat / nova / solid / moderna) living inside a whole Mezzanine *project*, not installable packages. You clone the project and uncomment one name in `INSTALLED_APPS`. 14 commits, no releases, 172 stars, last meaningful activity years ago. Preview images in the README are broken empty headings. Installation instructions assume Mezzanine's old project layout.

`docs/overview.rst` still advertises a second, paid marketplace:

> A handful of attractive Free Themes are available thanks to @abhinavsohani, while there is also a marketplace for buying and selling Premium Themes thanks to @joshcartme.

The premium URL is `http://mezzathe.me/` (MEZZaTHEME, announced on the Google Group in the mid-2010s). The current README **dropped the premium mention** and kept only the free GitHub repo. `mezzathe.me` is not a living storefront comparable to WordPress.org/themes (11,000+ themes) or ThemeForest. The third-party plugin list in `overview.rst` is a graveyard of GitHub repos (`mezzanine-foundation`, `mezzanine-business-theme`, `mezzanine-html5boilerplate`, `mezzanine-flexipage`, `django-widgy`, …) with no install counts, no compatibility matrix, and no first-party review.

FAQ invitation to "package your theme up and put it on PyPI and let us know via the mailing list" is not a marketplace. It is a 2011 open-source distribution hope.

**Reality:** there is no theme economy. There is one abandoned demo repo and a dead premium domain. WordPress's competitive moat here is not taste — it is liquidity. Mezzanine cannot "compete with block themes" while its official marketplace is a 14-commit GitHub project that still documents Bootstrap 3 class names.

---

## 6. What is unsalvageable

Treat these as landfill, not as upgrade targets:

1. **TinyMCE 4.1.10 + `themes/modern` + `skins/lightgray` + `skin.ie7.min.css` + `jquery.tinymce.min.js`.** Upstream is on 7.x, LGPL-2.1, with a different plugin API, no jQuery build, no IE7 skin. The tree also vendors `plugins/example`, `plugins/example_dependency`, 16 smiley GIFs, and **`moxieplayer.swf`**. You do not upgrade this in place. You replace the editor.

2. **jQuery Tools Overlay / Expose.** Unversioned (`@VERSION`), abandoned with Flowplayer, patched in-tree with a hand-rolled `jQuery.browser` shim so it would load on jQuery 1.9+. This is the inline-edit modal. It must die with the modal.

3. **Chosen 0.9.12.** Pre-accessible `<select>` replacement. Admin-only. Replace with native `<select>` + CSS or a maintained widget.

4. **Magnific Popup 0.9.6.** 2013 lightbox, jQuery plugin, last meaningful release 2016. Gallery should be a native `<dialog>` / CSS lightbox island.

5. **IE stack:** html5shiv 3.7.3, Respond 1.3.0, `<!--[if lt IE 9]>`, `<!--[if IE 7]>`, `skin.ie7.min.css`, eot/svg fonts, `jQuery.browser.msie`. Docs still claim "Internet Explorer and Edge < 79 are generally unsupported" — then ship polyfills for IE8 anyway.

6. **GIF era:** `loadingAnimation.gif`, TinyMCE `loader.gif` / `anchor.gif` / `object.gif` / `trans.gif`, 16 emoticon GIFs, Django-1.3 admin `arrow-up.gif` / `arrow-down.gif` / `icon_deletelink.gif` (the README in that folder says they were "removed in Django 1.4").

7. **Universal Analytics snippet** in `footer_scripts.html`. UA property IDs stopped collecting in July 2023. Dead code that still fires a network request if `GOOGLE_ANALYTICS_ID` is set.

8. **Bootstrap 3.2.0 + Glyphicons + `bootstrap-theme.css` + `pull-left` / `img-responsive` / `visible-lg` / `sr-only` / `nav-list`.** A 3 → 5 rewrite is not a theme upgrade; it is a class-name holocaust. Every first-party template is soaked in BS3.

9. **jQuery UI smoothness 1.8.24 CSS paired with 1.12.1 JS.** Already internally inconsistent. Used for admin datepickers / filebrowser dialogs (docs still say 1.8.24 JS).

10. **`mezzanine.mobile`, `TemplateForDeviceMiddleware`, `pages/menus/mobile.html`, `pages/menus/primary.html`.** Dead branches.

11. **Twitter widget** (`twitter/tweets.html`) protocol-strips `http:` from avatar URLs and talks to `http://twitter.com/...`. The `mezzanine.twitter` app is commented out of the project template for a reason.

12. **grappelli-safe admin skin + Chosen + nestedSortable** as the page-tree UX. It works. It looks like 2012 Django admin. Competing with WP's site editor while this is the authoring chrome is not a frontend problem you solve with a nicer `base.html`.

13. **Stale docs that name files that are not in the tree** (`jquery-1.8.3.min.js`, `jquery-ui-1.8.24.min.js`, "Free Themes Marketplace", `mezzathe.me`). The documentation is part of the frontend product and it lies.

What *is* salvageable underneath the landfill:

- Named template blocks and the page/blog template-resolution ladder
- `{% editable %}` *idea* (not the jQuery Tools implementation)
- `{% page_menu %}` + `PAGE_MENU_TEMPLATES` as a menu-placement API
- `{% thumbnail %}`, `{% nevercache %}`, `{% ifinstalled %}`
- `HOST_THEMES` loader
- `collecttemplates` as a migration aid
- Form-builder rendering (`includes/form_fields.html`) once widgets emit modern classes
- The fact that the whole public site is server-rendered HTML with no mandatory React

---

## 7. A modern theming model that actually beats WordPress

WordPress FSE's strengths: visual layout, `theme.json` tokens, patterns, a huge theme/plugin market. Its weaknesses: React lock-in (Gutenberg), block markup in the database, upgrade-fragile serialized HTML, poor default performance, a theme model that fights anyone who wants a real design system.

Mezzanine should not imitate Gutenberg. It should bet the opposite: **HTML is the source of truth, the server owns the tree, the editor paints tokens and islands.**

### 7.1 Design tokens first (`theme.css` + `theme.json` — but JSON is data, not a React schema)

First-party file every theme must ship:

```
mytheme/
  theme.toml          # name, parent, supports, screenshot, engines
  tokens.css          # :root { --mz-color-bg: …; --mz-font-body: …; --mz-space-2: … }
  tokens.dark.css     # optional [data-theme=dark] override
  templates/          # Django templates, same block names as core
  islands/            # JS/CSS per island, import-mapped
  preview/            # optional HTML fixtures for the visual editor
```

`tokens.css` is the public API. Core's `mezzanine.css` is rewritten to consume only tokens. A child theme overrides `:root` and is done — no Bootstrap rebuild, no copied `base.html` for a color change. This is what `theme.json` got right; the mistake is making JSON the only way to express it and tying it to a React editor.

Ship three first-party token sets (not four abandoned Bootstrap skins): `literal` (editorial serif), `plain` (system UI), `dense` (docs/app). Dark mode is a token sheet, not a theme.

### 7.2 A declared template contract (Theme SDK)

Publish `mezzanine.theme.blocks` — a documented, versioned list of blocks and required includes. Core templates stop being "copy me" and become **parent templates you `{% extends %}`**:

```
{% extends "mezzanine/shell.html" %}
{% block shell_nav %}…{% endblock %}
{% block shell_main %}…{% endblock %}
```

Add **slots** as well as blocks. Blocks are compile-time (Django). Slots are runtime, filled by page processors / a `ThemeSlot` model (`nav.cta`, `home.hero`, `article.byline`, `footer.col-1`). Authors fill slots in admin; designers style whatever lands. This is FeinCMS/Widgy's good idea without Widgy's widget soup, and it is how you beat WP blocks: the HTML structure stays in git, the *content* of named holes stays in the DB.

SDK Python API (sketch, not in repo today):

```python
# mytheme/apps.py
from mezzanine.theme import Theme
class MyTheme(Theme):
    name = "Literal"
    parent = "mezzanine.themes.plain"
    tokens = "tokens.css"
    slots = ["home.hero", "nav.cta"]
    islands = ["gallery", "comments", "search"]
```

`mezzanine-project` writes a theme package, not an empty `project_name/`. Discovery is `importlib.metadata` entry points (`mezzanine.themes`), not "put it first in INSTALLED_APPS and pray."

### 7.3 Island architecture, not a JS framework

Default public JS budget: **zero**, plus opt-in islands.

| Island | Replaces | Implementation |
|---|---|---|
| `nav` | `bootstrap.js` collapse + `bootstrap-extras.js` hover | 30 lines Alpine or a `<details>`/`popover` |
| `gallery` | Magnific Popup | `<dialog>` + CSS scroll-snap, progressive enhancement |
| `comments` | jQuery `.reply` toggle | HTMX swap of the reply form |
| `rating` | jQuery `onclick` count of radios | HTMX POST |
| `search` | full page submit | HTMX GET into `#search-results` |
| `edit` | jQuery Tools + jquery.form + TinyMCE-on-the-front | staff-only island, loaded if `has_site_permission` |

HTMX + Alpine (or vanilla + CSS) keeps the Django view as the state machine. No React SSR, no hydration tax, no `theme.json` → block markup → save-to-DB loop. WordPress cannot do this without throwing Gutenberg away.

Admin can keep a richer editor (ProseMirror / TipTap / Lexical *or* a current TinyMCE 7, behind `RICHTEXT_WIDGET_CLASS` which already exists). The public site never loads it.

### 7.4 Visual theme editor without React lock-in

Authors need a GUI. They do not need Gutenberg.

A first-party **Theme Studio** at `/admin/theme/`:

1. **Token painter** — bind color / type / space tokens to form controls. Live-preview is an `<iframe>` of the real site with `?theme_preview=1` injecting an override stylesheet. No React tree, no block parser.
2. **Slot filler** — click a `[data-slot]` in the iframe, edit the contents (rich text, image, menu, HTML snippet) in a side panel. Save writes `ThemeSlot` rows, not serialized block HTML.
3. **Template picker** — reuse the existing slug/parent/content-type ladder; show the candidate list the view already builds (`pages/views.py` lines 82–99) as a readable stack. Let the author pin `get_template_name()` from the UI.
4. **Pattern library** — HTML partials in `mytheme/patterns/` (`hero-split.html`, `post-card.html`). Inserting a pattern is `{% include %}` or a slot default, not a block comment in the database.

The editor chrome can be any small island (even Preact) because it is **admin-only** and talks to Django over HTTP. The public theme never imports it. That is the anti-lock-in. WordPress fused the editor runtime with the frontend runtime; Mezzanine must refuse to.

### 7.5 First-party theme SDK + a real catalog

- `pip install mezzanine-theme-literal`
- entry point, screenshot, token file, `supports = ["blog", "forms", "galleries", "accounts"]`
- CI fixture that renders `index`, `blog_post_detail`, `gallery`, `form`, `404` against each first-party theme on every Mezzanine commit
- A catalog site that is just a Mezzanine site listing those packages (not a 2014 WordPress clone store). Paid themes can exist later; **liquidity starts with three official ones that do not rot.**

`HOST_THEMES` stays. It becomes `hostname → theme entry point`.

### 7.6 Why this beats FSE

- Git-owned layout, DB-owned content (WP FSE puts layout *in* the DB)
- Tokens are CSS, so designers use the tools they already have
- Islands mean a gallery bug does not take down the nav
- No React tax on the public LCP
- Multi-host themes already exist
- Django templates are a known skill; "learn Gutenberg" is not
- Upgrade path for old sites is mechanical (see §8), not "resave every page in the block editor"

---

## 8. Migration path for existing Mezzanine templates

Do not do a flag day. The existing contract is "a Django app whose templates win." Keep that working forever.

### Phase 0 — honesty (one release)

- Delete or quarantine: `mezzanine.mobile`, IE polyfills, `moxieplayer.swf`, `plugins/example*`, unused `menus/primary.html` + `menus/mobile.html`, UA snippet.
- Fix docs: remove `jquery-1.8.3.min.js`, `mezzathe.me`, "Marketplace" wording.
- Publish the block/slot contract as documentation of what `base.html` already exposes. No behavior change.

### Phase 1 — tokens behind the old classes (one release)

- Rewrite `mezzanine.css` to map existing BS3 class looks onto custom properties (`--mz-color-panel-bg: #F8F8F8` etc.).
- Leave Bootstrap 3 in place. A 2014 theme still renders.
- Add `mezzanine/shell.html` that `{% extends %}`-compatible with today's `base.html` blocks. Old `base.html` becomes a thin wrapper around `shell.html` so `{% extends "base.html" %}` keeps working.

### Phase 2 — compat layer, not a rewrite

Ship `mezzanine.theme.compat.bootstrap3` — a CSS file that defines `.col-md-7`, `.panel`, `.img-responsive`, `.pull-left`, `.sr-only`, `.glyphicon-*` as aliases onto the new tokenized primitives (CSS grid + lucide/system icons). Existing copied templates work unmodified.

New first-party templates use the new primitives only (`mz-cluster`, `mz-stack`, `mz-nav`). `collecttemplates` grows a `--rewrite` that applies a documented class map and prints a diff.

### Phase 3 — JS divorce

- Public pages: stop shipping jQuery. Islands load only when the DOM contains their root.
- `{% editable %}` keeps the same template tags; the implementation swaps from jQuery Tools to a staff-only island. `jquery.form` / overlay / expose / `loadingAnimation.gif` leave the tree.
- Admin: jQuery can remain until grappelli-safe is replaced; that is a different audit. Do not block public theming on admin.

### Phase 4 — theme packages

- A `Theme` base class + entry points.
- `HOST_THEMES` accepts entry-point names.
- Parent themes via `Theme.parent` (template loaders already support ordered apps; formalize it).
- First-party `plain` theme becomes the default `INSTALLED_APPS` head.

### What an existing site operator does

```
# still works, indefinitely
INSTALLED_APPS = ["my_old_theme", "mezzanine.core", ...]

# opt in
INSTALLED_APPS = ["my_old_theme", "mezzanine.theme.compat.bootstrap3", ...]

# later, when they want tokens / studio
# my_old_theme/theme.toml + tokens.css that reproduce their hex values
# no template rewrite required if they keep compat.bootstrap3
```

The slug/parent/content-type template ladder does not change. Page processors do not change. `{% editable %}` call sites do not change. That is the migration: **keep the Django-shaped API, replace the 2013 implementation under it.**

Sites that ran `collecttemplates` years ago and drifted are the hard cases. Give them a checker (`manage.py theme_lint`) that diffs their copies against current core and classifies: identical / class-map-only / semantic drift. Drift stays their problem; the SDK does not pretend to merge HTML.

---

## Competitive scorecard vs WordPress FSE

| Capability | WordPress FSE (2026) | Mezzanine as shipped | Mezzanine if §7 is built |
|---|---|---|---|
| Visual layout editor | Yes (React) | No | Slot + token studio, admin-only |
| Design tokens | `theme.json` | Hex in `mezzanine.css` | CSS custom properties |
| Pattern / block library | Huge, DB-serialized | None | Git-owned HTML partials |
| Theme marketplace | Thousands | 4 abandoned skins | 3 official + entry points |
| Author edits content on-site | Blocks | Field overlay (jQuery Tools) | Same tags, new island |
| Per-page template | Limited | Excellent filesystem ladder | Same, exposed in Studio |
| Multi-host themes | Multisite ceremony | `HOST_THEMES` loader | Same |
| Public JS cost | High (Gutenberg or theme bloat) | jQuery + Bootstrap 3 on every page | Zero + islands |
| Accessibility baseline | Mixed, improving | Fail | Achievable (semantic shell) |
| Upgrade of old themes | Often "rebuild in blocks" | Copy stays frozen | Compat class map |
| Skill required to theme | WP + React + blocks | Django templates | Django templates + CSS tokens |

---

## EXECUTIVE VERDICT

**Mezzanine cannot compete with WordPress block themes or FSE as it exists in this tree.** The public frontend is Bootstrap **3.2.0** (2014) + jQuery **3.4.1** + TinyMCE **4.1.10** (2015) + Chosen **0.9.12** + Magnific Popup **0.9.6** + unversioned jQuery Tools + a GIF spinner + a Flash player. Theming is "copy templates, put your app first." The "marketplace" is a 14-commit GitHub repo of four Bootstrap 3 skins. `mezzanine.mobile` is a `FutureWarning`. Accessibility is a hamburger `sr-only` span. There is no design-token layer, no slot/block contract, no visual editor, no theme SDK.

The salvage is real, and it is **not** "port to Gutenberg." It is the thing WordPress threw away: server-rendered HTML with a stable template API. Keep the inheritance ladder, `{% editable %}`, `{% page_menu %}`, and `HOST_THEMES`. Landfill the 2013 JavaScript. Put CSS tokens under the existing class names, then ship three first-party themes and an admin Theme Studio that paints tokens and fills slots without putting React on the public site.

Until that happens, any claim that Mezzanine is a WordPress alternative on the frontend is nostalgia. It is a well-structured Django site from the Bootstrap 3 era. That is a starting point, not a product.

**Ship/no-ship on frontend competitiveness: NO-SHIP.**
**Ship/no-ship on a token + island + SDK rebuild that *could* beat FSE: SHIP, as a new theme engine, not as a Bootstrap upgrade.**
