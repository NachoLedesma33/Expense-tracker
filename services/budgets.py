from statistics import mean, stdev
from datetime import date
from collections import defaultdict
from django.db.models import Sum
from transactions.models import Transaction, Budget


def suggest_budgets(user, month=None):
    if month is None:
        month = date.today().replace(day=1)

    suggestions = []
    categories = list(user.categories.all())
    if not categories:
        return suggestions

    # 1) Bulk-fetch all expense amounts per category (for mean/stdev)
    history_qs = Transaction.objects.filter(
        user=user, category__in=categories, type='expense',
    ).values('category_id', 'amount')

    cat_amounts = defaultdict(list)
    for row in history_qs:
        cat_amounts[row['category_id']].append(float(row['amount']))

    # 2) Bulk-fetch existing budgets for this month
    existing_qs = Budget.objects.filter(user=user, month=month)
    existing_map = {b.category_id: b for b in existing_qs}

    # 3) Bulk-fetch current month spending per category
    current_qs = Transaction.objects.filter(
        user=user, category__in=categories, type='expense',
        date__year=month.year, date__month=month.month,
    ).values('category_id').annotate(total=Sum('amount'))

    current_map = {
        item['category_id']: float(item['total'] or 0)
        for item in current_qs
    }

    for cat in categories:
        amounts = cat_amounts.get(cat.id, [])
        if len(amounts) < 2:
            continue

        avg = mean(amounts)
        try:
            sd = stdev(amounts)
        except Exception:
            sd = avg * 0.3

        suggested = round(avg + sd, 2)
        existing = existing_map.get(cat.id)

        suggestions.append({
            'category_id': cat.id,
            'category_name': cat.name,
            'avg': round(avg, 2),
            'std': round(sd, 2),
            'suggested': suggested,
            'existing': float(existing.amount) if existing else None,
            'current': current_map.get(cat.id, 0),
            'confidence': 'high' if len(amounts) > 10 else 'medium',
        })

    return sorted(suggestions, key=lambda x: -x['suggested'])


def get_budgets_with_spending(user, month=None):
    if month is None:
        month = date.today().replace(day=1)

    budgets = Budget.objects.filter(user=user, month=month).select_related('category')

    # Bulk-fetch spending for all budgets in one query
    cat_ids = [b.category_id for b in budgets]
    if cat_ids:
        spent_qs = Transaction.objects.filter(
            user=user, category_id__in=cat_ids, type='expense',
            date__year=month.year, date__month=month.month,
        ).values('category_id').annotate(total=Sum('amount'))
        spent_map = {item['category_id']: float(item['total'] or 0) for item in spent_qs}
    else:
        spent_map = {}

    result = []
    for b in budgets:
        spent = spent_map.get(b.category_id, 0)
        pct = round((spent / float(b.amount)) * 100, 1) if float(b.amount) > 0 else 0
        result.append({
            'budget': b,
            'spent': spent,
            'remaining': float(b.amount) - spent,
            'percentage': pct,
        })
    return result
