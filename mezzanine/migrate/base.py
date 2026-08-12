"""Base importer command (moved from mezzanine.blog.management.base)."""

from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.contrib.redirects.models import Redirect
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand, CommandError
from django.utils.encoding import force_str
from django.utils.html import strip_tags

from mezzanine.conf import settings
from mezzanine.core.models import CONTENT_STATUS_DRAFT, CONTENT_STATUS_PUBLISHED
from mezzanine.generic.models import Keyword, ThreadedComment
from mezzanine.migrate.report import MigrationReport
from mezzanine.pages.models import RichTextPage
from mezzanine.utils.html import decode_entities

User = get_user_model()


class BaseImporterCommand(BaseCommand):
    """
    Base importer for blogging-platform management commands.

    Subclasses override ``handle_import`` and call ``add_post`` /
    ``add_page`` / ``add_comment``.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "-m",
            "--mezzanine-user",
            dest="mezzanine_user",
            help="Username to assign imported blog posts to.",
        )
        parser.add_argument(
            "--noinput",
            action="store_false",
            dest="interactive",
            help="Do NOT prompt for input of any kind. "
            "Fields will be truncated if too long.",
        )
        parser.add_argument(
            "-n",
            "--navigation",
            action="store_true",
            dest="in_navigation",
            help="Add any imported pages to navigation",
        )
        parser.add_argument(
            "-f",
            "--footer",
            action="store_true",
            dest="in_footer",
            help="Add any imported pages to footer navigation",
        )

    def __init__(self, **kwargs):
        self.posts = []
        self.pages = []
        self.report = MigrationReport()
        super().__init__(**kwargs)

    def add_post(
        self,
        title=None,
        content=None,
        old_url=None,
        pub_date=None,
        tags=None,
        categories=None,
        comments=None,
        status=None,
        meta_title=None,
        meta_description=None,
    ):
        if not title:
            title = strip_tags(content).split(". ")[0]
        title = decode_entities(title)
        if categories is None:
            categories = []
        if tags is None:
            tags = []
        if comments is None:
            comments = []
        if status is None:
            status = (
                CONTENT_STATUS_DRAFT
                if pub_date is None
                else CONTENT_STATUS_PUBLISHED
            )
        self.posts.append(
            {
                "title": force_str(title),
                "publish_date": pub_date,
                "content": force_str(content),
                "categories": categories,
                "tags": tags,
                "comments": comments,
                "old_url": old_url,
                "status": status,
                "meta_title": meta_title,
                "meta_description": meta_description,
            }
        )
        return self.posts[-1]

    def add_page(
        self,
        title=None,
        content=None,
        old_url=None,
        tags=None,
        old_id=None,
        old_parent_id=None,
        status=None,
        meta_title=None,
        meta_description=None,
    ):
        if not title:
            text = decode_entities(strip_tags(content)).replace("\n", " ")
            title = text.split(". ")[0]
        if tags is None:
            tags = []
        if status is None:
            status = CONTENT_STATUS_PUBLISHED
        self.pages.append(
            {
                "title": title,
                "content": content,
                "tags": tags,
                "old_url": old_url,
                "old_id": old_id,
                "old_parent_id": old_parent_id,
                "status": status,
                "meta_title": meta_title,
                "meta_description": meta_description,
            }
        )

    def add_comment(
        self, post=None, name=None, email=None, pub_date=None, website=None, body=None
    ):
        if post is None:
            if not self.posts:
                raise CommandError("Cannot add comments without posts")
            post = self.posts[-1]
        post["comments"].append(
            {
                "user_name": name,
                "user_email": email,
                "submit_date": pub_date,
                "user_url": website,
                "comment": body,
            }
        )

    def trunc(self, model, prompt, **fields):
        for field_name, value in fields.items():
            field = model._meta.get_field(field_name)
            max_length = getattr(field, "max_length", None)
            if not max_length:
                continue
            elif not prompt:
                fields[field_name] = value[:max_length]
                continue
            while len(value) > max_length:
                encoded_value = value.encode("utf-8")
                new_value = input(
                    "The value for the field %s.%s exceeds "
                    "its maximum length of %s chars: %s\n\nEnter a new value "
                    "for it, or press return to have it truncated: "
                    % (model.__name__, field_name, max_length, encoded_value)
                )
                value = new_value if new_value else value[:max_length]
            fields[field_name] = value
        return fields

    def handle(self, *args, **options):
        mezzanine_user = options.get("mezzanine_user")
        site = Site.objects.get_current()
        verbosity = int(options.get("verbosity", 1))
        prompt = options.get("interactive")

        if mezzanine_user is None:
            raise CommandError("No Mezzanine user has been specified")
        try:
            mezzanine_user = User.objects.get(username=mezzanine_user)
        except User.DoesNotExist:
            raise CommandError("Invalid Mezzanine user: %s" % mezzanine_user)

        self.report = MigrationReport()
        self.handle_import(options)

        blog_installed = "mezzanine.blog" in settings.INSTALLED_APPS
        if self.posts and not blog_installed:
            self.report.skipped.append(
                "%d posts skipped (mezzanine.blog not installed)" % len(self.posts)
            )
            self.posts = []

        if blog_installed:
            from mezzanine.blog.models import BlogCategory, BlogPost

            for post_data in self.posts:
                categories = post_data.pop("categories")
                tags = post_data.pop("tags")
                comments = post_data.pop("comments")
                old_url = post_data.pop("old_url")
                meta_title = post_data.pop("meta_title", None)
                meta_description = post_data.pop("meta_description", None)
                post_data = self.trunc(BlogPost, prompt, **post_data)
                initial = {
                    "title": post_data.pop("title"),
                    "user": mezzanine_user,
                }
                post, created = BlogPost.objects.get_or_create(**initial)
                for k, v in post_data.items():
                    setattr(post, k, v)
                if meta_title:
                    post._meta_title = meta_title
                    post.gen_description = False
                if meta_description:
                    post.description = meta_description
                    post.gen_description = False
                post.save()
                if created:
                    self.report.posts_imported += 1
                    if verbosity >= 1:
                        print("Imported post: %s" % post)
                for name in categories:
                    cat = self.trunc(BlogCategory, prompt, title=name)
                    if not cat["title"]:
                        continue
                    cat, cat_created = BlogCategory.objects.get_or_create(**cat)
                    if cat_created and verbosity >= 1:
                        print("Imported category: %s" % cat)
                    post.categories.add(cat)
                for comment in comments:
                    comment = self.trunc(ThreadedComment, prompt, **comment)
                    comment["site"] = site
                    post.comments.create(**comment)
                    self.report.comments_imported += 1
                    if verbosity >= 1:
                        print("Imported comment by: %s" % comment["user_name"])
                self.add_meta(post, tags, prompt, verbosity, old_url)

        in_menus = []
        footer = [
            menu[0]
            for menu in settings.PAGE_MENU_TEMPLATES
            if menu[-1] == "pages/menus/footer.html"
        ]
        if options["in_navigation"]:
            in_menus = [menu[0] for menu in settings.PAGE_MENU_TEMPLATES]
            if footer and not options["in_footer"]:
                in_menus.remove(footer[0])
        elif footer and options["in_footer"]:
            in_menus = footer
        parents = []
        for page in self.pages:
            tags = page.pop("tags")
            old_url = page.pop("old_url")
            old_id = page.pop("old_id")
            old_parent_id = page.pop("old_parent_id")
            meta_title = page.pop("meta_title", None)
            meta_description = page.pop("meta_description", None)
            status = page.pop("status", CONTENT_STATUS_PUBLISHED)
            page = self.trunc(RichTextPage, prompt, **page)
            page["status"] = status
            page["in_menus"] = in_menus
            if meta_title:
                page["_meta_title"] = meta_title
                page["gen_description"] = False
            if meta_description:
                page["description"] = meta_description
                page["gen_description"] = False
            obj, created = RichTextPage.objects.get_or_create(**page)
            if created:
                self.report.pages_imported += 1
                if verbosity >= 1:
                    print("Imported page: %s" % obj)
            self.add_meta(obj, tags, prompt, verbosity, old_url)
            parents.append(
                {
                    "old_id": old_id,
                    "old_parent_id": old_parent_id,
                    "page": obj,
                }
            )

        for obj in parents:
            if obj["old_parent_id"]:
                for parent in parents:
                    if parent["old_id"] == obj["old_parent_id"]:
                        obj["page"].parent = parent["page"]
                        obj["page"].save()
                        break

        if verbosity >= 1:
            print(self.report.render())

    def add_meta(self, obj, tags, prompt, verbosity, old_url=None):
        for tag in tags:
            keyword = self.trunc(Keyword, prompt, title=tag)
            keyword, created = Keyword.objects.get_or_create_iexact(**keyword)
            obj.keywords.create(keyword=keyword)
            if created and verbosity >= 1:
                print("Imported tag: %s" % keyword)
        if old_url is not None:
            old_path = urlparse(old_url).path
            if not old_path.strip("/"):
                return
            redirect = self.trunc(Redirect, prompt, old_path=old_path)
            redirect["site"] = Site.objects.get_current()
            redirect, created = Redirect.objects.get_or_create(**redirect)
            redirect.new_path = obj.get_absolute_url()
            redirect.save()
            self.report.note_redirect(old_url, redirect.new_path)
            if created and verbosity >= 1:
                print("Created redirect for: %s" % old_url)

    def handle_import(self, options):
        raise NotImplementedError
