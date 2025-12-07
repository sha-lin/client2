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
    path('am/quotes/create/', views.create_quote, name='create_quote'),
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
    
    # Job Detail & Management
    path('job/<int:pk>/', views.job_detail, name='job_detail'),
    path('job/<int:pk>/add-note/', views.add_job_note, name='add_job_note'),
    path('job/<int:pk>/upload-file/', views.upload_job_file, name='upload_job_file'),
    path('job/<int:pk>/update-progress/', views.update_job_progress, name='update_job_progress'),
    path('job/<int:pk>/add-stage/', views.add_vendor_stage, name='add_vendor_stage'),
    
    # QC Inspection Start (placeholder if doesn't exist)
    path('qc-inspection/start/<int:job_id>/', views.qc_inspection_start, name='qc_inspection_start'),
    
    path('account-manager/quotes/', views.quote_management, name='quote_management'),
    path('account-manager/quotes/create/', views.create_multi_quote, name='create_multi_quote'),
    path('account-manager/catalog/', views.product_catalog, name='product_catalog'),
    path('account-manager/analytics/', views.analytics, name='analytics'),
    path('account-manager/base/', views.base_view, name='base_view'),
    path('quotes/<str:quote_id>/send/', views.send_quote, name='send_quote'),

    # ===== Production Team URLs =====
    path('production/quotes/', views.quote_review_queue, name='production_quote_review'),
    # Add this to your urlpatterns in clientapp/urls.py
   path('production/quotes/<str:quote_id>/cost-v2/', views.update_quote_costing_v2, name='production_quote_costing_v2'),
    path('production/catalog/', views.production_catalog, name='production_catalog'),
    # path('production/catalog/', views.product_detail, name='product_detail'),
    path('production/dashboard/', views.production2_dashboard, name='production2_dashboard'),
    path('notifications/', views.notifications, name='notifications'),
    
    path('base2/', views.base_view, name='base_view'),

    # Global search
    path('search/', views.search, name='search'),

    path('login-redirect/', views.login_redirect, name='login_redirect'),
    # Finance (restricted to Finance group)
    
    path('update-quote-status/', views.update_quote_status, name='update_quote_status'),
    path('production/jobs/', views.production_jobs, name='production_jobs'),
    # Product Image AJAX endpoints
path('ajax/product-image/<int:image_id>/', views.ajax_get_product_image, name='ajax_get_product_image'),
path('ajax/product-image/<int:image_id>/update/', views.ajax_update_product_image, name='ajax_update_product_image'),
path('ajax/product-image/<int:image_id>/delete/', views.ajax_delete_product_image, name='ajax_delete_product_image'),
path('ajax/product-image/<int:image_id>/replace/', views.ajax_replace_product_image, name='ajax_replace_product_image'),
    

    
    # Finance Dashboard
   
    # path('analytics_production/', views.analytics_dashboard, name='analytics_dashboard'),
    # path('dashboard/', views.analytics_dashboard, name='analytics_dashboard'),
    
    # Product Catalog 
    path('production/catalog/', views.production_catalog, name='production_catalog'),
    path('production/products/create/', views.product_create, name='product_create'),
    path('production/products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('production/products/<int:product_pk>/images/<int:image_pk>/delete/', 
         views.product_delete_image, name='product_delete_image'),
    path('production/products/images/<int:image_pk>/update/', 
         views.product_update_image_metadata, name='product_update_image_metadata'),
    path('production/products/calculate-pricing/', 
         views.calculate_pricing, name='calculate_pricing'),
      path('my-jobs/', views.my_jobs, name='my_jobs'),
    path('my-quotes/', views.my_quotes, name='my_quotes'),
    path('quote-detail/<str:quote_id>/', views.quote_detail2, name='quote_detail2'),

    path('quotes/<str:quote_id>/action/', views.quote_action, name='quote_action'),
    # Multi-Product Quotes
    path('quotes/', views.quotes_list, name='quotes_list'),
    # path('quotes/create/', views.create_quote, name='create_quote'),
    path('create/quote', views.quote_create, name='quote_create'),
    path('quotes/<str:quote_id>/download/', views.download_quote_pdf, name='download_quote_pdf'),
    # path('quotes/<str:quote_id>/', views.quote_detail, name='quote_detail'),
    # path('quotes/<str:quote_id>/edit/', views.quote_edit, name='quote_edit'),
    
    # Self-Quote Interface (Customer-facing)
    path('self-quote/', views.self_quote, name='self_quote'),
     path('api/product-price/<int:product_id>/', views.get_product_price, name='get_product_price'),
    
    # API endpoints for AJAX operations
    # path('api/products/search/', views.api_product_search, name='api_product_search'),
    # path('api/quotes/<str:quote_id>/add-item/', views.api_quote_add_item, name='api_quote_add_item'),
    # path('api/quotes/<str:quote_id>/remove-item/', views.api_quote_remove_item, name='api_quote_remove_item'),
    # path('api/quotes/<str:quote_id>/calculate/', views.api_quote_calculate, name='api_quote_calculate'),
     # Quote Sending & Approval
    # path('quotes/<str:quote_id>/send/', views.send_quote, name='send_quote'),
    path('quotes/approve/<str:token>/', views.quote_approval, name='quote_approval'),
    path('quotes/<str:quote_id>/approve/', views.handle_quote_approval, name='handle_quote_approval'),
    # LPO Management
    path('lpo/', views.lpo_list, name='lpo_list'),
    path('lpo/<str:lpo_number>/', views.lpo_detail, name='lpo_detail'),
    path('lpo/<str:lpo_number>/sync/', views.sync_to_quickbooks, name='sync_to_quickbooks'),
    

    path('vendor-comparison/<int:job_id>/', views.vendor_comparison, name='vendor_comparison'),
    path('ajax/create-vendor/', views.ajax_create_vendor, name='ajax_create_vendor'),
    # Quality control inspection page
    path('qc-inspection/<int:inspection_id>/', views.qc_inspection, name='qc_inspection'),
    path('vendors/', views.vendor_list, name='vendor_list'),
