# Vote E — Frontend / API / Performance

**Voter:** E  
**Seats:** General FRONTEND (`03-frontend.md`), General INTERFACE (`05-interface.md`), General PERFORMANCE (`15-performance.md`)  
**Also read:** `02-editor.md`, `11-python-cms.md`, `10-wordpress.md`  
**Constraint:** Did not modify the Mezzanine repo.

## Ballot

| Motion | Vote | One line |
|---|---|---|
| M1 Strategy | **C** | New product from the kernel. In-place “beat WordPress” is nostalgia. Hospice and library-only waste the salvage. |
| M2 Year-1 ICP | **D** | Python shops replacing a marketing WP box. They buy Django templates + a typed API + fast-by-default. |
| M3 Editor | **B** | Editorial Desk. Authors never load ModelAdmin. Do not staff a Sanity/Wagtail visual editor. |
| M4 Wedge | **A** | One-click WP migrate that keeps URLs/SEO + AI that fills *typed* fields. Kits are the landing, not the wedge. |
| M5 Name | **D** | Defer. Do not ship “Mezzanine 6.” Do not pick Masthead/Nova before the product exists. |
| M6 Commerce Y1 | **A** | None. Catalog+Stripe is a Y2 affordance. Cartridge is landfill. |
| M7 Ecosystem | **B** | Curated signed kits/types only. Three official themes that do not rot. Never a plugin bazaar. |
| M8 Admin fate | **B** | Django admin is the superuser escape hatch. Not the product. Not deleted in Y1. |

Letters only: **C D B A D A B B**

---

## Seat facts that bind every vote

These are not opinions. They are the audits.

**Frontend is NO-SHIP as shipped.** Bootstrap 3.2.0, jQuery 3.4.1, TinyMCE 4.1.10, Chosen 0.9.12, Magnific 0.9.6, unversioned jQuery Tools, a Flash player, a GIF spinner, IE shims, Universal Analytics. Theming is “copy `base.html`, put your app first.” The marketplace is a 14-commit GitHub repo of four Bootstrap 3 skins. There is no token layer, no slot contract, no theme SDK.

Salvage, not the files: named template blocks, the page/blog template ladder, `{% editable %}` *contract*, `{% page_menu %}`, `HOST_THEMES`, server-rendered HTML with no mandatory React.

The rebuild that could beat FSE is the *opposite* of Gutenberg: HTML in git, tokens in CSS, slots in the DB, islands (HTMX/Alpine/vanilla) on the public site, Theme Studio admin-only. Compat class map, no flag day.

**Interface is not headless.** No REST, no GraphQL, no OpenAPI, no webhooks, no preview tokens, no CORS, no JSON content endpoints. Search is `ILIKE` + Python scoring. SEO is 2010 meta keywords + a sitemap with no `lastmod` on pages, no OG, no canonical, no JSON-LD. Content i18n is optional modeltranslation with untranslatable slugs. Feeds are blog RSS/Atom only.

The move is not “add DRF to `BlogPost`.” It is schema-as-code that emits Admin + REST + GraphQL + OpenAPI + TypeScript SDK + Python client from one declaration. Search becomes Postgres FTS (then Meilisearch). SEO is a JSON member every surface consumes.

**Performance is a careful 2010 origin.** Mint cache + two-phase `nevercache` + one-query menus are clever. The unit of work is still “a Django request that reuses a bytestring.” No Vary, no ETag/surrogate keys, no purge, no CDN contract. `{% thumbnail %}` writes JPEG on first GET. No WebP/AVIF/srcset. Admin tree renders every node. Edge/ISR grade: F.

P0 is honesty (Redis + nginx recipe, real `Cache-Control`). P1 is cliffs (FTS, srcset, query budgets). P2 is the product change: publish emits a content hash + surrogate keys; origin is a factory; islands replace string-split `nevercache`. Do not polish `{% thumbnail %}`. Change what a published page *is*.

**Editor (read, not my seat):** Django admin + frozen `grappelli_safe` + TinyMCE 4. Inline edit is a yellow jQuery Tools modal that reloads the page. Preview is “staff are exempt from the published queryset.” Default status is Published. Do not port Gutenberg. Keep `Displayable`, page types, tree, `{% editable %}` tags.

