import json
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg, Count, Q, Sum
from django.urls import reverse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from functools import wraps

from .forms import (
    LeadForm,
    ClientForm,
    ProductForm,
    QuoteCostingForm,
    ProductionUpdateForm,
)
from .models import (
    Lead,
    Client,
    ClientContact,
    ComplianceDocument,
    Product,
    Quote,
    ActivityLog,
    ProductionUpdate,
    Notification,
    Job,
    JobProduct,
)


def group_required(group_name, allow_superuser=False):
    """
    Require authenticated user to belong to group_name.
    Redirect anonymous users to login, and show a friendly redirect for
    authenticated users without permission.
    """
    login_url = getattr(settings, 'LOGIN_URL', '/accounts/login/')

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect(f"{login_url}?next={request.get_full_path()}")
            if allow_superuser and user.is_superuser:
                return view_func(request, *args, **kwargs)
            if user.groups.filter(name=group_name).exists():
                return view_func(request, *args, **kwargs)

            messages.warning(request, "You don't have access to that section.")
            fallback_name = 'dashboard'
            if user.groups.filter(name='Production Team').exists():
                fallback_name = 'production_dashboard2'
            return redirect(reverse(fallback_name))
        return _wrapped
    return decorator


@login_required
def search(request):
    """Global search for clients, leads, quotes, and jobs"""
    q = request.GET.get('q', '').strip()
    clients = leads = quotes = jobs = []
    if q:
        clients = Client.objects.filter(
            Q(name__icontains=q) | Q(company__icontains=q) | Q(email__icontains=q) | Q(client_id__icontains=q)
        ).order_by('name')[:25]
        leads = Lead.objects.filter(
            Q(name__icontains=q) | Q(email__icontains=q) | Q(lead_id__icontains=q)
        ).order_by('-created_at')[:25]
        quotes = Quote.objects.filter(
            Q(quote_id__icontains=q) | Q(product_name__icontains=q)
        ).select_related('client', 'lead').order_by('-created_at')[:25]
        jobs = Job.objects.filter(
            Q(job_number__icontains=q) | Q(job_name__icontains=q) | Q(product__icontains=q)
        ).select_related('client').order_by('-created_at')[:25]

    context = {
        'q': q,
        'clients': clients,
        'leads': leads,
        'quotes': quotes,
        'jobs': jobs,
        'current_view': 'search',
    }
    return render(request, 'search_results.html', context)


@login_required
@group_required('Account Manager')
def edit_client(request, pk):
    """Edit client details (Account Manager)"""
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Client updated successfully.')
            return redirect('client_profile', pk=client.pk)
    else:
        form = ClientForm(instance=client)

    return render(request, 'client_edit.html', {
        'form': form,
        'client': client,
        'current_view': 'clients',
    })


    

def group_required(group_name, allow_superuser=False):
    """
    Require authenticated user to belong to group_name.
    - redirects anonymous users to settings.LOGIN_URL (with ?next=...)
    - returns 403 for authenticated users not in the group
    - allow_superuser=False by default so superusers do NOT bypass unless you opt in
    """
    login_url = getattr(settings, 'LOGIN_URL', '/accounts/login/')

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect(f"{login_url}?next={request.get_full_path()}")
            if allow_superuser and user.is_superuser:
                return view_func(request, *args, **kwargs)
            if user.groups.filter(name=group_name).exists():
                return view_func(request, *args, **kwargs)

            # Graceful redirect instead of 403
            messages.warning(request, "You don't have access to that section.")

            # Determine best fallback based on user's groups
            fallback_name = 'dashboard'
            if user.groups.filter(name='Production Team').exists():
                fallback_name = 'production_dashboard2'
            elif user.groups.filter(name='Account Manager').exists():
                fallback_name = 'dashboard'

            return redirect(reverse(fallback_name))
        return _wrapped
    return decorator


@login_required
def dashboard(request):
    """
    Unified Dashboard - Combines main dashboard + production metrics
    Accessible to all authenticated users
    """
    # Redirect Finance users to their own dashboard
    if request.user.is_authenticated and request.user.groups.filter(name='Finance').exists():
        return redirect('finance_dashboard')
    from django.db.models import Count, Sum, Q
    from datetime import datetime, timedelta
    
    # ========== EXISTING LEAD/CLIENT METRICS ==========
    total_leads = Lead.objects.count()
    converted_leads = Lead.objects.filter(status='Converted').count()
    active_clients = Client.objects.filter(status='Active').count()
    b2b_clients = Client.objects.filter(client_type='B2B').count()
    
    # ========== PRODUCTION METRICS (MERGED FROM PRODUCTION DASHBOARD) ==========
    from .models import Job, Quote
    
    # Job Statistics
    total_jobs = Job.objects.count()
    pending_jobs = Job.objects.filter(status='pending').count()
    in_progress_jobs = Job.objects.filter(status='in_progress').count()
    completed_jobs = Job.objects.filter(status='completed').count()
    
    # Quote Statistics
    total_quotes = Quote.objects.count()
    draft_quotes = Quote.objects.filter(status='Draft').count()
    pending_quotes = Quote.objects.filter(status='Quoted').count()
    approved_quotes = Quote.objects.filter(status='Approved').count()
    
    # Revenue from approved quotes
    total_revenue = Quote.objects.filter(status='Approved').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Calculate quote conversion rate
    sent_quotes = Quote.objects.filter(status__in=['Quoted', 'Client Review', 'Approved', 'Lost']).count()
    conversion_rate = round((approved_quotes / sent_quotes * 100), 1) if sent_quotes > 0 else 0
    
    # Top Product Interests from leads
    product_interests = Lead.objects.exclude(product_interest='').values('product_interest').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    total_with_interest = sum(item['count'] for item in product_interests)
    top_products = []
    if total_with_interest > 0:
        for item in product_interests:
            percentage = round((item['count'] / total_with_interest) * 100)
            top_products.append({
                'name': item['product_interest'],
                'interest': percentage
            })
    else:
        top_products = [
            {'name': 'Business Cards', 'interest': 85},
            {'name': 'Brochures', 'interest': 72},
            {'name': 'Banners & Signage', 'interest': 68},
            {'name': 'Packaging', 'interest': 54},
            {'name': 'Corporate Stationery', 'interest': 45},
        ]
    
    # Recent Activity - Mix of leads, clients, jobs, and quotes
    recent_activity = []
    
    # Recent clients
    recent_clients = Client.objects.order_by('-created_at')[:2]
    for client in recent_clients:
        time_diff = datetime.now() - client.created_at.replace(tzinfo=None)
        time_str = format_time_diff(time_diff)
        recent_activity.append({
            'client': client.company if client.company else client.name,
            'action': 'Profile Activated',
            'time': time_str,
            'type': client.client_type
        })
    
    # Recent jobs
    recent_jobs = Job.objects.order_by('-created_at')[:2]
    for job in recent_jobs:
        time_diff = datetime.now() - job.created_at.replace(tzinfo=None)
        time_str = format_time_diff(time_diff)
        recent_activity.append({
            'client': job.client.name,
            'action': f'Job Created - {job.product}',
            'time': time_str,
            'type': 'Job'
        })
    
    # Recent quotes
    recent_quotes = Quote.objects.filter(status='Quoted').order_by('-created_at')[:2]
    for quote in recent_quotes:
        time_diff = datetime.now() - quote.created_at.replace(tzinfo=None)
        time_str = format_time_diff(time_diff)
        client_name = quote.client.name if quote.client else quote.lead.name
        recent_activity.append({
            'client': client_name,
            'action': f'Quote {quote.quote_id} Sent',
            'time': time_str,
            'type': 'Quote'
        })
    
    # Sort by most recent
    recent_activity = sorted(recent_activity, key=lambda x: x['time'])[:6]
    
    # Lifecycle status
    dormant_clients = Client.objects.filter(status='Dormant').count()
    inactive_clients = Client.objects.filter(status='Inactive').count()
    
    # Calculate average onboarding time
    converted_with_dates = Lead.objects.filter(status='Converted').exclude(created_at=None)
    if converted_with_dates.exists():
        total_time = 0
        count = 0
        for lead in converted_with_dates:
            try:
                client = Client.objects.filter(email=lead.email).first()
                if client:
                    time_diff = (client.created_at - lead.created_at).days
                    if time_diff >= 0:
                        total_time += time_diff
                        count += 1
            except:
                pass
        avg_onboarding = round(total_time / count, 1) if count > 0 else 2.3
    else:
        avg_onboarding = 2.3
    
    context = {
        'current_view': 'dashboard',
        
        # Lead/Client Metrics
        'total_leads': total_leads,
        'converted_leads': converted_leads,
        'active_clients': active_clients,
        'b2b_clients': b2b_clients,
        
        # Production Metrics (NEW)
        'total_jobs': total_jobs,
        'pending_jobs': pending_jobs,
        'in_progress_jobs': in_progress_jobs,
        'completed_jobs': completed_jobs,
        'total_quotes': total_quotes,
        'draft_quotes': draft_quotes,
        'pending_quotes': pending_quotes,
        'approved_quotes': approved_quotes,
        'total_revenue': total_revenue,
        'conversion_rate': conversion_rate,
        
        # Shared Data
        'recent_activity': recent_activity,
        'top_products': top_products,
        'dormant_clients': dormant_clients,
        'inactive_clients': inactive_clients,
        'avg_onboarding': avg_onboarding,
        'notifications': Notification.objects.filter(recipient=request.user).order_by('-created_at')[:5] if request.user.is_authenticated else [],
        'unread_notifications_count': Notification.objects.filter(recipient=request.user, is_read=False).count() if request.user.is_authenticated else 0,
    }
    return render(request, 'dashboard.html', context)


