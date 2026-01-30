# clientapp/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/jobs/(?P<job_id>\w+)/$', consumers.JobUpdateConsumer.as_asgi()),
    re_path(r'ws/dashboard/(?P<dashboard_type>\w+)/$', consumers.DashboardConsumer.as_asgi()),
    re_path(r'ws/notifications/(?P<user_id>\w+)/$', consumers.NotificationConsumer.as_asgi()),
    re_path(r'ws/substitutions/(?P<substitution_id>\w+)/$', consumers.SubstitutionConsumer.as_asgi()),
]
