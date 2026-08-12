.. image:: https://img.shields.io/pypi/v/nova-cms.svg
   :target: https://pypi.org/project/nova-cms/
   :alt: PyPI
.. image:: https://img.shields.io/pypi/pyversions/nova-cms.svg
   :target: https://pypi.org/project/nova-cms/
   :alt: Python versions
.. image:: https://img.shields.io/pypi/djversions/nova-cms.svg
   :target: https://pypi.org/project/nova-cms/
   :alt: Django versions
.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
   :target: https://github.com/astral-sh/ruff
   :alt: Ruff

====
Nova
====

Nova is a publishing kernel descended from Mezzanine.

Install the ``nova-cms`` package. Import ``mezzanine``. The public
name is a working title; the import path does not change.

Nova is a Django content-management kernel: hierarchical pages, a
``Displayable`` publishing model, page processors, and hostname
multi-site. It is `BSD licensed`_. It is not Mezzanine 7, not a
Grappelli restyle, and not a commerce engine.

Originally created by `Stephen McDonald`_ as `Mezzanine`_.


Installation
============

Friday path (Brochure kit — the Year‑1 install)::

    $ uvx nova-project mysite --kit brochure
    $ cd mysite
    $ just bootstrap    # Postgres + Redis via compose, migrate, superuser
    $ just up           # http://127.0.0.1:8001/  (host ports 5433/6380/8001)

Before the first PyPI release of ``nova-cms``, start web with the monorepo
mounted so the container can ``pip install -e`` it::

    $ NOVA_CMS_SRC=/path/to/mezzanine just up

``just bootstrap`` does not take a kit argument; the kit is chosen when
``nova-project`` writes the project. Optionally::

    $ just import-wp ./export.xml   # requires nova-cms[migrate] (feedparser)
    $ just test

Without compose/just::

    $ pip install 'nova-cms[migrate]'
    $ nova-project mysite --kit brochure
    $ cd mysite
    $ python manage.py createdb --noinput
    $ python manage.py runserver

Omit ``--kit brochure`` for the full template (blog + galleries still
on). ``mezzanine-project`` remains a deprecated alias of ``nova-project``
for one minor.

With ``DEBUG=True`` and ``createdb --noinput``, the default account is
``admin`` / ``default``. With ``DEBUG=False``, ``createdb`` refuses that
account — use interactive createsuperuser.

Requires **Python 3.12+** and **Django 5.2, 6.0, or 6.1**. See the
documentation overview for dependencies and adding Nova to an existing
Django project.


Features
========

In addition to Django itself (ORM, templates, cache, admin), the tree
still ships:

* Hierarchical page navigation
* Draft by default, opaque preview tokens (staff URL-guessing drafts is gone)
* Per-(user, site) roles for on-site edit and preview issue
* Scheduled publishing
* Drag-and-drop page ordering
* WYSIWYG editing in admin (TinyMCE 4 until Y1.5)
* `In-line page editing`_ via HTMX textarea islands (no public jQuery)
* Brochure site kit for Friday install of a marketing site
* Adult WordPress WXR import (permalinks, Yoast meta, redirect report)
* Drag-and-drop HTML5 forms builder with CSV export
* SEO friendly URLs and meta data
* Configurable `dashboard`_ widgets
* Optional blog / galleries / accounts extras
* Tagging
* User accounts and profiles with email verification
* Translated to over 35 languages
* `Multi-lingual sites`_
* `Custom templates`_ per page or blog post
* Bootstrap-based default templates + Brochure design tokens
* API for `custom content types`_
* `Search engine and API`_ (materialization capped in Y1)
* Seamless integration with third-party Django apps
* WordPress and RSS importers
* Built-in threaded comments
* `Akismet`_ spam filtering


Support
=======

To **report a security issue**, please send an email privately to
`core-team@mezzaninecms.com`_. This gives us a chance to fix the issue
and create an official release prior to the issue being made public.

For other questions, use the `GitHub issue tracker`_ when you have a
reproducible bug (include enough to fork, run, and see it: traceback,
Python, Django, database). Broader discussion still happens on the
historical `mezzanine-users`_ list.

Communications in all project spaces are expected to conform to the
`Django Code of Conduct`_.


Contributing
============

Nova is an open source project managed using Git. The repository is
hosted on `GitHub`_. Fork it and open a pull request. See
``CONTRIBUTING.rst``.


.. _`Stephen McDonald`: https://github.com/stephenmcd
.. _`Mezzanine`: https://github.com/stephenmcd/mezzanine
.. _`Django Code of Conduct`: https://www.djangoproject.com/conduct/
.. _`BSD licensed`: http://www.linfo.org/bsdlicense.html
.. _`In-line page editing`: https://github.com/prondubuisi/mezzanine/blob/master/docs/inline-editing.rst
.. _`custom content types`: https://github.com/prondubuisi/mezzanine/blob/master/docs/content-architecture.rst
.. _`Search engine and API`: https://github.com/prondubuisi/mezzanine/blob/master/docs/search-engine.rst
.. _`dashboard`: https://github.com/prondubuisi/mezzanine/blob/master/docs/admin-customization.rst
.. _`Custom templates`: https://github.com/prondubuisi/mezzanine/blob/master/docs/content-architecture.rst
.. _`Multi-lingual sites`: https://github.com/prondubuisi/mezzanine/blob/master/docs/multi-lingual-sites.rst
.. _`Akismet`: http://akismet.com/
.. _`GitHub`: https://github.com/prondubuisi/mezzanine/
.. _`mezzanine-users`: http://groups.google.com/group/mezzanine-users/topics
.. _`core-team@mezzaninecms.com`: mailto:core-team@mezzaninecms.com?subject=Nova+Security+Issue
.. _`GitHub issue tracker`: https://github.com/prondubuisi/mezzanine/issues
