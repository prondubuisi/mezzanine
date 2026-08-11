# Vote F — Modules / Commerce / Platform-DX

**Seat:** Voter F. First-party modules, commerce affordance, platform and developer experience.
**Briefs binding this ballot:** `09-modules.md`, `16-commerce.md`, `07-platform.md`, `06-extensibility.md`, `08-legacy.md`, `13-product.md`, `11-python-cms.md`.
**Not binding:** product's higher-ed federation thesis, the WordPress-gravity "steal one job" thesis, the Editorial Desk as year-1 product. Those seats can vote them. This seat will not.

---

## Ballot

| Motion | Vote | One line |
|---|---|---|
| M1 Strategy | **C** | Extract the kernel into a new product. Do not hospice it, do not library-only it, do not "beat WordPress" in place. |
| M2 Year-1 ICP | **D** | Python shops replacing a marketing WP box. The buyer who feels platform debt and will pay for modules + a checkout. |
| M3 Editor | **A** | Modernize Django admin + HTMX inline. Do not build a second admin in Y1. |
| M4 Wedge | **B** | Site kits + Friday install. That is the empty cell Wagtail refuses. |
| M5 Name | **D** | Defer. Masthead and Nova are both fine working titles; neither is a Y1 deliverable. |
| M6 Commerce Y1 | **B** | Catalog + Stripe Checkout. Affordance, not engine. Cartridge stays dead. |
| M7 Ecosystem | **B** | Curated signed kits/types only. Never an open plugin bazaar. |
| M8 Admin fate | **A** | Django admin remains the CMS surface. Superuser hatch is a different product. |

Letters only, for the tally: **C D A B D B B A**

---

## M1 Strategy — **C**

New product that extracts the Mezzanine kernel and rebrands.

- **Not A (Hospice/LTS).** Hospice is already the last three years of the repo: Pillow pins, `pkg_resources`, one XSS fix, a tox museum. Platform score 3.5/10. Existing 5.2 sites can stay until April 2028; that is a maintenance lane, not a strategy. Modules, commerce, and DX all die under hospice.
- **Not B (Extract Displayable/Page library only).** The kernel *is* Displayable + Page + processors + search + multi-site. Shipping only that is a CMS framework. Python-CMS is explicit: the empty cell is a *shippable Django website*, the product Wagtail's Zen refuses. A library cannot host typed form-pages, a DAM, memberships, or a Stripe checkout protocol. Commerce's salvage ("Category is a Page, Product is a Displayable") only matters if those types still live in a product.
- **Not D (Evolve in place to beat WordPress).** Category error (skeptic, WordPress brief). Evolving *this* tree keeps Grappelli-safe, TinyMCE 4, Bootstrap 3.2, `import imp`, `django < 6`, `admin`/`default`, and a dead `jupo.org`. You cannot beat Gutenberg from a compatibility museum. Product is right: do not ship "Mezzanine 6."
- **C is the only move that funds a platform reboot *and* keeps the product ideas.** Legacy's extract list *is* the company: `Displayable` / `Page` / processors / search / multi-site / forms-as-pages / `KeywordsField` pattern. Modules then replace engines (typed form blocks, DAM, allauth, Activity comments) on those bones. Commerce hangs `Product` on `Displayable` and `Category` on `Page`. Platform deletes 60% of the tree on day one (twitter, mobile, bit.ly, UA, Disqus-in-core, committed OAuth secrets, `imp`, `distutils`, universal wheels) and ships `pyproject.toml` + uv + Ruff + Django 5.2/6.1 on Python 3.12+.

Compat contract (legacy, one major only): same table names and `Displayable`/`Page`/`BlogPost` columns, `nova_from_mezzanine` (or equivalent), then drop the hatch. Hospice 6.x until 5.2 LTS ends. Two products, one graveyard.

---

## M2 Year-1 ICP — **D**

Python shops replacing a marketing WP box.

This seat's buyer is the person who already has Django talent, already hates the WP box in the corner, and will feel a 2026 platform (uv, typed public API, Django 6.1, no default password, HTTPS docs). That is not a freelancer Friday, not a university comms director, not an agency buying visual-editor theater.