def format_time_diff(time_diff):
    """Helper function to format time differences"""
    if time_diff.days > 0:
        return f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
    elif time_diff.seconds // 3600 > 0:
        hours = time_diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    else:
        minutes = time_diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"


# ========== ACCOUNT MANAGER VIEWS ==========

@group_required('Account Manager')
def quote_management(request):
    """
    Quote Management - Account Manager only
    This is the ONLY view under Production tab for AM
    """
    from django.db.models import Count, Sum
    from decimal import Decimal
    
    # Get all quotes with aggregations
    all_quotes = Quote.objects.select_related('client', 'lead', 'created_by').order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status', 'All')
    if status_filter != 'All':
        all_quotes = all_quotes.filter(status=status_filter)
    
    # Group quotes by quote_id
    quotes_dict = {}
    for quote in all_quotes:
        if quote.quote_id not in quotes_dict:
            quotes_dict[quote.quote_id] = {
                'quote': quote,
                'items': [],
                'total_amount': Decimal('0'),
                'subtotal': Decimal('0')
            }
        quotes_dict[quote.quote_id]['items'].append(quote)
        quotes_dict[quote.quote_id]['total_amount'] += quote.total_amount
        quotes_dict[quote.quote_id]['subtotal'] += (quote.unit_price * quote.quantity)
    
    quotes_list = list(quotes_dict.values())
    
    # Quote statistics
    quote_stats = {
        'total': len(quotes_list),
        'draft': Quote.objects.filter(status='Draft').values('quote_id').distinct().count(),
        'quoted': Quote.objects.filter(status='Quoted').values('quote_id').distinct().count(),
        'approved': Quote.objects.filter(status='Approved').values('quote_id').distinct().count(),
        'lost': Quote.objects.filter(status='Lost').values('quote_id').distinct().count(),
    }
    
    # Calculate total values
    total_value = sum(q['total_amount'] for q in quotes_list)
    approved_value = Quote.objects.filter(status='Approved').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    clients = Client.objects.filter(status='Active').order_by('name')
    leads = Lead.objects.exclude(status__in=['Converted', 'Lost']).order_by('name')
    products = Product.objects.filter(is_active=True).order_by('name')

    context = {
        'current_view': 'quote_management',
        'quotes': quotes_list,
        'quote_stats': quote_stats,
        'status_filter': status_filter,
        'total_value': total_value,
        'approved_value': approved_value,
        'clients': clients,
        'leads': leads,
        'products': products,
    }
    
    return render(request, 'quote_management.html', context)


# ========== STANDALONE VIEWS (NEW SIDEBAR ITEMS) ==========

@group_required('Account Manager')
def analytics(request):
    """
    Analytics Dashboard - Standalone tab on main sidebar
    Shows comprehensive business analytics
    """
    from django.db.models import Count, Sum, Avg, Q
    from datetime import datetime, timedelta
    from decimal import Decimal
    
    # Date ranges
    today = datetime.now().date()
    thirty_days_ago = today - timedelta(days=30)
    ninety_days_ago = today - timedelta(days=90)
    
    # ========== SALES ANALYTICS ==========
    # Revenue trends (last 6 months)
    revenue_by_month = []
    for i in range(6):
        month_start = today.replace(day=1) - timedelta(days=30*i)
        month_revenue = Quote.objects.filter(
            status='Approved',
            approved_at__year=month_start.year,
            approved_at__month=month_start.month
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        revenue_by_month.insert(0, {
            'month': month_start.strftime('%b'),
            'revenue': float(month_revenue)  # ✅ FIXED: was revenue_revenue
        })
    
    # ========== QUOTE ANALYTICS ==========
    # Quote conversion funnel
    total_quotes = Quote.objects.values('quote_id').distinct().count()
    quoted = Quote.objects.filter(status='Quoted').values('quote_id').distinct().count()
    client_review = Quote.objects.filter(status='Client Review').values('quote_id').distinct().count()
    approved = Quote.objects.filter(status='Approved').values('quote_id').distinct().count()
    lost = Quote.objects.filter(status='Lost').values('quote_id').distinct().count()
    
    conversion_rate = round((approved / total_quotes * 100), 1) if total_quotes > 0 else 0
    
    # Average quote value
    avg_quote_value = Quote.objects.filter(status='Approved').aggregate(
        avg=Avg('total_amount')
    )['avg'] or 0
    
    # ========== CLIENT ANALYTICS ==========
    # Client acquisition trend
    new_clients_30d = Client.objects.filter(created_at__gte=thirty_days_ago).count()
    new_clients_90d = Client.objects.filter(created_at__gte=ninety_days_ago).count()
    
    # Client type breakdown
    b2b_count = Client.objects.filter(client_type='B2B').count()
    b2c_count = Client.objects.filter(client_type='B2C').count()
    
    # Top clients by revenue
    top_clients = Client.objects.annotate(
        total_revenue=Sum('quotes__total_amount', filter=Q(quotes__status='Approved'))
    ).filter(total_revenue__isnull=False).order_by('-total_revenue')[:10]
    
    # ========== PRODUCT ANALYTICS ==========
    # Top products by quote count
    top_products = Quote.objects.filter(status='Approved').values('product_name').annotate(
        count=Count('id'),
        revenue=Sum('total_amount')
    ).order_by('-revenue')[:10]
    
    # ========== LEAD ANALYTICS ==========
    # Lead conversion funnel
    total_leads = Lead.objects.count()
    qualified_leads = Lead.objects.filter(status='Qualified').count()
    converted_leads = Lead.objects.filter(status='Converted').count()
    lost_leads = Lead.objects.filter(status='Lost').count()
    
    lead_conversion_rate = round((converted_leads / total_leads * 100), 1) if total_leads > 0 else 0
    
    # Lead sources performance
    lead_sources = Lead.objects.values('source').annotate(
        count=Count('id'),
        converted=Count('id', filter=Q(status='Converted'))
    ).order_by('-count')[:5]
    
    context = {
        'current_view': 'analytics',
        
        # Sales Analytics
        'revenue_by_month': revenue_by_month,
        'total_revenue': sum(m['revenue'] for m in revenue_by_month),
        
        # Quote Analytics
        'total_quotes': total_quotes,
        'conversion_rate': conversion_rate,
        'avg_quote_value': avg_quote_value,
        'quote_funnel': {
            'quoted': quoted,
            'client_review': client_review,
            'approved': approved,
            'lost': lost,
        },
        
        # Client Analytics
        'new_clients_30d': new_clients_30d,
        'new_clients_90d': new_clients_90d,
        'b2b_count': b2b_count,
        'b2c_count': b2c_count,
        'top_clients': top_clients,
        
        # Product Analytics
        'top_products': top_products,
        
        # Lead Analytics
        'total_leads': total_leads,
        'lead_conversion_rate': lead_conversion_rate,
        'lead_sources': lead_sources,
    }
    
    return render(request, 'analytics.html', context)


@group_required('Account Manager')
def product_catalog(request):
    """Product catalog view for account managers (read-only)"""

    search = request.GET.get('search', '').strip()
    product_type = request.GET.get('product_type', 'all')
    availability = request.GET.get('availability', 'all')

    products = Product.objects.filter(is_active=True)

    if search:
        products = products.filter(Q(name__icontains=search) | Q(sku__icontains=search))

    if product_type != 'all':
        products = products.filter(product_type=product_type)

    if availability != 'all':
        products = products.filter(availability=availability)
    
    context = {
        'current_view': 'product_catalog',
        'products': products.order_by('name'),
        'search': search,
        'product_type': product_type,
        'availability': availability,
    }
    
    return render(request, 'product_catalog.html', context)


# ========== PRODUCTION TEAM VIEWS (Keep existing) ==========




def lead_intake(request):
    """Lead intake and qualification view"""
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            lead = form.save()
            messages.success(request, f'Lead {lead.lead_id} created successfully')
            return redirect('lead_intake')
        else:
            messages.error(request, 'Please fill in all required fields')
    else:
        form = LeadForm()
    
    # Search and filter
    search_query = request.GET.get('search', '')
    leads = Lead.objects.all()
    
    if search_query:
        leads = leads.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(lead_id__icontains=search_query)
        )
    
    products = Product.objects.filter(is_active=True).order_by('name')

    context = {
        'current_view': 'leads',
        'leads': leads,
        'form': form,
        'search_query': search_query,
        'products': products,
    }
    return render(request, 'lead_intake.html', context)


