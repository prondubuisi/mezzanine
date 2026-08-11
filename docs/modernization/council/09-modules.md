# 09 — First-Party Modules: Accounts, Forms, Galleries, Generic

**Council role:** General MODULES  
**Scope:** `mezzanine.accounts`, `mezzanine.forms`, `mezzanine.galleries`, `mezzanine.generic`  
**Method:** Independent audit from source, tests, docs, fixtures. No repo modifications.  
**Comparators:** Gravity Forms, WordPress Media Library, Jetpack/WP comments, WooCommerce users.  
**Django replacements considered:** django-allauth, django-filer / wagtailimages, django-taggit, django-comments-xtd, django-star-ratings, django-forms-builder (ancestor of `mezzanine.forms`).

---

## EXECUTIVE VERDICT

**These four apps are a 2012 “batteries included” suite that still ships as if they were product features. They are not.** They are thin, clever, and tightly coupled to the page tree and admin — which is their only remaining moat. Feature-for-feature they lose to Gravity Forms, WP Media, Jetpack Comments, and Woo users by a decade. The right move is not a parity chase. It is a split:

| Module | Verdict | Why |
|---|---|---|
| **Forms** | **Modernize the *idea*, replace the *engine*** | Page-native form is a real differentiator. The field model (integer type enum, EAV entries, no conditionals, no consent, no file policy) is not salvageable as a Gravity Forms competitor. Rebuild as typed blocks on the page tree. |
| **Galleries** | **Do not modernize as a media library** | A zip-import page with Magnific Popup is not a DAM. The actual media library is `filebrowser_safe` (optional, jQuery-UI 1.8-era). Replace both with a first-class asset model. Keep zip-import as an *ingestion UX*, not as the product. |
| **Accounts** | **Replace the identity stack; keep the CMS gate** | `accounts` is a thin Django User wrapper (min password 6, magic-link reset that *logs you in*, no 2FA, no social, no roles beyond `is_active`/`is_staff`). Public members and CMS users are the same table. Use allauth (or equivalent) for identity; keep `Page.login_required` and grow it into entitlements. |
| **Generic (comments / ratings / keywords)** | **Keep the *field pattern*, replace the *products*** | `CommentsField` / `KeywordsField` / `RatingField` (denormalized GFK + extra columns) is the best code in this audit. The products on top — `django_comments` threads, cookie ratings, admin-JS tags — are commodities. Swap implementations; keep the contribute-to-class API. |

**Do not ship a “Mezzanine 7 with nicer Bootstrap on the same models.”** The models encode 2012 product assumptions (Akismet-or-nothing spam, Disqus-or-built-in comments, Gravatar as identity, JPEG/PNG/GIF thumbnails, password length as the only policy). Modernizing *around* those assumptions wastes the one thing these apps still have: they live inside the CMS page object.

**If only four bets are funded:**

1. **Form builder as typed blocks** on `Page` (conditionals, consent, uploads as media, typed JSON entries).
2. **Media as a first-class DAM** (variants, AVIF/WebP, blurhash, alt, usage). Kill galleries-as-library.
3. **Memberships + paywalls** as a generalization of `Page.login_required` — not another user-profile form.
4. **Comments as an activity protocol** (webmentions / ActivityPub adapter), with the GFK field remaining the CMS hook.

Everything else in this folder is replace-or-delete.

---

## How these apps sit in the product

Default `INSTALLED_APPS` in the project template (`mezzanine/project_template/project_name/settings.py`):

- **On by default:** `mezzanine.generic`, `mezzanine.forms`, `mezzanine.galleries`
- **Commented out:** `mezzanine.accounts`
- **Optional, auto-appended if importable:** `filebrowser_safe` (the real “Media Library”), `grappelli_safe`

`mezzanine.generic` is also auto-installed when blog is present, and it forces `COMMENTS_APP = "mezzanine.generic"` plus `django_comments` (`mezzanine/utils/conf.py`).

So the marketed “features” in `README.rst` — *“Drag-and-drop HTML5 forms builder with CSV export”*, *“User accounts and profiles with email verification”*, *“Disqus integration, or built-in threaded comments”*, *“Tagging”*, *“Akismet spam filtering”* — are four small apps plus an optional FileBrowser fork, not a platform.

---

## 1. Forms builder — capabilities and limits

**Identity:** `mezzanine.forms` is explicitly “a port of django-forms-builder for Mezzanine” (`mezzanine/forms/__init__.py`). The differentiator vs. the standalone library is that `Form` **is a `Page`** (`mezzanine/forms/models.py`):

```11:51:mezzanine/forms/models.py
class Form(Page, RichText):
    """
    A user-built form.
    """

    button_text = models.CharField(_("Button text"), max_length=50, blank=True)
    response = RichTextField(_("Response"))
    send_email = models.BooleanField(...)
    email_from = models.EmailField(...)
    email_copies = models.CharField(...)   # comma-separated notify list
    email_subject = models.CharField(...)
    email_message = models.TextField(...)
```

That single inheritance is the whole product thesis: a form gets slugs, menus, draft/publish, SEO meta, `login_required`, search, and the page tree for free. Gravity Forms is a plugin bolted onto posts. Mezzanine forms *are* content.

### What it can do (from code)