- **Not A (Django freelancer Friday-site).** Friday-install is the *wedge* (M4), not the *ICP*. Freelancers do not fund a DAM, typed form engine, allauth+entitlements, Stripe protocol, or a platform reboot. They will `uvx` the kits we build for D.
- **Not B (Higher-ed federation).** Product's pick. Wagtail already is the Django CMS of record for NASA/Google/NHS and the university web team. Python-CMS: do not become "Wagtail but smaller." Federation (SSO, central policy, 30–300 properties) is a Y2 platform, not a Y1 DX story. This seat will not spend year 1 losing to Torchbox.
- **Not C (Agencies migrating WP).** WordPress brief's buyer. Agencies want a visual editor, a plugin store, and a non-dev Tuesday edit. That pulls M3 toward C and M7 toward C, both of which this seat rejects. Champion inside the agency is often a Python engineer — that person is D wearing an agency badge.
- **D fits all three briefs this vote carries.**
  - **Platform/DX:** they evaluate `pyproject.toml`, the matrix, ASGI, compose/`just`, coverage above 57%, Trusted Publishing. A marketing-site replacement is a Django deploy they already know how to run.
  - **Modules:** they leave WP for Gravity Forms / Media / memberships / comments they do not want to keep paying. Form-as-`Page`, DAM, `Page.login_required` → Gate, `CommentsField` as activity hook — that is the migration prize.
  - **Commerce:** magazines, museums, NGOs, course-makers, and the Python shop with a merch/donate/course SKU. Catalog + Stripe Checkout is exactly "the page you already wrote can take money." Not Utah tax, not Woo.

Anti-persona (commerce + WordPress, agreed): the $4 Woo store.

---

## M3 Editor — **A**

Modernize Django admin + HTMX inline.

- **Python-CMS law:** stay on Django admin, modernize with HTMX, do not build a second React admin. Content stays models / relational blocks, not StreamField JSON.
- **Platform law:** inline edit is HTMX endpoints with CSRF on every mutation, not `editable.js` + TinyMCE 4 + jquery.tools. Skin is vanilla Django 5/6 admin or a *maintained* extra (Unfold/Jazzmin), not `grappelli_safe`. Kill Flash `moxieplayer.swf` and the IE7 TinyMCE skin in the same PR as the XSS regression file.
- **Modules law:** the form builder becomes typed blocks *on the page tree*, inside this admin — not a Sanity canvas. Keep `CommentsField` / `KeywordsField` / `RatingField` as the CMS API. Drag-and-drop inlines and the entries/CSV UX are the pieces to keep.
- **Not B (Editorial Desk, hide admin from editors).** Product's year-1 flagship. This seat will not spend the reboot budget on a second admin while `import imp` still ships, coverage is 57%, and Exploit-DB 52385 has no regression test. A Desk is a Y2 skin over the same models, if D still wants it after kits ship.
- **Not C (typed-block visual editor).** That product is called Wagtail. StreamField religion is how you lose the "relational content, real models, makemigrations is the toolkit" slot. Typed blocks are correct for *forms* (modules 6.1) and for *certified kit types* (extensibility). They are not a new authoring runtime in Y1.

`{% editable %}` stays as the contract. The implementation is replaced.

---

## M4 Wedge — **B**

Site kits + Friday install.

Python-CMS wedges 5 and 7, platform §9, extensibility "themes are not apps with models," modules "do not ship Mezzanine 7 with nicer Bootstrap on the same models."

Year-1 kit shape (this seat):

1. **Friday install:** `uvx` / Copier + `just dev` + compose (Postgres, Mailpit) + ASGI. No `mezzanine-project`, no `createdb --noinput`, no `admin`/`default`, no `imp`. Time-to-first-edit in minutes. Playground/WASM is the stretch, not the gate.
2. **Three kits, signed, that work:** Institute/brochure (pages, forms-as-pages, DAM, blog-as-view), Course/NGO (same + memberships/paywall + Stripe catalog), Magazine (same + issues as pages). Not page-type homework.
3. **Modules inside the kits, not as plugins:** typed FormPage, Asset DAM with zip-ingest, allauth + Gate, comments off or Activity adapter. Galleries are a collection view over the DAM.
4. **Commerce inside the kits that need it:** a `Product(Displayable)` and `Category(Page)` with Stripe Checkout. The page takes money.

