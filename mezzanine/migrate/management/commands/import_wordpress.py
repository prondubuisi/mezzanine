"""Adult WordPress WXR importer (PR-035)."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from pathlib import Path
from time import mktime, timezone
from xml.dom import Node
from xml.dom.minidom import parse

from django.core.management.base import CommandError
from django.utils import timezone as django_timezone
from django.utils.html import linebreaks

from mezzanine.core.models import CONTENT_STATUS_DRAFT, CONTENT_STATUS_PUBLISHED
from mezzanine.migrate.base import BaseImporterCommand

# Yoast SEO postmeta keys commonly present in WXR exports.
_YOAST_TITLE_KEYS = (
    "_yoast_wpseo_title",
    "yoast_wpseo_title",
)
_YOAST_DESC_KEYS = (
    "_yoast_wpseo_metadesc",
    "yoast_wpseo_metadesc",
)


class Command(BaseImporterCommand):
    """
    Import a WordPress Extended RSS (WXR) file or URL.

    Maps posts → BlogPost (when blog is installed), pages → RichTextPage
    with parent tree, old URLs → Redirect, and Yoast title/description
    into MetaData fields. HTML stays in ``content``.
    """

    help = "Import a WordPress WXR export (posts, pages, redirects, Yoast meta)."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "-u",
            "--url",
            dest="url",
            help="Path or URL to a WXR export file",
        )

    def get_text(self, xml, name):
        nodes = xml.getElementsByTagName("wp:comment_" + name)[0].childNodes
        accepted_types = [Node.CDATA_SECTION_NODE, Node.TEXT_NODE]
        return "".join(n.data for n in nodes if n.nodeType in accepted_types)

    def _postmeta(self, xmlitem) -> dict[str, str]:
        meta = {}
        for node in xmlitem.getElementsByTagName("wp:postmeta"):
            keys = node.getElementsByTagName("wp:meta_key")
            vals = node.getElementsByTagName("wp:meta_value")
            if not keys or not vals:
                continue
            key = self._node_text(keys[0])
            val = self._node_text(vals[0])
            if key:
                meta[key] = val
        return meta

    @staticmethod
    def _node_text(node) -> str:
        accepted = (Node.CDATA_SECTION_NODE, Node.TEXT_NODE)
        return "".join(n.data for n in node.childNodes if n.nodeType in accepted)

    def _yoast(self, meta: dict[str, str]) -> tuple[str | None, str | None]:
        title = None
        desc = None
        for key in _YOAST_TITLE_KEYS:
            if meta.get(key):
                title = meta[key]
                break
        for key in _YOAST_DESC_KEYS:
            if meta.get(key):
                desc = meta[key]
                break
        return title, desc

    def _wp_status(self, entry) -> int:
        raw = getattr(entry, "wp_status", None) or getattr(entry, "status", "publish")
        raw = str(raw).lower()
        if raw in ("publish", "public"):
            return CONTENT_STATUS_PUBLISHED
        return CONTENT_STATUS_DRAFT

    def handle_import(self, options):
        url = options.get("url")
        if url is None:
            raise CommandError("Usage is import_wordpress --url=<path-or-url>")
        # Local paths must exist; feedparser also accepts file:// and http(s).
        path = Path(url)
        if path.exists():
            url = str(path.resolve())
        try:
            import feedparser
        except ImportError as exc:
            raise CommandError(
                "feedparser is required for import_wordpress. "
                "Install with: pip install 'nova-cms[migrate]'"
            ) from exc

        feed = feedparser.parse(url)
        if getattr(feed, "bozo", False) and not feed.get("entries"):
            raise CommandError(
                "Could not parse WXR from %s: %s"
                % (url, getattr(feed, "bozo_exception", "unknown error"))
            )

        xml = parse(url)
        xmlitems = xml.getElementsByTagName("item")
        if len(xmlitems) != len(feed.get("entries", [])):
            # Prefer feedparser length; minidom may include extra nodes.
            pass

        for i, entry in enumerate(feed["entries"]):
            xmlitem = xmlitems[i] if i < len(xmlitems) else None
            content_value = ""
            if getattr(entry, "content", None):
                content_value = entry.content[0].get("value", "")
            elif getattr(entry, "summary", None):
                content_value = entry.summary
            content = linebreaks(self.wp_caption(content_value))

            pub_date = getattr(entry, "published_parsed", None) or getattr(
                entry, "updated_parsed", None
            )
            if pub_date:
                pub_date = datetime.fromtimestamp(mktime(pub_date))
                pub_date -= timedelta(seconds=timezone)
                if django_timezone.is_naive(pub_date):
                    pub_date = django_timezone.make_aware(pub_date, dt_timezone.utc)

            terms = defaultdict(set)
            for item in getattr(entry, "tags", []):
                scheme = item.get("scheme") if isinstance(item, dict) else item.scheme
                term = item.get("term") if isinstance(item, dict) else item.term
                terms[scheme].add(term)

            meta = self._postmeta(xmlitem) if xmlitem is not None else {}
            yoast_title, yoast_desc = self._yoast(meta)
            status = self._wp_status(entry)
            post_type = getattr(entry, "wp_post_type", None) or "post"
            old_url = entry.get("link") or entry.get("id")

            if post_type == "post":
                post = self.add_post(
                    title=entry.title,
                    content=content,
                    pub_date=pub_date,
                    tags=terms.get("tag") or terms.get(None) or set(),
                    categories=terms.get("category") or set(),
                    old_url=old_url,
                    status=status,
                    meta_title=yoast_title,
                    meta_description=yoast_desc,
                )
                if xmlitem is not None:
                    for c in xmlitem.getElementsByTagName("wp:comment"):
                        try:
                            name = self.get_text(c, "author")
                            email = self.get_text(c, "author_email")
                            website = self.get_text(c, "author_url")
                            body = self.get_text(c, "content")
                            c_date = self.get_text(c, "date_gmt")
                            fmt = "%Y-%m-%d %H:%M:%S"
                            c_pub = datetime.strptime(c_date, fmt)
                            c_pub -= timedelta(seconds=timezone)
                            if django_timezone.is_naive(c_pub):
                                c_pub = django_timezone.make_aware(
                                    c_pub, dt_timezone.utc
                                )
                        except (IndexError, ValueError):
                            self.report.skipped.append(
                                "malformed comment on post %r" % entry.title
                            )
                            continue
                        self.add_comment(
                            post=post,
                            name=name,
                            email=email,
                            body=body,
                            website=website,
                            pub_date=c_pub,
                        )

            elif post_type == "page":
                old_id = getattr(entry, "wp_post_id", None)
                parent_id = getattr(entry, "wp_post_parent", None) or None
                if parent_id in (0, "0"):
                    parent_id = None
                self.add_page(
                    title=entry.title,
                    content=content,
                    tags=terms.get("tag") or set(),
                    old_id=old_id,
                    old_parent_id=parent_id,
                    old_url=old_url,
                    status=status,
                    meta_title=yoast_title,
                    meta_description=yoast_desc,
                )

            elif post_type == "attachment":
                # Attachments stay FileField until Media-as-Displayable (Y1.5).
                att_url = getattr(entry, "wp_attachment_url", None) or old_url
                self.report.note_attachment_failure(
                    "attachment not imported (no Media model in Y1): %s" % att_url
                )

            else:
                self.report.note_unmapped(str(post_type))

    def wp_caption(self, post):
        for match in re.finditer(r"\[caption (.*?)\](.*?)\[/caption\]", post):
            meta = "<div "
            caption = ""
            for imatch in re.finditer(r'(\w+)="(.*?)"', match.group(1)):
                if imatch.group(1) == "id":
                    meta += 'id="%s" ' % imatch.group(2)
                if imatch.group(1) == "align":
                    meta += 'class="wp-caption %s" ' % imatch.group(2)
                if imatch.group(1) == "width":
                    width = int(imatch.group(2)) + 10
                    meta += 'style="width: %spx;" ' % width
                if imatch.group(1) == "caption":
                    caption = imatch.group(2)
            parts = (match.group(2), caption)
            meta += '>%s<p class="wp-caption-text">%s</p></div>' % parts
            post = post.replace(match.group(0), meta)
        return post
