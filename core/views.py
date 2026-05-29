import json
from django.views.generic import TemplateView
from services import get_dashboard_stats, get_expenses_by_category, get_monthly_income_vs_expenses


class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['stats'] = get_dashboard_stats()
        ctx['category_chart'] = json.dumps(get_expenses_by_category())
        ctx['monthly_chart'] = json.dumps(get_monthly_income_vs_expenses())
        return ctx


class SettingsView(TemplateView):
    template_name = 'core/settings.html'
