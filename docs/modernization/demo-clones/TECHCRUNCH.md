# Tech news desk demo (TechCrunch-shaped)

Unofficial IA demo inspired by [techcrunch.com](https://techcrunch.com/).
Not affiliated with TechCrunch or Yahoo.

## Recreate

```bash
export NOVA_CMS_SRC=/path/to/mezzanine
nova-project tcdemo --kit techcrunch
cd tcdemo
just bootstrap   # or migrate + createdb
just demo-techcrunch
# or: just activate-theme techcrunch --seed
python manage.py runserver 127.0.0.1:8003
```

Login (DEBUG createdb default): `admin` / `default`.

## What you get

| Path | Content |
|------|---------|
| `/` | Dark hero, desk cards, latest posts river |
| `/startups/`, `/venture/`, `/ai/`, `/apps/`, `/security/` | Section intro + category posts |
| `/events/` | Static events stub (no Events model yet) |
| `/blog/` | Full river |
| `/contact/` | Press/general form |
| `/about/` | Demo disclaimer |

## Architecture (CMS)

Same pattern as White House:

1. **Theme kit `techcrunch`** — tokens, nav, home copy (`theme.json`)  
2. **Content** — `seed_site_clone --site techcrunch` → pages + categories + posts  
3. **Shared shell** — `kit_base`, `nova-banner` / `nova-grid` / river, section page processor  

Edit stories in **Admin → Blog posts**. Switch chrome with `activate_theme techcrunch`.

## Not in scope

Infinite scroll, Crunchbase graph, first-class Events calendar, author profiles.
