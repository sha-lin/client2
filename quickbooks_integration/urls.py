from django.urls import path
from . import views

urlpatterns = [
    path('accounting/', views.accounting_dashboard, name='accounting_dashboard'),

    path('connect/', views.connect_quickbooks, name='qb_connect'),
    path('callback/', views.quickbooks_callback, name='qb_callback'),
    path('invoices/', views.get_invoices, name='qb_invoices'),
    path('balance-sheet/', views.get_balance_sheet, name='qb_balance_sheet'),
    # path('profit-loss/', views.get_profit_and_loss, name='get_profit_and_loss'),
]
