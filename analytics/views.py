from django.views.generic import TemplateView


class OverviewView(TemplateView):
    template_name = 'analytics/overview.html'
