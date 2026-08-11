# Vote G — Architect / Swing

**Seat:** Voter G (swing). Mandate: pick the path that is implementable from *this* tree (`mezzanine.__version__ = "9999dev0"`, Django 2.2–5.2, `grappelli_safe` + TinyMCE 4.1.10) without becoming a worse Wagtail.

**Read:** `01-architect.md` (kernel), `14-skeptic.md`, `13-product.md`, `11-python-cms.md`, `10-wordpress.md`, `02-editor.md`, `06-extensibility.md`. Cross-checked against `07-platform`, `08-legacy`, `12-ai-native`, `16-commerce`, `04-security`, `17-inclusion`, and the models in `mezzanine/core/models.py`, `mezzanine/pages/models.py`, `mezzanine/pages/page_processors.py`.

**How I break ties.** Product and WordPress want a company. Skeptic wants hospice. Python-CMS wants Friday-install and a refusal to clone Wagtail. Editor wants a typed-block desk. The kernel report is the only one that names what is actually *good* in this repo and what is a dead end. I vote the intersection of **architect extract** + **Python-CMS DNA** + **skeptic's category-error veto**. I reject any motion that requires staffing a StreamField/React admin, a campus federation OS, or a WordPress-killer slide in year 1.

---

## Ballot

| Motion | Vote | One line |
|---|---|---|
| **M1 Strategy** | **C** | New product that extracts the Mezzanine kernel (rebrand). |
| **M2 Year-1 ICP** | **D** | Python shops replacing a marketing WP box. |
| **M3 Editor** | **A** | Modernize Django admin + HTMX inline. |
| **M4 Wedge** | **B** | Site kits + Friday install. |
| **M5 Name** | **D** | Defer name; ship under a working title. |
| **M6 Commerce Y1** | **A** | None. |
| **M7 Ecosystem** | **B** | Curated signed kits/types only. |
| **M8 Admin fate** | **B** | Admin is superuser-only escape hatch (not replaced in Y1). |

**Path string:** `C D A B D A B B`

---

## M1 Strategy — **C**

A Hospice/LTS only · B Extract Displayable/Page library only · **C New product that extracts Mezzanine kernel (rebrand)** · D Evolve Mezzanine in place to beat WordPress

