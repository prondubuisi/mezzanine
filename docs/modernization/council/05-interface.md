# 05 — Interface: APIs, Search, SEO, i18n, Feeds

**Council seat:** General INTERFACE (independent, from code)
**Repo:** `/Users/prondubuisi/gitrepos/dev/mezzanine`
**Surfaces WordPress won with:** WP REST API + Yoast/RankMath + WPML/Polylang + RSS + headless frontends
**Date of reading:** 2026-08-11

---

## EXECUTIVE VERDICT

Mezzanine is a **server-rendered HTML CMS with a Python "Search API"** (a Django manager, not HTTP). It has **no public REST API, no GraphQL, no OpenAPI, no webhooks, no preview tokens, no JSON content endpoints, and no CORS/auth story for a headless client.**

Search is **SQL `icontains` (LIKE/ILIKE)** with in-Python scoring. There is **no Haystack, no Whoosh, no Elasticsearch, no Solr.** SEO is 2010-era meta title/description/keywords plus a Django sitemap — **no Open Graph, no Twitter Cards, no canonical, no JSON-LD, no hreflang, no per-page robots.** i18n is **first-class for UI gettext (38 locale catalogs)** and **second-class for content** (optional `django-modeltranslation`, off by default, slugs not translatable, migrations hostile). Feeds are **Django syndication RSS/Atom for the blog only.** Sharing is **two hardcoded `<a>` buttons** (Twitter intent + Facebook sharer) plus optional bit.ly.

**Headless viability today: NO.** Proven below. WordPress won this war a decade ago; Payload/Strapi/Sanity were born in it. Mezzanine never entered the building.

The revolutionary move is not "add DRF later." It is **schema-as-code content types that generate Admin + REST + GraphQL + TypeScript SDK + Python client from one declaration.** That beats WordPress (REST bolted on, GraphQL is WPGraphQL plugin, types are PHP folklore) and beats Payload (TS-first, Python/Django world is a second-class citizen).

---

## 1. Search implementation

**SQL LIKE. Not Haystack. Not Whoosh. Not Elasticsearch. Not Solr.**

Zero hits for `haystack`, `whoosh`, `elasticsearch`, or `solr` in Python/docs/config. The only `opensearch` mention is a commented Sphinx theme setting in `docs/conf.py`.

### What actually runs

The documented "Search API" (`docs/search-engine.rst`) is **`mezzanine.core.managers.SearchableManager.search()`** — a Python method on a Django manager. The HTTP surface is one HTML view.

**HTTP entry:** `GET /search/?q=…&type=app.Model` → `mezzanine.core.views.search` → `TemplateResponse("search_results.html")`.

```92:114:mezzanine/core/views.py
def search(request, template="search_results.html", extra_context=None):
    """
    Display search results. Takes an optional "contenttype" GET parameter
    in the form "app-name.ModelName" to limit search results to a single model.
    """
    query = request.GET.get("q", "")
    # ...
    results = search_model.objects.search(query, for_user=request.user)
    paginated = paginate(results, page, per_page, max_paging_links)
    return TemplateResponse(request, template, context)
```

**Query translation** (`SearchableQuerySet.search` in `mezzanine/core/managers.py`):

1. Split on quotes; treat `+term` / `-term` as required / excluded.
2. Strip English stop words from `STOP_WORDS` (`mezzanine/core/defaults.py` ~644+).
3. Build Django `Q` objects with **`field__icontains`** — i.e. `ILIKE '%term%'` on every configured field.
4. Combine with `AND`/`OR`/`NOT`.
5. `annotate_scores()` **iterates every matching row in Python**, counts substring occurrences × field weight, then divides by `age ** SEARCH_AGE_SCALE_FACTOR` (default 1.5).
6. Heterogeneous search (abstract `Displayable`) **materializes every model's matches into a Python list** and `sorted(..., reverse=True)`.

```159:197:mezzanine/core/managers.py
        excluded = [
            reduce(
                iand,
                [
                    ~Q(**{"%s__icontains" % f: t[1:]})
                    for f in self._search_fields.keys()
                ],
            )
            for t in terms
            if t[0:1] == "-"
        ]
        required = [
            reduce(
                ior,
                [Q(**{"%s__icontains" % f: t[1:]}) for f in self._search_fields.keys()],
            )
            ...
        ]
        optional = [
            reduce(
                ior, [Q(**{"%s__icontains" % f: t}) for f in self._search_fields.keys()]
            )
            ...
        ]
```

