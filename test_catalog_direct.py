#!/usr/bin/env python
"""
Phase 1.3 - Direct Product Catalog Verification
Verify all endpoints work by direct database manipulation and response checking
"""

import os
import sys
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'client.settings')

# Add testserver to ALLOWED_HOSTS before Django setup
os.environ['ALLOWED_HOSTS'] = 'localhost,127.0.0.1,testserver'

sys.path.insert(0, '.')

django.setup()

from django.contrib.auth.models import User, Group
from rest_framework.test import APIRequestFactory, force_authenticate
from clientapp.api_views import ProductViewSet
from clientapp.models import Product, ProductPricing, ProductSEO
from rest_framework import status as http_status

def setup_test_environment():
    """Setup test user and environment"""
    user, created = User.objects.get_or_create(
        username='test_catalog_user',
        defaults={
            'email': 'test@catalog.com',
            'first_name': 'Test',
            'last_name': 'Catalog'
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Add to Production Team group
    pt_group, _ = Group.objects.get_or_create(name='Production Team')
    user.groups.add(pt_group)
    
    return user

def test_viewset_endpoints():
    """Test ProductViewSet endpoints"""
    print('\n' + '='*70)
    print('PRODUCT CATALOG API - ENDPOINT VERIFICATION')
    print('='*70)
    
    user = setup_test_environment()
    factory = APIRequestFactory()
    viewset = ProductViewSet()
    
    tests_passed = 0
    tests_failed = 0
    
    # TEST 1: Create Product
    print('\n[TEST 1] POST /api/v1/products/ - Create Product')
    try:
        request = factory.post('/api/v1/products/', {
            'name': 'Catalog Test Product',
            'internal_code': 'CAT-001',
            'short_description': 'Test product for catalog',
            'long_description': 'Long description for testing',
            'customization_level': 'semi_customizable',
            'primary_category': 'print-products',
            'base_price': '150.00',
            'status': 'draft'
        }, format='json')
        
        force_authenticate(request, user=user)
        viewset.request = request
        viewset.format_kwarg = None
        
        response = viewset.create(request)
        
        if response.status_code in [200, 201]:
            product_id = response.data['id']
            print(f'[PASS] Product created: ID={product_id}')
            tests_passed += 1
        else:
            print(f'[FAIL] Status {response.status_code}')
            tests_failed += 1
    except Exception as e:
        print(f'[ERROR] {str(e)}')
        tests_failed += 1
    
    # TEST 2: List Products
    print('\n[TEST 2] GET /api/v1/products/ - List Products')
    try:
        request = factory.get('/api/v1/products/')
        force_authenticate(request, user=user)
        viewset.request = request
        viewset.format_kwarg = None
        
        response = viewset.list(request)
        
        if response.status_code == 200:
            print(f'[PASS] Products listed')
            tests_passed += 1
        else:
            print(f'[FAIL] Status {response.status_code}')
            tests_failed += 1
    except Exception as e:
        print(f'[ERROR] {str(e)}')
        tests_failed += 1
    
    # Get latest product for remaining tests
    try:
        product = Product.objects.latest('id')
        product_id = product.id
    except:
        print('[SKIP] No products available for further testing')
        return tests_passed, tests_failed
    
    # TEST 3: Retrieve Product
    print(f'\n[TEST 3] GET /api/v1/products/{product_id}/ - Retrieve Product')
    try:
        request = factory.get(f'/api/v1/products/{product_id}/')
        force_authenticate(request, user=user)
        viewset.request = request
        viewset.format_kwarg = None
        viewset.kwargs = {'pk': product_id}
        
        response = viewset.retrieve(request, pk=product_id)
        
        if response.status_code == 200:
            print(f'[PASS] Product retrieved: {response.data["name"]}')
            tests_passed += 1
        else:
            print(f'[FAIL] Status {response.status_code}')
            tests_failed += 1
    except Exception as e:
        print(f'[ERROR] {str(e)}')
        tests_failed += 1
    
    # TEST 4: Update Product
    print(f'\n[TEST 4] PATCH /api/v1/products/{product_id}/ - Update Product')
    try:
        request = factory.patch(f'/api/v1/products/{product_id}/', {
            'name': 'Updated Catalog Product',
            'base_price': '200.00'
        }, format='json')
        force_authenticate(request, user=user)
        viewset.request = request
        viewset.format_kwarg = None
        viewset.kwargs = {'pk': product_id}
        
        response = viewset.partial_update(request, pk=product_id)
        
        if response.status_code == 200:
            print(f'[PASS] Product updated: {response.data["name"]}')
            tests_passed += 1
        else:
            print(f'[FAIL] Status {response.status_code}')
            tests_failed += 1
    except Exception as e:
        print(f'[ERROR] {str(e)}')
        tests_failed += 1
    
    # TEST 5: Calculate Price
    print(f'\n[TEST 5] POST /api/v1/products/{product_id}/calculate-price/ - Calculate Price')
    try:
        request = factory.post(f'/api/v1/products/{product_id}/calculate-price/', {
            'quantity': 1000,
            'include_breakdown': True
        }, format='json')
        force_authenticate(request, user=user)
        viewset.request = request
        viewset.format_kwarg = None
        viewset.kwargs = {'pk': product_id}
        
        response = viewset.calculate_price(request, pk=product_id)
        
        if response.status_code in [200, 201]:
            print(f'[PASS] Price calculated')
            tests_passed += 1
        else:
            print(f'[FAIL] Status {response.status_code}')
            tests_failed += 1
    except Exception as e:
        print(f'[ERROR] {str(e)}')
        tests_failed += 1
    
    # TEST 6: Save Draft
    print(f'\n[TEST 6] POST /api/v1/products/{product_id}/save-draft/ - Save Draft')
    try:
        request = factory.post(f'/api/v1/products/{product_id}/save-draft/', {}, format='json')
        force_authenticate(request, user=user)
        viewset.request = request
        viewset.format_kwarg = None
        viewset.kwargs = {'pk': product_id}
        
        response = viewset.save_draft(request, pk=product_id)
        
        if response.status_code in [200, 201]:
            print(f'[PASS] Draft saved')
            tests_passed += 1
        else:
            print(f'[FAIL] Status {response.status_code}')
            tests_failed += 1
    except Exception as e:
        print(f'[ERROR] {str(e)}')
        tests_failed += 1
    
    # TEST 7: Publish Product
    print(f'\n[TEST 7] POST /api/v1/products/{product_id}/publish/ - Publish Product')
    try:
        request = factory.post(f'/api/v1/products/{product_id}/publish/', {}, format='json')
        force_authenticate(request, user=user)
        viewset.request = request
        viewset.format_kwarg = None
        viewset.kwargs = {'pk': product_id}
        
        response = viewset.publish(request, pk=product_id)
        
        if response.status_code in [200, 201]:
            print(f'[PASS] Product published')
            tests_passed += 1
        else:
            print(f'[FAIL] Status {response.status_code}')
            tests_failed += 1
    except Exception as e:
        print(f'[ERROR] {str(e)}')
        tests_failed += 1
    
    # TEST 8: Change History
    print(f'\n[TEST 8] GET /api/v1/products/{product_id}/change-history/ - Get Change History')
    try:
        request = factory.get(f'/api/v1/products/{product_id}/change-history/')
        force_authenticate(request, user=user)
        viewset.request = request
        viewset.format_kwarg = None
        viewset.kwargs = {'pk': product_id}
        
        response = viewset.change_history(request, pk=product_id)
        
        if response.status_code == 200:
            print(f'[PASS] Change history retrieved')
            tests_passed += 1
        else:
            print(f'[FAIL] Status {response.status_code}')
            tests_failed += 1
    except Exception as e:
        print(f'[ERROR] {str(e)}')
        tests_failed += 1
    
    # TEST 9: Archive Product
    print(f'\n[TEST 9] POST /api/v1/products/{product_id}/archive/ - Archive Product')
    try:
        request = factory.post(f'/api/v1/products/{product_id}/archive/', {}, format='json')
        force_authenticate(request, user=user)
        viewset.request = request
        viewset.format_kwarg = None
        viewset.kwargs = {'pk': product_id}
        
        response = viewset.archive(request, pk=product_id)
        
        if response.status_code in [200, 201]:
            print(f'[PASS] Product archived')
            tests_passed += 1
        else:
            print(f'[FAIL] Status {response.status_code}')
            tests_failed += 1
    except Exception as e:
        print(f'[ERROR] {str(e)}')
        tests_failed += 1
    
    # TEST 10: Add Video
    print(f'\n[TEST 10] POST /api/v1/products/{product_id}/add-video/ - Add Video')
    try:
        request = factory.post(f'/api/v1/products/{product_id}/add-video/', {
            'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        }, format='json')
        force_authenticate(request, user=user)
        viewset.request = request
        viewset.format_kwarg = None
        viewset.kwargs = {'pk': product_id}
        
        response = viewset.add_video(request, pk=product_id)
        
        if response.status_code in [200, 201]:
            print(f'[PASS] Video added')
            tests_passed += 1
        else:
            print(f'[FAIL] Status {response.status_code} - {response.data}')
            tests_failed += 1
    except Exception as e:
        print(f'[ERROR] {str(e)}')
        tests_failed += 1
    
    return tests_passed, tests_failed

if __name__ == '__main__':
    passed, failed = test_viewset_endpoints()
    
    print('\n' + '='*70)
    print(f'RESULTS: {passed} passed, {failed} failed')
    print('='*70 + '\n')
    
    sys.exit(0 if failed == 0 else 1)
