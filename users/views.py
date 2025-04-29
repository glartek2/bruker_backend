from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
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
        user = None

    if user and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        messages.success(request, "Thank you for your email confirmation.Now you can login to your account.")
        return redirect('users:login')

    else:
        messages.error(request, "Activation link invalid.")

    return redirect('home_module:home page')


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

    if email.send():
        messages.success(
            request,
            mark_safe(f'Dear <b>{user}</b>, please go to your email <b>{to_email}</b> inbox and click on \
                      the received activation link to confirm and complete the registration. <b>Note:</b> Check your spam folder.')
        )
    else:
        messages.error(request, f'Problem sending email to {to_email}, check if you typed it correctly.')


def reset_password(request, uidb64, token):
    User = get_user_model()

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)

            if form.is_valid():
                form.save()
                messages.success(request,
                                 "Your password was successfully reset.Now you can log in to your account.")
                return redirect('users:login')
        else:
            form = SetPasswordForm(user)
            return render(request, 'user/password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, "Activation link invalid or expired.")
        return redirect('home_module:home_page')


def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']
            User = get_user_model()
            try:
                user = User.objects.get(email=email)
                reset_password_email(request, user, email)
                messages.success(request, 'We send you an email with password reset instruction.')
                return redirect('users:login')
            except ObjectDoesNotExist:
                messages.error(request, 'User with given email not found.')

    else:
        form = PasswordResetForm()

    return render(request, 'user/password_reset_form.html', {'form': form})


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

    if email.send():
        messages.success(
            request,
            mark_safe(
                f'Dear <b>{user}</b>,please go to your email<b>{to_email}</b>inbox and click on \
                      the received link to confirm password reset. <b>Note:</b> Check your spam folder.')
        )
    else:
        messages.error(request, f'Problem sending email to {to_email}, check if you typed it correctly.')


@user_not_authenticated
def register(request):
    if request.method == 'POST':

        form = UserRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            activate_email(request, user, form.cleaned_data['email'])
            return redirect('home_module:home page')

        else:
            for error in list(form.errors.values()):
                messages.error(request, error)

    else:
        form = UserRegistrationForm()

    return render(request, template_name="user/register.html", context={'form': form})


@login_required
def custom_logout(request):
    logout(request)
    messages.info(request, "Logged out successfully")

    return redirect('home_module:home page')


@user_not_authenticated
def custom_login(request):
    max_attempts = 3

    if request.method != "POST":
        request.session['failed_login_attempts'] = 0

    attempts = request.session.get('failed_login_attempts', 0)

    if request.method == "POST":
        form = UserLoginForm(request=request, data=request.POST)

        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )

            if user:
                request.session['failed_login_attempts'] = 0
                login(request, user)
                messages.success(request, mark_safe(f"Hello <b>{user.username}</b>! You have been logged in"))
                return redirect('home_module:home page')

        else:
            attempts += 1
            request.session['failed_login_attempts'] = attempts

            if attempts >= max_attempts:
                reset_password_url = reverse('users:password_reset')

                msg = mark_safe(
                    "Wrong password entered 3 times."
                    f"<a href=\"{reset_password_url}\">Reset password</a>"
                )
                messages.warning(request, msg)
            else:

                messages.error(request, "Incorrect username or password")

    form = UserLoginForm()

    return render(request=request, template_name='user/login.html', context={'form': form})