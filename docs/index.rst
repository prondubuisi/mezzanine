====
Nova
====

Welcome to Nova, a publishing kernel descended from Mezzanine.
Install ``nova-cms`` and ``import mezzanine``. To learn what still
ships and how to install it, read the :doc:`overview`.

.. note::
    A working knowledge of `Django <https://www.djangoproject.com/>`_
    is required. The documentation assumes as much. If you're new to
    Django, work through the
    :doc:`Django tutorial <django:intro/tutorial01>`
    first. Import paths remain ``mezzanine.*``. *A mantra carried
    forward from Mezzanine: this is just Django* —
    `Ken Bolton <http://bscientific.org/>`_.

**Front-end developers** might be interested in in-place editing of
content while viewing a page. See :doc:`inline-editing`.

**Back-end developers** can get a technical overview of how content is
managed, and how to customize it, from :doc:`content-architecture`
(the main components, and how to add your own types) and
:doc:`model-customization` for lower-level work. There is also
:doc:`admin-customization` and a :doc:`model-graph`.

**System administrators** can find production notes in
:doc:`deployment` and :doc:`caching-strategy`.

**Further reading** includes :doc:`frequently-asked-questions`,
:doc:`utilities`, :doc:`user-accounts`, :doc:`multi-lingual-sites`,
:doc:`search-engine`, and :doc:`configuration`. You can also
:doc:`blog-importing` (WordPress and RSS), or browse the
auto-generated docs for each of the :doc:`packages` under
``mezzanine.*``.

Table Of Contents
=================

.. toctree::
    :maxdepth: 2

    overview
    content-architecture
    model-customization
    admin-customization
    multi-lingual-sites
    utilities
    model-graph
    inline-editing
    caching-strategy
    multi-tenancy
    deployment
    frequently-asked-questions
    user-accounts
    search-engine
    configuration
    blog-importing
    twitter-integration
    packages
    colophon
