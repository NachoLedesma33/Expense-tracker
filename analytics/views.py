from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class OverviewView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/overview.html'
