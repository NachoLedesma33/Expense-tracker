from django.db import models
from django.conf import settings

CURRENCY_CHOICES = [
    ('USD', 'USD ($)'),
    ('EUR', 'EUR (€)'),
    ('GBP', 'GBP (£)'),
    ('MXN', 'MXN ($)'),
    ('ARS', 'ARS ($)'),
    ('BRL', 'BRL (R$)'),
    ('CLP', 'CLP ($)'),
    ('COP', 'COP ($)'),
]


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='profile'
    )
    preferred_currency = models.CharField(
        max_length=3, choices=CURRENCY_CHOICES, default='USD'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.user.username
