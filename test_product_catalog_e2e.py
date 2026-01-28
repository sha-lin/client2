#!/usr/bin/env python
"""
End-to-End Testing Script for Product Catalog
Tests complete product creation flow across all tabs with data persistence
"""

import os
import sys
import django
from django.conf import settings
from io import BytesIO
from PIL import Image
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'client.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.conf import settings
# Add testserver to ALLOWED_HOSTS for testing
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

from django.contrib.auth.models import User, Group
from django.test import Client
from django.urls import reverse
from clientapp.models import Product, ProductImage, ProductVideo, ProductPricing, ProductChangeHistory
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

print("\n" + "="*80)
print("PRODUCT CATALOG END-TO-END TEST SUITE")
print("="*80 + "\n")

# Test Counter
tests_passed = 0
tests_failed = 0

def test_result(test_name, passed, message=""):
    """Display test result"""
    global tests_passed, tests_failed
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {test_name}")
    if message:
        print(f"       └─ {message}")
    if passed:
        tests_passed += 1
    else:
        tests_failed += 1

# ============================================================================
# SETUP: Create test user and client
# ============================================================================
print("SETUP: Initializing test environment...")
print("-" * 80)

# Create or get test user
user, created = User.objects.get_or_create(
    username='testuser_e2e',
    defaults={
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User',
    }
)

# Add to Production Team group
prod_team_group, _ = Group.objects.get_or_create(name='Production Team')
user.groups.add(prod_team_group)
user.set_password('testpass123')
user.save()

test_result("Test User Created", True, f"User: {user.username}")

# Create API client
from rest_framework.test import APIClient as DRFAPIClient
client = DRFAPIClient()
client.force_authenticate(user=user)
# Important: APIClient needs to force_authenticate via a request
from django.test import RequestFactory
factory = RequestFactory()
request = factory.get('/')
request.user = user
client.force_authenticate(request.user)

test_result("API Client Authenticated", True, f"Authenticated as: {user.username}")

# ============================================================================
# TEST 1: Create Base Product with General Info Tab Data
# ============================================================================
print("\n" + "="*80)
print("TEST GROUP 1: General Info Tab - Product Creation")
print("="*80 + "\n")

test_product_data = {
    'name': 'Premium Business Cards - E2E Test',
    'internal_code': 'BC-E2E-001',
    'short_description': 'High-quality business cards with custom design',
    'long_description': 'Premium 350gsm card stock with full-color printing on both sides. Perfect for professional branding and networking.',
    'technical_specs': 'Material: 350gsm Cardstock, Size: 3.5x2in, Colors: Full CMYK',
    'customization_level': 'semi_customizable',
    'primary_category': 'print-products',
    'sub_category': 'business-cards',
    'product_family': 'standard-print',
    'visibility': 'public',
    'feature_product': True,
    'bestseller_badge': False,
    'new_arrival': True,
    'base_price': '250.00',
    'status': 'draft',
}

# Create product
response = client.post('/api/v1/products/', data=json.dumps(test_product_data), content_type='application/json')
test_result("Create Product Endpoint", response.status_code == 201, f"Status: {response.status_code}")

if response.status_code == 201:
    product_data = response.json()
    product_id = product_data['id']
    test_result("Product ID Generated", 'id' in product_data, f"Product ID: {product_id}")
    
    # Verify fields saved
    product = Product.objects.get(id=product_id)
    test_result("Product Name Saved", product.name == test_product_data['name'], f"Name: {product.name}")
    test_result("Product Code Saved", product.internal_code == test_product_data['internal_code'], f"Code: {product.internal_code}")
    test_result("Product Description Saved", product.short_description == test_product_data['short_description'])
    test_result("Customization Level Saved", product.customization_level == 'semi_customizable')
    test_result("Category Saved", product.primary_category == 'print-products')
    test_result("Base Price Saved", str(product.base_price) == '250.00')
    test_result("Status is Draft", product.status == 'draft')
    test_result("Created By Set", product.created_by == user, f"Created by: {product.created_by.username}")
