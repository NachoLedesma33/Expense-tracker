from django.urls import path
from .views import HomeView, SettingsRedirectView

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('settings/', SettingsRedirectView.as_view(), name='settings'),
]
