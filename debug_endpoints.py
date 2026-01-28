#!/usr/bin/env python
"""Debug script to check registered API routes"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'client.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.urls import get_resolver
from rest_framework.routers import DefaultRouter
from clientapp import api_views

# Create router to see what gets registered
router = DefaultRouter()
router.register("products", api_views.ProductViewSet, basename="product")

print("\n" + "="*80)
print("REGISTERED PRODUCT ENDPOINTS")
print("="*80 + "\n")

# Get all URLs from the router
for pattern in router.urls:
    print(f"{pattern.pattern}")

print("\n" + "="*80)
print("CHECKING PRODUCTVIEWSET ACTIONS")
print("="*80 + "\n")

vs = api_views.ProductViewSet()
actions = [name for name in dir(vs) if not name.startswith('_')]
custom_actions = []

# Check which are @action decorated
import inspect
for name in actions:
    attr = getattr(vs, name)
    if hasattr(attr, 'mapping'):  # @action sets a 'mapping' attribute
        custom_actions.append(f"{name} -> {getattr(attr, 'mapping', {})}")

print(f"Total methods/attributes: {len(actions)}")
print(f"Custom actions with @action: {len(custom_actions)}\n")

for action in custom_actions:
    print(f"  • {action}")

print("\n" + "="*80)
print("CHECKING ACTUAL DJANGO URLS")
print("="*80 + "\n")

resolver = get_resolver()
patterns = resolver.url_patterns

product_urls = [p for p in patterns if 'product' in str(p.pattern).lower()]

for p in product_urls[:10]:
    print(f"{p.pattern}")
