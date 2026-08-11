# General INCLUSION — Executive Verdict

**Council seat:** Accessibility, localization, editorial operations  
**Subject:** Mezzanine CMS (`/Users/prondubuisi/gitrepos/dev/mezzanine`)  
**Date:** 2026-08-11  
**Verdict:** **NOT FIT FOR A NEWSROOM. NOT FIT FOR A PUBLIC-SECTOR OR REGULATED SITE.** Ship as a brochure CMS for a single language, staffed by one webmaster, and you will be fine. Ship as a multilingual newsroom, and you will fail WCAG, fail translation, and fail the desk.

---

## 1. The one-paragraph judgment

Mezzanine speaks thirty-five *interface* languages from catalogs last extracted around 2013, and it treats *content* language as an optional, off-by-default column-injection trick (`django-modeltranslation`). It has two content states — Draft and Published — and it defaults new `Displayable` objects to **Published**. “Preview” is “staff can see unpublished URLs on the live site.” “Roles” are Django’s `is_staff` / `is_superuser` plus a per-site permission flag. There is no skip link, no `<main>`, no `aria-*` in any first-party template, and exactly **one** `alt=` in the entire HTML tree (a Twitter avatar). Featured images and gallery images publish with no alternate text. Accessibility is not mentioned in docs, tests, or settings. WordPress in 2010 already beat this stack on roles, revisions, scheduled review, and media alt. Mezzanine’s path forward is not “add a plugin.” It is to make inclusion a type system: media that cannot exist without alt, themes that cannot ship without contrast tokens, and a publish button that refuses inaccessible, untranslated, unowned copy.

---

## 2. Localization — UI strings are a museum; content language is a sidecar

### 2.1 What exists

- Gettext is wired through templates and models. The `<html>` tag sets `lang` and `dir="rtl"` when `LANGUAGE_BIDI` is true. RTL Bootstrap CSS is loaded. This is the strongest inclusion signal in the repo.

```1:2:/Users/prondubuisi/gitrepos/dev/mezzanine/mezzanine/core/templates/base.html
<!doctype html>
<html lang="{{ LANGUAGE_CODE }}"{% if LANGUAGE_BIDI %} dir="rtl"{% endif %}>
```

- Per-app `locale/` trees cover ~38 languages (ar, bg, ca, cs, da, de, en, eo, es, et, fa, fa_IR, fi, fr, hr_HR, hu, id_ID, is_IS, it, ja, ko, lv, nb, nl, pap, pl, pt_BR, pt_PT, ru, sk, sr_Latn, sv, tr, uk_UA, vi_VN, zh, zh_CN, zh_TW). README’s “translated to over 35 languages” is a catalog count, not a quality claim.
- Optional **content** translation via `django-modeltranslation`, documented in `/Users/prondubuisi/gitrepos/dev/mezzanine/docs/multi-lingual-sites.rst`. Off by default:

```1049:1057:/Users/prondubuisi/gitrepos/dev/mezzanine/mezzanine/core/defaults.py
register_setting(
    name="USE_MODELTRANSLATION",
    description=_(
        "If ``True``, the django-modeltranslation application will "
        "be automatically added to the ``INSTALLED_APPS`` setting."
    ),
    editable=False,
    default=False,
)
```

- When enabled, translation is **same-row extra columns**, not linked translation objects. Registered fields:

| Model layer | Translatable | Not translatable |
|---|---|---|
| `Slugged` | `title` | **`slug`** |
| `Displayable` / `MetaData` | `_meta_title`, `description` | `status`, `publish_date`, `expiry_date`, `keywords` |
| `RichText` | `content` | — |
| `BlogPost` | inherited only | **`featured_image`**, categories M2M as objects |
| `GalleryImage` | `description` | `file` |
| `Form` / `Field` | button, response, emails, label, choices, help | field type, required |
| `conf.Setting` | `value` | — |

Source: `/Users/prondubuisi/gitrepos/dev/mezzanine/mezzanine/core/translation.py`, `blog/translation.py`, `pages/translation.py`, `galleries/translation.py`, `forms/translation.py`, `conf/translation.py`.

