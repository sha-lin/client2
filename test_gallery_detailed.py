#!/usr/bin/env python
import os
import sys
import django
import json
import tempfile
from PIL import Image

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'client.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import Client
from django.contrib.auth.models import User, Group
from clientapp.models import Product
from rest_framework_simplejwt.tokens import RefreshToken

def get_jwt_token_for_user(user):
    """Get JWT token for a user"""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)

print("\n" + "="*80)
print("TESTING GALLERY IMAGE UPLOAD - BROWSER-LIKE REQUEST")
print("="*80)

# Get or create test user
user = User.objects.filter(username='prod_user').first()
if not user:
    print("ERROR: prod_user does not exist!")
    sys.exit(1)

# Get token
token = get_jwt_token_for_user(user)
print(f"✓ User: {user.username}")
print(f"✓ Token: {token[:50]}...")

# Get test product
product = Product.objects.filter(id=51).first()
if not product:
    print("ERROR: Product 51 does not exist!")
    sys.exit(1)
else:
    print(f"✓ Product: {product.name} (ID: 51)")

# Create a real test image file
print("\n" + "-"*80)
print("Creating test image files...")
print("-"*80)

image_files = []
for i in range(2):
    img = Image.new('RGB', (300, 300), color='red')
    temp_file = tempfile.NamedTemporaryFile(suffix=f'_{i}.png', delete=False)
    img.save(temp_file, 'PNG')
    temp_file.close()
    image_files.append(temp_file.name)
    print(f"✓ Created test image: {temp_file.name}")

# Use TestClient with explicit SERVER_NAME
client = Client(SERVER_NAME='127.0.0.1')

print("\n" + "-"*80)
print("TEST 1: Using Authorization header with JWT token")
print("-"*80)

with open(image_files[0], 'rb') as f1, open(image_files[1], 'rb') as f2:
    response = client.post(
        '/api/v1/products/51/upload-gallery-images/',
        data={
            'images': [f1, f2]
        },
        HTTP_AUTHORIZATION=f'Bearer {token}',
        HTTP_HOST='127.0.0.1:8000'
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.get('Content-Type')}")
    
    if response.status_code in [200, 201]:
        print("✓ SUCCESS!")
        try:
            result = json.loads(response.content)
            print(json.dumps(result, indent=2))
        except:
            print(f"Response: {response.content[:300]}")
    else:
        print(f"✗ FAILED")
        print(f"Response (first 500 chars):\n{response.content[:500]}")

print("\n" + "-"*80)
print("TEST 2: Check route is registered - Manual router inspection")
print("-"*80)

from clientapp.api_urls import router
from rest_framework.routers import SimpleRouter

for pattern, viewset, basename in router.registry:
    if 'product' in basename and 'product-approval' not in basename:
        print(f"\nBasename: {basename}")
        print(f"  Pattern: {pattern}")
        
        # Check if viewset has upload_gallery_images method
        if hasattr(viewset, 'upload_gallery_images'):
            print(f"  ✓ Has upload_gallery_images method")
            method = getattr(viewset, 'upload_gallery_images')
            if hasattr(method, 'kwargs'):
                print(f"    Decorator kwargs: {method.kwargs}")

print("\n" + "-"*80)
print("TEST 3: Direct method call test")
print("-"*80)

from clientapp.api_views import ProductViewSet
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

factory = APIRequestFactory()
view_set = ProductViewSet()

# Create a mock request with files
with open(image_files[0], 'rb') as f:
    request = factory.post(
        f'/api/v1/products/51/upload-gallery-images/',
        {'images': f},
        format='multipart',
        HTTP_AUTHORIZATION=f'Bearer {token}'
    )
    
    # Convert to DRF request
    drf_request = Request(request)
    drf_request.user = user
    drf_request.auth = token
    
    # Call the view set directly
    try:
        view_set.kwargs = {'pk': '51'}
        view_set.request = drf_request
        view_set.format_kwarg = None
        
        response = view_set.upload_gallery_images(drf_request, pk='51')
        print(f"Direct method call status: {response.status_code}")
        print(f"Response data: {response.data}")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

# Cleanup
for img_file in image_files:
    try:
        os.unlink(img_file)
    except:
        pass

print("\n" + "="*80)
print("END OF TESTS")
print("="*80 + "\n")