**Python-CMS (read):** Do not become “Wagtail but smaller.” Slot is the Django site you ship on Friday. Relational models, site kits, HTMX, not a second React admin.

**WordPress (read):** You cannot beat gravity. Steal one job. The only 24-month wedge is WP migrate that preserves URLs/SEO + typed AI authoring. Treat this tree as reference architecture, not the thing you ship. Django-admin modernization is a museum project.

Those six documents agree on one strategic shape: **extract the kernel, do not evolve the museum, do not clone Gutenberg or Wagtail, do not open a plugin bazaar.** They disagree on *who pays in year 1* and *how much editor to build*. Frontend + API + performance break those ties as follows.

---

## M1 Strategy — **C**

A Hospice/LTS only · B Extract Displayable/Page library only · C New product that extracts Mezzanine kernel (rebrand) · D Evolve Mezzanine in place to beat WordPress

**Not D.** Frontend cannot compete with block themes from this tree. Interface never entered the API war. Performance has no path to edge/ISR without rewriting the response contract. “Mezzanine 6: now with REST and Tailwind” is the slide the skeptic forbade and the WordPress map called a museum project. Evolving in place keeps Bootstrap 3 class names, Grappelli identity, TinyMCE 4, mint-cache-as-the-CDN, and a brand that already means 2013.

**Not A.** Hospice is honest for *existing* sites (security, Django 5.2 LTS, kill Twitter/UA/Flash). It leaves the salvage on the table: template ladder, `HOST_THEMES`, `Displayable`/`Page`, mint-cache-as-proto-SWR, `nevercache`-as-proto-ESI, page processors, `{% editable %}` as a contract. Those are a product, not a CVE queue.

**Not B.** A tiny Displayable/Page library on stock Django admin is an honest extract and a useful migration target. It does not give us a Theme SDK, a schema compiler, preview tokens, publish-time artifacts, or three first-party themes. Frontend/API/performance need a *shipped surface*, not a PyPI mixin.

**C.** New product. Steal the kernel (mixins, tree, processors, host themes, template ladder, editable tags, mint/SWR idea). Landfill the 2013 JS, Grappelli-as-identity, TinyMCE 4 tree, Cartridge, Twitter, IE stack, `icontains` search, string-split cache. Ship a token+island theme engine, schema-as-code API, and publish-as-build-event. Rebrand so nobody has to put “Mezzanine” on a slide next to WordPress 6.9. Keep a mechanical import from old sites (`LegacyHTML` block + `theme.compat.bootstrap3`). The old package can LTS in parallel; that is A *as a side job*, not the strategy.

This is the only strategy in which frontend’s “new theme engine,” interface’s “schema-as-code,” and performance’s “change what a published page is” are the same roadmap instead of three plugins on a dying tree.

---

## M2 Year-1 ICP — **D**

A Django freelancer Friday-site · B Higher-ed federation (comms director) · C Agencies migrating WP · D Python shops replacing a marketing WP box

Who actually buys what my seats can *ship* in twelve months?

**Not A (freelancer Friday-site).** Frontend can land this: three token themes, `uvx` install, zero public JS. Python-CMS wants it. It does not pay for a typed API, preview tokens, webhooks, or an edge contract. A freelancer does not consume `@mezzanine/client` or `mezzanine.client`. Friday-install is the *on-ramp*, not the ICP.

**Not B (higher-ed federation).** `HOST_THEMES` wants to grow up into this, and Product wants the comms director. Year-1 federation is SSO + 30–300 properties + a11y gate + Desk + campus preview. Performance must already be edge-honest or you will origin-render a hundred sites and die. That is a year-2 buyer who harvests after the kernel works. Do not make the comms director the first customer of a missing Theme Studio and a missing revalidation API.

**Not C (agencies migrating WP).** The WordPress map’s buyer. They will compare the canvas to Elementor / FSE in week one. Frontend is NO-SHIP against that comparison. Agencies also want a marketplace (we refuse, M7) and a commerce story (we refuse in Y1, M6). The migrate *tool* is the wedge (M4); the agency *firm* is a channel, not the year-1 design partner.

