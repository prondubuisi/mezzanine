# 08 — Legacy Autopsy

**Role:** General ARCHAEOLOGIST  
**Subject:** Mezzanine CMS, as of August 2026  
**Constraint:** Do not modify the Mezzanine repo. This is a kill list, not a patch.

---

## EXECUTIVE VERDICT

Mezzanine is a **compatibility museum with a still-beating heart**.

The heart is real: hierarchical pages, `Displayable` publishing, a page tree, scheduled draft/preview, a thin blog, a forms builder, multi-site, and a search API. That kernel would still be a good Django CMS in 2026 if it were extracted.

Everything around it is 2012 product marketing that was never allowed to die. The README still advertises JVM/Jython, bit.ly, Gravatar, Disqus, Universal Analytics, Facebook/Twitter sharing, Freenode, Mercurial, and Bitbucket. The Twitter app was deprecated in 5.0 and still ships, still calls API v1.1, still embeds hard-coded OAuth secrets. The mobile app is two files and a `FutureWarning`. Comments sit on `django-contrib-comments`, a package Django itself evicted in 2013. The last three years of “releases” are Pillow pins, `pkg_resources` removal, and an XSS fix. No product features.

**Living product?** No. A small group (Henri Hulski, molokov, Ken Bolton in spirit) keeps the tox matrix breathing. That is hospice, not product.

**What to do:** treat the fork as a **new product** (`Nova` / Mezzanine 7), API-compatible with the content models for migration, and delete ~60% of the tree on day one.

---

## 1. Dead integrations (with evidence)

### 1.1 `mezzanine.twitter` — deprecated, still installed, already dead at the wire

Docs say it will be removed “in a future version” (`docs/twitter-integration.rst`, deprecated since 5.0). A Django system check fires `mezzanine.twitter.W001` if the app is in `INSTALLED_APPS` (`mezzanine/twitter/checks.py`). The project template comments it out. **It is still in the package**, with 38 locale trees, a migration, admin mixin, poll command, and template tags.

It talks to **Twitter API 1.1**:

```54:66:mezzanine/twitter/models.py
        urls = {
            QUERY_TYPE_USER: (
                "https://api.twitter.com/1.1/statuses/"
                "user_timeline.json?screen_name=%s"
                "&include_rts=true" % value.lstrip("@")
            ),
            QUERY_TYPE_LIST: (
                "https://api.twitter.com/1.1/lists/statuses.json"
                "?list_id=%s&include_rts=true" % value
            ),
            QUERY_TYPE_SEARCH: "https://api.twitter.com/1.1/search/tweets.json"
            "?q=%s" % value,
        }
```

v1.1 timeline/search were restricted/retired in 2023. This code cannot work for a new site. The default query is still `"from:stephen_mcd mezzanine"` (`mezzanine/twitter/defaults.py`).

Worse: **committed OAuth consumer/access secrets** as a fallback when nothing is configured, so the demo feed can scrape without keys:

```76:83:mezzanine/twitter/models.py
                auth_settings = (
                    "KxZTRD3OBft4PP0iQW0aNQ",
                    "sXpQRSDUVJ2AVPZTfh6MrJjHfOGcdK4wRb1WTGQ",
                    "1368725588-ldWCsd54AJpG2xcB5nyTHyCeIC3RJcNVUAkB1OI",
                    "r9u7qS18t8ad4Hu9XVqmCGxlIpzoCN3e1vx6LOSVgyw3R",
                )
```

`TweetableAdminMixin` (`mezzanine/twitter/admin.py`) optionally imports `python-twitter` and posts 140-char updates. `BlogPostAdmin` still inherits it (`mezzanine/blog/admin.py`). `poll_twitter` still calls `db.close_connection()` — a Django 1.x API (`mezzanine/twitter/management/commands/poll_twitter.py`). Templates still use `http://twitter.com/...` and Glyphicons (`mezzanine/twitter/templates/twitter/tweets.html`).

**Sentence:** delete the entire `mezzanine/twitter/` tree, the mixin, the docs page, `requests-oauthlib` if nothing else needs it, and every locale copy.

### 1.2 `mezzanine.mobile` — a tombstone

```1:8:mezzanine/mobile/__init__.py
import warnings

warnings.warn(
    "mezzanine.mobile has been deprecated. Please remove it from your "
    "INSTALLED_APPS.",
    FutureWarning,
    stacklevel=2,
)
```

