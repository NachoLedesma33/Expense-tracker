from datetime import date, timedelta
from django.db.models import Sum, Count
from transactions.models import Transaction


def generate_insights(user) -> list[dict]:
    today = date.today()
    first_of_month = today.replace(day=1)
    insights = []

    qs = Transaction.objects.filter(user=user)
    this_month = qs.filter(date__gte=first_of_month)

    expense_month = this_month.filter(type='expense')

    this_total = float(expense_month.aggregate(t=Sum('amount'))['t'] or 0)

    top_cat = (
        expense_month.values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
        .first()
    )
    if top_cat and float(top_cat['total']) > 0:
        insights.append({
            'type': 'top_category',
            'title': 'Top Category This Month',
            'message': f"Your biggest expense this month is "
                       f"<strong>{top_cat['category__name'] or 'Uncategorized'}</strong> "
                       f"at <strong>${float(top_cat['total']):.2f}</strong>",
            'severity': 'info',
        })

    last_month_start = (first_of_month - timedelta(days=1)).replace(day=1)
    last_month = qs.filter(
        date__gte=last_month_start, date__lt=first_of_month, type='expense',
    )
    last_total = float(last_month.aggregate(t=Sum('amount'))['t'] or 0)
    if last_total > 0:
        change = ((this_total - last_total) / last_total) * 100
        if abs(change) > 5:
            is_up = change > 0
            insights.append({
                'type': 'trend',
                'title': 'Month-over-Month',
                'message': (
                    f"{'📈' if is_up else '📉'} You spent "
                    f"<strong>{abs(change):.0f}% {'more' if is_up else 'less'}</strong> "
                    f"this month compared to last month"
                ),
                'severity': 'warning' if is_up and change > 10 else 'success',
            })

    this_income = float(this_month.filter(type='income').aggregate(t=Sum('amount'))['t'] or 0)
    if this_income > 0 and this_total > 0:
        ratio = (this_total / this_income) * 100
        if ratio > 90:
            insights.append({
                'type': 'burn_rate',
                'title': 'High Burn Rate',
                'message': f"You've spent <strong>{ratio:.0f}%</strong> of your income "
                           f"this month. Consider cutting non-essential expenses.",
                'severity': 'danger',
            })
        elif ratio < 50:
            insights.append({
                'type': 'savings',
                'title': 'Good Saving Rate',
                'message': f"You've only spent <strong>{ratio:.0f}%</strong> "
                           f"of your income. Great job saving!",
                'severity': 'success',
            })

    recurring = (
        expense_month.values('title', 'amount')
        .annotate(count=Count('id'))
        .filter(count__gte=2)
        .order_by('-count')
    )
    for rec in recurring[:3]:
        insights.append({
            'type': 'recurring',
            'title': 'Recurring Expense',
            'message': f"<strong>{rec['title']}</strong> "
                       f"(${float(rec['amount']):.2f}) appeared "
                       f"<strong>{rec['count']}×</strong> this month",
            'severity': 'info',
        })

    uncategorized = qs.filter(category__isnull=True).count()
    if uncategorized > 3:
        insights.append({
            'type': 'uncategorized',
            'title': 'Uncategorized Transactions',
            'message': f"You have <strong>{uncategorized}</strong> uncategorized "
                       f"transactions. Categorize them for better analytics.",
            'severity': 'warning',
        })

    days_elapsed = (today - first_of_month).days + 1
    daily_avg = this_total / days_elapsed if days_elapsed > 0 else 0
    projected_monthly = daily_avg * 30
    insights.append({
        'type': 'daily_avg',
        'title': 'Daily Average',
        'message': f"You're spending <strong>${daily_avg:.2f}/day</strong> on average. "
                   f"Projected: <strong>${projected_monthly:.2f}</strong> this month",
        'severity': 'info',
    })

    return insights


def generate_recommendations(user) -> list[dict]:
    today = date.today()
    first_of_month = today.replace(day=1)
    qs = Transaction.objects.filter(user=user)
    this_month = qs.filter(date__gte=first_of_month)
    recs = []

    top_cat = (
        this_month.filter(type='expense')
        .values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
        .first()
    )
    if top_cat and float(top_cat['total']) > 0:
        recs.append({
            'type': 'reduce_spending',
            'message': f"Consider setting a budget for "
                       f"<strong>{top_cat['category__name'] or 'Uncategorized'}</strong> "
                       f"(${float(top_cat['total']):.2f} this month)",
            'action': 'Set Budget',
            'url': '#',
        })

    small_txns = this_month.filter(type='expense', amount__lt=5).count()
    if small_txns > 5:
        recs.append({
            'type': 'small_expenses',
            'message': f"You've made <strong>{small_txns}</strong> small purchases "
                       f"(<$5). They add up!",
            'action': 'Review',
            'url': '/transactions/',
        })

    return recs