- Project template wraps URLs in `i18n_patterns` and optionally mounts `set_language`. LocaleMiddleware is auto-inserted when modeltranslation is on (`mezzanine/utils/conf.py`).
- Language switcher: `/Users/prondubuisi/gitrepos/dev/mezzanine/mezzanine/core/templates/includes/language_selector.html` — unlabeled `<select>`, submit button hidden by jQuery `onchange`. No `hreflang`. No language name announced to AT beyond the option text.

### 2.2 The PO files are stale

This is not a vibe. It is the headers.

| Catalog | POT-Creation-Date | PO-Revision-Date | Notes |
|---|---|---|---|
| `core/locale/en` | **2013-10-05** | unset | File-level `#, fuzzy` |
| `core/locale/fr` | 2013-10-05 | 2013-06-23 | Last translator 2013 |
| `core/locale/de` | 2013-10-05 | 2015-04-03 | Best of a bad set |
| `core/locale/ar` | 2013-10-05 | 2013-03-30 | |
| `core/locale/ja` | 2017-01-01 (re-extract) | **2013-06-17** | ~40 empty `msgstr` after re-extract |
| `blog/locale/en` | 2013-11-09 | unset | `#, fuzzy` |
| `pages/locale/*` | 2013-11-09 (es: 2015-04-09) | 2013–2016 | zh_CN revised 2016-11-18 |
| `accounts/locale/fr` | 2013-11-09 | 2013-11-09 | |

English catalogs are **empty templates** (`msgstr ""` throughout) marked fuzzy. They are not a source of truth; they are leftover `makemessages` output.

Reference lines in the catalogs do not match the current tree. `core/locale/en` still cites `admin.py:27` for “This field is required if status is set to published.” That string now lives at `DisplayableAdminForm.clean_content` around line 69 of `/Users/prondubuisi/gitrepos/dev/mezzanine/mezzanine/core/admin.py`. `models.py:275` in the PO is “Content”; in today’s `models.py` line 275 is `def save` on `Displayable`. The catalogs have not been regenerated against this codebase in a decade.

**Operational meaning:** a Japanese or Arabic newsroom that enables Mezzanine today gets a mix of 2013 translations, untranslated 2017+ strings, and English fallbacks. That is not localization. That is a language lottery.

### 2.3 Content multilingual is not a CMS feature

`docs/multi-lingual-sites.rst` is honest: Mezzanine only integrates modeltranslation. The rest is the integrator’s problem. The integration itself has landmines:

1. **Shipped migrations omit translation columns.** You must `USE_MODELTRANSLATION = False` → migrate → flip True → `sync_translation_fields`, or invent a private `MIGRATION_MODULES`. Language set becomes a schema fork. You cannot share migrations across a French and a Japanese deploy.
2. **`save_model` re-saves the object in every language** (`DisplayableAdmin.save_model`, `mezzanine/core/admin.py` ~136–152). Combined with fallbacks, this is how you accidentally materialize English into `title_fr`.
3. **`date_hierarchy` is disabled** when modeltranslation is on (upstream bug, documented in-admin). The newsroom calendar view disappears the moment you go multilingual.
4. **Slugs are not translated.** A French title still lives at `/about/` unless an editor hand-edits a single shared slug. Polylang/WPML give you `/fr/a-propos/` as a first-class object. Mezzanine gives you a column and a prayer.
5. **Featured images are not translated.** The Paris desk and the Montreal desk share one hero. Captions cannot differ. That is not how picture desks work.
6. **No translation completeness.** No “FR 80% / missing 12 strings.” No “this post has no Arabic body.” Publish does not care.
7. **No hreflang, no `lang` on content fragments, no per-language canonical.** SEO and AT both guess.
8. **The practical multilingual pattern in this codebase is multi-tenancy** (`docs/multi-tenancy.rst`): one Site per language, one domain, duplicated trees. That is how you get two newsrooms that drift, not one story in three languages.

**Vs WordPress Polylang / WPML**

| Capability | Polylang / WPML | Mezzanine |
|---|---|---|
| Translation as a linked object | Yes (post ↔ post) | No (columns on one row) |
| Language-specific slug / URL | Yes | No (slug untranslated) |
| Media translation | Yes | No (`FileField` unregistered) |
| Translation completeness UI | Yes | No |
| Language switcher + hreflang | Yes | Switcher only; no hreflang |
| Fallback policy | Configurable, visible | `MODELTRANSLATION_FALLBACK_LANGUAGES` (silent) |
| UI catalog freshness | Continuous (wordpress.org) | Frozen 2013–2016 |
| Default-on | Often (plugin) | Off |

