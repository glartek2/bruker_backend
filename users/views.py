import json
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.views.decorators.http import require_POST

from .forms import UserRegistrationForm, UserLoginForm
from .decorators import user_not_authenticated
from .tokens import account_activation_token
from django.urls import reverse


def activate(request, uidb64, token):
    User = get_user_model()

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return JsonResponse({"success": False, "message": "Invalid activation link"}, status=400)

    if account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        return JsonResponse(
            {
                "success": True,
                "message": "Thank you for your email confirmation. Now you can login to your account."
            }

        )

    else:
        return JsonResponse({"success": False, "message": "Invalid activation link"}, status=400)


def activate_email(request, user, to_email):
    mail_subject = "Activate your user account"
    message = render_to_string("template_activate_account.html", {
        'user': user,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'

    })

    email = EmailMessage(mail_subject, message, to=[to_email])

    return email.send()


@require_POST
def reset_password(request, uidb64, token):
    User = get_user_model()

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return JsonResponse({"success": False, "message": "Invalid user"}, status=400)

    if not default_token_generator.check_token(user, token):
        return JsonResponse({"success": False, "message": "Invalid or expired token"}, status=400)

    data = json.loads(request.body)
    form = SetPasswordForm(user, data)

    if form.is_valid():
        form.save()
        return JsonResponse(
            {"success": True, "message": "Your password was successfully reset. Now you can log in to your account."}
        )
    return JsonResponse({"success": False, "errors": form.errors}, status=400)


@require_POST
def password_reset_request(request):
    data = json.loads(request.body)
    form = PasswordResetForm(data)
    if form.is_valid():
        email = form.cleaned_data['email']
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
            if reset_password_email(request, user, email):
                return JsonResponse(
                    {"success": True, "message": "We send you an email with password reset instruction."})
            else:
                return JsonResponse({"success": False, "message": "Error sending email"}, status=500)
        except ObjectDoesNotExist:

            return JsonResponse({"success": False, "message": "User with given email not found."}, status=404)

    return JsonResponse({"success": False, "errors": form.errors}, status=400)


def reset_password_email(request, user, to_email):
    mail_subject = 'Reset your password'
    message = render_to_string('template_reset_password.html', {
        'user': user,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http',
    })
    email = EmailMessage(mail_subject, message, to=[to_email])

    return email.send()


@user_not_authenticated
@require_POST
def register(request):
    data = json.loads(request.body)
    form = UserRegistrationForm(data)

    if form.is_valid():
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        email_sent = activate_email(request, user, form.cleaned_data['email'])
        return JsonResponse(
            {
                "success": True,
                "message": "Registration successful. Activation email sent." if email_sent
                else "User created, but email failed."
            })

    return JsonResponse({"success": False, "errors": form.errors}, status=400)


@require_POST
def custom_logout(request):
    if request.user.is_authenticated:
        logout(request)
        return JsonResponse({'success': True, 'message': 'Logged out'})
    return JsonResponse({'success': False, 'message': 'Not logged in'}, status=401)


@require_POST
def custom_login(request):
    MAX_ATTEMPTS = 3
    attempts = request.session.get('failed_login_attempts', 0)

    data = json.loads(request.body)
    form = UserLoginForm(request=request, data=data)

    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        User = get_user_model()
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            user = None

        if user:
            user = authenticate(request, username=user.username, password=password)
            if user:
                request.session['failed_login_attempts'] = 0
                login(request, user)
                return JsonResponse({
                    "success": True,
                    "message": f"Hello {user.username}, you are now logged in.",
                    "data": user.to_dict(),
                })

    attempts += 1
    request.session['failed_login_attempts'] = attempts

    if attempts >= MAX_ATTEMPTS:
        reset_url = request.build_absolute_uri(reverse('users:password_reset'))
        return JsonResponse({
            "success": False,
            "message": (
                "Too many failed attempts. "
                f"Please reset your password: {reset_url}"
            ),
            "attempts": attempts,
            "blocked": True
        }, status=429)

    return JsonResponse({
        "success": False,
        "message": "Incorrect email or password.",
        "attempts": attempts,
        "remaining": MAX_ATTEMPTS - attempts
    }, status=400)