| Capability | Implementation | Evidence |
|---|---|---|
| 15 built-in field types | Integer enum `1..15` | `mezzanine/forms/fields.py` (`TEXT` … `DOB` + `HIDDEN`) |
| Extra types / widgets | `FORMS_EXTRA_FIELDS`, `FORMS_EXTRA_WIDGETS` | `fields.py` 95–115, `defaults.py` |
| Required / visible / default / placeholder / help | Columns on `AbstractBaseField` | `models.py` 67–91 |
| Choices | Comma-separated, backtick-quoted | `get_choices()` |
| File upload | `forms.FileField`, stored under `FORMS_UPLOAD_ROOT/forms/<uuid>/` | `forms.py` 215–216 |
| Email to submitter | First `EmailField` on the form | `FormForForm.email_to()` |
| Email to staff + file attachments | `email_copies`, `send_mail_template` | `page_processors.py` 62–72 |
| Thank-you copy | `Form.response` richtext, `?sent=1` | `templates/pages/form.html` |
| Default values as Django templates | `Template(field.default).render(context)` | `forms.py` 175 |
| Hidden fields | Type 12 | Used for constants / templated defaults |
| Admin drag-and-drop field editor | `TabularDynamicInlineAdmin` | `admin.py` `FieldAdmin` |
| Entries browser + filters + CSV | `EntriesForm` + `FormAdmin.entries_view` | `admin.py` 128–186, `forms.py` 241–445 |
| Delete selected entries | Permission `delete_formentry` | `admin.py` 138–176 |
| File download (staff) | `admin:form_file` streams from disk | `admin.py` 188–198 |
| Signals | `form_valid`, `form_invalid` | `signals.py` |
| Demo fixture | Contact form: Name, Email, Subject select, Message | `fixtures/mezzanine_optional.json` |
| i18n of button text | Tested | `tests/test_forms.py` `test_submit_button_text` |

### Conditional logic? **No.**

There is no `show_if`, no branching, no multi-page/wizard, no calculated fields, no payment field, no section/page-break type. `visible` is a static admin boolean (`FieldManager.visible()`), not a runtime rule. Front-end JS for the public form is one autofocus line (`templates/pages/form.html` 39–41). Admin JS only toggles filter-option visibility on the entries screen.

Gravity Forms’ entire mid-market value (conditional sections, multi-page, pricing, webhooks) is absent.

### File uploads? **Yes, but unsafe-by-omission.**

```215:216:mezzanine/forms/forms.py
            if value and self.fields[field_key].widget.needs_multipart_form:
                value = fs.save(join("forms", str(uuid4()), value.name), value)
```

- UUID directory avoids overwrite. Good.
- **No extension/MIME whitelist.** `FILE = 9` is a naked `forms.FileField`.
- **No size cap** beyond Django’s global upload settings.
- **Path stored as a string** in `FieldEntry.value` (`CharField(max_length=FORMS_FIELD_MAX_LENGTH)` default **2000**).
- `FORMS_UPLOAD_ROOT` default is `""` (`defaults.py`). `FileSystemStorage(location="")` resolves to the process CWD. A project that enables file fields without setting this writes user uploads next to `manage.py`.
- Download is staff-only, but `file_view` uses `guess_type` + raw `open(path)` with no path-canonicalization check against `FORMS_UPLOAD_ROOT`. The stored value is whatever was saved; there is no “is this still under the upload root?” assert.
- Staff notification emails attach the raw upload (`page_processors.py` 35–38, 70).

This is 2011 contact-form quality, not Gravity Forms file fields (type restrictions, max size, virus-scan hooks, stored as attachments with access control).

### Spam? **Akismet or nothing, and success is faked.**

```31:34:mezzanine/forms/page_processors.py
    if form.is_valid():
        url = page.get_absolute_url() + "?sent=1"
        if is_spam(request, form, url):
            return redirect(url)
```

Spam posts get the same `?sent=1` thank-you as real ones. No entry is saved. No log. No quarantine. `is_spam` walks `SPAM_FILTERS` (default: `is_spam_akismet`). Akismet is skipped entirely if `AKISMET_API_KEY` is empty, and **fails closed to “not spam”** on any network error (`utils/views.py` 108–109). Field mapping is heuristic: first field labelled “Name”, first `EmailField`, first `URLField`, first `Textarea` (`utils/views.py` 83–92). If there is no textarea, Akismet is not called.

There is **no CAPTCHA** in tree. Docs point at a third-party `mezzanine-captcha` plugin (`docs/overview.rst`). There is **no honeypot** on forms (the honeypot CSS in comments is from `django_comments`, not forms). CSRF is present via `{% fields_for %}` (`core/templates/includes/form_fields.html`). Hidden `referrer` is passed for Akismet.

Gravity Forms: Akismet + native honeypot + reCAPTCHA/hCaptcha + Cloudflare Turnstile + built-in anti-spam scoring. Mezzanine: one optional HTTP call to Akismet 1.1 over **http://** (`utils/views.py` 101) unless you wrap it yourself.

### Accessibility? **Labels only. HTML5 off by default.**

`FORMS_USE_HTML5` defaults to **`False`** (`core/defaults.py`). When off:

- Inputs are generic `text` / `select` / `textarea`
- `placeholder_text` is stripped from the admin inline (`forms/admin.py` 48–50)
- No `type="email|url|number|date"`

When on, `required` is set as an empty attribute and a few HTML5 input types are swapped in (`fields.py` 81–93; `forms.py` 191–199).

`includes/form_fields.html` does the 2013 Bootstrap 3 pattern: `<label for="...">` + control + `.help-block`. Missing, relative to WCAG 2.2 / Gravity Forms’ accessibility work:

- No `aria-describedby` linking help/errors to the control
- No `aria-invalid`
- Errors replace help text instead of appending
- Radio / checkbox groups are not wrapped in `<fieldset>` / `<legend>`
- Required is a visual `<p>required</p>`, not `aria-required` (the HTML5 `required` attr is the only machine signal, and it’s off by default)
- Date fields use `SelectDateWidget` (three `<select>`s) unless HTML5 is on
- Autofocus via jQuery on first visible input — hostile to keyboard/AT users who didn’t ask
- No autocomplete tokens on name/email
- No visible focus management after error

Tests (`tests/test_forms.py`) assert HTTP 200 on GET/POST. There is no a11y test.

### GDPR / privacy? **None.**