Mezzanine’s multilingual story is “we wrapped a Django app and wrote a 200-line RST file.” It is not a product.

---

## 3. Editorial operations — a webmaster’s desk, not a newsroom

### 3.1 Status is a boolean wearing a choice field

```228:265:/Users/prondubuisi/gitrepos/dev/mezzanine/mezzanine/core/models.py
CONTENT_STATUS_DRAFT = 1
CONTENT_STATUS_PUBLISHED = 2
CONTENT_STATUS_CHOICES = (
    (CONTENT_STATUS_DRAFT, _("Draft")),
    (CONTENT_STATUS_PUBLISHED, _("Published")),
)
...
    status = models.IntegerField(
        _("Status"),
        choices=CONTENT_STATUS_CHOICES,
        default=CONTENT_STATUS_PUBLISHED,   # <-- the landmine
        ...
    )
    publish_date = models.DateTimeField(...)  # "won't be shown until this time"
    expiry_date = models.DateTimeField(...)   # "won't be shown after this time"
```

- **Default is Published.** A new page or post is live unless someone remembers to click Draft. The quick-blog dashboard widget is the exception (`blog/forms.py` forces `CONTENT_STATUS_DRAFT`). The main admin is not.
- `publish_date` is auto-set to `now()` on first save. “Scheduled publishing” in the README means “type a future datetime into a box.” There is no queue, no “Scheduled” state, no cron-visible calendar of what goes out tonight.
- There is no Pending Review, Legal Hold, Copydesk, Killed, or Embargoed.

### 3.2 Preview is privilege leakage, not a workflow

`PublishedManager.published` (`mezzanine/core/managers.py`):

```64:70:/Users/prondubuisi/gitrepos/dev/mezzanine/mezzanine/core/managers.py
        if for_user is not None and for_user.is_staff:
            return self.all()
        return self.filter(
            Q(publish_date__lte=now()) | Q(publish_date__isnull=True),
            Q(expiry_date__gte=now()) | Q(expiry_date__isnull=True),
            Q(status=CONTENT_STATUS_PUBLISHED),
        )
```

If you are staff, you see everything on the public site. That is the preview. There is:

- no signed preview token for an outside lawyer or freelancer
- no “share preview link” that expires
- no unpublished URL distinct from the public slug
- no “this is a draft” banner required in the public templates

A reporter’s draft of a courtroom story is one guessed URL away from any intern with `is_staff`.

### 3.3 Ownership is a foreign key, not a desk

`Ownable` (`mezzanine/core/models.py` ~532–551) is `user = ForeignKey(..., verbose_name="Author")`. `OwnableAdmin` hides other people’s rows from non-superusers, unless the model is listed in `OWNABLE_MODELS_ALL_EDITABLE`. Inline editing is restricted to owner or superuser (`is_editable`).

That is “my posts / all posts.” It is not:

- section editor can edit the politics desk, not sports
- copy editor can change body but not publish
- contributor can submit, cannot publish
- legal can lock

`SitePermission` (`mezzanine/core/models.py` ~607–625, middleware in `mezzanine/core/middleware.py`) answers a different question: *which Site may this staff user admin?* Multi-tenant hosting, not editorial rank.

Page hooks `can_add` / `can_change` / `can_delete` / `can_move` default to “yes” (`pages/models.py` ~198–223). They are extension points, not a role matrix. Django `auth.Group` appears in the admin menu. No group is predefined. No documentation describes an Editor or Contributor.

### 3.4 What a newsroom expects and does not get

| Newsroom need | WordPress | Mezzanine |
|---|---|---|
| Roles: Super Admin / Admin / Editor / Author / Contributor / Subscriber | Built-in | `is_superuser` / `is_staff` + SitePermission + optional Ownable filter |
| Pending review | Yes | No |
| Revisions + compare + restore | Yes (built-in) | Django `LogEntry` only (who clicked Save, not a snapshot) |
| Editorial comments on a post | Yes (editorial notes; also public comments) | Public `ThreadedComment` only |
| Scheduled posts as a first-class state | Yes | `publish_date` in the future, status still “Published” |
| Preview for non-staff | Shareable preview (block editor) | Staff-on-live-site |
| Default new post | Draft | **Published** |
| Lock / checkout | Plugins / Gutenberg lock | None |
| Section / beat permissions | Categories + roles + plugins | Page-tree hooks you write yourself |

