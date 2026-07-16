from django.urls import path
from .views import (
    TransactionListView,
    TransactionCreateView,
    TransactionUpdateView,
    TransactionDeleteView,
    CategoryCreateView,
    TransactionExportView,
    PredictCategoryView,
    LearnCategoryView,
)

app_name = 'transactions'

urlpatterns = [
    path('', TransactionListView.as_view(), name='list'),
    path('create/', TransactionCreateView.as_view(), name='create'),
    path('<int:pk>/update/', TransactionUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', TransactionDeleteView.as_view(), name='delete'),
    path('category/create/', CategoryCreateView.as_view(), name='category_create'),
    path('export/', TransactionExportView.as_view(), name='export'),
    path('predict-category/', PredictCategoryView.as_view(), name='predict_category'),
    path('learn-category/', LearnCategoryView.as_view(), name='learn_category'),
]
