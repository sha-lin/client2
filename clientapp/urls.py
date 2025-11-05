# clients/urls.py
from django.urls import path
from . import views

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
    
    # Quotes
    path('quotes/create/', views.create_quote, name='create_quote'),
    # path('quotes/', views.quotes_list, name='quotes_list'),
    path('quotes/<str:quote_id>/', views.quote_detail, name='quote_detail'),
    path('quotes/<str:quote_id>/update-status/', views.update_quote_status, name='update_quote_status'),
    path('quotes/<str:quote_id>/delete/', views.delete_quote, name='delete_quote'),
    
    # API endpoints for quotes
    path('api/client/<int:client_id>/', views.get_client_details, name='get_client_details'),
    path('api/lead/<int:lead_id>/', views.get_lead_details, name='get_lead_details'),
    path('api/quotes/save-draft/', views.save_quote_draft, name='save_quote_draft'),
    
    # Jobs
    path('jobs/create/', views.create_job, name='create_job'),
    path('job/<int:pk>/', views.job_detail, name='job_detail'),
    
    path('account-manager/quotes/', views.quote_management, name='quote_management'),
    path('account-manager/catalog/', views.product_catalog, name='product_catalog'),
    path('account-manager/dashboard/', views.production_dashboard, name='production_dashboard'),
    path('account-manager/analytics/', views.analytics, name='analytics'),
    path('account-manager/base/', views.base_view, name='base_view'),

    # ===== Production Team URLs =====
    path('production/quotes/', views.quote_review_queue, name='production_quote_review'),
    path('production/catalog/', views.production_catalog, name='production_catalog'),
    path('production/dashboard/', views.production2_dashboard, name='production_dashboard2'),
    path('production/analytics/', views.production_analytics, name='production_analytics'),
    
    path('base2/', views.base_view, name='base_view'),

]
