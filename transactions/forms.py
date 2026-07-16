from django import forms
from django.core.validators import MinValueValidator
from .models import Transaction, Category, Budget


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['title', 'amount', 'type', 'category', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
        error_messages = {
            'title': {'required': 'Title is required.'},
            'amount': {'required': 'Amount is required.', 'invalid': 'Enter a valid number.'},
            'type': {'required': 'Select a transaction type.'},
            'date': {'required': 'Select a date.'},
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['category'].required = False
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)
        else:
            self.fields['category'].queryset = Category.objects.none()
        self.fields['amount'].validators.append(MinValueValidator(0.01))

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        return amount

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise forms.ValidationError('Title is required.')
        if len(title) < 2:
            raise forms.ValidationError('Title must be at least 2 characters.')
        return title


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        error_messages = {
            'name': {
                'required': 'Category name is required.',
            },
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Category name is required.')
        if len(name) < 2:
            raise forms.ValidationError('Name must be at least 2 characters.')
        if self.user and Category.objects.filter(name=name, user=self.user).exists():
            raise forms.ValidationError('You already have a category with this name.')
        return name


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['category', 'amount', 'month']
        widgets = {
            'month': forms.DateInput(attrs={'type': 'month'}),
        }
        error_messages = {
            'category': {'required': 'Select a category.'},
            'amount': {'required': 'Budget amount is required.'},
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)
        else:
            self.fields['category'].queryset = Category.objects.none()
        self.fields['amount'].validators.append(MinValueValidator(0.01))

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        return amount
