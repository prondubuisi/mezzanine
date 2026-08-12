# Security, Auth, Multi-Tenancy, Compliance
## Byzantine Council — General SECURITY
## Repo: Mezzanine CMS (`mezzanine/__init__.py` version `9999dev0`)

**Scope.** Code-backed review of auth, HTML sanitization, comments, uploads, multi-site isolation, CSRF/redirects, dependency surface, and 2026-era gaps versus WordPress. Public CVEs checked against this tree. The Mezzanine repo was not modified.

---

## EXECUTIVE VERDICT

**Mezzanine is a 2010-era Django CMS that inherited Django’s good defaults (CSRF middleware, ORM parameterization, HttpOnly sessions) and then spent a decade adding its own attack surface without a hardening program.** It is safer than a raw WordPress install *only* because it is less popular. It is *not* safer than a hardened WordPress site, and it is not ready for 2026 multi-tenant or compliance use.

Three 2025 CVEs exist. **Two are still present in this tree.** The third (blog-body `<script>`) is theoretically blocked by default bleach-on-save, but the control is admin-disableable, not re-applied on render, and barely tested.

| Finding | Severity | Status in this tree |
|---|---|---|
| CVE-2025-6050 — stored XSS via `displayable_links_js` titles (JSON served as `text/html`) | High (admin XSS) | **UNPATCHED** |
| CVE-2025-29573 — stored XSS via unsanitized form-upload filenames | High (admin XSS) | **UNPATCHED** |
| CVE-2025-50481 — stored XSS in blog post body (`<script>` via TinyMCE source) | Medium (PR:H) | Default bleach HIGH *should* strip; control is fragile |
| Password-reset link logs the user in | High | Present by design |
| Form-field `default` rendered as a Django template (SSTI) | High (staff→RCE) | Present |
| Media library shared across tenants | High (isolation fail) | Documented, unfixed |
| `RICHTEXT_FILTER_LEVEL` editable in admin → “No filtering” | High | Present |
| Drafts visible to *any* `is_staff` by URL, no signed preview | Medium | Present |
| Min password length 6; no 2FA/passkeys/SSO/CSP/audit | High (2026 gap) | Present |
| Django 2.2 still declared supported; jQuery 3.4.1 + jQuery UI 1.12.1 + TinyMCE 4 | High (EOL) | Present |

**WordPress comparison, without the marketing.** WordPress is attacked constantly *and* has Wordfence, Sucuri, WP-CLI hardening, capability roles, application passwords, 2FA plugins, signed updates, and a CVE-to-patch machine measured in days. Mezzanine has bleach, a site FK, and a GitHub issue tracker. That is not a hardening ecosystem. It is a prayer.

**Ship / no-ship.** Do not put this on the public internet as a multi-tenant CMS, a regulated property, or anything that accepts untrusted HTML from “trusted staff.” Single-site brochureware behind SSO and a WAF is the only honest deployment shape.

---

## 1. Auth model (Django users + extras)

### What exists

Mezzanine does **not** invent a user table. It uses `django.contrib.auth` (`AUTH_USER_MODEL`) and layers:

| Layer | File | What it does |
|---|---|---|
| `MezzanineBackend` | `mezzanine/core/auth_backends.py` | Login by **username or email** + password, **or** `uidb36` + Django `default_token_generator` |
| `SitePermission` | `mezzanine/core/models.py` (`SitePermission`) | `OneToOne(User)` + M2M `sites`. Used *instead of* `is_staff` for admin/inline-edit *after* the user is already staff |
| `SitePermissionMiddleware` | `mezzanine/core/middleware.py` | Sets `request.user.has_site_permission`; **logs the user out** if staff hits `/admin` without a row for `current_site_id()` |
| `mezzanine.accounts` | `mezzanine/accounts/` | Optional signup / profile / password-reset. **Not** in the default `INSTALLED_APPS` of the project template |
| `Ownable` | `mezzanine/core/models.py` | `user` FK; `is_editable` = owner or superuser. Admin changelist filter only — not a capability system |

`MezzanineBackend.authenticate` (`mezzanine/core/auth_backends.py`):

```24:48:mezzanine/core/auth_backends.py
    def authenticate(self, *args, **kwargs):
        if kwargs:
            username = kwargs.pop("username", None)
            if username:
                username_or_email = Q(username=username) | Q(email=username)
                password = kwargs.pop("password", None)
                try:
                    user = User.objects.get(username_or_email, **kwargs)
                except User.DoesNotExist:
                    pass
                else:
                    if user.check_password(password):
                        return user
            else:
                # uidb36 + token path — same token as password reset
                ...
                if default_token_generator.check_token(user, token):
                    return user
```

### Extras that look like features and behave like bugs