Inline editing (`includes/editable_toolbar.html`, `includes/editable_form.html`) is a nice webmaster feature and a terrible newsroom feature: it puts TinyMCE on the live page with an empty toolbar toggle and no audit trail.

The only publish gate in the entire admin is “content cannot be empty if status is Published” (`DisplayableAdminForm.clean_content`). That is a not-null check. It is not an editorial standard.

---

## 4. Accessibility — Bootstrap 3 cosmetics, zero construction

### 4.1 Inventory of first-party templates

Searched: `alt=`, `aria-`, `role=`, `tabindex`, `wcag`, `skip`, `sr-only` across `*.html`. Result:

| Pattern | Hits in first-party HTML | Where |
|---|---|---|
| `alt=` | **1** | Twitter avatar (`twitter/tweets.html`) |
| `aria-label` / `aria-invalid` / `aria-describedby` / `aria-current` / `aria-expanded` | **0** | — |
| `role=` | 2 meaningful | `role="navigation"` on a **div** navbar; `role="search"` on the search form; `role="form"` on ratings |
| skip link | **0** | — |
| `<main>`, `<nav>`, `<header>` landmarks | **0** (footer is the only HTML5 landmark) | `base.html` |
| `sr-only` | 1 | Hamburger “Toggle Navigation” |
| `wcag` / `accessibility` / `a11y` in py/rst/html/md | **0** | The words do not exist in this project |

Vendor JS (jQuery UI, Bootstrap, TinyMCE) contains ARIA. That does not count. Mezzanine did not author it and does not test it.

### 4.2 Concrete failures (WCAG 2.2 mapping)

**1.4.3 Contrast (AA) — fail by stylesheet.**  
`/Users/prondubuisi/gitrepos/dev/mezzanine/mezzanine/core/static/css/mezzanine.css`:

```31:38:/Users/prondubuisi/gitrepos/dev/mezzanine/mezzanine/core/static/css/mezzanine.css
.navbar-text {
  font-style: italic;
  font-size: 11px;
  color: #aaa !important;
  line-height: 100%;
  ...
}
```

`#aaa` on Bootstrap’s default navbar `#f8f8f8` is ~2.2:1. AA needs 4.5:1. The `!important` is how you tell a theme author “do not fix this.”

**1.1.1 Non-text content — fail by omission.**  
Featured image, no alt:

```53:57:/Users/prondubuisi/gitrepos/dev/mezzanine/mezzanine/blog/templates/blog/blog_post_detail.html
{% block blog_post_detail_featured_image %}
{% if settings.BLOG_USE_FEATURED_IMAGE and blog_post.featured_image %}
<p><img class="img-responsive" src="{{ MEDIA_URL }}{% thumbnail blog_post.featured_image 600 0 %}"></p>
{% endif %}
{% endblock %}
```

Same on the list (`blog_post_list.html` ~102–107). Gallery images use `title="{{ image.description }}"` (tooltip) and **no `alt`** (`galleries/templates/pages/gallery.html` ~20–22). `GalleryImage.description` is auto-filled from the **filename** on first save (`galleries/models.py` ~148–165) — so even if you later wire it to `alt`, zip-imported photos become `DSC_0142` for screen-reader users. Comment gravatars have no alt. Admin order arrows (`OrderWidget`, `pages/menus/admin.html`) have no alt. Page-tree delete control is an empty `<a class="delete">`.

`FileField` is a thin wrapper around Django/filebrowser. There is no `alt_text` column. Media cannot be accessible because the type does not know what alt is.

**2.4.1 Bypass blocks — fail.**  
`base.html` goes `body → div.navbar → div.container → h1 → ul.breadcrumb → columns`. No skip link. Fixed navbar (`navbar-fixed-top` + `body { padding-top: 50px }`) is a keyboard tax on every page.

