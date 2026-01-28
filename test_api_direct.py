#!/usr/bin/env python
"""
Phase 1.3 - Direct API Endpoint Testing
Test the ProductViewSet endpoints directly
"""

import os
import sys
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'client.settings')
sys.path.insert(0, '/home/client')

django.setup()

from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from rest_framework import status
from clientapp.models import Product, ProductPricing, ProductSEO

def setup_test_user():
    """Create test user with Production Team role"""
    user, created = User.objects.get_or_create(
        username='test_integration_user',
        defaults={
            'email': 'test_integration@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Add to Production Team group
    pt_group, _ = Group.objects.get_or_create(name='Production Team')
    user.groups.add(pt_group)
    
    return user

def test_api_endpoints():
    """Test all API endpoints"""
    print('\n' + '='*70)
    print('PHASE 1.3 - PRODUCTVIEWSET API ENDPOINT TESTING')
    print('='*70)
    
    user = setup_test_user()
    client = APIClient()
    client.force_authenticate(user=user)
    
    results = {
        'passed': 0,
        'failed': 0,
        'tests': []
    }
    
    # TEST 1: Create Product (POST /api/v1/products/)
    print('\n[TEST 1] Create Product...')
    try:
        data = {
            'name': 'Test Business Cards',
            'internal_code': 'TEST-BC-001',
            'short_description': 'Quality business cards for professionals',
            'long_description': 'Premium business cards with full-color print',
            'customization_level': 'semi_customizable',
            'primary_category': 'print-products',
            'base_price': '250.00',
            'status': 'draft'
        }
        
        response = client.post('/api/v1/products/', data, format='json')
        
        if response.status_code in [200, 201]:
            product = response.json()
            product_id = product['id']
            print(f'[PASS] Product created: {product_id} - {product["name"]}')
            results['passed'] += 1
            results['tests'].append(('Create Product', 'PASS'))
        else:
            print(f'[FAIL] Status {response.status_code}: {response.data}')
            results['failed'] += 1
            results['tests'].append(('Create Product', 'FAIL'))
            return results  # Stop if create fails
    except Exception as e:
        print(f'[ERROR] {str(e)}')
        results['failed'] += 1
        results['tests'].append(('Create Product', 'ERROR'))
        return results
    
    # TEST 2: Retrieve Product (GET /api/v1/products/{id}/)
    print(f'\n[TEST 2] Retrieve Product {product_id}...')
    try:
        response = client.get(f'/api/v1/products/{product_id}/')
        
        if response.status_code == 200:
            product = response.json()
            print(f'[PASS] Product retrieved: {product["name"]}')
            print(f'       Status: {product["status"]}, Price: {product["base_price"]}')
            results['passed'] += 1
            results['tests'].append(('Retrieve Product', 'PASS'))
        else:
            print(f'[FAIL] Status {response.status_code}')
            results['failed'] += 1
            results['tests'].append(('Retrieve Product', 'FAIL'))
    except Exception as e:
        print(f'[ERROR] {str(e)}')
        results['failed'] += 1
        results['tests'].append(('Retrieve Product', 'ERROR'))
    
    # TEST 3: List Products (GET /api/v1/products/)
    print('\n[TEST 3] List Products...')
    try:
        response = client.get('/api/v1/products/')
        
        if response.status_code == 200:
            products = response.json()
            count = products.get('count', len(products) if isinstance(products, list) else 1)
            print(f'[PASS] Products listed: {count} total')
            results['passed'] += 1
            results['tests'].append(('List Products', 'PASS'))
        else:
            print(f'[FAIL] Status {response.status_code}')
            results['failed'] += 1
            results['tests'].append(('List Products', 'FAIL'))
    except Exception as e:
        print(f'[ERROR] {str(e)}')
        results['failed'] += 1
        results['tests'].append(('List Products', 'ERROR'))
    
    # TEST 4: Update Product (PATCH /api/v1/products/{id}/)
    print(f'\n[TEST 4] Update Product {product_id}...')
    try:
        data = {
            'name': 'Premium Business Cards',
            'short_description': 'Updated description',
            'base_price': '300.00'
        }
        
        response = client.patch(f'/api/v1/products/{product_id}/', data, format='json')
        
        if response.status_code in [200, 201]:
            product = response.json()
            print(f'[PASS] Product updated: {product["name"]}')
            print(f'       New Price: {product["base_price"]}')
            results['passed'] += 1
            results['tests'].append(('Update Product', 'PASS'))
        else:
            print(f'[FAIL] Status {response.status_code}: {response.data}')
            results['failed'] += 1
            results['tests'].append(('Update Product', 'FAIL'))
    except Exception as e:
        print(f'[ERROR] {str(e)}')
        results['failed'] += 1
        results['tests'].append(('Update Product', 'ERROR'))
    
    # TEST 5: Save Draft (POST /api/v1/products/{id}/save-draft/)
    print(f'\n[TEST 5] Save Draft {product_id}...')
    try:
        response = client.post(f'/api/v1/products/{product_id}/save-draft/', {}, format='json')
        
        if response.status_code in [200, 201]:
            product = response.json()
            print(f'[PASS] Product saved as draft: {product["status"]}')
            results['passed'] += 1
            results['tests'].append(('Save Draft', 'PASS'))
        else:
            print(f'[FAIL] Status {response.status_code}: {response.data}')
            results['failed'] += 1
            results['tests'].append(('Save Draft', 'FAIL'))
    except Exception as e:
        print(f'[ERROR] {str(e)}')
        results['failed'] += 1
        results['tests'].append(('Save Draft', 'ERROR'))
    
    # TEST 6: Calculate Price (POST /api/v1/products/{id}/calculate-price/)
    print(f'\n[TEST 6] Calculate Price for {product_id}...')
    try:
        data = {
            'quantity': 1000,
            'include_breakdown': True
        }
        
        response = client.post(f'/api/v1/products/{product_id}/calculate-price/', data, format='json')
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f'[PASS] Price calculated')
            print(f'       Unit Price: {result.get("unit_price", "N/A")}')
            print(f'       Total Price: {result.get("total_price", "N/A")}')
            results['passed'] += 1
            results['tests'].append(('Calculate Price', 'PASS'))
        else:
            print(f'[FAIL] Status {response.status_code}: {response.data}')
            results['failed'] += 1
            results['tests'].append(('Calculate Price', 'FAIL'))
    except Exception as e:
        print(f'[ERROR] {str(e)}')
        results['failed'] += 1
        results['tests'].append(('Calculate Price', 'ERROR'))
    
    # TEST 7: Publish Product (POST /api/v1/products/{id}/publish/)
    print(f'\n[TEST 7] Publish Product {product_id}...')
    try:
        response = client.post(f'/api/v1/products/{product_id}/publish/', {}, format='json')
        
        if response.status_code in [200, 201]:
            product = response.json()
            print(f'[PASS] Product published: {product["status"]}')
            results['passed'] += 1
            results['tests'].append(('Publish Product', 'PASS'))
        else:
            print(f'[FAIL] Status {response.status_code}: {response.data}')
            results['failed'] += 1
            results['tests'].append(('Publish Product', 'FAIL'))
    except Exception as e:
        print(f'[ERROR] {str(e)}')
        results['failed'] += 1
        results['tests'].append(('Publish Product', 'ERROR'))
    
    # TEST 8: Change History (GET /api/v1/products/{id}/change-history/)
    print(f'\n[TEST 8] Get Change History for {product_id}...')
    try:
        response = client.get(f'/api/v1/products/{product_id}/change-history/')
        
        if response.status_code == 200:
            history = response.json()
            count = history.get('count', len(history) if isinstance(history, list) else 1)
            print(f'[PASS] Change history retrieved: {count} entries')
            results['passed'] += 1
            results['tests'].append(('Change History', 'PASS'))
        else:
            print(f'[FAIL] Status {response.status_code}')
            results['failed'] += 1
            results['tests'].append(('Change History', 'FAIL'))
    except Exception as e:
        print(f'[ERROR] {str(e)}')
        results['failed'] += 1
        results['tests'].append(('Change History', 'ERROR'))
    
    # TEST 9: Archive Product (POST /api/v1/products/{id}/archive/)
    print(f'\n[TEST 9] Archive Product {product_id}...')
    try:
        response = client.post(f'/api/v1/products/{product_id}/archive/', {}, format='json')
        
        if response.status_code in [200, 201]:
            product = response.json()
            print(f'[PASS] Product archived: {product["status"]}')
            results['passed'] += 1
            results['tests'].append(('Archive Product', 'PASS'))
        else:
            print(f'[FAIL] Status {response.status_code}: {response.data}')
            results['failed'] += 1
            results['tests'].append(('Archive Product', 'FAIL'))
    except Exception as e:
        print(f'[ERROR] {str(e)}')
        results['failed'] += 1
        results['tests'].append(('Archive Product', 'ERROR'))
    
    # TEST 10: Add Video (POST /api/v1/products/{id}/add-video/)
    # Need to create a new product for this since archived can't have videos
    print('\n[TEST 10] Creating new product for video test...')
    try:
        data = {
            'name': 'Video Test Product',
            'internal_code': 'TEST-VID-001',
            'short_description': 'Product with video',
            'long_description': 'Test product for video',
            'customization_level': 'non_customizable',
            'primary_category': 'promotional',
            'base_price': '100.00',
            'status': 'draft'
        }
        
        response = client.post('/api/v1/products/', data, format='json')
        
        if response.status_code in [200, 201]:
            video_product = response.json()
            video_product_id = video_product['id']
            
            # Now add video
            print(f'\n[TEST 10] Add Video to Product {video_product_id}...')
            video_data = {
                'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
            }
            
            response = client.post(f'/api/v1/products/{video_product_id}/add-video/', video_data, format='json')
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f'[PASS] Video added: {result.get("video_url", "N/A")}')
                results['passed'] += 1
                results['tests'].append(('Add Video', 'PASS'))
            else:
                print(f'[FAIL] Status {response.status_code}: {response.data}')
                results['failed'] += 1
                results['tests'].append(('Add Video', 'FAIL'))
        else:
            print(f'[FAIL] Could not create test product: {response.status_code}')
            results['failed'] += 1
            results['tests'].append(('Add Video', 'FAIL'))
    except Exception as e:
        print(f'[ERROR] {str(e)}')
        results['failed'] += 1
        results['tests'].append(('Add Video', 'ERROR'))
    
    # Print summary
    print('\n' + '='*70)
    print('TEST SUMMARY')
    print('='*70)
    
    for test_name, status_str in results['tests']:
        status_symbol = '[PASS]' if status_str == 'PASS' else '[FAIL]' if status_str == 'FAIL' else '[ERR]'
        print(f'{status_symbol} {test_name}')
    
    print('\n' + '='*70)
    print(f'RESULTS: {results["passed"]} passed, {results["failed"]} failed')
    print('='*70 + '\n')
    
    return results['failed'] == 0

if __name__ == '__main__':
    success = test_api_endpoints()
    sys.exit(0 if success else 1)
