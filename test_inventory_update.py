#!/usr/bin/env python
"""
Quick test to verify inventory update endpoint works.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'client.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth.models import User, Group
from clientapp.models import Product, ProductChangeHistory
from clientapp.api_views import ProductViewSet
from decimal import Decimal

def test_update_inventory():
    print("\n" + "="*60)
    print("INVENTORY UPDATE API TEST")
    print("="*60)
    
    # Setup test data
    print("\n[1] Setting up test data...")
    
    # Get or create Production Team group
    pt_group, _ = Group.objects.get_or_create(name='Production Team')
    
    # Get or create test user
    user, _ = User.objects.get_or_create(
        username='test_pt_user',
        defaults={'email': 'test@example.com'}
    )
    user.groups.add(pt_group)
    print(f"  ✓ Using user: {user.username}")
    
    # Get or create test product
    product, created = Product.objects.get_or_create(
        id=51,
        defaults={
            'name': 'Test Inventory Product',
            'customization_level': 'semi_customizable',
            'base_price': Decimal('100.00'),
            'stock_quantity': 10,
            'min_stock_level': 5,
            'reorder_quantity': 20,
            'created_by': user,
            'updated_by': user,
            'status': 'draft'
        }
    )
    
    if created:
        print(f"  ✓ Created product: {product.name} (ID: {product.id})")
    else:
        print(f"  ✓ Using product: {product.name} (ID: {product.id})")
    
    # Test API call
    print("\n[2] Testing inventory update API...")
    
    factory = APIRequestFactory()
    request_data = {
        'stock_quantity': 50,
        'min_stock_level': 10,
        'reorder_quantity': 30,
        'backorder_allowed': True
    }
    
    request = factory.post(
        f'/api/v1/products/{product.id}/update_inventory/',
        request_data,
        format='json'
    )
    force_authenticate(request, user=user)
    
    viewset = ProductViewSet()
    viewset.request = request
    viewset.format_kwarg = None
    viewset.kwargs = {'pk': product.id}
    
    try:
        response = viewset.update_inventory(request, pk=product.id)
        print(f"  ✓ API response status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"  ✓ Response data: {response.data}")
        else:
            print(f"  ✗ Unexpected status: {response.status_code}")
            print(f"    {response.data}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Verify updates
    print("\n[3] Verifying product updates...")
    product.refresh_from_db()
    
    success = True
    fields = [
        ('stock_quantity', product.stock_quantity, 50),
        ('min_stock_level', product.min_stock_level, 10),
        ('reorder_quantity', product.reorder_quantity, 30),
        ('backorder_allowed', product.backorder_allowed, True),
    ]
    
    for name, actual, expected in fields:
        if actual == expected:
            print(f"  ✓ {name}: {actual}")
        else:
            print(f"  ✗ {name}: Expected {expected}, got {actual}")
            success = False
    
    # Check change history
    print("\n[4] Verifying change history...")
    changes = ProductChangeHistory.objects.filter(product=product).order_by('-changed_at')
    
    if changes.exists():
        print(f"  ✓ Found {changes.count()} change records")
        for change in changes[:3]:
            print(f"    - {change.field_changed}: {change.old_value} → {change.new_value}")
    else:
        print("  ⚠ No change history found")
    
    # Summary
    print("\n" + "="*60)
    if success:
        print("✓ TEST PASSED - Inventory update working!")
        print("="*60)
        return True
    else:
        print("✗ TEST FAILED")
        print("="*60)
        return False

if __name__ == '__main__':
    try:
        success = test_update_inventory()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