**2.4.4 / 2.4.6 Link and heading purpose — fail in chrome.**  
Pagination is a bare `&larr;` / `&rarr;` with no accessible name (`includes/pagination.html`). Twitter “open” control is a glyphicon-only link (`twitter/tweets.html` line 20). Search submit is “Go.” Language selector has no `<label>`. Search field is placeholder-only:

```1:5:/Users/prondubuisi/gitrepos/dev/mezzanine/mezzanine/core/templates/includes/search_form.html
{% load mezzanine_tags i18n %}
<form action="{% url "search" %}" class="navbar-form navbar-right" role="search">

<div class="form-group">
    <input class="form-control" placeholder="{% trans "Search" %}" type="text" name="q" value="{{ request.GET.q }}">
```

Placeholder is not a label. It disappears as you type. Contrast on placeholders is typically worse than body text.

**1.3.1 Info and relationships — mixed.**  
`includes/form_fields.html` *does* emit `<label for="...">`. That is the one competent form pattern. Errors go in a sibling `.help-block` with **no** `aria-invalid`, **no** `aria-describedby`, **no** `role="alert"`. `form_errors.html` is a visual banner only. The comment honeypot is hidden with `display:none` CSS, so it remains in the accessibility tree as a mystery field (`generic/includes/comments.html` line 15).

**3.3.2 / 4.1.2 Forms — HTML5 is off.**  
`FORMS_USE_HTML5` defaults to **False**. `Html5Mixin` (required attribute, email/url types, autofocus) is used by accounts and comments, not by `FormForForm`. The forms builder — the thing editors give to the public — is the least accessible form path.

**Keyboard / widgets — inherited rot.**  
Navbar toggle has no `aria-expanded`. Dropdowns use Bootstrap 3 + `class="dropdown-toggle disabled"` (yes, `disabled` on the parent that has children — a known keyboard trap). Chosen 0.9.12 (2012) replaces `<select>` in admin. Magnific Popup drives the gallery. TinyMCE is the default `RICHTEXT_WIDGET_CLASS`. None of these are in Mezzanine’s test suite as AT or keyboard targets.

**Admin chrome.**  
Login (`admin/login.html`) has real labels. That is the high-water mark. Page tree (`pages/menus/admin.html`) is a drag-and-drop nest of empty controls and unlabeled arrow GIFs. Language and site switchers in `admin/includes/dropdown_menu.html` are unlabeled `<select onchange=...>`. `editable-toolbar-toggle` is an empty `<a href="#">`.

### 4.3 What “accessibility-ready” means in WordPress, and why Mezzanine cannot tick it

WordPress.org will not list a theme as accessibility-ready without, among other things:

- a skip link
- keyboard-operable menus
- form labels
- acceptable contrast
- heading structure
- `alt` on content images (or a documented decorative exception)

Mezzanine’s default theme would be rejected on the first three items before a reviewer opened a blog post. There is no theme review, no `accessibility-ready` tag, no `prefers-reduced-motion`, no contrast token, no forced-colors consideration. Bootstrap 3 is the design system. Bootstrap 3 was released in 2013, the same year the PO files froze.

---

## 5. Comparison card — Mezzanine vs a 2015 WordPress newsroom

```
                         WP + Polylang/WPML          Mezzanine
UI i18n                  continuous                  2013 catalogs
Content i18n             linked posts, slugs, media  optional columns
hreflang                 yes                         no
Roles                    6 built-in + caps           staff / superuser / owner
Revisions                yes                         no
Editorial notes          yes                         no
Pending review           yes                         no
Scheduled state          yes                         publish_date hack
Preview token            yes                         staff sees live drafts
Default status           draft                       published
A11y theme gate          accessibility-ready         none
Media alt required       field in library            field does not exist
Publish-time a11y        plugins (Editoria11y etc.)  empty-body check only
Skip link                required for the tag        absent
```

Mezzanine wins on: Django-native code, page tree, forms builder as a Page type, RTL stylesheet present, `lang`/`dir` on `<html>`. Those are not enough.

---

## 6. Proposals

### 6.1 Real multilingual content (not just UI strings)

Stop treating language as extra columns on one row. Introduce a **`TranslationSet`** and **`LocaleEdition`**:

