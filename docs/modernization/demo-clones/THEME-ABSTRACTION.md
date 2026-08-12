# Theme abstraction notes (from six-site IA clones)

**Preference:** a **WordPress-like theme system** (packaged look + templates +
assets, swappable without rewriting the project).  
**Design contract:** Amendment 1 §A1.2a (KD12b) in local `docs/modernization/DESIGN.md`
(gitignored — not uploaded). Mock: `docs/modernization/demo/index.html` → **Themes**.  
**Today:** Nova has **HOST_THEMES** (hostname → package) + **kits** (copy-on-create
tokens/templates). Clones reuse one chrome and swap **content**.

This file tracks **commonalities** across TechCrunch / TIME / White House /
Harvard Gazette / TED Blog / Spotify Newsroom demos for designing a real theme
layer.

---

## What every clone needed (common surface)

| Concern | How clones express it | WP theme analogue |
|---------|----------------------|-------------------|
| Site identity | SITE_TITLE, SITE_TAGLINE, brand color | `style.css` Theme Name + Customizer |
| Global chrome | Header, footer, nav shell | `header.php` / `footer.php` |
| Primary nav items | Section pages + blog link | Menu locations |
| Section IA | Named landings (Politics, Research, …) | Pages + categories |
| Story stream | BlogPost + categories | `index.php` / `home.php` / archives |
| Single story | Blog detail template | `single.php` |
| Static pages | RichTextPage | `page.php` |
| Contact / press | Form page | page template + plugin |
| Design tokens | CSS variables in `tokens.css` | `theme.json` + CSS |
| Home hero | kit `index.html` block | front-page template |
| Media | Media model / featured image (often off) | Media library + featured image |

---

## Differences (must not force into one template)

| Site class | Extra needs |
|------------|-------------|
| Tech news (TC) | Dense river, topics, events teaser |
| Magazine (TIME) | Sections, packages, ideas vs news |
| Gov (WH) | Document types, briefings, accessibility-first chrome |
| University (Gazette) | Research/campus hubs, people later |
| Ideas/video (TED) | Talk/video entity, themes |
| Corporate newsroom (Spotify) | Press kit, embargo, brand footer |

---

## Proposed WP-like theme abstraction (target)

```text
Theme package (importable)
├── theme.json          # name, version, slots, menus, colors, template map
├── templates/
│   ├── base.html       # chrome
│   ├── home.html       # front page (river or hero)
│   ├── section.html    # category/section landing
│   ├── single.html     # post
│   └── page.html       # page
├── static/<theme>/
│   └── tokens.css      # or theme.json → CSS variables
└── optional: screenshot.png
```

### Runtime selection (preferred over copy-on-create kits)

1. **Setting** `ACTIVE_THEME = "nova_themes.magazine"` **or**  
2. **HOST_THEMES**-style map (already exists) but with a **theme.json** contract  
3. Loader order: active theme → project overrides → apps  

Kits become **theme + content recipe** (`theme` + `seed profile`), not a one-time copy that freezes chrome.

### Template slots (from clone commonalities)

| Slot | Purpose |
|------|---------|
| `chrome` | nav, footer, brand |
| `home` | river / hero / packages |
| `section` | list by category/section |
| `single` | article |
| `page` | marketing page |
| `form` | contact/press |
| `search` | results |

### Menus (WP menu locations)

| Location | Clone use |
|----------|-----------|
| `primary` | Section pages + News |
| `footer` | About, Contact, legal |
| `social` | optional later |

### Tokens (already partial)

Shared CSS variables: `--nova-ink`, `--nova-accent`, `--nova-font-*`, measure, radius.  
Theme packages only override tokens + a few layout blocks.

---

## Gaps blocking WP-like themes today

See also `PARITY-BACKLOG.md`. Theme-specific:

1. No installable theme package contract (`theme.json`)  
2. Kits **copy** templates into the project — switching theme is manual  
3. No home/section/single **slot** map; one `base.html` + content types  
4. Section pages ≠ category archives (dual IA)  
5. Featured image default off; no theme supports “post thumbnail” UX  
6. No Customizer-equivalent for logo/colors without code  

---

## Sit lab testing protocol

Project: `/Users/prondubuisi/gitrepos/dev/sitelab`  
Server: http://127.0.0.1:8001/  

```bash
export NOVA_CMS_SRC=/Users/prondubuisi/gitrepos/dev/mezzanine
cd /Users/prondubuisi/gitrepos/dev/sitelab
just demo-clone techcrunch --flush   # then time, whitehouse, …
# hard-refresh browser
```

Order for UI pass: `techcrunch` → `time` → `whitehouse` → `harvard_gazette` → `ted_blog` → `spotify_newsroom`.

For each site, note:

- [ ] Brand/title correct  
- [ ] Nav sections present  
- [ ] Posts visible under `/blog/`  
- [ ] Contact form  
- [ ] What feels “missing for a theme” (home river, section lists, …)  

Append observations under **Session notes** below.

---

## Implemented slice (2026-08-12)

After White House IA parity, common surface was extracted before the Spotify kit:

| Piece | Status |
|-------|--------|
| `kit_base.html` + tokens block | Done (all first-party kits) |
| Shared `nova_kits/newsroom.css` (banner/grid/card/river) | Done |
| `kit_wants_blog(meta)` from kit.json types | Done (no kit-name allowlist) |
| `seed_profile` on kit.json → createdb | Done (whitehouse, spotify) |
| Section slug ↔ category listing | Done (page processor) |
| Installable theme.json / Customizer | Still gap (see above) |

White House and Spotify kits are **thin**: tokens + nav + home copy only.

## Session notes

_(fill while testing)_

| Site | Time | Observation | Theme implication |
|------|------|-------------|-------------------|
| whitehouse | 2026-08-12 | IA demo good; shared classes replace wh-* | Tokens-only kit works |
| spotify_newsroom | 2026-08-12 | Kit + slug-aligned sections | Same shell, dark tokens |
