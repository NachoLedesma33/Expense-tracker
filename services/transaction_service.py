from datetime import date, timedelta
from django.db.models import Sum, Q, Count
from django.db.models.functions import TruncMonth
from transactions.models import Transaction, Category


def get_dashboard_stats(user):
    qs = Transaction.objects.filter(user=user)
    income = qs.filter(type='income').aggregate(total=Sum('amount'))['total'] or 0
    expenses = qs.filter(type='expense').aggregate(total=Sum('amount'))['total'] or 0
    balance = income - expenses
    count = qs.count()
    last_transactions = qs.select_related('category')[:5]
    return {
        'balance': balance,
        'income': income,
        'expenses': expenses,
        'count': count,
        'last_transactions': last_transactions,
    }


def get_expenses_by_category(user):
    data = (
        Transaction.objects.filter(user=user, type='expense')
        .values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    labels = [item['category__name'] or 'Uncategorized' for item in data]
    values = [float(item['total']) for item in data]
    return {'labels': labels, 'values': values}


def get_monthly_income_vs_expenses(user, months=6):
    today = date.today()
    start_date = today.replace(day=1)
    for _ in range(months - 1):
        if start_date.month > 1:
            start_date = start_date.replace(month=start_date.month - 1)
        else:
            start_date = start_date.replace(year=start_date.year - 1, month=12)

    monthly = (
        Transaction.objects.filter(user=user, date__gte=start_date, date__lte=today)
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


def get_filtered_transactions(user, type_filter=None, category_id=None,
                               date_from=None, date_to=None, search=None):
    qs = Transaction.objects.filter(user=user).select_related('category')
    if type_filter and type_filter != 'all':
        qs = qs.filter(type=type_filter)
    if category_id:
        qs = qs.filter(category_id=category_id)
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)
    if search:
        qs = qs.filter(
            Q(title__icontains=search) |
            Q(category__name__icontains=search)
        )
    return qs


def get_analytics_data(user):
    qs = Transaction.objects.filter(user=user)
    income = qs.filter(type='income').aggregate(total=Sum('amount'))['total'] or 0
    expenses = qs.filter(type='expense').aggregate(total=Sum('amount'))['total'] or 0
    balance = income - expenses

    expense_by_cat = (
        qs.filter(type='expense')
        .values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    category_labels = [c['category__name'] or 'Uncategorized' for c in expense_by_cat]
    category_values = [float(c['total']) for c in expense_by_cat]

    income_by_cat = (
        qs.filter(type='income')
        .values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    income_cat_labels = [c['category__name'] or 'Uncategorized' for c in income_by_cat]
    income_cat_values = [float(c['total']) for c in income_by_cat]

    today = date.today()
    start_date = today.replace(day=1)
    for _ in range(5):
        if start_date.month > 1:
            start_date = start_date.replace(month=start_date.month - 1)
        else:
            start_date = start_date.replace(year=start_date.year - 1, month=12)

    monthly = (
        qs.filter(date__gte=start_date, date__lte=today)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(
            income=Sum('amount', filter=Q(type='income')),
            expense=Sum('amount', filter=Q(type='expense')),
        )
        .order_by('month')
    )
    monthly_labels = [m['month'].strftime('%b %Y') for m in monthly]
    monthly_income = [float(m['income'] or 0) for m in monthly]
    monthly_expenses = [float(m['expense'] or 0) for m in monthly]

    cumulative = []
    running = 0
    for inc, exp in zip(monthly_income, monthly_expenses):
        running += inc - exp
        cumulative.append(round(running, 2))

    top_expense_cats = expense_by_cat[:5]
    top_income_cats = income_by_cat[:5]

    latest = qs.select_related('category').order_by('-date')[:10]

    month_count = qs.annotate(month=TruncMonth('date')).values('month').distinct().count()
    avg_monthly_expense = expenses / month_count if month_count else 0

    return {
        'income': income,
        'expenses': expenses,
        'balance': balance,
        'transaction_count': qs.count(),
        'avg_monthly_expense': avg_monthly_expense,
        'category_labels': category_labels,
        'category_values': category_values,
        'income_cat_labels': income_cat_labels,
        'income_cat_values': income_cat_values,
        'monthly_labels': monthly_labels,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'cumulative_balance': cumulative,
        'top_expense_cats': top_expense_cats,
        'top_income_cats': top_income_cats,
        'latest_transactions': latest,
    }


def export_transactions_csv(user, type_filter=None, category_id=None,
                             date_from=None, date_to=None, search=None):
    qs = Transaction.objects.filter(user=user).select_related('category')
    if type_filter and type_filter != 'all':
        qs = qs.filter(type=type_filter)
    if category_id:
        qs = qs.filter(category_id=category_id)
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)
    if search:
        qs = qs.filter(
            Q(title__icontains=search) |
            Q(category__name__icontains=search)
        )
    return qs.order_by('-date', '-created_at')