- One canonical story, N editions. Each edition has its own `slug`, `title`, `body`, `featured_media`, `status`, `publish_date`, `completeness`.
- `hreflang` and language switcher are generated from the set, never from `LANGUAGES` settings alone. Missing editions do not render a fallback body silently; they render a “not available in FR — read in EN” affordance the reader can refuse.
- Slugs are per-locale. `/en/election-guide/` and `/fr/guide-elections/` are siblings, not a fight over one `slug` column.
- Media is translatable: the same `MediaAsset` can carry locale-specific crop, caption, and alt. A French alt is not “the English alt, but in France.”
- Completeness is a number the publish gate can see: `editions.complete_for(locale) >= threshold`.
- UI catalogs: throw away the 2013 PO tree or regenerate it in CI. Empty `msgstr` in a non-`en` locale is a test failure, not a Transifex souvenir. English is the source; it does not need a fuzzy empty catalog.
- Migrations: translation is data, not schema. No more `sync_translation_fields` as a rite of passage.

This kills the “spin up a Site per language” multi-tenancy workaround for i18n. Sites stay for organizations. Languages stay for readers.

### 6.2 Roles that match newsrooms

Replace the staff boolean with a capability matrix that maps to desks.

| Role | Create | Edit others | Publish | Schedule | Legal lock | A11y override | Translations |
|---|---|---|---|---|---|---|---|
| Contributor | own, draft only | no | no | no | no | no | own locale |
| Reporter | own | no | no | propose | no | no | own locale |
| Copy editor | — | yes, body/headline | no | no | no | no | yes |
| Section editor | yes | yes, in section | yes, in section | yes | no | no | assign |
| Publisher / IE | yes | yes | yes | yes | no | yes (logged) | all |
| Legal / Standards | read | no | unpublish only | no | yes | no | n/a |
| Accessibility editor | read | alt/caption/transcript | block | no | no | no | n/a |

Implementation notes, Django-native:

- Drop “default=Published.” New `Displayable` is `draft`.
- Add states: `draft → in_review → copydesk → scheduled → published → killed`, with `embargo` as a flag, not a state.
- `Ownable` becomes `desk` (FK to a Section) + `authors` (M2M) + `last_editor`. Superuser-sees-all remains; everyone else is desk-scoped.
- Preview is a signed, expiring token on a `/_preview/<token>/` path that does not require `is_staff`. Drafts are never at the public slug.
- Revisions are snapshots (django-reversion or a first-party `ContentRevision`). Editorial comments are a `Note` model on the edition, not `ThreadedComment`.
- Django Groups are *generated from* these roles so the admin does not invent a parallel universe.

### 6.3 Accessibility as a gate on publish

`DisplayableAdminForm.clean_content` is the right *shape* and the wrong *check*. Replace it with a **`PublishGate`** that runs on the transition into `scheduled` or `published`:

1. **Media:** every non-decorative image has non-filename alt ≥ N characters, in the edition’s locale. Every `<iframe>` has a title. Every uploaded video has a transcript or caption track.
2. **Document:** one `h1`, no skipped heading levels in the rich-text HTML, no empty links, no `javascript:` hrefs.
3. **Contrast in authored HTML:** inline `style="color:…"` that fails against the theme’s background token is an error, not a warning.
4. **Language:** `html[lang]` matches the edition. Embeds that are a different language are wrapped with `lang=`.
5. **Translation:** if the site is multilingual, the edition set either has a complete sibling or an explicit “publish this locale only” acknowledgement.
6. **Ownership:** an identified author and desk. Anonymous publish is a publisher-only override.

Gates return structured violations (`code`, `wcag`, `selector`, `fix`). The admin shows them as a checklist, not a ValidationError traceback. Overriding a gate requires the Accessibility editor or Publisher role and writes an audit row.

Staff preview (the current behavior) must render the same checklist as a banner: “this draft would fail publish for 4 reasons.”

### 6.4 Revolutionary: accessible by construction

Do not audit after the fact. Make illegal states unrepresentable.

**Typed media.**

```
MediaAsset
  kind: Image | Video | Audio | Document
  file: ...
  decorative: bool

ImageAsset(MediaAsset)
  alt: Translatable[NonEmptyStr]   # required if not decorative
  longdesc: optional
  credit: optional
  focal_point: ...

VideoAsset
  transcript: Translatable[Text] | captions: VTT   # one required
  title: Translatable[NonEmptyStr]
```

