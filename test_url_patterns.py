#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'client.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.urls import path, get_resolver
from django.urls.resolvers import URLPattern, URLResolver

print("\n" + "="*80)
print("INSPECTING ALL REGISTERED URL PATTERNS")
print("="*80 + "\n")

resolver = get_resolver()

def show_urls(patterns, prefix=""):
    """Recursively show all URL patterns"""
    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            # It's a nested router
            new_prefix = prefix + str(pattern.pattern)
            show_urls(pattern.url_patterns, new_prefix)
        else:
            # It's a pattern
            full_pattern = prefix + str(pattern.pattern)
            if 'upload' in str(full_pattern):
                print(f"Found: {full_pattern}")
                print(f"  Pattern object: {pattern}")
                print(f"  Callback: {pattern.callback}")
                print()

show_urls(resolver.url_patterns)

print("\n" + "="*80)
print("LOOKING FOR /api/v1/ PATTERNS")
print("="*80 + "\n")

for pattern in resolver.url_patterns:
    pattern_str = str(pattern.pattern)
    if 'api' in pattern_str:
        print(f"API Pattern: {pattern_str}")
        if isinstance(pattern, URLResolver):
            print(f"  Has {len(pattern.url_patterns)} nested patterns")
            # Check nested patterns
            for nested in pattern.url_patterns:
                nested_str = str(nested.pattern)
                if 'product' in nested_str and 'upload' in nested_str:
                    print(f"    Found: {nested_str}")

print("\n" + "="*80)
print("CHECKING DRF ROUTER ROUTES")
print("="*80 + "\n")

from clientapp.api_urls import router

all_urls = router.get_urls()
print(f"Total routes from router: {len(all_urls)}\n")

for url in all_urls:
    url_str = str(url.pattern)
    if 'product' in url_str and 'upload' in url_str:
        print(f"Router URL: {url_str}")
        print(f"  Callback: {url.callback}")
        print(f"  Name: {url.name}")
        print()

print("\n" + "="*80)
print("CHECKING WHICH PATTERN MATCHES /api/v1/products/51/upload-gallery-images/")
print("="*80 + "\n")

test_url = '/api/v1/products/51/upload-gallery-images/'
try:
    match = resolver.resolve(test_url)
    print(f"✓ URL MATCHED!")
    print(f"  View: {match.func}")
    print(f"  Args: {match.args}")
    print(f"  Kwargs: {match.kwargs}")
    print(f"  URL name: {match.url_name}")
except Exception as e:
    print(f"✗ URL DOES NOT MATCH")
    print(f"  Error: {e}")
    
print("\n" + "="*80)
print("CHECKING WHICH PATTERN MATCHES /api/v1/products/51/upload-primary-image/")
print("="*80 + "\n")

test_url2 = '/api/v1/products/51/upload-primary-image/'
try:
    match = resolver.resolve(test_url2)
    print(f"✓ URL MATCHED!")
    print(f"  View: {match.func}")
    print(f"  Args: {match.args}")
    print(f"  Kwargs: {match.kwargs}")
    print(f"  URL name: {match.url_name}")
except Exception as e:
    print(f"✗ URL DOES NOT MATCH")
    print(f"  Error: {e}")