Default field weights on `Displayable` (`mezzanine/core/models.py:270`):

```python
search_fields = {"keywords": 10, "title": 5}
```

`RichText` adds `"content"`. `KeywordsField` rewrites `keywords` → `keywords_string` (denormalized space-joined titles) so search can `icontains` a CharField (`mezzanine/generic/fields.py:212-231`).

Defaults (`mezzanine/core/defaults.py`):

| Setting | Default | Meaning |
|---|---|---|
| `SEARCH_MODEL_CHOICES` | `("pages.Page", "blog.BlogPost")` | Dropdown models |
| `SEARCH_PER_PAGE` | `10` | HTML pagination |
| `SEARCH_AGE_SCALE_FACTOR` | `1.5` | Recency bias |
| `STOP_WORDS` | English function-word list | Always English |

### Why this loses

- **No inverted index.** Every search is N `ILIKE '%x%'` ORs. Full table scan on title/content/keywords.
- **Scoring is O(results × terms × fields) in Python after fetch.** Heterogeneous search cannot even return a queryset (docs admit this: "the result is a list of model instances").
- **No stemming, no language analyzers, no synonyms, no typo tolerance, no facets, no highlighting, no suggestions.**
- Stop words are English-only. A French or Arabic site still strips `the`/`and` and does not strip `le`/`و`.
- Draft exclusion is a published-manager filter, not an index-time concern — fine at 100 pages, fatal at 100k.
- The "Search API" cannot be consumed by a mobile app or Next.js frontend without scraping HTML.

WordPress won here with Elasticsearch plugins (ElasticPress) and later with hosted search. Mezzanine never left `icontains`.

---

## 2. SEO fields and sitemaps

### Fields (2010 Yoast-lite, minus the lite)

`MetaData` + `Displayable` (`mezzanine/core/models.py`):

| Field | Purpose | Gap vs modern SEO |
|---|---|---|
| `_meta_title` | Optional `<title>` override | No title templates, no sitename control beyond `SITE_TITLE` append |
| `description` | Meta description; auto-filled from first RichText/TextField sentence if `gen_description=True` | No length meter, no SERP preview |
| `gen_description` | Bool, default True | Fine |
| `keywords` | `KeywordsField` → `<meta name="keywords">` | **Google has ignored this since ~2009** |
| `slug` | URL | Not translatable; no canonical separate from slug |
| `in_sitemap` | Bool, default True | Binary include/exclude only |
| `status` / `publish_date` / `expiry_date` | Draft + schedule | Preview = staff session on the same HTML URL |
| `short_url` | bit.ly or absolute URL | Sharing, not SEO |

Admin groups these under a collapsed **"Meta data"** fieldset (`mezzanine/core/admin.py:101-111`): `_meta_title`, `slug`, `(description, gen_description)`, `keywords`, `in_sitemap`.

Rendered HTML (`mezzanine/core/templates/base.html`):

```html
<meta name="keywords" content="{% block meta_keywords %}{% endblock %}">
<meta name="description" content="{% block meta_description %}{% endblock %}">
<title>{% block meta_title %}{% endblock %}{% if settings.SITE_TITLE %} | {{ settings.SITE_TITLE }}{% endif %}</title>
```

Page/blog templates fill those via `{% metablock %}` (strip tags + escape) and `{% keywords_for %}`. **That is the entire on-page SEO surface.**

### What is missing (the WordPress/Yoast checklist)

- **No Open Graph** (`og:title`, `og:description`, `og:image`, `og:type`, `og:url`)
- **No Twitter Cards**
- **No `<link rel="canonical">`**
- **No JSON-LD / schema.org** (Article, BreadcrumbList, Organization)
- **No per-page robots** (`noindex`/`nofollow`) except search results hardcode `<meta name="robots" content="noindex">`
- **No hreflang** for multilingual
- **No focus keyword / readability**
- **No 301 manager beyond `django.contrib.redirects`**
- **Google Analytics is `analytics.js` (ga.js successor, itself deprecated)** in `includes/footer_scripts.html` — not gtag/GA4
- Static `mezzanine/core/static/robots.txt` is `User-agent: * / Disallow:` (allow all). In `DEBUG`, `mezzanine/urls.py` **overrides** with `Disallow: /`. Production robots is just the static file; no sitemap line is injected.

### Sitemaps

