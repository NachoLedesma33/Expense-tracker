from django.contrib import admin
from .models import Category, Transaction, Budget


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user']
    list_filter = ['user']
    search_fields = ['name']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['title', 'amount', 'type', 'category', 'user', 'date']
    list_filter = ['type', 'user', 'category', 'date']
    search_fields = ['title']
    date_hierarchy = 'date'


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['category', 'user', 'amount', 'month']
    list_filter = ['user', 'month']