- No consent / lawful-basis field type
- No “store submission? / send email?” split beyond the form-level `send_email` flag
- `FormEntry` stores only `form` FK + `entry_time` (`models.py` 141–151)
- **No IP, no user FK, no user-agent, no consent timestamp**
- No retention policy, no anonymize, no export-of-*this-person’s*-data (CSV is per-form, not per-subject)
- File uploads persist forever under UUID dirs
- Double opt-in is not a form feature (that lives, poorly, in `accounts`)

A European contact form built with this app is a DPIA finding waiting for a lawyer.

### Entries model: EAV, 2000-character ceiling

```154:167:mezzanine/forms/models.py
class FieldEntry(models.Model):
    entry = models.ForeignKey("FormEntry", ...)
    field_id = models.IntegerField()
    value = models.CharField(max_length=settings.FORMS_FIELD_MAX_LENGTH, null=True)
```

- `field_id` is a loose integer, **not an FK**. Delete a field, entries become orphans with a number.
- All values are strings. Multi-select is `", ".join(...)`. Files are paths. Booleans are `"True"` / `"False"`-ish.
- Export filters run **in Python over every FieldEntry** (`EntriesForm.rows`) — no SQL for “email contains X”. Fine for a church contact form. Fatal for a 50k-row lead gen form.
- No webhook, no Mailchimp (that was `mezzanine-mailchimp`, third-party), no Zapier, no CRM.

### Forms vs Gravity Forms (honest score)

| | Mezzanine Forms | Gravity Forms |
|---|---|---|
| Placement | First-class Page | Plugin shortcode / block |
| Field types | 15 + extension hook | 30+ including consent, list, credit card, website, password, captcha |
| Conditional logic | None | Per-field, per-page, per-notification |
| Multi-page | No | Yes |
| Payments | No (Cartridge is a different app) | Stripe/PayPal add-ons |
| Uploads | Unvalidated FileField | Typed, sized, access-controlled |
| Spam | Optional Akismet, fail-open | Honeypot + CAPTCHA + Akismet + scoring |
| GDPR | None | Consent field, export/erase add-ons |
| A11y | Label + optional HTML5 | Multi-year WCAG investment |
| Entries | In-process EAV filter + CSV | DB-backed search, notes, star, partials |
| Extensibility | Signals + extra field IDs | PHP hooks, add-on economy |
| Notifications | One submitter email + one CC list | Multiple routed notifications, PDFs |

**Keep:** form-as-page, drag-and-drop admin inline, CSV, signals, templated defaults.  
**Throw away:** the integer type enum, the EAV `FieldEntry`, the absence of a policy layer.

---

## 2. Galleries / media — not a media library

Two different things are routinely conflated.

### A. `mezzanine.galleries` — a page type

```118:165:mezzanine/galleries/models.py
class Gallery(Page, RichText, BaseGallery):
    """Page bucket for gallery photos."""

class GalleryImage(Orderable):
    gallery = models.ForeignKey("Gallery", ..., related_name="images")
    file = FileField(..., format="Image", ...)
    description = models.CharField(..., max_length=1000, blank=True)
```

Capabilities:

- Ordered images on a page
- Zip import on save: open zip, `PIL.Image.verify()`, basename only (zip-slip mitigated by `os.path.split(name)[1]`), charset-detect the filename, write into `galleries/<slug>/`, autogenerate description from filename title-case (`models.py` 50–165)
- Admin: `TabularDynamicInlineAdmin` (`galleries/admin.py`)
- Front: Bootstrap 3 grid + Magnific Popup lightbox (`templates/pages/gallery.html`)
- Thumbnails via `{% thumbnail image.file 131 75 %}` — fixed 131×75 crop

What it is **not**:

- Not reusable assets. An image belongs to one gallery. Reuse is “upload it again” unless FileBrowser is in the mix.
- No alt text distinct from `description`. The template puts `description` on the `<a title>` and the `<img>` has **no `alt`** (`gallery.html` 20–21). Instant WCAG fail.
- No caption / credit / license / focal point / EXIF store (thumbnail *reads* orientation and then **strips EXIF** — `mezzanine_tags.py` 368–389)
- No folders, collections, tags on assets, smart crops, srcset, art direction
- No video, PDF, SVG policy
- Zip import: no max zip size, `except: continue` on bad images, `except ImportError: pass` if Pillow missing (then *any* zip member is treated as an image), Unicode filename warnings rather than a real codec strategy

Tests (`tests/test_galleries.py`): zip creates images with descriptions; thumbnail writes a 24×24 JPEG. That is the entire product contract.

### B. The actual “Media Library” is `filebrowser_safe`

Documented as a Grappelli/FileBrowser fork (`docs/admin-customization.rst` “Media Library Integration”, `docs/overview.rst`). Wired as `OPTIONAL_APPS` + `PACKAGE_NAME_FILEBROWSER = "filebrowser_safe"`. `mezzanine.core.fields.FileField` is a compatibility shim:

```101:121:mezzanine/core/fields.py
# Define a ``FileField`` that maps to filebrowser's ``FileBrowseField``
# if available, falling back to Django's ``FileField`` otherwise.
```

`MEDIA_LIBRARY_PER_SITE` can isolate directories per Django site. TinyMCE can pop a jQuery UI 1.8.24 dialog (`filebrowser/js/jquery-ui-1.8.24.min.js` — cited in docs). This is a **filesystem browser**, not a media database:

- Files are paths on disk / storage
- No first-class `Asset` row with metadata, renditions, or usage index
- No “where is this image used?”
- No derived variants other than FileBrowser/Mezzanine thumbnails
- Admin skin is frozen to the Grappelli-safe era

### C. Thumbnails are a template tag, not a rendition pipeline

`{% thumbnail %}` (`mezzanine/core/templatetags/mezzanine_tags.py` 275+) :

