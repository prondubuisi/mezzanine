from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.messages import error, info
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import NoReverseMatch, get_script_prefix, reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST

from mezzanine.accounts import get_profile_form
from mezzanine.accounts.forms import (
    LoginForm,
    PasswordResetConfirmForm,
    PasswordResetForm,
)
from mezzanine.conf import settings
from mezzanine.utils.email import send_approve_mail, send_verification_mail
from mezzanine.utils.urls import login_redirect, next_url

User = get_user_model()

# Django PasswordResetConfirmView: stash the token, then render on a
# token-free URL so site chrome / Referer / analytics cannot leak it.
INTERNAL_RESET_SESSION_TOKEN = "_password_reset_token"
RESET_URL_TOKEN = "set-password"


@sensitive_post_parameters("password")
def login(
    request,
    template="accounts/account_login.html",
    form_class=LoginForm,
    extra_context=None,
):
    """
    Login form.
    """
    form = form_class(request.POST or None)
    if request.method == "POST" and form.is_valid():
        authenticated_user = form.save()
        info(request, _("Successfully logged in"))
        auth_login(request, authenticated_user)
        return login_redirect(request)
    context = {"form": form, "title": _("Log in")}
    context.update(extra_context or {})
    return TemplateResponse(request, template, context)


@require_POST
def logout(request):
    """
    Log the user out. POST-only to prevent CSRF-logout via GET.
    """
    auth_logout(request)
    info(request, _("Successfully logged out"))
    return redirect(next_url(request) or get_script_prefix())


@sensitive_post_parameters("password1", "password2")
def signup(request, template="accounts/account_signup.html", extra_context=None):
    """
    Signup form.
    """
    profile_form = get_profile_form()
    form = profile_form(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        new_user = form.save()
        if not new_user.is_active:
            if settings.ACCOUNTS_APPROVAL_REQUIRED:
                send_approve_mail(request, new_user)
                info(
                    request,
                    _(
                        "Thanks for signing up! You'll receive "
                        "an email when your account is activated."
                    ),
                )
            else:
                send_verification_mail(request, new_user, "signup_verify")
                info(
                    request,
                    _(
                        "A verification email has been sent with "
                        "a link for activating your account."
                    ),
                )
            return redirect(next_url(request) or "/")
        else:
            info(request, _("Successfully signed up"))
            auth_login(request, new_user)
            return login_redirect(request)
    context = {"form": form, "title": _("Sign up")}
    context.update(extra_context or {})
    return TemplateResponse(request, template, context)


def signup_verify(request, uidb36=None, token=None):
    """
    View for the link in the verification email sent to a new user
    when they create an account and ``ACCOUNTS_VERIFICATION_REQUIRED``
    is set to ``True``. Activates the user and logs them in,
    redirecting to the URL they tried to access when signing up.
    """
    user = authenticate(uidb36=uidb36, token=token, is_active=False)
    if user is not None:
        user.is_active = True
        user.save()
        auth_login(request, user)
        info(request, _("Successfully signed up"))
        return login_redirect(request)
    else:
        error(request, _("The link you clicked is no longer valid."))
        return redirect("/")


@login_required
def profile_redirect(request):
    """
    Just gives the URL prefix for profiles an action - redirect
    to the logged in user's profile.
    """
    return redirect("profile", username=request.user.username)


def profile(
    request, username, template="accounts/account_profile.html", extra_context=None
):
    """
    Display a profile.
    """
    lookup = {"username__iexact": username, "is_active": True}
    context = {"profile_user": get_object_or_404(User, **lookup)}
    context.update(extra_context or {})
    return TemplateResponse(request, template, context)


@login_required
def account_redirect(request):
    """
    Just gives the URL prefix for accounts an action - redirect
    to the profile update form.
    """
    return redirect("profile_update")


@sensitive_post_parameters("password1", "password2")
@login_required
def profile_update(
    request, template="accounts/account_profile_update.html", extra_context=None
):
    """
    Profile update form.
    """
    profile_form = get_profile_form()
    form = profile_form(
        request.POST or None, request.FILES or None, instance=request.user
    )
    if request.method == "POST" and form.is_valid():
        user = form.save()
        info(request, _("Profile updated"))
        try:
            return redirect("profile", username=user.username)
        except NoReverseMatch:
            return redirect("profile_update")
    context = {"form": form, "title": _("Update Profile")}
    context.update(extra_context or {})
    return TemplateResponse(request, template, context)


def password_reset(
    request,
    template="accounts/account_password_reset.html",
    form_class=PasswordResetForm,
    extra_context=None,
):
    form = form_class(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        send_verification_mail(request, user, "password_reset_verify")
        info(
            request,
            _(
                "A verification email has been sent with "
                "a link for resetting your password."
            ),
        )
    context = {"form": form, "title": _("Password Reset")}
    context.update(extra_context or {})
    return TemplateResponse(request, template, context)


@never_cache
@sensitive_post_parameters("password1", "password2")
def password_reset_verify(
    request,
    uidb36=None,
    token=None,
    template="accounts/account_form.html",
    form_class=PasswordResetConfirmForm,
    extra_context=None,
):
    """
    Validate the password-reset token and let the user set a new
    password. Does not create a login session: a stolen reset mail
    must not become a logged-in user.

    A valid email token is stored in the session and the browser is
    redirected to a token-free ``set-password`` URL before any site
    chrome is rendered, matching Django's PasswordResetConfirmView.
    """
    if token == RESET_URL_TOKEN:
        session_token = request.session.get(INTERNAL_RESET_SESSION_TOKEN)
        user = (
            authenticate(uidb36=uidb36, token=session_token, is_active=True)
            if session_token
            else None
        )
        if user is None:
            error(request, _("The link you clicked is no longer valid."))
            return redirect("/")
        form = form_class(user, request.POST or None)
        if request.method == "POST" and form.is_valid():
            form.save()
            request.session.pop(INTERNAL_RESET_SESSION_TOKEN, None)
            info(
                request,
                _(
                    "Your password has been reset. Please log in "
                    "with your new password."
                ),
            )
            return redirect("login")
        context = {"form": form, "title": _("Password Reset")}
        context.update(extra_context or {})
        return TemplateResponse(request, template, context)

    user = authenticate(uidb36=uidb36, token=token, is_active=True)
    if user is None:
        error(request, _("The link you clicked is no longer valid."))
        return redirect("/")
    request.session[INTERNAL_RESET_SESSION_TOKEN] = token
    return redirect(
        reverse(
            "password_reset_verify",
            kwargs={"uidb36": uidb36, "token": RESET_URL_TOKEN},
        )
    )
