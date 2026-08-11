# Vote D — Security, Inclusion, AI-Safety

**Seat:** Voter D (Byzantine consensus)  
**Lenses:** adversarial security, accessibility/editorial inclusion, AI-safety (Proposal law, provenance, deny-by-default)  
**Sources:** `04-security.md`, `17-inclusion.md`, `12-ai-native.md`, `14-skeptic.md`, `13-product.md`, `02-editor.md`  
**Constraint:** Mezzanine repo not modified.

## Ballot

| Motion | Vote | One line |
|---|---|---|
| M1 Strategy | **C** | Extract the kernel into a new product. Do not hospice-only, library-only, or “beat WordPress in place.” |
| M2 Year-1 ICP | **D** | Python shop replacing one marketing WP box. Not campus federation until isolation and gates exist. |
| M3 Editor | **B** | Editorial Desk; hide admin from editors. Typed-visual is the model, not the Y1 surface. |
| M4 Wedge | **D** | AI provenance / RAG content OS. Cite-or-don’t-write. Never silent publish. |
| M5 Name | **D** | Defer. A name is a fitness claim we cannot make yet. |
| M6 Commerce Y1 | **A** | None. Payments expand the threat model before the floor exists. |
| M7 Ecosystem | **B** | Curated, signed kits/types only. No plugin bazaar. |
| M8 Admin fate | **B** | Superuser-only escape hatch. Editors never live in Django admin. |

**Compact:** M1=C M2=D M3=B M4=D M5=D M6=A M7=B M8=B

---

## Why these letters (by motion)

### M1 Strategy — **C** New product that extracts the Mezzanine kernel (rebrand)

Security’s ship/no-ship line is not ambiguous: this tree is not a 2026 multi-tenant or compliance CMS. Two 2025 CVEs are still present (`displayable_links_js` as `text/html`, form-upload filename XSS). Password-reset *is* login. Form `default` is SSTI. `RICHTEXT_FILTER_LEVEL` is an admin kill switch. Bleach runs on save, not render. Drafts are “any `is_staff`.” Media and users are shared across sites. That is not a backlog you evolve past while claiming to beat WordPress.

Inclusion’s verdict is the same shape: not a newsroom, not public-sector, not multilingual. Default status is Published. There is one `alt=` in the first-party tree. PO files froze in 2013. Roles are a boolean. Inclusion-as-types (media that cannot exist without alt, themes that cannot ship failing contrast, publish that refuses unowned/untranslated/inaccessible copy) cannot be shimmed onto TinyMCE `valid_elements: "*[*]"` and `grappelli_safe`.

AI-native forbids a chatbot bolted onto Grappelli. The law is Proposal → Policy → Revision → human Publish. That is a new content OS, not a Mezzanine 7 feature flag.

- **A Hospice/LTS** is a *duty* to existing operators (patch the two live CVEs, drop Django 2.2, kill Twitter/Flash). It is not a strategy. Hospice never gets typed media, signed preview, or Proposal law.
- **B Extract library only** keeps Displayable/Page honest and then abandons the desk, the gates, and the AI OS. A library cannot enforce deny-by-default publish.
- **D Evolve in place to beat WordPress** is the skeptic’s forbidden move and security’s deck-chair rearrange. You would ship the old attack surface under a new README.

**C** is the only path that lets illegal states stop compiling: extract Page/Displayable/processors, throw away the 2012 chrome, and build defaults WordPress *cannot* ship (no stored `<script>` even if a site owner tries, no cross-tenant `get(id=)`, no password-only staff, no image without alt, no model output without a citation and a human).

Hospice the old tree in parallel. Do not confuse that with the product.

### M2 Year-1 ICP — **D** Python shops replacing a marketing WP box

Product wants a university comms director and a federation of 30–300 properties. Inclusion explicitly rejects public-sector / higher-ed / regulated as a ship target *for this system*. Security says the only honest deploy today is single-site brochureware behind SSO and a WAF, and that current “multi-tenancy” is virtual hosting: shared users, shared media, IDOR on form files, drafts-by-URL, superuser as cross-tenant god object.

