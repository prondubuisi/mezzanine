# Magazine-shaped demo (TIME-inspired)

Unofficial IA demo inspired by [time.com](https://time.com/).
Not affiliated with TIME USA, LLC.

## Recreate

```bash
export NOVA_CMS_SRC=/path/to/mezzanine
nova-project timedemo --kit time
cd timedemo
just bootstrap
just demo-time
# or: just activate-theme time --seed
python manage.py runserver 127.0.0.1:8004
```

## What you get

| Path | Content |
|------|---------|
| `/` | Magazine hero, section cards, latest river |
| `/politics/`, `/world/`, `/business/`, … | Section intro + listed posts |
| `/ideas/` | Essays desk |
| `/blog/` | Full story list |
| `/contact/` | Form |

## Architecture

CMS content (`seed_site_clone --site time`) + theme kit `time` (tokens, nav, home).
Shared newsroom shell: `kit_base`, section page processor, river include.

## Not in scope

Covers / special packages, paywall, video essays, newsletter product.
