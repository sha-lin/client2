#!/usr/bin/env python
"""
Simple End-to-End Testing Script for Product Catalog
Tests complete product creation flow using REST API
"""

import os
import sys
import django
import json
from io import BytesIO
from PIL import Image

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'client.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.conf import settings
# Add testserver to ALLOWED_HOSTS for testing
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient
from clientapp.models import Product, ProductImage, ProductVideo, ProductPricing

print("\n" + "="*80)
print("PRODUCT CATALOG END-TO-END TEST - SIMPLIFIED")
print("="*80 + "\n")

tests_passed = 0
tests_failed = 0

def test_result(test_name, passed, message=""):
    """Display test result"""
    global tests_passed, tests_failed
    status = "✅" if passed else "❌"
    print(f"{status} {test_name}")
    if message:
        print(f"   └─ {message}")
    if passed:
        tests_passed += 1
    else:
        tests_failed += 1

# ============================================================================
# SETUP
# ============================================================================
print("SETUP: Initializing test environment...\n")

# Create or get test user
user, created = User.objects.get_or_create(
    username='testuser_e2e_v2',
    defaults={
        'email': 'test2@example.com',
        'first_name': 'E2E',
        'last_name': 'Test',
    }
)
user.set_password('testpass123')
user.save()

# Add to Production Team group
prod_team_group, _ = Group.objects.get_or_create(name='Production Team')
user.groups.add(prod_team_group)

test_result("Test User Created", True, f"User: {user.username}")

# Create API client
client = APIClient()
client.force_authenticate(user=user)
test_result("API Client Ready", True)

product_id = None

# ============================================================================
# TEST 1: CREATE PRODUCT
# ============================================================================
print("\n" + "-"*80)
print("TEST 1: Create Product with General Info")
print("-"*80 + "\n")

test_product_data = {
    'name': 'Premium Business Cards - E2E Test',
    'internal_code': 'BC-E2E-TEST-001',
    'short_description': 'High-quality business cards with custom design',
    'long_description': 'Premium 350gsm card stock with full-color printing',
    'customization_level': 'semi_customizable',
    'primary_category': 'print-products',
    'base_price': '250.00',
    'status': 'draft',
}

response = client.post('/api/v1/products/', test_product_data, format='json')
test_result("POST /api/v1/products/", response.status_code == 201, f"Status: {response.status_code}")

if response.status_code == 201:
    product_data = response.json()
    product_id = product_data.get('id')
    test_result("Product Created with ID", product_id is not None, f"ID: {product_id}")
    
    # Verify in database
    product = Product.objects.get(id=product_id)
    test_result("Name Saved", product.name == test_product_data['name'])
    test_result("Code Saved", product.internal_code == 'BC-E2E-TEST-001')
    test_result("Status is Draft", product.status == 'draft')
else:
    try:
        print(f"   └─ Error: {response.json()}")
    except:
        print(f"   └─ Error Status: {response.status_code}")

# ============================================================================
# TEST 2: UPDATE PRICING
# ============================================================================
if product_id:
    print("\n" + "-"*80)
    print("TEST 2: Update Product Pricing")
    print("-"*80 + "\n")
    
    pricing_data = {
        'base_cost': '150.00',
        'standard_margin': '40.00',
        'unit_lead_time_days': 7,
    }
    
    response = client.patch(f'/api/v1/products/{product_id}/', pricing_data, format='json')
    test_result("PATCH /api/v1/products/{id}/", response.status_code == 200, f"Status: {response.status_code}")
    
    if response.status_code == 200:
        # Verify pricing
        pricing = ProductPricing.objects.filter(product_id=product_id).first()
        test_result("Pricing Record Created", pricing is not None)
        if pricing:
            test_result("Base Cost Saved", str(pricing.base_cost) == '150.00', f"Cost: {pricing.base_cost}")

# ============================================================================
# TEST 3: UPLOAD PRIMARY IMAGE
# ============================================================================
if product_id:
    print("\n" + "-"*80)
    print("TEST 3: Upload Primary Image")
    print("-"*80 + "\n")
    
    # Create test image
    image = Image.new('RGB', (400, 400), color='red')
    img_io = BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)
    img_io.name = 'primary_test.png'
    
    response = client.post(
        f'/api/v1/products/{product_id}/upload_primary_image/',
        {'image': img_io, 'alt_text': 'Business card design'},
        format='multipart'
    )
    test_result("POST /api/v1/products/{id}/upload_primary_image/", 
                response.status_code == 201, f"Status: {response.status_code}")
    
    if response.status_code == 201:
        image_data = response.json()
        test_result("Primary Image Saved", image_data.get('is_primary') == True)
        
        # Verify in database
        primary_img = ProductImage.objects.filter(product_id=product_id, is_primary=True).first()
        test_result("Primary Image in Database", primary_img is not None)

