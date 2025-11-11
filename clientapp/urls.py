# clients/urls.py
from django.urls import path
from . import views
from django.urls import reverse
from django.shortcuts import redirect
from django.urls import include

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Leads
    path('leads/', views.lead_intake, name='lead_intake'),
    path('leads/qualify/<str:lead_id>/', views.qualify_lead, name='qualify_lead'),
    path('leads/convert/<str:lead_id>/', views.convert_lead, name='convert_lead'),
    path('leads/check-duplicate/', views.check_duplicate_lead, name='check_duplicate_lead'),
    
    # Clients
    path('clients/', views.client_list, name='client_list'),
    path('clients/onboarding/', views.client_onboarding, name='client_onboarding'),
    path('clients/<int:pk>/', views.client_profile, name='client_profile'),
    path('clients/<int:pk>/edit/', views.edit_client, name='edit_client'),
    path('clients/<int:pk>/edit/', views.edit_client, name='edit_client'),
    
    # Quotes
    path('quotes/create/', views.create_quote, name='create_quote'),
    # path('quotes/', views.quotes_list, name='quotes_list'),
    path('quotes/<str:quote_id>/', views.quote_detail, name='quote_detail'),
    path('quotes/<str:quote_id>/update-status/', views.update_quote_status, name='update_quote_status'),
    path('quotes/<str:quote_id>/delete/', views.delete_quote, name='delete_quote'),
    path('production/quotes/<str:quote_id>/cost/', views.update_quote_costing, name='production_quote_costing'),
    
    # API endpoints for quotes
    path('api/client/<int:client_id>/', views.get_client_details, name='get_client_details'),
    path('api/lead/<int:lead_id>/', views.get_lead_details, name='get_lead_details'),
    path('api/quotes/save-draft/', views.save_quote_draft, name='save_quote_draft'),
    
    # Jobs
    path('jobs/create/', views.create_job, name='create_job'),
    path('job/<int:pk>/', views.job_detail, name='job_detail'),
    
    path('account-manager/quotes/', views.quote_management, name='quote_management'),
    path('account-manager/catalog/', views.product_catalog, name='product_catalog'),
    path('account-manager/analytics/', views.analytics, name='analytics'),
    path('account-manager/base/', views.base_view, name='base_view'),

    # ===== Production Team URLs =====
    path('production/quotes/', views.quote_review_queue, name='production_quote_review'),
    path('production/catalog/', views.production_catalog, name='production_catalog'),
    path('production/dashboard/', views.production2_dashboard, name='production_dashboard2'),
    path('production/analytics/', views.production_analytics, name='production_analytics'),
    path('notifications/', views.notifications, name='notifications'),
    
    path('base2/', views.base_view, name='base_view'),

    # Global search
    path('search/', views.search, name='search'),

    path('login-redirect/', views.login_redirect, name='login_redirect'),
    # Finance (restricted to Finance group)
    path('finance/', views.finance_dashboard, name='finance_dashboard'),
    path('finance/client/<int:client_id>/', views.finance_client_entity, name='finance_client_entity'),
    path('ledger/', include('django_ledger.urls', namespace='django_ledger')),
    path('update-quote-status/', views.update_quote_status, name='update_quote_status'),
    path('production/jobs/', views.production_jobs, name='production_jobs'),


]
