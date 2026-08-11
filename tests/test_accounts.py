from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.forms.fields import DateField, DateTimeField
from django.urls import reverse
from django.utils.http import int_to_base36

from mezzanine.accounts import ProfileNotConfigured
from mezzanine.accounts.forms import ProfileForm
from mezzanine.conf import settings
from mezzanine.utils.tests import TestCase

User = get_user_model()


class AccountsTests(TestCase):
    def account_data(self, test_value):
        """
        Returns a dict with test data for all the user/profile fields.
        """
        # User fields
        data = {"email": test_value + "@example.com"}
        for field in ("first_name", "last_name", "username", "password1", "password2"):
            if field.startswith("password"):
                value = "x" * settings.ACCOUNTS_MIN_PASSWORD_LENGTH
            else:
                value = test_value
            data[field] = value
        # Profile fields
        try:
            profile_form = ProfileForm()
            ProfileFieldsForm = profile_form.get_profile_fields_form()
            for name, field in ProfileFieldsForm().fields.items():
                if name != "id":
                    if hasattr(field, "choices"):
                        value = list(field.choices)[0][0]
                    elif isinstance(field, (DateField, DateTimeField)):
                        value = "9001-04-20"
                    else:
                        value = test_value
                    data[name] = value
        except ProfileNotConfigured:
            pass
        return data

    def test_account(self):
        """
        Test account creation.
        """
        # Verification not required - test an active user is created.
        data = self.account_data("test1")
        settings.ACCOUNTS_VERIFICATION_REQUIRED = False
        response = self.client.post(reverse("signup"), data, follow=True)
        self.assertEqual(response.status_code, 200)
        users = User.objects.filter(email=data["email"], is_active=True)
        self.assertEqual(len(users), 1)
        # Verification required - test an inactive user is created,
        settings.ACCOUNTS_VERIFICATION_REQUIRED = True
        data = self.account_data("test2")
        emails = len(mail.outbox)
        response = self.client.post(reverse("signup"), data, follow=True)
        self.assertEqual(response.status_code, 200)
        users = User.objects.filter(email=data["email"], is_active=False)
        self.assertEqual(len(users), 1)
        # Test the verification email.
        self.assertEqual(len(mail.outbox), emails + 1)
        self.assertEqual(len(mail.outbox[0].to), 1)
        self.assertEqual(mail.outbox[0].to[0], data["email"])
        # Test the verification link.
        new_user = users[0]
        verification_url = reverse(
            "signup_verify",
            kwargs={
                "uidb36": int_to_base36(new_user.id),
                "token": default_token_generator.make_token(new_user),
            },
        )
        response = self.client.get(verification_url, follow=True)
        self.assertEqual(response.status_code, 200)
        users = User.objects.filter(email=data["email"], is_active=True)
        self.assertEqual(len(users), 1)

    def test_min_password_length(self):
        """
        Passwords shorter than ACCOUNTS_MIN_PASSWORD_LENGTH (12) are rejected.
        """
        self.assertEqual(settings.ACCOUNTS_MIN_PASSWORD_LENGTH, 12)
        settings.ACCOUNTS_VERIFICATION_REQUIRED = False
        data = self.account_data("shortpw")
        data["password1"] = "x" * 11
        data["password2"] = "x" * 11
        response = self.client.post(reverse("signup"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email=data["email"]).count(), 0)
        self.assertTrue(response.context["form"].errors)

    def _reset_url(self, user):
        return reverse(
            "password_reset_verify",
            kwargs={
                "uidb36": int_to_base36(user.id),
                "token": default_token_generator.make_token(user),
            },
        )

    def test_password_reset_request_sends_mail(self):
        """
        Submitting the reset form emails a verification link.
        """
        user = User.objects.create_user(
            "resetmail", "resetmail@example.com", "old-password-12"
        )
        emails = len(mail.outbox)
        response = self.client.post(
            reverse("mezzanine_password_reset"), {"username": user.username}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), emails + 1)
        self.assertEqual(mail.outbox[-1].to, [user.email])

    def test_password_reset_does_not_log_in(self):
        """
        Following the reset link must not create a session. The user
        sets a new password, then logs in separately.
        """
        user = User.objects.create_user(
            "resetme", "resetme@example.com", "old-password-12"
        )
        url = self._reset_url(user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["user"].is_authenticated)
        self.assertNotIn("_auth_user_id", self.client.session)

        new_password = "x" * settings.ACCOUNTS_MIN_PASSWORD_LENGTH
        response = self.client.post(
            url, {"password1": new_password, "password2": new_password}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["user"].is_authenticated)
        self.assertNotIn("_auth_user_id", self.client.session)

        user.refresh_from_db()
        self.assertTrue(user.check_password(new_password))
        self.assertFalse(user.check_password("old-password-12"))
        self.assertTrue(self.client.login(username="resetme", password=new_password))

    def test_password_reset_invalid_token(self):
        """
        A bad token does not log anyone in and does not change the password.
        """
        user = User.objects.create_user(
            "badtoken", "badtoken@example.com", "old-password-12"
        )
        url = reverse(
            "password_reset_verify",
            kwargs={
                "uidb36": int_to_base36(user.id),
                "token": "not-a-real-token",
            },
        )
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        user.refresh_from_db()
        self.assertTrue(user.check_password("old-password-12"))

    def test_password_reset_rejects_short_password(self):
        """
        The confirm form enforces the same minimum length.
        """
        user = User.objects.create_user(
            "resetshort", "resetshort@example.com", "old-password-12"
        )
        url = self._reset_url(user)
        response = self.client.post(url, {"password1": "short", "password2": "short"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertNotIn("_auth_user_id", self.client.session)
        user.refresh_from_db()
        self.assertTrue(user.check_password("old-password-12"))

    def test_logout_post_only(self):
        """
        Logout is POST-only so a GET cannot CSRF-logout a session.
        """
        self.client.login(username=self._username, password=self._password)
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)

        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)
