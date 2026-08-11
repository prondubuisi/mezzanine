# 07 — Platform: Developer Experience, Packaging, Tests, CI, Django/Python Modernity

**Council role:** General PLATFORM (independent, from code)
**Repo:** `/Users/prondubuisi/gitrepos/dev/mezzanine`
**Date:** 2026-08-11
**Scope:** Packaging, version matrix, tests, CI/release, bootstrap, typing, docs, 2026 DevEx
**Constraint honored:** mezzanine tree was not modified.

---

## EXECUTIVE VERDICT

**Mezzanine's platform layer is a 2014–2018 Django CMS that learned to *list* Django 5.2 and Python 3.14, but did not learn to *be* a 2026 Python project.**

The classifiers and tox matrix look modern. Everything around them is not:

| Layer | What the repo actually is | What 2026 requires |
|---|---|---|
| Runtime advertised | Python ≥3.8, Django 2.2–5.2 (`django < 6`) | Python 3.12+, Django 5.2 LTS + 6.1 |
| Runtime in docs | Python 3.7–3.10, Django 2.2–4.0 | Same as above, and truthful |
| Packaging | `setup.py` + `setup.cfg` + `universal = 1` wheels; `pyproject.toml` is Black config only | PEP 621 + hatchling/setuptools backend, `uv`, non-universal py3 wheel |
| Lint | `black==22.3.0`, `flake8<4`, `isort<6`, `pyupgrade<3` | Ruff (replaces all four) |
| Types | Zero annotations, no mypy, no django-stubs | Typed public API + django-stubs in CI |
| Tests | ~87 methods, `cov-fail-under 57`, unittest `TestCase` | 80%+ on security/admin/pages; pytest + factories; Postgres |
| CI | 35 EOL combos, PyPI token, no provenance | 6–8 living combos, trusted publishing, SBOM, SLSA |
| Bootstrap | `mezzanine-project` + `createdb` + `admin`/`default` | `uvx` / cookiecutter / compose / just |
| Frontend shipped | Bootstrap **3.2.0** (2014), jQuery **3.4.1**, TinyMCE 4 | HTMX starter, no IE shims, no vendored 2014 CSS |
| Site/docs | `http://mezzanine.jupo.org/` — community reports it dead | HTTPS docs that match the classifiers |

**Hard blockers for a 2026 release:**

1. `install_requires` is `django >= 2.2, <6` — **Django 6.0 and 6.1 cannot be installed.** Django 6.1 is the current feature release (2026-08-05). Django 4.2 LTS died 2026-04-07. The only living LTS inside the pin is 5.2.
2. Generated projects `import imp` (`settings.py:307`). `imp` was removed in Python 3.12. The bootstrap command `from distutils.dir_util import copy_tree` — `distutils` was also removed in 3.12. Classifiers claim 3.12–3.14.
3. Docs still teach Python 3.7–3.10 and Django 2.2–4.0, `python setup.py install`, default password `default`, Freenode IRC, Bitbucket/Mercurial, and Jython.
4. A stored XSS in 6.1.0 is public (Exploit-DB 52385, July 2025). The suite has one happy-path `escape()` assertion and no regression test.
5. `mezzanine.jupo.org` is the project's identity and it does not reliably serve the project. CI only deploys docs from `stable`, on Python 3.9, via an ancient GitHub Pages action.

**Score (platform only):** 3.5 / 10. Not unmaintained — 6.1.1 shipped June 2025, Django 5.2 is in the matrix — but the *engineering system* is a museum with a fresh coat of classifiers.

**Recommendation:** Treat the next major as a **platform reboot**, not a compat patch. Drop everything EOL, move metadata to `pyproject.toml`, replace the linter stack with Ruff, replace `mezzanine-project` with a compose/`just` starter, and stop promising Django 2.2.

---

## 1. Supported Python / Django matrix vs what 2026 actually needs

### What the packaging metadata claims

From `setup.cfg`:

```26:46:setup.cfg
    Programming Language :: Python :: 3.8
    Programming Language :: Python :: 3.9
    Programming Language :: Python :: 3.10
    Programming Language :: Python :: 3.11
    Programming Language :: Python :: 3.12
    Programming Language :: Python :: 3.13
    Programming Language :: Python :: 3.14
    Framework :: Django
    Framework :: Django :: 2.2
    Framework :: Django :: 3.0
    Framework :: Django :: 3.1
    Framework :: Django :: 3.2
    Framework :: Django :: 4.0
    Framework :: Django :: 4.1
    Framework :: Django :: 4.2
    Framework :: Django :: 5.0
    Framework :: Django :: 5.1
    Framework :: Django :: 5.2
...
python_requires = >=3.8
```

Install pin:

```49:51:setup.cfg
install_requires =
    django-contrib-comments >= 2.0
    django >= 2.2, <6
```

No `Framework :: Django :: 6.0` or `6.1`. The upper bound **forbids** current Django.

### What tox generates (cartesian explosion)

```1:21:tox.ini
[tox]
envlist =
    py{38,39,310,311,312,313,314}-dj{22,30,31,32,40,41,42,50,51,52}
    package
    lint
```

That is **7 × 10 = 70 theoretical cells**. Many are physically impossible (Django 5.2 needs ≥3.10; Django 2.2 never saw 3.12). CI then hand-picks ~35 of them, including `py38-dj22` — a pairing whose *both* members have been EOL for years.

### What the docs still tell humans

`docs/overview.rst` (included from README plus an install section) is a time capsule:

```48:49:docs/overview.rst
* `Python`_ 3.7 to 3.10
* `Django`_ 2.2 to 4.0
```

Python 3.7 EOL: June 2023. The overview is **two major Django LTS cycles** behind `setup.cfg`, which is itself one cycle behind reality.

### What is actually supported by upstream in August 2026

Django (djangoproject.com/download, retrieved 2026-08-11):