- Pillow, on first request, filesystem cache under `.thumbnails/<original-name>/`
- Formats: **PNG / GIF / JPEG only** (`filetype = {".png": "PNG", ".gif": "GIF"}.get(..., "JPEG")`)
- Quality default 95, crop center, optional pad, optional no-upscale
- **No WebP, no AVIF, no srcset, no blurhash / LQIP, no CMS-time pre-generation**
- Missing source image → return the original URL and hope
- Works against `default_storage` for *read*, but existence checks mix `os.path.exists` on `MEDIA_ROOT` with `default_storage` — brittle on S3

### Galleries vs WordPress Media Library

| | Mezzanine | WordPress Media |
|---|---|---|
| Object model | `GalleryImage` row *or* a FileBrowser path | `attachment` post type, first-class |
| Metadata | One description string | alt, caption, description, EXIF, author |
| Reuse | Per-gallery file | Insert anywhere, tracked |
| Sizes | On-the-fly JPEG/PNG/GIF | Registered image sizes + srcset + webp (core since 5.8/6.x) |
| Editor | Zip + inline + optional FB dialog | Media modal, block editor, focal point (via block) |
| A11y | No alt on gallery `<img>` | Alt is a first-class field |
| DAM features | None | Folders/search via plugins; core has enough for 90% of sites |

**Verdict:** Do not “improve Gallery.” It is a demo content type (the fixture is “cities of the world”). A real media story is a new app.

---

## 3. Accounts — profiles, verification, CMS users vs members

`mezzanine.accounts` is **not installed by default** (commented in the project template). Docs (`docs/user-accounts.rst`) pitch it as public signup so users can comment, buy via Cartridge, and view `login_required` pages.

### What it actually is

A set of function views + one `ProfileForm` over `django.contrib.auth.User`, with an optional OneToOne profile model.

| Surface | Behavior | File |
|---|---|---|
| Signup / login / logout | Session auth, email-or-username login | `views.py`, `core/auth_backends.py` |
| Profile update | Same form as signup; password optional | `views.py` `profile_update` |
| Public profile | Off by default (`ACCOUNTS_PROFILE_VIEWS_ENABLED = False`) | `urls.py` 67–79, `defaults.py` |
| Profile model | `ACCOUNTS_PROFILE_MODEL = "app.Model"` with a User FK | `accounts/__init__.py`, `models.py` auto-create on `post_save` |
| Exclude fields / no username | Settings | `defaults.py`, `forms.py` |
| Custom form class | `ACCOUNTS_PROFILE_FORM_CLASS` | `defaults.py` |
| Email verification | `ACCOUNTS_VERIFICATION_REQUIRED` → inactive user + token link | `views.signup`, `utils/email.py` `send_verification_mail` |
| Staff approval | `ACCOUNTS_APPROVAL_REQUIRED` → inactive + email to `ACCOUNTS_APPROVAL_EMAILS` | `views.py`, `admin.py` `save_model` |
| Approval then verify | Staff activate → user still inactive, gets verify mail | `admin.py` 27–42 |
| Password reset | Token link **logs the user in** and redirects to `profile_update` | `views.password_reset_verify` |
| Password policy | `ACCOUNTS_MIN_PASSWORD_LENGTH` default **6**. No complexity, no `AUTH_PASSWORD_VALIDATORS` | `forms.py` 158–177 |
| Rate limiting | None | — |
| Social / SSO / 2FA / passkeys | None | — |
| Roles / groups UX | None beyond Django admin | — |
| Avatar | Gravatar from email, not an upload | `account_profile.html` |

`MezzanineBackend` (`core/auth_backends.py`) authenticates by username **or** email **or** `(uidb36, token)`. The token path is how both signup-verify and password-reset work. Password-reset therefore *is* a magic-link login. Convenient. Also: a leaked inbox is a live session, and there is no “set a new password before continuing” forced step — the user lands on the profile form where password is optional.

Tests (`tests/test_accounts.py`): create active user when verification off; create inactive + mail + token activates. That is the full account test file.

### Profiles are not members

```31:45:docs/user-accounts.rst
    class MyProfile(models.Model):
        user = models.OneToOneField("auth.User")
        date_of_birth = models.DateField(null=True)
        bio = models.TextField()

    ACCOUNTS_PROFILE_MODEL = "myapp.MyProfile"
```

The profile is a bag of extra fields injected into `ProfileForm` (`forms.py` 121–135). It is not:

- a membership
- a billing customer (Cartridge has its own)
- a role
- a verified identity beyond one email click

Public profile pages render `profile_fields` (verbose name + value) and a Gravatar. There is no privacy granularity (everything not in `ACCOUNTS_PROFILE_FORM_EXCLUDE_FIELDS` is public). Default is “users can only see their own” because public views are off.

### CMS users vs members — one table, two costumes

```46:50:mezzanine/pages/models.py
    login_required = models.BooleanField(
        _("Login required"),
        default=False,
        help_text=_("If checked, only logged in users can view this page"),
    )
```

Middleware (`pages/middleware.py` 75–77): unauthenticated + `login_required` → `redirect_to_login`. That is the entire authorization model for “members.” No groups, no plans, no “this page for subscribers.” Third-party plugins (`mezzanine-protected-pages`, `mezzanine-page-auth`) tried to add group checks; they are not in tree.

Staff (`is_staff` / `is_superuser`) use the same `User`. `SitePermissionUserAdmin` can scope staff to sites. There is no customer/member/staff split like WooCommerce (`customer` role vs `shop_manager` vs `administrator`). A “member” who comments is the same object that, if flagged staff, gets `/admin/`.

Woo users: billing/shipping, order history, downloads, payment methods, role `customer`, integration with memberships/subscriptions plugins. Mezzanine accounts: a signup form and a Gravatar.

### Accounts vs Woo / WP users

