# White House–style demo

Unofficial IA demo inspired by [whitehouse.gov](https://www.whitehouse.gov/).
Not affiliated with the U.S. government.

## Recreate efficiently

```bash
# From monorepo parent directory:
cd /path/to
export NOVA_CMS_SRC=/path/to/mezzanine

uv run --directory "$NOVA_CMS_SRC" python -c "
import os, sys
os.chdir('.')
sys.argv = ['nova-project', 'whdemo', '--kit', 'whitehouse']
from mezzanine.bin.mezzanine_project import create_project
create_project()
"

cd whdemo
export NOVA_CMS_SRC=/path/to/mezzanine
just bootstrap          # migrate + superuser + seed whitehouse
just up                 # http://127.0.0.1:8001/
```

Re-seed only:

```bash
just demo-whitehouse    # or: just demo-clone whitehouse --flush
```

Login: `admin` / `default` (DEBUG createdb default).

## What you get

| Path | Content |
|------|---------|
| `/` | Briefing Room hero, priority cards, latest posts river |
| `/releases/` | Section intro + listed Releases posts |
| `/briefings/` | Briefing posts |
| `/presidential-actions/` | Action summaries |
| `/nominations/` | Nominations posts |
| `/administration/`, `/priorities/`, `/about/` | Static hubs |
| `/blog/` | Full news list |
| `/contact/` | Press/general form |

## How it works (lean)

1. **Kit `whitehouse`** — navy/red tokens, official-style chrome, home grid.
2. **`seed_site_clone --site whitehouse`** — pages + categories + 8 posts (slugs aligned).
3. **Page processor** — RichText section pages whose slug matches a `BlogCategory` list posts on the page.
4. **Homepage river** — shared `includes/recent_posts.html`.

## Not in scope (yet)

EO PDF packages, live video, full USWDS, multi-step clearance workflow.