| Series | Status on 2026-08-11 | Python | Extended support |
|---|---|---|---|
| **6.1** | Current feature (released 2026-08-05) | 3.12–3.14 | Dec 2027 |
| **6.0** | Mainstream ended 2026-08-04; extended until Apr 2027 | 3.12–3.14 | Apr 2027 |
| **5.2 LTS** | Only living LTS | 3.10–3.14 | **Apr 2028** |
| 5.1 / 5.0 | EOL | — | — |
| 4.2 LTS | EOL **2026-04-07** | — | — |
| 3.2 / 2.2 LTS | EOL 2024 / 2022 | — | — |

Python (devguide / endoflife.date):

| Version | Status Aug 2026 |
|---|---|
| 3.14 | Bugfix (current) |
| 3.13 | Bugfix (bugfix window ends ~Oct 2026) |
| 3.12 | Security (until Oct 2028) — **Django 6 minimum** |
| 3.11 | Security (until Oct 2027) — Django 5.2 only |
| 3.10 | Security, **EOL 2026-10-31** (11 weeks away) |
| 3.9 | EOL Oct 2025 |
| 3.8 | EOL Oct 2024 |

Django 6.0 release notes are explicit: *“Python 3.12 is now the minimum supported version for Django. The Django 5.2.x series is the last to support Python 3.10 and 3.11.”*

### Compatibility truth table (advertised vs honest)

| Combo Mezzanine advertises | Honest 2026 status |
|---|---|
| py38 + dj22 | Both EOL. Do not ship. Security liability. |
| py39 + dj30/31 | All three EOL. |
| py3.10 + dj32/40/41/42/50/51 | Django side EOL. Python 3.10 dies Oct 2026. |
| py3.10–3.14 + **dj52** | **Only honest cell.** 5.2 LTS until Apr 2028. |
| Any Python + **dj60/dj61** | **Blocked by `django < 6`.** Not tested. Not classified. |
| Docs 3.7–3.10 / 2.2–4.0 | Actively false. |

### Compat shims that exist only to keep the dead alive

`mezzanine/utils/deprecation.py` still branches on Django **1.9 / 1.10**:

```37:43:mezzanine/utils/deprecation.py
def is_authenticated(user):
    if django.VERSION < (1, 10):
        return user.is_authenticated()
    return user.is_authenticated
```

`get_middleware_setting_name()` still returns `MIDDLEWARE_CLASSES`. `mezzanine/utils/urls.py` has `except ImportError:  # for Django2.2 support`. This is not “being a good citizen.” It is paying a tax to pretend 2019 is still a product.

The project template still special-cases Django 4.2 file storage instead of using the `STORAGES` dict Django 4.2 introduced:

```172:178:mezzanine/project_template/project_name/settings.py
if DJANGO_VERSION[:2] > (4, 2):
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
```

`DEFAULT_FILE_STORAGE` was deprecated in 4.2 and removed as a first-class setting path in 5.1+. A 2026 template uses `STORAGES = {"default": ..., "staticfiles": ...}`.

**Platform ruling:** The 2026 support matrix should be **Python 3.12–3.14 × Django 5.2 / 6.0 / 6.1**, with 3.11 kept *only* if 5.2-LTS-on-older-python is a stated goal. Everything else is nostalgia billed as CI minutes.

---

## 2. Packaging: leftover `setup.py`, universal wheels, no build backend

### The three-file split

| File | Role in 2026 | Role here |
|---|---|---|
| `pyproject.toml` | **The** project file: build backend, deps, tool config | 14 lines of `[tool.black]` exclude regex |
| `setup.cfg` | Legacy declarative metadata | Entire package definition |
| `setup.py` | Should not exist, or be a one-liner during transition | `from setuptools import setup; setup()` |

```1:3:setup.py
from setuptools import setup

setup()
```

There is **no** `[build-system]` table. PEP 517 isolated builds therefore fall back to setuptools' legacy path. `tox.ini`'s `package` env and `.releaserc` still invoke `python setup.py sdist` / `bdist_wheel` — the invocation setuptools has been warning about since 2021.

```25:34:tox.ini
[testenv:package]
deps =
    twine
    check-manifest
skip_install = true
commands =
    python setup.py -q sdist --dist-dir="{envtmpdir}/dist"
    twine check "{envtmpdir}/dist/*"
    check-manifest --ignore-bad-ideas '*.mo' {toxinidir}
```

```13:16:.releaserc
    ["@semantic-release/exec", {
      "verifyConditionsCmd": "python -m pip install -U pip setuptools wheel twine",
      "prepareCmd": "sed -i 's/9999dev0/${nextRelease.version}/' mezzanine/__init__.py",
      "publishCmd": "python setup.py sdist bdist_wheel && twine upload dist/*"
```

No `build`, no `hatchling`, no `uv build`. Version is a sentinel string mutated by `sed` at release time (`mezzanine/__init__.py`: `__version__ = "9999dev0"`). That works. It is also the opposite of `setuptools_scm` / hatch version-from-VCS.

### `packages = mezzanine` and `universal = 1`

```45:48:setup.cfg
[options]
python_requires = >=3.8
packages = mezzanine
include_package_data = true
```

```80:81:setup.cfg
[bdist_wheel]
universal = 1
```

Two packaging defects:

1. **`packages = mezzanine`** does not use `find:` / `find_namespace:`. Subpackages (`mezzanine.blog`, `mezzanine.pages`, …) ride along as `package_data` because `MANIFEST.in` has `recursive-include mezzanine *`. Imports work by accident of directory layout, not because the package graph is declared. `options.packages.find` is the 2016-and-later answer.
2. **`universal = 1`** means `py2.py3-none-any`. This package is Python 3 only (`python_requires = >=3.8`). A universal wheel is a lie to the installer and a Warehouse smell. Correct tag: `py3-none-any`.

`MANIFEST.in` also `prune tests` and excludes `.releaserc`, `tox.ini`, `pytest.ini`. Fine for an sdist. Combined with no `testpaths` extra that re-includes them, downstream packagers cannot run the suite from the sdist without the git tree.

### Dependency hygiene

Pinned with lower bounds only, plus that fatal Django upper bound:

