from django import template
from users.models import CURRENCY_CHOICES

register = template.Library()

CURRENCY_SYMBOLS = {
    'USD': '$',
    'EUR': '\u20ac',
    'GBP': '\u00a3',
    'MXN': '$',
    'ARS': '$',
    'BRL': 'R$',
    'CLP': '$',
    'COP': '$',
}


@register.filter
def currency(value, user=None):
    symbol = '$'
    if user and user.is_authenticated:
        try:
            code = user.profile.preferred_currency
            symbol = CURRENCY_SYMBOLS.get(code, '$')
        except Exception:
            pass
    return f'{symbol}{value}'
