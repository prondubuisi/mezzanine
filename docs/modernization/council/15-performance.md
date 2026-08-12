# General PERFORMANCE — Executive Verdict

**Unit:** Byzantine council, independent, from code.
**Repo:** `/Users/prondubuisi/gitrepos/dev/mezzanine`
**Scope:** request path, cache, search, admin tree, static/image pipeline, WordPress delta, edge-ready redesign.
**Repo was not modified.**

---

## EXECUTIVE VERDICT

Mezzanine’s performance story is **2010-era origin-first, done with unusual care**. The page-menu query, ascendant walk, mint cache, and two-phase `nevercache` are genuinely clever for a Django CMS of that generation. The architecture is **not** a modern web-performance stack.

**One-line judgment:** a well-tuned single-origin Django app that can look fast on a small brochure site *if* you bolt on Memcached/Redis and hide it behind nginx. It cannot compete with WordPress 6.8 + Redis object cache + a page-cache plugin + Cloudflare + speculative loading, and it has no path to an edge/ISR world without a rewrite of the response contract.

**Scorecard (origin, uncached, typical page):**

| Surface | Grade | Why |
|---|---|---|
| Page-view request path | C+ | Heavy middleware; cache hit still runs session + auth + second-phase render |
| Caching model | B− | Mint + two-phase is smart; origin-only, no Vary, no HTTP/CDN contract |
| Search | D | `icontains` LIKE, materialize-all, Python scoring. Dies at ~10k rows |
| Admin page tree | C | One clever query, then render the entire tree + per-node permission + N updates on drag |
| Images / static | D+ | On-demand PIL JPEG thumbs; no WebP/AVIF/srcset; compressor optional; jQuery 3.4 / Bootstrap 3 |
| Query hygiene | B | Blog list and menus do `select_related`/`prefetch`; search, save, slug rewrite, sitemap do not |
| Edge / ISR readiness | F | Full Django request required; HTML is not addressable by content hash; no revalidation API |

**If we do nothing else:** ship a documented production recipe (Redis + nginx `proxy_cache` + hashed static) and stop claiming the built-in cache is “aggressive.” It is a *developer convenience*, not a CDN.

---

## 1. Request path for a page view

Default stack from `mezzanine/project_template/project_name/settings.py`:

```
UpdateCacheMiddleware                  # outermost — response writer + nevercache phase 2
SessionMiddleware
CommonMiddleware
CsrfViewMiddleware
AuthenticationMiddleware
MessageMiddleware
XFrameOptionsMiddleware
CurrentRequestMiddleware               # thread-local request (used by CurrentSiteManager)
RedirectFallbackMiddleware             # 404 → Redirect.objects.get
AdminLoginInterfaceSelectorMiddleware  # admin login POST only
SitePermissionMiddleware               # staff: SitePermission.objects.get
PageMiddleware                         # slug walk, processors, often *is* the view
FetchFromCacheMiddleware               # innermost — GET + anon cache lookup
```

`mezzanine.utils.conf.set_dynamic_settings` **strips both cache middlewares** if `CACHES` / `CACHE_BACKEND` is unset. The project template’s `local_settings.py` does **not** define a cache. Out of the box, production is uncached origin Django.

### Cache-HIT path (anonymous GET, `CACHES` configured)

Django still runs the full `process_request` chain *before* the view:

1. Session cookie parsed (needed to know “anonymous”).
2. Auth middleware loads the user (or AnonymousUser).
3. `CurrentRequestMiddleware` stashes the request in a thread-local.
4. `FetchFromCacheMiddleware.process_request` builds
   `{prefix}.{site_id}.default` + i18n suffix + `request.get_full_path()`, MD5-hashes it, `cache_get`.
5. On hit: returns `HttpResponse(cached_bytes)`. **View, `PageMiddleware`, menus, search, DB content: skipped.**
6. Response still walks back out. `UpdateCacheMiddleware.process_response` **always** splits the body on the `nevercache.{NEVERCACHE_KEY}` delimiter, `Template(...).render(RequestContext)` for every odd fragment, rewrites `Content-Length`, flushes messages, and re-runs `CsrfViewMiddleware.process_response`.