`models.py` is one comment: `# Required for INSTALLED_APPS.` Device detection was removed in 4.3; `TemplateForDeviceMiddleware` remains as a stub that only warns (`mezzanine/core/middleware.py`). Cache keys still mention the old device slot (`mezzanine/utils/cache.py`).

**Sentence:** delete the app. Delete the middleware class. Stop shipping a package whose only job is to warn you it exists.

### 1.3 bit.ly v3 — URL shortening as a content-model concern

`Displayable.short_url` + `generate_short_url()` call **bit.ly API v3** when `BITLY_ACCESS_TOKEN` is set (`mezzanine/core/models.py`, `mezzanine/core/defaults.py`). The share buttons on blog posts call `{% set_short_url_for blog_post %}` then tweet the short URL (`mezzanine/blog/templates/blog/blog_post_detail.html`). This couples publishing to a 2010 link-shortener and writes `"unset"` into the DB when bit.ly is absent.

**Sentence:** drop the field from the public API or keep it as a nullable override. Do not call bit.ly from `save()`.

### 1.4 Google Analytics — Universal Analytics, sunset 2023-07-01

```5:14:mezzanine/core/templates/includes/footer_scripts.html
{% if settings.GOOGLE_ANALYTICS_ID and not request.user.is_staff %}
<script>
(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
})(window,document,'script','//www.google-analytics.com/analytics.js','ga');

ga('create', '{{ settings.GOOGLE_ANALYTICS_ID }}', 'auto');
ga('send', 'pageview');
```

That is `analytics.js` / `ga()`, not gtag, not GA4. Docs theme still loads classic `ga.js` (`docs/mezzanine_theme/layout.html`). Setting: `GOOGLE_ANALYTICS_ID`.

**Sentence:** delete the snippet. If analytics stays, it is a one-line hook for Plausible / GA4 / whatever the site owner injects.

### 1.5 Disqus — third-party comments as a first-class setting

Full stack still in tree:

- Settings: `COMMENTS_DISQUS_SHORTNAME`, `COMMENTS_DISQUS_API_PUBLIC_KEY`, `COMMENTS_DISQUS_API_SECRET_KEY` (`mezzanine/generic/defaults.py`)
- Tags + HMAC SSO (`mezzanine/generic/templatetags/disqus_tags.py`)
- Templates: `disqus_comments.html`, `disqus_counts.html`, `disqus_sso.html`
- Admin dashboard swaps to Disqus’s `recent_comments_widget.js` when shortname is set
- Blog list/detail load count.js

**Sentence:** extract to an optional plugin or delete. A 2026 CMS does not vendor Disqus SSO.

### 1.6 Gravatar — MD5 email → `//www.gravatar.com/avatar/`

```203:209:mezzanine/core/templatetags/mezzanine_tags.py
@register.simple_tag
def gravatar_url(email, size=32):
    bits = (md5(email.lower().encode("utf-8")).hexdigest(), size)
    return "//www.gravatar.com/avatar/%s?s=%s&d=identicon&r=PG" % bits
```

Used on comments, admin comment list, account profiles. `ThreadedComment.email_hash` exists “for backward compatibility” when the tag took a hash instead of an email (`mezzanine/generic/models.py`). Privacy-hostile by default (email leak via hash), no local avatar, no initials.

**Sentence:** delete as default. Avatars are a profile field or a pluggable backend.

### 1.7 Facebook / Twitter share buttons

Hard-coded in the blog detail template:

```91:95:mezzanine/blog/templates/blog/blog_post_detail.html
{% block blog_post_detail_sharebuttons %}
{% set_short_url_for blog_post %}
<a class="btn btn-sm share-twitter" ... href="https://twitter.com/intent/tweet?url=...
<a class="btn btn-sm share-facebook" ... href="https://www.facebook.com/sharer/sharer.php?u=...
```

README feature bullet: “Sharing via Facebook or Twitter.” This is not a feature. It is two `<a>` tags and a bit.ly dependency.

### 1.8 Akismet — HTTP/1.1 REST, `urlopen`, Python 2 comment