- `django >= 2.2, <6` — discussed.
- `pytz >= 2021.1` — obsolete; stdlib `zoneinfo` exists since 3.9. `mezzanine/utils/timezone.py` still iterates `pytz.all_timezones`.
- `filebrowser_safe >= 1.1.1` / `grappelli_safe >= 1.1.1` — private forks, the original reason Mezzanine's admin looks like 2013 Grappelli. These are the packaging millstone. A 2026 Mezzanine either vendors a maintained admin skin or targets vanilla Django admin + Unfold/Jazzmin as extras.
- `django-contrib-comments >= 2.0` — unmaintained-adjacent; Django itself ejected comments a decade ago.
- `bleach[css] >= 5` — acceptable, but the only sanitizer test is `assertEqual(escape("<foo><div></div></foo>"), "<div></div>")`.
- No optional extra for `[postgres]`, `[redis]`, `[html5]`, `[dev]`. `testing` and `codestyle` extras exist; they pin the fossil toolchain.

### What “done” looks like

```toml
# target, not present
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "mezzanine"
requires-python = ">=3.12"
dependencies = ["django>=5.2,<6.2", ...]
[project.optional-dependencies]
dev = ["ruff", "pytest-django", "django-stubs", "pre-commit"]
```

Plus `uv.lock` (or `requirements.txt` generated from uv) for the docs/dev extras, and Trusted Publishing instead of `TWINE_PASSWORD`.

---

## 3. Test quality: coverage of security, admin, pages; what is missing

### Shape of the suite

| File | Lines (approx) | Methods | Character |
|---|---|---|---|
| `tests/test_core.py` | 797 | ~30 | Kitchen sink: HTML, search, multisite, password reset, admin inlines, cache, CSRF cookie, management commands |
| `tests/test_pages.py` | 516 | 18 | **Best file.** Hierarchy, slugs, `login_required`, menus, processors, checks |
| `tests/test_conf.py` | 261 | 13 | Editable settings + `TemplateSettings`. Thread-race test is `@skipUnless(False, ...)` |
| `tests/test_generic.py` | 210 | 8 | Ratings, comments, keywords |
| `tests/test_blog.py` | 116 | 5 | Status codes + `blog_months` |
| `tests/test_forms.py` | 106 | 3 | GET/POST 200, one i18n button, one custom email class |
| `tests/test_accounts.py` | 82 | **1** | Signup + verification email |
| `tests/test_galleries.py` | 54 | 2 | Zip import, thumbnail size |
| `tests/conftest.py` | 62 | — | Copies `project_template` to `/tmp` and `django.setup()` |

`pytest.ini` is honest to the point of self-owning:

```1:8:pytest.ini
[pytest]
addopts =
    --tb short
    --cov=mezzanine
    --cov-report html
    --cov-report term:skip-covered
    # Original coverage was 54% (not great), but at least ensure we don't go below
    --cov-fail-under 57
```

**.coveragerc** omits migrations and `*/tests/*`. 57% on the remaining library is a floor, not a goal. A CMS whose job is to accept untrusted HTML and staff input cannot ship at 57%.

Almost the entire suite is `mezzanine.utils.tests.TestCase` — a Django `TestCase` that creates a **superuser** named `test`/`test` and enables `force_debug_cursor`. There is one `pytest.mark.parametrize` (the `ifinstalled` tag) and one module-level `pytest.mark.skipif` for “are we on `stable`?”. No `pytest.fixture`s, no factory_boy / model_bakery, no `django_db` markers, no pytest-django `client`/`admin_client` fixtures. `conftest.py` does not set `TESTING=True`; `set_dynamic_settings()` only flips `TESTING` when `sys.argv[1] in ("test", "testserver")`. Under pytest that is false, so cache/nevercache tests must *manually* override `TESTING`. They even comment `# Well, this is silly`.

CI runs SQLite only. There is no Postgres service, no MySQL, no Redis, no Elasticsearch, no live-server, no Playwright.

### Pages — the one solid island

`test_pages.py` is the closest thing to a real suite:

- ascendant caching and query counts (`with_ascendants_for_slug` is 1 query)
- `set_parent` / cycle detection / slug rewrite
- `login_required` against anonymous vs authenticated, with and without `mezzanine.accounts`, with `LOGIN_URL` as path / name / view
- `page_menu` query-count invariance across a 3×3×3 tree
- `in_menus` flags and `MenusField` defaults
- page processors (`exact_page=True`)
- `PageAdminForm` slug cleaning
- system check for the page context processor

This is the core product. It should be the *template* for everything else. It is not.

Gaps even here: no test that drag-and-drop `_order` persists through the admin UI; no test that a draft child of a published parent is hidden; no test of `PageMiddleware` 404 vs fallthrough against a crowded `urlpatterns`; no test of per-page template resolution (`pages/richtextpage.html` vs slug override).

### Admin — sampled, not tested

Present:

- admin site-switcher dropdown appears once a second `Site` exists (`test_admin_sites_dropdown`)
- `BaseDynamicInlineAdmin` moves `_order` to the end of fieldsets (four unit tests, no browser)
- `ContentTyped` change-view redirects `Page` → `RichTextPage`
- password-reset *from the admin login page* (HTML scrape of “Forgot password?”)

Missing, and these are the features Mezzanine *sells*:

- Drag-and-drop page tree (the signature admin UX)
- Dashboard widgets (`DASHBOARD_TAGS`)
- Inline front-end editing (`editable.js`) — **zero tests**
- WYSIWYG widget loading / TinyMCE setup
- Filebrowser / Grappelli integration
- Admin menu ordering / `ADMIN_REMOVAL`
- Translation tabs
- Preview-on-site / draft preview token
- Scheduled publish from the admin

Admin is 40% of the product and ~8% of the assertions.

### Security — a pamphlet where a book should be

What exists:

| Test | What it actually proves |
|---|---|
| `CoreTests.test_escape` | `"<foo><div></div></foo>"` → `"<div></div>"`. One string. |
| `CSRFTestCase.test_csrf_cookie_with_nevercache` | `{% csrf_token %}` inside `{% nevercache %}` still sets the cookie |
| `GenericTests.test_comment_form_returns_400_when_missing_data` | Empty POST to `comment` is 400 (bot path) |
| `CoreTests.test_password_reset` | Happy-path reset email + form |
| `CoreTests.test_draft` | Draft URL is 404 to anonymous, 200 to staff |
| `PagesTests.test_login_required` | Authz on pages |
| `test_static_proxy*` | Three happy-path 200s for `static/test/image.jpg` |