| | Mezzanine accounts | WP users + Woo |
|---|---|---|
| Default on? | No | Yes |
| Identity providers | Username/email + password | WP + social via plugins; Woo customers |
| Verification | Optional email token | Optional; Woo has no native verify |
| Approval queue | Yes (nice, actually) | Manual `user_status` / plugins |
| Password policy | Length ≥ 6 | WP 3.7+ strength meter; filterable |
| Reset | Magic-link login | Reset form, then set password |
| Profiles | Optional sidecar model | `usermeta` soup |
| Members vs admins | Same `User`, `is_staff` | Roles/caps |
| Paywall | Boolean `Page.login_required` | Memberships, Paid Memberships Pro, Woo Memberships |
| 2FA / passkeys | No | Plugins (and now WP-core application passwords) |

**The one accounts idea worth keeping:** the three-state onboarding — instant / verify-email / staff-approve (and approve-then-verify). That maps cleanly onto community, corporate, and editorial sites. Everything else should come from django-allauth + django-otp / allauth-mfa + a real entitlements layer.

---

## 4. Ratings, keywords/tags, comments

All three are **generic relations** that inject extra columns onto the host model (`mezzanine/generic/fields.py`). This is the architectural gem.

```133:270:mezzanine/generic/fields.py
class CommentsField(BaseGenericRelation):
    fields = {"%s_count": IntegerField(editable=False, default=0)}

class KeywordsField(BaseGenericRelation):
    fields = {"%s_string": CharField(editable=False, blank=True, max_length=500)}

class RatingField(BaseGenericRelation):
    fields = {
        "%s_count": IntegerField(...),
        "%s_sum": IntegerField(...),
        "%s_average": FloatField(...),
    }
```

Constraints: one of each field class per model (enforced). `related_items_changed` recomputes denormalized values on save/delete. Blog posts use comments + rating (`blog/models.py`); every `Displayable` (pages, blog, Cartridge products) gets keywords via `MetaData.keywords` (`core/models.py` 151). Search reads `keywords_string` (weight 10).

### Keywords / tags

- `Keyword` (slugged, site-scoped via `CurrentSiteManager`) + `AssignedKeyword` (GFK, orderable)
- Admin widget: text input + hidden IDs + AJAX `admin_keywords_submit` + clickable cloud of every existing keyword (`generic/forms.py` `KeywordsWidget`, `views.py` `admin_keywords_submit`)
- Punctuation stripped except dashes; case-insensitive get-or-create
- Unused keywords can be garbage-collected (`KeywordManager.delete_unused`)
- Template tag `keywords_for` on an instance **or** a `"app.model"` string for a **tag cloud** with `weight` (`keyword_tags.py`)
- `keywords_string` max_length **500** — a hard ceiling on “convenient search denorm”

Vs. WordPress tags: WP tags are a taxonomy (`post_tag`) with archive pages, counts, and REST. Mezzanine keywords are a CMS tagging widget plus a search blob. There is no first-class keyword archive view in `generic`. Blog categories are a separate M2M (`BlogCategory`).

Vs. django-taggit: taggit is the ecosystem standard (TPA, Wagtail-adjacent, slugs, through tables). Mezzanine’s version adds: site scoping, ordered assignment, search-string denorm, and a custom admin widget. Those three are worth a thin wrapper around taggit, not a parallel universe.

### Ratings

- Integer from `RATINGS_RANGE` (default `range(1, 6)` i.e. 1–5)
- `Rating` GFK + optional `user` FK
- Anonymous: cookie `mezzanine-rating` stores `"app.label.pk"` tokens; duplicate raises (`RatingForm.clean`)
- Authenticated: `get_or_create`; same value again **deletes** (toggle undo); different value updates
- `RATINGS_ACCOUNT_REQUIRED` can stash POST in session and bounce to login (`generic/views.py` `initial_validation`)
- AJAX returns `{rating_average, rating_count, rating_sum}`
- UI: radio list + “Rate” (`templates/generic/includes/rating.html`)
- Comments themselves can be rated (`COMMENTS_USE_RATINGS`, `ThreadedComment.rating`)

Limits:

- Cookie is trivial to clear or forge — this is not a vote system
- No half-stars, no 0–10, no “helpful?” boolean without changing `RATINGS_RANGE`
- No recaptcha / rate limit on POST `/rating/`
- Recompute loads **all** rating rows into Python (`list(related_manager.all())`) — fine until it isn’t
- Tests (`tests/test_generic.py` `test_rating`) cover the account-required vs cookie semantics

WP: Jetpack likes / core comment karma / Woo product reviews (which are comments with a rating meta). Mezzanine ratings are closer to “star widget for a blog post,” which is a weekend app in 2026.

### Comments

`ThreadedComment` subclasses `django_comments.Comment` (`generic/models.py`):

```17:59:mezzanine/generic/models.py
class ThreadedComment(Comment):
    by_author = models.BooleanField(...)
    replied_to = models.ForeignKey("self", ..., related_name="comments")
    rating = RatingField(...)
```

Behavior:

- Threading via `replied_to`; template recursion with **one query** (`comment_tags.comment_thread` buckets by parent — tested in `test_comment_queries`)
- `is_public` default = `COMMENTS_DEFAULT_APPROVED` (**True**)
- Site FK set on first save
- Duplicate: same name/email/url/object/reply + same calendar day + same text → return existing (`forms.py` 150–164)
- Honeypot: django_comments field, hidden with `.input_id_honeypot {display:none !important;}` (CSS hide, not `autocomplete=off` / `tabindex=-1` / `aria-hidden`)
- Akismet via same `is_spam` as forms; spam → redirect, no save
- Notification emails to `COMMENTS_NOTIFICATION_EMAILS`
- Commenter name/email/url cookies, 90 days (`views.comment`)
- `COMMENTS_ACCOUNT_REQUIRED` uses the same session-stash-and-login pattern as ratings
- Gravatar; `by_author` if `request.user == obj.user`
- Unapproved / removed can still occupy a slot with a placeholder (`COMMENTS_UNAPPROVED_VISIBLE` / `REMOVED_VISIBLE`, both default True)
- Filter hook `COMMENT_FILTER` (default `linebreaksbr` + `urlize`)
- Staff dashboard widget `recent_comments`
- Admin: no add (crashes), no bulk delete, no flag (`generic/admin.py`)
- Missing POST data → **400** (bot defense, tested)

