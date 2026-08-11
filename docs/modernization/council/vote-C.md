# Vote C — Skeptic, constructive
**Voter:** C  
**Lean:** Skeptic  
**Constraint honored:** hospice/do-nothing is not the ballot. M1 is not A.

## Tally

| Motion | Vote |
|---|---|
| M1 Strategy | **C** |
| M2 Year-1 ICP | **D** |
| M3 Editor | **A** |
| M4 Wedge | **B** |
| M5 Name | **D** |
| M6 Commerce Y1 | **B** |
| M7 Ecosystem | **B** |
| M8 Admin fate | **B** |

**Ballot line:** C D A B D B B B

---

## M1 Strategy — **C** New product that extracts Mezzanine kernel (rebrand)

Beat-WordPress in place (D) is the category error the dissent brief named. WordPress is a labor market, a $5 host, and an SEO priesthood. Mezzanine 7-with-REST-and-Tailwind does not move that. Platform score 3.5/10, two 2025 XSS CVEs still in tree, `django < 6`, `import imp` on a 3.14 classifier — this is not a chassis you “evolve.”

Hospice/LTS (A) is the honest ops job for the sites already on 5.2 until April 2028. It is not a product strategy. Extract-library-only (B) is the honest engineering artifact and I would ship that library *inside* the new product — it is not enough by itself. A Displayable/Page package with no installable site is a PyPI ghost. Wagtail already is the serious Django CMS; a mixin repo does not take its lunch.

**C is the smallest company that is still a company:** steal the kernel (Page tree, Displayable, processors, search-as-manager, `{% editable %}`), delete ~60% of the tree on day one (twitter, mobile, bit.ly, UA, Disqus-in-core, Cartridge hooks, TinyMCE 4, Bootstrap 3, Grappelli-safe-or-death), new package, migration command, no “WordPress killer” slide. Legacy’s extract list is the spec. Do not start by forking this CSS.

---

## M2 Year-1 ICP — **D** Python shops replacing a marketing WP box

Higher-ed federation (B) is Product’s romance and Security’s red flag. Multi-site here is a `site` FK plus a shared media root, shared user table, IDOR on form files, and drafts visible to any `is_staff`. That is virtual hosting. Do not sell it to a university comms director in year 1 as a “publishing OS.” You will inherit their compliance questionnaire and fail it.

Agencies migrating WP (C) is walking into gravity: plugin economy, cPanel, Upwork, Elementor muscle memory. We do not have that labor market and will not grow one in 12 months.

Django freelancer Friday-site (A) is the Python-CMS empty cell and a good *motion*, not a good *buyer*. Freelancers have no budget and already have Wagtail, static, and Notion.

**D is one job, one champion, one box.** WordPress brief: the champion is the Python/platform engineer who already hates the marketing WordPress. They have Django in production. They do not need a federation story. They need a typed site that their marketer can edit on Tuesday without a deploy pipeline, without a plugin bazaar, and without us pretending to be Automattic.

Anti-persona still holds: $4 Woo store, Webflow designers, NYT-scale newsrooms.

---

## M3 Editor — **A** Modernize Django admin + HTMX inline

Typed-block visual editor (C) is “become Wagtail/Sanity.” That product exists, twice, with NASA/NHS logos. Python-CMS was explicit: do not build a second React admin.

New Editorial Desk that hides admin from editors (B) is the right *eventual* shape (Product is not wrong about editors vs. superusers) and the wrong year-1 build. Kernel extract + kits + platform reboot already is the year. A desk on top is a second product.

**A is the DNA we actually have.** `{% editable %}` + page processors + stock admin is Mezzanine’s only remaining non-Wagtail offer. Reimplement inline edit as HTMX with CSRF on every mutation. Kill TinyMCE 4 / jquery.tools / `editable.js`. Unfold/Jazzmin or vanilla Django 5/6 admin for the back office — not another `grappelli_safe` fork. This is a modernization of a contract, not a museum restoration of Grappelli.

---

## M4 Wedge — **B** Site kits + Friday install

WP migrate + typed AI authoring (A) is the WordPress brief’s “only 24-month wedge.” I am not buying it as the *wedge*. Obsessive WXR import is a year of SEO edge cases; the existing `import_*` commands have **zero tests**; importers skip `full_clean()` and will persist raw HTML that templates then `|safe`. AI authoring is real (Proposal-gated, typed fields — the AI-native brief is sound) and it is a feature, not the reason a Python shop picks us this Friday.