def qualify_lead(request, lead_id):
    """Qualify a lead"""
    lead = get_object_or_404(Lead, lead_id=lead_id)
    lead.status = 'Qualified'
    lead.save()
    messages.success(request, f'Lead {lead.lead_id} qualified successfully')
    return redirect('lead_intake')


def convert_lead(request, lead_id):
    """Convert lead to client"""
    lead = get_object_or_404(Lead, lead_id=lead_id)
    lead.status = 'Converted'
    lead.save()
    
    # Pre-fill client form with lead data
    prefilled_data = {
        'name': lead.name,
        'email': lead.email,
        'phone': lead.phone,
        'lead_source': lead.source if hasattr(lead, 'source') else '',
    }
    
    # Only add preferred_contact if it exists in the Lead model
    if hasattr(lead, 'preferred_contact'):
        prefilled_data['preferred_channel'] = lead.preferred_contact
    
    request.session['prefilled_lead'] = prefilled_data
    messages.info(request, f'Converting lead {lead.name} to client')
    return redirect('client_onboarding')

def client_onboarding(request):
    """Client onboarding workflow - Matches HTML template B2B/B2C structure"""
    prefilled_data = request.session.get('prefilled_lead', None)
    
    if request.method == 'POST':
        client_type = request.POST.get('client_type', 'B2B')
        
        try:
            if client_type == 'B2C':
                # ============ B2C SIMPLIFIED ONBOARDING - SINGLE STEP ============
                # B2C Template Fields (all with _b2c suffix):
                # 1. Company Name (Optional)
                # 2. Contact Person (Required)
                # 3. Email (Required)
                # 4. Phone (Required)
                # 5. Preferred Channel
                # 6. Lead Source
                # Then: Save Client button (no steps)
                
                company = request.POST.get('company_b2c', '').strip()  # Optional
                name = request.POST.get('name_b2c', '').strip()  # Required
                email = request.POST.get('email_b2c', '').strip()  # Optional now
                phone = request.POST.get('phone_b2c', '').strip()  # Required
                preferred_channel = request.POST.get('preferred_channel_b2c', 'Email')
                lead_source = request.POST.get('lead_source_b2c', '')
                
                # Validate required B2C fields (only name, email, phone)
                if not name:
                    messages.error(request, 'Contact Person is required')
                    return redirect('client_onboarding')
                if not phone:
                    messages.error(request, 'Phone is required')
                    return redirect('client_onboarding')
                
                # Check for duplicate email only if provided
                if email and Client.objects.filter(email=email).exists():
                    messages.error(request, f'A client with email {email} already exists')
                    return redirect('client_onboarding')
                
                # Create B2C client - Single step, no complexity
                client = Client.objects.create(
                    client_type='B2C',
                    company=company if company else '',  # Optional
                    name=name,
                    email=email or '',
                    phone=phone,
                    preferred_channel=preferred_channel,
                    lead_source=lead_source,
                    payment_terms='Prepaid',  # B2C always prepaid (hardcoded)
                    risk_rating='Low',  # Default for B2C
                    credit_limit=0,  # No credit for B2C
                    is_reseller=False,  # B2C never resellers
                    status='Active',
                    onboarded_by=request.user,
                    account_manager=request.user
                )
                
                # Log activity
                ActivityLog.objects.create(
                    client=client,
                    activity_type='Note',
                    title=f"B2C Client Profile Created",
                    description=f"B2C client {client.name} onboarded successfully.",
                    created_by=request.user
                )
                
                # Clear session data
                if 'prefilled_lead' in request.session:
                    del request.session['prefilled_lead']
                
                messages.success(request, f'B2C Client {client.client_id} created successfully!')
                return redirect('client_profile', pk=client.pk)
                
            else:
                # ============ B2B FULL ONBOARDING - 3 STEPS ============
                # Step 1: Core Details (Company, Contact, Email, Phone + Financial)
                # Step 2: Contacts & Brand Assets (Optional)
                # Step 3: Compliance Documents (Optional)
                # Then: Save Client button
                
                # STEP 1: Core Details - B2B fields (NO _b2c suffix)
                company = request.POST.get('company', '').strip()  # Required
                name = request.POST.get('name', '').strip()  # Required
                email = request.POST.get('email', '').strip()  # Required
                phone = request.POST.get('phone', '').strip()  # Required
                preferred_channel = request.POST.get('preferred_channel', 'Email')
                lead_source = request.POST.get('lead_source', '')
                
                # Financial fields (B2B only)
                vat_tax_id = request.POST.get('vat_tax_id', '')
                payment_terms = request.POST.get('payment_terms', 'Prepaid')
                risk_rating = request.POST.get('risk_rating', 'Low')
                is_reseller = request.POST.get('is_reseller') == 'on'
                
                # Validate required B2B fields
                if not company:
                    messages.error(request, 'Company Name is required')
                    return redirect('client_onboarding')
                if not name:
                    messages.error(request, 'Contact Person is required')
                    return redirect('client_onboarding')
                if not email:
                    messages.error(request, 'Email is required')
                    return redirect('client_onboarding')
                if not phone:
                    messages.error(request, 'Phone is required')
                    return redirect('client_onboarding')
                
                # Check for duplicate email
                if Client.objects.filter(email=email).exists():
                    messages.error(request, f'A client with email {email} already exists')
                    return redirect('client_onboarding')
                
                # Create B2B client with Step 1 data
                client = Client.objects.create(
                    client_type='B2B',
                    company=company,
                    name=name,
                    email=email,
                    phone=phone,
                    preferred_channel=preferred_channel,
                    lead_source=lead_source,
                    vat_tax_id=vat_tax_id,
                    payment_terms=payment_terms,
                    risk_rating=risk_rating,
                    is_reseller=is_reseller,
                    status='Active',
                    onboarded_by=request.user,
                    account_manager=request.user
                )
                
                # STEP 2: Contacts & Brand Assets (OPTIONAL - may be empty)
                contact_names = request.POST.getlist('contact_name[]')
                contact_emails = request.POST.getlist('contact_email[]')
                contact_phones = request.POST.getlist('contact_phone[]')
                contact_roles = request.POST.getlist('contact_role[]')
                
                # Only create contacts if data provided
                for i, contact_name in enumerate(contact_names):
                    if contact_name.strip():
                        ClientContact.objects.create(
                            client=client,
                            full_name=contact_name.strip(),
                            email=contact_emails[i].strip() if i < len(contact_emails) else '',
                            phone=contact_phones[i].strip() if i < len(contact_phones) else '',
                            role=contact_roles[i] if i < len(contact_roles) else 'None',
                        )
                
                # STEP 3: Compliance Documents (OPTIONAL - may be empty)
                compliance_files = request.FILES.getlist('compliance_files')
                doc_type = request.POST.get('doc_type', '')
                doc_expiry = request.POST.get('doc_expiry', None)
                
                # Only create compliance docs if files uploaded AND doc_type selected
                if compliance_files and doc_type:
                    for file in compliance_files:
                        ComplianceDocument.objects.create(
                            client=client,
                            document_type=doc_type,
                            file=file,
                            expiry_date=doc_expiry if doc_expiry else None,
                            uploaded_by=request.user
                        )

                # BRAND ASSETS (OPTIONAL)
                brand_files = request.FILES.getlist('brand_files')
                brand_asset_type = request.POST.get('brand_asset_type', 'Logo')
                if brand_files:
                    for file in brand_files:
                        BrandAsset.objects.create(
                            client=client,
                            asset_type=brand_asset_type if brand_asset_type else 'Logo',
                            file=file,
                            description=''
                        )
                
                # BRAND ASSETS (OPTIONAL)
                brand_files = request.FILES.getlist('brand_files')
                brand_type = request.POST.get('brand_type', '')
                if brand_files and brand_type:
                    from .models import BrandAsset
                    for file in brand_files:
                        BrandAsset.objects.create(
                            client=client,
                            asset_type=brand_type,
                            file=file,
                            description='',
                            uploaded_by=request.user
                        )
                
                # Log activity
                ActivityLog.objects.create(
                    client=client,
                    activity_type='Note',
                    title=f"B2B Client Profile Created",
                    description=f"B2B client {client.company} onboarded successfully.",
                    created_by=request.user
                )
                
                # Clear session data
                if 'prefilled_lead' in request.session:
                    del request.session['prefilled_lead']
                
                messages.success(request, f'B2B Client {client.client_id} created successfully!')
                return redirect('client_profile', pk=client.pk)
        
        except Exception as e:
            messages.error(request, f'Error creating client: {str(e)}')
            import traceback
            print(traceback.format_exc())
            return redirect('client_onboarding')
    
    # GET request - show form
    form = ClientForm(initial=prefilled_data) if prefilled_data else ClientForm()
    
    context = {
        'current_view': 'onboarding',
        'form': form,
        'prefilled_lead': prefilled_data,
    }
    return render(request, 'client_onboarding.html', context)