**D.** Python shop, 5–40 engineers, one marketing WordPress box they hate, a real Django (or Python) backend they love. Champion is the platform engineer in the WordPress map. They already write templates. They already want a Python client *and* a Next/Remix SDK for the one JS surface. They will accept git-owned layout + Desk instead of Gutenberg. They will accept Redis+CDN+srcset in Y1 and ISR in Y2. Success looks like: replace that WP box, keep organic, expose content to internal services via the generated API, stop paying the plugin tax.

This ICP lets frontend ship the Theme SDK without faking FSE, lets interface ship schema-as-code as the reason to switch (Payload does not give them a Python client; WP REST is a `meta` bag), and lets performance win with “fast by default, no plugin lottery” instead of promising Cloudflare APO on day one.

---

## M3 Editor — **B**

A Modernize Django admin + HTMX inline · B New Editorial Desk, hide admin from editors · C Typed-block visual editor (Sanity/Wagtail-like)

**Not C.** The editor audit’s *content model* (typed blocks, portable text, nest≤2, bindings) is right. The *motion* is a visual editor “Sanity/Wagtail-like.” That is a React admin. Wagtail already staffs that platform. Mezzanine cannot. Frontend’s non-negotiable is: the public site never imports the editor runtime. A Wagtail/Sanity-like canvas becomes the document and then leaks, or it becomes a second theme you must keep in sync. Performance already knows Gutenberg’s long-post cliff. Interface wants portable blocks in the *schema*, not a Studio SPA. Python-CMS said do not build a second React admin. We will put typed blocks in the schema and render them with Django templates. We will not staff a visual editor that looks like the thing we are refusing to clone.

**Not A.** HTMX inline + a less-embarrassing ModelAdmin is Phase 0–1 of the theme/editor migration (replace jQuery Tools, stop shipping TinyMCE to anonymous visitors, default Draft). It is not a 2026 authoring product. WordPress called it a museum project. Preview tokens, role-preview, time-travel, SEO inspector, and Theme Studio do not fit in a Grappelli fieldset. `{% editable %}` stays as the *tag*; the yellow modal dies. That work happens either way. It is not the editor strategy.

**B.** Editorial Desk is the author surface: outline + inspector + real-template preview (anonymous / staff / share-token / as-of-date). Page tree, assignments, draft/review/schedule, a11y/SEO gates, AI proposals against typed fields. Authors never see Django admin. Superusers still can (M8). Runtime is Django fragments + one portable-text island (TipTap/ProseMirror) + HTMX morph for sections. No React replica of the front end.

Why this is the frontend/API/performance vote:

- **Frontend:** Theme Studio (token painter, slot filler, template-ladder picker, pattern insert) lives in the Desk, admin-only. Public JS budget stays zero + opt-in islands. The live Django template *is* the canvas. That is how we beat FSE without becoming FSE.
- **API:** Desk is a client of the schema-generated API. Preview tokens, revisions, webhooks, SEO object — the same contract a Next.js preview or a Python SSG uses. If the editor is ModelAdmin, those endpoints never become real.
- **Performance:** Staff JS is no longer injected into every public `base.html` because inline editing *might* load. Cached shells never contain editor chrome. Publish from the Desk is the build event that emits `content_hash` + surrogate keys.

Migration: `RichTextField` remains; a command wraps blobs in `LegacyHTML`; explode later. `TinyMceWidget` stays opt-in for sites that refuse.

---

## M4 Wedge — **A**

A WP migrate + typed AI authoring · B Site kits + Friday install · C Federation publishing OS · D AI provenance/RAG content OS

**A.** The WordPress map stated the only wedge that can steal share in 24 months, and my three seats are exactly what make it true:

1. **Migrate that preserves URLs/SEO.** Interface must emit canonical, 301 map, OG, sitemap `lastmod`, redirects as data — or organic dies and the trial ends at day 90. Performance must make the imported site *faster* than the WP+Cloudflare box it left (srcset/WebP, real `Cache-Control`, FTS, no jQuery on the public page) or the champion cannot defend the switch. Frontend must restyle imported HTML through tokens + `LegacyHTML`, not ask them to rebuild in blocks.
2. **Typed AI authoring.** Interface’s schema is the only reason AI is not “write more HTML.” Editor/AI-native: every action is a Proposal against typed fields (alt, description, outline, translation), citation required, human publish. That is a product advantage Gutenberg cannot grow from a blob.