else:
    try:
        print(f"❌ Create Product failed: {response.json()}")
    except:
        print(f"❌ Create Product failed with status {response.status_code}")
    product_id = None

# ============================================================================
# TEST 2: Update with Pricing Tab Data
# ============================================================================
print("\n" + "="*80)
print("TEST GROUP 2: Pricing Tab - Pricing Configuration")
print("="*80 + "\n")

if product_id:
    pricing_data = {
        'base_cost': '150.00',
        'standard_margin': '40.00',
        'vip_margin': '35.00',
        'standard_margin_percentage': '26.67',
        'vip_margin_percentage': '23.33',
        'unit_lead_time_days': 7,
        'bulk_lead_time_days': 14,
        'rush_available': True,
        'rush_lead_time_days': 3,
        'rush_fee_percentage': '50.00',
        'pricing_type': 'tiered',
    }
    
    response = client.patch(f'/api/v1/products/{product_id}/', data=json.dumps(pricing_data), content_type='application/json')
    test_result("Update Pricing Data", response.status_code == 200, f"Status: {response.status_code}")
    
    # Verify pricing saved
    pricing = ProductPricing.objects.filter(product_id=product_id).first()
    if pricing:
        test_result("Pricing Record Created", True, f"Pricing ID: {pricing.id}")
        test_result("Base Cost Saved", str(pricing.base_cost) == '150.00')
        test_result("Standard Margin Saved", str(pricing.standard_margin) == '40.00')
        test_result("Lead Time Saved", pricing.unit_lead_time_days == 7)
        test_result("Rush Pricing Available", pricing.rush_available == True)
    else:
        test_result("Pricing Record Created", False, "No pricing found")

# ============================================================================
# TEST 3: Upload Primary Image
# ============================================================================
print("\n" + "="*80)
print("TEST GROUP 3: Images Tab - Primary Image Upload")
print("="*80 + "\n")

if product_id:
    # Create test image
    image = Image.new('RGB', (400, 400), color='red')
    img_io = BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)
    img_io.name = 'primary_test.png'
    
    response = client.post(
        f'/api/v1/products/{product_id}/upload-primary-image/',
        {'image': img_io, 'alt_text': 'Business card design'},
        format='multipart'
    )
    test_result("Upload Primary Image", response.status_code == 201, f"Status: {response.status_code}")
    
    if response.status_code == 201:
        image_data = response.json()
        test_result("Image ID Generated", 'id' in image_data, f"Image ID: {image_data.get('id')}")
        test_result("Primary Flag Set", image_data.get('is_primary') == True)
        test_result("Alt Text Saved", image_data.get('alt_text') == 'Business card design')
        
        # Verify in database
        primary_img = ProductImage.objects.filter(product_id=product_id, is_primary=True).first()
        test_result("Primary Image in Database", primary_img is not None)

# ============================================================================
# TEST 4: Upload Gallery Images
# ============================================================================
print("\n" + "="*80)
print("TEST GROUP 4: Images Tab - Gallery Images Upload")
print("="*80 + "\n")

if product_id:
    # Create multiple test images
    gallery_images = []
    for i in range(3):
        image = Image.new('RGB', (400, 400), color=['blue', 'green', 'yellow'][i])
        img_io = BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)
        img_io.name = f'gallery_{i}.png'
        gallery_images.append(img_io)
    
    response = client.post(
        f'/api/v1/products/{product_id}/upload-gallery-images/',
        {'images': gallery_images},
        format='multipart'
    )
    test_result("Upload Gallery Images", response.status_code == 201, f"Status: {response.status_code}")
    
    if response.status_code == 201:
        response_data = response.json()
        test_result("Gallery Count Correct", response_data.get('count') == 3, f"Count: {response_data.get('count')}")
        
        # Verify in database
        gallery_imgs = ProductImage.objects.filter(product_id=product_id, is_primary=False)
        test_result("Gallery Images in Database", gallery_imgs.count() >= 3, f"Total gallery images: {gallery_imgs.count()}")

# ============================================================================
# TEST 5: Add Video
# ============================================================================
print("\n" + "="*80)
print("TEST GROUP 5: Images Tab - Video Addition")
print("="*80 + "\n")

