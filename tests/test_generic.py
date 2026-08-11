from unittest import skipUnless
from unittest.mock import patch

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.template import Context, Template
from django.test.utils import override_settings
from django.urls import reverse

from mezzanine.blog.models import BlogPost
from mezzanine.conf import settings
from mezzanine.core.models import CONTENT_STATUS_PUBLISHED
from mezzanine.generic.forms import KeywordsWidget, RatingForm
from mezzanine.generic.models import AssignedKeyword, Keyword, ThreadedComment
from mezzanine.generic.views import comment
from mezzanine.pages.models import RichTextPage
from mezzanine.utils.tests import TestCase
from mezzanine.utils.views import is_spam_akismet


class _AkismetForm(forms.Form):
    """Minimal form with the fields ``is_spam_akismet`` extracts."""

    name = forms.CharField(label="Name")
    email = forms.EmailField()
    url = forms.URLField(required=False)
    comment = forms.CharField(widget=forms.Textarea)


class GenericTests(TestCase):
    @skipUnless("mezzanine.blog" in settings.INSTALLED_APPS, "blog app required")
    def test_rating(self):
        """
        Test that ratings can be posted and avarage/count are calculated.
        """
        blog_post = BlogPost.objects.create(
            title="Ratings", user=self._user, status=CONTENT_STATUS_PUBLISHED
        )
        if settings.RATINGS_ACCOUNT_REQUIRED:
            self.client.login(username=self._username, password=self._password)
        data = RatingForm(None, blog_post).initial
        for value in settings.RATINGS_RANGE:
            data["value"] = value
            response = self.client.post(reverse("rating"), data=data)
            response.delete_cookie("mezzanine-rating")
        blog_post = BlogPost.objects.get(id=blog_post.id)
        count = len(settings.RATINGS_RANGE)
        _sum = sum(settings.RATINGS_RANGE)
        average = _sum / count
        if settings.RATINGS_ACCOUNT_REQUIRED:
            self.assertEqual(blog_post.rating_count, 1)
            self.assertEqual(blog_post.rating_sum, settings.RATINGS_RANGE[-1])
            self.assertEqual(blog_post.rating_average, settings.RATINGS_RANGE[-1] / 1)
        else:
            self.assertEqual(blog_post.rating_count, count)
            self.assertEqual(blog_post.rating_sum, _sum)
            self.assertEqual(blog_post.rating_average, average)

    @skipUnless("mezzanine.blog" in settings.INSTALLED_APPS, "blog app required")
    def test_comment_ratings(self):
        """
        Test that a generic relation defined on one of Mezzanine's generic
        models (in this case ratings of comments) correctly sets its
        extra fields.
        """
        blog_post = BlogPost.objects.create(title="Post with comments", user=self._user)
        content_type = ContentType.objects.get_for_model(blog_post)
        kwargs = {
            "content_type": content_type,
            "object_pk": blog_post.id,
            "site_id": settings.SITE_ID,
            "comment": "First!!!11",
        }
        comment = ThreadedComment.objects.create(**kwargs)
        comment.rating.create(value=settings.RATINGS_RANGE[0])
        comment.rating.create(value=settings.RATINGS_RANGE[-1])
        comment = ThreadedComment.objects.get(pk=comment.pk)

        self.assertEqual(len(comment.rating.all()), comment.rating_count)

        self.assertEqual(
            comment.rating_average,
            (settings.RATINGS_RANGE[0] + settings.RATINGS_RANGE[-1]) / 2,
        )

    @skipUnless("mezzanine.blog" in settings.INSTALLED_APPS, "blog app required")
    def test_comment_queries(self):
        """
        Test that rendering comments executes the same number of
        queries, regardless of the number of nested replies.
        """
        blog_post = BlogPost.objects.create(title="Post", user=self._user)
        content_type = ContentType.objects.get_for_model(blog_post)
        kwargs = {
            "content_type": content_type,
            "object_pk": blog_post.id,
            "site_id": settings.SITE_ID,
        }
        template = "{% load comment_tags %}{% comment_thread blog_post %}"
        context = {
            "blog_post": blog_post,
            "posted_comment_form": None,
            "unposted_comment_form": None,
        }
        if settings.COMMENTS_ACCOUNT_REQUIRED:
            self.queries_used_for_template(template, **context)
        before = self.queries_used_for_template(template, **context)
        self.assertTrue(before > 0)
        self.create_recursive_objects(ThreadedComment, "replied_to", **kwargs)
        after = self.queries_used_for_template(template, **context)
        self.assertEqual(before, after)

    @skipUnless("mezzanine.pages" in settings.INSTALLED_APPS, "pages app required")
    def test_keywords(self):
        """
        Test that the keywords_string field is correctly populated.
        """
        page = RichTextPage.objects.create(title="test keywords")
        keywords = {"how", "now", "brown", "cow"}
        Keyword.objects.all().delete()
        for keyword in keywords:
            keyword_id = Keyword.objects.get_or_create(title=keyword)[0].id
            page.keywords.get_or_create(keyword_id=keyword_id)
        page = RichTextPage.objects.get(id=page.id)
        self.assertEqual(keywords, set(page.keywords_string.split()))
        # Test removal.
        first = Keyword.objects.all()[0]
        keywords.remove(first.title)
        first.delete()
        page = RichTextPage.objects.get(id=page.id)
        self.assertEqual(keywords, set(page.keywords_string.split()))
        page.delete()

    def test_delete_unused(self):
        """
        Only ``Keyword`` instances without any assignments should be deleted.
        """
        assigned_keyword = Keyword.objects.create(title="assigned")
        Keyword.objects.create(title="unassigned")
        AssignedKeyword.objects.create(
            keyword_id=assigned_keyword.id, content_object=RichTextPage(pk=1)
        )
        Keyword.objects.delete_unused(keyword_ids=[assigned_keyword.id])
        self.assertEqual(Keyword.objects.count(), 2)
        Keyword.objects.delete_unused()
        self.assertEqual(Keyword.objects.count(), 1)
        self.assertEqual(Keyword.objects.all()[0].id, assigned_keyword.id)

    def test_comment_form_returns_400_when_missing_data(self):
        """
        Assert 400 status code response when expected data is missing from
        the comment form. This simulates typical malicious bot behavior.
        """
        request = self._request_factory.post(reverse("comment"))
        if settings.COMMENTS_ACCOUNT_REQUIRED:
            request.user = self._user
            request.session = {}
        response = comment(request)
        self.assertEqual(response.status_code, 400)

    def test_multiple_comment_forms(self):

        template = Template(
            """
            {% load comment_tags %}
            {% comments_for post1 %}
            {% comments_for post2 %}
        """
        )

        request = self._request_factory.get(reverse("comment"))
        request.user = self._user

        context = {
            "post1": BlogPost.objects.create(title="Post #1", user=self._user),
            "post2": BlogPost.objects.create(title="Post #2", user=self._user),
            "request": request,
        }

        result = template.render(Context(context))

        self.assertInHTML(
            '<input id="id_object_pk" name="object_pk" '
            'type="hidden" value="%d" />' % context["post2"].pk,
            result,
        )

    def test_keywords_widget(self):
        """
        Test that Keywords widget is returning proper value
        for form rendering and its support for different data types.
        """

        keyword_widget = KeywordsWidget()

        keywords = {"how", "now", "brown"}
        Keyword.objects.all().delete()
        keyword_id_list = []
        for keyword in keywords:
            keyword_id = Keyword.objects.get_or_create(title=keyword)[0].id
            keyword_id_list.append(keyword_id)

        keyword_id_string = ",".join(map(str, keyword_id_list))
        values_from_string = keyword_widget.decompress(keyword_id_string)

        self.assertIn("how", values_from_string[1])
        self.assertIn("now", values_from_string[1])
        self.assertIn("brown", values_from_string[1])

        for keyword_id in keyword_id_list:
            AssignedKeyword.objects.create(
                keyword_id=keyword_id, content_object=RichTextPage(pk=1)
            )

        assigned_keywords = AssignedKeyword.objects.all()
        values_from_relation = keyword_widget.decompress(assigned_keywords)

        self.assertIn("how", values_from_relation[1])
        self.assertIn("now", values_from_relation[1])
        self.assertIn("brown", values_from_relation[1])

        self.assertEqual(("", ""), keyword_widget.decompress(None))

    def test_comments_defaults_off(self):
        """
        Built-in comments are not auto-approved and require an account.
        """
        self.assertFalse(settings.COMMENTS_DEFAULT_APPROVED)
        self.assertTrue(settings.COMMENTS_ACCOUNT_REQUIRED)

    @skipUnless("mezzanine.blog" in settings.INSTALLED_APPS, "blog app required")
    def test_comments_not_auto_approved(self):
        """
        Newly saved comments stay unpublished until moderated.
        """
        blog_post = BlogPost.objects.create(
            title="Moderated comments",
            user=self._user,
            status=CONTENT_STATUS_PUBLISHED,
        )
        content_type = ContentType.objects.get_for_model(blog_post)
        saved = ThreadedComment.objects.create(
            content_type=content_type,
            object_pk=blog_post.id,
            site_id=settings.SITE_ID,
            comment="Please approve me",
        )
        saved.refresh_from_db()
        self.assertFalse(saved.is_public)

    @skipUnless("mezzanine.blog" in settings.INSTALLED_APPS, "blog app required")
    def test_comments_account_required_redirects_anonymous(self):
        """
        Anonymous comment posts are sent to login when accounts are required.
        """
        blog_post = BlogPost.objects.create(
            title="Login to comment",
            user=self._user,
            status=CONTENT_STATUS_PUBLISHED,
        )
        response = self.client.post(
            reverse("comment"),
            data={
                "content_type": "blog.blogpost",
                "object_pk": blog_post.pk,
                "comment": "anonymous spam",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(settings.LOGIN_URL, response["Location"])

    def _akismet_form(self):
        form = _AkismetForm(
            data={
                "name": "Alice",
                "email": "alice@example.com",
                "url": "https://example.com/",
                "comment": "Hello from a real person",
            }
        )
        self.assertTrue(form.is_valid())
        return form

    def test_is_spam_akismet_no_key_is_not_spam(self):
        """
        With no API key configured, Akismet is a no-op (not spam).
        """
        request = self._request_factory.post("/comment/", {"comment": "x"})
        request.META["REMOTE_ADDR"] = "127.0.0.1"
        with override_settings(AKISMET_API_KEY=""):
            self.assertFalse(is_spam_akismet(request, self._akismet_form(), "/post/"))

    @override_settings(AKISMET_API_KEY="testkey")
    @patch("mezzanine.utils.views.urlopen")
    def test_is_spam_akismet_uses_https(self, mock_urlopen):
        """
        The Akismet comment-check endpoint is requested over HTTPS.
        """
        mock_urlopen.return_value.read.return_value = b"false"
        request = self._request_factory.post(
            "/comment/", {"comment": "x", "referrer": "https://example.com/"}
        )
        request.META["REMOTE_ADDR"] = "127.0.0.1"
        request.META["HTTP_USER_AGENT"] = "test-agent"
        self.assertFalse(is_spam_akismet(request, self._akismet_form(), "/post/"))
        self.assertTrue(mock_urlopen.called)
        sent = mock_urlopen.call_args[0][0]
        self.assertTrue(sent.full_url.startswith("https://"))
        self.assertEqual(
            sent.full_url,
            "https://testkey.rest.akismet.com/1.1/comment-check",
        )

    @override_settings(AKISMET_API_KEY="testkey")
    @patch("mezzanine.utils.views.urlopen")
    def test_is_spam_akismet_fail_closed_on_error(self, mock_urlopen):
        """
        When a key is set and Akismet errors, treat the content as spam.
        """
        mock_urlopen.side_effect = OSError("akismet unavailable")
        request = self._request_factory.post("/comment/", {"comment": "x"})
        request.META["REMOTE_ADDR"] = "127.0.0.1"
        self.assertTrue(is_spam_akismet(request, self._akismet_form(), "/post/"))

    @override_settings(AKISMET_API_KEY="testkey")
    @patch("mezzanine.utils.views.urlopen")
    def test_is_spam_akismet_true_response_is_spam(self, mock_urlopen):
        mock_urlopen.return_value.read.return_value = b"true"
        request = self._request_factory.post("/comment/", {"comment": "x"})
        request.META["REMOTE_ADDR"] = "127.0.0.1"
        self.assertTrue(is_spam_akismet(request, self._akismet_form(), "/post/"))
