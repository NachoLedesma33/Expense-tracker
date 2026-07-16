import json
import csv
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.contrib import messages
from .models import Transaction, Category
from .forms import TransactionForm, CategoryForm
from services import get_filtered_transactions, export_transactions_csv, predict_category, learn_from_correction


class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'transactions/list.html'
    context_object_name = 'transactions'
    paginate_by = 20

    def get_queryset(self):
        return get_filtered_transactions(
            self.request.user,
            type_filter=self.request.GET.get('type', 'all'),
            category_id=self.request.GET.get('category', ''),
            date_from=self.request.GET.get('date_from', ''),
            date_to=self.request.GET.get('date_to', ''),
            search=self.request.GET.get('search', ''),
            categories=self.request.GET.getlist('categories'),
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.filter(user=self.request.user)
        ctx['form'] = TransactionForm(user=self.request.user)
        ctx['category_form'] = CategoryForm(user=self.request.user)
        ctx['current_type'] = self.request.GET.get('type', 'all')
        ctx['current_category'] = self.request.GET.get('category', '')
        ctx['current_date_from'] = self.request.GET.get('date_from', '')
        ctx['current_date_to'] = self.request.GET.get('date_to', '')
        ctx['current_search'] = self.request.GET.get('search', '')
        ctx['selected_categories'] = self.request.GET.getlist('categories')
        return ctx

    def get(self, request, *args, **kwargs):
        if request.headers.get('HX-Request'):
            target = request.headers.get('HX-Target', '')
            if target == 'transaction-list':
                self.object_list = self.get_queryset()
                context = self.get_context_data()
                page_obj = context.get('page_obj')
                is_paginated = context.get('is_paginator')
                paginator = context.get('paginator')
                html = render_to_string('transactions/partials/transaction_rows.html', {
                    'transactions': context['object_list'],
                    'page_obj': page_obj,
                    'is_paginated': is_paginated,
                    'paginator': paginator,
                }, request=request)
                return HttpResponse(html)
            elif target == 'search-results':
                self.object_list = self.get_queryset()
                context = self.get_context_data()
                html = render_to_string('transactions/partials/transaction_rows.html', {
                    'transactions': context['object_list'],
                }, request=request)
                return HttpResponse(html)
            elif target == 'filter-count':
                count = self.get_queryset().count()
                return HttpResponse(f'{count} transaction{"s" if count != 1 else ""}')
        return super().get(request, *args, **kwargs)


class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'transactions/partials/form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        if self.object.category:
            learn_from_correction(self.object.title, self.object.category_id)
        messages.success(self.request, 'Transaction created.')
        if self.request.headers.get('HX-Request'):
            html = render_to_string('transactions/partials/transaction_row.html', {
                't': self.object,
            }, request=self.request)
            return HttpResponse(html, status=201)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('transactions:list')

    def form_invalid(self, form):
        if self.request.headers.get('HX-Request'):
            html = render_to_string('transactions/partials/form.html', {
                'form': form,
            }, request=self.request)
            return HttpResponse(html, status=422)
        return super().form_invalid(form)


class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'transactions/partials/form.html'
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse_lazy('transactions:list')

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, 'Transaction updated.')
        if self.request.headers.get('HX-Request'):
            html = render_to_string('transactions/partials/transaction_row.html', {
                't': self.object,
            }, request=self.request)
            return HttpResponse(html)
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('HX-Request'):
            html = render_to_string('transactions/partials/form.html', {
                'form': form,
            }, request=self.request)
            return HttpResponse(html, status=422)
        return super().form_invalid(form)


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse_lazy('transactions:list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(request, 'Transaction deleted.')
        if request.headers.get('HX-Request'):
            return HttpResponse(status=200)
        return super().delete(request, *args, **kwargs)


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    success_url = reverse_lazy('transactions:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        messages.success(self.request, 'Category created.')
        if self.request.headers.get('HX-Request'):
            html = render_to_string('transactions/partials/category_option.html', {
                'category': self.object,
            }, request=self.request)
            return HttpResponse(html, status=201)
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('HX-Request'):
            html = render_to_string('transactions/partials/category_form.html', {
                'category_form': form,
            }, request=self.request)
            return HttpResponse(html, status=422)
        return super().form_invalid(form)


class TransactionExportView(LoginRequiredMixin, ListView):
    def get(self, request, *args, **kwargs):
        qs = export_transactions_csv(
            request.user,
            type_filter=request.GET.get('type', 'all'),
            category_id=request.GET.get('category', ''),
            date_from=request.GET.get('date_from', ''),
            date_to=request.GET.get('date_to', ''),
            search=request.GET.get('search', ''),
        )
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
        writer = csv.writer(response)
        writer.writerow(['Title', 'Amount', 'Type', 'Category', 'Date'])
        for t in qs:
            writer.writerow([
                t.title,
                t.amount,
                t.type,
                t.category.name if t.category else '',
                t.date.isoformat(),
            ])
        return response


class PredictCategoryView(LoginRequiredMixin, View):
    def get(self, request):
        text = request.GET.get('q', '').strip()
        if len(text) < 3:
            return HttpResponse('')
        result = predict_category(text)
        if result['category_id'] is None:
            return HttpResponse('')
        try:
            cat = Category.objects.get(id=result['category_id'])
            html = render_to_string('transactions/partials/predicted_category.html', {
                'category': cat,
                'confidence': result['confidence'],
            }, request=request)
            return HttpResponse(html)
        except Category.DoesNotExist:
            return HttpResponse('')


class LearnCategoryView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            text = data.get('text', '').strip()
            cat_id = data.get('category_id')
            if text and cat_id:
                learn_from_correction(text, int(cat_id))
                return JsonResponse({'status': 'ok'})
            return JsonResponse({'status': 'skip', 'reason': 'missing_fields'}, status=400)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'status': 'error', 'reason': 'invalid_data'}, status=400)