path('quality-control/', views.quality_control_list, name='quality_control_list'),
    # AJAX endpoints
    path('api/select-vendor/', views.select_vendor, name='select_vendor'),
    path('api/submit-qc/', views.submit_qc, name='submit_qc'),
    path('api/vendors/create/', views.ajax_create_vendor, name='ajax_create_vendor'),
    path('processes/', views.process_list, name='process_list'),
    path('processes/create/', views.process_create, name='process_create'),
    path('processes/<str:process_id>/edit/', views.process_edit, name='process_edit'),
    # path('processes/<str:process_id>/', views.process_detail, name='process_detail'),
    
    # AJAX endpoints
    path('ajax/generate-process-id/', views.ajax_generate_process_id, name='ajax_generate_process_id'),
    path('ajax/calculate-margin/', views.ajax_calculate_margin, name='ajax_calculate_margin'),
    path('delivery/', views.delivery_list, name='delivery_list'),
    # Job Completion
    # path('jobs/<int:pk>/complete/', views.complete_job, name='complete_job'),
    
    # Lead Conversion
    # path('leads/<str:lead_id>/convert-to-client/', views.convert_lead_to_client, name='convert_lead_to_client'),
    
    # Live Data API
    # path('api/dashboard/data/', views.get_dashboard_data, name='get_dashboard_data'),
    # path('api/notifications/', views.get_notifications, name='get_notifications'),
    # path('api/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
        # Admin Dashboard AJAX Endpoints
    path('admin/dismiss-alert/<int:alert_id>/', views.dismiss_alert, name='dismiss_alert'),
    path('admin/export-report/<str:report_type>/', views.export_dashboard_report, name='export_report'),
    
    # NEW: Process-Product Integration AJAX endpoint
    path('ajax/process/<int:process_id>/variables/', views.ajax_process_variables, name='ajax_process_variables'),

    # Add these to your urlpatterns
path('qc-inspection/<int:inspection_id>/', views.qc_inspection, name='qc_inspection'),
path('api/submit-qc/', views.submit_qc, name='submit_qc'),
path('delivery/handoff/<int:job_id>/', views.delivery_handoff, name='delivery_handoff'),
    path('api/submit-delivery-handoff/', views.submit_delivery_handoff, name='submit_delivery_handoff'),
    path('deliveries/', views.delivery_list, name='delivery_list'),
    path('job/<int:pk>/mark-completed/', views.complete_job, name='mark_job_completed'),
    path('production/settings/', views.production_settings, name='production_settings'),
]
