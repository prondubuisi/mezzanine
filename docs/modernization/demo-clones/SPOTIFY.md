# Spotify Web Player–style demo

Unofficial **music player UI** demo inspired by the Spotify web app.
Not affiliated with Spotify AB. No real audio streaming.

This is **not** the corporate newsroom (`spotify_newsroom` seed profile).

## Recreate

```bash
export NOVA_CMS_SRC=/path/to/mezzanine
cd /path/to
uv run --directory "$NOVA_CMS_SRC" python -c "
import os, sys
os.chdir('.')
sys.argv = ['nova-project', 'spotdemo', '--kit', 'spotify']
from mezzanine.bin.mezzanine_project import create_project
create_project()
"
cd spotdemo
# migrate as usual, then:
python manage.py runserver 127.0.0.1:8002
```

```bash
just demo-spotify-flow   # prints route map
```

## Demo flow

| Step | Path | What |
|------|------|------|
| 1 | `/` | Home shelves (playlists, albums, jump back in) |
| 2 | `/search/?q=Luna` | Search tracks/artists/albums/playlists |
| 3 | `/playlist/daily-mix-1/` | Playlist + track list + Play |
| 4 | `/album/night-bus/` | Album detail |
| 5 | `/artist/luna-park/` | Artist + popular + discography |
| 6 | `/library/` | Library grid |
| — | bottom bar | Demo now-playing (no audio) |

## Abstraction map

| Layer | Location | Responsibility |
|-------|----------|----------------|
| Catalog data | `mezzanine/demos/music_catalog.py` | Artists, albums, tracks, playlists (plain dicts) |
| Views / URLs | `mezzanine/kits/spotify/views.py`, `urls.py` | HTTP surface |
| Chrome | `kits/spotify/templates/spotify/` | Player shell, shelves, tables |
| Assets | `kits/spotify/static/spotify/player.{css,js}` | Layout + fake transport |
| Kit contract | `kit.json` → `urlconf` | Mount routes at `/` via `apply_kit` |

Editorial kits (White House, newsroom seed) stay on `kit_base` + blog.
This kit does **not** use newsroom chrome or `seed_site_clone`.

## Related but separate

- **IA profile** `spotify_newsroom` — company press site shape (blog/pages).
- **Kit** `spotify` — music player UI only.
