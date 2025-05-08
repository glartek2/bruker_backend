from django.urls import path
from . import views

app_name = "users"

urlpatterns = [

]

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    # path('register/', views.register, name="register"),
    # path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('reset_password/', views.password_reset_request, name='password_reset'),
    path('reset/<uidb64>/<token>/', views.reset_password, name='reset')

]