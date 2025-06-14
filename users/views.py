from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import authenticate, get_user_model
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from .serializers import RegisterSerializer, LoginSerializer, TokenResponseSerializer, ResetPasswordConfirmSerializer, \
    ResetPasswordRequestSerializer, MessageSerializer
from .tokens import account_activation_token


def send_email(request, user, mail_subject, token_generator, template_name, to_email,extra_context=None):
    context = {
        "user": user,
        "domain": "bruker-backend",
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "token": token_generator.make_token(user),
        "protocol": "https" if request.is_secure() else "http",
    }
    if extra_context:
        context.update(extra_context)

    message = render_to_string(template_name, context)

    email = EmailMessage(mail_subject, message, to=[to_email])
    email.content_subtype = "html"
    email.send()


class ActivateAccountView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter('uidb64', str, OpenApiParameter.PATH),
            OpenApiParameter('token', str, OpenApiParameter.PATH)
        ]
    )
    def get(self, request, uidb64, token):

        User = get_user_model()

        try:

            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)

        except Exception:
            return Response({'detail': "Invalid activation link"}, status=status.HTTP_400_BAD_REQUEST)

        if account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()

            return Response({'detail': "Account activated succesfully"}, status=status.HTTP_200_OK)

        return Response({'detail': "Invalid activation link"}, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordRequestView(APIView):

    @extend_schema(
        request=ResetPasswordRequestSerializer,
        responses={200: OpenApiResponse(description="Reset link sent if user exist"),
                   400: OpenApiResponse(description="Validation error")}

    )
    def post(self, request):
        serializer = ResetPasswordRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        User = get_user_model()
        user = User.objects.filter(email=email).first()

        if user:
            send_email(
                request,
                user,
                mail_subject="Rest your password",
                token_generator=default_token_generator,
                template_name='template_reset_password.html',
                to_email=email
            )
        return Response({'detail': 'If the email exists, a reset link has been sent.'}, status=status.HTTP_200_OK)


class ResetPasswordConfirmationView(APIView):

    @extend_schema(
        parameters=[
            OpenApiParameter('uidb64', str, OpenApiParameter.PATH),
            OpenApiParameter('token', str, OpenApiParameter.PATH)
        ],
        request=ResetPasswordConfirmSerializer,
        responses={200: MessageSerializer, 400: OpenApiResponse(description="Invalid token or validation error")}
    )
    def post(self, request, uidb64, token):
        serializer = ResetPasswordConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = get_user_model().objects.get(pk=uid)

        except Exception:
            return Response({'detail': "Invalid link."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"detail": 'Token invalid or expired.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({"detail": "Password has been reset successfully"}, status=status.HTTP_200_OK)


class RegisterView(APIView):
    @extend_schema(
        request=RegisterSerializer,
        responses={201: TokenResponseSerializer},
        description="Register a new user"
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            send_email(
                request,
                user,
                mail_subject="Activate your account",
                token_generator=account_activation_token,
                template_name='template_activate_account.html',
                to_email=user.email
            )
            token = Token.objects.get(user=user)
            return Response({'token': token.key}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    @extend_schema(
        request=LoginSerializer,
        responses={200: TokenResponseSerializer},
        description="Log in with username and password"
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(username=serializer.validated_data['username'],
                                password=serializer.validated_data['password'])
            if user:
                token, _ = Token.objects.get_or_create(user=user)
                return Response({'token': token.key})
            return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={204: OpenApiResponse(description="Token deleted")},
    )
    def post(self, request):
        if hasattr(request, 'auth') and request.auth:
            request.auth.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