1. **Token login is a full session, not a password-change ticket.**
   - Signup verify (`accounts/views.py` `signup_verify`) authenticates with `is_active=False`, flips `is_active`, `auth_login`s, honors `next`.
   - Password reset verify (`password_reset_verify`) authenticates with `is_active=True`, **`auth_login`s, redirects to `profile_update`**. There is no “set a new password first” step. Steal the email link → you *are* the user. Django’s own `PasswordResetConfirmView` (wired in `mezzanine/core/urls.py` for admin) does this correctly; Mezzanine accounts does not.

2. **Password policy is 2011.** `ACCOUNTS_MIN_PASSWORD_LENGTH` default is **6** (`mezzanine/accounts/defaults.py`). No complexity, no breach-list check, no hook to `AUTH_PASSWORD_VALIDATORS`. `createdb` still seeds `admin` / `default` (`mezzanine/core/management/commands/createdb.py`). Middleware warns if that pair is still live — it does not force a change.

3. **User enumeration is free.**
   - Login: `"Invalid username/email and password"` vs `"Your account is inactive"`.
   - Reset: `"Invalid username/email"` if no active user.
   - Signup: `"This email is already registered"` / `"This username is already registered"`.

4. **No lockout, no rate limit, no 2FA, no WebAuthn, no SSO.** Accounts is a form + email token. Disqus SSO (`mezzanine/generic/templatetags/disqus_tags.py`) HMAC-signs `{id, username, email}` for a third-party comment vendor. That is the only “SSO” in the tree, and it ships user PII to Disqus.

5. **Roles are a boolean plus Django’s global perms.**
   - `is_superuser` → every site, every perm.
   - `is_staff` + `SitePermission` for current site → admin.
   - Django model perms (`blog.change_blogpost`, etc.) are **global**, not per-site. Grant “change blog” once, switch site, same grant applies.
   - `SitePermission` is `OneToOne` — you cannot attach different role sets to different tenants.
   - If `SitePermissionMiddleware` is missing, `has_site_permission()` **falls back to `user.is_staff`** (`mezzanine/utils/sites.py`). There is a system check (`mezzanine/core/checks.py` `W04`), not a hard fail.

6. **Logout is a GET** (`accounts/urls.py` → `views.logout`). CSRF-logout a victim into an attacker-controlled `?next=` (host-checked, but still a session kill + UX trap).

7. **Profile URLs accept `username` as `.*`** (`accounts/urls.py`). Fine for Django path matching; sloppy for caching and logging.

**Net:** this is Django auth with an email-or-username convenience backend and a site-membership flag. It is not an identity platform.

---

## 2. HTML sanitization — is TinyMCE content actually sanitized on save?

### The intended design

Yes — **on model-field `clean()`, not on render.**

```50:54:mezzanine/core/fields.py
    def clean(self, value, model_instance):
        """
        Remove potentially dangerous HTML tags and attributes.
        """
        return escape(value)
```

`escape()` (`mezzanine/utils/html.py`) is `bleach.clean(...)` with `strip=True`, `RICHTEXT_ALLOWED_TAGS` / `_ATTRIBUTES` / `_STYLES`, plus `tel` on protocols. Default filter level is `RICHTEXT_FILTER_LEVEL_HIGH` (`mezzanine/core/defaults.py`). TinyMCE is explicitly told *not* to help:

```83:83:mezzanine/core/static/mezzanine/js/tinymce_setup.js
        valid_elements: "*[*]"  // Don't strip anything since this is handled by bleach.
```

On the public site, content is piped through `|richtext_filters` (`blog/templates/blog/blog_post_detail.html`, `pages/richtextpage.html`, etc.). Default `RICHTEXT_FILTERS` is **only** `mezzanine.utils.html.thumbnails` — BeautifulSoup rewrite of `<img src>` to thumbnail paths — then `mark_safe`. **Bleach does not run again.**

### Why this is not “sanitized”

1. **Save-time only, form-path only.** `Model.save()` does not call `full_clean()`. Admin `ModelForm` does. Shell, management commands, WordPress/blog importers, `queryset.update()`, fixtures, and any future API will persist raw HTML that the template will then `|safe`.

2. **The kill switch is in the admin UI.** `RICHTEXT_FILTER_LEVEL` is `editable=True` with a “No filtering” choice that “allow[s] any code to be entered by staff members, including script tags” (setting description in `defaults.py`). Any staff who can open Settings can disable the only XSS control, then persist `<script>` forever. Render will still `|safe` it.

3. **The HIGH whitelist is not a sanitizer policy; it is a 2012 HTML soup.** Allowed tags include `form`, `input`, `button`, `textarea`, `select`, `iframe` is added at LOW, plus `object` / `embed` / `classid` / `data` at LOW. Allowed attributes include `style`, `href`, `src`, `id`, `class`, `action`, `form`. That is a CSRF gadget kit and a phishing kit even when `<script>` dies.