`mezzanine/utils/views.py` `is_spam_akismet` posts to `http://%s.rest.akismet.com/1.1/comment-check` (plaintext HTTP). Default `SPAM_FILTERS` is this one function. Fine as an *optional* adapter; wrong as the only built-in, and the Python 2/3 `b"true"` dual-check is a fossil.

### 1.9 Blog importers for dead or fossil APIs

`docs/blog-importing.rst` + `mezzanine/blog/management/commands/`:

| Command | Platform | Status |
|---|---|---|
| `import_wordpress` | WordPress WXR | Keep as optional extra (still useful) |
| `import_rss` | RSS | Keep as optional extra |
| `import_blogml` | BlogML | Niche; extra or delete |
| `import_tumblr` | Tumblr | Old unauthenticated API shape; extra or delete |
| `import_blogger` | Blogger | **TODO in source: update to v3.** Still depends on Google `gdata` (`mezzanine/blog/management/commands/import_blogger.py`) — a library Google killed |
| `import_posterous` | Posterous | **Posterous shut down April 2013.** The command still takes `--posterous-user` / `--posterous-pass` |

**Sentence:** WordPress + RSS stay in an `extras` package. Posterous and gdata-Blogger are vandalism to keep.

### 1.10 Jython / JVM — README fiction

README features list, last bullet: “`JVM` compatible (via `Jython`)” with links to jython.org. `setup.cfg` requires Python `>=3.8`. Jython 2.7 is Python 2; Jython 3 is not a production runtime. There is **zero** Jython-specific code. The claim is a 2011 talking point that survived twelve years of Python 3 migration.

### 1.11 Bitbucket + Mercurial + Freenode

```105:110:README.rst
Mezzanine is an open source project managed using both the Git and
Mercurial version control systems. These repositories are hosted on
both `GitHub`_ and `Bitbucket`_ respectively
```

Bitbucket **dropped Mercurial in 2020**. Freenode as a community hub **collapsed in 2021**; README still says “drop by the `#mezzanine` IRC channel on Freenode.” Support is a Google Group (`mezzanine-users`) plus GitHub issues. `docs/overview.rst` still lists third-party plugins hosted on Bitbucket (`mezzanine-mdown`, `mezzanine-pagedown`, `mezzanine-admin-backup`, `mezzanine-mailchimp`, `mezzanineopenshift`).

### 1.12 Fabric / fabfile

Removed in 5.0 (`docs/deployment.rst`). Twitter docs still mention “the Fabric script described earlier” and default cron for `poll_twitter`. The ghost of Fabric is still writing copy.

### 1.13 Admin / front-end asset crypt

Vendored, frozen, and in some cases **Flash**:

| Asset | Version / date | Path |
|---|---|---|
| TinyMCE | **4.1.10 (2015-05-05)** | `mezzanine/core/static/mezzanine/tinymce/tinymce.min.js` |
| TinyMCE IE7 skin | `skin.ie7.min.css` | same tree |
| TinyMCE Flash player | `moxieplayer.swf` | `tinymce/plugins/media/` |
| TinyMCE “example” plugins | shipped | `plugins/example/`, `example_dependency/` |
| Bootstrap | **3.2.0 (2014)** | `mezzanine/core/static/js/bootstrap.js` |
| jQuery | 3.4.1 (2019) | setting `JQUERY_FILENAME` |
| jQuery UI | 1.12.1 (2016) | `JQUERY_UI_FILENAME` |
| Chosen | **0.9.12 (~2012)** | `mezzanine/core/static/mezzanine/chosen/` |
| jquery.tools overlay/expose | ~2011 | `jquery.tools.overlay.js` |
| jquery.form | ancient | `jquery.form.js` |
| Glyphicons | Bootstrap 3 | tweets template |

`docs/inline-editing.rst` still documents `jquery-1.8.3.min.js`. TinyMCE config still uses the v4 plugin names `contextmenu`, `print`, `file_browser_callback` (`mezzanine/core/static/mezzanine/js/tinymce_setup.js`).

**grappelli_safe / filebrowser_safe** are required deps (`setup.cfg`). FAQ (`docs/frequently-asked-questions.rst`) admits they are frozen forks created because upstream “took paths that weren't desired,” and “have relatively low activity.” They exist so the admin can look like 2012 Grappelli.

### 1.14 Cartridge, mezzanine-api, the plugin graveyard

