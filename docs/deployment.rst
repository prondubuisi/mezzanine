==========
Deployment
==========

Deployment of a Mezzanine site to production is mostly identical to
deploying a regular Django site. For serving static content, Mezzanine
makes full use of Django's ``staticfiles`` app. For more information,
see the Django docs for
`deployment <https://docs.djangoproject.com/en/dev/howto/deployment/>`_ and
`staticfiles <https://docs.djangoproject.com/en/dev/howto/static-files/>`_.

Mezzanine's only customization to the deployment process is adding built-in
support for a ``local_settings.py`` file. This file is not kept under version
control and you can use it to include production-only configuration.
Setting ``DEBUG = False`` there enables secure cookies, HSTS, and
``SECURE_SSL_REDIRECT`` via Django's ``SecurityMiddleware``. Do not put
``SSLRedirectMiddleware`` in ``MIDDLEWARE``; that class has been removed.

.. versionchanged:: 5.0
   Previously Mezzanine used to ship a fabfile for automatic deployments. It
   has been removed in favor of regular Django deployment methods.