**Not B as the wedge.** Three official kits + Friday install are *mandatory packaging* (see M7 and frontend §7.5). They are how D lands after A. Alone they are “be a nicer cookiecutter,” which CodeRed CRX and every Wagtail starter already are.

**Not C.** Federation is the year-2 primitive (`HOST_THEMES` grown up). It is not how a Python shop replaces one marketing box.

**Not D.** Provenance, embeddings, MCP — correct architecture, wrong wedge. Nobody issues a PO for a “RAG content OS.” They issue a PO to escape a WP box and keep search traffic. Provenance ships *inside* A as the law on AI fills, not as the headline.

---

## M5 Name — **D**

A Keep Mezzanine · B Masthead · C Nova · D Defer name, ship under working title

**Not A.** Frontend’s last sentence: any claim that Mezzanine is a WordPress alternative on the frontend is nostalgia. The name is a 2013 Bootstrap theme plus a dead `mezzathe.me`. Shipping “Mezzanine 6” is M1-D by another path.

**Not B.** Fine newspaper word. It locks the higher-ed comms-director story (M2-B) which we did not pick. Python shops do not buy a masthead.

**Not C.** Legacy autopsy likes it. Frontend already has an abandoned first-party-adjacent skin named “nova” in `mezzanine-themes`. Generic, colliding, startup-shaped.

**D.** Working title (`mezzanine-next`, `displayable`, whatever is on the repo). Extract the kernel. Ship the Theme SDK, the schema compiler, the Desk v1, the importer. Name it when there is a company and an ICP who have touched the product. Rebrand is part of M1-C; the *string* can wait. Do not burn Masthead or Nova on a slide before Friday-install works.

---

## M6 Commerce Y1 — **A**

A None · B Catalog + Stripe · C Revive Cartridge

**Not C.** Cartridge is Django ≤4.1, Stripe broken since 2020, a CSS parasite on `base.html`. Performance and security tax. Landfill. Salvage the *idea* (Category is a Page, Product is a Displayable) as schema types later.

**Not B in year 1.** Commerce’s “page can take money” is the right *shape* and a small Stripe Checkout redirect would even be API-clean (no PAN, cart is not in the public cache shell). It still competes with Theme SDK + schema compiler + FTS + srcset + preview tokens + WP importer + Desk for the same Y1 budget. The ICP (marketing WP box) rarely needs a catalog to switch. WordPress anti-persona is the $4 Woo store — do not aim there. Product said never Woo-clone.

**A.** No commerce surface in Y1. If a kit needs a “buy” button it is a Stripe Payment Link in a slot, not a cart. Revisit B in Y2 as schema types + Checkout session + a product-card pattern in the Theme SDK, still not an engine.

---

## M7 Ecosystem — **B**

A Never marketplace · B Curated signed kits/types only · C Open plugin marketplace

**Not C.** Frontend: WordPress’s moat is liquidity, and we will not grow 11,000 themes. Interface: types come from the schema, not from `add_action`. Performance: an open plugin marketplace is how query budgets die and random JS lands on every public page. WordPress 2025: 51.5% abandoned plugins, 11,334 vulns. Extensibility audit: must not grow a WP-scale economy. Mezzanine’s own third-party list is already a cemetery.

**Not A.** “Never” forbids the only liquidity we can actually create: three official token themes (`literal`, `plain`, `dense`), five site kits that CI renders on every commit (`index`, `blog_post_detail`, `gallery`, `form`, `404`), and signed content-type packs. Frontend §7.5 is explicit: liquidity starts with three official themes that do not rot. Discovery is `importlib.metadata` entry points, not “put it first in `INSTALLED_APPS` and email the list.”

**B.** Curated, signed, versioned kits and types. Capability manifest (content type, processor, setting, template pack, island, tokens). Unsigned code does not load. Paid kits later; no storefront in Y1. `HOST_THEMES` becomes `hostname → theme entry point`. This is guarded composition, not a bazaar.