A “cached” page is **not** a static file. It is still a Django worker, a session, CSRF cookie logic, and N template compiles of the nevercache islands (messages, user panel, language selector, ratings, form CSRF).

Compare: WP Super Cache / LiteSpeed / nginx `try_files` can serve HTML with **zero** application runtime.

### Cache-MISS / first-byte path (anonymous page)

After `FetchFromCache` sets `request._update_cache = True`:

1. **URL resolve** to the catch-all `pages.views.page` (or a blog/form/gallery pattern under a page prefix).
2. **`SitePermissionMiddleware.process_view`**: superuser short-circuit; staff issues `SitePermission.objects.get(user=, sites=current_site_id())`.
3. **`PageMiddleware.process_view`** (this *is* the page controller):
   - `path_to_slug(request.path_info)`
   - `Page.objects.with_ascendants_for_slug(slug, for_user=, include_login_required=True)` — **one** `published` queryset, `slug__in=['a','a/b','a/b/c']`, `order_by('-slug')`, then a Python parent-chain check. Caches `_ascendants` on the leaf.
   - Assigns `request.page`, runs `context_processors.page` → `page.set_helpers`.
   - Enforces `login_required` → `redirect_to_login`.
   - If the resolved view is **not** `page_view`, **invokes that view from inside middleware** (blog post, form, custom app). A 404 whose slug *exactly* matches a page is swallowed and retried as a page.
   - Runs `page_processors` for `page.content_model` and `slug:{slug}`. A processor may return `HttpResponse` (forms) or a dict merged into `extra_context`.
   - Otherwise calls `pages.views.page`, which builds a template candidate list from slug, `get_content_model().get_template_name()`, content type, and each ascendant.
4. **Template render** (`base.html`):
   - `{% page_menu %}` × 4 (dropdown, breadcrumb, left tree, footer). First call loads **every published page** with `select_related(*all non-proxy Page subclasses)` and groups by `parent_id` in Python. Subsequent calls are dict lookups.
   - `{% compress css/js %}` if django-compressor is installed.
   - `{% nevercache %}` islands serialized to tokens.
   - `{% editable_loader %}` for staff: jQuery tools + TinyMCE + `displayable_links_js` URL (that view walks **all** Displayable via `url_map`).
5. **`UpdateCacheMiddleware`**: if anon + 200 + text + `_update_cache` + `max-age` not 0, `cache_set` of **pre-nevercache** `response.content`. Then second-phase render as above.

### Hidden per-request taxes (even when “just a page”)

| Tax | Where | Cost |
|---|---|---|
| Thread-local request | `CurrentRequestMiddleware` | Required for `current_site_id()` / `CurrentSiteManager` |
| Site lookup | `utils/sites.current_site_id` | Session `site_id`, else `Site.objects.get(domain__iexact=host)` (mint-cached if cache on) |
| Editable settings | `mezzanine.conf.Settings._load` | `Setting.objects.all()` **once per request** (WeakKeyDictionary) |
| 404 fallback | `RedirectFallbackMiddleware` | Extra `Redirect.objects.get` on every 404 |
| `get_content_model()` | views, processors, admin | `getattr(page, page.content_model)` — extra query unless `select_related` |
| Parent walk on save | `Page.save` | `while parent is not None: parent = parent.parent` — N queries, no cache |

`PageMiddleware` calling the view from `process_view` is a performance *and* correctness smell: inner middleware `process_view` never runs for page-owned URLs, exception handling is custom, and the cache layer cannot distinguish “this view is uncacheable” except via `Cache-Control` / `max-age` on the response.

---

## 2. Caching model

Documented in `docs/caching-strategy.rst`. Three ideas stacked:

### 2.1 Page cache (Django per-site cache, Mezzanine fork)