4. **Tests do not prove the property.** `tests/test_core.py` `test_escape` asserts `escape("<foo><div></div></foo>") == "<div></div>"`. No `<script>`, no `onerror`, no `javascript:`, no mXSS, no `<math>`, no mutation via BeautifulSoup `thumbnails()`.

5. **`richtext_filters` will `mark_safe` a filter that forgot to.** The `SafeText` check is a `FutureWarning`, not an exception (`mezzanine/core/templatetags/mezzanine_tags.py`).

6. **Adjacent `|safe` sinks that never see bleach:**
   - `{{ blog_post.description_from_content|safe }}` (`blog_post_list.html`) — OK *if* `gen_description` rebuilt it from bleached content.
   - `{{ result.description|truncatewords_html:20|safe }}` (`search_results.html`) — `description` is a plain `TextField`. Uncheck “Generate description”, type HTML, get stored XSS on search.
   - `{{ tweet.text|safe }}` (`twitter/tweets.html`).
   - Keyword widget builds `<a>` from `Keyword.title` and `mark_safe`s it (`generic/forms.py`). Titles come from staff, but they are not escaped.

### CVE-2025-50481 — still present *as a class of bug*

Public advisory: stored XSS at `/blog/blogpost/add` in **v6.1.0**, payload `<script>alert(document.location)</script>` in TinyMCE source, CVSS 4.8 (`PR:H/UI:R/S:C`). Session cookie is HttpOnly (PoC author noted hijack failed).

Against *this* tree, that exact payload should be stripped by `RichTextField.clean()` **if** the save goes through a `ModelForm` **and** `RICHTEXT_FILTER_LEVEL != NONE`. There is no 6.1.1-style extra hardening (render-time bleach, TinyMCE `valid_elements` lockdown, CSP). The public PoC is a staff member pasting HTML into a field the product advertises as HTML. The product’s own setting page tells you how to turn the defense off.

**Treat CVE-2025-50481 as unfixed in spirit.** The control that “fixes” it is optional, skippable, and not on the read path.

### CVE-2025-6050 — **still present, confirmed**

v6.1.1 (2025-06-04) shipped `[security] fix XSS in admin` (`898630d`). This tree’s `displayable_links_js` is the pre-patch code:

```186:186:mezzanine/core/views.py
    return HttpResponse(dumps([link[1] for link in sorted_links]))
```

- No `JsonResponse`, no `content_type="application/json"`. Django `HttpResponse` defaults to **`text/html`**.
- Titles are interpolated into JSON with `str(title)` and dumped. A title of `</script><script>alert(1)</script>` is an XSS when a browser navigates the URL.
- The view has **no** `@staff_member_required`. It is mounted at `/admin/displayable_links.js` via `LazyAdminSite.urls` (`mezzanine/boot/lazy_admin.py`) **without** `admin_view()`. Sibling views (`static_proxy`, `admin_keywords_submit`) are decorated; this one is not.
- `url_map(for_user=request.user)` leaks draft titles to any staff session, published titles to the world.

A contributor with `blog.add_blogpost` (or any `Displayable`) plants a title; a superuser opens TinyMCE or the raw URL; that’s admin XSS → session-adjacent actions (the CSRF token is already in `window.__csrf_token` on every admin page — `admin/base_site.html`).

---

## 3. Comments / spam (Akismet)

### Pipeline

`mezzanine.generic` wraps `django_comments`. POST `/comment/` → `initial_validation` → `ThreadedCommentForm` → `is_spam()` → save.

Defaults (`mezzanine/generic/defaults.py`):

| Setting | Default | Problem |
|---|---|---|
| `COMMENTS_DEFAULT_APPROVED` | **`True`** | Public immediately |
| `COMMENTS_ACCOUNT_REQUIRED` | `False` | Anonymous comments |
| `COMMENTS_UNAPPROVED_VISIBLE` | `True` | “Waiting” placeholders still render |
| `COMMENT_FILTER` | `None` | Falls back to `urlize` + `linebreaksbr` with `autoescape=True` — **this part is actually fine** |
| `SPAM_FILTERS` | `(is_spam_akismet,)` | No-op unless `AKISMET_API_KEY` is set |

Comment HTML is **escaped** on render (`comment_filter` in `generic/templatetags/comment_tags.py`). That is one of the few things done correctly. Do not “improve” it by running comments through `richtext_filters`.

### Akismet is fail-open and HTTP

`is_spam_akismet` (`mezzanine/utils/views.py`):

