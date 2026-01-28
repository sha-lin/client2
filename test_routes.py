#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'client.settings')
django.setup()

from clientapp.api_urls import router
from django.urls import path

# Print all registered routes
print("=" * 80)
print("REGISTERED API ROUTES")
print("=" * 80)

for idx, url_pattern in enumerate(router.urls):
    print(f"{idx+1}. {url_pattern.pattern}")
    if 'upload' in str(url_pattern.pattern):
        print(f"   ^^^ UPLOAD ROUTE FOUND ^^^")

print("\n" + "=" * 80)
print("CHECKING SPECIFIC PRODUCT ROUTES")
print("=" * 80)

for url_pattern in router.urls:
    pattern_str = str(url_pattern.pattern)
    if 'products' in pattern_str:
        print(pattern_str)
