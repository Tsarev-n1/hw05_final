from django import views
from django.urls import path
from django.contrib.auth.views import LogoutView, LoginView
from . import views

app_name = 'users'

urlpatterns = [
    path(
        'logout/',
        LogoutView.as_view(template_name='users/logged_out.html'),
        name='logout'
    ),
    path('signup/', views.SignUp.as_view(), name='signup'),
    path(
        'login/',
        LoginView.as_view(template_name='users/login.html'),
        name='login'
    ),
    path(
        'password_change/',
        views.PasswordChange.as_view(),
        name='password_change'
    ),
    path(
        'password_change_done/',
        views.PasswordChangeDone.as_view(),
        name='password_change_done'
    ),
    path(
        'password_reset_form/',
        views.PasswordResetEmail.as_view(),
        name='password_reset_email'
    ),
    path(
        'password_reset_done/',
        views.PasswordResetDone.as_view(),
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        views.PasswordResetConfirm.as_view(),
        name='password_reset_confirm'
    ),
    path(
        'password_reset_complete/',
        views.PasswordResetComplete.as_view(),
        name='password_reset_complete'
    ),
]