- `FetchFromCacheMiddleware` (request, innermost) / `UpdateCacheMiddleware` (response, outermost).
- **Authenticated users are never cached.** `CACHE_ANONYMOUS_ONLY = False` is explicitly ignored.
- Keys **do not honor `Vary`**. Every anonymous visitor gets the same HTML per URL. A/B, geo, currency, feature flags: all broken or must live inside `nevercache`.
- Key = `CACHE_MIDDLEWARE_KEY_PREFIX` + `current_site_id()` + `"default"` (device detection removed in 4.3; dummy kept for key stability) + Django i18n suffix + **`request.get_full_path()`** (query string included).
- Keys are MD5-hexed before hitting the backend (`memcache` 255-char limit).
- Only `text/*`, non-streaming, status 200 (in `DEBUG`, non-200 is skipped so tracebacks render).

### 2.2 Two-phase rendering (`nevercache`)

Based on Holovaty / django-phased. First render leaves `{% nevercache %}…{% endnevercache %}` as literal tokens `nevercache.{NEVERCACHE_KEY}`. Cached blob is the *almost*-static page. Phase 2, on every response including hits, splits and renders the islands with a fresh `RequestContext`.

Used in stock templates for: messages, language selector, user panel, CSRF inside forms, ratings.

Costs:

- `Template(part.decode("utf-8"))` **compiled on every request**, every island. No compiled-template cache.
- Phase 2 has **no view context** — only context processors. Easy to accidentally cache personalized HTML if a developer puts it outside `nevercache`.
- `NEVERCACHE_KEY` is a secret delimiter. If it appears in content, the page splits wrong.

### 2.3 Mint cache (Disqus snippet)

`cache_set` packs `(value, refresh_time, refreshed)` and stores with TTL = requested + `CACHE_SET_DELAY_SECONDS` (default **30s**).

`cache_get`: if `now > refresh_time` and not yet `refreshed`, writes the stale value back with a 30s TTL marked `refreshed=True` and returns `None` (fake miss). One unlucky client regenerates; everyone else keeps eating stale.

This is **origin-process stale-while-revalidate**, not HTTP `stale-while-revalidate`. The CDN never sees it. There is no `Age`, no `ETag`, no `Surrogate-Control`, no purge API keyed by path or content.

`add_cache_bypass(url)` appends `?t=<epoch>` so comment/rating POSTs don’t land on a stale GET. That also **fragments the cache** (full path is in the key).

### 2.4 What is *not* here

- No object-cache layer around ORM (`Page.get`, menus, settings, site). Django’s cache framework is used only for the page blob and site_id.
- No fragment cache besides `nevercache` (which is the inverse: cache everything *except* fragments).
- No cache versioning / content hash. Publish does not purge. You wait out `CACHE_MIDDLEWARE_SECONDS`.
- No CDN integration, no surrogate keys, no `Cache-Control` policy helper.
- Project template ships **no** `CACHES`. Docs say “preconfigured to cache aggressively when deployed… with a cache backend installed.” The “when” is doing a lot of work.

**Honest description:** a mint-cached anonymous full-page store with ESI-by-string-split, sitting in whatever Django cache backend the operator remembered to configure.

---

## 3. Search performance

`mezzanine.core.views.search` → `Displayable.objects.search(query, for_user=)` → `SearchableManager.search`.

### Algorithm

1. Tokenize: quotes = phrase, `+` required, `-` excluded, stopwords stripped (`STOP_WORDS` is a long English tuple).
2. For each remaining term × each `search_fields` key, emit `Q(field__icontains=term)`. Combine with `OR` (optional) / `AND` (required) / `AND NOT` (excluded). `distinct()`.
3. Default fields on `Displayable`: `{"keywords": 10, "title": 5}` — keywords are the denormalized `keywords_string` (good; `KeywordsField.related_items_changed` writes a single string).
4. Rich text models add `content` via inheritance.
5. `SEARCH_MODEL_CHOICES` default `("pages.Page", "blog.BlogPost")`. Abstract `Displayable.search` loops **each concrete leaf model**, runs `published().search().annotate_scores()`, concatenates Python lists, `sorted(..., key=result_count, reverse=True)`.
6. `annotate_scores` **`list()`s the entire queryset**, then for every row × field × term does `field_value.lower().count(term) * weight`, then divides by `age ** SEARCH_AGE_SCALE_FACTOR` (default **1.5**).
7. View then `paginate`s that **list**. Django’s `Paginator` on a list is fine; the damage is already done.

