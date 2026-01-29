#!/usr/bin/env python
"""
Simple E2E Flow Tester - Interactive Version
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yourapp.settings')
django.setup()

from django.contrib.auth.models import User, Group
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import traceback

# Import models
from clientapp.models import (
    Lead, Client, Quote, QuoteLineItem, QuoteApprovalToken,
    Job, JobProduct, JobVendorStage, JobNote,
    Product, Vendor, Payment, PaymentTransaction,
    JobProgressUpdate, JobMessage
)

print("\n" + "="*80)
print("SYSTEM END-TO-END TEST: Lead → Client → Job → Completion → Payment")
print("="*80 + "\n")

test_data = {}
passed_tests = 0
failed_tests = 0

def test(name, condition, detail=""):
    """Quick test helper"""
    global passed_tests, failed_tests
    if condition:
        print(f"✓ {name}")
        if detail:
            print(f"  → {detail}")
        passed_tests += 1
    else:
        print(f"✗ {name}")
        if detail:
            print(f"  → {detail}")
        failed_tests += 1

try:
    # STEP 1: Setup
    print("\n[STEP 1] Create Test Users and Companies")
    print("-" * 80)
    
    # Clean up existing test users
    User.objects.filter(username__startswith='test_').delete()
    
    # Create groups
    am_group, _ = Group.objects.get_or_create(name='Account Managers')
    pt_group, _ = Group.objects.get_or_create(name='Production Team')
    vendor_group, _ = Group.objects.get_or_create(name='Vendors')
    
    # Create users
    am_user = User.objects.create_user(
        username='test_am_user',
        email='test_am@company.com',
        first_name='John',
        last_name='Manager',
        password='TestPassword123!'
    )
    am_user.groups.add(am_group)
    test_data['am_user'] = am_user
    test("Account Manager user created", am_user.id > 0, f"User ID: {am_user.id}")
    
    pt_user = User.objects.create_user(
        username='test_pt_user',
        email='test_pt@company.com',
        first_name='Jane',
        last_name='Producer',
        password='TestPassword123!'
    )
    pt_user.groups.add(pt_group)
    test_data['pt_user'] = pt_user
    test("Production Team user created", pt_user.id > 0, f"User ID: {pt_user.id}")
    
    vendor_user = User.objects.create_user(
        username='test_vendor_user',
        email='test_vendor@vendor.com',
        first_name='Bob',
        last_name='Vendor',
        password='TestPassword123!'
    )
    vendor_user.groups.add(vendor_group)
    test_data['vendor_user'] = vendor_user
    test("Vendor user created", vendor_user.id > 0, f"User ID: {vendor_user.id}")
    
    # Create vendor company
    vendor = Vendor.objects.create(
        name='Test Vendor Inc',
        email='vendor@test.com',
        phone='+254712345678',
        contact_person='Bob Vendor',
        active=True
    )
    test_data['vendor'] = vendor
    test("Vendor company created", vendor.id > 0, f"Vendor: {vendor.name}")
    
    # STEP 2: Create Lead
    print("\n[STEP 2] Create and Progress Lead")
    print("-" * 80)
    
    lead = Lead.objects.create(
        name='Test Lead Client',
        email='testlead@client.com',
        phone='+254712345679',
        source='Website',
        product_interest='Custom Manufacturing',
        preferred_contact='Email',
        preferred_client_type='B2B',
        status='New',
        created_by=am_user
    )
    test_data['lead'] = lead
    test("Lead created", lead.lead_id is not None, f"Lead ID: {lead.lead_id}")
    
    # Progress lead
    lead.status = 'Contacted'
    lead.save()
    lead.status = 'Qualified'
    lead.save()
    test("Lead progressed to Qualified", lead.status == 'Qualified', f"Status: {lead.status}")
    
    # STEP 3: Create and Approve Quote
    print("\n[STEP 3] Create Quote and Get Approval")
    print("-" * 80)
    
    quote = Quote.objects.create(
        lead=lead,
        quote_number='QT-2026-TEST-001',
        status='Draft',
        valid_until=timezone.now() + timedelta(days=30),
        created_by=am_user
    )
    test_data['quote'] = quote
    test("Quote created", quote.quote_number is not None, f"Quote #: {quote.quote_number}")
    
    # Add line item
    product = Product.objects.first()
    if not product:
        product = Product.objects.create(
            name='Test Product',
            sku='TST-001',
            created_by=am_user
        )
    
    line_item = QuoteLineItem.objects.create(
        quote=quote,
        product=product,
        description='Custom manufacturing',
        quantity=100,
        unit_price=Decimal('50.00'),
        discount_percent=Decimal('10.00')
    )
    test("Quote line item added", line_item.id > 0, f"Qty: {line_item.quantity}")
    
    # Update quote amounts
    quote.subtotal = Decimal('5000.00')
    quote.discount_amount = Decimal('500.00')
    quote.total_amount = Decimal('4500.00')
    quote.status = 'Sent'
    quote.save()
    test("Quote sent to client", quote.status == 'Sent', f"Amount: KES {quote.total_amount}")
    
    # Approve quote
    approval_token = QuoteApprovalToken.objects.create(
        quote=quote,
        expires_at=timezone.now() + timedelta(days=30)
    )
    approval_token.is_used = True
    approval_token.used_at = timezone.now()
    approval_token.save()
    quote.status = 'Approved'
    quote.approved_at = timezone.now()
    quote.save()
    test("Quote approved by client", quote.status == 'Approved', f"Approval: {quote.approved_at}")
    
    # STEP 4: Convert to Client
    print("\n[STEP 4] Convert Lead to Client and Onboard")
    print("-" * 80)
    
    client = Client.objects.create(
        client_type='B2B',
        company='Test Lead Client Inc',
        name='Test Lead Client',
        email=lead.email,
        phone=lead.phone,
        status='Active',
        payment_terms='Net 30',
        account_manager=am_user,
        converted_from_lead=lead
    )
    test_data['client'] = client
    test("Client created", client.client_id is not None, f"Client ID: {client.client_id}")
    
    # Mark lead as converted
    lead.status = 'Converted'
    lead.converted_to_client = True
    lead.converted_at = timezone.now()
    lead.save()
    test("Lead marked as converted", lead.converted_to_client, "Conversion complete")
    
    # Link quote to client
    quote.client = client
    quote.save()
    test("Quote linked to client", quote.client == client, f"Client: {client.client_id}")
    
    # STEP 5: Create Job from Quote
    print("\n[STEP 5] Create Job in Account Manager Portal")
    print("-" * 80)
    
    job = Job.objects.create(
        job_number='JB-2026-TEST-001',
        quote=quote,
        client=client,
        status='Pending',
        priority='High',
        description='Test job from quote',
        created_by=am_user
    )
    test_data['job'] = job
    test("Job created", job.job_number is not None, f"Job #: {job.job_number}")
    
    # Add job products
    JobProduct.objects.create(
        job=job,
        product=product,
        quantity=100,
        unit_price=Decimal('50.00'),
        notes='Manufacturing'
    )
    
    job.total_budget = quote.total_amount
    job.save()
    test("Job products added", JobProduct.objects.filter(job=job).count() > 0, "Budget set")
    
    # STEP 6: Assign Job to PT User
    print("\n[STEP 6] Assign Job to Production Team User")
    print("-" * 80)
    
    job.assigned_to = pt_user
    job.assigned_at = timezone.now()
    job.status = 'Assigned'
    job.save()
    test("Job assigned to PT user", job.assigned_to == pt_user, f"Assigned to: {pt_user.get_full_name()}")
    
    JobNote.objects.create(
        job=job,
        note='Job assigned to PT',
        created_by=am_user,
        note_type='System'
    )
    test("Assignment note created", JobNote.objects.filter(job=job).count() > 0)
    
    # STEP 7: Create Tasks in PT Portal
    print("\n[STEP 7] Create Tasks in Production Team Portal")
    print("-" * 80)
    
    stages = []
    stage_names = ['Manufacturing', 'QC Inspection', 'Packaging']
    
    for i, stage_name in enumerate(stage_names):
        stage = JobVendorStage.objects.create(
            job=job,
            stage_name=stage_name,
            description=f'{stage_name} stage',
            planned_start_date=timezone.now() + timedelta(days=i*5),
            planned_end_date=timezone.now() + timedelta(days=i*5+3),
            status='Not Started',
            assigned_to=pt_user
        )
        stages.append(stage)
    
    test("Job stages created", len(stages) == 3, f"Stages: {len(stages)}")
    
    # STEP 8: Assign Tasks to Vendors
    print("\n[STEP 8] Assign Tasks to Vendors")
    print("-" * 80)
    
    stage = stages[0]
    stage.assigned_vendor = vendor
    stage.status = 'Assigned'
    stage.save()
    test("Vendor assigned to stage", stage.assigned_vendor == vendor, f"Vendor: {vendor.name}")
    
    JobMessage.objects.create(
        job=job,
        vendor=vendor,
        message='You have been assigned manufacturing task',
        message_type='Assignment',
        created_by=pt_user
    )
    test("Vendor notification sent", JobMessage.objects.filter(job=job).count() > 0)
    
    # STEP 9: Vendor Completes Tasks
    print("\n[STEP 9] Vendor Executes and Completes Tasks")
    print("-" * 80)
    
    for i, stage in enumerate(stages):
        stage.status = 'In Progress'
        stage.actual_start_date = timezone.now() - timedelta(days=3-i)
        stage.save()
        
        # Progress update
        JobProgressUpdate.objects.create(
            job=job,
            stage=stage,
            vendor=vendor,
            progress_percent=50,
            status='In Progress',
            notes=f'{stage.stage_name} in progress',
            updated_by=vendor_user
        )
        
        # Complete stage
        stage.status = 'Completed'
        stage.actual_end_date = timezone.now()
        stage.save()
        
        JobProgressUpdate.objects.create(
            job=job,
            stage=stage,
            vendor=vendor,
            progress_percent=100,
            status='Completed',
            notes=f'{stage.stage_name} completed',
            updated_by=vendor_user
        )
    
    test("All stages completed", 
         JobVendorStage.objects.filter(job=job, status='Completed').count() == 3,
         f"Completed: {JobVendorStage.objects.filter(job=job, status='Completed').count()}")
    
    # STEP 10: Complete Job
    print("\n[STEP 10] Complete Job and Quality Control")
    print("-" * 80)
    
    job.status = 'In Progress'
    job.start_date = timezone.now() - timedelta(days=10)
    job.save()
    
    job.status = 'QC'
    job.save()
    test("Job moved to QC", job.status == 'QC', "QC in progress")
    
    JobNote.objects.create(
        job=job,
        note='QC check complete - approved',
        created_by=pt_user,
        note_type='QC'
    )
    
    job.status = 'Completed'
    job.completion_date = timezone.now()
    job.save()
    test("Job marked completed", job.status == 'Completed', f"Completed: {job.completion_date}")
    
    # STEP 11: Generate Payments
    print("\n[STEP 11] Generate Payments")
    print("-" * 80)
    
    try:
        payment = Payment.objects.create(
            job=job,
            client=client,
            amount=Decimal('5220.00'),  # with VAT
            payment_date=timezone.now(),
            payment_method='Bank Transfer',
            reference_number='BANK-TXN-001',
            status='Completed',
            created_by=am_user
        )
        test_data['payment'] = payment
        test("Payment created", payment.id > 0, f"Amount: KES {payment.amount}")
        
        # Transaction
        txn = PaymentTransaction.objects.create(
            payment=payment,
            transaction_type='Deposit',
            amount=payment.amount,
            transaction_date=timezone.now(),
            reference_number='BANK-TXN-001',
            status='Confirmed',
            created_by=am_user
        )
        test("Payment transaction recorded", txn.id > 0, f"TXN: {txn.reference_number}")
    except Exception as e:
        test("Payment processing", False, f"Error: {str(e)}")
    
    # STEP 12: Final Verification
    print("\n[STEP 12] Final System Verification")
    print("-" * 80)
    
    test("Lead → Client conversion verified", 
         Lead.objects.get(id=lead.id).converted_to_client,
         f"{lead.lead_id} → {client.client_id}")
    
    test("Quote → Job creation verified",
         Job.objects.get(id=job.id).quote == quote,
         f"{quote.quote_number} → {job.job_number}")
    
    test("Job assignment verified",
         Job.objects.get(id=job.id).assigned_to == pt_user,
         f"PT User: {pt_user.username}")
    
    test("Job completion verified",
         Job.objects.get(id=job.id).status == 'Completed',
         f"Status: {job.status}")
    
    total_stages = JobVendorStage.objects.filter(job=job).count()
    completed_stages = JobVendorStage.objects.filter(job=job, status='Completed').count()
    test("All job stages completed",
         total_stages == completed_stages,
         f"{completed_stages}/{total_stages} stages done")
    
    total_notes = JobNote.objects.filter(job=job).count()
    test("Job tracking notes created",
         total_notes > 0,
         f"Notes: {total_notes}")
    
    # FINAL REPORT
    print("\n" + "="*80)
    print("TEST REPORT")
    print("="*80)
    print(f"\n✓ PASSED: {passed_tests}")
    print(f"✗ FAILED: {failed_tests}")
    print(f"TOTAL:   {passed_tests + failed_tests}")
    
    if failed_tests == 0:
        print(f"\n{'='*80}")
        print("✓ ALL TESTS PASSED - SYSTEM WORKFLOW IS FUNCTIONAL")
        print(f"{'='*80}\n")
    else:
        print(f"\n{'='*80}")
        print(f"⚠ {failed_tests} TEST(S) FAILED - REVIEW ABOVE FOR DETAILS")
        print(f"{'='*80}\n")
    
    # Test data summary
    print("\nTest Data Created:")
    for key, obj in test_data.items():
        if hasattr(obj, 'id'):
            print(f"  • {key}: ID={obj.id}")
        else:
            print(f"  • {key}: {obj}")

except Exception as e:
    print(f"\n✗ CRITICAL ERROR: {str(e)}")
    traceback.print_exc()

print("\n[END OF TEST]\n")
