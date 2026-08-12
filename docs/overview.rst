.. include:: ../README.rst


Friday install
==============

Compose + ``just`` is the documented local path. Postgres, Redis,
and a web process::

    $ uvx nova-project mysite --kit brochure
    $ cd mysite
    $ just bootstrap
    $ just up

``--kit brochure`` is the Year-1 site kit: pages + forms, design tokens,
and demo fixtures (no blog, no galleries). Omit ``--kit`` for the full
template with blog and galleries still enabled.

``just bootstrap`` starts Postgres and Redis, runs migrations, and
creates a superuser. It does not take a kit argument — the kit is
chosen when ``nova-project`` writes the project, not at bootstrap.

Then, optionally::

    $ just import-wp ./export.xml
    $ just test

``nova-project`` writes ``compose.yaml``, ``justfile``, and
``.env.example`` into the new project. The same files live at the
repository root, where ``just test`` runs the package tests and
``just bootstrap`` / ``just up`` drive a sample site against the
in-tree project template. Copy ``.env.example`` to ``.env`` if you
start Compose without ``just bootstrap``.

With ``DEBUG=False``, ``createdb --noinput`` will not create the old
``admin`` / ``default`` account.

For information on how to add Nova (the ``mezzanine`` package) to an
existing Django project, see the FAQ section of the documentation.


Dependencies
============

Nova uses as few libraries as possible beyond a standard Django
environment. Unless marked optional, these install with ``nova-cms``:

* `Python`_ 3.12 to 3.14
* `Django`_ 5.2 to 6.1
* `django-contrib-comments`_ - for built-in threaded comments
* `Pillow`_ - for image resizing (`Python Imaging Library`_ fork)
* `grappelli-safe`_ - admin skin (`Grappelli`_ fork)
* `filebrowser-safe`_ - for managing file uploads (`FileBrowser`_ fork)
* `bleach`_ and `BeautifulSoup`_ - for sanitizing markup in content
* `pytz`_ and `tzlocal`_ - for timezone support
* `chardet`_ - for supporting arbitrary encoding in file uploads
* `django-modeltranslation`_ - for multi-lingual content (optional)
* `django-compressor`_ - for merging JS/CSS assets (optional)
* `requests`_ - HTTP client used by remaining first-party code

Note that various systems may contain
`specialized instructions for installing Pillow`_.

The admin dashboard:

.. image:: img/dashboard.png
   :alt: Nova / Mezzanine admin dashboard


Browser Support
===============

The admin interface works with current Chrome, Safari, Firefox, and
Microsoft Edge. Internet Explorer and Edge < 79 are unsupported.


Extending
=========

Extension is ordinary Django: subclass ``Page`` or ``Displayable``,
drop in a ``page_processors.py``, install another Django app. There
is no plugin marketplace and no theme store. Cartridge (the old
Mezzanine shop) is not part of this product.


.. _`Python`: http://python.org/
.. _`Django`: https://www.djangoproject.com/
.. _`django-contrib-comments`: https://pypi.org/project/django-contrib-comments/
.. _`bleach`: https://pypi.org/project/bleach/
.. _`BeautifulSoup`: http://www.crummy.com/software/BeautifulSoup/
.. _`pytz`: https://pypi.org/project/pytz/
.. _`tzlocal`: https://pypi.org/project/tzlocal/
.. _`django-compressor`: https://pypi.org/project/django_compressor/
.. _`Python Imaging Library`: http://www.pythonware.com/products/pil/
.. _`Pillow`: https://github.com/python-pillow/Pillow
.. _`grappelli-safe`: https://github.com/stephenmcd/grappelli-safe
.. _`filebrowser-safe`: https://github.com/stephenmcd/filebrowser-safe
.. _`Grappelli`: https://github.com/sehmaschine/django-grappelli
.. _`FileBrowser`: https://github.com/sehmaschine/django-filebrowser
.. _`requests`: https://docs.python-requests.org/en/latest/
.. _`chardet`: https://chardet.readthedocs.io
.. _`specialized instructions for installing Pillow`: https://pillow.readthedocs.io/en/latest/installation.html
.. _`django-modeltranslation`: https://django-modeltranslation.readthedocs.io