What does **not** exist, and has already bitten the project:

- **Stored XSS regression.** Exploit-DB 52385 (2025-07-23) is a stored XSS in Mezzanine 6.1.0 via `/blog/blogpost/add`. There is no test that a staff-submitted `<script>`, `onerror=`, `javascript:` URL, or SVG payload is stripped at save *and* at render. `RICHTEXT_FILTER_LEVEL_NONE` is a documented foot-gun with no warning test.
- CSRF on the forms builder POST, ratings POST, inline-edit POST.
- `static_proxy` as an **open-redirect / SSRF** surface — only the blessed test image is fetched.
- File upload: content-type spoof, polyglot HTML-in-image, zip-slip in `Gallery.zip_import`, SVG as image.
- Mass assignment on `ProfileForm` / extra model fields.
- Host header / `SitesAllowedHosts` fallback (it queries `Site.objects.all()` the first time `ALLOWED_HOSTS` is iterated — a debug=False foot-gun).
- Password reset host poisoning (a real historical bug; the changelog mentions it; no regression test).
- `SECRET_KEY` / `NEVERCACHE_KEY` not being the template placeholders in production.
- Admin CSRF + same-site cookies.
- Rate limiting / lockout on `mezzanine.accounts`.
- Privilege: staff vs superuser vs `SitePermissionMiddleware`. The middleware has a system check and no behavioral test.

`mezzanine.utils.tests.TestCase.setUp` creates a **superuser** for every test. Almost nothing is asserted as a non-privileged user. That is how you get a green suite and a stored XSS.

### App-by-app holes

| App | Tests | Missing |
|---|---|---|
| `accounts` | 1 method | Login, logout, password change, profile update, inactive user, username enumeration, `ACCOUNTS_APPROVAL_REQUIRED`, custom profile model |
| `blog` | 5 | Categories, keywords, author filter, featured image, related posts, draft/future, `BLOG_SLUG=""`, import commands (WordPress, Blogger, …) — **seven** `import_*` commands, zero tests |
| `forms` | 3 | Email send, CSV export, file field, hidden fields, multi-step, required-field 200-on-invalid (the test POSTs `"test"` into every type including dates and files and only checks 200) |
| `galleries` | 2 | Zip-slip, non-image members, empty zip, PIL missing, EXIF |
| `generic` | 8 | Disqus path, Akismet, threaded reply notifications, rating cookie forging |
| `twitter` | 0 | Deprecated in 5.0; still in the tree; still has models, management commands, templates |
| `mobile` | 0 | Two files: a `FutureWarning` and a comment. Still a package. |
| `conf` | 13 | Admin form for settings; cache invalidation across processes (the race test is hard-skipped: `@skipUnless(False, "Only run manually - see Github issue #1126")`) |
| `boot` / lazy admin | 0 | The `admin.autodiscover()` replacement is load-bearing and untested |
| Search | inside core | No ranking-fuzz, no untrusted `q=` XSS, no multi-model registration API |

### Fixture / bootstrap smell

`conftest.pytest_configure` **copies the project template into `/tmp` and imports it as the Django settings module**. That means:

- The test settings *are* the production template, including `import imp` (see §5). Tests pass on 3.12+ only because they write `test_settings.py` and never create `local_settings.py`, so the `if os.path.exists(f): import imp` branch is not executed.
- There is no dedicated `tests/settings.py`. A template regression is a suite regression, which is good, except the dangerous branches are the ones the suite does not take.
- `PASSWORD_HASHERS = MD5PasswordHasher` is correct for speed and is the only modern testing choice in the file.

**Platform ruling:** Pages are tested like a library. Everything else is tested like a weekend project. Security coverage is performative. 57% with a superuser-only client is how CVEs ship with green badges.

---

## 4. CI reality

One workflow: `.github/workflows/main.yml`, name `Test and release`. Triggers: every `push` and every `pull_request` (no path filters, no `workflow_dispatch` concurrency group that cancels outdated PR runs).

### Jobs

**`test`** — `fail-fast: false`, ~35 explicit matrix rows, `ubuntu-latest`, `actions/setup-python@v5`, `pip install -U pip tox`, `tox -e ${{ matrix.tox-env }}`, then `mikepenz/action-junit-report@v3`.

The matrix still pays for:

- Django 2.2, 3.0, 3.1 (EOL 2022 / 2021 / 2021)
- Django 3.2 LTS (EOL 2024)
- Django 4.0, 4.1 (EOL 2023)
- Django 4.2 LTS (EOL April 2026 — **already dead at time of this report**)
- Django 5.0, 5.1 (EOL)
- Python 3.8, 3.9 (EOL)

GitHub `ubuntu-latest` in 2026 is 24.04. `actions/setup-python` can still fetch 3.8 from the deadsnakes-style cache, but 3.8 wheels for current manylinux and for `Pillow >= 7` are a time bomb. A single broken EOL cell does not fail the badge (`fail-fast: false`) — it just burns minutes and trains contributors to ignore red.

**`lint`** pins **Python 3.9** and runs `tox -e package -e lint -e pyupgrade`. The linters themselves:

```67:72:setup.cfg
codestyle =
    flake8 >= 3, <4
    black == 22.3.0
    isort >= 5, <6
    pyupgrade >= 2, <3
```

| Tool | Pinned | Current (2026) | Age |
|---|---|---|---|
| Black | **22.3.0** (Mar 2022) | 25.x | 4 years |
| Flake8 | **<4** (3.9 is 2020–21) | 7.x | 5 years |
| isort | <6 | 5.13 / ruff-isort | frozen |
| pyupgrade | <3 (`--py38-plus`) | 3.x | 3+ years |

Ruff replaced this entire cluster for the rest of the ecosystem in 2023–2024. Keeping flake8 3.x means the lint job cannot even *see* modern pyflakes/pycodestyle. `pyupgrade --py38-plus` will not rewrite `imp`, `distutils`, `pytz`, or `utcfromtimestamp`.