- README still lists “Ecommerce / Shopping cart module (Cartridge)” → `cartridge.jupo.org` (same dead jupo.org estate).
- `createdb` still special-cases `cartridge.shop` fixtures (`mezzanine/core/management/commands/createdb.py`).
- `mezzanine-api` (gcushen) was **archived 2022-09-25** with the banner: “Mezzanine CMS and Mezzanine API are no longer maintained. … use Wagtail.”
- `docs/overview.rst` plugin list is a 2013–2016 yearbook: html5boilerplate, OpenShift, Stackato, Instagram, WYMeditor, Webfaction, Buffer.

### 1.15 Python 2 leftovers (the ones that still compile)

Not `ugettext` (those were renamed) and not `django.conf.urls.url` (urls use `path`/`re_path`). The real fossils:

| Fossil | Where |
|---|---|
| `try: unicode` / `except NameError` | `mezzanine/blog/feeds.py`, `mezzanine/core/models.py` (`description_from_content`) |
| `unicode = lambda s: s` then `unicode(self._title)` | feeds |
| `db.close_connection()` | `poll_twitter` |
| `bdist_wheel.universal = 1` | `setup.cfg` — advertises a py2/py3 wheel |
| `MIDDLEWARE_CLASSES` fallback | `mezzanine/utils/deprecation.py` (Django < 1.10) |
| `is_authenticated()` call vs property | same file, `django.VERSION < (1, 10)` |
| `field.rel.to` vs `remote_field.model` | same file, `django.VERSION < (1, 9)` |
| Cookie encode workaround “on Python 2” | `mezzanine/utils/views.py` |
| `import imp` to load `local_settings.py` | `mezzanine/project_template/project_name/settings.py` — **`imp` was removed in Python 3.12** while `setup.cfg` claims 3.12–3.14 |
| `slugify_unicode` | `mezzanine/utils/urls.py` |
| `deep_force_unicode` | `mezzanine/utils/docs.py` |
| Comment: “os.path.join() in Python 2.x” | `mezzanine/galleries/models.py` |

`pkg_resources` was removed in 6.1.0 (2025-04). That is the level of “feature” this project ships now.

### 1.16 Docs / classifiers lie about the present

- `docs/overview.rst`: “Python 3.7 to 3.10” / “Django 2.2 to 4.0”
- `setup.cfg`: Python 3.8–3.14, Django 2.2–5.2
- `tox.ini`: the full cartesian product including Django 2.2 in 2026 (Django 4.2 LTS itself went EOL April 2026)
- Local `CHANGELOG` **stops at 4.3.1 (2018-08-08)** and says “see GitHub Releases” for 5.0+
- Project site `mezzanine.jupo.org` is dead / redirects; README still points every doc link there
- ReadTheDocs, per community report, stuck on 4.3.1

This is not sloppy copy. It is the signature of a project that can bump classifiers but cannot tell a new user what it is.

---

## 2. Social graph of 2012

The product’s idea of “social” is a closed loop of services that defined a WordPress-era brochure site:

```
                    ┌──────────── bit.ly v3 ────────────┐
                    │  Displayable.short_url            │
BlogPost ──publish──┤                                   ├── tweet 140 chars
                    │  TweetableAdminMixin              │   via python-twitter
                    └──────────── Twitter API 1.1 ──────┘
                                      │
                                      ▼
                         sidebar: poll_twitter cron
                         default query: from:stephen_mcd
                         hard-coded OAuth secrets

Comments ──┬── django_comments.Comment
           ├── Gravatar(MD5(email))
           ├── Akismet HTTP/1.1
           └── OR Disqus embed + SSO HMAC

Footer ────── Universal Analytics (analytics.js)

Share bar ─── twitter.com/intent/tweet + facebook.com/sharer
              (still the 2012 popup URLs)
```

Every node is either deprecated, privacy-hostile, or commercially dead for new apps:

- **Twitter/X API 1.1** is not a free “put a widget on your CMS” surface anymore.
- **bit.ly** is not how you share URLs in 2026.
- **Gravatar** is an email-hash CDN; many jurisdictions treat that as personal data.
- **Disqus** is an ad/tracker iframe. A first-party threaded comment model already exists.
- **Facebook sharer.php** is a link, not an integration.
- **Universal Analytics** stopped processing hits in 2023.
- **Freenode** is not where the community is.
- Default Twitter query and committed secrets are a shrine to the founder’s 2012 account.