**Disqus escape hatch:** if `COMMENTS_DISQUS_SHORTNAME` is set, the built-in form is replaced by the Disqus embed, with optional SSO signed by HMAC-SHA1 (`disqus_tags.py`). SSO payload is `{id, username, email}`. Disqus keys are editable settings.

Not present: subscriptions (“notify me of replies”), Markdown/CommonMark by default, moderation queue UX beyond Django admin, user blocking, Akismet *training* (spam/ham submit), imported comment identity, ActivityPub/webmentions, reactions, edit window, soft-delete that preserves threading beyond the placeholder.

### Comments vs Jetpack / WP

| | Mezzanine built-in | WP + Jetpack Comments |
|---|---|---|
| Threading | Yes, efficient | Yes |
| Moderation | `is_public` / `is_removed` | Hold / spam / trash / approved + Akismet training |
| Spam | Akismet fail-open + honeypot CSS | Akismet first-class |
| Identity | Cookies or accounts or Disqus SSO | WP user, WP.com, social |
| Subscriptions | No | Jetpack “notify me” |
| Hosting | In-process Django | Local or Jetpack-hosted |
| Ratings/likes | Star ratings on comments | Likes (Jetpack) |
| Federation | No | No (still) |
| Default approve | **Yes** | No (usually) |

Default-approve-plus-fail-open-Akismet is a spam cannon. Any modernization that keeps in-process comments must flip `COMMENTS_DEFAULT_APPROVED` to False and add a real honeypot + rate limit before any redesign.

---

## 5. Differentiator vs replace-with-best-in-class

### Worth modernizing (the coupling is the product)

1. **Form as a `Page`.** Draft, schedule, menu, slug, `login_required`, rich intro + rich thank-you, per-site. No Django form library gives you this without you reinventing a CMS. **Keep the content type; replace the field/entry engine.**

2. **Generic relation fields with denormalized counters.** `CommentsField` / `KeywordsField` / `RatingField` are a clean CMS API: one line on the model, admin widget, search integration, template tags. Reimplement the *backends*; do not force every content type to know about taggit/comments-xtd internals.

3. **Staff-approve + email-verify onboarding.** Rarely done well in CMS land. Keep the state machine; stop writing auth views.

4. **Zip-import as an ingestion verb.** Editors love it. It belongs on a DAM asset collection, not on a Gallery page model.

5. **Entries filter UI** (include columns, type-aware filters, CSV). The *UX* is closer to Gravity Forms than most Django admin list filters. Rebuild on a relational/JSON entry store, don’t run filters in a Python loop.

### Replace with best-in-class Django apps

| Mezzanine piece | Replace with | Why not modernize in place |
|---|---|---|
| `accounts` views/forms/backend | **django-allauth** (+ mfa) | Social, email verification, rate limits, password reset done correctly, adapter API. Mezzanine’s token-login reset is a security smell. |
| Password policy | Django `AUTH_PASSWORD_VALIDATORS` | Length-6 is not a policy. |
| Keywords store | **django-taggit** (wrapped by `KeywordsField`) | Ecosystem, migrations, slug collisions solved. Keep widget + `keywords_string` if search needs it. |
| Built-in comments | **django-comments-xtd** *or* drop-in hosted (or none) | xtd already does threading, confirm-by-email, follow-up, flags — on the same `django_comments` substrate. Or stop hosting comments. |
| Ratings | **django-star-ratings** or a 80-line HTMX widget | Cookie voting is not a product. |
| FileBrowser “Media Library” | **django-filer** or **Wagtail images** (if the new CMS goes that way) or a purpose-built Asset model | FB-safe is a jQuery-UI filesystem. It cannot grow into a DAM. |
| Gallery page | A thin “collection” content type over the DAM | Do not keep `GalleryImage.file` as the source of truth. |
| `{% thumbnail %}` | **easy-thumbnails** / **sorl** / **django-versatileimagefield** / imgproxy | Need WebP/AVIF, async, remote storage, srcset. |
| Forms engine | New typed-block builder (see §6). Interim: **django-formtools** wizards + a JSON schema renderer. Not django-forms-builder — that’s this code’s parent. | Integer enums + EAV cannot express conditionals or consent. |
| Disqus integration | Delete or isolate | Disqus is a GDPR/performance liability; keep only if a site already depends on it. |
| Gravatar as identity | Optional adapter | Fine as fallback, not as the profile picture system. |
| Akismet-only spam | **django-honeypot** + Turnstile/hCaptcha + Akismet + fail-closed logging | Shared `SPAM_FILTERS` hook is good; the default filter is not. |

### Do not replace (yet)

- `Page.login_required` + middleware redirect — this is the seed of memberships.
- `fields_for` / `errors_for` / `Html5Mixin` — small, useful; just fix a11y.
- Form `form_valid` / `form_invalid` signals — the right extension point for webhooks.
- `ACCOUNTS_PROFILE_MODEL` injection — allauth has adapters; keep a documented profile convention.

### Explicit non-goals (do not build)

- A Gravity Forms clone with pricing fields and Stripe inside `mezzanine.forms`
- A WooCommerce customer area inside `mezzanine.accounts`
- Another star-rating jQuery plugin
- Continuing to fork FileBrowser / Grappelli to get a media library

---

## 6. Revolutionary module ideas

These are not “v2 of the same app.” They are the products a 2026 Mezzanine would be *for*.

### 6.1 Form builder as typed blocks