- Returns `False` if no API key.
- Returns `False` on **any** exception (`urlopen` timeout, DNS, HTTP 500).
- Posts to **`http://<key>.rest.akismet.com/1.1/comment-check`** — cleartext, MITM can flip spam/ham.
- Trusts `HTTP_X_FORWARDED_FOR` first (`ip_for_request`). Any client can spoof the IP Akismet sees unless a reverse proxy overwrites the header.
- Field mapping is heuristic (“first field labelled Name”, first `EmailField`, first `Textarea`). Easy to miss the actual body.

Disqus is the other escape hatch. That moves XSS/spam to a third party and adds the SSO HMAC above.

### Other comment/rating issues

- **`replied_to` is taken from raw POST** (`generic/forms.py` `comment.replied_to_id = self.data.get("replied_to")`) — not validated to belong to the same `content_object`. Thread hijack / orphan replies.
- Duplicate check is same-day + same text + same name/email/url. Trivial to bypass.
- Ratings for anonymous users are a cookie (`mezzanine-rating`). Delete the cookie, vote again. Authenticated ratings are `get_or_create` by user — better, still no rate limit.
- `Rating` / `AssignedKeyword` are **not** `SiteRelated`. Comments are (via `Comment.site` + `CommentManager(CurrentSiteManager)`).
- Staff see unapproved/removed comment bodies (`comment_tags.py` uses `parent.comments.all()` for `is_staff`). Combined with any admin XSS, that’s a data-exfil channel.

**Net:** comments are XSS-safer than blog HTML. They are not spam-safe by default. Auto-approve + no captcha + fail-open Akismet is how you get a comment spam landfill.

---

## 4. File upload / galleries risks

### Forms app (user-submitted files) — worst of the three

`FormForForm.save` (`mezzanine/forms/forms.py`):

```216:216:mezzanine/forms/forms.py
                value = fs.save(join("forms", str(uuid4()), value.name), value)
```

- UUID directory is good. **Original filename is preserved.**
- No extension allowlist, no content sniff, no AV, no size cap beyond `FORMS_FIELD_MAX_LENGTH` (which is for the stored path string, 2000 chars).
- `FORMS_UPLOAD_ROOT` default is `""` (`forms/defaults.py`). `FileSystemStorage(location="")` is “wherever the process cwd is.” Misconfigure this and uploads land in the project tree.
- Files are **emailed as attachments** to `email_copies` (`forms/page_processors.py`) — staff inboxes become malware dropboxes.

**CVE-2025-29573 — still present.** Admin “View Entries” builds:

```430:435:mezzanine/forms/forms.py
            if field_entry.value and field_id in file_field_ids:
                url = reverse("admin:form_file", args=(field_entry.id,))
                field_value = self.request.build_absolute_uri(url)
                if not csv:
                    parts = (field_value, split(field_entry.value)[1])
                    field_value = mark_safe('<a href="%s">%s</a>' % parts)
```

`split(...)[1]` is the attacker-controlled filename. It is interpolated into HTML and `mark_safe`d. Filename `"><img src=x onerror=alert(1)>.pdf` is stored XSS every time an admin views entries. That is the CVE. No `format_html`, no `escape`.

**`file_view` is worse than the CVE writeup.**

```188:198:mezzanine/forms/admin.py
    def file_view(self, request, field_entry_id):
        field_entry = get_object_or_404(FieldEntry, id=field_entry_id)
        path = join(fs.location, field_entry.value)
        response = HttpResponse(content_type=guess_type(path)[0])
        with open(path, "r+b") as f:
            response["Content-Disposition"] = "attachment; filename=%s" % f.name
```

- No check that `FieldEntry` belongs to a `Form` on the **current site**. Staff on tenant A who can guess/enumerate `field_entry_id` downloads tenant B’s uploads. `admin_view` is “is staff,” not “has this object.”
- `Content-Disposition` uses `f.name` (full filesystem path) unsanitized — header injection if a filename contains `\r\n`.
- `content_type` is guessed from the attacker’s filename. `file.html` served without `attachment` discipline on some browsers is another XSS. They set `attachment`, which helps, then put the raw path in the header, which does not.

### Galleries / zip import — better, not good

`BaseGallery.save` (`mezzanine/galleries/models.py`):

- Takes `os.path.split(name)[1]` — **zip-slip path traversal is blocked.**
- `PIL.Image.open` + `verify()` — non-images skipped. (Pillow CVEs still apply.)
- No zip-bomb limits (entry count, uncompressed size, compression ratio).
- No pixel-bomb limits (100k×100k PNG).
- Images land under a **shared** media tree (`GALLERIES_UPLOAD_DIR`, often filebrowser’s directory). See §5.

### filebrowser_safe media library

Default project pulls `filebrowser_safe` and `grappelli_safe` as `OPTIONAL_APPS` (`project_template/.../settings.py`). The media library is the admin upload surface for TinyMCE. Historical `filebrowser_safe` CVEs (path traversal) were bumped in ancient CHANGELOG entries; this repo just pins `>= 1.1.1` and hopes. There is no content-type policy, no SVG-as-XSS policy, no separate download domain.