`mezzanine/core/sitemaps.py` — one class, Django's `contrib.sitemaps`:

```13:35:mezzanine/core/sitemaps.py
class DisplayableSitemap(Sitemap):
    def items(self):
        return list(Displayable.objects.url_map(in_sitemap=True).values())

    def lastmod(self, obj):
        if blog_installed and isinstance(obj, BlogPost):
            return obj.updated or obj.publish_date

    def get_urls(self, **kwargs):
        kwargs["site"] = Site.objects.get(id=current_site_id())
        return super().get_urls(**kwargs)
```

Wired at `sitemap.xml` if `django.contrib.sitemaps` is installed (`mezzanine/urls.py:32-37`).

`DisplayableManager.url_map` (`managers.py:422-445`) walks every `Displayable` subclass, filters `published()` + `in_sitemap=True`, excludes `http(s)://` slugs, injects a fake Home object. **No `priority`, no `changefreq`, no image sitemap, no news sitemap, no hreflang alternates.** `lastmod` is **BlogPost only** — pages have no lastmod.

Facebook/Twitter share will scrape a page with no `og:*` tags. That is not a small miss; it is the difference between a rich card and a naked URL.

---

## 3. i18n / l10n — 38 UI locales, content translation is not first-class

### UI strings: yes, and more than 35

README: *"Translated to over 35 languages."* Count of `mezzanine/core/locale/*` catalogs: **38**.

`ar, bg, ca, cs, da, de, en, eo, es, et, fa, fa_IR, fi, fr, hr_HR, hu, id_ID, is_IS, it, ja, ko, lv, nb, nl, pap, pl, pt_BR, pt_PT, ru, sk, sr_Latn, sv, tr, uk_UA, vi_VN, zh, zh_CN, zh_TW`

Same set is duplicated under `accounts/`, `blog/`, `conf/`, `core/`, `forms/`, `galleries/`, `generic/`, `pages/`, `twitter/`. This is gettext for chrome (admin labels, "Share on Twitter", form buttons). **It is not content.**

### Content translation: optional, off, and incomplete

Project template (`mezzanine/project_template/project_name/settings.py`):

```python
USE_MODELTRANSLATION = False
LANGUAGES = (("en", _("English")),)
```

`django-modeltranslation` is **not** in `install_requires` (`setup.cfg`). `mezzanine/utils/conf.py` will **disable** the feature and warn if the package is missing. Docs (`docs/multi-lingual-sites.rst`) are explicit: *"Mezzanine only provides the integration of django-modeltranslation."*

When enabled, translation registrations are:

| Module | Model | Translatable fields |
|---|---|---|
| `mezzanine/core/translation.py` | Slugged | `title` |
| | Displayable | `_meta_title`, `description` |
| | RichText | `content` |
| `mezzanine/pages/translation.py` | Page | `titles` (+ inherited) |
| | RichTextPage | (content via RichText) |
| | Link | none extra |
| `mezzanine/blog/translation.py` | BlogPost | Displayable + RichText |
| | BlogCategory | title |
| `mezzanine/forms/translation.py` | Form | `content`, `button_text`, `response`, `email_subject`, `email_message` |
| | Field | `label`, `choices`, `default`, `placeholder_text`, `help_text` |
| `mezzanine/galleries/translation.py` | Gallery | content |
| | GalleryImage | `description` |
| `mezzanine/conf/translation.py` | Setting | `value` |

**Not translatable:**

- **`slug`** — `Slugged.get_slug()` always slugifies `title_<default LANGUAGE_CODE>` (`models.py:105-116`). One URL per object. No `/en/about` vs `/fr/a-propos` from content; `i18n_patterns` only prefixes the *same* slug.
- **Keywords / tags**
- **Blog categories' slugs**
- **Featured images, galleries' files**
- **Comments**

### Why this is not first-class

1. **Default is off.** A new `mezzanine-project` is monolingual.
2. **Shipped migrations do not contain translation columns.** You must `sync_translation_fields` / `update_translation_fields`, or invent a custom `MIGRATION_MODULES` (docs § "Translation Fields and Migrations"). Adding a language is a schema event Mezzanine will not migrate for you.
3. **Admin date hierarchy is disabled when modeltranslation is on** (upstream bug workaround, `core/admin.py:88-90`).
4. **Language switcher** is a POST form to Django `set_language` (`includes/language_selector.html`). Cookie/session, not content negotiation, not path-based locale unless the integrator wraps `i18n_patterns` themselves (the project `urls.py` wraps admin + home; `mezzanine.urls` is included *outside* that block after the `if USE_MODELTRANSLATION` `set_language` route).
5. **No hreflang, no per-locale sitemap, no translation completeness UI, no "this page is 30% translated" admin.**
6. **Fallback** is delegated to `MODELTRANSLATION_FALLBACK_LANGUAGES` — empty fields show the fallback language, which is a silent SEO duplicate risk.

