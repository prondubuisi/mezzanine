==============================================
Demo: wordpress.org–shaped site on Nova (PoC)
==============================================

This proof of concept rebuilds the **public information architecture** of a
popular open-source CMS marketing site (inspired by `wordpress.org`_) using
Nova kits and seeds — not a pixel clone, and not affiliated with Automattic.

What you get
============

* **Pages:** Features, Learn, Hosting, Community, About, Get started
* **Form:** Contact (typed Form page — no contact-form plugin)
* **News:** Blog posts including a “Hello world” analogue
* **Tokens:** Blue marketing palette under ``static/wporg/tokens.css``
* **Import path:** a sample WXR at ``tests/fixtures/wxr_wporg_inspired.xml``

Friday path (generated project)
===============================

::

    $ uvx nova-project openpublish --kit wporg
    $ cd openpublish
    $ just bootstrap
    $ just demo-wporg          # or: python manage.py seed_wporg_demo
    $ just up

Then open http://127.0.0.1:8001/ — nav pages from seed + News from the blog.

Monorepo path (no PyPI)
=======================

::

    $ cd /path/to/mezzanine
    $ NOVA_CMS_SRC=$PWD just up   # from a generated project, or run tests
    $ uv run python -c "..."      # or use project_template manage.py
    $ just demo-wporg

From this repository’s package tests::

    $ uv run pytest tests/test_wporg_demo.py -q

Import the same IA via WXR
==========================

::

    $ just import-wp tests/fixtures/wxr_wporg_inspired.xml

That exercises the adult importer (pages → RichTextPage, posts → BlogPost,
redirects) with content that matches the seed’s story.

Why this is the PoC
===================

WordPress’s default marketing shape is universal: product pages + news +
get-started CTA + contact. Reproducing that with **typed models**, one kit
flag, and one seed command is the honest “replace a marketing WP box”
demo — without Gutenberg, theme.json, or 69k plugins.

.. _wordpress.org: https://wordpress.org/