- **Not A (WP migrate + typed AI authoring).** Obsessive WP import is a *must-have feature* (preserve URLs, 301 map) for ICP D. It is not the wedge. AI authoring is a Proposal plane on typed fields (AI-native brief), not the reason a Python shop picks this on Friday.
- **Not C (Federation publishing OS).** Product's primitive. Hostname multi-tenancy already exists and should be productized *later*. Y1 federation is how you skip Friday install and arrive at a campus RFP against Wagtail.
- **Not D (AI provenance/RAG content OS).** Right architecture, wrong year. Provenance as a field and embeddings on `Displayable` can land as model columns. They are not the wedge while the starter still `import imp`.

Success metric this seat will accept: a Python shop replaces one marketing WP box in a week, on Django 5.2/6.1, without writing a page type.

---

## M5 Name — **D**

Defer the name. Ship under a working title.

- Product wants **Masthead** (fallback Lectern). That name is a higher-ed publishing OS. This ballot rejected that ICP.
- Legacy wants **Nova**. Fine as a working title. Also a collision-prone word on PyPI.
- **Keep Mezzanine** keeps the identity the README still sells: Grappelli-safe, Disqus-or-comments, bit.ly, Cartridge, jupo.org, Freenode. Legacy is right — that name currently means hospice.
- Platform/DX rule: the 90-day sequence is metadata truth, `pyproject.toml`, Ruff, template fix, CI collapse, Trusted Publishing, XSS suite, stubs, docs. A brand workshop is not on that list.

Working titles allowed on the box: Nova, Masthead, or `mezzanine7` in private. Public name after three kits have real users. Do not call it Mezzanine-NG.

---

## M6 Commerce Y1 — **B**

Catalog + Stripe Checkout.

Commerce brief, quoted because it is the whole vote: **ship the commerce affordance in year 1; do not ship a commerce engine.**

Year-1 shape:

- `Product` is a `Displayable`. `Category` is a `Page`. That is the Cartridge salvage and the only reason Cartridge ever felt like Mezzanine.
- `catalog` app + `checkout` protocol + Stripe Checkout. Order is a receipt. Never see a PAN. No PCI scope.
- Memberships (modules 6.3) take a `price_ref`. Form `PaymentBlock` is a typed field that starts the same checkout protocol, not a second cart.
- Hard no: shipping plugins, tax engines, Cartridge compat layer, "WooCommerce replacement" marketing, vendoring Oscar, rebuilding Saleor.

- **Not A (None).** Then magazines, museums, NGOs, and course-makers stay on WP+Woo or a Stripe link in a rich-text blob. The differentiator — the page you already wrote can take money — does not exist. Modules' paywall and PaymentBlock have nothing to call.
- **Not C (Revive Cartridge).** PyPI 1.3.4 (Sep 2022), Django ≤4.1, Stripe broken since 2020. Sibling fossil. `createdb`'s `create_shop` hook is on the kill list. Platform will not pin another dead tree.

Year 2 optional adapters (Saleor, Oscar, Shopify) are adapters, not a rewrite. Never rebuild Woo.

---

## M7 Ecosystem — **B**

Curated signed kits and content types only.

Extensibility brief is law for this seat: Mezzanine cannot and must not grow a WordPress-scale plugin economy. Extension today is honest Django — subclass `Page`, `page_processors.py`, `register_setting`, template override. That is a platform. It is not a marketplace.

Y1 rules:

1. Core stays whole. Pages, rich text, blog-as-view, forms, DAM, search, settings, `{% editable %}`. Do not extract batteries to prove modularity.
2. Kits and types are reviewed, signed, versioned capability packages (`content_type`, `theme.json`, `settings`, `templates`). No unsigned code on the editorial surface.
3. Themes do not ship models. `HOST_THEMES` as "theme = Django app that defines `HomePage`" is the original sin.
4. `EXTRA_MODEL_FIELDS` and `deepcopy(fieldsets)` are not the public API. Version `plugins.v1` as register_* functions.
5. Cartridge-class vendor apps: few, trusted, full process. Catalog+Stripe is first-party, not a vendor app.
6. Measure success by sites that never needed a plugin.

