from django.urls import path
from .views import HomeView, SettingsView

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('settings/', SettingsView.as_view(), name='settings'),
]