Compare WPML/Polylang: per-locale slugs, translation jobs, hreflang, language switcher that actually changes the URL, media translation. Mezzanine has extra VARCHAR columns and a `<select>`.

**Verdict on the user's question:** 38 gettext locales exist. **Content translation is not first-class.** It is an optional, migration-hostile, slug-less integration of a third-party app.

---

## 4. Feeds and sharing

### Feeds — blog RSS/Atom only

`mezzanine/blog/feeds.py`: `PostsRSS` (Django `Feed`) and `PostsAtom` (`Atom1Feed`).

Routes (`mezzanine/blog/urls.py`):

- `/blog/feeds/<rss|atom>/`
- `/blog/tag/<tag>/feeds/<format>/`
- `/blog/category/<category>/feeds/<format>/`
- `/blog/author/<username>/feeds/<format>/`

Features that *are* there: title/description from the Blog `Page` (or `SITE_TITLE`/`SITE_TAGLINE`); `login_required` blog page → empty feed; author name + author archive link; `item_pubdate`; categories; featured-image enclosure (`item_enclosure_*`); richtext-filtered HTML with `absolute_urls`; `BLOG_RSS_LIMIT` default 20.

`base.html` advertises both:

```html
<link rel="alternate" type="application/rss+xml" title="RSS" href="{% url "blog_post_feed" "rss" %}">
<link rel="alternate" type="application/atom+xml" title="Atom" href="{% url "blog_post_feed" "atom" %}">
```

**Missing:** JSON Feed, RSS for pages/galleries, podcast RSS (third-party `mezzanine-podcast`), Atom `rel=self` beyond `feed_url`, pagination of feeds, ETag/Last-Modified, content-type negotiation on the HTML URL.

`blog_post_feed` (`blog/views.py:104-111`) is a 3-line format→class map. Unknown format → 404. That is the entire feed controller.

### Sharing — two `<a>` tags and a 2012 Twitter app

Blog detail (`mezzanine/blog/templates/blog/blog_post_detail.html:91-95`):

```html
{% set_short_url_for blog_post %}
<a class="btn btn-sm share-twitter" ... href="https://twitter.com/intent/tweet?url={{ blog_post.short_url|urlencode }}&amp;text={{ blog_post.title|urlencode }}">
<a class="btn btn-sm share-facebook" ... href="https://www.facebook.com/sharer/sharer.php?u={{ request.build_absolute_uri }}">
```

`set_short_url_for` calls `Displayable.generate_short_url()` — bit.ly v3 if `BITLY_ACCESS_TOKEN` is set, else stores `"unset"` and uses the absolute URL. **No Open Graph image means the Facebook share card is whatever Facebook's scraper invents from the first `<img>`.**

`mezzanine.twitter` is the **opposite** direction: poll Twitter API 1.1 (`statuses/user_timeline`, `lists/statuses`, `search/tweets`) and render a sidebar of tweets. It is **deprecated** (`mezzanine/twitter/checks.py`: `mezzanine.twitter.W001`) and the 1.1 API it calls is itself retired. `TweetableAdminMixin` can "Send to Twitter" on save. That is not a sharing platform; it is a dead inbound widget.

No AddThis, no Web Share API, no LinkedIn/Mastodon/Threads, no copy-link, no OG debugger-friendly markup.

### Adjacent "social" surfaces

- **Disqus** or built-in `ThreadedComment` (`mezzanine/generic/`)
- **Ratings** (integer range, cookie-deduped, optional AJAX JSON)
- **Gravatar** from comment email
- **Akismet** for comment/form spam
- **Google Analytics** (legacy `analytics.js`)

These are HTML-page features, not an API.

---

## 5. Is there ANY public API (REST / GraphQL / JSON)?

### In-tree: no.

Grep across `*.py` / `*.rst` / `*.cfg` / `*.toml` for `rest_framework`, `graphql`, `serializer` (as Django REST), `webhook`, `cors`, `TokenAuthentication`, `openapi`, `swagger`, `JsonResponse`:

