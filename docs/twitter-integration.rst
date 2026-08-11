===================
Twitter Integration
===================

``mezzanine.twitter`` has been **removed**. It targeted the retired
Twitter API 1.1, was deprecated since Mezzanine 5.0, and is no longer
importable.

Do not add ``mezzanine.twitter`` to ``INSTALLED_APPS``. The
``poll_twitter`` command, ``TweetableAdminMixin``, Twitter template
tags, and ``TWITTER_*`` settings are gone.

Leftover tables
===============

If an existing site still has Twitter tables, drop them after removing
the app from ``INSTALLED_APPS``::

    DROP TABLE IF EXISTS twitter_tweet;
    DROP TABLE IF EXISTS twitter_query;

OAuth material is burned
========================

``mezzanine/twitter/models.py`` shipped hard-coded fallback OAuth
consumer and access tokens used when no ``TWITTER_*`` settings were
configured. Treat those credentials as **burned**. They remain in git
history on purpose: this fork will **not** rewrite history with
``git filter-repo`` (that would change every SHA and every downstream
clone). The keys are no longer present in the working tree.