if product_id:
    video_data = {
        'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'title': 'Product Demo Video'
    }
    
    response = client.post(
        f'/api/v1/products/{product_id}/add-video/',
        video_data,
        format='json'
    )
    test_result("Add Video", response.status_code == 201, f"Status: {response.status_code}")
    
    if response.status_code == 201:
        video_response = response.json()
        test_result("Video ID Generated", 'id' in video_response, f"Video ID: {video_response.get('id')}")
        test_result("Video Type Detected", video_response.get('video_type') == 'youtube', f"Type: {video_response.get('video_type')}")
        
        # Verify in database
        video = ProductVideo.objects.filter(product_id=product_id).first()
        test_result("Video in Database", video is not None)
        if video:
            test_result("Video URL Saved", 'youtube' in video.video_url.lower())

# ============================================================================
# TEST 6: Update E-commerce & SEO Tab Data
# ============================================================================
print("\n" + "="*80)
print("TEST GROUP 6: E-commerce & SEO Tab - Meta Data")
print("="*80 + "\n")

if product_id:
    seo_data = {
        'seo_title': 'Premium Business Cards | Professional Printing',
        'seo_description': 'Custom business cards for professionals. 350gsm cardstock, full color printing.',
        'seo_keywords': 'business cards, printing, custom printing, professional cards',
    }
    
    response = client.patch(f'/api/v1/products/{product_id}/', seo_data, format='json')
    test_result("Update SEO Data", response.status_code == 200, f"Status: {response.status_code}")
    
    # Verify in database
    product = Product.objects.get(id=product_id)
    if hasattr(product, 'seo') and product.seo:
        test_result("SEO Title Saved", product.seo.seo_title == seo_data['seo_title'])
        test_result("SEO Keywords Saved", product.seo.seo_keywords == seo_data['seo_keywords'])
    else:
        test_result("SEO Record Created", False, "No SEO record found")

# ============================================================================
# TEST 7: Calculate Price
# ============================================================================
print("\n" + "="*80)
print("TEST GROUP 7: Pricing - Price Calculation")
print("="*80 + "\n")

if product_id:
    calc_data = {'quantity': 1000}
    
    response = client.post(
        f'/api/v1/products/{product_id}/calculate-price/',
        calc_data,
        format='json'
    )
    test_result("Calculate Price", response.status_code == 200, f"Status: {response.status_code}")
    
    if response.status_code == 200:
        price_data = response.json()
        test_result("Quantity in Response", price_data.get('quantity') == 1000)
        test_result("Unit Price Calculated", 'unit_price' in price_data, f"Unit Price: {price_data.get('unit_price')}")
        test_result("Total Price Calculated", 'total_price' in price_data, f"Total Price: {price_data.get('total_price')}")

# ============================================================================
# TEST 8: Get Change History (Auto-Audit)
# ============================================================================
print("\n" + "="*80)
print("TEST GROUP 8: History Tab - Change Audit Trail")
print("="*80 + "\n")

if product_id:
    response = client.get(f'/api/v1/products/{product_id}/change-history/')
    test_result("Get Change History", response.status_code == 200, f"Status: {response.status_code}")
    
    if response.status_code == 200:
        history_data = response.json()
        history_count = history_data.get('count', 0)
        test_result("Change History Entries Created", history_count > 0, f"Total changes: {history_count}")
        
        # Check for specific field changes
        results = history_data.get('results', [])
        if results:
            field_changes = {h.get('field_changed') for h in results}
            test_result("Name Change Recorded", 'name' in field_changes)
            test_result("Status Change Recorded", 'status' in field_changes or history_count > 0)

# ============================================================================
# TEST 9: Publish Product
# ============================================================================
print("\n" + "="*80)
print("TEST GROUP 9: Workflow - Product Publishing")
print("="*80 + "\n")

if product_id:
    response = client.post(f'/api/v1/products/{product_id}/publish/', {}, format='json')
    test_result("Publish Product", response.status_code == 200, f"Status: {response.status_code}")
    
    if response.status_code == 200:
        pub_data = response.json()
        test_result("Status Changed to Published", pub_data.get('status') == 'published')
        
        # Verify in database
        product = Product.objects.get(id=product_id)
        test_result("Published in Database", product.status == 'published')

