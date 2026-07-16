from django.db import models
from django.conf import settings


class Budget(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='budgets',
    )
    category = models.ForeignKey(
        'Category', on_delete=models.CASCADE,
        related_name='budgets',
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    month = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'category', 'month'],
                name='unique_budget_per_month',
            )
        ]
        ordering = ['category__name']

    def __str__(self):
        return f'{self.category.name}: ${self.amount} ({self.month.strftime("%b %Y")})'


class Category(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='categories'
    )

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['name', 'user'], name='unique_category_per_user')
        ]

    def __str__(self):
        return self.name


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='transactions'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='transactions'
    )
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f'{self.title} ({self.get_type_display()}: ${self.amount})'