`BlogPost.featured_image` becomes `FK(ImageAsset)`. The ORM refuses `save()` if `decorative=False` and alt is empty. TinyMCE’s image plugin may only insert an `ImageAsset` id, never a raw `<img src>`. Zip import into a gallery creates `ImageAsset` rows in `incomplete` state; the gallery page **will not render** an incomplete asset on the public site (it can render a placeholder in admin). Filename-derived “descriptions” are banned.

**Contrast tokens in themes.**

A theme is not a pile of CSS. It is a contract:

```
theme.tokens.json
  color.text
  color.bg
  color.accent
  color.text-on-accent
  color.muted          # must still pass 4.5:1 against color.bg
  focus.ring
  space.*, size.type.*
```

CI computes contrast for every text/background pair. A theme that ships `#aaa` on `#f8f8f8` **does not build**. Authors cannot pick arbitrary hex in the rich-text color picker; they pick `accent` or `muted`. `!important` greys are a compile error.

**Landmarks by template inheritance.**

`base.html` is a skeleton that *cannot* be overridden into inaccessibility:

```
skip-link → header/nav → main#content (tabindex=-1) → aside → footer
```

Child templates fill `{% block main %}`. They cannot omit the skip target. Menus emit `<nav aria-label=...>` and `aria-current="page"`. Pagination emits `aria-label="Pagination"` and text alternatives for next/prev. Search has a visible or visually-hidden `<label>`. The language selector is a `<nav aria-label="Language">` with links (progressive enhancement), not a JS-only `<select>`.

**Rich text is a typed subset.**

The allow-list (`RICHTEXT_ALLOWED_ATTRIBUTES` already includes `alt`, `hreflang`, `tabindex` — and never uses them) becomes a schema: `img` without `alt` is stripped or rejected at `RichTextField.clean`. `alt` is not “allowed.” It is required.

That is the revolution: **inclusion is not a theme option and not a checklist a junior editor forgets on deadline. It is the shape of the data.**

---

## 7. What to keep

- `lang` / `dir` on `<html>`, RTL CSS path.
- `form_fields.html` label-for-id pattern — extend it with `aria-invalid` / `aria-describedby`.
- `Html5Mixin` — turn `FORMS_USE_HTML5` on, and make `FormForForm` inherit it.
- Draft-visible-to-staff as a *debug* mode, not as preview.
- `publish_date` / `expiry_date` as scheduling primitives — promote them to states, do not delete them.
- Page-tree `can_*` hooks — they are the right extension point once roles exist.
- modeltranslation integration as a migration story for existing sites; do not make it the future.

---

## 8. Immediate non-negotiables (if the project continues)

These are not the revolution. These are the apology.

1. Default `status` to Draft.
2. Put a skip link and a `<main id="content">` in `base.html`.
3. Add `alt="{{ image.description }}"` on gallery and featured images *and* stop auto-filling description from filename.
4. Label the search input and the language selector.
5. Delete `#aaa !important`.
6. Add `aria-invalid` + `aria-describedby` in `form_fields.html`.
7. Hide the honeypot with `hidden` / `tabindex="-1"` / `aria-hidden="true"`, not CSS.
8. Regenerate PO files; fail CI on empty `msgstr` for supported locales.
9. Stop re-saving every language in `DisplayableAdmin.save_model` without an explicit “copy to empty locales” action.
10. Write one test that fetches `/` and asserts a skip link and at least one `alt` on every `<img>`.

Until 1–7 land, do not call this CMS “ready” for a government, a university, a broadcaster, or anyone who has to answer to a human rights commission.

---

## 9. Final vote

**REJECT as a multilingual, accessible, editorial platform.**

Mezzanine is a competent 2013 Django brochure CMS with a page tree, a forms builder, and a well-intentioned i18n story that froze in place. Inclusion was never a requirement, so the system cannot enforce it. The way out is not another optional app. The way out is types: media that require alt, themes that require contrast, editions that require a language, roles that require a desk, and a publish button that will not move until those types are satisfied.

I will not vote to ship this to a newsroom.

— **General INCLUSION**
