#!/usr/bin/env python
"""
Debug script to test Jobs API endpoints and diagnose AM jobs page issues
"""
import os
import django
import json
from django.contrib.auth.models import User, Group
from django.test import Client

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clientapp.models import Job, Client as ClientModel
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

print("=" * 80)
print("JOBS API DEBUG SCRIPT")
print("=" * 80)

# 1. Check if any jobs exist
print("\n1. CHECKING JOBS IN DATABASE:")
print("-" * 80)
jobs = Job.objects.all()
print(f"   Total jobs in database: {jobs.count()}")
if jobs.exists():
    for job in jobs[:3]:
        print(f"   - Job #{job.job_number}: {job.job_name} (Status: {job.status})")
else:
    print("   ⚠️  No jobs found in database!")

# 2. Check Production Team group
print("\n2. CHECKING PRODUCTION TEAM GROUP:")
print("-" * 80)
pt_group = Group.objects.filter(name='Production Team').first()
if pt_group:
    pt_users = pt_group.user_set.all()
    print(f"   Production Team group exists")
    print(f"   Members: {pt_users.count()}")
    for user in pt_users[:3]:
        print(f"   - {user.get_full_name() or user.username} (ID: {user.id})")
else:
    print("   ⚠️  Production Team group does NOT exist!")

# 3. Check Account Manager group
print("\n3. CHECKING ACCOUNT MANAGER GROUP:")
print("-" * 80)
am_group = Group.objects.filter(name='Account Manager').first()
if am_group:
    am_users = am_group.user_set.all()
    print(f"   Account Manager group exists")
    print(f"   Members: {am_users.count()}")
    for user in am_users[:3]:
        print(f"   - {user.get_full_name() or user.username} (ID: {user.id})")
else:
    print("   ⚠️  Account Manager group does NOT exist!")

# 4. Get an AM user for testing
print("\n4. SETTING UP TEST USER:")
print("-" * 80)
test_am = am_users.first() if am_group and am_users.exists() else None
if test_am:
    print(f"   Using AM user: {test_am.get_full_name() or test_am.username} (ID: {test_am.id})")
    
    # Get or create token
    token, created = Token.objects.get_or_create(user=test_am)
    print(f"   Token: {token.key[:20]}...")
else:
    print("   ⚠️  No Account Manager users found!")

# 5. Test API endpoint
if test_am:
    print("\n5. TESTING API ENDPOINTS:")
    print("-" * 80)
    
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    
    # Test GET /api/jobs/
    print("\n   Testing: GET /api/jobs/")
    response = client.get('/api/jobs/')
    print(f"   Status: {response.status_code}")
    print(f"   Headers: Authorization set")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Success!")
        print(f"   Response type: {type(data).__name__}")
        if isinstance(data, dict):
            print(f"   Keys: {list(data.keys())}")
            if 'results' in data:
                print(f"   Jobs returned: {len(data['results'])}")
        elif isinstance(data, list):
            print(f"   Jobs returned: {len(data)}")
    else:
        print(f"   ✗ Error!")
        print(f"   Response: {response.text[:200]}")
    
    # Test GET /api/users/?groups=Production%20Team
    print("\n   Testing: GET /api/users/?groups=Production%20Team")
    response = client.get('/api/users/?groups=Production%20Team')
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Success!")
        if isinstance(data, dict) and 'results' in data:
            print(f"   PT Users returned: {len(data['results'])}")
        elif isinstance(data, list):
            print(f"   PT Users returned: {len(data)}")
    else:
        print(f"   ✗ Error!")
        print(f"   Response: {response.text[:200]}")

# 6. Check permissions
print("\n6. CHECKING API PERMISSIONS:")
print("-" * 80)

from clientapp.api_views import JobViewSet
from rest_framework.test import APIRequestFactory
from django.contrib.auth.models import AnonymousUser

factory = APIRequestFactory()
viewset = JobViewSet()

# Check permission classes
print(f"   JobViewSet permission_classes: {viewset.permission_classes}")

# Check if AM can access
if test_am:
    print(f"\n   Can AM user access jobs?")
    request = factory.get('/api/jobs/')
    request.user = test_am
    viewset.request = request
    
    try:
        for perm_class in viewset.permission_classes:
            perm = perm_class()
            has_perm = perm.has_permission(request, viewset)
            print(f"   - {perm_class.__name__}: {has_perm}")
    except Exception as e:
        print(f"   Error checking permissions: {e}")

print("\n" + "=" * 80)
print("DEBUG COMPLETE")
print("=" * 80)