---

## M8 Admin fate — **B**

A Stay Django admin forever · B Admin is superuser-only escape hatch · C Replace admin entirely in Y1

**Not A.** If admin is forever the product, the Desk is a skin, Theme Studio is a ModelAdmin page, preview stays “staff queryset exemption,” and `editable_loader` keeps dumping jQuery onto the public site. Python-CMS’s “stay on admin” is a *staffing* warning (do not become Wagtail’s JS platform), not a product identity. We heed the warning in M3 (no React Studio). We do not make Grappelli the authoring chrome.

**Not C.** Replacing admin entirely in Y1 is a quarter that does not ship the Theme SDK, the schema API, FTS, srcset, or the importer. Users, settings, comments, form CSV, media, SitePermission, and the ORM escape hatch can stay `django.contrib.admin` (stock, not grappelli-as-identity). Schema codegen can keep emitting ModelAdmin for superusers. Killing that in Y1 is how you miss P0/P1 performance and ship no API.

**B.** Editors live in the Desk (M3). Superusers keep `/admin/` for data, auth, settings, and “I need the ORM.” New features are not designed against `__grappelli_installed`. Public pages never load admin/editor JS. This is the only admin fate that matches frontend’s staff-only island rule, interface’s “admin is one generated surface,” and performance’s “do not spend the edge quarter on a new SPA.”

---

## What Y1 looks like if this ballot wins

Kernel extracted. Working title. Python shop replaces a marketing WP box.

| Quarter | Frontend | API / interface | Performance |
|---|---|---|---|
| Q1 | Landfill IE/Flash/UA/Twitter. Tokenize `mezzanine.css`. `shell.html`. Staff JS off the public page. | `mezzanine.schema` sketch. SEO object (OG, canonical, JSON-LD) on every Displayable. Draft default. | Document Redis + nginx. Real `Cache-Control` / ETag. Compile `nevercache` once. |
| Q2 | Compat Bootstrap 3 layer. First official theme (`plain`). Islands for nav/gallery/search. | REST `/api/v1` generated. OpenAPI. Preview tokens. Postgres FTS behind `.search()`. | WebP + 3-wide srcset. Query-budget CI on `/`, `/blog/`, `/search/`, admin tree. |
| Q3 | Theme Studio in the Desk (tokens + slots). Kit #1 (marketing site). | TS SDK + Python client. Webhooks on publish. WP importer preserves slugs/301s. | Publish emits `content_hash` + surrogate keys. Purge API. |
| Q4 | Themes `literal` + `dense`. Pattern library. `{% editable %}` = island, not modal. | AI Proposal fills typed SEO/alt/outline. Search HTTP resource. | Islands replace string-split. Speculation Rules on cacheable shells. Imgproxy path.

Hospice LTS of the old package continues for existing sites. Cartridge stays dead. No marketplace. No “Mezzanine beats WordPress” slide.

---

## Explicit dissent from other seats (so the tally can weigh it)

- **Python-CMS** wants M2-A, M3-A, M8-A (Friday site, stay on Django admin). I take the Friday *install* and the no-second-React-admin constraint, and still vote Desk + escape-hatch admin, because frontend/API cannot live inside ModelAdmin.
- **Product** wants M2-B, M5-B, federation-first. Federation is real and `HOST_THEMES` is the seed. It is year 2 for my seats.
- **WordPress** wants M2-C (agencies) with the same M4-A wedge. Agencies will grade us on a visual canvas we are refusing to build (M3 not C). Python shops will not.
- **Commerce** wants M6-B. Correct later; not in the Y1 budget that has to change what a page is.
- **Skeptic** will read M1-C as “still a company you do not have.” Fair. That is why M5 is D and the Y1 ICP is one replaceable WP box, not gravity.

If the council collapses C toward A (hospice only), I will flip M3/M4/M7/M8 to the smallest possible letters (A / none / A / A) rather than pretend a LTS tree is getting a Desk. Do not hospice *and* promise an API.

— Voter E (frontend, interface, performance)