### Why this will not scale

| Issue | Effect |
|---|---|
| `LIKE '%term%'` | Cannot use B-tree. Seq scan of `title` / `content` / `keywords_string` per model |
| No `SearchVector` / GIN / Haystack / ES | No ranking in the database |
| Heterogeneous union in Python | N queries + full materialization; no `LIMIT` pushed to SQL |
| Scoring in Python | Every matching row loaded, including 50k-char richtext |
| `Page` search includes **all subclasses** via MTI | Searching “Page” hits the page table; scoring may `getattr` missing subclass fields |
| `slug` is `max_length=2000`, **not indexed** | Lookup by slug in middleware is `slug__in` on a 2000-char column |
| Only `publish_date` is `db_index=True` | Status + expiry filters are unindexed |

**`url_map` / sitemap / TinyMCE link list** (`DisplayableManager.url_map`, `displayable_links_js`): iterate every `Displayable` subclass, `published().filter(**kwargs)`, call `get_absolute_url()` per row. Sitemap of a 20k-post blog is a memory and query bomb.

**Verdict:** fine for a 200-page brochure. Indefensible past a few thousand posts. WordPress core search is also LIKE-based and also bad — but the ecosystem (ElasticPress, Relevanssi, Algolia, Jetpack search) is how real sites survive. Mezzanine has no equivalent hook that is used in-tree.

---

## 4. Admin tree performance

`PageAdmin.change_list_template` → `admin/pages/page/change_list.html` → `{% page_menu "pages/menus/admin.html" %}`.

### What is good

`page_menu` loads the tree **once**:

```python
rel = [m.__name__.lower() for m in Page.get_content_models() if not m._meta.proxy]
published = Page.objects.published(for_user=user).select_related(*rel)
```

That is the right shape: one query, MTI children joined, grouped by `parent_id` in a `defaultdict`. Recursion is template-side, not query-side.

### What is not

1. **The entire tree is rendered as nested `<ol>` HTML.** 2,000 pages = 2,000 `<li>`s, 2,000 permission blocks, 2,000 “Add…” `<select>`s cloned with every content type. No windowing, no lazy children, no virtualization.
2. **`{% set_page_permissions page %}` per node** calls `page.get_content_model()` + `user.has_perm` + `model.can_{add,change,delete}(request)`. `select_related` usually saves the extra query; the Python/auth work does not.
3. **jQuery UI + `jquery.mjs.nestedSortable`** on the whole tree (`page_tree.js`). `connectWith` is called out in a comment as a known performance bug they worked around. Drag-stop POSTs `{id, parent_id, siblings: [...]}`.
4. **`admin_page_ordering`**: if parent changes, `set_parent` (save + possible `set_slug` which `filter(slug__startswith=)` and **`.save()` every descendant**). Then:
   ```python
   for i, page in enumerate(pages.order_by("_order")):
       Page.objects.filter(id=page.id).update(_order=i)
   for i, page_id in enumerate(request.POST.getlist("siblings[]")):
       Page.objects.filter(id=get_id(page_id)).update(_order=i)
   ```
   That is **O(siblings)** round-trips. No `bulk_update`, no single `CASE` UPDATE, no transaction visible in the view.
5. **`Page.save` rebuilds `titles` by walking `parent.parent…`** — N queries on every save, including slug rewrite.
6. Cookie `mezzanine-admin-tree` remembers open nodes, but **closed branches are still in the DOM**. Collapse is CSS/`$.hide()`, not server-side.

**Breakpoint:** tens of pages = delightful. Hundreds = sluggish. Thousands = unusable (browser + worker). WordPress’s nested-pages / CMS tree plugins hit the same wall; the modern answer is a virtualized tree + `/children?parent=` endpoint.

---

## 5. N+1 and query hygiene (audit)

