import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from services import get_analytics_data, generate_insights, generate_recommendations


class OverviewView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/overview.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['data'] = get_analytics_data(self.request.user)
        ctx['insights'] = generate_insights(self.request.user)
        ctx['recommendations'] = generate_recommendations(self.request.user)
        ctx['chart_json'] = {
            'category': json.dumps({
                'labels': ctx['data']['category_labels'],
                'values': ctx['data']['category_values'],
            }),
            'monthly': json.dumps({
                'labels': ctx['data']['monthly_labels'],
                'income': ctx['data']['monthly_income'],
                'expenses': ctx['data']['monthly_expenses'],
            }),
            'cumulative': json.dumps({
                'labels': ctx['data']['monthly_labels'],
                'balance': ctx['data']['cumulative_balance'],
            }),
            'income_cat': json.dumps({
                'labels': ctx['data']['income_cat_labels'],
                'values': ctx['data']['income_cat_values'],
            }),
        }
        return ctx