### `static_proxy` (`/admin/asset_proxy/`)

`@staff_member_required`, intended to serve TinyMCE plugin HTML same-origin. It strips a host/`STATIC_URL`/`/` prefix and `finders.find`s the rest. `finders.find` is the real guard. Tests only check happy paths (`tests/test_core.py`). A staff XSS that points `?u=` at unexpected static paths is the residual risk, not unauth LFI.

### Thumbnail tag

`{% thumbnail %}` (`mezzanine_tags.py`) writes under `MEDIA_ROOT / image_dir / .thumbnails /`. It trusts the `image_url` argument. Used on staff-supplied `FileField`s this is fine; used on unsanitized HTML `src` via `thumbnails()` it is an interesting “make me a file” primitive if `src` can leave `MEDIA_URL`. The function bails unless `MEDIA_URL` is in the HTML, then only rewrites `src` that *startswith* `MEDIA_URL`. Not a traversal on its own.

---

## 5. Multi-site isolation (can tenant A see tenant B?)

**Short answer: yes, in several places that matter.** Mezzanine’s multi-tenancy is “a `site` FK and a manager filter,” not a tenant boundary.

### What is isolated

`SiteRelated.save` stamps `current_site_id()` (`mezzanine/core/models.py`). `CurrentSiteManager.get_queryset` always adds `site_id = current_site_id()` (`mezzanine/core/managers.py`). Pages, blog posts, keywords, comments (via `CommentManager`), and most `Displayable`s are filtered.

`current_site_id()` pipeline (`mezzanine/utils/sites.py`, documented in `docs/multi-tenancy.rst`):

1. `override_current_site_id` thread-local
2. `request.session["site_id"]` — **admin site switcher**
3. `Site.objects.get(domain__iexact=request.get_host())` (cached)
4. `MEZZANINE_SITE_ID` env
5. `settings.SITE_ID`

### What is *not* isolated

The docs themselves admit it:

> “these sites will share some resources, such as **the media library**, while there is separation of content stored in the database”

Concrete leaks from code:

| Resource | Isolated? | Notes |
|---|---|---|
| `auth.User` / groups / permissions | **No** | One user table. A staff account is global; `SitePermission` only gates *admin entry* per host |
| Django model perms | **No** | `blog.change_blogpost` is not per-site |
| filebrowser / `MEDIA_ROOT` | **No** | Documented share. Tenant A’s images are tenant B’s URLs if you know the path |
| `Form` entries / uploaded files | **Partial** | `Form` is a `Page` (site-scoped). `file_view(field_entry_id)` is **not** site-scoped |
| `Rating`, `AssignedKeyword` | **No** | No `site` FK |
| `Redirect` | Yes, in admin list | `SiteRedirectAdmin.get_queryset` filters; raw `Redirect.objects` would not |
| Cache | Prefixed by `current_site_id()` | Good. Site ID itself is cached **by Host header** (`%s.site_id.%s` % (prefix, domain)) |
| Sessions | Shared cookie jar if you share a parent domain | `session["site_id"]` is an explicit override of host matching |

### Cross-tenant access patterns

1. **Admin site switcher CSRF.** `set_site` is a GET (`core/views.py`, `?site_id=`). Staff-only, permission-checked for non-superusers, then `request.session["site_id"] = site_id`. An attacker who can make a superuser’s browser hit `/set_site/?site_id=2&next=/admin/` silently rebinds their admin to tenant 2. Low-and-slow content swap.

2. **Host header → site.** If `ALLOWED_HOSTS` is `*` or the `SitesAllowedHosts` fallback (`mezzanine/utils/conf.py` — “You haven’t defined ALLOWED_HOSTS… fall back to the domains configured as sites”), a matching `Host:` selects a tenant. Django’s `ALLOWED_HOSTS` is the real control. The project template defaults to `["localhost", "127.0.0.1"]`, then `local_settings.py` is `exec`’d — production depends on the operator.

3. **Drafts are not tenant-secret from other staff.** `PublishedManager.published` returns `self.all()` for **any** `for_user.is_staff` (`core/managers.py`). It does not check `has_site_permission`. A staff user on tenant A who can hit tenant B’s host (and is not logged out — middleware only intercepts `/admin`) can open tenant B draft URLs. Blog detail uses the same `published(for_user=request.user)`.

4. **Superuser is a cross-tenant god object.** Correct for a single operator; fatal if you sell “multi-tenant CMS” to two customers in one process.

5. **No row-level security, no DB schema-per-tenant, no separate `SECRET_KEY` per site.** `NEVERCACHE_KEY` and `SECRET_KEY` are process-global. Compromise one tenant’s template injection (see §9 SSTI) and you have every tenant.

