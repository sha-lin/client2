#!/usr/bin/env python
"""
Test script to verify vendor invoice creation works without IntegrityError.
This tests the fix for: null value in column "line_items" violates not-null constraint
"""
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "client.settings")
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.contrib.auth.models import User
from clientapp.models import (
    Vendor, PurchaseOrder, Job, Client, VendorInvoice
)
from clientapp.api_serializers import VendorInvoiceDetailedSerializer
from datetime import datetime, timedelta
import json

def test_vendor_invoice_creation():
    """Test that vendor invoices can be created without IntegrityError"""
    
    print("\n" + "="*80)
    print("TESTING VENDOR INVOICE CREATION - IntegrityError Fix")
    print("="*80)
    
    try:
        # Get or create test vendor
        test_vendor_user, _ = User.objects.get_or_create(
            username='test_vendor_user',
            defaults={'email': 'test_vendor@example.com', 'first_name': 'Test', 'last_name': 'Vendor'}
        )
        
        test_vendor, _ = Vendor.objects.get_or_create(
            user=test_vendor_user,
            defaults={
                'name': 'Test Vendor Inc',
                'email': 'test_vendor@example.com',
                'phone': '+1-555-0001',
                'active': True
            }
        )
        print(f"✓ Vendor created/retrieved: {test_vendor.name}")
        
        # Get or create test client
        test_client, _ = Client.objects.get_or_create(
            name='Test Client',
            defaults={'email': 'test_client@example.com', 'phone': '+1-555-0002'}
        )
        print(f"✓ Client created/retrieved: {test_client.name}")
        
        # Get or create test job
        test_job, _ = Job.objects.get_or_create(
            job_number='TEST-JOB-001',
            defaults={
                'client': test_client,
                'status': 'in_progress',
                'product': 'Test Product',
                'quantity': 100
            }
        )
        print(f"✓ Job created/retrieved: {test_job.job_number}")
        
        # Get or create test PO
        test_po, _ = PurchaseOrder.objects.get_or_create(
            po_number='TEST-PO-001',
            defaults={
                'job': test_job,
                'vendor': test_vendor,
                'product_type': 'Test Product',
                'quantity': 100,
                'unit_cost': 10.00,
                'total_cost': 1000.00,
                'status': 'ACCEPTED',
                'required_by': (datetime.now() + timedelta(days=7)).date()
            }
        )
        print(f"✓ Purchase Order created/retrieved: {test_po.po_number}")
        
        # TEST 1: Create invoice with minimal data (no line_items)
        print("\n" + "-"*80)
        print("TEST 1: Creating invoice WITHOUT line_items field (should default to [])")
        print("-"*80)
        
        invoice_data = {
            'purchase_order': test_po.id,
            'vendor': test_vendor.id,
            'job': test_job.id,
            'invoice_date': datetime.now().date().isoformat(),
            'due_date': (datetime.now() + timedelta(days=30)).date().isoformat(),
            'status': 'draft'
            # NOTE: line_items NOT provided
        }
        
        serializer = VendorInvoiceDetailedSerializer(data=invoice_data)
        if serializer.is_valid():
            invoice = serializer.save()
            print(f"✓ Invoice created successfully (ID: {invoice.id})")
            print(f"  Invoice Number: {invoice.invoice_number}")
            print(f"  Line Items: {invoice.line_items}")
            print(f"  Subtotal: {invoice.subtotal}")
            assert invoice.line_items == [], "line_items should default to empty list"
            assert invoice.line_items is not None, "line_items should NOT be NULL"
            print("✓ PASS: line_items correctly defaults to []")
        else:
            print(f"✗ FAIL: Serializer validation failed: {serializer.errors}")
            return False
        
        # TEST 2: Create invoice with empty line_items
        print("\n" + "-"*80)
        print("TEST 2: Creating invoice WITH empty line_items = []")
        print("-"*80)
        
        invoice_data2 = {
            'purchase_order': test_po.id,
            'vendor': test_vendor.id,
            'job': test_job.id,
            'invoice_date': datetime.now().date().isoformat(),
            'due_date': (datetime.now() + timedelta(days=30)).date().isoformat(),
            'line_items': [],  # Explicitly empty
            'subtotal': 1000.00,
            'total_amount': 1000.00,
            'status': 'draft'
        }
        
        serializer2 = VendorInvoiceDetailedSerializer(data=invoice_data2)
        if serializer2.is_valid():
            invoice2 = serializer2.save()
            print(f"✓ Invoice created successfully (ID: {invoice2.id})")
            print(f"  Invoice Number: {invoice2.invoice_number}")
            print(f"  Line Items: {invoice2.line_items}")
            print(f"  Subtotal: {invoice2.subtotal}")
            assert invoice2.line_items == [], "line_items should be empty list"
            assert invoice2.line_items is not None, "line_items should NOT be NULL"
            print("✓ PASS: line_items correctly set to []")
        else:
            print(f"✗ FAIL: Serializer validation failed: {serializer2.errors}")
            return False
        
        # TEST 3: Create invoice with sample line_items
        print("\n" + "-"*80)
        print("TEST 3: Creating invoice WITH sample line_items data")
        print("-"*80)
        
        sample_line_items = [
            {'description': 'Printing', 'quantity': 1000, 'unit_price': 0.35, 'amount': 350.00},
            {'description': 'Setup', 'quantity': 1, 'unit_price': 100.00, 'amount': 100.00}
        ]
        
        invoice_data3 = {
            'purchase_order': test_po.id,
            'vendor': test_vendor.id,
            'job': test_job.id,
            'invoice_date': datetime.now().date().isoformat(),
            'due_date': (datetime.now() + timedelta(days=30)).date().isoformat(),
            'line_items': sample_line_items,
            'subtotal': 450.00,
            'tax_rate': 10,
            'tax_amount': 45.00,
            'total_amount': 495.00,
            'status': 'draft'
        }
        
        serializer3 = VendorInvoiceDetailedSerializer(data=invoice_data3)
        if serializer3.is_valid():
            invoice3 = serializer3.save()
            print(f"✓ Invoice created successfully (ID: {invoice3.id})")
            print(f"  Invoice Number: {invoice3.invoice_number}")
            print(f"  Line Items Count: {len(invoice3.line_items)}")
            print(f"  Line Items: {json.dumps(invoice3.line_items, indent=2)}")
            print(f"  Subtotal: {invoice3.subtotal}")
            print(f"  Tax Amount: {invoice3.tax_amount}")
            print(f"  Total: {invoice3.total_amount}")
            assert len(invoice3.line_items) == 2, "Should have 2 line items"
            assert invoice3.line_items is not None, "line_items should NOT be NULL"
            print("✓ PASS: line_items correctly stored with data")
        else:
            print(f"✗ FAIL: Serializer validation failed: {serializer3.errors}")
            return False
        
        print("\n" + "="*80)
        print("✓ ALL TESTS PASSED - IntegrityError Fix Verified!")
        print("="*80)
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_vendor_invoice_creation()
    sys.exit(0 if success else 1)