Skeptic is right that D is a category error. WordPress is a labor market, not a feature list. Evolving *in place* — REST on `Page`, Tailwind on Bootstrap 3, TinyMCE swapped for a block editor that still writes HTML — is exactly the Frankenstein `01-architect` §6–7 forbids. The dead ends (MTI-as-CPT, `RichText.content` as a bleach'd blob, thread-local `current_site_id`, `SearchableManager` materializing the world, `grappelli_safe` as identity) cannot grow WordPress-class revisions, taxonomies, media-as-content, or preview tokens. Decorating them wastes the years we do not have.

A (hospice) is a *job*, not a strategy. Keep a security-patch branch for existing sites — Django `<6` already cannot take 6.1 — but the mixin kernel is too good to only embalm. `Displayable` vs `Page`, `@processor_for`, `PageMiddleware`'s "app under a page" rule, `with_ascendants_for_slug`, `SitePermission` + host themes, `BaseGenericRelation` denormalisation, `{% editable %}`: those are original. Throwing them into LTS-only discards the only architecture that is not a worse Wagtail.

B (library only) is honest and too small. A PyPI `displayable` of mixins on stock Django admin deletes the product: processors, forms-as-pages, the tree changelist, `HOST_THEMES`, `createdb` batteries. That is a weekend extract, not a CMS.

**C is the architect verdict, productized.** Promote the import-stable kernel (`SiteRelated` / `Slugged` / `MetaData` / `TimeStamped` / `Displayable` / `RichText` / `Orderable` / `Ownable` / `ContentTyped`, `Page` tree + `content_model`, `processor_for`, `PageMiddleware`, `current_site_id` pipeline moved off thread-locals, `BaseGenericRelation`). Freeze contracts with tests. Blog, forms, galleries, accounts stay apps on that kernel. Beside it — not inside `RichTextField.clean` — add a type registry that is not MTI, a document column with a plaintext projection, `Revisable` + signed preview tokens that plug into `published(for_user=)`, media as a `Displayable`. New name, new chrome. Old sites migrate by model, not by slogan.

This is not a greenfield rewrite (which will re-lose the Page/Displayable split) and not "Mezzanine 7: now with REST, the WordPress killer." It is the only path that becomes a modern Django CMS without discarding what is actually good.

---

## M2 Year-1 ICP — **D**

A Django freelancer Friday-site · B Higher-ed federation (comms director) · C Agencies migrating WP · **D Python shops replacing a marketing WP box**

Product's B (university comms director, 30–300 properties, Campus SSO, WP Multisite harvest) is the best *story* and the least implementable. This tree's multi-site is `django.contrib.sites` + `CurrentSiteManager` + a session switcher. Architect §3 is blunt: shared media, shared types, shared users, no RLS, site id on `threading.local()`. Security: two unpatched stored XSS, form-field SSTI, no 2FA/SSO/CSP/audit, "do not put this on the public internet as a multi-tenant CMS." Inclusion: "NOT FIT FOR A PUBLIC-SECTOR OR REGULATED SITE." Federation as Y1 ICP is a compliance product we cannot ship from this process model.

C (agencies fleeing WP) is WordPress-general's buyer. Agencies need a visual editor, a migrate that preserves the whole site, and a SKU they can resell to non-devs. We have `import_wordpress` — a WXR *blog* importer that requires `feedparser` and writes `BlogPost`s. We do not have a Multisite migrator, a 301 map product, or an editor a marketing manager prefers to Gutenberg+Elementor. Selling to agencies in Y1 forces M3=C and a WP-killer slide. That is how we become a worse Wagtail *and* a worse WordPress.

A (freelancer Friday-site) is the historical audience and the README's "batteries included" posture. It is also a dying, non-paying cell that CodeRed CRX and "just use Wagtail" already occupy. Keep Friday-install as the *wedge* (M4), not the *buyer*.

**D is who can adopt this kernel without us inventing a second CMS.** A 5–30 person Python shop with one marketing WordPress they hate already has the talent to subclass `Page`, write a processor, and deploy Django. They want typed models, not a plugin bazaar. They will tolerate Django admin in year 1 if the page tree, forms, blog, and host themes work on current Django. They are the champion WordPress-general named ("Python/platform engineer with a WP box they hate") without the agency theater. Higher-ed federation is a year-2 vertical *on top of* this ICP if — and only if — media, SSO, and preview tokens exist.

---

## M3 Editor — **A**

**A Modernize Django admin + HTMX inline** · B New Editorial Desk, hide admin from editors · C Typed-block visual editor (Sanity/Wagtail-like)

Editor's own audit is the evidence: the admin is `LazyAdminSite` + `grappelli_safe` + TinyMCE **4.1.10 (2015)** + jQuery Tools overlay + full reload. The page tree (`page_menu` + `admin_page_ordering` + `ContentTyped` add-dropdown) is the one 2026-worthy surface. `{% editable %}` is the right contract with a museum implementation.

C is how we become a worse Wagtail. Wagtail 7.4 LTS already *is* typed blocks + a custom admin + Torchbox + NASA/NHS. Python-CMS: "Do not modernize Mezzanine into 'Wagtail but smaller.'" Editor §9.6 admits we cannot staff a Gutenberg. Building a Sanity/Wagtail-like canvas on an HTML blob and MTI types is shimming the missing document model onto the dead end that prevented it (`01-architect` §6.1–6.2). Portable text + max-nest-2 sections is a *good later design*; it is not a Y1 editor while `RichText.content` is still a `TextField`.

B (Editorial Desk) is Product's identity and Editor §9.9's destination. Assignments, embargoes, corrections, a11y gate, People/Events/Stories as first-class — none of that has a fork-point in this repo. Two statuses, default **Published**, preview = `is_staff` queryset bypass, no revisions, no roles beyond `Ownable` + `SitePermission`. A desk in Y1 is a greenfield app that hides the only working authoring UI (the tree) before the kernel is extracted. That is a rewrite wearing a product name.

**A is the implementable editor that does not hire a JS platform team.** Keep `PageAdmin` / `ContentTypedAdmin` / `DisplayableAdmin` / forms inlines / settings single-form. Kill TinyMCE 4 as the default (keep `RICHTEXT_WIDGET_CLASS` as a seam). Replace `editable.js` + jQuery Tools + `jquery.form` with HTMX + morphdom against the existing `{% editable %}` tag — same POST to `core.views.edit`, no yellow modal, no full reload. Rebuild `page_tree.js` without jQuery UI nestedSortable. Default new objects to Draft. That is months, on this code, by a Python team. It is also how Python-CMS said not to become Wagtail.

Typed blocks come *after* `RichText` grows a document column (kernel work, M1=C). The desk comes *after* editors no longer need ModelAdmin for pages (M8=B). Neither is the Y1 editor.

---

## M4 Wedge — **B**

A WP migrate + typed AI authoring · **B Site kits + Friday install** · C Federation publishing OS · D AI provenance/RAG content OS

A is WordPress-general's "only wedge that can steal share." Skeptic: you cannot steal share; do not fork gravity. The importer we have is blog WXR. Typed AI authoring (`12-ai-native` Proposal/Ability/Provenance) needs typed fields that do not exist. Shipping "WP migrate + AI" as the wedge forces a migrate product and an AI product before the kernel is extracted. That is two startups.

C is Product's primitive. Hostname multi-tenancy is real and should be *kept* (`current_site_id` pipeline, `HOST_THEMES`, `SitePermission`). It is not a publishing OS. Promoting it to federation in Y1 leaks media and types (`docs/multi-tenancy.rst` already admits shared media) and walks into the security/inclusion veto.

D is a content-OS thesis with zero code. Embeddings-on-Displayable is a later kernel mixin, not a go-to-market.

**B is the wedge this repo already almost is.** `mezzanine-project` + `createdb` + fixtures + `HOST_THEMES` + `collecttemplates` is a Friday site that the platform report says is *broken on the advertised Pythons* (`import imp`, `distutils.copy_tree`, `django < 6`). Fix the bootstrap. Ship five signed kits (Institute/brochure/magazine/docs/campaign) as theme+fixture+type packs — not StreamField homework, not a plugin bazaar. That is Wagtail's refused cell ("not an instant website in a box") and Mezzanine's original DNA (`README.rst`: functionality by default, not modules). Python shop ICP (M2=D) buys a kit on Friday. Agencies can come later if the kits are good.

---

## M5 Name — **D**

A Keep Mezzanine · B Masthead · C Nova · **D Defer name, ship under working title**

M1=C requires a rebrand *eventually*. Shipping "Mezzanine 6 now with REST" is the forbidden slide. Keeping the name (A) while extracting a new product confuses every existing site and every Wagtail comparison.

B (Masthead) and C (Nova) are fine words. Product prefers Masthead; legacy prefers Nova. Neither is an architecture decision. Naming fights consume the round that should freeze the kernel contract.

**D.** Working title: extract as `mezzanine.kernel` (import-stable, boring) and ship the product under a codename until a buyer exists. Pick Masthead/Nova/Lectern when there is a site to put it on. Do not block code on a noun.

---

## M6 Commerce Y1 — **A**

**A None** · B Catalog + Stripe · C Revive Cartridge

Cartridge is a sibling hard-wired into `createdb.create_shop` and `collecttemplates`, not a plugin. FAQ: it cannot run without Mezzanine. Commerce report: PyPI 1.3.4 (2022), Django ≤4.1, Stripe broken since 2020. C is necromancy. There is no Cartridge in this tree to revive — only comments and a `create_shop` branch.

B (catalog + Stripe Checkout, Category-as-Page, Product-as-Displayable) is the *right shape* and the wrong year. Y1 of an extract is kernel contracts, Django 5.2/6, HTMX inline, Friday kits, TinyMCE/Twitter/mobile funeral. A catalog is a kit we can add when `Displayable` + processors are stable. Shipping checkout while drafts have no tokens and media is a filesystem is how a marketing site becomes a PCI distraction. Product's "never Woo" stands.

**A.** No commerce engine, no Stripe, no Cartridge compat layer in Y1. Keep the *idea* that a page can take money (processor returns a response; Category is a Page) as a year-2 kit. Magazines and NGOs can donate via a Stripe link in a kit before we own a cart.

---

## M7 Ecosystem — **B**

A Never marketplace · **B Curated signed kits/types only** · C Open plugin marketplace

C is WordPress plugin hell inside an unsandboxed Python process. Extensibility is unambiguous: no `do_action`, no zip-upload-to-gunicorn, no 60k plugins. README already chose batteries over modules. The third-party RST list is a cemetery. We will not grow a `.org`.

A (never) overfits the skeptic and fights M4=B. Kits *are* an ecosystem. A typed capability surface (`content_type`, `page_processor`, `settings`, `theme`, `richtext_filter`) is how those kits stay reviewable.

**B**, exactly as `06-extensibility` specified, scoped to what we can actually sign in Y1: five-to-fifty reviewed kits and types, capability manifest, hash-pinned, applied at deploy, not at runtime. WASM/iframe isolation is year-2 machinery; Y1 is "curated git/PyPI index + human review + no unsigned `admin_ui`." Themes do not ship models. `EXTRA_MODEL_FIELDS` is deprecated, not a plugin API. Cartridge-class siblings use a vendor door, not the kit catalog. Success metric is sites that never needed a kit, not kit count.

---

## M8 Admin fate — **B**

A Stay Django admin forever · **B Admin is superuser-only escape hatch** · C Replace admin entirely in Y1

C is a rewrite. The tree, forms builder, settings form, `SitePermission`, filebrowser mount, `LazyAdminSite` EXTRA_MODEL_FIELDS deferral — all are ModelAdmin. Replacing them in Y1 while extracting the kernel is how you ship neither.

A (forever) is Python-CMS's anti-Wagtail reflex turned into a trap. Grappelli-as-identity, IE7 padding on the dashboard, Admin/Site login radio: that is a 2012 product. If admin is the product forever, we are a museum with HTMX. WordPress-general is right that admin modernization is not a WordPress strategy — and we are not running a WordPress strategy (M1≠D, M4≠A).

**B is the destination that keeps Y1 honest.** Superusers keep Django admin for users, settings, form entries, comments, raw types, migrations. Editors live on the site: HTMX `{% editable %}`, the page tree (can stay a ModelAdmin changelist until it doesn't), draft/preview once tokens exist. We do *not* hide admin in month one (M3=A: we modernize it). We *declare* it is not the product, so nobody designs new editorial features against `__grappelli_installed`. Grappelli/Filebrowser become optional skins, then leave.

This is Editor §9.9 without pretending the desk ships in Q1.

---

## Coherence — one path, not eight compromises

```
Extract kernel as a new product (C)
    sold to Python shops retiring one marketing WP (D)
    via Friday kits on a fixed bootstrap (B)
    edited in modernized Django admin + HTMX inline (A)
    with admin declared an escape hatch (B)
    no commerce, no marketplace, no name fight (A / B / D)
```

What this refuses, on purpose:

| Loud ask | Why no |
|---|---|
| Beat WordPress / evolve in place (M1=D) | Category error; shims on dead ends |
| Hospice only (M1=A) | Kernel is still original; LTS is a branch, not the company |
| Library-only extract (M1=B) | Throws away processors, forms, tree, kits |
| Higher-ed federation ICP (M2=B) | Tenancy + a11y + SSO are not in this process |
| Agency WP-migrate ICP (M2=C) | Forces a visual editor and a migrate product we do not have |
| Editorial Desk as Y1 editor (M3=B) | No workflow model to hang a desk on |
| Typed-block visual editor (M3=C) | Worse Wagtail; cannot staff it; body is still HTML |
| WP+AI wedge (M4=A) | Importer is blog-only; AI needs types |
| Federation / RAG OS wedges (M4=C/D) | Year-2 kernels, not a first customer |
| Keep the name (M5=A) | Conflicts with extract-and-rebrand |
| Catalog+Stripe or Cartridge (M6=B/C) | Wrong year; sibling is dead |
| Open marketplace (M7=C) | Plugin hell, no sandbox |
| Replace admin in Y1 (M8=C) | Unimplementable; deletes the working tree |
| Admin forever (M8=A) | Museum |

**LTS footnote, not a motion.** Existing Mezzanine sites get a hospice branch: security patches, Django 5.2 only, delete `mezzanine.twitter` / `mezzanine.mobile`, no feature promises. That is Skeptic's "yes if someone wants that job." It is not the product.

**Wagtail test.** If a vote would require a custom React admin, StreamField-shaped JSON as the religion, or "Wagtail but smaller and unpaid," it fails. A, here, is HTMX on the admin we have. C (M1) is a kernel extract, not a CMS rewrite. D (M2) is people who already write Django. That is the swing.

— Voter G
