# Friday install recipes for Nova.
# Works in this repository (package tests + in-tree sample) and in a
# project written by nova-project.
# Kit selection happens in nova-project. This file does not take a kit argument.

set dotenv-load := true
set positional-arguments := true

# Start Postgres + Redis, migrate, create a superuser.
# Kit is chosen by nova-project, not this recipe.
bootstrap:
	#!/usr/bin/env bash
	set -euo pipefail
	just _ensure-env
	docker compose up -d --wait db redis
	just _django createdb --noinput || just _django migrate --noinput

# Run the test suite (package pytest, or manage.py test in a generated project).
test *args:
	#!/usr/bin/env bash
	set -euo pipefail
	if [ -f tests/conftest.py ] && [ -f pyproject.toml ]; then
		if command -v uv >/dev/null 2>&1; then
			uv run pytest -q --reuse-db "$@"
		else
			python -m pytest -q --reuse-db "$@"
		fi
	else
		just _django test "$@"
	fi

# Start Postgres, Redis, and the web process.
# Pre-PyPI: from a generated project, point at the monorepo so web can
# ``pip install -e`` it: ``NOVA_CMS_SRC=../mezzanine just up`` (or absolute).
up *args:
	#!/usr/bin/env bash
	set -euo pipefail
	just _ensure-env
	if [ -z "${NOVA_CMS_SRC:-}" ] && [ -f manage.py ]; then
		# Walk up for a monorepo checkout (common when developing A0′).
		for cand in .. ../.. ../../..; do
			if [ -f "$cand/pyproject.toml" ] && grep -q 'name = "nova-cms"' "$cand/pyproject.toml" 2>/dev/null; then
				export NOVA_CMS_SRC="$(cd "$cand" && pwd)"
				break
			fi
		done
	fi
	docker compose up "$@"

# Import a WordPress WXR export. Usage: just import-wp path/to/export.xml
import-wp *args:
	#!/usr/bin/env bash
	set -euo pipefail
	if [ "$#" -lt 1 ]; then
		echo "usage: just import-wp path/to/export.xml" >&2
		exit 2
	fi
	url="$1"
	shift
	just _django import_wordpress --mezzanine-user="${NOVA_IMPORT_USER:-admin}" --url="$url" "$@"

_ensure-env:
	#!/usr/bin/env bash
	set -euo pipefail
	if [ -f .env ]; then
		exit 0
	fi
	if [ -f .env.example ]; then
		cp .env.example .env
	elif [ -f mezzanine/project_template/.env.example ]; then
		cp mezzanine/project_template/.env.example .env
	fi

_django *args:
	#!/usr/bin/env bash
	set -euo pipefail
	run() {
		if command -v uv >/dev/null 2>&1; then
			uv run --with 'psycopg[binary]' --with redis "$@"
		else
			"$@"
		fi
	}
	if [ -f manage.py ]; then
		run python manage.py "$@"
		exit 0
	fi
	# Package repo: drive the in-tree project template as the sample site.
	export PYTHONPATH="${PWD}${PYTHONPATH:+:$PYTHONPATH}"
	tmpl=mezzanine/project_template
	dst="$tmpl/project_name/local_settings.py"
	src="$tmpl/project_name/local_settings.py.template"
	if [ ! -f "$dst" ]; then
		# Heredoc lines must stay recipe-indented or just 1.x misparses them.
		python3 - "$src" "$dst" <<'PY'
		import pathlib, re, secrets, string, sys
		src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
		alphabet = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
		def key():
		    return "".join(secrets.choice(alphabet) for _ in range(50))
		text = src.read_text()
		text = re.sub(r"\{\{\s*secret_key\s*\}\}", key(), text)
		text = re.sub(r"\{\{\s*nevercache_key\s*\}\}", key(), text)
		dst.write_text(text)
		PY
	fi
	run python "$tmpl/manage.py" "$@"