Selling **B Higher-ed federation** in year 1 is selling isolation and WCAG you do not have to people who answer to counsel and a human-rights commission. That is an inclusion and security failure, not a GTM win.

**C Agencies migrating WP** imports the plugin-XSS culture and will demand HTML freedom plus a marketplace — the two things that make WordPress indefensible.

**A Django freelancer Friday-site** is how `createdb` still seeds `admin`/`default` and how inaccessible kits ship because “it worked on Friday.” Fast-and-loose defaults are the opposite of this seat.

**D** is the honest ICP: one marketing site, one Python shop, one WP box they already hate, a technical buyer who can put OIDC in front and not ask for unsigned plugins. Blast radius is one tenant. That is where you prove render-time sanitization, draft-default, signed preview, required alt, and Proposal-gated AI *before* anyone says “campus.”

Federation is a year-2+ privilege earned by tests that fail the build when tenant A reads tenant B.

### M3 Editor — **B** New Editorial Desk, hide admin from editors

Security: the admin *is* the XSS oracle (`window.__csrf_token` on every page, unpatched `displayable_links_js`, filename `mark_safe`, Settings can set filter level to none). Authors must not live there.

Inclusion: a newsroom is desks, states (`draft → review → copydesk → scheduled → published`), signed preview for non-staff, and a publish button that runs gates. Django admin will never be that. Default-Published + staff-sees-live-URL is not preview.

AI-safety: accept/reject of a Proposal is a desk verb. It is not a TinyMCE toolbar button and not a sidebar ChatGPT.

- **A Modernize admin + HTMX inline** keeps editors on the infected surface and calls it progress. HTMX on `{% editable %}` is a fine *implementation tactic* inside a desk. It is not the product.
- **C Typed-block visual editor** is the right *document model* (editor §7, inclusion typed media, AI filling typed fields). Building a Sanity/Wagtail canvas in Y1 is a new contenteditable XSS factory before the old CVEs are gone. Types first, canvas later. The Desk can edit typed fields as forms + portable-text islands without cloning Gutenberg.

Authors see the Desk. Superusers keep admin as break-glass (see M8). TinyMCE 4, jQuery Tools overlay, Chosen, Flash: kill list, not roadmap.

### M4 Wedge — **D** AI provenance / RAG content OS

This is the only wedge that encodes the AI-safety law instead of bolting a generator onto a CMS.

Non-negotiable shape (from `12-ai-native.md`, enforced by this seat):

- Every model action is a **Proposal** against typed fields, never a silent publish.
- **Citations required.** If you cannot cite the site’s own retrieval, you do not write the sentence.
- **Deny-by-default.** Provider-agnostic. Human publish.
- `ProvenanceEvent` on every generated span (who / what / when / source / model / prompt hash).
- Evals: citation precision, schema-valid output, **no-unpublished-leak**, a11y-alt coverage.
- No training on private org content without a contract.
- No SEO sludge farms. No auto-publish.

Why not the others:

- **A WP migrate + typed AI authoring** — migrate is a first-class *ability*, and it must stay `MigrationJob → inferred schema → human confirm`. Security already flags importers as a bleach bypass (`Model.save()` does not `full_clean()`). If migrate+AI is the *wedge*, raw WP HTML and uncited drafts become the growth loop. Unsafe unless D’s pipeline exists first.
- **B Site kits + Friday install** — ships themes without contrast tokens, skip links, or alt types. “Friday” fights hardened project-template defaults (SecurityMiddleware, password validators, no `admin`/`default` in `DEBUG=False`).
- **C Federation publishing OS** — product’s romance; security’s documented lie until tenancy is a test. Do not wedge on isolation you failed.

RAG over *this site’s published* content, with provenance and a human on the publish key, is how AI becomes an inclusion tool (alt, transcript, translation proposals) rather than a spam cannon. That is the wedge WordPress cannot copy without burning the plugin economy.

### M5 Name — **D** Defer name, ship under working title

A name is a claim.