The social graph is not “legacy support.” It is the **identity** the README still sells. Kill the identity.

---

## 3. Comments system modernity

### What it is

`mezzanine.generic` is a **django-contrib-comments adapter** plus three generic-relations (comments, keywords, ratings).

```17:20:mezzanine/generic/models.py
class ThreadedComment(Comment):
    """
    Extend the ``Comment`` model from ``django_comments`` to
    add comment threading.
```

Django **removed** `django.contrib.comments` in 1.6 (2013) and dumped it into `django-contrib-comments`. Mezzanine still requires `django-contrib-comments >= 2.0` (`setup.cfg`). The app implements the comments-framework hooks:

```6:18:mezzanine/generic/__init__.py
# These methods are part of the API for django_comments

def get_model():
    ...
    return ThreadedComment

def get_form():
    ...
    return ThreadedCommentForm
```

Admin subclasses `django_comments.admin.CommentsAdmin`. Ratings subclass `CommentSecurityForm` so they can piggyback on comment security fields. Cookies store name/email/url for 90 days (`mezzanine-comment-*`). Duplicate detection is “same text, same day.” Honeypot is a CSS `display:none`. Approval/removal visibility is a pair of settings that render placeholder messages rather than deleting.

### Dual-stack

If `COMMENTS_DISQUS_SHORTNAME` is set, the built-in admin is **not registered** and templates include Disqus instead (`mezzanine/generic/admin.py`, `comments.html`). Two comment systems, one setting, no migration path between them.

### Modernity score: 2011

A 2026 comments system would be: first-party model (or a maintained package), auth-required option that is not session-stashing POST bodies, moderation queue, Akismet/Turnstile as plugins, no Gravatar-by-default, no Disqus in core, no dependency on a package Django itself orphaned twelve years ago.

**Keep:** the *idea* of `ThreadedComment` (parent FK, `by_author`, optional rating) and `CommentsField` as a GenericRelation convenience.  
**Delete:** `django_comments` inheritance, Disqus, Gravatar default, cookie identity, `CommentSecurityForm` as the ratings base.  
**Rewrite:** a small first-party `nova.comments` (or drop comments from core entirely and document Wagtail/django-comments-xtd/a custom app).

`generic` should be split. Keywords and ratings are not “comments.” They are stuck in the same app because 2010 Mezzanine put all GenericForeignKeys in one bucket.

---

## 4. Feature vs maintenance ratio

### In-repo CHANGELOG

`CHANGELOG` is a 2010–2018 novel, then:

```
Version 5.0 and newer
---------------------
Please refer to the GitHub Releases Page.
```

The last *product* work visible in that file (4.2–4.3, 2016–2018) is already compatibility: Django 1.11/2.x, `on_delete`, `MIDDLEWARE`, device-detection *removal*, SSL middleware deprecation, `as_tag` deprecation. The last new-ish features in that era: search age weighting, BlogML import, Coveralls. That is eight years ago.

### GitHub releases (5.0 → 6.1.1)

| Version | Date | What it actually was |
|---|---|---|
| 5.0.0 | 2021-11-22 | Django 2.2–3.2 compatibility dump; twitter deprecated; loader_tags deprecated |
| 5.1.0 | 2022-01-05 | Django 4.0 compatibility |
| 5.1.1–5.1.4 | 2022 | collation, MiddlewareMixin removal, email uniqueness, bleach pin |
| 6.0.0 | 2022-05-12 | Drop Python 3.6 because bleach 5 required it |
| 6.0.1 | 2025-04-02 | frozenset+list / bleach; Django 4.1/4.2; drop py3.7; pin Pillow <10 |
| 6.1.0 | 2025-04-06 | Pillow ≥10 + LANCZOS; replace `pkg_resources` |
| 6.1.1 | 2025-06-04 | XSS in admin |

**Three years (2023-08 → 2026-08):** one security fix, one Pillow API rename, one packaging hygiene commit, a tox line. **Zero features.** The 2022–2025 gap is three silent years.

Latest commit observed on GitHub: 2026-04-19, “Adding missing dj42 from tox.ini” (molokov + henri-hulski). That is the current climax of the project.

### Ratio