def client_list(request):
    """Client list view with filters"""
    # Get filter parameters
    search_query = request.GET.get('search', '')
    filter_type = request.GET.get('type', 'All')
    filter_status = request.GET.get('status', 'All')
    
    clients = Client.objects.all()
    
    # Apply filters
    if search_query:
        clients = clients.filter(
            Q(name__icontains=search_query) |
            Q(company__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(client_id__icontains=search_query)
        )
    
    if filter_type != 'All':
        clients = clients.filter(client_type=filter_type)
    
    if filter_status != 'All':
        clients = clients.filter(status=filter_status)
    
    context = {
        'current_view': 'clients',
        'clients': clients,
        'search_query': search_query,
        'filter_type': filter_type,
        'filter_status': filter_status,
    }
    return render(request, 'client_list.html', context)


def check_duplicate_lead(request):
    """Check for duplicate leads - AJAX endpoint"""
    name = request.GET.get('name', '')
    email = request.GET.get('email', '')
    phone = request.GET.get('phone', '')
    
    duplicate = Lead.objects.filter(
        Q(name__iexact=name) | Q(email__iexact=email) | Q(phone=phone)
    ).first()
    
    if duplicate:
        return JsonResponse({
            'duplicate': True,
            'message': f'Similar lead found: {duplicate.name} ({duplicate.lead_id})'
        })
    return JsonResponse({'duplicate': False})

# ========= QUOTE CREATION / MANAGEMENT =========


@login_required
@group_required('Account Manager')
@transaction.atomic
def create_quote(request):
    """Create a single quote for a client or lead"""
    if request.method == 'POST':
        try:
            quote_type = request.POST.get('quote_type')
            client_id = request.POST.get('client_id')
            lead_id = request.POST.get('lead_id')

            client = None
            lead = None

            # Determine entity type
            if quote_type == 'client' and client_id:
                client = get_object_or_404(Client, id=client_id)
            elif quote_type == 'lead' and lead_id:
                lead = get_object_or_404(Lead, id=lead_id)
            else:
                messages.error(request, "Please select a valid client or lead.")
                return redirect('create_quote')

            # Extract form data
            product_name = request.POST.get('product_name', '').strip()
            quantity = int(request.POST.get('quantity', 1))
            
            # Check if this is a modal submission (no unit_price provided)
            is_modal_submission = not request.POST.get('unit_price', '').strip()
            
            if is_modal_submission:
                # For modal submissions, get price from Product model
                product_sku = request.POST.get('product_sku', '').strip()
                if product_sku:
                    try:
                        product = Product.objects.get(sku=product_sku, is_active=True)
                        unit_price = product.base_price
                    except Product.DoesNotExist:
                        messages.error(request, f"Product with SKU {product_sku} not found.")
                        return redirect('create_quote')
                else:
                    # Fallback: try to find product by name
                    try:
                        product = Product.objects.filter(name=product_name, is_active=True).first()
                        unit_price = product.base_price if product else Decimal('0')
                    except:
                        unit_price = Decimal('0')
            else:
                # Full form submission
                unit_price_raw = request.POST.get('unit_price', '').strip()
                unit_price = Decimal(unit_price_raw) if unit_price_raw else Decimal('0')
            
            include_vat = request.POST.get('include_vat') == 'on'
            payment_terms = request.POST.get('payment_terms', 'Prepaid')
            status = request.POST.get('status', 'Draft')
            notes = request.POST.get('notes', '')
            terms = request.POST.get('terms', '')
            valid_until_str = request.POST.get('valid_until')
            quote_date_str = request.POST.get('quote_date')

            if not product_name:
                error_msg = "Product name is required."
                if is_modal_submission:
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('create_quote')

            if quantity <= 0:
                error_msg = "Quantity must be greater than zero."
                if is_modal_submission:
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('create_quote')

            # Set dates
            quote_date = timezone.now().date()
            valid_until = quote_date + timedelta(days=30)
            if quote_date_str:
                quote_date = timezone.datetime.fromisoformat(quote_date_str).date()
            if valid_until_str:
                valid_until = timezone.datetime.fromisoformat(valid_until_str).date()

            # Create quote
            quote = Quote.objects.create(
                client=client,
                lead=lead,
                product_name=product_name,
                quantity=quantity,
                unit_price=unit_price,
                payment_terms=payment_terms,
                status=status,
                include_vat=include_vat,
                quote_date=quote_date,
                valid_until=valid_until,
                notes=notes,
                terms=terms,
                created_by=request.user
            )

            # Create activity log
            if client:
                ActivityLog.objects.create(
                    client=client,
                    activity_type='Quote',
                    title=f"Quote {quote.quote_id} Created",
                    description=f"Quote for {product_name} (x{quantity})",
                    related_quote=quote,
                    created_by=request.user
                )

            if is_modal_submission:
                return JsonResponse({
                    'success': True, 
                    'message': f'Quote {quote.quote_id} created successfully!',
                    'quote_id': quote.quote_id
                })
            else:
                messages.success(request, f"Quote {quote.quote_id} created successfully!")
                if client:
                    return redirect('client_profile', pk=client.pk)
                elif lead:
                    return redirect('lead_intake')
                return redirect('dashboard')

        except Exception as e:
            messages.error(request, f"Error creating quote: {str(e)}")
            import traceback; print(traceback.format_exc())
            return redirect('create_quote')

    # GET — Render form
    clients = Client.objects.filter(status='Active').order_by('name')
    leads = Lead.objects.exclude(status__in=['Converted', 'Lost']).order_by('-created_at')
    products = Product.objects.filter(is_active=True).order_by('name')
    today = timezone.now().date()
    default_valid_until = today + timedelta(days=30)

    context = {
        'clients': clients,
        'leads': leads,
        'products': products,
        'today': today.isoformat(),
        'default_valid_until': default_valid_until.isoformat(),
    }
    return render(request, 'create_quote.html', context)



def client_profile(request, pk):
    """Unified Client Profile View — includes jobs, quotes, activities, and financials"""
    client = get_object_or_404(Client, pk=pk)

    # ================= JOBS =================
    jobs = client.jobs.all().order_by('-created_at')

    # ================= QUOTES =================
    all_quotes = client.quotes.all().order_by('-created_at')

    # Group quotes by quote_id (some quotes may have multiple line items)
    quotes_dict = {}
    for quote in all_quotes:
        if quote.quote_id not in quotes_dict:
            quotes_dict[quote.quote_id] = {
                'quote': quote,
                'items': [],
                'total_amount': Decimal('0'),
                'subtotal': Decimal('0')
            }
        quotes_dict[quote.quote_id]['items'].append(quote)
        quotes_dict[quote.quote_id]['total_amount'] += quote.total_amount
        quotes_dict[quote.quote_id]['subtotal'] += (quote.unit_price * quote.quantity)

    quotes_list = list(quotes_dict.values())

    # Quote statistics by status
    quote_stats = {
        'draft': {'count': 0, 'value': Decimal('0')},
        'quoted': {'count': 0, 'value': Decimal('0')},
        'client_review': {'count': 0, 'value': Decimal('0')},
        'approved': {'count': 0, 'value': Decimal('0')},
        'lost': {'count': 0, 'value': Decimal('0')},
    }

    for group in quotes_list:
        status = group['quote'].status.lower().replace(' ', '_')
        if status in quote_stats:
            quote_stats[status]['count'] += 1
            quote_stats[status]['value'] += group['total_amount']

    total_quotes = len(quotes_list)
    approved_value = quote_stats['approved']['value']
    conversion_rate = round((quote_stats['approved']['count'] / total_quotes * 100), 1) if total_quotes > 0 else 0
    avg_margin = 0  # placeholder, not used in simplified pricing

    # ================= ACTIVITIES =================
    activities = client.activities.all().order_by('-created_at')[:20]
    recent_activities = activities[:5]

    production_updates = ProductionUpdate.objects.filter(
        Q(quote__client=client) | Q(job__client=client)
    ).select_related('quote', 'job', 'created_by').order_by('-created_at')[:10]

    # ================= FINANCIAL METRICS =================
    outstanding_balance = quote_stats['quoted']['value'] + quote_stats['client_review']['value']
    lifetime_value = approved_value
    payment_performance = 95  # mock; replace with real payment logic if available

    credit_limit = client.credit_limit or Decimal('500000')
    credit_used = outstanding_balance
    available_credit = credit_limit - credit_used if credit_limit > credit_used else Decimal('0')
    credit_utilization = round((credit_used / credit_limit * 100), 1) if credit_limit > 0 else 0

    # ================= JOB STATISTICS =================
    job_stats = {
        'total': jobs.count(),
        'pending': jobs.filter(status='pending').count(),
        'in_progress': jobs.filter(status='in_progress').count(),
        'completed': jobs.filter(status='completed').count(),
        'on_hold': jobs.filter(status='on_hold').count(),
    }

    # ================= RECENT QUOTES FOR OVERVIEW =================
    recent_quotes = quotes_list[:3]  # Get 3 most recent quotes

    # ================= CONTEXT =================
    context = {
        'client': client,
        'jobs': jobs,
        'quotes': quotes_list,
        'quote_stats': quote_stats,
        'total_quotes': total_quotes,
        'total_revenue': approved_value,
        'conversion_rate': conversion_rate,
        'avg_margin': avg_margin,

        # Activity Log
        'activities': activities,
        'recent_activities': recent_activities,

        # Financial Data
        'outstanding_balance': outstanding_balance,
        'lifetime_value': lifetime_value,
        'payment_performance': payment_performance,
        'credit_limit': credit_limit,
        'credit_used': credit_used,
        'available_credit': available_credit,
        'credit_utilization': credit_utilization,

        # Job Statistics
        'job_stats': job_stats,
        'production_updates': production_updates,
        'recent_quotes': recent_quotes,
    }

    return render(request, 'client_profile.html', context)

def update_quote_status(request):
    """Handle quote approval, rejection, and discount requests"""
    if request.method == 'POST':
        quote_id = request.POST.get('quote_id')
        action = request.POST.get('action')
        
        try:
            # Get the first quote with this quote_id (they're grouped)
            quote = Quote.objects.filter(quote_id=quote_id).first()
            if not quote:
                return JsonResponse({'success': False, 'error': 'Quote not found'})
            
            if action == 'approve':
                quote.status = 'Approved'
                quote.save()
                
                # Create job automatically
                job = Job.objects.create(
                    client=quote.client,
                    quote=quote,
                    job_name=f"Job for {quote.product_name}",
                    job_type='printing',  # You can map this from product type
                    product=quote.product_name,
                    quantity=quote.quantity,
                    person_in_charge='Production Team',  # Default assignment
                    status='pending',
                    expected_completion=quote.valid_until,
                    created_by=request.user
                )
                
                # Create activity log
                ActivityLog.objects.create(
                    client=quote.client,
                    activity_type='Quote',
                    title=f"Quote {quote.quote_id} Approved - Job {job.job_number} Created",
                    description=f"Quote approved and job created for production",
                    related_quote=quote,
                    created_by=request.user
                )
                
                return JsonResponse({'success': True, 'message': f'Quote {quote.quote_id} approved successfully!'})
                
            elif action == 'reject':
                reject_reason = request.POST.get('reject_reason', '')
                quote.status = 'Lost'
                quote.loss_reason = reject_reason or 'Rejected by account manager'
                quote.save()
                
                # Create activity log
                ActivityLog.objects.create(
                    client=quote.client,
                    activity_type='Quote',
                    title=f"Quote {quote.quote_id} Rejected",
                    description=f"Quote rejected: {reject_reason}",
                    related_quote=quote,
                    created_by=request.user
                )
                
                return JsonResponse({'success': True, 'message': f'Quote {quote.quote_id} rejected.'})
                
            elif action == 'discount':
                discount_notes = request.POST.get('discount_notes', '')
                # Create a notification or activity for discount request
                ActivityLog.objects.create(
                    client=quote.client,
                    activity_type='Quote',
                    title=f"Discount Requested - Quote {quote.quote_id}",
                    description=f"Discount request: {discount_notes}",
                    related_quote=quote,
                    created_by=request.user
                )
                
                return JsonResponse({'success': True, 'message': 'Discount request submitted to production team.'})
                
            elif action == 'status_update':
                new_status = request.POST.get('new_status')
                loss_reason = request.POST.get('loss_reason', '')
                
                quote.status = new_status
                if new_status == 'Lost':
                    quote.loss_reason = loss_reason
                quote.save()
                
                return JsonResponse({'success': True, 'message': f'Quote status updated to {new_status}.'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})



def quote_detail(request, quote_id):
    """View detailed quote with all items"""
    # Get all quotes with this quote_id
    quotes = Quote.objects.filter(quote_id=quote_id).order_by('id')
    
    if not quotes.exists():
        messages.error(request, 'Quote not found')
        return redirect('dashboard')
    
    first_quote = quotes.first()
    
    # Calculate totals
    subtotal = sum(q.unit_price * q.quantity for q in quotes)
    vat_amount = subtotal * Decimal('0.16') if first_quote.include_vat else Decimal('0')
    total_amount = subtotal + vat_amount
    
    context = {
        'quote_id': quote_id,
        'quotes': quotes,
        'first_quote': first_quote,
        'client': first_quote.client,
        'lead': first_quote.lead,
        'subtotal': subtotal,
        'vat_amount': vat_amount,
        'total_amount': total_amount,
        'production_updates': first_quote.production_updates.select_related('created_by').order_by('-created_at'),
    }
    
    return render(request, 'quote_detail.html', context)



def delete_quote(request, quote_id):
    """Delete a quote and all its items"""
    if request.method == 'POST':
        # Delete all quotes with this quote_id
        quotes = Quote.objects.filter(quote_id=quote_id)
        client = quotes.first().client if quotes.exists() else None
        
        quotes.delete()
        
        messages.success(request, f'Quote {quote_id} deleted successfully')
        
        if client:
            return redirect('client_profile', pk=client.pk)
        return redirect('dashboard')
    
    return redirect('dashboard')



def quotes_list(request):
    """List all quotes with filters"""
    
    all_quotes = Quote.objects.all().order_by('-created_at')
    
   
    quotes_dict = {}
    for quote in all_quotes:
        if quote.quote_id not in quotes_dict:
            quotes_dict[quote.quote_id] = {
                'quote': quote,
                'items_count': 0,
                'total_amount': Decimal('0')
            }
        quotes_dict[quote.quote_id]['items_count'] += 1
        quotes_dict[quote.quote_id]['total_amount'] += quote.total_amount
    
    quotes_list = list(quotes_dict.values())
    
    
    status_filter = request.GET.get('status')
    if status_filter:
        quotes_list = [q for q in quotes_list if q['quote'].status == status_filter]
    
    context = {
        'quotes': quotes_list,
        'status_filter': status_filter,
    }
    
    return render(request, 'quotes_list.html', context)

def get_client_details(request, client_id):
    """API endpoint to get client details for quote form"""
    try:
        client = get_object_or_404(Client, id=client_id)
        data = {
            'success': True,
            'name': client.company if client.company else client.name,
            'email': client.email,
            'phone': client.phone,
            'address': client.address,
            'default_markup': float(client.default_markup),
            'payment_terms': client.payment_terms,
            'client_type': client.client_type,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def get_lead_details(request, lead_id):
    """API endpoint to get lead details for quote form"""
    try:
        lead = get_object_or_404(Lead, id=lead_id)
        data = {
            'success': True,
            'name': lead.name,
            'email': lead.email,
            'phone': lead.phone,
            'default_markup': 35,  # Default markup for leads
            'payment_terms': 'Prepaid',
            'source': lead.source if hasattr(lead, 'source') else '',
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def save_quote_draft(request):
    """Save quote as draft via AJAX"""
    if request.method == 'POST':
        try:
            # Get JSON data
            data = json.loads(request.body)
            
            quote_type = data.get('quote_type')
            client_id = data.get('client_id')
            lead_id = data.get('lead_id')
            
            client = None
            lead = None
            
            if quote_type == 'client' and client_id:
                client = get_object_or_404(Client, id=client_id)
            elif quote_type == 'lead' and lead_id:
                lead = get_object_or_404(Lead, id=lead_id)
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Please select a client or lead'
                }, status=400)
            
            items = data.get('items', [])
            
            if not items:
                return JsonResponse({
                    'success': False,
                    'error': 'Please add at least one item'
                }, status=400)
            
            # Create draft quotes
            created_quotes = []
            for item in items:
                quote = Quote.objects.create(
                    client=client,
                    lead=lead,
                    product_name=item['description'],
                    quantity=item['quantity'],
                    cost_price=Decimal(str(item['cost'])),
                    markup_percentage=Decimal(str(item['markup'])),
                    selling_price=Decimal(str(item['price'])),
                    status='Draft',
                    notes=data.get('notes', ''),
                    created_by=request.user
                )
                created_quotes.append(quote)
            
            return JsonResponse({
                'success': True,
                'message': 'Draft saved successfully',
                'quote_id': created_quotes[0].quote_id if created_quotes else None
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    }, status=400)

@login_required
@group_required('Production Team')
@transaction.atomic
def create_job(request):
    """Create a new production job with detailed line items"""
    clients = Client.objects.filter(status='Active').order_by('name')

    def parse_date(value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            try:
                return datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                return None

    if request.method == 'POST':
            client_id = request.POST.get('client_id')
            if not client_id:
                messages.error(request, 'Please select a client.')
                return redirect('create_job')
            
            client = get_object_or_404(Client, id=client_id)
            
            job_name = request.POST.get('job_name', '').strip()
            job_type = request.POST.get('job_type', 'other')
            priority = request.POST.get('priority', 'normal')
            person_in_charge = request.POST.get('person_in_charge', '').strip()
            status = request.POST.get('status', 'pending').lower()
            notes = request.POST.get('notes', '')
            
            if status not in dict(Job.STATUS_CHOICES):
                status = 'pending'

            if not job_name or not person_in_charge:
                messages.error(request, 'Job name and person in charge are required.')
                return redirect('create_job')
            
            products_data = []
            for idx in range(1, 6):
                product_name = request.POST.get(f'product_name_{idx}', '').strip()
                if not product_name:
                    continue
                quantity_raw = request.POST.get(f'quantity_{idx}', '1')
                try:
                    quantity_val = int(quantity_raw)
                except ValueError:
                    quantity_val = 1
                if quantity_val <= 0:
                    quantity_val = 1
                unit = request.POST.get(f'unit_{idx}', 'pcs')
                specs = request.POST.get(f'specifications_{idx}', '')
                products_data.append({
                    'name': product_name,
                    'quantity': quantity_val,
                    'unit': unit,
                    'specs': specs,
                })
            
            if not products_data:
                messages.error(request, 'Please add at least one product line item.')
                return redirect('create_job')
            
            start_date = parse_date(request.POST.get('start_date')) or timezone.now().date()
            expected_completion = parse_date(request.POST.get('expected_completion')) or start_date
            delivery_date = parse_date(request.POST.get('delivery_date'))
            delivery_method = request.POST.get('delivery_method', 'pickup')

            main_product = products_data[0]

            job = Job.objects.create(
                client=client,
                job_name=job_name,
                job_type=job_type,
                priority=priority,
                product=main_product['name'],
                quantity=main_product['quantity'],
                person_in_charge=person_in_charge,
                status=status,
                start_date=start_date,
                expected_completion=expected_completion,
                delivery_date=delivery_date,
                delivery_method=delivery_method,
                notes=notes,
                created_by=request.user
            )

            for product_data in products_data:
                JobProduct.objects.create(
                    job=job,
                    product_name=product_data['name'],
                    quantity=product_data['quantity'],
                    unit=product_data['unit'],
                    specifications=product_data['specs'],
                )

                ActivityLog.objects.create(
                    client=client,
                    activity_type='Order',
                    title=f"Job Created - {job.job_number}",
                    description=f"Job {job.job_name} created with priority {job.priority} and status {job.status}.",
                    created_by=request.user
                )
                
            ProductionUpdate.objects.create(
                update_type='job',
                job=job,
                status='pending',
                progress=0,
                notes='Job created and scheduled.',
                created_by=request.user
            )
                
            messages.success(request, f"Job '{job.job_name}' created successfully for {client.name}.")
            return redirect('job_detail', pk=job.pk)
    
    context = {
        'clients': clients,
        'current_year': timezone.now().year,
        'current_view': 'production_jobs',
    }
    return render(request, 'create_job.html', context)


@login_required
def job_detail(request, pk):
    """View and update an existing job"""
    job = get_object_or_404(Job.objects.select_related('client'), pk=pk)
    clients = Client.objects.filter(status='Active').order_by('name')
    job_updates = job.production_updates.select_related('created_by').order_by('-created_at')
    can_manage = request.user.groups.filter(name='Production Team').exists()

    update_form = ProductionUpdateForm(initial={
        'status': job.status if job.status in dict(Quote.PRODUCTION_STATUS_CHOICES) else 'in_progress',
        'progress': 100 if job.status == 'completed' else 0,
    })

    if request.method == 'POST':
        action = request.POST.get('action', 'update_job')

        if action == 'record_update':
            if not can_manage:
                messages.error(request, 'Only production team members can record production updates.')
                return redirect('job_detail', pk=job.pk)

            update_form = ProductionUpdateForm(request.POST)
            if update_form.is_valid():
                update = update_form.save(commit=False)
                update.update_type = 'job'
                update.job = job
                update.created_by = request.user
                update.save()

                if update.status in dict(Job.STATUS_CHOICES):
                    job.status = update.status
                    job.save(update_fields=['status', 'updated_at'])

                messages.success(request, 'Production update recorded successfully.')
            return redirect('job_detail', pk=job.pk)
        else:
            job.product = request.POST.get('product', job.product)
            quantity_raw = request.POST.get('quantity', job.quantity)
            try:
                job.quantity = int(quantity_raw)
            except (TypeError, ValueError):
                pass

            job.person_in_charge = request.POST.get('person_in_charge', job.person_in_charge)
            job.notes = request.POST.get('notes', job.notes)

            status_value = request.POST.get('status', job.status).lower()
            if status_value in dict(Job.STATUS_CHOICES):
                job.status = status_value

            job.save()
            messages.success(request, 'Job updated successfully.')
            return redirect('job_detail', pk=job.pk)

    context = {
        'clients': clients,
        'job': job,
        'is_update': True,
        'job_updates': job_updates,
        'update_form': update_form,
        'can_manage': can_manage,
        'current_view': 'production_jobs',
    }
    return render(request, 'create_job.html', context)


@group_required('Account Manager')
def base_view(request):
    """Simple base view used by sidebar link"""
    return render(request, 'base2.html', {})


@login_required
@group_required('Production Team')
def quote_review_queue(request):
    """Quote review / queue for Production Team"""
    status_filter = request.GET.get('status', 'pending')
    search = request.GET.get('search', '').strip()

    quotes_qs = Quote.objects.select_related('client', 'lead', 'created_by').order_by('-created_at')

    if status_filter == 'pending':
        quotes_qs = quotes_qs.filter(production_status__in=['pending', 'in_progress'])
    elif status_filter == 'costed':
        quotes_qs = quotes_qs.filter(production_status='costed')
    elif status_filter == 'sent':
        quotes_qs = quotes_qs.filter(status__in=['Quoted', 'Client Review'])
    elif status_filter == 'approved':
        quotes_qs = quotes_qs.filter(status='Approved')

    if search:
        quotes_qs = quotes_qs.filter(
            Q(quote_id__icontains=search) |
            Q(product_name__icontains=search) |
            Q(client__name__icontains=search) |
            Q(lead__name__icontains=search)
        )

    quotes = list(quotes_qs)
    cost_forms = {quote.quote_id: QuoteCostingForm(instance=quote) for quote in quotes}

    context = {
        'current_view': 'production_quotes',
        'quotes': quotes,
        'status_filter': status_filter,
        'search': search,
        'cost_forms': cost_forms,
        'pending_count': Quote.objects.filter(production_status__in=['pending', 'in_progress']).count(),
        'costed_count': Quote.objects.filter(production_status='costed').count(),
        'sent_count': Quote.objects.filter(status__in=['Quoted', 'Client Review']).count(),
        'approved_count': Quote.objects.filter(status='Approved').count(),
    }
    return render(request, 'quote_review.html', context)


@login_required
@group_required('Production Team')
@transaction.atomic
def update_quote_costing(request, quote_id):
    """Update costing details for a quote"""
    quote = get_object_or_404(Quote, quote_id=quote_id)
    related_quotes = Quote.objects.filter(quote_id=quote.quote_id).order_by('created_at')

    if request.method == 'POST':
        form = QuoteCostingForm(request.POST, instance=quote)
        if form.is_valid():
            if not form.has_changed():
                messages.info(request, 'No changes detected in the costing form.')
                return redirect('production_quote_review')

            quote_obj = form.save(commit=False)
            if quote_obj.production_status == 'pending':
                quote_obj.production_status = 'costed'
            if quote_obj.status == 'Draft' and quote_obj.production_status in ['costed', 'sent_to_client']:
                quote_obj.status = 'Quoted'
            quote_obj.costed_by = request.user
            quote_obj.save()

            progress = 50
            if quote_obj.production_status in ['sent_to_client', 'in_production', 'completed']:
                progress = 100

            ProductionUpdate.objects.create(
                update_type='quote',
                quote=quote_obj,
                status=quote_obj.production_status,
                progress=progress,
                notes=form.cleaned_data.get('production_notes', ''),
                created_by=request.user
            )

            messages.success(request, f'Quote {quote_obj.quote_id} updated successfully.')
            return redirect('production_quote_review')
    else:
        form = QuoteCostingForm(instance=quote)

    context = {
        'quote': quote,
        'related_quotes': related_quotes,
        'form': form,
        'current_view': 'production_quotes',
    }
    return render(request, 'approve_quote.html', context)


@login_required
@group_required('Production Team')
def production_catalog(request):
    """Production Team product/catalog view with create & update actions"""
    search = request.GET.get('search', '').strip()
    product_type = request.GET.get('product_type', 'all')
    availability = request.GET.get('availability', 'all')

    products = Product.objects.all()

    if search:
        products = products.filter(Q(name__icontains=search) | Q(sku__icontains=search))
    if product_type != 'all':
        products = products.filter(product_type=product_type)
    if availability != 'all':
        products = products.filter(availability=availability)

    products = products.order_by('name')

    editing_product = None
    form = ProductForm()

    if request.method == 'POST':
        action = request.POST.get('action', 'save')
        product_id = request.POST.get('product_id')

        if action == 'toggle' and product_id:
            product = get_object_or_404(Product, pk=product_id)
            product.is_active = not product.is_active
            product.updated_by = request.user
            product.save(update_fields=['is_active', 'updated_at', 'updated_by'])
            messages.success(request, f'{product.name} status updated.')
            return redirect('production_catalog')

        if product_id:
            editing_product = get_object_or_404(Product, pk=product_id)

        form = ProductForm(request.POST, instance=editing_product)
        if form.is_valid():
            product = form.save(commit=False)
            if editing_product is None:
                product.created_by = request.user
            product.updated_by = request.user
            product.save()
            messages.success(request, f'Product {product.name} saved successfully.')
            return redirect('production_catalog')
    else:
        product_id = request.GET.get('product_id')
        if product_id:
            editing_product = get_object_or_404(Product, pk=product_id)
            form = ProductForm(instance=editing_product)

    context = {
        'current_view': 'production_catalog',
        'products': products,
        'form': form,
        'editing_product': editing_product,
        'search': search,
        'product_type': product_type,
        'availability': availability,
    }
    return render(request, 'production_catalog.html', context)


@login_required
@group_required('Production Team')
def production2_dashboard(request):
    """Production Team dashboard"""
    total_jobs = Job.objects.count()
    pending_jobs = Job.objects.filter(status='pending').count()
    in_progress_jobs = Job.objects.filter(status='in_progress').count()
    completed_jobs = Job.objects.filter(status='completed').count()

    quotes_pending = Quote.objects.filter(production_status__in=['pending', 'in_progress']).count()
    quotes_costed = Quote.objects.filter(production_status='costed').count()
    quotes_sent = Quote.objects.filter(status__in=['Quoted', 'Client Review']).count()

    recent_updates = ProductionUpdate.objects.select_related('quote', 'job', 'created_by').order_by('-created_at')[:8]

    context = {
        'current_view': 'production_dashboard',
        'total_jobs': total_jobs,
        'pending_jobs': pending_jobs,
        'in_progress_jobs': in_progress_jobs,
        'completed_jobs': completed_jobs,
        'quotes_pending': quotes_pending,
        'quotes_costed': quotes_costed,
        'quotes_sent': quotes_sent,
        'active_products': Product.objects.filter(is_active=True).count(),
        'recent_updates': recent_updates,
    }
    return render(request, 'production2_dashboard.html', context)


@login_required
@group_required('Production Team')
def production_analytics(request):
    """Production-side analytics"""
    quotes_by_status = Quote.objects.values('production_status').annotate(count=Count('id'))
    jobs_by_status = Job.objects.values('status').annotate(count=Count('id'))
    avg_quote_value = Quote.objects.aggregate(avg=Avg('total_amount'))['avg'] or 0
    recent_costings = Quote.objects.filter(costed_by__isnull=False).select_related('client', 'lead').order_by('-updated_at')[:10]

    context = {
        'current_view': 'production_analytics',
        'quotes_by_status': quotes_by_status,
        'jobs_by_status': jobs_by_status,
        'avg_quote_value': avg_quote_value,
        'recent_costings': recent_costings,
    }
    return render(request, 'production_analytics.html', context)


@login_required
def notifications(request):
    """List notifications for the logged-in user"""
    user_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')

    if request.method == 'POST':
        notification_ids = request.POST.getlist('mark_read')
        if notification_ids:
            Notification.objects.filter(recipient=request.user, id__in=notification_ids).update(is_read=True)
            messages.success(request, 'Selected notifications marked as read.')
        else:
            Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
            messages.success(request, 'All notifications marked as read.')
        return redirect('notifications')

    context = {
        'current_view': 'notifications',
        'notifications': user_notifications,
    }
    return render(request, 'notifications.html', context)


def permission_denied_view(request, *args, **kwargs):
    messages.warning(request, "You don't have access to that section.")
    fallback = 'dashboard'
    if request.user.groups.filter(name='Production Team').exists():
        fallback = 'production_dashboard2'
    return redirect(reverse(fallback))


def login_redirect(request):
    """
    Custom login redirect view that sends users to appropriate dashboard based on their group
    """
    if request.user.is_authenticated:
        if request.user.groups.filter(name='Finance').exists():
            return redirect('finance_dashboard')
        if request.user.groups.filter(name='Production Team').exists():
            return redirect('production_dashboard2')
        else:
            # Default to main dashboard for Account Managers and other users
            return redirect('dashboard')
    else:
        # Fallback for unauthenticated users
        return redirect('login')

# Add before the login_redirect function (around line 1859):
@login_required
@group_required('Production Team')
def production_jobs(request):
    """Production Team jobs management - list view"""
    jobs = Job.objects.all().order_by('-created_at')
    
    # Filter options
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        jobs = jobs.filter(status=status_filter)
    
    context = {
        'current_view': 'production_jobs',
        'jobs': jobs,
        'status_filter': status_filter,
    }
    return render(request, 'production_jobs.html', context)


# Add imports after existing imports:
from django_ledger.models import EntityModel

# Add finance decorator after group_required:
def finance_required(view_func):
    """Require Finance group membership"""
    return group_required('Finance')(view_func)

# Add finance dashboard view before login_redirect:
@finance_required
def finance_dashboard(request):
    """Finance dashboard with Django Ledger integration"""
    # Get or create entity for each client
    entities = []  # list of {'entity': EntityModel, 'client_id': int}
    # Resolve available EntityModel field names safely
    entity_field_names = {f.name for f in EntityModel._meta.get_fields()}
    for client in Client.objects.all():
        entity_name = f"{client.name} ({client.client_id})"
        entity = EntityModel.objects.filter(name=entity_name).first()
        if not entity:
            defaults = {}
            if 'admin' in entity_field_names:
                defaults['admin'] = request.user
            if 'address_1' in entity_field_names:
                defaults['address_1'] = getattr(client, 'address', '') or ''
            if 'phone' in entity_field_names:
                defaults['phone'] = getattr(client, 'phone', '') or ''
            if 'email' in entity_field_names:
                defaults['email'] = getattr(client, 'email', '') or ''
            # Optional helpful fields if present in installed version
            if 'country' in entity_field_names:
                defaults['country'] = 'KE'
            if 'currency' in entity_field_names:
                defaults['currency'] = 'KES'

            # Use treebeard-friendly creation to avoid depth NULL (use add_root when available)
            try:
                if hasattr(EntityModel, 'add_root'):
                    entity = EntityModel.add_root(name=entity_name, **defaults)
                else:
                    entity = EntityModel.objects.create(name=entity_name, **defaults)
            except Exception:
                # Fallback minimal create on any schema mismatch
                minimal_kwargs = {'name': entity_name}
                if 'admin' in entity_field_names:
                    minimal_kwargs['admin'] = request.user
                entity = EntityModel.objects.create(**minimal_kwargs)
        entities.append({'entity': entity, 'client_id': client.id})
    
    context = {
        'current_view': 'finance_dashboard',
        'entities': entities,
        'total_entities': EntityModel.objects.count(),
    }
    return render(request, 'finance_dashboard.html', context)

# Add client-entity mapping view:
@finance_required
def finance_client_entity(request, client_id):
    """Map client to Django Ledger entity"""
    client = get_object_or_404(Client, id=client_id)
    
    entity_field_names = {f.name for f in EntityModel._meta.get_fields()}
    entity_name = f"{client.name} ({client.client_id})"
    entity = EntityModel.objects.filter(name=entity_name).first()
    if not entity:
        defaults = {}
        if 'admin' in entity_field_names:
            defaults['admin'] = request.user
        if 'address_1' in entity_field_names:
            defaults['address_1'] = getattr(client, 'address', '') or ''
        if 'phone' in entity_field_names:
            defaults['phone'] = getattr(client, 'phone', '') or ''
        if 'email' in entity_field_names:
            defaults['email'] = getattr(client, 'email', '') or ''
        if 'country' in entity_field_names:
            defaults['country'] = 'KE'
        if 'currency' in entity_field_names:
            defaults['currency'] = 'KES'
        try:
            if hasattr(EntityModel, 'add_root'):
                entity = EntityModel.add_root(name=entity_name, **defaults)
            else:
                entity = EntityModel.objects.create(name=entity_name, **defaults)
        except Exception:
            minimal_kwargs = {'name': entity_name}
            if 'admin' in entity_field_names:
                minimal_kwargs['admin'] = request.user
            entity = EntityModel.objects.create(**minimal_kwargs)
    
    # Render within our theme using an iframe wrapper
    return render(request, 'finance_entity.html', {'entity': entity, 'current_view': 'finance_dashboard'})

