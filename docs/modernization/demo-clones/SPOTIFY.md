# Spotify listening demo (CMS-aligned)

Unofficial **listening UI** theme inspired by the Spotify web player.
Not affiliated with Spotify AB.

## WordPress analogue

| WordPress | Nova |
|-----------|------|
| **Plugin** (CPTs + rewrites + admin) | `mezzanine.music` — Artist, Album, Track, Playlist models, admin, URLs, `seed_music_demo` |
| **Theme** (templates + CSS) | `mezzanine.kits.spotify` — presentation only |
| **Demo content import** | `seed_music_demo` (from `demos/music_catalog.py` seed source) |
| **Front page / single / archive** | `music/home.html`, playlist/album/artist templates |

Content is edited in **Admin → Music**. The kit does **not** own data at runtime.

## Recreate

```bash
export NOVA_CMS_SRC=/path/to/mezzanine
nova-project spotdemo --kit spotify
cd spotdemo
# migrate includes music tables
python manage.py migrate
python manage.py seed_music_demo --flush
python manage.py runserver 127.0.0.1:8002
```

```bash
just demo-spotify-flow
```

## Flow

1. Home `/` — featured playlists + albums from **published** CMS rows  
2. Search `/search/?q=Luna` — queries models  
3. Playlist `/playlist/daily-mix-1/` — M2M tracks  
4. Album / artist detail  
5. Library  
6. Admin: change a playlist title → refresh public site  

## Abstraction rules

1. **Plugin** (`music`) — models, admin, routes, seed command  
2. **Theme kit** (`spotify`) — templates/CSS/JS only  
3. **Seed source** (`music_catalog.py`) — import input only; not imported by views  
4. Editorial newsroom profile `spotify_newsroom` remains a **separate** blog IA demo  

## Not in scope

Real audio streaming, licensed catalog, accounts, Connect devices.