- **Not A (Never marketplace).** Then kits have no distribution path and every shop forks templates. A *curated* index of ≤50 signed packages is not a bazaar.
- **Not C (Open plugin marketplace).** WordPress 69k plugins, 51.5% abandoned, 11,334 vulns in 2025. Python has no cheap sandbox. `page_processors` run with the ORM. Product: never an infinite marketplace. Extensibility: if this council wants WordPress, fork WordPress.

Developers can still `pip install` anything. That is Django. The *product* does not bless it.

---

## M8 Admin fate — **A**

Stay on Django admin. Modernize it. Do not replace it in Y1. Do not demote it to an escape hatch until a real editor exists — and this ballot refused to fund that editor in Y1.

- Consistent with M3 **A**. Editors live in a Django 5/6 admin that has been stripped of Grappelli-safe, given HTMX inline edit, a first-class DAM picker, typed form inlines, and an a11y gate on publish. Superusers get the same surface plus settings, sites, and the checkout receipts.
- **Not B (superuser-only escape hatch).** That vote is M3 B in costume. It assumes an Editorial Desk that this seat will not staff in year 1. Shipping "hide admin" with no Desk leaves editors in a trapdoor.
- **Not C (replace admin entirely in Y1).** Platform suicide. The 90-day reboot already has to: tell the truth in classifiers, move to `pyproject.toml`, Ruff + django-upgrade, fix the template (`importlib`, `asgi.py`, `STORAGES`, no default password), collapse CI to 9 living cells, Trusted Publishing, XSS suite, stubs on `pages`/`utils`, HTTPS docs. Replacing admin on top of that is how you ship a pretty empty shell on Django 2.2 shims.

"Forever" is the option text, not a vow against a Y3 Desk. The Y1 vow is: admin is the product surface, and it must stop being a 2012 Grappelli fork.

---

## What this seat will treat as non-negotiable regardless of the tally

These are not motions. They are the platform/modules/commerce floor. A winning ballot that skips them is a press release.

1. **Matrix:** Python 3.12–3.14 × Django 5.2 / 6.0 / 6.1. Drop `django < 6`. Drop 2.2–5.1 classifiers. Docs match the wheel.
2. **Packaging:** PEP 621 + hatchling/setuptools backend, `py3-none-any`, uv, Ruff, pre-commit, Trusted Publishing. Delete `universal = 1`, `PYPI_TOKEN`, `sed` versioning.
3. **Template:** no `imp`, no `distutils`, no `admin`/`default`, `asgi.py`, `STORAGES`, `SecurityMiddleware`, split settings. `mezzanine-project` frozen as a shim.
4. **Security:** XSS regression for Exploit-DB 52385 before feature work. Form uploads get MIME/size policy. Password reset is not a magic-link login. Comments default-approve dies. Akismet fail-closed or gone. No committed secrets.
5. **Kill list (day one of the new product):** `mezzanine.twitter` (including fallback OAuth secrets), `mezzanine.mobile`, bit.ly-on-save, Universal Analytics snippet, Disqus-in-core, Gravatar-as-default, Posterous/gdata-Blogger importers, TinyMCE 4 tree, Bootstrap 3.2 as the shipped theme, Cartridge hooks in `createdb`.
6. **Keep as API:** `Displayable` / `Page` / page processors / search-as-manager / hostname multi-site / `register_setting` / `{% editable %}` / `CommentsField`·`KeywordsField`·`RatingField` contribute-to-class pattern. Form-as-`Page`. `Page.login_required` as the seed of Gate.
7. **Replace as engines:** forms EAV → typed blocks + JSONB; FileBrowser/Gallery → Asset DAM; accounts views → allauth; comments inheritance → first-party or adapter; `{% thumbnail %}` → renditions.
8. **Commerce floor:** catalog + Stripe Checkout or no commerce story at all. Never Cartridge. Never Woo-clone marketing.

Until those ship, the classifiers are a press release, not a contract.

---

*Voter F · Modules, Commerce, Platform/DX · 2026-08-11*