Call it **~95% compatibility churn / 5% product** since 4.3, and **100% compatibility** since 5.1. A living CMS in this window would have shipped: GA4 or first-party analytics hook, TinyMCE 6/7 or a non-TinyMCE editor, Bootstrap 5 or no CSS framework, Django 5 admin, a headless/API story, removal of Twitter/Disqus/bit.ly. None of that happened. They kept Django 2.2 in the tox matrix instead.

`AUTHORS` is a glorious 2009–2017 roll (Stephen McDonald through Christian Kuper, ~280 names, including Google, Inc.). It does not read like a 2024–2026 project. 267 GitHub contributors historically; two people touching tox in 2026.

---

## 5. Community: living product or compatibility museum?

**Museum.** The exhibits are well-lit.

Evidence:

1. **Founder absence.** Discussion #2038 (“Is Mezzanine still viable?”): Stephen McDonald “is no longer actively working on the project”; jupo.org owner gone; official site 404s.
2. **Maintainers describe hospice.** Same thread: Ken/Henri/others “keeping this project alive”; a user on Django 2.2 “plans to update”; molokov publishes a personal fork because “I'm not sure if the maintenance team for the main repo has time.”
3. **Ecosystem voted with archives.** `mezzanine-api` archived, points at Wagtail. Premium themes gone. Free themes claim Mez ≤4.x. Cartridge is a sibling ghost.
4. **Support channels are 2012.** Google Group first, GitHub issues if you’re “certain,” Freenode for a chat. No Discord, no Discussions-as-home, no current docs site.
5. **CONTRIBUTING.rst** still sends people to the mailing list for anything that is not a sure bug.
6. **Quotes in the README** are from Van Lindberg, Jesse Noller, Audrey Roy, Phil Hughes — a 2011–2013 prestige collage. Not a 2026 community signal.
7. **“Diverse and active community”** is the second paragraph of the README. GitHub Discussions for “is this dying?” has six participants.

What *is* alive: a tox file that still tries to prove Django 2.2 through 5.2. That is the opposite of a product strategy. It is a compatibility museum with a very large gift shop of classifiers.

---

## 6. Extract vs delete vs rewrite

### EXTRACT (the kernel — this is the company)

These models and behaviors are why anyone still runs Mezzanine. They must survive under stable import paths or a documented rename map.

| Piece | Path | Why |
|---|---|---|
| `SiteRelated`, `Slugged`, `MetaData`, `TimeStamped`, `Displayable`, `RichText`, `Orderable`, `Ownable`, `ContentTyped` | `mezzanine/core/models.py` | The actual CMS. Draft/publish/expiry, slugs, SEO fields, scheduled publishing |
| `Page` tree + `PageMiddleware` + page processors | `mezzanine/pages/` | Hierarchical nav, login_required, content types as subclasses |
| `BlogPost` / `BlogCategory` | `mezzanine/blog/models.py` | Thin and good. Keep the model; strip social/Disqus |
| Search API on `Displayable` | `mezzanine/core/managers.py` | One of the few distinctive features |
| Forms builder | `mezzanine/forms/` | Still a product. Extract as optional app |
| Galleries | `mezzanine/galleries/` | Optional app |
| Keywords | `mezzanine/generic/` (split out) | Tagging that the admin JS already understands |
| Multi-site + `SitePermission` | `mezzanine/core/` + `utils/sites.py` | Real multi-tenancy |
| Editable settings registry | `mezzanine/conf/` | Useful; rewrite storage, keep the idea |
| `createdb` / `mezzanine-project` | `bin/` + `core/management` | Project bootstrap, minus Cartridge special cases |
| Rich-text bleach pipeline | `mezzanine/utils/html.py` | Keep the contract, update bleach usage |

Migration promise: **same table names, same concrete fields on `Page` / `BlogPost` / `Displayable` subclasses.** A 4.3/5.x/6.x site dumps data and points `INSTALLED_APPS` at Nova.

### DELETE (do not port, do not wrap, do not “deprecate again”)

