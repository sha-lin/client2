#!/usr/bin/env python
"""Debug script to check if @action routes are registered"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'client.settings')
django.setup()

from clientapp.api_urls import router
from clientapp.api_views import ProductViewSet

print("=" * 80)
print("ROUTER URL PATTERNS FOR PRODUCTS")
print("=" * 80)

# Find all product-related patterns
product_patterns = [p for p in router.urls if 'products' in str(p.pattern)]

print(f"\nTotal product patterns found: {len(product_patterns)}")
print("\nPatterns:")

for i, pattern in enumerate(product_patterns):
    print(f"{i+1}. {pattern.pattern}")

# Also check the viewset itself
print("\n" + "=" * 80)
print("PRODUCTVIEWSET METHODS")
print("=" * 80)

# Get all methods decorated with @action
from rest_framework.decorators import action as action_decorator
import inspect

methods_with_action = []
for name, method in inspect.getmembers(ProductViewSet, predicate=inspect.isfunction):
    if hasattr(method, 'actions'):  # @action decorator adds 'actions' attribute
        methods_with_action.append((name, method.actions))
        print(f"✓ @action found: {name}")
        print(f"  Methods: {method.actions}")

if not methods_with_action:
    print("❌ No @action decorated methods found!")

# Check if the ViewSet was registered correctly
print("\n" + "=" * 80)
print("VIEWSET REGISTRATION")
print("=" * 80)

print(f"ProductViewSet registered: {any('product' in str(p.callback.cls.__name__).lower() for p in router.urls if hasattr(p.callback, 'cls'))}")

# Try to see all basenames
print("\nRouter registry:")
for prefix, viewset, basename in router.registry:
    if 'product' in prefix.lower():
        print(f"  Prefix: {prefix}, ViewSet: {viewset.__name__}, Basename: {basename}")