| Term | Hits in product code |
|---|---|
| `rest_framework` | none |
| `graphql` | none |
| `serializer` | TinyMCE minified JS only |
| `webhook` | none |
| `cors` / `TokenAuthentication` | none |
| `openapi` / `swagger` | none |
| `JsonResponse` | none |

`setup.cfg install_requires` is Django + comments + Pillow + bleach + requests + grappelli/filebrowser-safe. **No DRF. No graphene. No strawberry. No pydantic.**

### What *looks* like JSON (and is not a content API)

| Endpoint | Auth | Payload | Purpose |
|---|---|---|---|
| `/displayable_links.js` (`core/views.py:161`) | none special (admin TinyMCE) | `[{"title","value"}]` | Link picker in the editor |
| `/admin_keywords_submit/` | `@staff_member_required` | `text/plain` `"ids\|titles"` | Admin keyword widget |
| `POST /rating/` if `CONTENT_TYPE: application/json` | session/cookie | `{rating_average, rating_count, rating_sum}` | Star-rating AJAX |
| `POST /comment/` AJAX errors | session | `{errors: …}` or `{location}` | Comment form |
| `GET /jsi18n/<packages>/` | public | Django JS catalog | Admin i18n |
| Blog `/feeds/rss\|atom` | public | XML | Syndication |
| Forms admin CSV export | staff | `text/csv` | Form entries download |

`request_is_ajax` (`mezzanine/utils/deprecation.py`) is literally `CONTENT_TYPE == "application/json"`. That is a comment/rating convenience, not content negotiation.

The word **"API"** in first-party docs means:

1. `SearchableManager.search()` — Python
2. "API for custom content types" — subclass `Page` / `Displayable` (`docs/content-architecture.rst`)
3. Third-party **`mezzanine-api`** listed in `docs/overview.rst:178` as an external plugin (`https://github.com/gcushen/mezzanine-api`)
4. `mezzanine-recipes` "with built-in REST API" — also third-party
5. Outbound HTTP to bit.ly, Twitter 1.1, Akismet, Disqus, Posterous/Tumblr importers

**There is no first-party HTTP content API.** A React/Next/iOS client cannot list published blog posts as JSON without writing the entire serialization + auth + pagination + draft-preview layer from scratch.

---

## 6. Headless viability today — NO (proof)

A headless CMS must let a separate frontend (Next.js, mobile, another site) **read, preview, and subscribe to content over HTTP** without rendering Django templates.

### Proof points from this tree

1. **Every public content view returns `TemplateResponse`.**
   - Pages: `mezzanine/pages/views.py:100` — template-name cascade (`pages/<slug>.html`, parent slugs, `pages/<content_model>.html`, `pages/page.html`).
   - Blog list/detail: `TemplateResponse` (`blog/views.py:75, 101`).
   - Search: `TemplateResponse` (`core/views.py:114`).
   - No `Accept: application/json` branch. No serializer. No `?format=json`.

2. **Page resolution is middleware + template, not a resource.**
   `PageMiddleware.process_view` loads the page by slug, enforces `login_required` via Django session login, runs `page_processors` that return **dicts for template context or an `HttpResponse`**. That contract is HTML-era. There is no "give me the page JSON for this slug."

3. **Draft preview is "log into admin, hit the same URL as a staff user."**
   `PublishedManager.published(for_user=)` returns `.all()` if `for_user.is_staff` (`managers.py:64-65`). Test: anonymous GET on a draft → 404; staff GET → 200 (`tests/test_core.py:121-131`). No preview token, no signed URL, no `?preview=1` for an unauthenticated Next.js preview mode, no draft/published split over HTTP.

4. **No API authentication.**
   Session cookies + CSRF + `staff_member_required`. No token, no JWT, no application credentials, no scoped keys. A static-site builder cannot fetch at build time without impersonating a browser session.

5. **No CORS, no OPTIONS handlers, no `Access-Control-Allow-Origin`.**
   A browser app on another origin cannot call anything even if you pretended rating JSON was a content API.

6. **Content types are Django models + templates, not a schema document.**
   `Page` subclasses register themselves via model inheritance and `PageAdmin`. The frontend discovers types by… reading Python. There is no `/api/schema`, no generated TypeScript.