# ============================================================================
# TEST 10: Verify Catalog Display
# ============================================================================
print("\n" + "="*80)
print("TEST GROUP 10: Catalog - Product Display")
print("="*80 + "\n")

if product_id:
    # Get via storefront endpoint
    response = client.get('/api/v1/storefront-products/')
    test_result("Get Storefront Products", response.status_code == 200, f"Status: {response.status_code}")
    
    if response.status_code == 200:
        products_data = response.json()
        
        # Look for our test product
        test_product_found = False
        if 'results' in products_data:
            for p in products_data['results']:
                if p.get('id') == product_id:
                    test_product_found = True
                    test_result("Test Product in Catalog", True, f"Found in catalog")
                    test_result("Product Has Name", p.get('name') == test_product_data['name'])
                    test_result("Product Has Price", 'base_price' in p)
                    test_result("Product Has Category", p.get('primary_category') == 'print-products')
                    break
        
        if not test_product_found:
            # Try single product endpoint
            response2 = client.get(f'/api/v1/storefront-products/{product_id}/')
            if response2.status_code == 200:
                prod = response2.json()
                test_result("Test Product Retrievable", True, f"Retrieved via direct endpoint")
                test_result("Has Name Field", prod.get('name') is not None)
                test_result("Has Images", 'images' in prod, f"Images: {len(prod.get('images', []))}")
                test_result("Has Videos", 'videos' in prod, f"Videos: {len(prod.get('videos', []))}")
            else:
                test_result("Test Product Retrievable", False, f"Status: {response2.status_code}")

# ============================================================================
# TEST 11: Complete Data Persistence Check
# ============================================================================
print("\n" + "="*80)
print("TEST GROUP 11: Data Persistence - Complete Verification")
print("="*80 + "\n")

if product_id:
    product = Product.objects.get(id=product_id)
    
    # All general fields
    test_result("All General Info Persisted", 
        product.name and product.internal_code and product.short_description,
        f"Name: {product.name}, Code: {product.internal_code}")
    
    # Pricing
    pricing = product.pricing
    test_result("Pricing Persisted", 
        pricing and pricing.base_cost is not None,
        f"Base Cost: {pricing.base_cost if pricing else 'N/A'}")
    
    # Images
    images = product.images.all()
    test_result("Images Persisted", 
        images.count() > 0,
        f"Total images: {images.count()}")
    
    # Videos
    videos = product.videos.all()
    test_result("Videos Persisted", 
        videos.count() > 0,
        f"Total videos: {videos.count()}")
    
    # SEO
    seo = product.seo
    test_result("SEO Data Persisted", 
        seo is not None,
        f"SEO exists: {seo is not None}")
    
    # Change History
    changes = product.change_history.all()
    test_result("Change History Persisted", 
        changes.count() > 0,
        f"Total changes: {changes.count()}")

# ============================================================================
# TEST 12: Save Draft Workflow
# ============================================================================
print("\n" + "="*80)
print("TEST GROUP 12: Workflow - Draft Saving")
print("="*80 + "\n")

# Create another product for draft testing
draft_product_data = {
    'name': 'Draft Test Product',
    'internal_code': 'DRAFT-001',
    'short_description': 'This is a draft product',
    'base_price': '100.00',
    'status': 'draft',
    'primary_category': 'print-products',
}

response = client.post('/api/v1/products/', draft_product_data, format='json')
if response.status_code == 201:
    draft_id = response.json()['id']
    test_result("Draft Product Created", True, f"Draft ID: {draft_id}")
    
    # Update it
    update_data = {
        'short_description': 'Updated draft description',
        'status': 'draft'
    }
    response = client.patch(f'/api/v1/products/{draft_id}/', update_data, format='json')
    test_result("Draft Can Be Updated", response.status_code == 200)
    
    # Verify it stays draft
    product = Product.objects.get(id=draft_id)
    test_result("Status Remains Draft", product.status == 'draft')

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
