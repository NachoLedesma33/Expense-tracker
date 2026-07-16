from statistics import mean, stdev
from datetime import date, timedelta
from django.db.models import Sum
from transactions.models import Transaction, Budget


def suggest_budgets(user, month=None):
    if month is None:
        month = date.today()
        month = month.replace(day=1)

    suggestions = []
    categories = user.categories.all()

    for cat in categories:
        history = Transaction.objects.filter(
            user=user, category=cat, type='expense',
        ).values_list('amount', flat=True)

        amounts = [float(a) for a in history]
        if len(amounts) < 2:
            continue

        avg = mean(amounts)
        try:
            sd = stdev(amounts)
        except Exception:
            sd = avg * 0.3

        suggested = round(avg + sd, 2)

        existing = Budget.objects.filter(
            user=user, category=cat, month=month,
        ).first()

        suggestions.append({
            'category_id': cat.id,
            'category_name': cat.name,
            'avg': round(avg, 2),
            'std': round(sd, 2),
            'suggested': suggested,
            'existing': float(existing.amount) if existing else None,
            'current': float(
                Transaction.objects.filter(
                    user=user, category=cat, type='expense',
                    date__year=month.year, date__month=month.month,
                ).aggregate(t=Sum('amount'))['t'] or 0
            ),
            'confidence': 'high' if len(amounts) > 10 else 'medium',
        })

    return sorted(suggestions, key=lambda x: -x['suggested'])


def get_budgets_with_spending(user, month=None):
    if month is None:
        month = date.today()
        month = month.replace(day=1)

    budgets = Budget.objects.filter(user=user, month=month).select_related('category')
    result = []
    for b in budgets:
        spent = float(
            Transaction.objects.filter(
                user=user, category=b.category, type='expense',
                date__year=month.year, date__month=month.month,
            ).aggregate(t=Sum('amount'))['t'] or 0
        )
        pct = round((spent / float(b.amount)) * 100, 1) if float(b.amount) > 0 else 0
        result.append({
            'budget': b,
            'spent': spent,
            'remaining': float(b.amount) - spent,
            'percentage': pct,
        })
    return result