7. **Rich text is stored HTML** (`RichTextField` + TinyMCE + bleach). A headless frontend gets a string of Mezzanine-filtered HTML with relative media URLs, not portable blocks (Payload/Sanity lexical, WordPress Gutenberg). `absolute_urls` exists only for RSS.

8. **i18n for a headless client does not exist.** No `?locale=fr`, no `Accept-Language` content selection API, no translated slug map.

9. **Search cannot be reused.** Results are a Python list of model instances scored in-process, rendered as HTML. No JSON hits, no cursor, no highlight fragments.

10. **The only documented REST option is an unmaintained third-party plugin** (`mezzanine-api`), not a core guarantee. Depending on it is not a product strategy.

**Conclusion:** you can scrape HTML or write your own DRF app next to Mezzanine. You cannot point Next.js `fetch` at this CMS today and ship. WordPress has done that since 4.7 (2016). Payload/Strapi/Sanity *are* the API. Mezzanine is a theme engine with an admin.

---

## 7. What a modern API surface must be

Minimum to stop losing to WordPress REST + SEO plugins + WPML, and to enter the Payload/Strapi conversation:

### 7.1 Typed content API (REST, versioned)

- `GET /api/v1/{type}` list with cursor pagination, filters (`status`, `locale`, `updated_since`, taxonomy), sparse fieldsets, includes.
- `GET /api/v1/{type}/{id|slug}` retrieve.
- Stable resource IDs (UUID) **and** locale-aware slugs.
- Published-only by default; drafts only with preview/auth.
- Media as first-class resources with srcset/focal point.
- Relationships: page tree as `parent`/`children`/`ancestors`, blog `categories`/`related`, keywords.
- **Locale as a first-class query dimension**, not a cookie.

### 7.2 Preview API

- Staff (or CI) mints a **short-lived signed preview token** for a specific object + revision.
- `GET /api/v1/preview?token=…` returns the draft payload the public API would hide.
- Works with Next.js Draft Mode / Remix preview / any SSR without a Django session cookie.
- Revision history: `GET /api/v1/{type}/{id}/revisions`.

### 7.3 Webhooks + content subscriptions

- On publish / unpublish / update / delete / schedule-fire: POST a signed payload to registered URLs (`X-Mezzanine-Signature`).
- At-least-once delivery, retries, dead-letter, delivery log in admin.
- Optional WebSocket / SSE `GET /api/v1/subscribe?types=blog_post` for live preview and ISR revalidation without polling.
- First consumer: Vercel/Netlify on-demand revalidation. That is how WordPress+Next and Contentful win.

### 7.4 OpenAPI as source of truth

- Every route emitted from the same schema that validates requests.
- `/api/v1/openapi.json` + Swagger/Redoc in admin.
- Error shape: `{code, message, details[], request_id}`.
- Idempotency keys on writes.

### 7.5 GraphQL optional, not mandatory

- `POST /graphql` generated from the same content-type schema.
- Relay-style connections, persisted queries, depth/cost limits.
- Ship it because WordPress has WPGraphQL and Payload has GraphQL by default — but **do not make it the only API.** REST + OpenAPI is how Python/Go/mobile clients actually integrate.

### 7.6 Auth, tenancy, rate limits

- Application tokens (read / preview / write scopes) in admin.
- Optional user JWT for comments/ratings from a headless frontend.
- Site (already a Mezzanine primitive) as tenant key.
- Rate limit + audit log.

### 7.7 Search as an HTTP resource

- `GET /api/v1/search?q=&types=&locale=` returning `{hits:[{id,type,title,url,highlight,score}], facets, next_cursor}`.
- Backed by Postgres FTS at v1, OpenSearch/Meilisearch adapter at v2. Kill `icontains`+Python score.

### 7.8 SEO as data, not just `<meta>` tags

- Return `seo: {title, description, canonical, robots, og, twitter, jsonld, hreflang[]}` on every Displayable.
- Sitemap becomes `GET /api/v1/sitemap` **and** still emits `sitemap.xml` (plus image/news/hreflang).
- GA4 / privacy-friendly analytics as a setting, not a 2014 snippet.

Without 7.1–7.4, "add an API" is a plugin graveyard. That is the `mezzanine-api` lesson.

---

## 8. Revolutionary: schema-as-code that generates everything

WordPress content types are PHP `register_post_type` + ACF field groups + a REST controller that almost maps + a GraphQL plugin that almost maps + a separate SEO plugin that writes into `postmeta`. Payload is better: a TypeScript `CollectionConfig` generates admin + REST + GraphQL. **Payload does not generate a first-class Python client, and the admin is React-only.**

