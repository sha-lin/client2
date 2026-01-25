#!/usr/bin/env python
"""
Test script to verify Quote calculation fix
Tests that total_amount includes VAT, shipping, and adjustments
"""
import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'client.settings')
django.setup()

from clientapp.models import Quote, Client
from django.contrib.auth.models import User
from django.utils import timezone

def test_quote_calculation():
    """Test quote calculation with VAT, shipping, and adjustments"""
    
    print("\n" + "="*70)
    print("QUOTE CALCULATION TEST")
    print("="*70)
    
    # Get or create a test client
    test_client, created = Client.objects.get_or_create(
        email='test@quote-calc.com',
        defaults={'name': 'Test Quote Calculation Client', 'status': 'Active'}
    )
    
    # Get or create a test user
    test_user, created = User.objects.get_or_create(
        username='quote_test_user',
        defaults={'email': 'quotetest@example.com', 'is_staff': False}
    )
    
    print(f"\nTest Client: {test_client.name} (email: {test_client.email})")
    print(f"Test User: {test_user.username}")
    
    # Test Case 1: Basic quote (no VAT, no shipping, no adjustment)
    print("\n" + "-"*70)
    print("TEST 1: Basic Quote (no VAT, no shipping)")
    print("-"*70)
    
    quote1 = Quote(
        client=test_client,
        product_name="Basic Product",
        quantity=10,
        unit_price=Decimal('100.00'),
        include_vat=False,
        shipping_charges=Decimal('0.00'),
        adjustment_amount=Decimal('0.00'),
        valid_until=timezone.now().date(),
        created_by=test_user
    )
    quote1.save()
    
    expected1 = Decimal('1000.00')  # 10 * 100
    print(f"Unit Price: ${quote1.unit_price}")
    print(f"Quantity: {quote1.quantity}")
    print(f"Include VAT: {quote1.include_vat}")
    print(f"Shipping: ${quote1.shipping_charges}")
    print(f"Adjustment: ${quote1.adjustment_amount}")
    print(f"Subtotal: ${quote1.subtotal}")
    print(f"Tax Total: ${quote1.tax_total}")
    print(f"TOTAL AMOUNT: ${quote1.total_amount}")
    print(f"Expected: ${expected1}")
    print(f"✓ PASS" if quote1.total_amount == expected1 else f"✗ FAIL")
    
    # Test Case 2: Quote with VAT only
    print("\n" + "-"*70)
    print("TEST 2: Quote with VAT (16%)")
    print("-"*70)
    
    quote2 = Quote(
        client=test_client,
        product_name="Product with VAT",
        quantity=10,
        unit_price=Decimal('100.00'),
        include_vat=True,
        shipping_charges=Decimal('0.00'),
        adjustment_amount=Decimal('0.00'),
        valid_until=timezone.now().date(),
        created_by=test_user
    )
    quote2.save()
    
    # Expected: (10 * 100) + (10 * 100 * 0.16) = 1000 + 160 = 1160
    expected2 = Decimal('1160.00')
    print(f"Unit Price: ${quote2.unit_price}")
    print(f"Quantity: {quote2.quantity}")
    print(f"Include VAT: {quote2.include_vat}")
    print(f"Shipping: ${quote2.shipping_charges}")
    print(f"Adjustment: ${quote2.adjustment_amount}")
    print(f"Subtotal: ${quote2.subtotal}")
    print(f"Tax Total: ${quote2.tax_total}")
    print(f"TOTAL AMOUNT: ${quote2.total_amount}")
    print(f"Expected: ${expected2}")
    print(f"✓ PASS" if quote2.total_amount == expected2 else f"✗ FAIL")
    
    # Test Case 3: Quote with VAT and Shipping
    print("\n" + "-"*70)
    print("TEST 3: Quote with VAT + Shipping")
    print("-"*70)
    
    quote3 = Quote(
        client=test_client,
        product_name="Product with VAT and Shipping",
        quantity=10,
        unit_price=Decimal('100.00'),
        include_vat=True,
        shipping_charges=Decimal('50.00'),
        adjustment_amount=Decimal('0.00'),
        valid_until=timezone.now().date(),
        created_by=test_user
    )
    quote3.save()
    
    # Expected: (10 * 100) + (10 * 100 * 0.16) + 50 = 1000 + 160 + 50 = 1210
    expected3 = Decimal('1210.00')
    print(f"Unit Price: ${quote3.unit_price}")
    print(f"Quantity: {quote3.quantity}")
    print(f"Include VAT: {quote3.include_vat}")
    print(f"Shipping: ${quote3.shipping_charges}")
    print(f"Adjustment: ${quote3.adjustment_amount}")
    print(f"Subtotal: ${quote3.subtotal}")
    print(f"Tax Total: ${quote3.tax_total}")
    print(f"TOTAL AMOUNT: ${quote3.total_amount}")
    print(f"Expected: ${expected3}")
    print(f"✓ PASS" if quote3.total_amount == expected3 else f"✗ FAIL")
    
    # Test Case 4: Quote with VAT, Shipping, and Adjustment
    print("\n" + "-"*70)
    print("TEST 4: Quote with VAT + Shipping + Adjustment (+$100)")
    print("-"*70)
    
    quote4 = Quote(
        client=test_client,
        product_name="Product with All Charges",
        quantity=10,
        unit_price=Decimal('100.00'),
        include_vat=True,
        shipping_charges=Decimal('50.00'),
        adjustment_amount=Decimal('100.00'),
        adjustment_reason="Rush delivery surcharge",
        valid_until=timezone.now().date(),
        created_by=test_user
    )
    quote4.save()
    
    # Expected: (10 * 100) + (10 * 100 * 0.16) + 50 + 100 = 1000 + 160 + 50 + 100 = 1310
    expected4 = Decimal('1310.00')
    print(f"Unit Price: ${quote4.unit_price}")
    print(f"Quantity: {quote4.quantity}")
    print(f"Include VAT: {quote4.include_vat}")
    print(f"Shipping: ${quote4.shipping_charges}")
    print(f"Adjustment: ${quote4.adjustment_amount}")
    print(f"Adjustment Reason: {quote4.adjustment_reason}")
    print(f"Subtotal: ${quote4.subtotal}")
    print(f"Tax Total: ${quote4.tax_total}")
    print(f"TOTAL AMOUNT: ${quote4.total_amount}")
    print(f"Expected: ${expected4}")
    print(f"✓ PASS" if quote4.total_amount == expected4 else f"✗ FAIL")
    
    # Test Case 5: Quote with Negative Adjustment (discount)
    print("\n" + "-"*70)
    print("TEST 5: Quote with VAT + Shipping - Adjustment (-$50)")
    print("-"*70)
    
    quote5 = Quote(
        client=test_client,
        product_name="Product with Discount",
        quantity=10,
        unit_price=Decimal('100.00'),
        include_vat=True,
        shipping_charges=Decimal('50.00'),
        adjustment_amount=Decimal('-50.00'),
        adjustment_reason="Bulk discount",
        valid_until=timezone.now().date(),
        created_by=test_user
    )
    quote5.save()
    
    # Expected: (10 * 100) + (10 * 100 * 0.16) + 50 - 50 = 1000 + 160 + 50 - 50 = 1160
    expected5 = Decimal('1160.00')
    print(f"Unit Price: ${quote5.unit_price}")
    print(f"Quantity: {quote5.quantity}")
    print(f"Include VAT: {quote5.include_vat}")
    print(f"Shipping: ${quote5.shipping_charges}")
    print(f"Adjustment: ${quote5.adjustment_amount}")
    print(f"Adjustment Reason: {quote5.adjustment_reason}")
    print(f"Subtotal: ${quote5.subtotal}")
    print(f"Tax Total: ${quote5.tax_total}")
    print(f"TOTAL AMOUNT: ${quote5.total_amount}")
    print(f"Expected: ${expected5}")
    print(f"✓ PASS" if quote5.total_amount == expected5 else f"✗ FAIL")
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    all_quotes = [quote1, quote2, quote3, quote4, quote5]
    all_expected = [expected1, expected2, expected3, expected4, expected5]
    
    passed = sum(1 for q, exp in zip(all_quotes, all_expected) if q.total_amount == exp)
    total = len(all_quotes)
    
    print(f"\nCreated {total} test quotes")
    print(f"Passed: {passed}/{total}")
    print(f"Status: {'✓ ALL TESTS PASSED' if passed == total else '✗ SOME TESTS FAILED'}")
    
    # Display the quotes in the database
    print("\n" + "="*70)
    print("QUOTES IN DATABASE:")
    print("="*70)
    
    for quote in Quote.objects.filter(client=test_client).order_by('-created_at'):
        print(f"\nQuote ID: {quote.quote_id}")
        print(f"  Product: {quote.product_name}")
        print(f"  Subtotal: ${quote.subtotal}")
        print(f"  VAT (16%): ${quote.tax_total}")
        print(f"  Shipping: ${quote.shipping_charges}")
        print(f"  Adjustment: ${quote.adjustment_amount}")
        print(f"  TOTAL: ${quote.total_amount}")

if __name__ == '__main__':
    test_quote_calculation()
