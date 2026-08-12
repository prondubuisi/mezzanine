# Spotify Newsroom–style demo

Unofficial IA demo inspired by [newsroom.spotify.com](https://newsroom.spotify.com/).
Not affiliated with Spotify AB.

## Recreate efficiently

```bash
# From monorepo parent directory:
cd /path/to
export NOVA_CMS_SRC=/path/to/mezzanine

uv run --directory "$NOVA_CMS_SRC" python -c "
import os, sys
os.chdir('.')
sys.argv = ['nova-project', 'spotdemo', '--kit', 'spotify']
from mezzanine.bin.mezzanine_project import create_project
create_project()
"

cd spotdemo
export NOVA_CMS_SRC=/path/to/mezzanine
just bootstrap          # migrate + superuser + seed (seed_profile)
just up                 # http://127.0.0.1:8001/
```

Re-seed only:

```bash
just demo-spotify       # or: just demo-clone spotify_newsroom --flush
```

Login: `admin` / `default` (DEBUG createdb default).

## What you get

| Path | Content |
|------|---------|
| `/` | Dark newsroom hero, section cards, latest posts river |
| `/company-news/` | Company announcements + listed posts |
| `/product-features/` | Product launch posts |
| `/culture/` | Workplace / culture posts |
| `/creators/` | Creator-economy posts |
| `/policy/` | Policy / trust posts |
| `/for-the-press/` | Press kit stub + contact path |
| `/about/` | Demo disclaimer |
| `/blog/` | Full story list |
| `/blog/<slug>/` | Story + section back-links |
| `/contact/` | Press/general form (submit → thank-you) |

## Demo flow (operator + visitor)

Intended path after bootstrap/seed:

1. **Home** `/` — brand hero, section cards, latest river  
2. **Section** `/company-news/` (or Product / Culture / …) — intro + listed posts  
3. **Story** `/blog/new-listening-feature/` — body + “All stories / section / press contact”  
4. **Category filter** `/blog/category/product-features/` — archive by desk  
5. **Press hub** `/for-the-press/` — media kit stub → contact  
6. **Contact** `/contact/` — submit email + message → `?sent=1` thanks  

Automated: `tests/test_spotify_demo.py::test_spotify_demo_end_to_end_flow`  
CLI after project create: `just demo-spotify` then open the URLs above.

## How it works (lean, modular)

1. **Kit `spotify`** — dark/green tokens, newsroom chrome, home grid, footer links.
2. **`seed_site_clone --site spotify_newsroom`** — pages + categories + posts (slugs aligned).
3. **Shared newsroom layer** — `kit_base.html`, `nova_kits/newsroom.css`, section page processor, river include, story template.
4. **`kit.json` `seed_profile`** — createdb seeds without hard-coding kit names for site clones.

## Abstraction map (keep separate)

| Layer | Location | Responsibility |
|-------|----------|----------------|
| Content recipe | `mezzanine/demos/site_profiles.py` | Pages, categories, posts, notes |
| Seed runner | `seed_site_clone` | Persist profile into DB |
| Shared chrome | `kits/shared/templates/` + `nova_kits/newsroom.css` | Layout shell, river, section list, story nav |
| Brand kit | `kits/spotify/` | Tokens, primary/footer nav, home copy only |
| Kit contract | `kit.json` (`types`, `seed_profile`) | Blog on/off + bootstrap seed |
| Loader | `kits/loader.py` | Validate + overlay project (no kit-name allowlists for blog) |

Do **not** put brand colors in shared CSS or seed copy in kit templates.

## Not in scope (yet)

Press asset packs, embargo workflow, multi-locale newsroom switcher, OG card pipeline,
demo-lab theme swap when switching profiles (content only today).