**Can tenant A see tenant B?**  
- Public content: only if host/session resolution is wrong, or media paths leak.  
- Staff: yes — shared users, shared media, shared perms, IDOR on form files, drafts-by-URL.  
- Superuser: always.

This is **virtual hosting**, not multi-tenancy. Do not sell it as the latter.

---

## 6. CSRF, clickjacking, open redirects

### CSRF — Django’s, plus Mezzanine footguns

Default `MIDDLEWARE` includes `django.middleware.csrf.CsrfViewMiddleware` (`project_template/.../settings.py`). Comment and form POSTs go through it. Admin AJAX sets `X-CSRFToken` from `window.__csrf_token` (`ajax_csrf.js`, `admin/base_site.html`). That global JS token means **any admin XSS is an instant CSRF oracle** — you do not even need to read the cookie (`CSRF_COOKIE_HTTPONLY` is not set in the template project).

Cache middleware re-runs CSRF on the way out so `{% csrf_token %}` inside `{% nevercache %}` still works (`UpdateCacheMiddleware`). That is careful. The complementary risk is `nevercache`: cached pages are split on `nevercache.` + `NEVERCACHE_KEY` and **odd-numbered chunks are `Template(...).render`ed** (`middleware.py`). If `NEVERCACHE_KEY` is empty/guessable, or ever appears in attacker-controlled cached HTML, that is stored SSTI on the anonymous cache path. `NEVERCACHE_KEY` default is `""`; `cache_installed()` is false without it. The project template generates one. Operators who copy settings and leave it blank, or set it to a published value, should be assumed compromised.

`set_site`, `logout`, and password-reset-verify are GET. CSRF middleware will not save you.

### Clickjacking

`XFrameOptionsMiddleware` is in the default stack → `X-Frame-Options: SAMEORIGIN`. Fine for 2013. Not a CSP `frame-ancestors` story. TinyMCE and filebrowser popups assume same-origin framing.

### Open redirects

`next_url` (`mezzanine/utils/urls.py`) uses `url_has_allowed_host_and_scheme(next, allowed_hosts=host)`. That is the right helper. Used by login, logout, signup, `set_site`, and verification emails.

Residual:

- `login_redirect` will `reverse()` `LOGIN_REDIRECT_URL` or use it as a raw path. A settings typo can still bounce off-site if someone puts an absolute URL in settings (the helper is not re-applied to the setting).
- Verification emails append `?next=` from the *signup* request (`utils/email.py`). Host is checked at click time via `login_redirect` → `next_url`. OK.
- `RedirectFallbackMiddleware` 301s to `redirect.new_path` with **no** open-redirect check. That is an admin-controlled open redirect by design. Combined with admin XSS, it is a phishing amplifier. `new_path` is not forced same-origin.

### Headers that are simply missing

Default middleware does **not** include `django.middleware.security.SecurityMiddleware`. Therefore, out of the box:

- no `SECURE_SSL_REDIRECT` / HSTS
- no `SECURE_CONTENT_TYPE_NOSNIFF`
- no `SECURE_REFERRER_POLICY`
- no `SECURE_CROSS_ORIGIN_OPENER_POLICY`

`SSLRedirectMiddleware` exists and is **deprecated**, and it will happily 302 HTTPS → **HTTP** for URLs not in `SSL_FORCE_URL_PREFIXES` (`SSL_FORCED_PREFIXES_ONLY`). That is a downgrade oracle. Do not use it.

No CSP. No Permissions-Policy. No Trusted Types. No `Cross-Origin-Resource-Policy`.

---

## 7. Dependency risk (grappelli_safe, filebrowser_safe, old jQuery)

Declared in `setup.cfg`:

```
django >= 2.2, <6
filebrowser_safe >= 1.1.1
grappelli_safe >= 1.1.1
bleach[css] >= 5
django-contrib-comments >= 2.0
pillow >= 7
```

Plus **vendored** frontend:

| Component | Where | Age / problem |
|---|---|---|
| jQuery **3.4.1** | `mezzanine/core/static/mezzanine/js/jquery-3.4.1.js` | 2019. CVE-2020-11022 / 11023 (XSS in `htmlPrefilter`) |
| jQuery UI **1.12.1** | `jquery-ui-1.12.1.js` | 2016. CVE-2021-41182/3/4, CVE-2022-31160 |
| TinyMCE **4.x** (full `tinymce/` tree) | `core/static/mezzanine/tinymce/` | EOL. Multiple XSS in plugins; `valid_elements: "*[*]"` disables its own XSS filter |
| chosen **0.9.12** | `mezzanine/chosen/` | Prehistoric |
| html5shiv / respond.min.js / `moxieplayer.swf` | static | IE8 fossils + a **Flash** player |
| `grappelli_safe` / `filebrowser_safe` | optional-but-default forks | Not upstream Grappelli/Filebrowser. Small fork, slow CVE pickup. Filebrowser is the upload attack surface |
| Django **2.2** still in classifiers | `setup.cfg` | EOL April 2022. Advertising it is an invitation to run a dead framework |

