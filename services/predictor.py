from datetime import date, timedelta
from django.db.models import Sum
from django.db.models.functions import TruncDate
from transactions.models import Transaction


def linear_regression(xs: list[float], ys: list[float]) -> tuple[float, float]:
    n = len(xs)
    if n < 2:
        return 0.0, 0.0
    sum_x = sum(xs)
    sum_y = sum(ys)
    sum_xy = sum(x * y for x, y in zip(xs, ys))
    sum_xx = sum(x * x for x in xs)
    denom = n * sum_xx - sum_x * sum_x
    if denom == 0:
        return 0.0, 0.0
    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    return slope, intercept


def predict_month_end(user) -> dict:
    today = date.today()
    first = today.replace(day=1)

    # last day of current month
    if today.month == 12:
        last_day = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(today.year, today.month + 1, 1) - timedelta(days=1)
    days_in_month = last_day.day

    daily_totals = (
        Transaction.objects.filter(
            user=user, type='expense',
            date__gte=first, date__lte=today,
        )
        .annotate(d=TruncDate('date'))
        .values('d')
        .annotate(total=Sum('amount'))
        .order_by('d')
    )

    cumulative = []
    day_numbers = []
    running = 0.0
    for entry in daily_totals:
        running += float(entry['total'])
        cumulative.append(running)
        day_numbers.append(entry['d'].day)

    if not cumulative:
        return {
            'current_total': 0,
            'projected_total': 0,
            'remaining_days': days_in_month - today.day,
            'daily_average': 0,
            'confidence': 'low',
        }

    current_total = cumulative[-1]
    if len(day_numbers) < 2:
        daily_avg = current_total / today.day if today.day > 0 else 0
        projected = daily_avg * days_in_month
        return {
            'current_total': current_total,
            'projected_total': round(projected, 2),
            'remaining_days': days_in_month - today.day,
            'daily_average': round(daily_avg, 2),
            'confidence': 'low',
        }

    slope, intercept = linear_regression(day_numbers, cumulative)
    projected = slope * days_in_month + intercept
    daily_avg = current_total / today.day if today.day > 0 else 0

    return {
        'current_total': current_total,
        'projected_total': round(max(0, projected), 2),
        'remaining_days': days_in_month - today.day,
        'daily_average': round(daily_avg, 2),
        'confidence': 'high' if len(day_numbers) > 15 else 'medium',
    }