**`release`** — `if: github.repository_owner == 'stephenmcd'`, needs test+lint, Python 3.9, Node, `cycjimmy/semantic-release-action@v4` wrapping **semantic-release 18** (current line is 24). Publishes with:

```
TWINE_USERNAME: __token__
TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
```

This is the 2021 PyPI token pattern. It is not Trusted Publishing (OIDC). There is no `id-token: write` permission, no `pypa/gh-action-pypi-publish`, no attestations, no Sigstore, no SBOM, no SLSA provenance. A leaked `PYPI_TOKEN` is a full package takeover. `sed -i` on `__init__.py` is the versioning implementation.

**`docs`** — only `if: github.ref == 'refs/heads/stable'`, after `release`, Python 3.9, `pip install -e . && pip install sphinx` (unpinned Sphinx), `sphinx-build`, deploy via `crazy-max/ghaction-github-pages@v2` (v4+ exists) to `fqdn: mezzanine.jupo.org`. Consequences:

- Docs do not deploy from `master` / PR / tag.
- If `stable` is quiet, the public site rots. Community discussion #2038: *“The project website appears dead. The only documentation I found (on readthedocs.io) is for version 4.3.”*
- Building docs on 3.9 in 2026 is itself a smell.

### What CI does not do

- No `dependabot.yml` / Renovate.
- No CodeQL, no `pip-audit`, no `osv-scanner`, no bandit, no gitleaks.
- No pre-commit.ci.
- No mypy / django-stubs job.
- No Postgres service container.
- No cache of pip/tox (`setup-python` cache is unused).
- No concurrency cancel.
- No OIDC / environment protection on `release`.
- No artifact retention of wheels for the docs job to install *the just-built package*.
- No scheduled job. A silent breakage on Django 5.2.17 (current 5.2 patch) would wait for the next human push.

CONTRIBUTING.rst promises: *“This will run all tests in all supported Python and Django versions.”* That sentence is doing a lot of unearned work. It runs a 2019 idea of “all supported.”

---

## 5. Project bootstrap: `mezzanine-project` vs cookiecutter / `django-admin start`

### The entry point

```74:76:setup.cfg
[options.entry_points]
console_scripts =
    mezzanine-project = mezzanine.bin.mezzanine_project:create_project
```

`mezzanine.bin.mezzanine_project.create_project` configures Django with `settings.configure()`, injects `mezzanine.bin` into `INSTALLED_APPS`, and dispatches to the `mezzanine_project` management command — a subclass of `django.core.management.commands.startproject.Command`.

That command:

1. Adds a `nevercache_key` template var.
2. Renders `local_settings.py.template` → `local_settings.py`.
3. Optionally overlays an `--alternate` package's `project_template` (Cartridge / Drum) via **`distutils.dir_util.copy_tree`**.
4. Deletes the template's top-level `__init__.py` so Python ≥3.7 tests don't treat the project dir as a package.

`distutils` is not in the stdlib on 3.12+. `mezzanine-project --alternate cartridge …` is dead on every Python the classifiers just added.

### The template it stamps out

`mezzanine/project_template/` is five files and a settings module that is a historical document:

| File | 2026 problem |
|---|---|
| `manage.py` | Fine, if dated. No `DJANGO_SETTINGS_MODULE` default beyond the template tag. |
| **no `asgi.py`** | Grep for `ASGI` / `asgi` across the repo: **zero hits.** Django has shipped ASGI since 3.0 (2019). |
| `wsgi.py` | Present. Only. |
| `urls.py` | `admin.autodiscover()` (a no-op since Django 1.7), `include(admin.site.urls)` instead of `admin.site.urls`, homepage is a `TemplateView` of `index.html` with three commented alternatives. |
| `settings.py` | `import imp` to exec `local_settings.py`. Empty `DATABASES["default"]["ENGINE"] = "django.db.backends."`. `DEBUG = False` in the committed file, `True` only after local_settings. `USE_I18N = False`. No `STORAGES`, no `SECURE_*`, no `django.middleware.security.SecurityMiddleware`, no `ManifestStaticFilesStorage`, no `.env`. `STATIC_ROOT` = `<project>/static`, `MEDIA_ROOT` = `<project>/media` — collectstatic writes into the source tree. |
| `local_settings.py.template` | SQLite `dev.db` in CWD. `SECRET_KEY` / `NEVERCACHE_KEY` filled by `startproject`. |

The `imp` block, quoted because it is the single most 2026-incompatible line in the starter:

```305:314:mezzanine/project_template/project_name/settings.py
f = os.path.join(PROJECT_APP_PATH, "local_settings.py")
if os.path.exists(f):
    import imp
    import sys

    module_name = "%s.local_settings" % PROJECT_APP
    module = imp.new_module(module_name)
    module.__file__ = f
    sys.modules[module_name] = module
    exec(open(f, "rb").read())
```

`imp` was removed in 3.12. A user who follows the documented happy path on Python 3.12+ gets `ModuleNotFoundError: No module named 'imp'` on first `manage.py`. Tests do not catch this (see §3).

### `createdb` is a 2012 onboarding spell

Docs:

```22:37:docs/overview.rst
    $ mezzanine-project project_name
    $ cd project_name
    $ python manage.py createdb --noinput
    $ python manage.py runserver
...
You should then be able to browse to http://127.0.0.1:8000/admin/ and
log in using the default account (``username: admin, password:
default``).
```

`createdb.py` hardcodes `DEFAULT_USERNAME = "admin"`, `DEFAULT_PASSWORD = "default"`. `--noinput` installs that account and demo pages. That is a tutorial convenience that has been a production incident waiting to happen for twelve years. A 2026 starter uses `createsuperuser` interactively, or prints a one-time link.

`createdb` also still has a Cartridge hook (`create_shop` if `cartridge.shop` is installed) and a comment *“Adds extra command options (executed only by Django >= 1.8)”*.

### Versus the 2026 bootstrap landscape