Mezzanine's actual asset is that **content types are already Python classes** (`Page` / `Displayable` subclasses). The miss is that those classes only generate an admin fieldset and an HTML template lookup. The same declaration should be the single source for every surface.

### The unit: a content schema, not a ModelAdmin

```python
# mezzanine_schema/blog.py  — the only file a developer writes
from mezzanine.schema import content_type, fields, i18n, seo, access

@content_type(
    slug="blog_post",
    label="Blog post",
    kind="collection",          # collection | singleton | tree
    locales=i18n.inherit(),     # slug IS translatable
    seo=seo.DisplayableSEO(),   # title, description, og, canonical, robots, jsonld
    access=access.public_read_staff_write(),
    webhooks=("publish", "unpublish", "update"),
    search=("title", "content", "keywords"),
)
class BlogPost:
    title = fields.Text(i18n=True, search_weight=5)
    slug = fields.Slug(from_field="title", i18n=True, unique_per_locale=True)
    content = fields.RichBlocks(i18n=True, search_weight=1)  # portable blocks, not TinyMCE HTML
    excerpt = fields.Text(i18n=True, seo="description")
    cover = fields.Media(kind="image", og=True)
    categories = fields.Relation("blog_category", many=True)
    author = fields.User()
    status = fields.Workflow("draft", "in_review", "published")
    publish_at = fields.Datetime(index=True)
```

One decorator. From it the compiler emits:

| Artifact | Consumer | Why it beats the field |
|---|---|---|
| Django model + migrations | runtime | today's Mezzanine, but generated |
| Admin (existing Grappelli *or* a new React admin) | editors | fieldsets, i18n tabs, SEO preview, webhook delivery log |
| REST `/api/v1/blog_posts` | any HTTP client | OpenAPI-first, typed filters |
| GraphQL `blogPosts` / `blogPost` | optional | same resolvers as REST |
| `openapi.json` | humans + codegen | not a plugin |
| **TypeScript SDK** (`@mezzanine/client`) | Next/Remix/mobile | `client.blogPosts.list({locale, previewToken})` |
| **Python client** (`mezzanine.client`) | SSG, data science, other Django apps | same operations, sync+async |
| JSON Schema / Pydantic / Zod | validate at edges | one source, three languages |
| Webhook payload types | infra | ISR, Slack, search indexer |
| Search document mapping | Postgres FTS / Meilisearch | no more `icontains` |
| Sitemap + hreflang + JSON-LD | SEO | generated from `seo=` |

### Why this beats WordPress

- WordPress REST is a lowest-common-denominator dump of `WP_Post`. Custom fields are `meta` bags. Types are folklore. GraphQL is a third plugin. Preview is cookies + `?p=`. SDKs are community.
- Schema-as-code **cannot drift**: if a field is not in the schema it is not in admin, REST, GraphQL, or the TS client. WordPress drifts by construction.

### Why this beats Payload

- Payload's schema is TypeScript. Python shops, data teams, and Django's ORM/admin/ecosystem are locked out.
- Generating **both** a TS SDK **and** a Python client from one schema makes Mezzanine the only CMS that is native to *both* the Next.js frontend *and* the Django/data backend — which is the actual split in serious organizations.
- Tree pages + scheduled publish + multi-site (`SiteRelated`) are Mezzanine primitives Payload still treats as extras. Keep them; expose them through the schema.

### Implementation sketch (do not bolt DRF onto `Displayable`)

1. **Introduce `mezzanine.schema`** as the public authoring API. Keep `Displayable` as the generated base (status, timestamps, site, SEO) so existing subclasses can be *declared* rather than hand-written.
2. **Rich text becomes portable blocks** (paragraph, heading, image, embed, code) with an HTML renderer for the legacy theme and a JSON renderer for headless. TinyMCE HTML stays import-only.
3. **Codegen step** (`manage.py schema_build` + a `pyproject` plugin) writes:
   - `mezzanine_generated/models.py`
   - `mezzanine_generated/api/` (Starlette/Django Ninja or DRF, but **views are generated**, not hand-grown)
   - `mezzanine_generated/openapi.json`
   - `packages/client/` TypeScript (openapi-typescript)
   - `mezzanine/client/` Python (httpx)
