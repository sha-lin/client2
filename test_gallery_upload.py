#!/usr/bin/env python
import os
import sys
import django
import json
from io import BytesIO
from PIL import Image

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'client.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import Client
from django.contrib.auth.models import User, Group
from clientapp.models import Product
from rest_framework_simplejwt.tokens import RefreshToken

def create_test_image():
    """Create an in-memory image file for testing"""
    file = BytesIO()
    image = Image.new('RGB', (300, 300), color='red')
    image.save(file, 'PNG')
    file.seek(0)
    file.name = 'test_image.png'
    return file

def get_jwt_token_for_user(user):
    """Get JWT token for a user"""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)

print("\n" + "="*80)
print("TESTING GALLERY IMAGE UPLOAD ENDPOINT")
print("="*80)

# Get or create test user
user = User.objects.filter(username='prod_user').first()
if not user:
    print("ERROR: prod_user does not exist. Creating test user...")
    user = User.objects.create_user(username='prod_user', password='testpass123')
else:
    print(f"✓ Using existing user: {user.username}")

# Ensure user is in Production Team group
pt_group, created = Group.objects.get_or_create(name='Production Team')
if user not in pt_group.user_set.all():
    pt_group.user_set.add(user)
    print("✓ Added user to Production Team group")
else:
    print("✓ User already in Production Team group")

# Get token
token = get_jwt_token_for_user(user)
print(f"✓ Generated JWT token for {user.username}")
print(f"  Token (first 50 chars): {token[:50]}...")

# Get test product
product = Product.objects.filter(id=51).first()
if not product:
    print("ERROR: Product 51 does not exist!")
    sys.exit(1)
else:
    print(f"✓ Found product: {product.name} (ID: {product.id})")

# Create Django test client
client = Client()

print("\n" + "-"*80)
print("TEST 1: POST to /api/v1/products/51/upload-gallery-images/")
print("-"*80)

# Create test images
test_files = [
    ('test_image_1.png', create_test_image()),
    ('test_image_2.png', create_test_image()),
]

# Prepare multipart form data
data = {}
for filename, file_obj in test_files:
    file_obj.name = filename
    # In multipart, we need to use the 'images' key (plural) as expected by the API
    if 'images' not in data:
        data['images'] = []
    data['images'].append(file_obj)

# Try the upload with JWT header
response = client.post(
    '/api/v1/products/51/upload-gallery-images/',
    data={'images': [create_test_image(), create_test_image()]},
    HTTP_AUTHORIZATION=f'Bearer {token}',
    content_type='multipart/form-data'
)

print(f"Status Code: {response.status_code}")
print(f"Response Content-Type: {response.get('Content-Type')}")
print(f"Response Body (first 500 chars):\n{response.content[:500]}")

if response.status_code == 201:
    print("\n✓ SUCCESS: Gallery upload returned 201 Created")
    try:
        result = json.loads(response.content)
        print(f"  Images uploaded: {result.get('count')}")
        for img in result.get('images', []):
            print(f"    - {img.get('url')}")
    except:
        print(f"  Could not parse response JSON")
elif response.status_code == 404:
    print("\n✗ FAILURE: 404 Not Found")
    print(f"  This means the route is NOT being registered")
    print(f"  Response: {response.content[:200]}")
elif response.status_code == 400:
    print("\n✗ FAILURE: 400 Bad Request")
    try:
        result = json.loads(response.content)
        print(f"  Error: {result}")
    except:
        print(f"  Response: {response.content[:200]}")
elif response.status_code == 401:
    print("\n✗ FAILURE: 401 Unauthorized")
    print(f"  Authentication issue. Token may not be valid")
    print(f"  Response: {response.content[:200]}")
elif response.status_code == 403:
    print("\n✗ FAILURE: 403 Forbidden")
    print(f"  Permission denied. User may not be in correct group")
    print(f"  Response: {response.content[:200]}")
else:
    print(f"\n✗ FAILURE: Status {response.status_code}")
    print(f"  Response: {response.content[:200]}")

print("\n" + "-"*80)
print("TEST 2: Check if upload_primary_image works (reference test)")
print("-"*80)

response2 = client.post(
    '/api/v1/products/51/upload-primary-image/',
    data={'image': create_test_image()},
    HTTP_AUTHORIZATION=f'Bearer {token}',
)

print(f"Status Code: {response2.status_code}")
if response2.status_code == 201:
    print("✓ Primary upload works (reference)")
else:
    print(f"✗ Primary upload also failing: {response2.status_code}")

print("\n" + "="*80)
print("END OF TESTS")
print("="*80 + "\n")
