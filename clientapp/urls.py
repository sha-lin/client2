from django.urls import path
from . import views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('leads/', views.lead_intake, name='lead_intake'),
    path('leads/qualify/<str:lead_id>/', views.qualify_lead, name='qualify_lead'),
    path('leads/convert/<str:lead_id>/', views.convert_lead, name='convert_lead'),
    path('onboarding/', views.client_onboarding, name='client_onboarding'),
    path('clients/', views.client_list, name='client_list'),
    path('client_profile/<int:pk>/', views.client_profile, name='client_profile'),
    path('check-duplicate-lead/', views.check_duplicate_lead, name='check_duplicate_lead'),
    path('create_quote/',views.create_quote, name='create_quote' ),
    path('jobs/new/', views.create_job, name='create_job'),
]
