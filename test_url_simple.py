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

print("\nChecking if gallery upload URL resolves...\n")

test_urls = [
    '/api/v1/products/51/upload-gallery-images/',
    '/api/v1/products/51/upload-primary-image/',
]

for url in test_urls:
    try:
        match = resolve(url)
        print(f"✓ {url}")
        print(f"  -> {match.func.__name__}")
    except Http404 as e:
        print(f"✗ {url}")
        print(f"  -> 404 Not Found")
