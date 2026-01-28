#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'client.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from clientapp.api_views import ProductViewSet
import inspect

print("\n" + "="*80)
print("CHECKING PRODUCTVIEWSET FOR ACTION DECORATORS")
print("="*80 + "\n")

# Get all methods
methods = inspect.getmembers(ProductViewSet, predicate=inspect.isfunction)

print(f"Found {len(methods)} methods in ProductViewSet\n")

# Look for action methods
print("Looking for @action decorated methods:\n")

for name, method in methods:
    # Check if method has the action decorator markers
    if hasattr(method, 'mapping'):
        print(f"✓ {name}")
        print(f"  - mapping: {method.mapping}")
        print(f"  - detail: {getattr(method, 'detail', 'N/A')}")
        print(f"  - methods: {getattr(method, 'methods', 'N/A')}")
        print()

print("\n" + "="*80)
print("CHECKING DRF ROUTER REGISTRATION")
print("="*80 + "\n")

from clientapp.api_urls import router

# Check what routes are registered
product_routes = [route for route in router.registry if route[2] == 'product']
if product_routes:
    print(f"✓ ProductViewSet is registered in router")
    pattern, viewset, basename = product_routes[0]
    print(f"  - Pattern: {pattern}")
    print(f"  - Viewset: {viewset}")
    print(f"  - Basename: {basename}")
    
    # Get all URLs from this viewset
    all_urls = router.get_urls()
    product_urls = [url for url in all_urls if 'product' in url.name and 'upload' in url.name]
    
    print(f"\n  URLs containing 'product' and 'upload':")
    for url in product_urls:
        print(f"    - {url.pattern} ({url.name})")
else:
    print("✗ ProductViewSet NOT registered in router!")
