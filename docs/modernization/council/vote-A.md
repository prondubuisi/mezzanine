# Voter A — Conservative / Engineering

### M1
- Vote: C
- Confidence: 0.78
- Why: Architect is explicit that evolve-in-place (D) will shim revisions, blocks, REST, and preview tokens onto the dead ends that prevent them (MTI-as-CPT, HTML-as-body, filebrowser-as-media, thread-local site), while a greenfield rewrite re-loses the Page/Displayable split and processor contract. Legacy calls the current tree a compatibility museum and recommends a new product that keeps the kernel and deletes ~60% on day one; Platform adds that `django < 6` is a hard dead end when 5.2 LTS ends April 2028. Hospice/LTS (A) is what two maintainers are already doing and ships zero product. Extract-library-only (B) undersells the architect's kernel: pages, processors, search, and Displayable are a CMS, not a PyPI mixin pack. C is the extraction with a new package and a migration hatch (`nova.compat` / same table names), not a WordPress slide.

### M2
- Vote: D
- Confidence: 0.74
- Why: Security's ship/no-ship line is single-site brochureware behind SSO and a WAF — not multi-tenant, not regulated. That kills Product's Year-1 ICP of a university federation (B): FERPA/a11y/SSO/audit are table stakes they do not have (no 2FA, shared media, unpatched CVE-2025-6050 and CVE-2025-29573, drafts visible to any `is_staff`). Agencies migrating WP (C) is WordPress's GTM, but Skeptic is right that you cannot out-feature the WP labor market in 24 months. Freelancer Friday-site (A) matches Python-CMS positioning but does not pay for a kernel extract plus platform reboot. A Python shop replacing one marketing WP box already has Django, already hates that box (WordPress's named champion), and can accept an extracted kernel on stock admin.

### M3
- Vote: A
- Confidence: 0.81
- Why: Python-CMS is the constraint I will not violate: stay on Django admin, modernize with HTMX, do not build a second React admin. Editor's own audit says Mezzanine cannot staff a Gutenberg, and the keep-list is Displayable, page types, `{% editable %}`, bleach, and the page tree — not a new shell. Product's Editorial Desk (B) and a Sanity/Wagtail-like typed-block editor (C) are company-scale UI bets on a tree that still vendors TinyMCE 4.1.10, Grappelli-safe, and jQuery Tools. Platform already asked for an HTMX starter and un-vendored 2014 CSS; that is the same work as modernizing admin plus rewriting `editable.js` as HTMX endpoints. Architect can get a JSON `RichText` document later without standing up a new editor product in Y1.

### M4
- Vote: B
- Confidence: 0.83
- Why: Platform's DevEx bar is time-to-first-edit in seconds; the current bootstrap is `import imp` (removed in 3.12), `distutils.copy_tree`, and `admin`/`default`. Python-CMS's empty cell is "the Django site you ship on Friday" plus five curated kits that work — that is the wedge we can actually engineer. Federation publishing OS (C) is Product's mission and is disqualified by Security's tenancy verdict (shared users, shared media, IDOR on form files). WP migrate + typed AI (A) is a useful importer (Legacy: keep WordPress + RSS as extras) but is not a strategy; Skeptic forbids the WP slide. AI provenance/RAG OS (D) is a Y2 content-plane idea, not a Y1 install story, and it widens the HTML/XSS surface Security just failed.

### M5
- Vote: D
- Confidence: 0.76
- Why: If M1 is a new product, Keep Mezzanine (A) is a lie: Legacy says the name currently means Grappelli-safe, Disqus, bit.ly, Cartridge, and a dead `jupo.org`. Product's Masthead and Legacy's Nova are both fine working titles and both un-checked for PyPI/trademark. Shipping under a working title until the extract and the first kit exist is the engineering order of operations; naming is not a blocker on the 90-day platform reboot (pyproject, Ruff, XSS regressions, drop EOL). Defer also avoids a second identity outage like the HTTP `mezzanine.jupo.org` docs host Platform already called a platform outage.

### M6
- Vote: A
- Confidence: 0.86
- Why: I dissent from Commerce's "ship the affordance in year 1." Cartridge is dead (PyPI 1.3.4, Django ≤4.1, Stripe broken since 2020); Legacy and Product both say burn the hooks, not revive them (C). Catalog + Stripe (B) is a small protocol, but Y1 already has a forced platform reboot, two confirmed unpatched High XSS CVEs, no SecurityMiddleware in the template, and a 57% test floor with a superuser-only client. Adding a checkout path before render-time bleach, signed previews, and a non-`imp` starter is scope, not leverage. Commerce's own hard no (PCI, shipping plugins, Woo clone) is correct — and the way to honor it in Y1 is to ship none.

### M7
- Vote: B
- Confidence: 0.88
- Why: Extensibility's verdict is the one I will treat as law: Mezzanine cannot and must not grow a WordPress-scale plugin economy; extension is subclass Page/Displayable, drop a processor, register a setting. WordPress 2025: 69k plugins, 51.5% abandoned, 11,334 vulns — that is the disease Security says we must not copy. Open marketplace (C) recreates it inside a Python process with no sandbox. Never-marketplace (A) conflicts with the M4 kits wedge and with Extensibility's "ten to fifty maintained apps" / signed reviewed catalog. Curated signed kits/types is the same typed-capability surface Product wants (capability manifests, no unsigned code) without pretending we have wordpress.org.

### M8
- Vote: A
- Confidence: 0.79
- Why: Consistent with M3. Python-CMS: do not become Wagtail by building a custom admin. Replacing admin entirely in Y1 (C) is malpractice on a 3.5/10 platform with admin XSS still in-tree (`displayable_links_js` served as `text/html`, no `admin_view`). Product wants admin as a superuser escape hatch (B) behind an Editorial Desk we cannot staff. Editor's keep-list is almost all ModelAdmin: page tree changelist, forms inlines, settings form, ContentTyped add dropdown, OwnableAdmin. The work is strip Grappelli-safe/filebrowser-safe, speak modern Django admin, put HTMX on `{% editable %}` — not hide the admin from the people who can actually run this stack (the M2 Python shop).