`bleach` is the right library (and `[css]` extra is used). Pin is `>= 5`, not a ceiling — OK.

`exec(open(f, "rb").read())` on `local_settings.py` (`project_template/.../settings.py`) plus `imp` (removed in 3.12, yet classifiers go to 3.14) is a deployment landmine. `ADMIN_REMOVAL` uses `exec`/`eval` on settings-controlled strings (`boot/lazy_admin.py`) — not remotely reachable unless an attacker writes settings.

**WordPress plugin XSS is a joke because there are 60k plugins. Mezzanine’s joke is that the *core* still ships jQuery UI 1.12 and TinyMCE 4 and calls it a product.**

---

## 8. What’s needed for 2026

These are not nice-to-haves. They are table stakes for a CMS that will be compared to WordPress, Wagtail, or a static site.

| Capability | Mezzanine now | 2026 requirement |
|---|---|---|
| **2FA** | None | TOTP + WebAuthn for `is_staff` / `is_superuser`, mandatory |
| **Passkeys** | None | Resident keys for admin; recover with backup codes |
| **CSP** | None | Strict CSP with nonces; TinyMCE either replaced or isolated in a sandboxed origin; `frame-ancestors 'self'` |
| **Secret scanning** | None | Pre-commit + CI (gitleaks) on `SECRET_KEY`, `NEVERCACHE_KEY`, Disqus/Bitly/Akismet keys, `local_settings.py` |
| **Signed preview URLs** | Drafts = “are you `is_staff`?” | HMAC/expiring token, capability-scoped, works logged-out, audit-logged, **not** “any staff on any site” |
| **Capability-based roles** | `is_staff` + global Django perms + optional `SitePermission` | Per-site roles: `page.publish`, `blog.edit_own`, `forms.read_entries`, `media.upload`, `settings.change_filter_level`. Superuser break-glass with step-up auth |
| **Audit log** | Django `LogEntry` for admin forms; inline `edit()` writes a change message | Immutable, exportable log: login, 2FA, site switch, setting change (especially `RICHTEXT_FILTER_LEVEL`), file download, preview-token issue, permission grant. Tamper-evident |
| **SSO** | Disqus HMAC only | OIDC/SAML for staff. SCIM optional. Disable password login when SSO is on |
| **Session hygiene** | `SESSION_EXPIRE_AT_BROWSER_CLOSE = True` in template; no rotation on privilege change | Rotate on login and 2FA; revoke all sessions on password reset; bind session to site |
| **Password reset** | Email link **is** login | One-time, single-purpose, sets password, does not create a session until the new password works |
| **Render-time sanitization** | Bleach on save only | Sanitize on save *and* on render; refuse `|safe` without a sanitizer pass; kill `RICHTEXT_FILTER_LEVEL_NONE` or require a second person |
| **Upload policy** | Filename + hope | Allowlist, separate download host, random stored names, `Content-Disposition: attachment`, SVG/HTML blocked, image re-encode |
| **Tenant isolation** | Site FK + shared media/users | Per-tenant media prefix or bucket; per-tenant roles; no shared superuser for customer tenants; tests that fail the build on cross-site `get(id=)` |
| **Dependency policy** | Django 2.2–5.2, vendored 2016 JS | Drop EOL Django; npm/cdn lockfile or un-vendor and renovate; no Flash; TinyMCE 7 or drop WYSIWYG |
| **Rate limits / lockout** | None | Login, reset, signup, comment, rating |
| **Security middleware** | Missing | `SecurityMiddleware` + secure cookie flags + CSP middleware as defaults in the project template |

Compliance (SOC2 / ISO 27001 / GDPR) additionally needs: data-retention on form entries and comments, export/delete for a data subject (there is none), encryption-at-rest guidance that is not “use Postgres,” and a security.txt / disclosure process that is not a decade-old email in the CHANGELOG.

---

## 9. Revolutionary: security-as-default that actually beats WordPress

WordPress’s original sin is *trusted HTML from untrusted plugins*, plus a capability system that every plugin reimplements wrong. Mezzanine’s opportunity is that it is small enough to make the *opposite* default and keep it.

Do not add a “Wordfence for Mezzanine.” That is copying the disease. Change the defaults so the class of bug stops compiling.

### Non-negotiable defaults (break them in settings, loudly)

