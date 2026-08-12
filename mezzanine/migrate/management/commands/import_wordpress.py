"""Adult WordPress WXR importer (PR-035)."""

from __future__ import annotations

import mimetypes
import re
from collections import defaultdict
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from pathlib import Path
from time import mktime, timezone
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
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
_THUMBNAIL_KEYS = ("_thumbnail_id", "thumbnail_id")
_ATTACHMENT_FETCH_TIMEOUT = 20


class Command(BaseImporterCommand):
    """
    Import a WordPress Extended RSS (WXR) file or URL.

    Maps posts → BlogPost (when blog is installed), pages → RichTextPage
    with parent tree, old URLs → Redirect, and Yoast title/description
    into MetaData fields. HTML stays in ``content``.

    Attachments are not a Media model (Y1.5): when an attachment is the
    featured image of a post (``_thumbnail_id`` or sole attached child),
    bytes are stored on ``BlogPost.featured_image``.
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
        parser.add_argument(
            "--skip-attachments",
            action="store_true",
            dest="skip_attachments",
            help="Do not download attachment bytes for featured images.",
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

    @staticmethod
    def _coerce_id(value):
        if value in (None, "", 0, "0"):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return value

    def _fetch_attachment_bytes(self, att_url: str) -> tuple[str, bytes] | None:
        """
        Load attachment bytes from a local path or HTTP(S) URL.

        Returns ``(filename, content)`` or None on failure.
        """
        if not att_url:
            return None
        parsed = urlparse(att_url)
        name = Path(parsed.path or att_url).name or "attachment.bin"
        # Local filesystem: absolute, cwd-relative, or next to the WXR file.
        candidates = []
        if parsed.scheme in ("", "file"):
            raw = parsed.path if parsed.scheme == "file" else att_url
            candidates.append(Path(raw))
            if not Path(raw).is_absolute():
                base = getattr(self, "_wxr_dir", None)
                if base is not None:
                    candidates.append(Path(base) / raw)
                candidates.append(Path.cwd() / raw)
        else:
            candidates.append(Path(att_url))
        for path in candidates:
            try:
                if path.is_file():
                    return name, path.read_bytes()
            except OSError:
                continue
        if parsed.scheme in ("http", "https"):
            try:
                req = Request(att_url, headers={"User-Agent": "nova-cms-import/1.0"})
                with urlopen(req, timeout=_ATTACHMENT_FETCH_TIMEOUT) as resp:
                    data = resp.read()
                    ctype = resp.headers.get("Content-Type", "")
                    if not Path(name).suffix and ctype:
                        ext = mimetypes.guess_extension(ctype.split(";")[0].strip())
                        if ext:
                            name = name + ext
                    return name, data
            except (URLError, OSError, ValueError) as exc:
                self.report.note_attachment_failure(
                    "download failed for %s: %s" % (att_url, exc)
                )
                return None
        self.report.note_attachment_failure(
            "unsupported attachment URL: %s" % att_url
        )
        return None

    def handle_import(self, options):
        url = options.get("url")
        if url is None:
            raise CommandError("Usage is import_wordpress --url=<path-or-url>")
        skip_attachments = bool(options.get("skip_attachments"))
        # Local paths must exist; feedparser also accepts file:// and http(s).
        path = Path(url)
        self._wxr_dir = Path.cwd()
        if path.exists():
            resolved = path.resolve()
            url = str(resolved)
            self._wxr_dir = resolved.parent
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

        # Pass 1: index attachments and post→thumbnail meta before creating rows.
        attachments: dict = {}  # att_id -> {url, parent_id, title}
        post_thumbnails: dict = {}  # post_wp_id -> att_id
        children: dict = defaultdict(list)  # parent_wp_id -> [att_id, ...]

        for i, entry in enumerate(feed["entries"]):
            xmlitem = xmlitems[i] if i < len(xmlitems) else None
            meta = self._postmeta(xmlitem) if xmlitem is not None else {}
            post_type = getattr(entry, "wp_post_type", None) or "post"
            wp_id = self._coerce_id(getattr(entry, "wp_post_id", None))
            parent_id = self._coerce_id(getattr(entry, "wp_post_parent", None))
            old_url = entry.get("link") or entry.get("id")

            if post_type == "attachment":
                att_url = getattr(entry, "wp_attachment_url", None) or old_url
                if wp_id is not None:
                    attachments[wp_id] = {
                        "url": att_url,
                        "parent_id": parent_id,
                        "title": entry.title,
                    }
                    if parent_id is not None:
                        children[parent_id].append(wp_id)
                else:
                    self.report.note_attachment_failure(
                        "attachment without wp:post_id: %s" % att_url
                    )
            elif post_type == "post" and wp_id is not None:
                for key in _THUMBNAIL_KEYS:
                    if meta.get(key):
                        post_thumbnails[wp_id] = self._coerce_id(meta[key])
                        break

        def featured_for_post(wp_id):
            if skip_attachments or wp_id is None:
                return None
            att_id = post_thumbnails.get(wp_id)
            if att_id is None:
                kids = children.get(wp_id) or []
                if len(kids) == 1:
                    att_id = kids[0]
            if att_id is None:
                return None
            att = attachments.get(att_id)
            if not att:
                self.report.note_attachment_failure(
                    "thumbnail id %s missing for post %s" % (att_id, wp_id)
                )
                return None
            fetched = self._fetch_attachment_bytes(att["url"])
            if not fetched:
                return None
            name, content = fetched
            return {"name": name, "content": content}

        # Pass 2: create posts/pages/comments; map featured images onto posts.
        used_attachment_ids = set()
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
            wp_id = self._coerce_id(getattr(entry, "wp_post_id", None))

            if post_type == "post":
                featured = featured_for_post(wp_id)
                if featured:
                    # Track which attachment ids were consumed as featured images.
                    att_id = post_thumbnails.get(wp_id)
                    if att_id is None:
                        kids = children.get(wp_id) or []
                        if len(kids) == 1:
                            att_id = kids[0]
                    if att_id is not None:
                        used_attachment_ids.add(att_id)
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
                    featured_image=featured,
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
                parent_id = self._coerce_id(getattr(entry, "wp_post_parent", None))
                self.add_page(
                    title=entry.title,
                    content=content,
                    tags=terms.get("tag") or set(),
                    old_id=wp_id,
                    old_parent_id=parent_id,
                    old_url=old_url,
                    status=status,
                    meta_title=yoast_title,
                    meta_description=yoast_desc,
                )

            elif post_type == "attachment":
                # Reported after posts so featured-image success is not noise.
                continue

            else:
                self.report.note_unmapped(str(post_type))

        # Residual attachments → Media library (PR-026 SiteRelated), not
        # featured on a post.
        for att_id, att in attachments.items():
            if att_id in used_attachment_ids:
                continue
            if skip_attachments:
                self.report.skipped.append(
                    "attachment skipped (--skip-attachments): %s" % att["url"]
                )
                continue
            fetched = self._fetch_attachment_bytes(att["url"])
            if not fetched:
                continue
            name, content = fetched
            try:
                from django.core.files.base import ContentFile

                from mezzanine.core.models import Media

                media = Media(
                    title=att.get("title") or name,
                    alt=att.get("title") or name,
                )
                media.file.save(name, ContentFile(content), save=False)
                media.save()
                self.report.attachments_imported += 1
            except Exception as exc:  # noqa: BLE001
                self.report.note_attachment_failure(
                    "media library import failed for %s: %s" % (att["url"], exc)
                )

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
