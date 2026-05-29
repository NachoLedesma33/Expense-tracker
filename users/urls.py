from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import RegisterView, LoginViewCustom, logout_view

app_name = 'users'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginViewCustom.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
]