**Thesis:** A form field is a content block. A form is a page whose body *is* a block stream. Entries are typed JSON, not EAV strings.

Sketch:

```
FormPage(Page):
    intro: richtext
    thank_you: richtext
    notify: [NotificationRule]          # routed, not one CC string
    store_policy: enum(store, email_only, both) + retention_days
    blocks: Stream[FieldBlock]

FieldBlock (typed, versioned):
    TextBlock | EmailBlock | ChoiceBlock | FileBlock |
    ConsentBlock | AddressBlock | RepeaterBlock | PaymentBlock |
    GroupBlock (fieldset) | PageBreakBlock

Each block:
    id: uuid (stable across edits — unlike today's field_id int)
    required: bool
    visible_when: Expr | None           # conditional logic
    pii_class: enum(none, personal, special)
    attrs: autocomplete, inputmode, autocomplete tokens

FormSubmission:
    form_id, submitted_at, locale
    actor: FK User | null
    ip_hash, user_agent_hash            # not raw IP if policy says so
    consent: JSON                       # copies of what was agreed
    payload: JSONB                      # typed by block schema
    files: M2M Asset                    # DAM objects, not paths
    status: received | spam | deleted
```

Why this is revolutionary *here* and not just “Wagtail forms”:

- The block stream **is** the page body. Editors already think in the page tree. Wagtail forms are a separate snippet; Gravity Forms is a plugin. Mezzanine can make “a form” as native as “a rich text page.”
- Conditionals compile to a small JSON logic tree the browser and server both evaluate (same schema, one source of truth).
- Consent is a block type, not a checkbox someone might add. Submissions without a passed `ConsentBlock` are rejected. Export/erase walks `pii_class`.
- File blocks produce `Asset` rows (see 6.2), with MIME allowlists, max size, virus-scan hook, and staff-only default ACL.
- Notifications are rules: “if `topic == Support` email support@…”. Today’s single `email_copies` is a field; it should be a workflow.
- Accessibility falls out of block renderers: every block owns its `fieldset`, `aria-describedby`, error linking. HTML5 is on. `FORMS_USE_HTML5 = False` dies.
- Entries stay queryable (`payload__email.keyword`) because JSONB is not a 2000-char `CharField`.

Migration path: a management command that reads `Field` + `FieldEntry` and emits a stream + JSON payload. Integer type 1..15 maps onto block classes. Hidden+templated defaults become `default_expr`.

### 6.2 Media as a first-class DAM

**Thesis:** Kill the dual-brain (Gallery rows vs FileBrowser paths). One `Asset` model. Galleries become queries. Thumbnails become renditions.

```
Asset:
    id, site, hash (perceptual + sha256)
    kind: image | video | audio | document | font | other
    original: Storage path
    title, alt, caption, credit, license, recorded_at
    width, height, duration, bytes, mime
    focal_x, focal_y
    blurhash | thumbhash
    dominant_color
    exif: JSON (stripped of GPS unless opted in)
    usage_count (maintained like CommentsField)
    folders/collections: M2M
    tags: KeywordsField (the pattern we keep)

Rendition:
    asset, pipe (e.g. "webp@80:1600w"), width, height, bytes, url
    generated_at, storage_path

Ingest verbs:
    upload, zip_import (today’s gallery UX), url_fetch, paste
    on ingest: sniff MIME, strip dangerous payloads, enqueue renditions
              (AVIF, WebP, jpeg fallback, 320/640/1280/1920, blurhash)
```

Front-end contract:

```html
<img
  alt="{{ asset.alt }}"
  src="{{ asset.rendition('jpeg@80:1280w').url }}"
  srcset="..."
  width="..." height="..."
  style="background: url('data:image/svg+xml,...blurhash...') center/cover"
  loading="lazy" decoding="async">
```

Gallery page becomes:

```
GalleryPage(Page):
    collection: FK Collection | inline AssetOrder[]
```

Why this beats WP Media *and* django-filer:

- **blurhash / thumbhash + AVIF** as defaults, not plugins
- **Usage index** (“this image is on 14 pages, 1 blog, 3 forms”) — WP still pretends attachments know their parents; filer is a folder tree
- **Focal point** stored once, all renditions honor it (thumbnail’s `left`/`top` today is a template-tag argument, not data)
- **Alt is required** for `kind=image` before publish — make the a11y failure a validation error, not a template omission
- Form uploads and gallery zips and TinyMCE inserts all create `Asset` rows. One quarantine, one virus hook, one GDPR erase.

`{% thumbnail %}` becomes a compatibility wrapper that asks the DAM for a rendition.

### 6.3 Memberships + paywalls

**Thesis:** `Page.login_required` is a boolean because 2012 sites had “members” or they didn’t. 2026 sites have plans, metered content, time-boxed previews, and staff previews.

```
Plan: name, site, price_ref (optional; payments are a plugin), entitlements[]
Entitlement: resource_type (page, collection, form, download, feature_flag),
             matcher (path prefix, tag, content_type),
             verbs (view, submit, download, comment)
Membership: user, plan, status, valid_from, valid_to, source (manual, stripe, invite)
Gate: attached to Displayable (replaces login_required)
      mode: public | login | plan_any | plan_all | preview(n_paragraphs)
```

Consequences:

- Accounts become **identity** (allauth). Memberships become **authorization**. Staff remain Django perms. The current collapse of all three into `User.is_active` ends.
- Forms can require a plan to *submit* (lead magnets, applications) without being “login_required pages.”
- Comments can require a plan (`COMMENTS_ACCOUNT_REQUIRED` is a boolean today).
- Cartridge, if it lives, sells a `Plan`, not a parallel customer table.
- Editorial preview (“first 200 words, then gate”) is a `Gate.mode = preview`, not a new page type.

This is the Woo Memberships / MemberPress / Ghost members move — except the gate hangs on the same `Displayable` every Mezzanine object already inherits. That is a differentiator WP cannot match without a plugin stack.