Mezzanine *does* try. The docs’ “great care to minimize database queries” is not marketing fluff on the happy paths.

**Done right**

- `page_menu`: one query + `select_related` all content types.
- `with_ascendants_for_slug`: one `slug__in` instead of recursive parent fetches (when slugs are the default hierarchical form).
- Blog list: `select_related("user").prefetch_related("categories", "keywords__keyword")`.
- Blog feeds: same.
- Comments: load all, `select_related("user")`, group by `replied_to_id` (same pattern as menus).
- Keywords: denormalized `keywords_string` for search; `select_related("keyword")` when hydrating.
- Settings: one `SELECT *` per request, then WeakKey cache.
- Site id: request-local + mint cache.

**Still N+1 or worse**

| Location | Pattern |
|---|---|
| `Page.save` titles | `while parent: parent = parent.parent` |
| `Page.get_ascendants` fallback | same, when custom slugs break the single-query path |
| `Page.set_slug` | per-descendant `.save()` |
| `admin_page_ordering` | per-sibling `UPDATE` |
| `SearchableManager.search` | all rows × all fields in Python |
| `Displayable.objects.url_map` | one query per model, then `get_absolute_url` each |
| `blog_post_detail` | `select_related()` with **no fields**; `related_posts.published()` extra query, no prefetch of categories/keywords on related |
| `SitePermissionMiddleware` | extra GET for every staff request (not cached) |
| `RedirectFallbackMiddleware` | extra GET on every 404 |
| `get_content_model()` without prior `select_related` | OneToOne fetch |
| Thumbnail tag | `os.path.exists` + possible PIL + local write **on the request that first sees a size** |

**Query budget today:** there is none. No middleware counter, no `assertNumQueries` culture in the hot paths, no fail-CI threshold.

---

## 6. Static asset pipeline and images

### Static

`mezzanine/utils/static.py`:

