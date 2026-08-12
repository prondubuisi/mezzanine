# Site clone parity backlog

**Date:** 2026-08-12  
**Branch / work:** `nova/24-six-site-clones-parity`  
**Command:** `python manage.py seed_site_clone --site <slug>`  
**Slugs:** `techcrunch`, `time`, `whitehouse`, `harvard_gazette`, `ted_blog`, `spotify_newsroom`

These are **information-architecture demos** with original copy, inspired by public
sites. They are not pixel clones, scrapes, or affiliated products.

---

## How to run a clone

```bash
# From monorepo or a generated project with blog+forms (e.g. --kit magazine|wporg)
python manage.py seed_site_clone --list
python manage.py seed_site_clone --site techcrunch --flush
# or
just demo-clone techcrunch
```

Suggested project:

```bash
cd /path/to
NOVA_CMS_SRC=/path/to/mezzanine uv run --directory mezzanine \
  python -c "..."  # or nova-project clonelab --kit wporg
```

---

## Cross-cutting gaps (all six)

| ID | Gap | Severity | Cycle note |
|----|-----|----------|------------|
| X1 | Homepage is static kit index, not a **news river** / latest posts | High | Homepage template using `BlogPost` queryset + pagination |
| X2 | **Section landings** are plain pages, not auto-listing by category | High | Page processor or section view: posts by category slug |
| X3 | Bootstrap 3 / Mezzanine chrome ≠ modern magazine/gov design systems | Medium | Theme tokens + layout kits (already partial) |
| X4 | No **author / people** model for bylines and staff bios | Medium | `Ownable` exists; public author profile pages missing |
| X5 | No **featured / hero / package** story layout | Medium | Document body blocks beyond html-only (Y1.5 schema limited) |
| X6 | **Search** is icontains / optional FTS — not editorial search UX | Medium | Facets by section, date, author |
| X7 | **RSS/Atom** per section not first-class | Low | Wire category feeds in blog URLs |
| X8 | **Paywall / membership** none | Low (product) | Out of Y1; note for TIME-class |
| X9 | **Events / calendar** none | High for TC/TED/Harvard | New optional app or kit model |
| X10 | **Video / transcript** first-class objects missing | High for TED/WH | Media + typed Talk/Briefing |
| X11 | Multi-site works; **newsroom locale switcher** UX missing | Medium | HOST_THEMES + site picker polish |
| X12 | Embargo / multi-channel publish missing | Medium | Schedule exists; no press embargo workflow |
| X13 | Comments off by default — fine; **moderation queue** UX thin | Low | |
| X14 | OG / social card pipeline not productized | Medium | |
| X15 | Admin is ModelAdmin — not a newsroom desk | High | Editorial Desk is north star, not Y1 |

---

## Per-site findings

### techcrunch (`techcrunch`)

| ID | Problem | Type | Evidence |
|----|---------|------|----------|
| TC1 | No infinite-scroll / dense story river homepage | Missing feature | Index is wporg-style static hero |
| TC2 | Crunchbase-like company graph absent | Missing feature | Out of kernel scope |
| TC3 | Events page is static HTML only | Missing feature | X9 |
| TC4 | Topic tags vs categories — only BlogCategory | Missing feature | KeywordsField exists but not section IA |
| TC5 | Trending / most-read widgets absent | Missing feature | No analytics hook |
| TC6 | Seed posts lack featured images | Bug/gap | FileField chooser works in admin; seed skips images |

### time (`time`)

| ID | Problem | Type | Evidence |
|----|---------|------|----------|
| TM1 | Section nav (Politics, World, …) not generated from categories | Missing feature | Manual pages only |
| TM2 | Cover / magazine issue object missing | Missing feature | |
| TM3 | Subscriber / newsletter wall missing | Missing feature | X8 |
| TM4 | Ideas vs news not distinguished by content type | Missing feature | Single BlogPost model |
| TM5 | Multimedia packages unsupported | Missing feature | X10 |

### whitehouse (`whitehouse`)

| ID | Problem | Type | Evidence |
|----|---------|------|----------|
| WH1 | No Executive Order / Proclamation content type | Missing feature | Mapped to BlogPost loosely |
| WH2 | Filters for actions by date/type missing | Missing feature | |
| WH3 | USWDS / gov theme not present | Missing feature | Bootstrap 3 chrome |
| WH4 | Live video / briefing player missing | Missing feature | X10 |
| WH5 | FOIA / advanced search missing | Missing feature | X6 |
| WH6 | Spanish / multi-language not demonstrated | Missing feature | modeltranslation optional |

### harvard_gazette (`harvard_gazette`)