Invite codes (`mezzanine-invites`, third-party) and group-protected pages become first-class `Membership.source = invite` and entitlements.

### 6.4 Comments as an activity protocol

**Thesis:** Stop treating comments as rows that belong to us. Treat them as **activities** that *may* be stored here.

```
Activity:
    verb: comment | reply | rate | mention | like
    actor: Person (local User | remote actor URI)
    object: any Displayable (GFK — keep CommentsField)
    target: parent Activity | null
    content: sanitized HTML / Markdown AST
    published, updated
    visibility: public | members | staff
    origin: native | webmention | activitypub | import
    external_uri: unique
    moderation: pending | approved | rejected | spam
```

Adapters:

- **Native** renderer: today’s threaded UI, but HTMX, with confirm-by-email (steal from comments-xtd) and a real honeypot.
- **Webmention** receiver: other sites reply to a post URL; they show up as activities with `origin=webmention`. This is the indie-web feature WP still half-does via plugins.
- **ActivityPub** optional: the blog post is a `Note`/`Article`; replies from Mastodon are comments. Outbound: “this site commented” can federate.
- **Import** adapter: Disqus XML, WP `wp:comment`, today’s `ThreadedComment`.

Ratings become `verb=rate` (or `like`) with a value. The denormalized `rating_average` columns stay — the field pattern is the CMS API; the store is activities.

Why this is not science-project:

- The GFK hook already exists. `CommentsField.related_items_changed` already maintains a count. Point it at `Activity.objects.filter(verb__in=..., moderation=approved)`.
- Default-approve dies. Federation *requires* a moderation queue; building that queue fixes the spam cannon.
- Sites that want zero local comments set `origin` allowlist to empty and keep Disqus/none.
- GDPR erase is “delete activities where actor.email = …” — one table, not comments + ratings + form entries.

---

## Security and compliance residual (cross-cutting)

These are not theoretical. They are in the code paths above.

| Issue | Where | Severity |
|---|---|---|
| Password min length 6, no validators | `accounts/defaults.py`, `forms.py` | High |
| Password reset = instant login | `accounts/views.py` `password_reset_verify` | High |
| Form uploads: no type/size policy; empty `FORMS_UPLOAD_ROOT` | `forms/forms.py`, `defaults.py` | High |
| Akismet over HTTP, fail-open | `utils/views.py` | Medium |
| Forms/comments spam discarded as fake success, no log | `forms/page_processors.py`, `generic/views.py` | Medium |
| Comments default approved | `COMMENTS_DEFAULT_APPROVED = True` | High (ops) |
| Honeypot only CSS-hidden | `generic/includes/comments.html` | Low–Med |
| Rating cookie forgeable; `/rating/` unthrottled | `generic/forms.py`, `urls.py` | Low |
| Gallery `<img>` without alt | `galleries/templates/pages/gallery.html` | Med (a11y/legal) |
| No consent field, no retention, no subject export | forms + comments + accounts | High (GDPR) |
| `FieldEntry.field_id` not an FK | `forms/models.py` | Low (integrity) |
| Token in verify URL, `next=` open redirect surface | `utils/email.py` (relies on `next_url`) | Needs review |
| Disqus SSO shares email with a third party | `disqus_tags.py` | Med (privacy) |

None of these require a rewrite to *mitigate*. They do require a rewrite to *stop being the kind of CMS that has them*.

---

## Test coverage vs product claims

| Claim (README / docs) | Test reality |
|---|---|
| Drag-and-drop HTML5 forms + CSV | Render/POST 200; custom email type; i18n button. **No CSV test. No file-upload test. No spam test.** (`tests/test_forms.py`) |
| Accounts + email verification | Signup active/inactive + token. **No approval flow, no profile model, no reset, no lockout.** (`tests/test_accounts.py`) |
| Galleries + zip import | Zip → images+descriptions; 24×24 thumb. **No invalid zip, no alt, no FB integration.** (`tests/test_galleries.py`) |
| Comments / ratings / keywords | Ratings math, comment-rating denorm, query count, keyword string, delete_unused, 400 on empty comment, widget decompress. **No spam, no Disqus, no threading POST, no cookie forge.** (`tests/test_generic.py`) |

The tests document what the maintainers still believe matters: the happy path of a demo site. They do not document a product.

---

## Recommended disposition (one page for the rest of the council)

```
mezzanine.forms        → freeze API, design FormPage + typed blocks (6.1)
mezzanine.galleries    → keep as a thin collection view over DAM; delete zip-on-the-page-model
filebrowser_safe       → exit ramp; do not fork further
mezzanine.accounts     → delete views; adopt allauth; keep approval-state + profile convention
Page.login_required    → generalize to Gate / Membership (6.3)
mezzanine.generic.fields → KEEP; this is core CMS kit
Keyword / AssignedKeyword → wrap taggit
ThreadedComment        → Activity adapter or comments-xtd; flip default-approve
Rating                 → Activity verb or a 80-line app
{% thumbnail %}        → rendition facade
SPAM_FILTERS           → keep hook; replace default; fail closed; log
```

**If the project has one release of courage:** ship DAM + typed form blocks + allauth, and leave comments as an adapter. That trio is a CMS. The current four apps are a museum of how Django shops out-featured WordPress in 2012 — and then stopped.

---

*Sources: in-tree modules under `mezzanine/{accounts,forms,galleries,generic}/`, `mezzanine/core/{fields,forms,auth_backends,models,defaults,templatetags}`, `mezzanine/utils/{views,email,conf}.py`, `mezzanine/pages/{models,middleware,defaults}.py`, `mezzanine/blog/models.py`, `docs/{user-accounts,overview,admin-customization,utilities,settings}.rst`, `README.rst`, `tests/test_{accounts,forms,galleries,generic}.py`, `project_template/.../settings.py`. No third-party runtime was executed.*