Federation publishing OS (C) — see M2. Isolation is not a product you can kit-bash.

AI provenance/RAG content OS (D) — year-2 content plane, not a wedge. Embeddings-on-Displayable and ProvenanceEvent are good laws to design toward. They do not get a first install.

**B is the empty cell Wagtail’s Zen refuses:** not a CMS framework, a shippable Django website. Five kits that work. `uvx` / compose / `just dev`. Time-to-first-edit in minutes, not a 12-step README that ends on Freenode. The Python shop’s WP box dies because the kit is done, not because we out-imported Yoast.

Keep WordPress+RSS import as an *extra*. Do not make it the billboard.

---

## M5 Name — **D** Defer name, ship under working title

Keep Mezzanine (A) inherits brand death: jupo.org, Grappelli, Disqus, Cartridge, “is this still viable?” (#2038). Do not ship “Mezzanine 7.”

Masthead (B) is Product’s newspaper/campus tell. It locks the federation ICP I already rejected.

Nova (C) is Legacy’s working name and a fine *candidate*. It is not a decision we are qualified to make in this round without a PyPI/trademark collision check (Legacy already hedges Entresol / PianoNobile / Storey).

**D.** Working title in the repo, package rename ready, no launch-day identity theater. The name is not the blocker. The `imp` import and the unpatched XSS are.

---

## M6 Commerce Y1 — **B** Catalog + Stripe

None (A) is the skeptic default and, under this round’s rule, do-nothing. Rejected.

Revive Cartridge (C) is necromancy. PyPI 1.3.4 (2022), Django ≤4.1, Stripe broken since 2020. `createdb` still special-cases `cartridge.shop`. Delete the hook. Do not compat-layer a dead cart.

**B is the commerce brief’s actual sentence:** ship the affordance, not the engine. Category is a Page, Product is a Displayable, checkout is Stripe Checkout, order is a receipt, never see a PAN. Magazines, museums, NGOs, a course page that can take money. Not Woo. Not Utah tax. Not Oscar-in-tree. Year 2 can grow an adapter; year 1 must not grow a PCI program.

A kit that can charge is still a kit (M4). A cart revival is a third product.

---

## M7 Ecosystem — **B** Curated signed kits/types only

Never marketplace (A) fights the kit wedge. If kits are the product, we need a *place* they live. That place is not a bazaar.

Open plugin marketplace (C) is copying WordPress’s original sin: 69k plugins, 51.5% abandoned, 11,334 vulns in 2025. We have no review machine, no signed-update machine, no Wordfence. Security: Mezzanine has no plugin economy left to burn — do not grow a new one.

**B.** Certified kits, typed blocks, signed capability manifests, Django types for IT as the escape hatch. Unsigned code does not run. This is the only ecosystem that does not recreate CVE-as-a-service and still lets M4 exist.

---

## M8 Admin fate — **B** Admin is superuser-only escape hatch

Stay Django admin forever (A) as the *editor* product is the museum project the WordPress brief warned about. The admin we have is also an XSS surface (`displayable_links_js` still `text/html`, form-filename `mark_safe`, `RICHTEXT_FILTER_LEVEL_NONE` in the settings UI). Forever is how those stay load-bearing.

Replace admin entirely in Y1 (C) is a rewrite on top of a platform reboot on top of a kernel extract. It will slip. It will ship neither.

**B matches M3=A without lying to editors.** Editors live on the site: HTMX inline, draft/preview/schedule, never a Grappelli tree. Superusers keep Django admin as break-glass (users, sites, raw types, the things IT actually needs). Hide `RICHTEXT_FILTER_LEVEL` from that UI or require env+restart. This is Product’s “guarded composition + Django escape hatch” without pretending we staff a Desk team this year.

---

## What I am not voting for (explicit)

- Mezzanine 7 as WordPress killer
- Campus federation as year-1 primitive
- StreamField / Sanity clone
- Cartridge
- Open plugin marketplace
- Spending the name cycle before the XSS suite exists
- Hospice as the only future (LTS is a *parallel* duty for 6.x, not this product)

## Confidence

High on M1/M2/M4/M7 (reports converge). Medium on M5 (defer is discipline, Nova is tempting). Medium on M6 (affordance is right; Y1 scope is tight). M3/M8 are a paired compromise: admin lives, editors do not live in it.