- **A Keep Mezzanine** keeps the CVE brand, the 2013 catalogs, and the skeptic’s “brand death.”
- **B Masthead** is Product’s newsroom metaphor. Inclusion just refused to ship this to a newsroom. Do not name the thing after the job we fail.
- **C Nova** is a fresh coat of paint on an undecided product. Fine as a *working* title, not as a decision.

Ship under a boring working title until: the two live CVEs are gone, render-time sanitization is on, default is Draft, skip-link + required alt exist, and Proposal/provenance is the only AI path. Then name it. Not before.

### M6 Commerce Y1 — **A** None

Commerce’s own brief is almost right (“affordance, not an engine; never see a PAN”) and still too early.

Y1 security/inclusion budget is: patch XSS, bleach on read, kill SSTI, 2FA/SSO for staff, signed preview, tenant-prefixed media, default Draft, alt as a type, publish gates, Proposal law. A catalog + Stripe Checkout adds webhooks, receipts, PII, order IDOR (the form-file bug with money), and AI-generated product copy liability.

**C Revive Cartridge** is a hard no from every technical brief (Django ≤4.1, Stripe broken since 2020, PCI cosplay).

Year 2, maybe **B** as “this page can take money” via Stripe Checkout, no PAN, no shipping plugins, no Woo slide — *after* the floor exists. Not in the same year we still serve JSON as `text/html`.

### M7 Ecosystem — **B** Curated signed kits/types only

**C Open plugin marketplace** is how WordPress got 11k+ vulns in a year. Mezzanine has no sandbox. Unsigned Python on the same process as `mark_safe` is RCE with extra steps. Security, extensibility, and product already said never.

**A Never marketplace** is the purist security vote. It also blocks the *only* safe distribution path for inclusion: contrast-token themes, typed-media kits, signed capability manifests that *cannot* turn bleach off or add a raw HTML field.

**B** is the security-engineering vote: reviewed, signed, versioned kits and content types. Abilities are named tools with JSON Schema and a permission callback — not `eval` of a plugin. A kit that fails contrast CI or omits alt types does not sign. No install-from-URL. No unsigned code on the publish path.

### M8 Admin fate — **B** Admin is superuser-only escape hatch

- **A Stay Django admin forever** leaves editors on Grappelli/TinyMCE 4/filebrowser, Settings as a security kill-switch panel, and no desk. Rejected by security, inclusion, product, and editor.
- **C Replace admin entirely in Y1** spends the year rewriting chrome instead of patching `displayable_links_js`, and you will get the authz bugs of a greenfield admin *plus* no break-glass. Superusers still need users, sessions, raw objects, and step-up recovery.

**B** matches the 2026 requirement list: staff live in the Desk (capability roles, gates, Proposals). Django admin remains for superuser break-glass with step-up auth. Settings that change the security model (`RICHTEXT_FILTER_LEVEL` — which should die as an admin editable — `COMMENTS_DEFAULT_APPROVED`, SSL) require re-auth and an audit row. Editors never see it.

---

## Cross-cuts this seat will not trade

1. **Sanitize on write *and* read.** `|richtext_filters` bleaches or it does not `mark_safe`. Delete `RICHTEXT_FILTER_LEVEL_NONE` from admin; raw HTML is an env var + restart.
2. **Default Draft. Signed, expiring, object-scoped preview.** Drafts are never “any `is_staff` on the public slug.”
3. **2FA/WebAuthn before `is_staff` works.** Password-reset does not create a session. SSO for orgs; disable password when SSO is on.
4. **Tenancy is a CI test**, not a docstring. Media keys `sites/<id>/`. No cross-site `get(id=)`.
5. **Inclusion is a type.** No `ImageAsset` without alt (or decorative=true). No theme that fails contrast. No publish without author/desk. Skip link + `<main>` are not optional.
6. **AI is a Proposal.** No unpublished retrieval leak. No provider lock-in. No training on private content without a contract. Citations or silence.
7. **Do not fork gravity.** We extract the kernel. We do not out-plugin WordPress.

If another voter’s plan needs an open marketplace, in-place WordPress-killer branding, campus federation in Y1, Cartridge, or a chatbot that can publish — this seat votes no on that plan, regardless of the letter it was filed under.

— **Voter D** (Security / Inclusion / AI-Safety)