| Mechanism | What users get | Mezzanine |
|---|---|---|
| `django-admin startproject` | `asgi.py`, `wsgi.py`, `settings.py` split-ready, no `imp` | Mezzanine wraps it and then *subtracts* ASGI and *adds* `imp` |
| cookiecutter-django / django-cookiecutter | Compose, Postgres, redis, whitenoise, settings split, pre-commit, CI, `.env` | None of these |
| `uvx` + `copier` | Re-runnable updates | One-shot copy |
| Wagtail's `wagtail start` | Working project, docs that match, `requirements.txt` | Working-if-you-are-on-3.11-and-don't-read-the-overview |
| WordPress Playground | Try in browser in 5 seconds | Try in 20 minutes if Pillow builds |

There is no `Dockerfile`, no `compose.yaml`, no `justfile`, no `Makefile`, no `.env.example`, no `requirements/local.txt`. `grep` for docker / cookiecutter / justfile / uv.lock / poetry across the repo: **no matches**.

`runserver` is overridden solely to print an ASCII mezzanine and to serve `MEDIA_URL` in DEBUG. Charming. Not a substitute for a compose stack.

**Platform ruling:** `mezzanine-project` should be frozen as a compatibility shim and replaced by a Copier/cookiecutter template that emits a 5.2/6.1 project: `uv sync`, `just dev`, `compose.yaml` (web + postgres + mailpit), `asgi.py` (uvicorn), `settings/` package (`base.py` / `dev.py` / `prod.py`), and no default password.

---

## 6. Type hints? mypy? Ruff?

**No. No. No.**

Grep of `mezzanine/**/*.py` for `->`, `from typing`, `TYPE_CHECKING`, `Optional[`, builtin generics used as annotations: **zero real hits.** The few `->` are in comments (`descendant -> ascendant order`).

There is:

- no `mypy.ini` / `[tool.mypy]`
- no `django-stubs`
- no `py.typed`
- no Ruff, no `[tool.ruff]`
- no pyright / basedpyright
- no `.pre-commit-config.yaml`
- no `pyupgrade` toward 3.12 (`--py38-plus` is the ceiling)

The type-check story is “Black 22 and flake8 3 said the files are 88 columns.” That is not a type-check story.

A 2026 Django library's minimum bar:

1. `py.typed` marker.
2. Annotations on public models, managers, `page_processors`, `register_setting`, and the search API.
3. `mypy --strict` (or basedpyright) on `mezzanine/` with `django-stubs` and `django-stubs-ext`.
4. Ruff for lint + format + isort + pyupgrade (`target-version = "py312"`), one tool, ~20ms.
5. pre-commit running `ruff`, `ruff-format`, `uv-lock`, `django-upgrade`.

`django-upgrade` in particular would mechanically delete half of `mezzanine/utils/deprecation.py`.

---

## 7. Docs quality and dead links (`jupo.org`)

### The identity URL is HTTP and widely reported dead

Every first-party URL in README / setup.cfg / docs is `http://mezzanine.jupo.org/` (no HTTPS, no trailing docs pin). `setup.cfg` `url = http://mezzanine.jupo.org/`. README image of the dashboard: `http://mezzanine.jupo.org/docs/_images/dashboard.png`. Cartridge: `http://cartridge.jupo.org/`.

