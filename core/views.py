import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, RedirectView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from services import get_dashboard_stats, get_expenses_by_category, get_monthly_income_vs_expenses


class HomeView(LoginRequiredMixin, RedirectView):
    url = reverse_lazy('transactions:list')


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['stats'] = get_dashboard_stats(self.request.user)
        ctx['category_chart'] = json.dumps(get_expenses_by_category(self.request.user))
        ctx['monthly_chart'] = json.dumps(get_monthly_income_vs_expenses(self.request.user))
        return ctx


class SettingsRedirectView(LoginRequiredMixin, RedirectView):
    url = reverse_lazy('users:settings')