- Entire `mezzanine/twitter/` (app, locales, migration, mixin, docs, `poll_twitter`, hard-coded secrets)
- Entire `mezzanine/mobile/`
- `TemplateForDeviceMiddleware`, `TemplateForHostMiddleware` (loader already exists), `SSLRedirectMiddleware`
- bit.ly (`BITLY_ACCESS_TOKEN`, `generate_short_url`, `set_short_url_for`)
- Gravatar tag as default
- Disqus settings, tags, templates, SSO
- Universal Analytics snippet + `GOOGLE_ANALYTICS_ID` as a built-in script
- Facebook/Twitter share blocks
- `import_posterous`, `import_blogger` (gdata)
- Fabric mentions, Freenode, Bitbucket, Mercurial, Jython, “JVM compatible”
- Vendored TinyMCE 4.1.10 tree (including `.swf`, IE7 skin, example plugins)
- Bootstrap 3.2, Chosen 0.9.12, jquery.tools, Glyphicons
- `python-twitter` / `requests-oauthlib` if unused elsewhere
- `bdist_wheel.universal = 1`
- Django 1.8–1.10 shims in `utils/deprecation.py`
- `import imp` local_settings loader
- Cartridge hooks in `createdb` / `collecttemplates`
- README feature list as currently written
- 38 copies of twitter/mobile locales

### REWRITE (shape is right, implementation is a trap)

| Thing | Why rewrite |
|---|---|
| Comments | First-party model; drop `django-contrib-comments` |
| Ratings | Stop inheriting comment security forms |
| Admin chrome | Django 5 admin or a maintained skin; stop forking Grappelli 2012 |
| File library | filebrowser_safe → django-storages + a small picker, or upstream filebrowser |
| WYSIWYG | TinyMCE 7 *or* a pluggable editor (TipTap/ProseMirror on the front, one server filter) |
| Front templates | No Bootstrap 3. Provide unstyled semantic templates + one optional 2026 theme |
| Inline editing | The idea is good; jquery.tools overlay is not |
| Accounts | Keep profiles/verification *or* document django-allauth and delete `mezzanine.accounts` |
| Analytics / spam / share | Plugin hooks, zero vendor SDKs in core |
| Importers | WordPress + RSS as `nova.extras` |
| Docs | Rebuild. Current docs still describe 3.7/4.0 and a live jupo.org |
| `local_settings.py` via `exec`+`imp` | `django-environ` / standard `DJANGO_SETTINGS_MODULE` split |
| Threadlocals `current_request()` | Keep a documented request middleware; stop pretending it is not threadlocals |

---

## 7. Mezzanine 7 / Nova — deletion manifesto

The smallest kernel worth keeping is **a page tree + publishable documents + search + optional blog/forms/galleries.**

```
nova/
  core/          Displayable, RichText, Orderable, sites, search, bleach
  pages/         Page tree, middleware, processors, menus
  blog/          BlogPost, categories, feeds  (optional extra)
  forms/         form builder                 (optional extra)
  galleries/     zip-import galleries         (optional extra)
  taxo/          keywords/tags                (split from generic)
  comments/      first-party, optional        (not django_comments)
  project/       cookiecutter / startproject
```

**Hard rules for the 7.0 cut:**

1. If it calls a third-party social API, it is not in core.
2. If it was deprecated before 5.0 and is still here, it is deleted, not re-deprecated.
3. If the README lists it and the code only has a setting, it is deleted from the README first.
4. One supported Django LTS, one previous. Not 2.2 through 5.2. Compatibility museum hours are over.
5. No vendored WYSIWYG older than three years. No SWF. No IE7 CSS.
6. Locales ship for core strings; dead apps do not get 38 `.po` trees.
7. `Displayable` / `Page` / `BlogPost` field names are a **stability promise**. Everything else is fair game.
8. Default password `admin` / `default` (`createdb`) dies. That is not “friendly.” It is a CVE waiting for a scanner.
9. No committed secrets. Ever. The Twitter fallback keys are the original sin of this codebase.
10. The project website, docs, and PyPI classifier must describe the same product.

That is the whole manifesto. The rest is taste.

---

## 8. Revolutionary position: new product, old bones

Do **not** ship “Mezzanine 7” as a sentimental continuation. The name currently means: Grappelli-safe, Disqus-or-comments, bit.ly, Cartridge, jupo.org, a Google Group.

Ship a **new product** that is honest about lineage:

### Name

Working name: **Nova**.

(Alternates if Nova is taken on PyPI: **Entresol**, **PianoNobile**, **Storey**. Do not call it Mezzanine-NG. NG is what people say when they are afraid to break up with the old name.)

### Positioning

> Nova is a Django CMS. It understands Mezzanine content.