# ============================================================================
# TEST 4: UPLOAD GALLERY IMAGES
# ============================================================================
if product_id:
    print("\n" + "-"*80)
    print("TEST 4: Upload Gallery Images")
    print("-"*80 + "\n")
    
    # Create test images
    gallery_images = []
    for i in range(2):
        image = Image.new('RGB', (400, 400), color=['blue', 'green'][i])
        img_io = BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)
        img_io.name = f'gallery_{i}.png'
        gallery_images.append(img_io)
    
    response = client.post(
        f'/api/v1/products/{product_id}/upload_gallery_images/',
        {'images': gallery_images},
        format='multipart'
    )
    test_result("POST /api/v1/products/{id}/upload_gallery_images/", 
                response.status_code == 201, f"Status: {response.status_code}")
    
    if response.status_code == 201:
        response_data = response.json()
        gallery_count = response_data.get('count', 0)
        test_result("Gallery Images Uploaded", gallery_count >= 2, f"Count: {gallery_count}")
        
        # Verify in database
        gallery_imgs = ProductImage.objects.filter(product_id=product_id, is_primary=False)
        test_result("Gallery Images in Database", gallery_imgs.count() >= 2, f"Total: {gallery_imgs.count()}")

# ============================================================================
# TEST 5: ADD VIDEO
# ============================================================================
if product_id:
    print("\n" + "-"*80)
    print("TEST 5: Add Product Video")
    print("-"*80 + "\n")
    
    video_data = {
        'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    }
    
    response = client.post(
        f'/api/v1/products/{product_id}/add_video/',
        video_data,
        format='json'
    )
    test_result("POST /api/v1/products/{id}/add_video/", 
                response.status_code == 201, f"Status: {response.status_code}")
    
    if response.status_code == 201:
        video_response = response.json()
        test_result("Video Type Detected", video_response.get('video_type') == 'youtube', 
                   f"Type: {video_response.get('video_type')}")
        
        # Verify in database
        video = ProductVideo.objects.filter(product_id=product_id).first()
        test_result("Video in Database", video is not None)

# ============================================================================
# TEST 6: GET CHANGE HISTORY
# ============================================================================
if product_id:
    print("\n" + "-"*80)
    print("TEST 6: Get Change History (Auto-Audit)")
    print("-"*80 + "\n")
    
    response = client.get(f'/api/v1/products/{product_id}/change_history/')
    test_result("GET /api/v1/products/{id}/change_history/", 
                response.status_code == 200, f"Status: {response.status_code}")
    
    if response.status_code == 200:
        history_data = response.json()
        history_count = history_data.get('count', 0)
        test_result("Change History Created", history_count > 0, f"Total changes: {history_count}")
        
        # Check for specific field changes
        results = history_data.get('results', [])
        if results:
            field_changes = {h.get('field_changed') for h in results}
            test_result("Field Changes Recorded", len(field_changes) > 0, f"Fields: {field_changes}")

# ============================================================================
# TEST 7: PUBLISH PRODUCT
# ============================================================================
if product_id:
    print("\n" + "-"*80)
    print("TEST 7: Publish Product")
    print("-"*80 + "\n")
    
    response = client.post(f'/api/v1/products/{product_id}/publish/', {}, format='json')
    test_result("POST /api/v1/products/{id}/publish/", 
                response.status_code == 200, f"Status: {response.status_code}")
    
    if response.status_code == 200:
        pub_data = response.json()
        test_result("Status Changed to Published", pub_data.get('status') == 'published')

# ============================================================================
# TEST 8: RETRIEVE FROM CATALOG
# ============================================================================
if product_id:
    print("\n" + "-"*80)
    print("TEST 8: Retrieve from Catalog")
    print("-"*80 + "\n")
    
    # Try storefront endpoint
    response = client.get(f'/api/v1/storefront-products/{product_id}/')
    test_result("GET /api/v1/storefront-products/{id}/", 
                response.status_code == 200, f"Status: {response.status_code}")
    
    if response.status_code == 200:
        prod = response.json()
        test_result("Product Has Name", prod.get('name') is not None, f"Name: {prod.get('name')}")
        test_result("Product Has Base Price", 'base_price' in prod, f"Price: {prod.get('base_price')}")
        test_result("Product Has Images", len(prod.get('images', [])) > 0, f"Images: {len(prod.get('images', []))}")
        test_result("Product Has Videos", len(prod.get('videos', [])) > 0, f"Videos: {len(prod.get('videos', []))}")

# ============================================================================
# TEST 9: COMPLETE DATA VERIFICATION
# ============================================================================
if product_id:
    print("\n" + "-"*80)
    print("TEST 9: Complete Data Persistence Verification")
    print("-"*80 + "\n")
    
    product = Product.objects.get(id=product_id)
    
    test_result("Product Name Persisted", product.name is not None)
    test_result("Product Status is Published", product.status == 'published')
    
    # Check pricing (might not exist if not created)
    try:
        has_pricing = product.pricing is not None
    except:
        has_pricing = False
    test_result("Product Has Pricing", has_pricing)
    
    test_result("Product Has Images", product.images.count() > 0, f"Images: {product.images.count()}")
    test_result("Product Has Videos", product.videos.count() > 0, f"Videos: {product.videos.count()}")
    test_result("Product Has Change History", product.change_history.count() > 0, f"Changes: {product.change_history.count()}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80 + "\n")

total_tests = tests_passed + tests_failed
pass_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0

print(f"✅ PASSED: {tests_passed}")
print(f"❌ FAILED: {tests_failed}")
print(f"📊 TOTAL:  {total_tests}")
print(f"📈 PASS RATE: {pass_rate:.1f}%\n")

if tests_failed == 0:
    print("🎉 ALL TESTS PASSED! Product catalog is ready for production.\n")
    sys.exit(0)
else:
    print(f"⚠️  {tests_failed} test(s) failed. Review issues above.\n")
    sys.exit(1)