Community signal (GitHub discussion #2038, still the top “is this alive?” thread): *the project website appears dead; Read the Docs only has 4.3.* This report's fetch of `http://mezzanine.jupo.org/` resolved to the GitHub repo README, not a docs site. CI deploys Pages only from `stable` onto that FQDN.

That is a **platform outage**, not a cosmetic issue. The classifiers, the README badges, the donate link, the “gallery of sites,” and every “see the docs” sentence in the code comments point at a rotting HTTP host.

### Docs content is a decade out of phase with the code

| Claim in docs | Code / world |
|---|---|
| Python 3.7–3.10, Django 2.2–4.0 | Classifiers 3.8–3.14 / 2.2–5.2; pin `<6` |
| `python setup.py install` | setuptools has discouraged this since 2019 |
| `createdb` + `admin`/`default` | still works, still dangerous |
| Freenode `#mezzanine` | Freenode collapsed in 2021; Libera is the successor; the channel is folklore |
| Bitbucket + Mercurial dual-hosting | `.hgignore` / `.hgtags` remain; nobody contributes via hg in 2026 |
| Jython / JVM compatible | listed as a **feature** in README |
| Fabric / fabfile “described earlier” in twitter docs | fabfile removed in 5.0 (`docs/deployment.rst`); twitter docs still mention it |
| IE + Edge <79 “generally unsupported” | html5shiv + respond.js still in `base.html` for `lt IE 9` |
| Bootstrap integration | **Bootstrap v3.2.0**, copyright 2014, shipped in-tree |
| “Free Themes Marketplace” | `https://github.com/thecodinghouse/mezzanine-themes` |
| mezzanine-api | archived Sep 2022, README says “use Wagtail” |
| Google Groups as primary support | `CONTRIBUTING.rst` still sends people there; issue templates point at GitHub Discussions. Two sources of truth, both quiet |

`docs/deployment.rst` is 19 lines. It says “deploy like Django” and notes the fabfile was removed. There is no 12-factor section, no HTTPS, no `SECURE_*`, no gunicorn/uvicorn, no WhiteNoise, no container, no PaaS.

`docs/twitter-integration.rst` is marked `deprecated:: 5.0` and still documents cron + OAuth + “the Fabric script described earlier.”

`docs/overview.rst` then spends hundreds of lines listing third-party plugins (OpenShift, Stackato, html5boilerplate, Bitbucket-hosted apps) and a **gallery of sites** whose URLs are a 2013–2016 webring. Several are parked or dead. This is not documentation; it is an attic.

Sphinx itself: custom 2010 `mezzanine_theme`, `djangodocs` extension, intersphinx pointed at `docs.djangoproject.com/en/dev/` (moving target, currently 6.1 — so the Django cross-links in a 2.2-era narrative resolve to 6.1 APIs). `docs/conf.py` still has a Latin-1 comment artifact (``#  Links``).

### CONTRIBUTING is thin and misspelled

`Continous Integration` (sic). Install extras, run pytest, run black/flake8, open a PR against `master`. No mention of tox, no mention of the 35-cell matrix a contributor just lit on fire, no CoC beyond “Django's,” no security.txt / `SECURITY.md` (security contact lives only in README as `core-team@mezzaninecms.com`).

### Frontend docs vs frontend bits

`base.html` still ships:

- Bootstrap **3.2.0** (2014) + `bootstrap-theme.css` + Glyphicons
- jQuery **3.4.1** (2019; current 3.7.x; known XSS CVEs in the 3.4 line)
- jQuery UI **1.12.1** (2016)
- TinyMCE **4 “modern”** with `skin.ie7.min.css` and a **Flash** `moxieplayer.swf`
- html5shiv + respond.js behind `<!--[if lt IE 9]>`
- `{% compress %}` assuming django-compressor is installed (it is optional)

A “Twitter Bootstrap integration” feature bullet in 2026, backed by Bootstrap 3.2, is a documentation bug that happens to execute in production.

---

## 8. What “modern standards” means, concretely

Not vibes. A checklist. Mezzanine's score against the 2026 default stack:

| Standard | Status | Evidence |
|---|---|---|
| **`pyproject.toml` as the project file** (PEP 517/518/621) | Fail | File is Black config. Metadata in `setup.cfg`. |
| **Build backend declared** | Fail | No `[build-system]`. |
| **`uv` for install/CI** | Fail | `pip install -U pip tox`. No lockfile. |
| **Ruff** (lint + format + isort + pyupgrade) | Fail | black 22.3.0 + flake8&lt;4 + isort + pyupgrade&lt;3. |
| **`django-upgrade`** | Fail | Manual Django 1.9 shims remain. |
| **Django 5.2+ as the *floor*** | Fail | Floor is 2.2. Ceiling is `<6`. |
| **Django 6.1 tested** | Fail | Not classified, not toxed, pin forbids it. |
| **Python 3.12+ as the *floor*** | Fail | Floor is 3.8. Template uses `imp`/`distutils`. |
| **django-stubs + mypy/pyright** | Fail | No annotations. |
| **`py.typed`** | Fail | — |
| **pre-commit** | Fail | No config. |
| **pytest-django idioms** | Partial | pytest is the runner; tests are unittest. |
| **Coverage that means something** | Fail | `--cov-fail-under 57`. |
| **Postgres in CI** | Fail | SQLite only. |
| **Dependabot / Renovate** | Fail | — |
| **pip-audit / OSV in CI** | Fail | — |
| **Trusted Publishing (OIDC → PyPI)** | Fail | Long-lived `PYPI_TOKEN`. |
| **Sigstore / `pypi-attestations`** | Fail | — |
| **SLSA provenance** | Fail | `python setup.py sdist bdist_wheel && twine upload`. |
| **SBOM** (CycloneDX / SPDX on the wheel) | Fail | — |
| **`SECURITY.md` + private vuln reporting that is not only an email in a README** | Fail | Email only. No GHSA enablement documented. |
| **ASGI first** | Fail | No `asgi.py` anywhere. |
| **`STORAGES` / Django 5 static** | Fail | `DEFAULT_FILE_STORAGE` shim. |
| **`zoneinfo` not pytz** | Fail | `pytz` is a hard dep. |
| **Settings via env** (`django-environ` / `pydantic-settings`) | Fail | `exec(open(local_settings.py))`. |
| **Compose + one-command dev** | Fail | — |
| **No default credentials in docs** | Fail | `admin` / `default`. |
| **HTTPS docs that match the wheel** | Fail | `http://mezzanine.jupo.org/`, content stuck at 4.x narrative. |
| **Frontend not from 2014** | Fail | Bootstrap 3.2.0, TinyMCE 4, Flash player. |

That is 0 pass, 1 partial, 28 fail. “We added a 3.14 classifier” is not modernity.

### A 90-day modernization sequence (ordered by leverage)

1. **Tell the truth in metadata.** `requires-python = ">=3.12"`, `django>=5.2,<6.2`, drop 2.2–5.1 classifiers, rewrite `docs/overview.rst` install section. One PR.
2. **Move to `pyproject.toml` + `python -m build`.** Kill `universal = 1`. Kill `setup.py` in `.releaserc`.
3. **Ruff + pre-commit + `django-upgrade --target-version 5.2`.** Delete `deprecation.py` branches for `<1.10`.
4. **Fix the template:** `importlib` not `imp`, `shutil.copytree` not `distutils`, add `asgi.py`, `STORAGES`, `SecurityMiddleware`, split settings, delete default password from docs.
5. **Collapse CI to py3.12/3.13/3.14 × dj5.2/6.0/6.1 + lint + a Postgres job.** 9 cells, not 35.
6. **Trusted Publishing + `pypa/gh-action-pypi-publish` + attestation.** Delete `PYPI_TOKEN`.
7. **XSS regression file** (`tests/test_richtext_security.py`) before any feature work. Treat Exploit-DB 52385 as the first test case.
8. **django-stubs on `mezzanine/utils` and `mezzanine/pages`** (the stable API).
9. **Docs:** Read the Docs or GitHub Pages from tags, HTTPS, FQDN either revived or retired. Redirect `jupo.org` → `mezzanine.readthedocs.io` if the domain is lost.
10. **SBOM** (`cyclonedx-py`) attached to the release; `uv lock` for the docs/dev extra.

---

## 9. Revolutionary DevEx (what a CMS in 2026 actually feels like)

The user-facing bar is no longer “it has a `startproject` wrapper.” WordPress Playground, Wagtail's new project template, and every JS meta-framework have moved the “time to first edit” target to **seconds**, on a phone, without a local Python.

Three concrete leaps, in increasing ambition. All are absent today.

### 9.1 One-command local: `docker compose` + `just`

A root `justfile`:

```just
dev:
    uv sync --extra dev
    docker compose up -d db mailpit
    uv run manage.py migrate
    uv run manage.py createsuperuser --noinput || true
    uv run uvicorn project.asgi:application --reload
```

`compose.yaml`: Postgres 17, Redis, Mailpit, optionally MinIO. The Django app can run on the host (fast reload via uv) or in a `web` service. `just test` = `uv run pytest -q --reuse-db`. `just fmt` = `uv run ruff format && uv run ruff check --fix`.

This replaces: `pip install mezzanine && mezzanine-project … && createdb --noinput && runserver`, the ASCII banner, and the empty `ENGINE = "django.db.backends."`.

### 9.2 First-class HTMX / API starter

Mezzanine's front-end story is server-rendered Bootstrap 3 and a jQuery inline editor. The 2026 shape:

- **Default theme:** Bootstrap 5 or a Pico/vanilla CSS theme, no jQuery.
- **Inline edit** reimplemented as HTMX endpoints with CSRF on every mutation, not `editable.js` + TinyMCE 4.
- **`mezzanine.api`:** a documented, versioned Django-Ninja (or DRF) app *in tree*, not the archived `gcushen/mezzanine-api`. Pages, blog, forms submissions as JSON, OpenAPI generated.
- A `project_template` extra `just frontend` that drops in an HTMX + Alpine island, not a third-party “mezzanine-themes” GitHub repo last touched years ago.

Without this, Mezzanine cannot recruit anyone who has touched Wagtail, Django + HTMX, or Next. Cartridge (ecommerce) is a sibling fossil (`cartridge.jupo.org`) and cannot be the “modern app” story.

### 9.3 WASM try-in-browser (the WordPress Playground move)

WordPress's single best DevEx decision of the 2020s was Playground: click a link, get a working CMS in the browser, no install.

A Mezzanine Playground is now *possible*:

- Pyodide 0.27+ runs CPython 3.12 in WASM.
- Django has been demonstrated on Pyodide (Wagtail has explored this; several `django-pyodide` spikes exist).
- SQLite is already the test DB.
- A static GitHub Pages app that boots `mezzanine` + the project template into a WebWorker, serves via a Service Worker at `/playground/`, and exposes the admin.

That is a quarter of engineering. It is also the only way a CMS that lost its `jupo.org` demo site gets a demo site back without owning a VPS. “Try Mezzanine” becomes a badge, not a 12-step README that begins with `pip install` and ends on Freenode.

Stretch: a `mezzanine-project --playground` that emits the WASM wrapper; a Read-the-Docs page with an embedded iframe of the playground; a “this snippet runs” story for page processors.

### Why this is not optional

Wagtail, Django CMS, and Fountain are not waiting. The competitive object is not “another Django site with an admin.” It is:

- install in one command or zero commands,
- edit a page in 30 seconds,
- ship on Django 6 / Python 3.14 without reading a deprecation module,
- not get XSS'd by a blog post.

Mezzanine currently fails all four. The code still has a hierarchical page model that is better than most of its successors. The platform around that model is why people open discussion #2038.

---

## File index (primary evidence)

| Path | Why it matters |
|---|---|
| `setup.cfg` | Classifiers 3.8–3.14 / Django 2.2–5.2; `django<6`; black 22.3.0; flake8&lt;4; `universal=1`; `packages = mezzanine` |
| `setup.py` | Legacy `setup()` |
| `pyproject.toml` | Black exclude only — no build backend, no project table |
| `tox.ini` | 70-cell cartesian; `python setup.py sdist`; pyupgrade `--py38-plus` |
| `pytest.ini` | `--cov-fail-under 57` |
| `.coveragerc` | omit tests + migrations |
| `.releaserc` | `sed` version; `setup.py sdist bdist_wheel`; twine + token |
| `.github/workflows/main.yml` | 35 EOL cells; lint on 3.9; token publish; docs only on `stable` |
| `CONTRIBUTING.rst` | pip extras + black/flake8; “Continous Integration” |
| `docs/overview.rst` | Python 3.7–3.10, Django 2.2–4.0, `setup.py install`, `admin`/`default` |
| `docs/deployment.rst` | 19 lines, fabfile removed |
| `docs/twitter-integration.rst` | deprecated, still cites Fabric |
| `mezzanine/bin/management/commands/mezzanine_project.py` | `distutils.dir_util.copy_tree` |
| `mezzanine/project_template/project_name/settings.py` | `import imp`; empty DB engine; `DEFAULT_FILE_STORAGE` |
| `mezzanine/project_template/project_name/local_settings.py.template` | sqlite `dev.db` |
| `mezzanine/core/management/commands/createdb.py` | `admin` / `default` |
| `mezzanine/utils/deprecation.py` | Django 1.9/1.10 branches |
| `mezzanine/utils/timezone.py` | pytz |
| `mezzanine/utils/tests.py` | superuser-for-every-test base |
| `tests/*` | 8 modules, ~87 methods, no factories, no XSS suite |
| `mezzanine/core/static/css/bootstrap.css` | Bootstrap v3.2.0, 2014 |
| `mezzanine/core/static/mezzanine/js/jquery-3.4.1.js` | jQuery 3.4.1 |
| `mezzanine/core/templates/base.html` | html5shiv, IE9, `{% compress %}` |
| `mezzanine/mobile/` | deprecated stub still packaged |
| `README.rst` | Jython, Freenode, Bitbucket, `http://mezzanine.jupo.org` |

---

## EXECUTIVE VERDICT (restate)

Mezzanine's **product idea** (hierarchical pages, inline edit, forms builder, integrated admin) is still coherent. Mezzanine's **platform** is a compatibility museum: Django 2.2 is advertised, Django 6.1 is forbidden, Python 3.12 classifiers sit on top of `import imp`, tests are allowed to sit at 57%, the linters are from 2022 and 2020, wheels are “universal,” PyPI is a long-lived token, and the website the README points at is a dead HTTP name.

A 2026-respecting Mezzanine is a **major version that deletes more than it adds**: drop EOL runtimes, move the project to `pyproject.toml` + uv + Ruff, replace `mezzanine-project` with a compose/`just` starter, put XSS regressions in CI, publish with OIDC, and put a working HTTPS document (or a WASM playground) where `jupo.org` used to be.

Until that happens, the classifiers are a press release, not a contract.

**Verdict: do not adopt for a new 2026 project without a platform reboot. Existing sites on 5.2 can stay, with eyes open, until 5.2 LTS ends in April 2028 — at which point the current pin (`django < 6`) is a hard dead end.**
