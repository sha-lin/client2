#!/usr/bin/env python
"""Test EstimateQuote creation via serializer"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'client.settings')
django.setup()

from clientapp.models import EstimateQuote
from clientapp.storefront_serializers import EstimateQuoteCreateSerializer

data = {
    'customer_name': 'Test User',
    'customer_email': 'test@example.com',
    'customer_phone': '+254701234567',
    'customer_company': 'Test Co',
    'line_items': [
        {
            'product_id': 'PROD-BC-001',
            'quantity': 100,
            'unit_price': '2500.00',
            'line_total': '250000.00',
            'notes': 'Test',
            'properties': {}
        }
    ],
    'subtotal': '250000.00',
    'tax_amount': '45000.00',
    'total_amount': '295000.00',
    'turnaround_time': 'standard',
    'delivery_method': 'pickup',
    'payment_terms': 'prepaid',
    'special_notes': 'Test notes'
}

print("Testing EstimateQuoteCreateSerializer...")
serializer = EstimateQuoteCreateSerializer(data=data)
if serializer.is_valid():
    estimate = serializer.save()
    print(f'SUCCESS: Created estimate {estimate.estimate_id}')
    print(f'Share token: {estimate.share_token}')
    print(f'Customer: {estimate.customer_name}')
    print(f'Total: {estimate.total_amount}')
else:
    print(f'ERROR: {serializer.errors}')
