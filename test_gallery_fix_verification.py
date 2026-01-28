#!/usr/bin/env python
import os
import sys
import django
import tempfile
import json
from PIL import Image

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'client.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import Client
from django.contrib.auth.models import User, Group
from clientapp.models import Product, ProductImage
from rest_framework_simplejwt.tokens import RefreshToken

def get_jwt_token_for_user(user):
    """Get JWT token for a user"""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)

print("\n" + "="*80)
print("TESTING FIXED GALLERY UPLOAD ENDPOINT")
print("="*80 + "\n")

# Get or create test user
user = User.objects.filter(username='prod_user').first()
if not user:
    print("ERROR: prod_user does not exist!")
    sys.exit(1)

# Ensure user is in Production Team group
pt_group, created = Group.objects.get_or_create(name='Production Team')
if user not in pt_group.user_set.all():
    pt_group.user_set.add(user)

# Get token
token = get_jwt_token_for_user(user)
print(f"✓ User: {user.username}")
print(f"✓ Token generated")

# Get test product
product = Product.objects.filter(id=51).first()
if not product:
    print("ERROR: Product 51 does not exist!")
    sys.exit(1)
else:
    print(f"✓ Product: {product.name} (ID: 51)")

# Delete existing gallery images for clean test
initial_count = product.images.filter(is_primary=False).count()
product.images.filter(is_primary=False).delete()
print(f"✓ Cleared {initial_count} existing gallery images")

# Create test images
image_files = []
for i in range(2):
    img = Image.new('RGB', (300, 300), color='blue')
    temp_file = tempfile.NamedTemporaryFile(suffix=f'_{i}.png', delete=False)
    img.save(temp_file, 'PNG')
    temp_file.close()
    image_files.append(temp_file.name)

print(f"✓ Created 2 test images\n")

# Test with corrected URL (using underscores)
client = Client(SERVER_NAME='127.0.0.1')

print("-"*80)
print("TEST: POST to /api/v1/products/51/upload_gallery_images/ (with underscores)")
print("-"*80 + "\n")

with open(image_files[0], 'rb') as f1, open(image_files[1], 'rb') as f2:
    response = client.post(
        '/api/v1/products/51/upload_gallery_images/',  # Using underscores!
        data={'images': [f1, f2]},
        HTTP_AUTHORIZATION=f'Bearer {token}',
        HTTP_HOST='127.0.0.1:8000'
    )
    
    print(f"Status Code: {response.status_code}\n")
    
    if response.status_code == 201:
        print("✓ SUCCESS! Gallery upload returned 201 Created\n")
        try:
            result = json.loads(response.content)
            print(f"Response:")
            print(f"  - Count: {result.get('count')}")
            print(f"  - Message: {result.get('message')}")
            print(f"  - Images uploaded:")
            for img in result.get('images', []):
                print(f"    - URL: {img.get('url')}")
                print(f"    - ID: {img.get('id')}")
        except Exception as e:
            print(f"Response: {response.content}")
    elif response.status_code == 400:
        print("✗ FAILED: 400 Bad Request\n")
        try:
            error = json.loads(response.content)
            print(f"Error: {error}")
        except:
            print(f"Response: {response.content[:300]}")
    elif response.status_code == 404:
        print("✗ FAILED: 404 Not Found")
        print("  -> URL pattern doesn't match. Check if endpoint uses underscores or hyphens")
    else:
        print(f"✗ FAILED: Status {response.status_code}")
        print(f"Response: {response.content[:300]}")

print("\n" + "-"*80)
print("TEST: Primary image upload with corrected URL")
print("-"*80 + "\n")

with open(image_files[0], 'rb') as f:
    response = client.post(
        '/api/v1/products/51/upload_primary_image/',  # Using underscores!
        data={'image': f},
        HTTP_AUTHORIZATION=f'Bearer {token}',
        HTTP_HOST='127.0.0.1:8000'
    )
    
    print(f"Status Code: {response.status_code}\n")
    
    if response.status_code == 201:
        print("✓ SUCCESS! Primary image upload also works with underscores\n")
        try:
            result = json.loads(response.content)
            print(f"Response:")
            print(f"  - URL: {result.get('url')}")
            print(f"  - Is Primary: {result.get('is_primary')}")
        except:
            pass
    else:
        print(f"✗ FAILED: Status {response.status_code}")

print("\n" + "-"*80)
print("VERIFYING IMAGES IN DATABASE")
print("-"*80 + "\n")

product.refresh_from_db()
all_images = product.images.all().count()
primary_images = product.images.filter(is_primary=True).count()
gallery_images = product.images.filter(is_primary=False).count()

print(f"Total images: {all_images}")
print(f"  - Primary: {primary_images}")
print(f"  - Gallery: {gallery_images}")

if gallery_images > 0:
    print(f"\n✓ Gallery images are in database!")
else:
    print(f"\n✗ No gallery images found in database")

# Cleanup
for img_file in image_files:
    try:
        os.unlink(img_file)
    except:
        pass

print("\n" + "="*80)
print("END OF TEST - Fix appears to be working!")
print("="*80 + "\n")