1. **HTML is a privilege, not a field type.**
   - Authors get Markdown or a locked block editor. WYSIWYG HTML is an explicit `html.publish` capability.
   - Bleach (or nh3) on **write and read**. `|richtext_filters` must bleach or it must not `mark_safe`.
   - Delete `RICHTEXT_FILTER_LEVEL_NONE` from the admin. If an operator wants raw HTML, they set an env var and restart.
   - TinyMCE `valid_elements: "*[*]"` is malpractice; if TinyMCE stays, it gets a denylist that matches the server.

2. **Untrusted bytes never become trusted HTML.**
   - Filenames are UUID + allowlisted extension. Display name is `{{ name }}` (escaped). `mark_safe` on a user string is a lint failure.
   - Uploads served from a cookieless attach-only origin.
   - Form `default` is **not** `Template(field.default).render(context)` (`forms/forms.py` line 175). That is staff SSTI → `{{ settings.SECRET_KEY }}` → game over. If you want `{{ user.email }}` prefill, whitelist three variables.

3. **Tenancy is a test, not a docstring.**
   - `CurrentSiteManager` stays.
   - Every `get_object_or_404(Model, id=...)` on a non-`SiteRelated` object that hangs off a site (form files, ratings) gets a site join.
   - Media keys prefixed `sites/<id>/`.
   - A CI test creates two sites, two staff, and fails if A can read B’s page, file, or draft.

4. **Staff are high-value, so treat them that way.**
   - 2FA required before `is_staff` works.
   - Preview = signed URL, 15 minutes, object-scoped, logged.
   - Settings that change the security model (`RICHTEXT_FILTER_LEVEL`, `COMMENTS_DEFAULT_APPROVED`, `SSL_*`) require re-auth.
   - `displayable_links_js` returns `JsonResponse` with `Content-Type: application/json` **and** is `admin_view`’d. That is the one-line fix for CVE-2025-6050 that v6.1.1 already wrote and this tree dropped.

5. **Comments are off or gated.**
   - `COMMENTS_DEFAULT_APPROVED = False`
   - `COMMENTS_ACCOUNT_REQUIRED = True`
   - Akismet over HTTPS, fail **closed** when a key is configured and the service errors
   - Or delete first-party comments and document “use an external system”

6. **The project template is a hardened artifact, not a tutorial.**
   - `SecurityMiddleware` on
   - `SECURE_SSL_REDIRECT`, HSTS, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `CSRF_COOKIE_HTTPONLY`
   - CSP nonce middleware
   - `AUTH_PASSWORD_VALIDATORS` (length 12, common-password, attribute similarity)
   - `createdb` refuses `default`/`admin` in `DEBUG=False`
   - No `exec(local_settings.py)`; use `django-environ` / importlib
   - Drop Django < 4.2, drop vendored jQuery UI, drop Flash

### Why this beats WordPress

WordPress cannot make these defaults without burning the plugin economy. Mezzanine has no plugin economy left to burn. A CMS that **cannot store a `<script>` even when a site owner tries**, that **cannot serve another tenant’s file by primary key**, and that **will not let staff log in with a password alone** is a product WordPress literally cannot ship. That is the only interesting security story this codebase still has.

Everything else — another Akismet toggle, another “please change the default password” banner, another `mark_safe` — is rearranging deck chairs on a CVE list that already started in 2025.

---

## Appendix A — Search notes (requested patterns)

| Pattern | Result |
|---|---|
| `mark_safe` | Keywords widget, form-entry filenames, default-password admin message, `richtext_filters`, twitter, order-widget arrows |
| CSRF | Middleware on; AJAX header from JS global; GET logout / `set_site` |
| Raw SQL / `extra()` | **None** found. Search is `icontains` Q-objects (`core/managers.py`) |
| `pickle` / `yaml.load` | None |
| `eval` / `exec` | `ADMIN_REMOVAL` in `lazy_admin.py`; `local_settings.py` loader |
| `request.GET` | `set_site` (`site_id`), `search` (`q`, `type`, `page`), `static_proxy` (`u`), `next_url` |
| XSS / bleach | Centralized in `utils/html.py`; not on render; not on titles/filenames/descriptions |
| `RICHTEXT_FILTER*` | Save-time bleach; render-time thumbnails only |

## Appendix B — CVE disposition

| CVE | Component | This tree |
|---|---|---|
| CVE-2025-6050 | `displayable_links_js` unsanitized titles as `text/html` | **Vulnerable** (6.1.1 patch not present) |
| CVE-2025-29573 | Forms “View Entries” filename XSS | **Vulnerable** |
| CVE-2025-50481 | Blog post body stored XSS via TinyMCE source | Default bleach *should* strip `<script>`; defense optional / skippable / untested. **Do not claim fixed.** |

---

*General SECURITY. Adversarial, from code. Do not confuse “Django won’t let you SQL-inject” with “this CMS is safe.”*
