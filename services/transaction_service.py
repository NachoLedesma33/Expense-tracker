from datetime import date
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth
from transactions.models import Transaction, Category


def get_dashboard_stats():
    income = Transaction.objects.filter(type='income').aggregate(total=Sum('amount'))['total'] or 0
    expenses = Transaction.objects.filter(type='expense').aggregate(total=Sum('amount'))['total'] or 0
    balance = income - expenses
    count = Transaction.objects.count()
    last_transactions = Transaction.objects.select_related('category')[:5]
    return {
        'balance': balance,
        'income': income,
        'expenses': expenses,
        'count': count,
        'last_transactions': last_transactions,
    }


def get_expenses_by_category():
    data = (
        Transaction.objects.filter(type='expense')
        .values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    labels = [item['category__name'] or 'Uncategorized' for item in data]
    values = [float(item['total']) for item in data]
    return {'labels': labels, 'values': values}


def get_monthly_income_vs_expenses(months=6):
    today = date.today()
    start_date = today.replace(day=1)
    for _ in range(months - 1):
        start_date = start_date.replace(month=start_date.month - 1) if start_date.month > 1 else start_date.replace(year=start_date.year - 1, month=12)

    monthly = (
        Transaction.objects.filter(date__gte=start_date, date__lte=today)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(
            income=Sum('amount', filter=Q(type='income')),
            expense=Sum('amount', filter=Q(type='expense')),
        )
        .order_by('month')
    )
    labels = [item['month'].strftime('%b %Y') for item in monthly]
    income_data = [float(item['income'] or 0) for item in monthly]
    expense_data = [float(item['expense'] or 0) for item in monthly]
    return {'labels': labels, 'income': income_data, 'expenses': expense_data}


def get_filtered_transactions(type_filter=None, category_id=None):
    qs = Transaction.objects.select_related('category').all()
    if type_filter and type_filter != 'all':
        qs = qs.filter(type=type_filter)
    if category_id:
        qs = qs.filter(category_id=category_id)
    return qs
