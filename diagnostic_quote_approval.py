# Diagnostic script for quote approval issues
# Save this as: clientapp/diagnostic_quote_approval.py
# Run with: python clientapp/diagnostic_quote_approval.py

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'client.settings')
django.setup()

from clientapp.models import Quote, QuoteApprovalToken, Job, LPO, Notification
from django.contrib.auth.models import Group, User
from django.utils import timezone
from datetime import timedelta

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def diagnose_quote_approval():
    """Comprehensive diagnostic for quote approval system"""
    
    print_header("QUOTE APPROVAL SYSTEM DIAGNOSTIC")
    
    # ===== 1. CHECK RECENT APPROVED QUOTES =====
    print_header("1. RECENT APPROVED QUOTES")
    
    recent_quotes = Quote.objects.filter(
        status='Approved',
        approved_at__isnull=False
    ).order_by('-approved_at')[:10]
    
    print(f"📋 Found {recent_quotes.count()} recently approved quotes\n")
    
    if recent_quotes.count() == 0:
        print("⚠️  NO APPROVED QUOTES FOUND!")
        print("   This might mean:")
        print("   - No quotes have been approved yet")
        print("   - Quote approval is not working")
        print("   - The approval flow has an issue\n")
    
    for quote in recent_quotes:
        print(f"Quote: {quote.quote_id}")
        print(f"  Client: {quote.client.name if quote.client else quote.lead.name}")
        print(f"  Approved: {quote.approved_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"  Status: {quote.status}")
        
        # Check if it has a job
        try:
            job = Job.objects.get(quote=quote)
            print(f"  ✅ Job: {job.job_number} (Status: {job.status})")
        except Job.DoesNotExist:
            print(f"  ❌ NO JOB FOUND! (This is the problem!)")
        except Job.MultipleObjectsReturned:
            jobs = Job.objects.filter(quote=quote)
            print(f"  ⚠️  MULTIPLE JOBS FOUND: {jobs.count()}")
            
        # Check if it has an LPO
        try:
            lpo = LPO.objects.get(quote=quote)
            print(f"  ✅ LPO: {lpo.lpo_number} (Status: {lpo.status})")
        except LPO.DoesNotExist:
            print(f"  ❌ NO LPO FOUND! (This is the problem!)")
        except LPO.MultipleObjectsReturned:
            lpos = LPO.objects.filter(quote=quote)
            print(f"  ⚠️  MULTIPLE LPOs FOUND: {lpos.count()}")
        
        print()
    
    # ===== 2. CHECK ALL JOBS =====
    print_header("2. ALL JOBS IN SYSTEM")
    
    total_jobs = Job.objects.count()
    jobs_with_quotes = Job.objects.filter(quote__isnull=False).count()
    jobs_without_quotes = Job.objects.filter(quote__isnull=True).count()
    
    print(f"Total Jobs: {total_jobs}")
    print(f"  - Linked to quotes: {jobs_with_quotes}")
    print(f"  - NOT linked to quotes: {jobs_without_quotes}")
    
    recent_jobs = Job.objects.order_by('-created_at')[:5]
    print(f"\n📦 5 Most Recent Jobs:")
    for job in recent_jobs:
        print(f"  {job.job_number} - {job.job_name}")
        print(f"    Created: {job.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"    Status: {job.status}")
        print(f"    Quote: {job.quote.quote_id if job.quote else 'NO QUOTE'}")
        print()
    
    # ===== 3. CHECK ALL LPOs =====
    print_header("3. ALL LPOs IN SYSTEM")
    
    total_lpos = LPO.objects.count()
    print(f"Total LPOs: {total_lpos}")
    
    recent_lpos = LPO.objects.order_by('-created_at')[:5]
    print(f"\n📄 5 Most Recent LPOs:")
    for lpo in recent_lpos:
        print(f"  {lpo.lpo_number}")
        print(f"    Created: {lpo.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"    Status: {lpo.status}")
        print(f"    Quote: {lpo.quote.quote_id}")
        print(f"    Client: {lpo.client.name}")
        print()
    
    # ===== 4. CHECK PRODUCTION TEAM GROUP =====
    print_header("4. PRODUCTION TEAM GROUP")
    
    try:
        prod_group = Group.objects.get(name='Production Team')
        members = prod_group.user_set.all()
        print(f"✅ Group exists with {members.count()} members\n")
        
        if members.count() == 0:
            print("⚠️  WARNING: Production Team group has NO MEMBERS!")
            print("   This means notifications won't be sent to anyone!")
            print("   ACTION NEEDED: Add users to Production Team group\n")
        else:
            print("Production Team Members:")
            for user in members:
                print(f"  - {user.username} ({user.email})")
                print(f"    Active: {user.is_active}")
                print(f"    Last login: {user.last_login}")
                print()
                
    except Group.DoesNotExist:
        print("❌ PRODUCTION TEAM GROUP NOT FOUND!")
        print("   This is a CRITICAL issue!")
        print("   The approval system tries to send notifications to this group")
        print("   but it doesn't exist!\n")
        print("   ACTION NEEDED: Create 'Production Team' group in admin\n")
    
    # ===== 5. CHECK RECENT NOTIFICATIONS =====
    print_header("5. RECENT QUOTE APPROVAL NOTIFICATIONS")
    
    recent_notifs = Notification.objects.filter(
        notification_type='quote_approved'
    ).order_by('-created_at')[:10]
    
    print(f"🔔 Found {recent_notifs.count()} quote approval notifications\n")
    
    if recent_notifs.count() == 0:
        print("⚠️  NO NOTIFICATIONS FOUND!")
        print("   This might mean:")
        print("   - No quotes have been approved")
        print("   - Notification creation is failing")
        print("   - Production Team group doesn't exist\n")
    
    for notif in recent_notifs:
        print(f"To: {notif.recipient.username} ({notif.recipient.email})")
        print(f"  Title: {notif.title}")
        print(f"  Created: {notif.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"  Read: {'Yes' if notif.is_read else 'No'}")
        print()
    
    # ===== 6. CHECK APPROVAL TOKENS =====
    print_header("6. APPROVAL TOKENS")
    
    total_tokens = QuoteApprovalToken.objects.count()
    used_tokens = QuoteApprovalToken.objects.filter(used=True).count()
    unused_tokens = QuoteApprovalToken.objects.filter(used=False).count()
    
    now = timezone.now()
    expired_tokens = QuoteApprovalToken.objects.filter(
        expires_at__lte=now
    ).count()
    
    valid_tokens = QuoteApprovalToken.objects.filter(
        used=False,
        expires_at__gt=now
    ).count()
    
    print(f"Total Tokens: {total_tokens}")
    print(f"  - Used: {used_tokens}")
    print(f"  - Unused: {unused_tokens}")
    print(f"  - Expired: {expired_tokens}")
    print(f"  - Currently Valid: {valid_tokens}\n")
    
    # Show recent tokens
    recent_tokens = QuoteApprovalToken.objects.order_by('-created_at')[:5]
    print("📝 5 Most Recent Tokens:")
    for token in recent_tokens:
        status = "✅ VALID" if token.is_valid() else "❌ INVALID"
        if token.used:
            status = "✓ USED"
        elif token.expires_at <= now:
            status = "⏰ EXPIRED"
            
        print(f"  {token.quote.quote_id}")
        print(f"    Status: {status}")
        print(f"    Created: {token.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"    Expires: {token.expires_at.strftime('%Y-%m-%d %H:%M')}")
        if token.used:
            print(f"    Used at: {token.used_at.strftime('%Y-%m-%d %H:%M')}")
        print()
    
    # ===== 7. CHECK FOR ORPHANED DATA =====
    print_header("7. DATA INTEGRITY CHECKS")
    
    # Jobs without quotes
    orphan_jobs = Job.objects.filter(quote__isnull=True).count()
    print(f"Jobs without linked quotes: {orphan_jobs}")
    
    # Quotes without jobs (but approved)
    approved_no_job = Quote.objects.filter(
        status='Approved',
        job__isnull=True
    ).count()
    print(f"Approved quotes without jobs: {approved_no_job}")
    if approved_no_job > 0:
        print("  ⚠️  This is a problem! Approved quotes should have jobs.")
    
    # Quotes without LPOs (but approved)
    approved_no_lpo = Quote.objects.filter(
        status='Approved',
        lpo__isnull=True
    ).count()
    print(f"Approved quotes without LPOs: {approved_no_lpo}")
    if approved_no_lpo > 0:
        print("  ⚠️  This is a problem! Approved quotes should have LPOs.")
    
    # ===== SUMMARY =====
    print_header("DIAGNOSTIC SUMMARY")
    
    issues = []
    
    if recent_quotes.count() == 0:
        issues.append("No approved quotes found")
    
    if approved_no_job > 0:
        issues.append(f"{approved_no_job} approved quotes missing jobs")
    
    if approved_no_lpo > 0:
        issues.append(f"{approved_no_lpo} approved quotes missing LPOs")
    
    try:
        prod_group = Group.objects.get(name='Production Team')
        if prod_group.user_set.count() == 0:
            issues.append("Production Team group has no members")
    except Group.DoesNotExist:
        issues.append("Production Team group doesn't exist")
    
    if recent_notifs.count() == 0 and recent_quotes.count() > 0:
        issues.append("No notifications being created for approvals")
    
    if len(issues) == 0:
        print("✅ NO CRITICAL ISSUES FOUND!")
        print("\nThe system appears to be working correctly.")
        print("If users are reporting problems, they might be:")
        print("  - Using expired/used tokens")
        print("  - Looking in the wrong place for jobs/LPOs")
        print("  - Not logged in as Production Team members")
    else:
        print("❌ ISSUES FOUND:\n")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")
        
        print("\n\nRECOMMENDED ACTIONS:")
        print("1. Create 'Production Team' group if it doesn't exist")
        print("2. Add users to Production Team group")
        print("3. Check server logs for errors during quote approval")
        print("4. Test approval flow with a new quote")
        print("5. Review quote_approval_services.py for errors")
    
    print("\n" + "="*60)
    print("Diagnostic complete!")
    print("="*60 + "\n")

if __name__ == "__main__":
    diagnose_quote_approval()