4. **Preview tokens + webhooks ship in core**, not as "mezzanine-api 2.0".
5. **Search v1 = Postgres `tsvector` generated from `search=`**, HTTP at `/api/v1/search`. Adapter interface for Meilisearch later.
6. **SEO object is a fieldset and a JSON member**, not three `<meta>` blocks. Templates become one consumer of that object; the API is another.

That is how Mezzanine stops being a 2012 WordPress lookalike and becomes the Django-native answer to Payload — without abandoning the admin, the page tree, or the Python developers who still actually run the backend.

---

## File index (cited)

| Concern | Path |
|---|---|
| Search SQL / scoring | `mezzanine/core/managers.py` |
| Search HTTP view | `mezzanine/core/views.py` |
| Search docs ("API") | `docs/search-engine.rst` |
| Search settings | `mezzanine/core/defaults.py` (`SEARCH_*`, `STOP_WORDS`) |
| Search UI | `mezzanine/core/templates/search_results.html`, `includes/search_form.html` |
| SEO model | `mezzanine/core/models.py` (`MetaData`, `Displayable`) |
| SEO admin | `mezzanine/core/admin.py` |
| SEO HTML | `mezzanine/core/templates/base.html`, `pages/templates/pages/page.html`, `blog/templates/blog/blog_post_detail.html` |
| Sitemap | `mezzanine/core/sitemaps.py`, `mezzanine/urls.py` |
| robots | `mezzanine/core/static/robots.txt`, `mezzanine/urls.py` |
| Keywords / ratings / comments | `mezzanine/generic/models.py`, `fields.py`, `views.py`, `urls.py` |
| Feeds | `mezzanine/blog/feeds.py`, `blog/urls.py`, `blog/views.py` |
| Share buttons | `mezzanine/blog/templates/blog/blog_post_detail.html` |
| bit.ly | `mezzanine/core/models.py` `generate_short_url` |
| Twitter (deprecated inbound) | `mezzanine/twitter/` |
| i18n content | `mezzanine/core/translation.py`, `blog/translation.py`, `pages/translation.py`, `forms/translation.py`, `galleries/translation.py`, `conf/translation.py` |
| i18n docs | `docs/multi-lingual-sites.rst` |
| i18n switcher | `mezzanine/core/templates/includes/language_selector.html` |
| i18n default off | `mezzanine/project_template/project_name/settings.py`, `mezzanine/utils/conf.py` |
| UI locales | `mezzanine/core/locale/*` (38) |
| Page HTML rendering | `mezzanine/pages/views.py`, `pages/middleware.py` |
| Draft = staff HTML | `mezzanine/core/managers.py` `PublishedManager`, `tests/test_core.py` |
| Third-party REST mention | `docs/overview.rst` (`mezzanine-api`) |
| Dependencies (no DRF) | `setup.cfg` |

---

## Scorecard vs the surfaces WordPress won with

| Surface | WordPress (core + winning plugins) | Mezzanine today | Gap |
|---|---|---|---|
| Public content API | WP REST (core since 4.7), WPGraphQL | **None** | Existential |
| Preview for headless | Preview links + Application Passwords + draft mode | Staff session on HTML URL | Existential |
| Webhooks | WP webhooks / Jetpack / various | **None** | Existential |
| OpenAPI / typed SDK | community, imperfect | **None** | Existential |
| Search | MySQL LIKE *or* ElasticPress / Algolia | **MySQL/Postgres LIKE + Python score** | Product |
| SEO | Yoast / RankMath (OG, schema, canonical, sitemap+) | meta title/desc/keywords + basic sitemap | Product |
| Multilingual content | WPML / Polylang (slugs, hreflang, jobs) | optional modeltranslation, no slug i18n | Product |
| UI i18n | many locales | **38 gettext catalogs — this one is fine** | Parity |
| Feeds | RSS + Jetpack JSON | Blog RSS/Atom | Minor |
| Sharing | OG + share buttons + Jetpack | Two `<a>` tags, no OG | Product |
| Headless | official handbook, countless hosts | **Not viable** | Existential |

**INTERFACE verdict:** Mezzanine's public surface is an HTML website. Everything WordPress weaponized after 2015 — REST, SEO data, real multilingual content, preview-for-JAMstack — is either a Python-only convenience, a third-party footnote, or absent. Do not "add django-rest-framework to blog." Ship **schema-as-code → Admin + REST + GraphQL + TS SDK + Python client**, or concede the interface layer permanently.
