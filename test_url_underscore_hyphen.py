#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'client.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.urls import resolve
from django.http import Http404

print("\nTesting URL patterns with UNDERSCORES vs HYPHENS...\n")

test_urls = [
    # With underscores
    ('/api/v1/products/51/upload_gallery_images/', 'Underscores'),
    ('/api/v1/products/51/upload_primary_image/', 'Underscores'),
    # With hyphens
    ('/api/v1/products/51/upload-gallery-images/', 'Hyphens'),
    ('/api/v1/products/51/upload-primary-image/', 'Hyphens'),
]

for url, style in test_urls:
    try:
        match = resolve(url)
        print(f"✓ {style:12} {url}")
        print(f"    -> {match.func.__name__}")
    except Http404:
        print(f"✗ {style:12} {url}")