- `static_lazy = lazy(static, str)` so `{% static %}` in compressed blocks gets a cache-busting URL.
- **If `STATICFILES_STORAGE` ends with `ManifestStaticFilesStorage`, `static_lazy` becomes identity** (workaround for issue #1772). Manifest hashing then depends entirely on Django; Mezzanine’s own lazy trick is disabled.

`django-compressor` is an `OPTIONAL_APP`. If present, `CompressorFinder` is appended and `COMPRESS_OFFLINE_CONTEXT` is seeded. `mezzanine_tags.compress` shadows the real tag; if compressor is absent it is a no-op.

`base.html` still ships:

- Bootstrap 3 + theme + RTL
- jQuery **3.4.1**
- `html5shiv` + `respond.min.js` for **IE < 9**
- TinyMCE 4-era (full plugin tree, `emoticons/img/*.gif`, `moxieplayer.swf`)
- analytics.js (not gtag)

No HTTP/2 push, no module scripts, no `defer`/`async` strategy, no critical CSS, no font subsetting. `editable_loader` dumps more jQuery plugins onto every staff page view.

### Images

`{% thumbnail url w h %}` (`mezzanine_tags.thumbnail`):

- PIL/Pillow, on first request, writes `{MEDIA_ROOT}/{dir}/.thumbnails/{original_name}/{prefix}-{w}x{h}.ext`.
- Formats: **JPEG / PNG / GIF**. No WebP, no AVIF, no JPEG XL.
- No `srcset`, no `sizes`, no `<picture>`, no density descriptors.
- Templates use a single hard-coded size (`90x90` list, `600x0` detail).
- Quality default 95 (large files).
- Filesystem `os.path.exists` / `os.makedirs` — hostile to multi-worker and to remote storage (there is a `MEDIA_URL` absolute-URL upload branch, but existence checks are local).
- Gallery zip import: PIL `verify()` then store originals. No derivative pipeline.

WordPress has generated `srcset` since 4.4, WebP in core since 6.1, big-image downscale, and a plugin/CDN ecosystem (Photon, Cloudflare Images, ShortPixel). Mezzanine is still “one resized JPEG next to the original.”

---

## 7. What WordPress has (and Mezzanine does not)

Not a compliment to WordPress’s core PHP. A compliment to **the stack the median serious WP site actually runs in 2026**.

### Object cache

- `WP_Object_Cache` in core; persistent drop-ins: **Redis Object Cache**, Memcached, APCu.
- All options, transients, post meta, query results can live in Redis. `alloptions` is the infamous footgun; it is still an *object* cache.
- Mezzanine equivalent: Django `cache` used for **page HTML + site_id**. ORM, settings, menus, permissions: hit Postgres/MySQL every miss-path request. `Setting.objects.all()` every request is the WP `alloptions` anti-pattern without the persistent object cache.

### Page cache

- **WP Super Cache** (Automattic): static HTML files, PHP optional.
- **W3 Total Cache**: page + DB + object + fragment + CDN + minify; disk/Redis/Memcached/APCu.
- **LiteSpeed Cache**, **WP Fastest Cache**, **WP-Optimize**, **NitroPack**.
- Host-level: Kinsta/WP Engine/Flywheel page cache in front of PHP.
- Mezzanine: mint-cached response body inside the Django worker. Always a Python process.

### CDN plugins

- Cloudflare (APO, cache rules, Polish, Mirage), KeyCDN, Bunny, StackPath, Jetpack Site Accelerator (Photon), W3TC CDN rewriter, Super Page Cache for Cloudflare.
- Media library URLs rewritten to CDN host; cache purge on publish via plugin hooks.
- Mezzanine: `MEDIA_URL` / `STATIC_URL` can point at a host. No purge, no surrogate keys, no image CDN transforms.

### Images

- Core responsive images (`srcset`/`sizes`), WebP (6.1+), big-image threshold, lazy loading (`loading="lazy"` default since 5.5), fetchpriority on LCP image (6.3).
- AVIF via plugins / hosts / Cloudflare Polish.
- Mezzanine: none of the above.

### Speculative loading (WordPress 6.8)

Shipped in core March 2025. Speculation Rules API. Default: **prefetch, moderate eagerness** (typically on hover / ~200ms before click). Feature-plugin data (~50k sites): **~1.9% median LCP passing-rate lift** — large for a single platform feature. Configurable to prerender / eager. Sites can exclude carts, authenticated routes, query strings. known footgun: background prefetches vs HTTP basic-auth staging.

Mezzanine: no Speculation Rules, no `prefetch`, no speculation-rules exclusion API. A `{% block extra_head %}` is not a strategy.

### Other WP platform wins Mezzanine lacks

- Script loading strategy (`defer`/`async`) since 6.3.
- Autoloaded options audit, Site Health performance guidance.
- Query Monitor as the de-facto query budget tool.
- Opcode cache (OPcache) is assumed; Django has no equivalent beyond `PYTHONOPTIMIZE` / cached bytecode.
- Interactivity API / block theme partial hydration (uneven, but moving).

**Bottom line vs WP:** a stock Mezzanine site vs a stock WP site is a fair-ish fight (both are origin CMS). A stock Mezzanine site vs a *normally hosted* WP site (Redis + page cache + Cloudflare + 6.8 speculation + srcset/WebP) is not a fight.

---

## 8. Revolutionary: edge-ready CMS

Do not “add Redis and a CDN plugin.” Change the **unit of cacheability** from “anonymous Django response” to “addressable published content at the edge.”

### 8.1 ISR-like for Django (the contract)

Next.js ISR: serve a stale HTML shell from the edge, revalidate in the background, address by path + tag.

Django equivalent that actually fits Mezzanine:

1. **Publish is the build event.** `Displayable.save` / status transition to published emits:
   - `content_hash` (see 8.2)
   - surrogate keys: `page:{id}`, `site:{id}`, `type:{model}`, `menu`, `path:{slug}`
   - a revalidation job (Celery / `django-tasks` / webhook to the CDN).
2. **Two artifacts per path:**
   - `shell.html` — fully static, no cookies, no CSRF, no user. Menus baked from a published snapshot.
   - `islands.json` or ESI/HTMX fragments for cart, auth, comments, ratings, messages.
3. **Origin render is a factory**, not the hot path. Workers generate artifacts; nginx / Cloudflare / Fastly / Fastly-Compute / Cloudflare Workers serve them.
4. **On-demand revalidation:** `POST /_revalidate` with signed payload `{paths, tags, hash}`. CDN purges by surrogate key. First viewer after publish may trigger origin fill (ISR); everyone else gets the new artifact.
5. **Preview** is a separate uncached channel (`?preview=` + staff auth), never the public cache key.

This kills two-phase string-split `nevercache`. Islands become real ESI / `<template>` / HTMX endpoints with their own CC.

### 8.2 Content hashes (cache identity)

Today the key is `path + site + lang`. Wrong. Two publishes of the same slug are indistinguishable; two sites on one worker share discipline only via prefix.

Proposed identity:

```
hash = sha256(
    site_id | lang | path |
    page.updated | page.status | titles |
    serialized MTI child (content, gallery image etags) |
    menu_snapshot_hash |
    theme_version | settings_version
)
```

Store `content_hash` on `Displayable`. Emit `ETag: "{hash}"` and `Cache-Control: public, s-maxage=31536000, stale-while-revalidate=86400, stale-if-error=604800`. URL can stay pretty; the hash is the validator. CDN uses hash as immutable object id.

Menus: one `menu_snapshot_hash` per site, invalidated when any `in_menus` page changes. That is the missing piece that makes baked menus safe.

### 8.3 Stale-while-revalidate (HTTP, not mint)

Mint cache already *understands* the idea. Lift it out of `cache_get` and onto the wire:

```
Cache-Control: public, s-maxage=60, stale-while-revalidate=600, stale-if-error=86400
CDN-Cache-Control: public, s-maxage=3600, stale-while-revalidate=86400
Surrogate-Key: page:42 site:1 type:richtextpage menu
```

Origin mint (30s single-regenerator) remains as a **thundering-herd lock** for artifact rebuilds. It is no longer the user-facing cache.

Authenticated HTML: `Cache-Control: private, no-store`. Never mix with public shells. Personalization only in islands.

Purge on comment is a **fragment** purge (`comments:page:42`), not `add_cache_bypass` query-string vandalism.

### 8.4 Image pipeline (AVIF, responsive srcset)

Replace `{% thumbnail %}` with a **derivative service**, not a template tag that writes JPEG during `GET`.

Minimum viable modern contract:

- Ingest original once (gallery zip, filebrowser, featured image).
- Async derivatives: AVIF, WebP, JPEG fallback; widths `320,640,960,1280,1920` (or content-aware).
- Template:
  ```html
  <picture>
    <source type="image/avif" srcset="… 320w, … 640w" sizes="(max-width: 700px) 100vw, 700px">
    <source type="image/webp" srcset="…">
    <img src="…jpeg" width="W" height="H" alt="" loading="lazy" decoding="async">
  </picture>
  ```
- LCP image (featured, first gallery): `fetchpriority="high"` `loading="eager"`.
- Blurhash / 16px LQIP as `background` or `src` placeholder.
- Implementation options, in order of sanity:
  1. **imgproxy / thumbor / Cloudflare Images** in front of `MEDIA` (no derivatives in Django).
  2. In-tree worker writing to object storage with a manifest table `(image_id, fmt, w, hash, url)`.
- Delete the local `.thumbnails/` directory protocol. It does not work under multiple workers or S3.

### 8.5 Query budgets

A CMS that will not name its budget will not keep one.

| Path | Budget (proposal) | Today (order of magnitude, miss) |
|---|---|---|
| Anonymous page, cache miss, origin fill | **≤ 8 queries, ≤ 50ms DB** | ~6–15 (settings + site + page+ascendants + menu + optional comments/keywords) — *close*, protect it |
| Anonymous page, edge hit | **0 origin queries** | N/A (always origin) |
| Blog list page | **≤ 6 queries** (posts+user, categories, keywords, page, settings, site) | already near this if prefetch holds |
| Search | **≤ 2 queries, LIMIT in SQL** | unbounded `icontains` + full materialize |
| Admin tree initial | **≤ 3 queries**, payload **≤ 500 nodes** then `/children` | 1 clever query + N perm + full HTML |
| Admin reorder | **1 transaction, 1–2 statements** | O(siblings) UPDATEs + descendant saves |

Enforcement:

- `QueryBudgetMiddleware` in `DEBUG` and CI: log / 500 if exceeded.
- `assertNumQueries` on a fixture site in CI for `GET /`, `GET /blog/`, `GET /search/?q=x`, `GET /admin/pages/page/`.
- `django-debug-toolbar` stays optional; the budget is not.

### 8.6 Speculative loading (steal 6.8, but safely)

Emit for anonymous HTML:

```html
<script type="speculationrules">
{"prefetch":[{"where":{"and":[
  {"href_matches":"/*"},
  {"not":{"href_matches":["/admin/*","/account/*","/*\\?*"]}}
]},"eagerness":"moderate"}]}
</script>
```

Only on **cacheable shells**. Never prefetch POST-able forms, `login_required` pages, or anything inside `nevercache` islands. Combined with edge cache, hover-prefetch becomes a ~0ms navigation.

### 8.7 Search (stop pretending LIKE is a product)

- Postgres: `SearchVector` + GIN on `(title, keywords_string, content)` materialized column, `ts_rank_cd`, `LIMIT` in SQL, age as a generated column.
- Or an adapter interface with a built-in Postgres backend and an official Meilisearch/Typesense backend.
- Heterogeneous search = `UNION ALL` of per-table limited subqueries, or a single `search_document` table updated on publish.
- Kill `annotate_scores` list-and-count.

### 8.8 Admin tree

- Endpoint `GET /admin/pages/tree/?parent=` returning JSON `{id,title,type,perms,child_count}`.
- Virtualized client (even 200 lines of vanilla JS).
- Reorder: one `UPDATE … FROM (VALUES …)` inside `transaction.atomic`.
- `set_slug` / titles: single recursive CTE, not Python walks.

---

## 9. What I would ship, in order

**P0 — stop lying to operators (1 week)**

- Document a reference `CACHES` (Redis) + nginx `proxy_cache` + `Cache-Control` snippet.
- Emit real `Cache-Control` / `Vary: Cookie` / `ETag` from `UpdateCacheMiddleware`.
- Compile `nevercache` islands once (`lru_cache` on source → `Template`).
- `bulk_update` in `admin_page_ordering`.

**P1 — stop the cliffs (2–4 weeks)**

- Postgres FTS backend behind the existing `.search()` API.
- `{% thumbnail %}` WebP + `srcset` of 3 widths; keep JPEG fallback.
- Query-budget middleware + CI tests on the four hot paths.
- `select_related` the missing blog-detail / related-posts cases; index `(site_id, status, publish_date)` and a reasonable `slug` prefix index (`varchar_pattern_ops` / hash of slug).

**P2 — the actual product change (a quarter)**

- Publish-time artifact + surrogate-key purge.
- Islands instead of `nevercache` string split.
- imgproxy (or equivalent) as the image pipeline.
- Virtualized admin tree.

Without P2, Mezzanine remains a fast-enough **origin CMS for small sites**. With P2, it can be the rare Django CMS that is honest about the edge.

---

## 10. Final word

Mezzanine’s cache middleware is the best part of its performance story and also the tell: **the unit of work is still “a Django request that happens to reuse a bytestring.”** WordPress won the last decade of CMS performance not by writing better loops, but by letting the page leave PHP — object cache, static HTML, CDN, then speculative loading so the next page leaves the browser cache before the click.

Mint cache is proto-SWR. `nevercache` is proto-ESI. `with_ascendants_for_slug` and `page_menu`’s single query are proto-query-budget. The seeds are in the repo. They were never grown into a platform.

**Verdict: capable origin, incapable edge. Do not polish `{% thumbnail %}`. Change what a published page *is*.**
