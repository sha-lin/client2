#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'client.settings')
django.setup()

from django.urls import resolve, reverse
from django.test import Client
import json

# Test if the URL resolves
try:
    match = resolve('/api/v1/products/51/upload-gallery-images/')
    print(f"✓ URL resolves to: {match.view_name}")
    print(f"  App: {match.app_name}")
    print(f"  Namespace: {match.namespace}")
except Exception as e:
    print(f"✗ URL does NOT resolve: {e}")

# Test with a client
client = Client()

# Get a token first
from django.contrib.auth.models import User
user = User.objects.filter(groups__name='Production Team').first()
if user:
    print(f"\nUsing user: {user.username}")
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    token = str(refresh.access_token)
    
    # Try a GET first to verify auth
    response = client.get(
        '/api/v1/products/51/',
        HTTP_AUTHORIZATION=f'Bearer {token}'
    )
    print(f"GET /api/v1/products/51/ - Status: {response.status_code}")
    
    # Now try the upload endpoint
    response = client.post(
        '/api/v1/products/51/upload-gallery-images/',
        HTTP_AUTHORIZATION=f'Bearer {token}',
        content_type='application/json'
    )
    print(f"POST /api/v1/products/51/upload-gallery-images/ - Status: {response.status_code}")
    if response.status_code != 201:
        print(f"Response: {response.content[:500]}")
else:
    print("No Production Team user found")