Not “the next Mezzanine.” Not “Wagtail but nostalgic.” A page-tree CMS with publishable models and a migration hatch.

### Compatibility contract (the only nostalgia that is allowed)

Publish a `nova.compat.mezzanine` layer for one major:

- Same concrete table names: `pages_page`, `blog_blogpost`, `blog_blogcategory`, `generic_assignedkeyword`, `generic_keyword`, `forms_*`, `galleries_*`
- Same `Displayable` columns: `title`, `slug`, `status`, `publish_date`, `expiry_date`, `in_sitemap`, SEO fields, `short_url` (nullable, inert)
- Same `Page` columns: `parent`, `in_menus`, `titles`, `login_required`, `content_model`
- Same `BlogPost` columns: `categories`, `allow_comments`, `featured_image`, `related_posts`
- A management command `nova_from_mezzanine` that: runs remaining Mez migrations, removes `mezzanine.twitter` / `mezzanine.mobile` tables, rewrites `INSTALLED_APPS`, leaves Disqus/bit.ly/GA settings as ignored leftovers

After one major, drop the compat package. Sites that did not migrate are on Mezzanine 6.x hospice, which already exists.

### What the new product is *not*

- Not a Twitter client
- Not a Disqus reseller
- Not a Gravatar proxy
- Not a bit.ly customer
- Not JVM-compatible
- Not Mercurial
- Not a Bootstrap 3 theme pack
- Not Cartridge
- Not a 12-version Django matrix

### What it is

A boring, extractable, **2026-native** CMS kernel: pages, publish, search, optional blog, optional forms, optional galleries, first-party comments if anyone still wants them, modern admin, modern editor, docs that are true.

The Byzantine move is not another deprecation warning on `mezzanine.twitter`. It is a new package name, a kill list, and a migration command.

---

## Appendix A — File-level kill list (first PR of Nova)

```
DELETE
  mezzanine/twitter/                  # entire app + locales + migrations
  mezzanine/mobile/                   # entire app
  docs/twitter-integration.rst
  mezzanine/generic/templatetags/disqus_tags.py
  mezzanine/generic/templates/generic/includes/disqus_*.html
  mezzanine/core/static/mezzanine/tinymce/   # replace, do not patch 4.1.10
  mezzanine/core/static/mezzanine/chosen/
  mezzanine/core/static/mezzanine/js/jquery.tools.*.js
  mezzanine/core/static/js/bootstrap.js      # 3.2.0
  mezzanine/blog/management/commands/import_posterous.py
  mezzanine/blog/management/commands/import_blogger.py

STRIP FROM
  README.rst                          # Jython, bit.ly, Gravatar, Disqus, GA, Freenode, Hg, Bitbucket, Facebook share
  mezzanine/core/defaults.py          # BITLY_*, GOOGLE_ANALYTICS_ID (as baked snippet)
  mezzanine/generic/defaults.py       # COMMENTS_DISQUS_*
  mezzanine/blog/admin.py             # TweetableAdminMixin
  mezzanine/blog/templates/blog/blog_post_detail.html  # share + disqus
  mezzanine/core/templates/includes/footer_scripts.html
  mezzanine/core/models.py            # generate_short_url bit.ly; unicode() shim
  mezzanine/core/templatetags/mezzanine_tags.py  # gravatar_url as default
  mezzanine/utils/deprecation.py      # Django 1.8–1.10 branches
  mezzanine/project_template/.../settings.py  # imp, twitter comment, cartridge folklore
  setup.cfg                           # universal=1, requests-oauthlib if unused, django<6 forever
  docs/overview.rst                   # plugin yearbook, version lie

REWRITE
  mezzanine/generic/                  # split keywords / ratings / comments
  comments → first-party
  admin skin → not grappelli_safe-or-death
  editor → not TinyMCE 4
```

## Appendix B — Community primary sources

- GitHub releases: https://github.com/stephenmcd/mezzanine/releases (5.0.0 … 6.1.1)
- Discussion #2038 “Is Mezzanine still viable?”
- Archived mezzanine-api: https://github.com/gcushen/mezzanine-api
- Twitter/X API v1.1 restriction (2023): timelines/search not available on current access tiers

---

*General ARCHAEOLOGIST, Byzantine council. The dirt is in the tree. The only mercy left is deletion.*