| ID | Problem | Type | Evidence |
|----|---------|------|----------|
| HG1 | School / faculty taxonomy missing | Missing feature | Institute kit scaffold only |
| HG2 | Research story template (experts, papers) missing | Missing feature | |
| HG3 | Campus events calendar missing | Missing feature | X9 |
| HG4 | People directory missing | Missing feature | X4 |
| HG5 | Photo essay / gallery not linked to posts | Missing feature | galleries extra optional |

### ted_blog (`ted_blog`)

| ID | Problem | Type | Evidence |
|----|---------|------|----------|
| TD1 | Talk entity (speaker, duration, embed, themes) missing | Missing feature | X10 |
| TD2 | Playlist / related talks missing | Missing feature | |
| TD3 | Transcript + translation workflow missing | Missing feature | |
| TD4 | Conference series model missing | Missing feature | X9 |
| TD5 | Visual design limited to tokens.css | Missing feature | X3 |

### spotify_newsroom (`spotify_newsroom`)

| ID | Problem | Type | Evidence |
|----|---------|------|----------|
| SN1 | Press kit asset packs incomplete | Partial | Media `is_public` helps; no pack model |
| SN2 | Embargoed publish workflow missing | Missing feature | X12 |
| SN3 | Locale newsrooms UX raw | Missing feature | X11 |
| SN4 | Category RSS polish needed | Missing feature | X7 |
| SN5 | Brand compliance / legal footer patterns manual | Missing feature | |

---

## Bugs encountered during clone build

| ID | Bug | Status | Notes |
|----|-----|--------|-------|
| B1 | Multi-line `{# #}` template comments leak to HTML | **Fixed** | PR #22; single-line only |
| B2 | Project names cannot contain hyphens in `nova-project` | Open | Use `openpublish` not `openpublish-demo` |
| B3 | `just up` background session can die when agent tool times out | Open | Operators should run compose detached in their terminal |
| B4 | Seed may leave orphan categories on `--flush` (categories not deleted) | Open | Flush only posts/pages/forms |
| B5 | Site name / SITE_TITLE | **Mitigated** | Seed now writes `Setting` SITE_TITLE/TAGLINE; project settings.py may still win |
| B6 | makemigrations noise in compose logs for dirty model state | Open | Cosmetic in demo containers |
| B7 | Re-seed without `--flush` did not update HTML (`body` JSON overwrote content) | **Fixed** | Seed sets `body=body_from_html(html)` |
| B8 | `Setting` lacks unique `(site, name)`; duplicate rows possible | Open | Conf may ignore DB when settings.py defines same key |
| B9 | Flush does not clear BlogCategory / keywords | Open | Orphans when switching profiles |
| S1 | All posts same `publish_date` | **Fixed** | Seed staggers by day |
| S5 | `BLOG_USE_FEATURED_IMAGE` default False hides thumbs | Open | Enable in clone projects |
| S6 | Section pages not linked to `/blog/category/<slug>/` | Open | Dual IA until X2 |

### Watch-agent deltas (explore subagents 2026-08-12)

Additional IDs from automated parity watchers (not full re-list of X/TC/TM/WH/HG/TD/SN tables):

| ID | Site | Problem | Severity |
|----|------|---------|----------|
| S2 | all | Blog not in page_menu (only URL include) | Med |
| S3 | all | `primary_nav_label` unused by seed/chrome | Low |
| S4 | all | `related_posts` never seeded | Med |
| S7 | all | Kit index ignores `{% blog_recent_posts %}` | Med |
| S8 | all | Search skips category/author/body JSON | Med |
| TC7–TC9 | techcrunch | Orphan cats; newsletter not chrome; keywords unused | Med–Low |
| TM6–TM8 | time | Empty cats; no Ideas template; generic homepage | Med–Low |
| WH7–WH10 | whitehouse | No PDF attachments; empty shells; no review state; a11y | Med–High |
| HG6–HG9 | harvard_gazette | River/sections/images/press tip form | High–Low |
| TD6–TD9 | ted_blog | River/themes hub/speakers/video seed | High–Med |
| SN6–SN10 | spotify_newsroom | River/sections/OG/press assets/multi-channel | High–Med |

---

## Recommended inclusion order (dev cycle)

1. **B5 + X1** — Site title seed + homepage latest posts (unlocks all news clones)
2. **X2** — Category section listings (TIME/TC/Gazette)
3. **X4** — Public author profiles
4. **X9** — Events optional app (TC, TED, Harvard)
5. **X10** — Video/Talk/Briefing typed content (TED, WH)
6. **X12** — Embargo workflow (newsroom)
7. **X3** — Design system tokens per vertical (gov, magazine, newsroom)

---

## Watch agent protocol (for follow-up runs)

For each site after seed:

1. Hit `/`, each page slug, `/blog/`, `/admin/`
2. Record 404s, empty sections, visual breaks
3. Append rows to this file under the site table
4. File GitHub issues only when Issues are enabled and item is actionable

**Agents invoked:** parent orchestrator (this doc); profile-driven seed tests as automated watchers.
