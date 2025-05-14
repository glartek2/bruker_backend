from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('activate/<uidb64>/<token>/', views.ActivateAccountView.as_view(), name='activate'),
    path('reset_password/', views.ResetPasswordRequestView.as_view(), name='reset_password'),
    path(
        'password_reset_confirm/<uidb64>/<token>/',
        views.ResetPasswordConfirmationView.as_view(),
        name='password_reset_confirm'
    )

]