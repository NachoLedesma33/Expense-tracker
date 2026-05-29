from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib import messages
from .models import Transaction, Category
from .forms import TransactionForm, CategoryForm
from services import get_filtered_transactions


class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'transactions/list.html'
    context_object_name = 'transactions'
    paginate_by = 20

    def get_queryset(self):
        type_filter = self.request.GET.get('type', 'all')
        category_id = self.request.GET.get('category', '')
        return get_filtered_transactions(
            self.request.user,
            type_filter=type_filter,
            category_id=category_id if category_id else None,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.filter(user=self.request.user)
        ctx['form'] = TransactionForm(user=self.request.user)
        ctx['category_form'] = CategoryForm(user=self.request.user)
        ctx['current_type'] = self.request.GET.get('type', 'all')
        ctx['current_category'] = self.request.GET.get('category', '')
        return ctx

    def get(self, request, *args, **kwargs):
        if request.headers.get('HX-Request'):
            self.object_list = self.get_queryset()
            context = self.get_context_data()
            html = render_to_string('transactions/partials/transaction_rows.html', {
                'transactions': context['object_list'],
            }, request=request)
            return HttpResponse(html)
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
