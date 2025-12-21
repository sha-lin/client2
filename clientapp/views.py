import decimal
import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg, Count, Q, Sum
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.core.exceptions import ValidationError
from functools import wraps
from django.contrib.auth.models import User, Group
from .models import BrandAsset
from django.core.paginator import Paginator



from .forms import (
    LeadForm,
    ClientForm,
    QuoteCostingForm,
    ProductionUpdateForm,
    VendorForm,
)

from .models import (
    Lead,
    Client,
    ClientContact,
    ComplianceDocument,
    Product,
    Quote,
    QuoteLineItem,
    ActivityLog,
    ProductionUpdate,
    Notification,
    Job,
    JobProduct,
    ProductTag,
    LPO,
    LPOLineItem,
    SystemAlert,
    ProcessVariableRange,
    Process,
    Vendor,
)

# Import comprehensive CRUD API endpoints
from .admin_api import (
    api_admin_leads,
    api_admin_lead_detail,
    api_admin_products,
    api_admin_product_detail,
    api_admin_vendors,
    api_admin_vendor_detail,
    api_admin_lpos,
    api_admin_payments,
    api_admin_qc_inspections,
    api_admin_deliveries,
    api_admin_create_user,
    api_admin_get_user,
    api_admin_update_user,
    api_admin_delete_user,
    api_admin_create_client,
    api_admin_get_client,
    api_admin_update_client,
    api_admin_delete_client,
    api_admin_create_lead,
    api_admin_get_lead,
    api_admin_update_lead,
    api_admin_delete_lead,
    api_admin_create_quote,
    api_admin_get_quote,
    api_admin_update_quote,
    api_admin_delete_quote,
    api_admin_create_product,
    api_admin_get_product,
    api_admin_update_product,
    api_admin_delete_product,
)

# Import admin dashboard views
from .admin_views import (
    admin_dashboard,
    clients_list,
    leads_list,
    quotes_list,
    products_list,
    jobs_list,
    vendors_list,
    processes_list,
    qc_list,
    deliveries_list,
    lpos_list,
    payments_list,
    analytics_view,
    users_list,
    get_object_detail,
    create_object,
    update_object,
    delete_object,
)

def notification_count_processor(request):
    """Add unread notification count to all templates"""
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return {'unread_notifications_count': unread_count}
    return {'unread_notifications_count': 0}

from clientapp.quote_approval_services import QuoteApprovalService
def send_quote_email(quote_id, request):
    """
    Send quote to client via email with approval link
    """
    from clientapp.quote_approval_services import QuoteApprovalService
    
    try:
        # Get quote
        quotes = Quote.objects.filter(quote_id=quote_id)
        if not quotes.exists():
            return {'success': False, 'message': 'Quote not found'}
        
        first_quote = quotes.first()
        
        # ✅ Use the service to send the email (which generates the token properly)
        result = QuoteApprovalService.send_quote_via_email(first_quote, request)
        
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'success': False, 'message': str(e)}

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
            if user.groups.filter(name='Production Team').exists():
                return redirect(reverse('production2_dashboard'))
            elif user.groups.filter(name='Account Manager').exists():
                return redirect(reverse('dashboard'))
            else:
                # User has no recognized group → send to login
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("Access denied. Please contact administrator.")

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
                fallback_name = 'production2_dashboard'
            elif user.groups.filter(name='Account Manager').exists():
                fallback_name = 'dashboard'

            return redirect(reverse(fallback_name))
        return _wrapped
    return decorator

@login_required
@group_required('Account Manager')
def dashboard(request):
    """Account Manager Dashboard - Matches original template structure"""
    from datetime import timedelta
    from django.db.models import Count, Sum, Q
    from decimal import Decimal
    
    # Date ranges
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    thirty_days_ago = today - timedelta(days=30)
    
    # ========== CORE METRICS (matches your template) ==========
    
        # Total leads (Global)
    total_leads = Lead.objects.all().count()
    
    # Converted leads (Global)
    converted_leads = Lead.objects.filter(status='Converted').count()
    
    # Active clients
    active_clients = Client.objects.filter(account_manager=request.user, status='Active').count()
    
    # B2B and B2C clients
    b2b_clients = Client.objects.filter(account_manager=request.user, client_type='B2B').count()
    b2c_clients = Client.objects.filter(account_manager=request.user, client_type='B2C').count()
    
    # ========== JOB METRICS ==========
    total_jobs = Job.objects.filter(client__account_manager=request.user).count()
    pending_jobs = Job.objects.filter(client__account_manager=request.user, status='pending').count()
    in_progress_jobs = Job.objects.filter(client__account_manager=request.user, status='in_progress').count()
    completed_jobs = Job.objects.filter(client__account_manager=request.user, status='completed').count()
    
    # ========== QUOTE METRICS ==========
    # Total unique quotes
    total_quotes = Quote.objects.filter(created_by=request.user).values('quote_id').distinct().count()
    
    # Draft quotes
    draft_quotes = Quote.objects.filter(created_by=request.user, status='Draft').values('quote_id').distinct().count()
    
    # Pending/Quoted
    pending_quotes = Quote.objects.filter(
        created_by=request.user, 
        status__in=['Quoted', 'Client Review']
    ).values('quote_id').distinct().count()
    
    # Approved quotes
    approved_quotes = Quote.objects.filter(created_by=request.user, status='Approved').values('quote_id').distinct().count()
    
    # Total revenue (from approved quotes)
    total_revenue = Quote.objects.filter(
        created_by=request.user,
        status='Approved'
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    # Conversion rate
    conversion_rate = round((approved_quotes / total_quotes * 100), 1) if total_quotes > 0 else 0
    
    # ========== MY PERSONAL KPIs (This Month) ==========
    my_quotes_this_month = Quote.objects.filter(
        created_by=request.user,
        created_at__gte=this_month_start
    ).values('quote_id').distinct().count()
    
    my_quotes_won = Quote.objects.filter(
        created_by=request.user,
        status='Approved',
        created_at__gte=this_month_start
    ).values('quote_id').distinct().count()
    
    my_clients_this_month = Client.objects.filter(
        account_manager=request.user,
        created_at__gte=this_month_start
    ).count()
    
    my_revenue = Quote.objects.filter(
        created_by=request.user,
        status='Approved',
        created_at__gte=this_month_start
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    my_win_rate = round((my_quotes_won / my_quotes_this_month * 100), 1) if my_quotes_this_month > 0 else 0
    
    # Changes from last period (set to 0 for now, you can calculate later)
    quotes_change = 0
    clients_change = 0
    revenue_change = Decimal('0')
    clients_change_abs = 0
    quotes_change_abs = 0
    revenue_change_abs = 0
    
    # ========== RECENT ITEMS ==========
    recent_quotes = Quote.objects.filter(
        created_by=request.user
    ).select_related('client', 'lead').order_by('-created_at')[:5]
    
    recent_clients = Client.objects.filter(
        account_manager=request.user
    ).order_by('-created_at')[:5]
    
    # ========== UPCOMING ACTIONS ==========
    upcoming_actions = []
    
    # Get quotes that need follow-up
    follow_up_quotes = Quote.objects.filter(
        created_by=request.user,
        status='Quoted',
        created_at__gte=timezone.now() - timedelta(days=7)
    ).select_related('client', 'lead')[:3]
    
    for quote in follow_up_quotes:
        client_name = quote.client.name if quote.client else (quote.lead.name if quote.lead else 'Unknown')
        upcoming_actions.append({
            'type': 'quote',
            'icon_color': 'blue',
            'title': 'Follow Up Quote',
            'description': f'Quote #{quote.quote_id} - {quote.product_name}',
            'client': client_name,
            'due_date': quote.created_at + timedelta(days=3),
            'time': (quote.created_at + timedelta(days=3)).strftime('%I:%M %p'),
        })
    
    # ========== RECENT ACTIVITY ==========
    recent_activity = []
    
    # Recent clients added
    for client in recent_clients[:3]:
        time_diff = timezone.now() - client.created_at
        recent_activity.append({
            'client': client.name,
            'action': 'New Client Onboarded',
            'time': format_time_diff(time_diff),
            'type': 'Client'
        })
    
    # Recent quotes
    for quote in recent_quotes[:3]:
        time_diff = timezone.now() - quote.created_at
        client_name = quote.client.name if quote.client else (quote.lead.name if quote.lead else 'Unknown')
        recent_activity.append({
            'client': client_name,
            'action': f'Quote {quote.quote_id} Created',
            'time': format_time_diff(time_diff),
            'type': 'Quote'
        })
    
    # ========== TOP PRODUCTS ==========
    top_products = Quote.objects.filter(
        created_by=request.user,
        status='Approved'
    ).values('product_name').annotate(
        total=Count('id')
    ).order_by('-total')[:5]
    
    # ========== NOTIFICATIONS ==========
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:5]
    
    unread_notifications_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    context = {
        'current_view': 'dashboard',
        
        # Lead/Client Metrics
        'total_leads': total_leads,
        'converted_leads': converted_leads,
        'active_clients': active_clients,
        'b2b_clients': b2b_clients,
        'b2c_clients': b2c_clients,
        
        # Production Metrics
        'total_jobs': total_jobs,
        'pending_jobs': pending_jobs,
        'in_progress_jobs': in_progress_jobs,
        'completed_jobs': completed_jobs,
        
        # Quote Metrics
        'total_quotes': total_quotes,
        'draft_quotes': draft_quotes,
        'pending_quotes': pending_quotes,
        'approved_quotes': approved_quotes,
        'total_revenue': total_revenue,
        'conversion_rate': conversion_rate,
        
        # Personal KPIs
        'my_new_clients': my_clients_this_month,
        'clients_change': clients_change,
        'clients_change_abs': clients_change_abs,
        'my_win_rate': my_win_rate,
        'my_quotes_sent': my_quotes_this_month,
        'quotes_change': quotes_change,
        'quotes_change_abs': quotes_change_abs,
        'my_revenue': my_revenue,
        'revenue_change': revenue_change,
        'revenue_change_abs': revenue_change_abs,
        
        # Activity & History
        'recent_activity': recent_activity,
        'recent_quotes': recent_quotes,
        'recent_clients': recent_clients,
        'top_products': top_products,
        'upcoming_actions': upcoming_actions,
        
        # Notifications
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
        
        # New Dashboard Sections
        'jobs_nearing_deadline': Job.objects.filter(
            client__account_manager=request.user,
            status__in=['pending', 'in_progress'],
            expected_completion__lte=timezone.now().date() + timedelta(days=5),
            expected_completion__gte=timezone.now().date()
        ).select_related('client').order_by('expected_completion')[:5],
        'active_jobs_count': pending_jobs + in_progress_jobs,
        

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
    products = Product.objects.filter(is_visible=True).order_by('name')

    # Calculate Average Margin
    total_revenue_all = 0
    total_cost_all = 0
    for q_dict in quotes_list:
        # Sum up for all items in this quote group
        for item in q_dict['items']:
            total_revenue_all += item.total_amount
            total_cost_all += (item.production_cost or Decimal('0'))
            
    avg_margin = 0
    if total_revenue_all > 0:
        avg_margin = ((total_revenue_all - total_cost_all) / total_revenue_all) * 100

    context = {
        'current_view': 'quote_management',
        'quotes': quotes_list,
        'quote_stats': quote_stats,
        'status_filter': status_filter,
        'total_value': total_value,
        'approved_value': approved_value,
        'avg_margin': avg_margin,
        'clients': clients,
        'leads': leads,
        'products': products,
    }
    
    return render(request, 'quote_management.html', context)


@login_required
@group_required('Account Manager')
def create_multi_quote(request):
    """
    Create a new quote from the multi-product quotes modal form
    """
    if request.method == 'POST':
        try:
            from decimal import Decimal
            from django.contrib import messages
            
            # Get form data
            quote_type = request.POST.get('quote_type')
            client_id = request.POST.get('client_id')
            lead_id = request.POST.get('lead_id')
            product_id = request.POST.get('product')
            quantity = int(request.POST.get('quantity', 1))
            unit_price = Decimal(request.POST.get('unit_price', '0'))
            notes = request.POST.get('notes', '')
            
            # Validate required fields
            if not product_id:
                messages.error(request, 'Please select a product')
                return redirect('quote_management')
            
            if not (client_id or lead_id):
                messages.error(request, 'Please select a client or lead')
                return redirect('quote_management')
            
            # Get the product
            product = Product.objects.get(id=product_id)
            
            # Create the quote
            quote = Quote.objects.create(
                client_id=client_id if quote_type == 'client' else None,
                lead_id=lead_id if quote_type == 'lead' else None,
                product=product,
                product_name=product.name,
                quantity=quantity,
                unit_price=unit_price,
                notes=notes,
                status='Draft',
                created_by=request.user,
            )
            
            messages.success(request, f'Quote {quote.quote_id} created successfully!')
            return redirect('quote_detail', quote_id=quote.quote_id)
            
        except Product.DoesNotExist:
            messages.error(request, 'Selected product not found')
            return redirect('quote_management')
        except Exception as e:
            messages.error(request, f'Error creating quote: {str(e)}')
            return redirect('quote_management')
    
    return redirect('quote_management')


# ========== STANDALONE VIEWS (NEW SIDEBAR ITEMS) ==========
@login_required
@group_required('Account Manager')
def analytics(request):
    """Analytics page with live charts and metrics"""
    from datetime import timedelta
    from django.db.models import Count, Sum, Avg
    import json
    
    today = timezone.now().date()
    
    # ================= REVENUE TREND (Last 6 months) =================
    revenue_data = []
    labels = []
    
    for i in range(5, -1, -1):
        month_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
        
        revenue = Quote.objects.filter(
            created_by=request.user,
            status='Approved',
            approved_at__gte=month_start,
            approved_at__lte=month_end
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        revenue_data.append(float(revenue))
        labels.append(month_start.strftime('%b %Y'))
    
    # ================= TOP PRODUCTS =================
    top_products = Quote.objects.filter(
        created_by=request.user,
        status='Approved'
    ).values('product_name').annotate(
        total_revenue=Sum('total_amount'),
        quantity_sold=Sum('quantity')
    ).order_by('-total_revenue')[:10]
    
    # Prepare Top Products for Chart
    top_products_list = list(top_products)
    top_product_labels = [p['product_name'] for p in top_products_list]
    top_product_data = [float(p['total_revenue']) for p in top_products_list]
    
    # ================= CONVERSION FUNNEL =================
    total_leads = Lead.objects.filter(created_by=request.user).count()
    qualified_leads = Lead.objects.filter(created_by=request.user, status='Qualified').count()
    converted_leads = Lead.objects.filter(created_by=request.user, status='Converted').count()
    
    total_quotes = Quote.objects.filter(created_by=request.user).values('quote_id').distinct().count()
    approved_quotes = Quote.objects.filter(created_by=request.user, status='Approved').values('quote_id').distinct().count()
    
    # ================= CLIENT TYPE BREAKDOWN =================
    b2b_clients = Client.objects.filter(account_manager=request.user, client_type='B2B').count()
    b2c_clients = Client.objects.filter(account_manager=request.user, client_type='B2C').count()
    
    # ================= AVERAGE DEAL SIZE =================
    avg_deal_size = Quote.objects.filter(
        created_by=request.user,
        status='Approved'
    ).aggregate(avg=Avg('total_amount'))['avg'] or 0
    
    # ================= AVG TURNAROUND TIME =================
    # Time from creation to approval
    approved_quotes_objs = Quote.objects.filter(created_by=request.user, status='Approved')
    total_hours = 0
    count_approved = 0
    for q in approved_quotes_objs:
        if q.approved_at and q.created_at:
             diff = q.approved_at - q.created_at
             total_hours += diff.total_seconds() / 3600
             count_approved += 1
    avg_turnaround = round(total_hours / count_approved, 1) if count_approved > 0 else 0

    context = {
        'current_view': 'analytics',
        
        # Chart data (convert to JSON for JavaScript)
        'revenue_labels': json.dumps(labels),
        'revenue_data': json.dumps(revenue_data),
        'top_product_labels': json.dumps(top_product_labels),
        'top_product_data': json.dumps(top_product_data),
        
        # Funnel data
        'total_leads': total_leads,
        'qualified_leads': qualified_leads,
        'converted_leads': converted_leads,
        'total_quotes': total_quotes,
        'approved_quotes': approved_quotes,
        
        # Client breakdown
        'b2b_clients': b2b_clients,
        'b2c_clients': b2c_clients,
        
        # Metrics
        'avg_deal_size': avg_deal_size,
        'conversion_rate': round((approved_quotes / total_quotes * 100), 1) if total_quotes > 0 else 0,
        'avg_turnaround': avg_turnaround,
    }
    
    return render(request, 'analytics.html', context)


@group_required('Account Manager')
def product_catalog(request):
    """Product catalog view for account managers (read-only) - returns only published products"""

    search = request.GET.get('search', '').strip()
    product_type = request.GET.get('product_type', 'all')
    availability = request.GET.get('availability', 'all')

    # Only show published and visible products
    products = Product.objects.filter(
        status='published',
        is_visible=True
    )

    if search:
        products = products.filter(Q(name__icontains=search) | Q(internal_code__icontains=search))

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



@login_required
@group_required('Account Manager')
def account_manager_jobs_list(request):
    """List of jobs for Account Manager"""
    jobs = Job.objects.filter(
        client__account_manager=request.user
    ).exclude(status='completed').select_related('client').order_by('-created_at')
    
    # Add custom status property for template
    for job in jobs:
        # Check for delivery status
        try:
            if hasattr(job, 'delivery') and job.delivery.status == 'delivered':
                job.delivery_status = 'delivered'
            else:
                job.delivery_status = None
        except:
            job.delivery_status = None
            
        # Check if overdue
        if job.expected_completion and job.expected_completion < timezone.now().date() and job.status not in ['completed']:
            job.is_overdue = True
        else:
            job.is_overdue = False

    context = {
        'jobs': jobs,
        'current_view': 'jobs',
    }
    return render(request, 'account_manager/jobs_list.html', context)


@login_required
@group_required('Account Manager')
def account_manager_job_detail(request, pk):
    """Job detail view for Account Manager"""
    job = get_object_or_404(Job, pk=pk)
    
    # Get production users
    production_group = Group.objects.filter(name='Production Team').first()
    production_users = production_group.user_set.all() if production_group else []
    
    # Calculate metrics
    days_active = (timezone.now().date() - job.start_date).days
    days_remaining = (job.expected_completion - timezone.now().date()).days if job.expected_completion else 0
    
    # Check if overdue
    job.is_overdue = False
    if job.expected_completion and job.expected_completion < timezone.now().date() and job.status != 'completed':
        job.is_overdue = True

    context = {
        'job': job,
        'production_users': production_users,
        'days_active': max(0, days_active),
        'days_remaining': days_remaining,
        'current_view': 'jobs',
    }
    return render(request, 'account_manager/job_detail.html', context)


@login_required
@group_required('Account Manager')
def account_manager_job_update(request, pk):
    """Update job assignment and status"""
    job = get_object_or_404(Job, pk=pk)
    
    if request.method == 'POST':
        person_in_charge = request.POST.get('person_in_charge')
        status = request.POST.get('status')
        
        if person_in_charge:
            job.person_in_charge = person_in_charge
        
        if status:
            job.status = status
            
        job.save()
        messages.success(request, f'Job {job.job_number} updated successfully.')
        
    return redirect('account_manager_job_detail', pk=pk)


@login_required
@group_required('Account Manager')
def account_manager_send_reminder(request, pk):
    """Send reminder to production team"""
    job = get_object_or_404(Job, pk=pk)
    
    if request.method == 'POST':
        # Create notification for production team
        # Ideally we should notify the specific person in charge if they are a user
        # But since person_in_charge is a CharField, we might try to find a user with that name
        # Or just notify all production team members
        
        production_group = Group.objects.filter(name='Production Team').first()
        if production_group:
            recipients = production_group.user_set.all()
            
            # Try to narrow down to person in charge if possible
            if job.person_in_charge:
                specific_user = User.objects.filter(
                    Q(username__iexact=job.person_in_charge) | 
                    Q(first_name__icontains=job.person_in_charge) | 
                    Q(last_name__icontains=job.person_in_charge)
                ).first()
                if specific_user:
                    recipients = [specific_user]
            
            for recipient in recipients:
                Notification.objects.create(
                    recipient=recipient,
                    notification_type='job_reminder',
                    title=f'⏰ Reminder: {job.job_name}',
                    message=f'Reminder for job {job.job_number} ({job.client.name}). Due date: {job.expected_completion}. Please update status.',
                    link=f'/job/{job.pk}/', # Link to PT job detail
                    related_job=job
                )
            
            messages.success(request, f'Reminder sent to production team for {job.job_number}.')
        else:
            messages.warning(request, 'No production team members found to notify.')
            
    return redirect('account_manager_job_detail', pk=pk)



# ========== PRODUCTION TEAM VIEWS (Keep existing) ==========

@login_required
@group_required('Account Manager')
def lead_intake(request):
    """Lead intake with automatic notification creation"""
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            # Save the lead with the current user as creator
            lead = form.save(commit=False)
            lead.created_by = request.user
            lead.save()
            
            # ✅ CREATE NOTIFICATION: Remind AM to create quote
            Notification.objects.create(
                recipient=request.user,
                notification_type='quote_reminder',
                title=f'📝 Create Quote for {lead.name}',
                message=f'New lead created: {lead.name} ({lead.lead_id}). Remember to send them a quote.',
                link=f'/create/quote?lead_id={lead.id}',
                related_lead=lead,
                action_url=f'/create/quote?lead_id={lead.id}',
                action_label='Create Quote'
            )
            
            # Notify all other account managers
            other_ams = User.objects.filter(groups__name='Account Manager').exclude(id=request.user.id)
            for am in other_ams:
                Notification.objects.create(
                    recipient=am,
                    notification_type='lead_created',
                    title=f'👤 New Lead: {lead.name}',
                    message=f'{request.user.get_full_name() or request.user.username} created a new lead',
                    link='/leads/',
                    related_lead=lead
                )
            
            messages.success(request, f'✅ Lead {lead.name} created! Check notifications for next steps.')
            return redirect('lead_intake')
        else:
            messages.error(request, 'Please fill in all required fields')
    else:
        form = LeadForm()
    
    # GET request - show leads list
    search_query = request.GET.get('search', '')
    leads = Lead.objects.all().order_by('-created_at')
    
    if search_query:
        leads = leads.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(lead_id__icontains=search_query)
        )
    
    # Get products for the form
    products = Product.objects.filter(is_visible=True).order_by('name')
    
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
                company = request.POST.get('company_b2c', '').strip()  # Optional
                name = request.POST.get('name_b2c', '').strip()  # Required
                email = request.POST.get('email_b2c', '').strip()  # Optional now
                phone = request.POST.get('phone_b2c', '').strip()  # Required
                preferred_channel = request.POST.get('preferred_channel_b2c', 'Email')
                lead_source = request.POST.get('lead_source_b2c', '')
                
                # Validate required B2C fields
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

                # LEAD CONVERSION CHECK (B2C)
                # Check if this phone/email belongs to a Lead
                existing_lead = Lead.objects.filter(Q(phone=phone) | Q(email=email) if email else Q(phone=phone)).first()
                if existing_lead:
                    # Check if Lead has an APPROVED quote
                    has_approved_quote = Quote.objects.filter(lead=existing_lead, status='Approved').exists()
                    if not has_approved_quote:
                        messages.error(request, f"Cannot onboard Lead '{existing_lead.name}' yet. They must approve a quote first.")
                        return redirect('client_onboarding')
                
                # Create B2C client
                client = Client.objects.create(
                    client_type='B2C',
                    company=company if company else '',
                    name=name,
                    email=email or '',
                    phone=phone,
                    preferred_channel=preferred_channel,
                    lead_source=lead_source,
                    payment_terms='Prepaid',
                    risk_rating='Low',
                    credit_limit=0,
                    is_reseller=False,
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
                company = request.POST.get('company', '').strip()
                name = request.POST.get('name', '').strip()
                email = request.POST.get('email', '').strip()
                phone = request.POST.get('phone', '').strip()
                preferred_channel = request.POST.get('preferred_channel', 'Email')
                lead_source = request.POST.get('lead_source', '')
                
                # Financial fields
                vat_tax_id = request.POST.get('vat_tax_id', '')
                payment_terms = request.POST.get('payment_terms', 'Prepaid')
                risk_rating = request.POST.get('risk_rating', 'Low')
                is_reseller = request.POST.get('is_reseller') == 'on'
                
                # Validate required B2B fields
                if not company or not name or not email or not phone:
                    messages.error(request, 'Please fill in all required fields (Company, Name, Email, Phone)')
                    return redirect('client_onboarding')
                
                # Check for duplicate email
                if Client.objects.filter(email=email).exists():
                    messages.error(request, f'A client with email {email} already exists')
                    return redirect('client_onboarding')

                # LEAD CONVERSION CHECK (B2B) - DISABLED
                # existing_lead = Lead.objects.filter(Q(email=email) | Q(phone=phone)).first()
                # if existing_lead:
                #     # Check if Lead has an APPROVED quote
                #     has_approved_quote = Quote.objects.filter(lead=existing_lead, status='Approved').exists()
                #     if not has_approved_quote:
                #         messages.error(request, f"Cannot onboard Lead '{existing_lead.name}' yet. They must approve a quote first.")
                #         return redirect('client_onboarding')
                
                # Create B2B client
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
                
                # STEP 2: Contacts
                contact_names = request.POST.getlist('contact_name[]')
                contact_emails = request.POST.getlist('contact_email[]')
                contact_phones = request.POST.getlist('contact_phone[]')
                contact_roles = request.POST.getlist('contact_role[]')
                
                for i, contact_name in enumerate(contact_names):
                    if contact_name.strip():
                        ClientContact.objects.create(
                            client=client,
                            full_name=contact_name.strip(),
                            email=contact_emails[i].strip() if i < len(contact_emails) else '',
                            phone=contact_phones[i].strip() if i < len(contact_phones) else '',
                            role=contact_roles[i] if i < len(contact_roles) else 'None',
                        )
                
                # STEP 3: Compliance Documents
                compliance_files = request.FILES.getlist('compliance_files')
                doc_type = request.POST.get('doc_type', '')
                doc_expiry = request.POST.get('doc_expiry', None)
                
                if compliance_files and doc_type:
                    for file in compliance_files:
                        ComplianceDocument.objects.create(
                            client=client,
                            document_type=doc_type,
                            file=file,
                            expiry_date=doc_expiry if doc_expiry else None,
                            uploaded_by=request.user
                        )

                # BRAND ASSETS
                brand_files = request.FILES.getlist('brand_files')
                brand_asset_type = request.POST.get('brand_asset_type', 'Logo')
                if brand_files:
                    from .models import BrandAsset
                    for file in brand_files:
                        BrandAsset.objects.create(
                            client=client,
                            asset_type=brand_asset_type,
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
                        product = Product.objects.get(sku=product_sku, is_visible=True)
                        unit_price = product.base_price
                    except Product.DoesNotExist:
                        messages.error(request, f"Product with SKU {product_sku} not found.")
                        return redirect('create_quote')
                else:
                    # Fallback: try to find product by name
                    try:
                        product = Product.objects.filter(name=product_name, is_visible=True).first()
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
    # Only show published and visible products for quote creation
    products = Product.objects.filter(
        status='published',
        is_visible=True
    ).order_by('name')
    
    today = timezone.now().date()
    default_valid_until = today + timedelta(days=30)
    
    # Get account manager name
    account_manager_name = request.user.get_full_name() or request.user.username
    
    context = {
        'clients': clients,
        'leads': leads,
        'products': products,
        'today': today.isoformat(),
        'default_valid_until': default_valid_until.isoformat(),
        'current_year': today.year,
        'account_manager_name': account_manager_name,
    }
    return render(request, 'quote_detail.html', context)



@login_required
@group_required('Account Manager')
def quote_create(request):
    """Create multi-product quote with product customization logic"""
    from clientapp.models import resolve_unit_price, QuoteLineItem
    
    if request.method == 'POST':
        try:
            # 1. Get Core Form Data
            client_name = request.POST.get('client_name', '').strip()
            valid_until = request.POST.get('valid_until')
            delivery_deadline = request.POST.get('delivery_deadline')
            special_instructions = request.POST.get('special_instructions', '')
            action = request.POST.get('action', 'save_draft')
            
            client_id = request.POST.get('client_id')
            lead_id = request.POST.get('lead_id')

            # 2. Validate Client Selection
            client = None
            lead = None
            if client_id:
                client = get_object_or_404(Client, id=client_id)
            elif lead_id:
                lead = get_object_or_404(Lead, id=lead_id)
            else:
                messages.error(request, "Please select a valid client or lead.")
                return redirect('quote_create')

            # 3. Parse Line Items
            product_ids = request.POST.getlist('product_id[]')
            quantities = request.POST.getlist('quantity[]')
            rates = request.POST.getlist('rate[]')  # Unit prices from form
            variable_amounts = request.POST.getlist('variable_amount[]', [])  # For semi-customizable products

            if not product_ids:
                messages.error(request, 'Please add at least one product to the quote')
                return redirect('quote_create')

            # 4. Check if editing existing quote
            existing_quote_id = request.POST.get('existing_quote_id', '').strip()
            is_editing = bool(existing_quote_id)
            
            # 5. Generate unique quote ID (only for new quotes)
            if is_editing:
                quote_group_id = existing_quote_id
                # Get existing quote
                existing_quote = Quote.objects.filter(quote_id=quote_group_id).first()
                if not existing_quote:
                    messages.error(request, f'Quote {quote_group_id} not found')
                    return redirect('quotes_list')
                
                # Check if quote is locked (sent to PT for costing)
                if existing_quote.status == 'Sent to PT' and request.user.groups.filter(name='Account Manager').exists():
                    messages.error(request, f'Quote {quote_group_id} is locked. Production Team is currently costing this quote. Please wait for costing to complete before editing.')
                    return redirect('quote_detail', quote_id=quote_group_id)
            else:
                quote_group_id = f"Q-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            
            # Initialize variables for email sending (if needed)
            quote_pk = None
            quote_id_for_redirect = quote_group_id
            
            # 6. Process and Save Quote with Line Items (Atomic transaction)
            with transaction.atomic():
                if is_editing:
                    # Update existing quote
                    quote = existing_quote
                    quote.client = client
                    quote.lead = lead
                    quote.valid_until = timezone.datetime.fromisoformat(valid_until).date() if valid_until else quote.valid_until
                    quote.notes = special_instructions
                    # Don't change created_by when editing
                    # Delete existing line items - we'll recreate them
                    QuoteLineItem.objects.filter(quote=quote).delete()
                else:
                    # Create new Quote record
                    quote = Quote(
                        quote_id=quote_group_id,
                        client=client,
                        lead=lead,
                        product_name='',  # Will be set from line items
                        quantity=1,  # Placeholder, actual quantity in line items
                        unit_price=Decimal('0'),  # Will be calculated from line items
                        total_amount=Decimal('0'),  # Will be calculated
                        status='Draft',
                        quote_date=timezone.now().date(),
                        valid_until=timezone.datetime.fromisoformat(valid_until).date() if valid_until else timezone.now().date() + timedelta(days=30),
                        notes=special_instructions,
                        created_by=request.user
                    )
                
                # ✅ SAVE THE QUOTE FIRST to get a primary key
                # This MUST happen before creating any QuoteLineItem objects
                quote.save()
                
                # Verify quote has a primary key
                if not quote.pk:
                    raise ValueError("Quote was not saved properly - no primary key assigned")
                
                # Now we can safely create line items - quote has a PK
                
                # Create line items with pricing snapshots
                total_amount = Decimal('0')
                has_fully_customizable = False
                
                for i in range(len(product_ids)):
                    product = Product.objects.get(id=product_ids[i])
                    qty = int(quantities[i]) if i < len(quantities) else 1
                    var_amount = Decimal(variable_amounts[i]) if i < len(variable_amounts) else Decimal('0')
                    
                    # Get unit price
                    if i < len(rates) and rates[i]:
                        try:
                            unit_price = Decimal(rates[i])
                        except (ValueError, TypeError):
                            unit_price = resolve_unit_price(product)
                    else:
                        unit_price = resolve_unit_price(product)
                    
                    # ✅ NOW create line items - quote has a PK
                    line_item = QuoteLineItem.objects.create(
                        quote=quote,
                        product=product,
                        product_name=product.name,
                        customization_level_snapshot=product.customization_level,
                        base_price_snapshot=product.base_price,
                        quantity=qty,
                        unit_price=unit_price,
                        variable_amount=var_amount,
                        order=i
                    )
                    
                    total_amount += line_item.line_total
                    
                    # Check if product is fully customizable
                    if product.customization_level == 'fully_customizable':
                        has_fully_customizable = True
                
                # Update quote totals
                quote.product_name = f"{len(product_ids)} item(s)" if len(product_ids) > 1 else QuoteLineItem.objects.filter(quote=quote).first().product_name if QuoteLineItem.objects.filter(quote=quote).exists() else ''
                quote.quantity = sum(item.quantity for item in QuoteLineItem.objects.filter(quote=quote))
                quote.total_amount = total_amount
                quote.save()

                # 8. Finalize Status based on the Action button clicked
                if action == 'save_draft':
                    quote.status = 'Draft'
                    quote.save()
                    if is_editing:
                        msg = f"💾 Quote {quote_group_id} updated and saved as draft."
                    else:
                        msg = f"💾 Quote {quote_group_id} saved as draft."
                
                elif action == 'save_send_pt':
                    # Check if quote can be sent to PT
                    can_send, error_msg = quote.can_send_to_pt()
                    if not can_send:
                        messages.error(request, error_msg)
                        quote.delete()  # Clean up
                        return redirect('quote_create')
                    
                    quote.status = 'Sent to PT'
                    quote.production_status = 'pending'
                    quote.save()
                    
                    # Notify Production Team
                    from django.contrib.auth.models import User
                    pt_users = User.objects.filter(groups__name='Production Team')
                    for pt in pt_users:
                        Notification.objects.create(
                            recipient=pt,
                            notification_type='quote_sent_pt',
                            title=f'📋 Quote {quote_group_id} Needs Costing',
                            message=f'New quote from {request.user.get_full_name()} requires costing.',
                            link=f'/production/quote-costing-v2/{quote_group_id}/',
                            related_quote_id=quote_group_id
                        )
                    if is_editing:
                        msg = f"✅ Quote {quote_group_id} updated and sent to PT for costing."
                    else:
                        msg = f"✅ Quote {quote_group_id} sent to PT for costing."
                
                elif action == 'send_to_customer':
                    # Check if quote can be sent to customer
                    can_send, error_msg = quote.can_send_to_customer()
                    if not can_send:
                        messages.error(request, error_msg)
                        return redirect('quote_detail', quote_id=quote_group_id)
                    
                    # Ensure quote is fully saved
                    quote.save()
                    
                    # Store quote_id to fetch fresh instance after transaction commits
                    # We'll handle email sending AFTER the transaction commits
                    quote_pk = quote.pk
                    quote_id_for_redirect = quote_group_id
                    msg = f"💾 Quote {quote_group_id} prepared for sending."
                
                # Log the Activity (only if client exists - leads don't have activity logs)
                if client:
                    ActivityLog.objects.create(
                        client=client,
                        activity_type='Quote',
                        title=f"Quote {quote_group_id} Created",
                        description=f"Quote with {len(product_ids)} items created.",
                        created_by=request.user
                    )

            # Transaction is now committed - all quote and line items are fully saved
            
            # After transaction commits, handle email sending if needed
            if action == 'send_to_customer':
                # Get a fresh instance from database (now fully committed)
                # The transaction has committed, so the quote is fully saved
                quote_for_email = Quote.objects.get(pk=quote_pk)
                
                # Use the send_quote view to handle email sending
                from .quote_approval_services import QuoteApprovalService
                result = QuoteApprovalService.send_quote_via_email(quote_for_email, request)
                
                if result['success']:
                    # Update quote status
                    quote_for_email.status = 'Sent to Customer'
                    quote_for_email.production_status = 'sent_to_client'
                    quote_for_email.save()
                    messages.success(request, f"✅ Quote {quote_id_for_redirect} sent to customer via email.")
                    return redirect('quote_detail', quote_id=quote_id_for_redirect)
                else:
                    messages.error(request, f"Error sending quote: {result.get('message', 'Unknown error')}")
                    return redirect('quote_detail', quote_id=quote_id_for_redirect)
            
            messages.success(request, msg)
            return redirect('quote_detail', quote_id=quote_group_id)

        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('quote_create')

    # GET request logic - handle both new quotes and editing existing quotes
    quote_id = request.GET.get('quote_id')
    existing_quote = None
    existing_line_items = []
    
    if quote_id:
        # Load existing quote for editing
        existing_quote = Quote.objects.filter(quote_id=quote_id).first()
        if existing_quote:
            existing_line_items = QuoteLineItem.objects.filter(quote=existing_quote).order_by('order', 'created_at')
    
    context = {
        'clients': Client.objects.filter(status='Active').order_by('name'),
        'leads': Lead.objects.exclude(status__in=['Converted', 'Lost']).order_by('-created_at'),
        'products': Product.objects.filter(status='published', is_visible=True).order_by('name'),
        'existing_quote': existing_quote,
        'existing_quotes': existing_line_items,  # Template expects 'existing_quotes' for line items
        'existing_line_items': existing_line_items,
        'quote_id': quote_id,
    }
    return render(request, 'quote_create.html', context)

@login_required
def download_quote_pdf(request, quote_id):
    """
    Download quote as PDF
    Accessible to account managers and authorized users
    """
    try:
        from .pdf_utils import QuotePDFGenerator
        
        # Verify quote exists and user has access
        quote = Quote.objects.filter(quote_id=quote_id).first()
        if not quote:
            messages.error(request, f'Quote {quote_id} not found')
            return redirect('quotes_list')
        
        # Generate and return PDF
        return QuotePDFGenerator.download_quote_pdf(quote_id, request)
        
    except Exception as e:
        messages.error(request, f'Error generating PDF: {str(e)}')
        import traceback
        traceback.print_exc()
        return redirect('quotes_list')

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

    # ================= ACTIVITIES =================
    activities = client.activities.all().order_by('-created_at')
    recent_activities = activities[:5]
    all_activities = activities

    # ================= DOCUMENTS =================
    compliance_documents = ComplianceDocument.objects.filter(client=client)
    brand_assets = BrandAsset.objects.filter(client=client) if hasattr(client, 'brand_assets') else []

    # ================= CONTACTS =================
    client_contacts = ClientContact.objects.filter(client=client)

    # ================= FINANCIAL METRICS =================
    total_revenue = all_quotes.filter(status='Approved').aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0')
    
    total_jobs_count = jobs.count()
    
    # Conversion rate (approved quotes / total quotes)
    total_quotes = len(quotes_list)
    approved_quotes = sum(1 for q in quotes_list if q['quote'].status == 'Approved')
    conversion_rate = round((approved_quotes / total_quotes * 100), 1) if total_quotes > 0 else 0
    
    # Last activity
    last_activity_date = recent_activities.first().created_at if recent_activities.exists() else None

    # ================= CONTEXT =================
    context = {
        'client': client,
        'client_quotes': all_quotes,  # For quotes tab table
        'quotes': quotes_list,
        'client_jobs': jobs,
        'recent_activities': recent_activities,
        'all_activities': all_activities,
        'compliance_documents': compliance_documents,
        'brand_assets': brand_assets,
        'client_contacts': client_contacts,
        
        # Metrics for Overview tab
        'total_jobs': total_jobs_count,
        'total_revenue': total_revenue,
        'conversion_rate': conversion_rate,
        'last_activity_date': last_activity_date,
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
    """View detailed quote with all items - Zoho-style with proper button visibility"""
    # Get quote (using quote_id, not pk)
    quote = Quote.objects.filter(quote_id=quote_id).first()
    
    if not quote:
        messages.error(request, 'Quote not found')
        return redirect('dashboard')
    
    # Get line items (preferred) or fallback to old quote records
    line_items = QuoteLineItem.objects.filter(quote=quote).order_by('order', 'created_at')
    
    # Calculate totals from line items
    if line_items.exists():
        subtotal = sum(item.line_total for item in line_items)
        quotes = []  # Empty for backward compatibility
    else:
        # Fallback: use old quote records
        quotes = Quote.objects.filter(quote_id=quote_id).order_by('id')
        subtotal = sum(q.unit_price * q.quantity for q in quotes)
        line_items = []
    
    vat_amount = subtotal * Decimal('0.16') if quote.include_vat else Decimal('0')
    total_amount = subtotal + vat_amount
    
    # Button visibility logic (Zoho-like)
    can_send_to_customer, send_to_customer_error = quote.can_send_to_customer()
    can_send_to_pt, send_to_pt_error = quote.can_send_to_pt()
    
    # Check if quote is locked (sent to PT) - Account Managers cannot edit when sent to PT
    is_locked = quote.status == 'Sent to PT' and request.user.groups.filter(name='Account Manager').exists()
    
    # Pass error message to template
    context = {
        'quote_id': quote_id,
        'quote': quote,
        'quotes': quotes,  # For backward compatibility
        'line_items': line_items,
        'first_quote': quote,  # Alias for template compatibility
        'client': quote.client,
        'lead': quote.lead,
        'subtotal': subtotal,
        'can_send_to_customer': can_send_to_customer,
        'can_send_to_pt': can_send_to_pt,
        'send_to_customer_error': send_to_customer_error,
        'send_to_pt_error': send_to_pt_error,
        'is_locked': is_locked,
        'vat_amount': vat_amount,
        'total_amount': total_amount,
        'production_updates': ProductionUpdate.objects.filter(quote=quote).select_related('created_by').order_by('-created_at'),
    }
    
    return render(request, 'quote_detail.html', context)
    
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

@login_required
def handle_quote_approval(request, quote_id):
    """
    Handle quote approval from client
    Creates notifications across all portals
    """
    try:
        quotes = Quote.objects.filter(quote_id=quote_id)
        if not quotes.exists():
            messages.error(request, 'Quote not found')
            return redirect('quotes_list')
        
        first_quote = quotes.first()
        lead = first_quote.lead
        
        # Update status
        quotes.update(status='Approved', approved_at=timezone.now())
        
        # ✅ CREATE NOTIFICATIONS FOR ALL PORTALS
        
        # 1. Notify the Account Manager who created the quote
        if first_quote.created_by:
            Notification.objects.create(
                recipient=first_quote.created_by,
                notification_type='quote_approved',
                title=f'🎉 Quote {quote_id} Approved!',
                message=f'Client approved your quote. Time to onboard them!',
                link=f'/client-onboarding/?lead_id={lead.id}' if lead else '/clients/',
                related_quote_id=quote_id,
                action_url=f'/client-onboarding/?lead_id={lead.id}' if lead else None,
                action_label='Onboard Client' if lead else None
            )
        
        # 2. Notify all Production Team members
        pt_users = User.objects.filter(groups__name='Production Team')
        for pt in pt_users:
            Notification.objects.create(
                recipient=pt,
                notification_type='quote_approved',
                title=f'✅ Quote {quote_id} Approved',
                message=f'New approved quote ready for production. Value: KES {first_quote.total_amount:,.0f}',
                link=f'/quote-detail/{quote_id}/',
                related_quote_id=quote_id
            )
        
        # 3. Notify all Admins
        admins = User.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                notification_type='quote_approved',
                title=f'Quote {quote_id} Approved',
                message=f'Value: KES {first_quote.total_amount:,.0f}',
                link='/admin/clientapp/quote/',
                related_quote_id=quote_id
            )
        
        messages.success(request, f'Quote {quote_id} approved! Notifications sent.')
        return redirect('quote_detail', quote_id=quote_id)
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('quotes_list')


@login_required
@group_required('Account Manager')
def quotes_list(request):
    """List all quotes with filters"""
    from decimal import Decimal
    from datetime import datetime, timedelta
    
    all_quotes = Quote.objects.select_related('client', 'lead', 'created_by').order_by('-created_at')
    
    # Group quotes by quote_id
    quotes_dict = {}
    for quote in all_quotes:
        if quote.quote_id not in quotes_dict:
            # Determine client name
            client_name = '-'
            if quote.client:
                client_name = quote.client.name
            elif quote.lead:
                client_name = quote.lead.name
            
            # Determine account manager
            account_manager = '-'
            if quote.created_by:
                account_manager = quote.created_by.get_full_name() or quote.created_by.username
            
            # Calculate valid until date (30 days from creation)
            valid_until = quote.created_at + timedelta(days=30)
            days_remaining = (valid_until.date() - datetime.now().date()).days
            
            quotes_dict[quote.quote_id] = {
                'id': quote.id,
                'quote_number': quote.quote_id,
                'client_name': client_name,
                'account_manager': account_manager,
                'item_count': 0,
                'approved_items': 0,
                'total_value': Decimal('0'),
                'total_cost': Decimal('0'),
                'margin': 0,
                'status': quote.status,
                'created_date': quote.created_at.strftime('%b %d, %Y'),
                'valid_until': valid_until.strftime('%b %d, %Y'),
                'days_remaining': days_remaining,
            }
        
        # Increment counters
        quotes_dict[quote.quote_id]['item_count'] += 1
        quotes_dict[quote.quote_id]['total_value'] += quote.total_amount
        if quote.production_cost: 
            quotes_dict[quote.quote_id]['total_cost'] += quote.production_cost
        # Count approved items
        if quote.status == 'Approved':
            quotes_dict[quote.quote_id]['approved_items'] += 1
        
        # Calculate margin (simplified - you may want to adjust this)
        if quote.unit_price > 0:
            # Assuming 25% margin as default - adjust based on your business logic
            quotes_dict[quote.quote_id]['margin'] = 25.0
        for q in quotes_dict.values():
            if q['total_value'] > 0:
                cost = q['total_cost']
                q['margin'] = ((q['total_value'] - cost) / q['total_value']) * 100
            else:
                q['margin'] = 0
    quotes_list = list(quotes_dict.values())

    total_quotes_count = len(quotes_list)
    pending_approval_count = sum(1 for q in quotes_list if q['status'] == 'Pending PT Approval')
    total_value = sum(q['total_value'] for q in quotes_list)
    avg_margin = sum(q['margin'] for q in quotes_list) / total_quotes_count if total_quotes_count > 0 else 0
    
    # Apply status filter
    status_filter = request.GET.get('status', 'all')
    if status_filter and status_filter != 'all':
        quotes_list = [q for q in quotes_list if q['status'] == status_filter]
    
    # Apply search filter
    search_query = request.GET.get('search', '')
    if search_query:
        quotes_list = [q for q in quotes_list if 
                      search_query.lower() in q['quote_number'].lower() or 
                      search_query.lower() in q['client_name'].lower()]
    
    context = {
        'quotes': quotes_list,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_quotes_count': total_quotes_count,
        'pending_approval_count': pending_approval_count,
        'total_value': total_value,
        'avg_margin': avg_margin,
    }
    
    return render(request, 'quote_list.html', context)


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
    """View job details with all related information"""
    from django.utils import timezone
    from datetime import timedelta
    from decimal import Decimal
    
    job = get_object_or_404(Job.objects.select_related('client', 'quote', 'created_by'), pk=pk)
    
    # Get related data
    attachments = job.attachments.select_related('uploaded_by').order_by('-uploaded_at')
    notes = job.job_notes.select_related('created_by').order_by('-created_at')
    production_updates = job.production_updates.select_related('created_by').order_by('-created_at')
    
    # Get vendor stages if they exist
    vendor_stages = job.vendor_stages.select_related('vendor').order_by('stage_order') if hasattr(job, 'vendor_stages') else []
    
    # Get QC inspection if exists
    qc_inspection = None
    try:
        qc_inspection = job.qc_inspection
    except:
        pass
    
    # Calculate progress
    overall_progress = 0
    current_stage = None
    if vendor_stages:
        total_stages = len(vendor_stages)
        completed_stages = sum(1 for s in vendor_stages if s.status == 'completed')
        in_progress_stage = next((s for s in vendor_stages if s.status in ['in_production', 'sent_to_vendor']), None)
        
        if in_progress_stage:
            # Calculate based on stages + current stage progress
            base_progress = (completed_stages / total_stages) * 100
            stage_contribution = (in_progress_stage.progress / total_stages)
            overall_progress = int(base_progress + stage_contribution)
            current_stage = in_progress_stage
        else:
            overall_progress = int((completed_stages / total_stages) * 100) if completed_stages > 0 else 0
    elif job.status == 'completed':
        overall_progress = 100
    elif job.status == 'in_progress':
        # Get from last production update if available
        last_update = production_updates.first()
        overall_progress = last_update.progress if last_update else 50
    else:
        overall_progress = 0
    
    # Calculate deadline info
    now = timezone.now()
    deadline = timezone.make_aware(
        timezone.datetime.combine(job.expected_completion, timezone.datetime.min.time())
    ) if job.expected_completion else now
    time_remaining = deadline - now
    hours_remaining = int(time_remaining.total_seconds() / 3600)
    is_overdue = hours_remaining < 0
    
    if is_overdue:
        deadline_text = f"Overdue by {abs(hours_remaining)}h"
    elif hours_remaining < 24:
        deadline_text = f"{hours_remaining}h remaining"
    else:
        days_remaining = hours_remaining // 24
        deadline_text = f"{days_remaining} days remaining"
    
    # Get primary vendor (from current stage or first stage)
    primary_vendor = None
    if vendor_stages:
        current = current_stage or vendor_stages[0]
        primary_vendor = current.vendor
    
    # Get account manager who created this job
    am_name = "System"
    if job.created_by:
        am_name = job.created_by.get_full_name() or job.created_by.username
    
    # Calculate current stage info
    current_stage_text = "Not Started"
    if current_stage:
        current_stage_text = f"{current_stage.stage_name} (Day {(now - current_stage.started_at).days + 1 if current_stage.started_at else 1} of {(current_stage.expected_completion - current_stage.started_at).days if current_stage.started_at and current_stage.expected_completion else '?'})"
    elif job.status == 'completed':
        current_stage_text = "Completed"
    elif job.status == 'in_progress':
        current_stage_text = "Vendor Production"
    
    # Get job specs from quote if available
    specs = {}
    if job.quote:
        specs = {
            'product_type': job.quote.product_name or job.product,
            'colors': '4/4 (CMYK both sides)',  # Default, could be stored in quote
            'size': 'A4 (210mm × 297mm)',  # Default
            'finishing': 'Matt Lamination',  # Default
            'quantity': f"{job.quantity:,} pcs",
            'folding': 'Tri-fold',  # Default
            'material': '150gsm Gloss Art Paper',  # Default
            'binding': 'None',  # Default
        }
    else:
        specs = {
            'product_type': job.product,
            'colors': '4/4 (CMYK both sides)',
            'size': 'A4 (210mm × 297mm)',
            'finishing': 'Matt Lamination',
            'quantity': f"{job.quantity:,} pcs",
            'folding': 'None',
            'material': 'Standard',
            'binding': 'None',
        }
    
    # Check if user can manage
    can_manage = request.user.groups.filter(name='Production Team').exists()
    
    # Get all jobs for the same client (for tabular view)
    client_jobs = []
    job_stats = {'total': 0, 'in_progress': 0, 'overdue': 0, 'completed': 0, 'pending': 0}
    
    if job.client:
        client_jobs_qs = Job.objects.filter(client=job.client).select_related('quote').order_by('-created_at')
        for cj in client_jobs_qs:
            # Calculate progress for each job
            cj_progress = 0
            if cj.status == 'completed':
                cj_progress = 100
            elif cj.status == 'in_progress':
                cj_progress = 50
            elif cj.status == 'pending':
                cj_progress = 10
            
            # Calculate deadline info
            cj_days = (cj.expected_completion - now.date()).days if cj.expected_completion else 0
            cj_is_overdue = cj_days < 0
            
            client_jobs.append({
                'id': cj.id,
                'job_number': cj.job_number,
                'product': cj.product,
                'quantity': cj.quantity,
                'status': cj.status,
                'status_display': cj.get_status_display(),
                'priority': cj.priority,
                'priority_display': cj.get_priority_display(),
                'expected_completion': cj.expected_completion,
                'days_remaining': cj_days,
                'is_overdue': cj_is_overdue,
                'progress': cj_progress,
                'is_current': cj.id == job.id,
                'job_type': cj.get_job_type_display(),
                'person_in_charge': cj.person_in_charge,
                'notes': cj.notes[:50] + '...' if cj.notes and len(cj.notes) > 50 else cj.notes,
            })
            
            # Update stats
            job_stats['total'] += 1
            if cj.status == 'in_progress':
                job_stats['in_progress'] += 1
            elif cj.status == 'completed':
                job_stats['completed'] += 1
            elif cj.status == 'pending':
                job_stats['pending'] += 1
            if cj_is_overdue and cj.status != 'completed':
                job_stats['overdue'] += 1
    
    context = {
        'job': job,
        'current_view': 'my_jobs',
        'client_jobs': client_jobs,
        'job_stats': job_stats,
        
        # Progress info
        'overall_progress': overall_progress,
        'current_stage': current_stage,
        'current_stage_text': current_stage_text,
        
        # Deadline info
        'deadline_text': deadline_text,
        'hours_remaining': hours_remaining,
        'is_overdue': is_overdue,
        
        # Related data
        'attachments': attachments,
        'notes': notes,
        'production_updates': production_updates,
        'vendor_stages': vendor_stages,
        'qc_inspection': qc_inspection,
        
        # Vendor info
        'primary_vendor': primary_vendor,
        'am_name': am_name,
        
        # Job specs
        'specs': specs,
        
        # Permissions
        'can_manage': can_manage,
        
        # For vendor/process lists
        'vendors': Vendor.objects.filter(active=True).order_by('name'),
    }
    
    return render(request, 'job_detail.html', context)


@login_required
@require_POST
def add_job_note(request, pk):
    """Add a note to a job"""
    job = get_object_or_404(Job, pk=pk)
    
    content = request.POST.get('content', '').strip()
    note_type = request.POST.get('note_type', 'general')
    
    if not content:
        return JsonResponse({'success': False, 'message': 'Note content is required'})
    
    try:
        from clientapp.models import JobNote
        
        note = JobNote.objects.create(
            job=job,
            content=content,
            note_type=note_type,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Note added successfully',
            'note': {
                'id': note.id,
                'content': note.content,
                'note_type': note.note_type,
                'created_by': note.created_by.get_full_name() or note.created_by.username,
                'created_at': note.created_at.strftime('%b %d, %H:%M'),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_POST
def upload_job_file(request, pk):
    """Upload a file attachment to a job"""
    job = get_object_or_404(Job, pk=pk)
    
    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'message': 'No file provided'})
    
    uploaded_file = request.FILES['file']
    
    # Validate file size (max 10MB)
    if uploaded_file.size > 10 * 1024 * 1024:
        return JsonResponse({'success': False, 'message': 'File too large (max 10MB)'})
    
    try:
        from clientapp.models import JobAttachment
        
        attachment = JobAttachment.objects.create(
            job=job,
            file=uploaded_file,
            file_name=uploaded_file.name,
            file_size=uploaded_file.size,
            uploaded_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'File uploaded successfully',
            'attachment': {
                'id': attachment.id,
                'file_name': attachment.file_name,
                'file_size': f"{attachment.file_size / 1024:.1f} KB" if attachment.file_size < 1024*1024 else f"{attachment.file_size / (1024*1024):.1f} MB",
                'uploaded_at': attachment.uploaded_at.strftime('%b %d, %H:%M'),
                'download_url': attachment.file.url,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_POST
def update_job_progress(request, pk):
    """Update job progress and vendor stage"""
    job = get_object_or_404(Job, pk=pk)
    
    try:
        import json
        data = json.loads(request.body)
        
        stage_id = data.get('stage_id')
        progress = data.get('progress', 0)
        status = data.get('status')
        notes = data.get('notes', '')
        
        if stage_id:
            from clientapp.models import JobVendorStage
            stage = get_object_or_404(JobVendorStage, pk=stage_id, job=job)
            stage.progress = progress
            if status:
                stage.status = status
                if status == 'completed' and not stage.completed_at:
                    stage.completed_at = timezone.now()
                elif status == 'in_production' and not stage.started_at:
                    stage.started_at = timezone.now()
            if notes:
                stage.notes = notes
            stage.save()
        
        # Update overall job status
        if data.get('mark_completed'):
            job.status = 'completed'
            job.actual_completion = timezone.now().date()
            job.save()
            
            # Also update related LPO status to 'completed'
            if job.quote and hasattr(job.quote, 'lpo'):
                try:
                    lpo = job.quote.lpo
                    if lpo.status != 'completed':
                        lpo.status = 'completed'
                        lpo.save()
                except:
                    pass
        
        return JsonResponse({'success': True, 'message': 'Progress updated'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_POST
def add_vendor_stage(request, pk):
    """Add a new vendor stage to a job"""
    job = get_object_or_404(Job, pk=pk)
    
    try:
        from clientapp.models import JobVendorStage
        
        vendor_id = request.POST.get('vendor_id')
        stage_name = request.POST.get('stage_name', 'Production')
        expected_days = int(request.POST.get('expected_days', 3))
        vendor_cost = request.POST.get('vendor_cost', 0)
        
        vendor = get_object_or_404(Vendor, pk=vendor_id)
        
        # Get next stage order
        last_stage = job.vendor_stages.order_by('-stage_order').first()
        next_order = (last_stage.stage_order + 1) if last_stage else 1
        
        stage = JobVendorStage.objects.create(
            job=job,
            vendor=vendor,
            stage_order=next_order,
            stage_name=stage_name,
            expected_completion=timezone.now() + timedelta(days=expected_days),
            vendor_cost=vendor_cost,
        )
        
        # Update job status if first stage
        if next_order == 1:
            job.status = 'in_progress'
            job.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Stage "{stage_name}" added',
            'stage_id': stage.id
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@group_required('Production Team')
def qc_inspection_start(request, job_id):
    """Start a QC inspection for a completed job"""
    job = get_object_or_404(Job.objects.select_related('client'), pk=job_id)
    
    # Check if QC inspection already exists
    try:
        existing_qc = job.qc_inspection
        # If exists, redirect to it
        return redirect('qc_inspection', inspection_id=existing_qc.id)
    except:
        pass
    
    # Allow QC inspection for jobs that are ready for QC (not just completed jobs)
    
    # Create new QC inspection
    try:
        from clientapp.models import QCInspection, Vendor
        
        # Generate reference number
        from django.utils import timezone
        year = timezone.now().year
        month = timezone.now().month
        count = QCInspection.objects.filter(
            created_at__year=year,
            created_at__month=month
        ).count() + 1
        ref_number = f"QC-{year}{month:02d}-{count:04d}"
        
        # Get vendor from job's vendor stages if available
        vendor = None
        if hasattr(job, 'vendor_stages') and job.vendor_stages.exists():
            last_stage = job.vendor_stages.order_by('-stage_order').first()
            vendor = last_stage.vendor if last_stage else None
        
        # If no vendor, get the first active vendor as default
        if not vendor:
            vendor = Vendor.objects.filter(active=True).first()
        
        if not vendor:
            messages.error(request, 'No vendor available for QC inspection. Please add a vendor first.')
            return redirect('job_detail', pk=job_id)
        
        qc = QCInspection.objects.create(
            job=job,
            status='pending',
            inspector=request.user
        )
        
        messages.success(request, f'QC Inspection {ref_number} started.')
        return redirect('qc_inspection', inspection_id=qc.id)
    except Exception as e:
        messages.error(request, f'Error creating QC inspection: {str(e)}')
        return redirect('job_detail', pk=job_id)


@login_required
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
            return redirect('my_quotes')
    else:
        form = QuoteCostingForm(instance=quote)

    context = {
        'quote': quote,
        'related_quotes': related_quotes,
        'form': form,
        'current_view': 'production_quotes',
        'processes': Process.objects.filter(status='active'),
    }
    return render(request, 'approve_quote.html', context)


# Add this AFTER your existing update_quote_costing view (around line 1138)

@login_required
@group_required('Production Team')
@transaction.atomic
def update_quote_costing_v2(request, quote_id):
    """
    Updated quote costing with Process integration
    Automatically pulls costs from linked processes
    """
    quote = get_object_or_404(Quote, quote_id=quote_id)
    related_quotes = Quote.objects.filter(quote_id=quote.quote_id).order_by('created_at')
    
    if request.method == 'POST':
        try:
            # Get form data
            action = request.POST.get('action', 'save')
            
            # Get line items (preferred) or fallback to old quote records
            line_items = QuoteLineItem.objects.filter(quote=quote).order_by('order', 'created_at')
            
            if line_items.exists():
                # Update QuoteLineItem prices with PT costing
                total_amount = Decimal('0')
                
                for item in line_items:
                    # Get costs from form (use line item ID)
                    unit_price_key = f'unit_price_{item.id}'
                    production_cost_key = f'production_cost_{item.id}'
                    vendor_id_key = f'selected_vendor_{item.id}'
                    
                    # Update unit price if provided
                    if unit_price_key in request.POST and request.POST[unit_price_key]:
                        try:
                            item.unit_price = Decimal(request.POST[unit_price_key])
                            item.save()  # This will recalculate line_total
                        except (ValueError, TypeError):
                            pass
                    
                    # Store production cost if provided
                    if production_cost_key in request.POST and request.POST[production_cost_key]:
                        try:
                            quote.production_cost = Decimal(request.POST[production_cost_key])
                        except (ValueError, TypeError):
                            pass
                    
                    total_amount += item.line_total
                
                # Update quote totals from line items
                quote.total_amount = total_amount
                if quote.include_vat:
                    vat_amount = total_amount * Decimal('0.16')
                    quote.total_amount = total_amount + vat_amount
            else:
                # Fallback: update old quote records
                for q in related_quotes:
                    production_cost = request.POST.get(f'production_cost_{q.id}')
                    vendor_id = request.POST.get(f'selected_vendor_{q.id}')
                    
                    if production_cost:
                        q.production_cost = Decimal(production_cost)
                    q.save()
            
            # Update status based on action
            if action == 'approve':
                quote.production_status = 'costed'
                quote.costed_by = request.user
                # Set status to 'Sent to PT' first if it's Draft, then to 'Costed'
                # This ensures proper status transition
                if quote.status == 'Draft':
                    # Temporarily bypass validation to set intermediate status
                    quote._skip_status_validation = True
                    quote.status = 'Sent to PT'
                    quote.save()
                    quote._skip_status_validation = False
                # Now transition to Costed
                quote.status = 'Costed'
                quote.save()
            
            # Create production update
            ProductionUpdate.objects.create(
                update_type='quote',
                quote=quote,
                status='costed' if action == 'approve' else 'in_progress',
                progress=100 if action == 'approve' else 50,
                notes=request.POST.get('production_notes', ''),
                created_by=request.user
            )
            
            if action == 'approve':
                # Notify AM
                Notification.objects.create(
                    recipient=quote.created_by,
                    notification_type='quote_pt_approved',
                    title=f'✅ Quote {quote_id} Costed & Ready',
                    message=f'Production team has costed your quote. You can now send it to the client.',
                    link=reverse('quote_detail', args=[quote_id]),
                    related_quote_id=quote_id,
                    action_url=reverse('quote_detail', args=[quote_id]),
                    action_label='View Quote'
                )
                
                messages.success(request, f'✅ Quote {quote_id} costed and approved!')
            else:
                messages.success(request, f'💾 Quote {quote_id} costing saved as draft.')
            
            return redirect('production_quote_review')
            
        except Exception as e:
            messages.error(request, f'Error saving costing: {str(e)}')
            import traceback
            traceback.print_exc()
            return redirect('production_quote_costing_v2', quote_id=quote_id)
    
    # GET request - prepare data for template
    
    # Get all available processes
    processes = Process.objects.filter(status='active').order_by('process_name')
    
    # Get line items (preferred) or fallback to old quote records
    line_items_objs = QuoteLineItem.objects.filter(quote=quote).order_by('order', 'created_at')
    
    # Prepare line items with process suggestions
    line_items = []
    
    if line_items_objs.exists():
        # Use QuoteLineItem
        for item in line_items_objs:
            suggested_process = None
            process_cost = None
            available_vendors = []
            
            # Try to find matching process by product
            if item.product and hasattr(item.product, 'pricing'):
                pricing = item.product.pricing
                if pricing.process:
                    suggested_process = pricing.process
                elif pricing.formula_process:
                    suggested_process = pricing.formula_process
                elif pricing.tier_process:
                    suggested_process = pricing.tier_process
            
            # If no process linked, search by product name similarity
            if not suggested_process:
                for process in processes:
                    if item.product_name.lower() in process.process_name.lower() or \
                       process.process_name.lower() in item.product_name.lower():
                        suggested_process = process
                        break
            
            # Get pricing based on quantity
            if suggested_process and suggested_process.pricing_type == 'tier':
                tier = suggested_process.tiers.filter(
                    quantity_from__lte=item.quantity,
                    quantity_to__gte=item.quantity
                ).first()
                if tier:
                    process_cost = tier.cost
            
            # Get vendors
            if suggested_process:
                available_vendors = suggested_process.process_vendors.all().order_by('-vps_score')
            
            line_items.append({
                'line_item': item,
                'quote': None,  # Not using old quote records
                'suggested_process': suggested_process,
                'process_cost': process_cost,
                'available_vendors': available_vendors,
                'current_cost': item.unit_price or Decimal('0'),
            })
    else:
        # Fallback: use old quote records
        for q in related_quotes:
            suggested_process = None
            process_cost = None
            available_vendors = []
            
            # Search for process by product name similarity
            for process in processes:
                if q.product_name.lower() in process.process_name.lower() or \
                   process.process_name.lower() in q.product_name.lower():
                    suggested_process = process
                    
                    # Get pricing based on quantity
                    if process.pricing_type == 'tier':
                        tier = process.tiers.filter(
                            quantity_from__lte=q.quantity,
                            quantity_to__gte=q.quantity
                        ).first()
                        if tier:
                            process_cost = tier.cost
                    
                    # Get vendors
                    available_vendors = process.process_vendors.all().order_by('-vps_score')
                    break
            
            line_items.append({
                'line_item': None,
                'quote': q,
                'suggested_process': suggested_process,
                'process_cost': process_cost,
                'available_vendors': available_vendors,
                'current_cost': q.production_cost or Decimal('0'),
            })
    
    context = {
        'quote_id': quote_id,
        'quote': quote,
        'line_items': line_items,
        'processes': processes,
        'current_view': 'production_quotes',
    }
    
    return render(request, 'quote_costing_v2.html', context)


@login_required
@group_required('Production Team')
def production_catalog(request):
    """Production Team product/catalog view with create & update actions"""
    search = request.GET.get('search', '').strip()
    product_type = request.GET.get('product_type', 'all')
    availability = request.GET.get('availability', 'all')

    products = Product.objects.all()

    # Apply filters
    if search:
        products = products.filter(Q(name__icontains=search) | Q(internal_code__icontains=search))
    if product_type != 'all':
        products = products.filter(product_type=product_type)
    if availability != 'all':
        products = products.filter(availability=availability)

    products = products.order_by('name')

    editing_product = None
    form = ProductionUpdateForm()

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

        form = ProductionUpdateForm(request.POST, instance=editing_product)
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
            form = ProductionUpdateForm(instance=editing_product)

    context = {
        'current_view': 'production_catalog',
        'products': products,
        'form': form,
        'editing_product': editing_product,
        'search': search,
        'product_type': product_type,
        'availability': availability,
    }
    return render(request, 'product_catalog.html', context)


# ================================
# PROCESS MANAGEMENT VIEWS (FORMULA-BASED PRICING)
# ================================

@login_required
@require_POST
def ajax_delete_process(request, process_id):
    """Delete a process via AJAX"""
    try:
        process = get_object_or_404(Process, pk=process_id)
        process_name = process.process_name
        process.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Process "{process_name}" deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
def process_variable_ranges_manager(request, process_id):
    """
    Web interface to manage variable ranges for a process
    """
    from .models import Process, ProcessVariable, ProcessVariableRange
    from django.contrib import messages
    
    process = get_object_or_404(Process, pk=process_id)
    
    if process.pricing_type != 'formula':
        messages.error(request, f"Process {process.process_name} is not formula-based.")
        return redirect('process_list')
    
    variables = process.variables.all().prefetch_related('ranges')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_range':
            return add_variable_range(request, process)
        elif action == 'delete_range':
            return delete_variable_range(request, process)
        elif action == 'create_sample_ranges':
            return create_sample_ranges(request, process)
    
    context = {
        'process': process,
        'variables': variables,
    }
    
    return render(request, 'process_variable_ranges_manager.html', context)

@login_required
def add_variable_range(request, process):
    """
    Add a new variable range via AJAX
    """
    from .models import ProcessVariable, ProcessVariableRange
    from django.contrib import messages
    
    try:
        variable_id = request.POST.get('variable_id')
        min_value = request.POST.get('min_value')
        max_value = request.POST.get('max_value')
        price = request.POST.get('price')
        rate = request.POST.get('rate') or '1.0'
        order = request.POST.get('order') or '1'
        
        variable = get_object_or_404(ProcessVariable, pk=variable_id, process=process)
        
        # Convert to Decimal
        min_val = Decimal(min_value) if min_value else None
        max_val = Decimal(max_value) if max_value else None
        price_val = Decimal(price) if price else Decimal('0')
        rate_val = Decimal(rate)
        order_val = int(order)
        
        # Create the range
        range_obj = ProcessVariableRange.objects.create(
            variable=variable,
            min_value=min_val,
            max_value=max_val,
            price=price_val,
            rate=rate_val,
            order=order_val
        )
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Range added successfully',
                'range': {
                    'id': range_obj.id,
                    'min_value': str(range_obj.min_value) if range_obj.min_value else '',
                    'max_value': str(range_obj.max_value) if range_obj.max_value else '',
                    'price': str(range_obj.price),
                    'rate': str(range_obj.rate),
                    'order': range_obj.order
                }
            })
        
        messages.success(request, 'Variable range added successfully!')
        
    except Exception as e:
        error_msg = f'Error adding range: {str(e)}'
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error_msg})
        messages.error(request, error_msg)
    
    return redirect('process_variable_ranges_manager', process_id=process.id)

@login_required
def delete_variable_range(request, process):
    """
    Delete a variable range via AJAX
    """
    from .models import ProcessVariableRange
    from django.contrib import messages
    
    try:
        range_id = request.POST.get('range_id')
        range_obj = get_object_or_404(ProcessVariableRange, pk=range_id, variable__process=process)
        range_obj.delete()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Range deleted successfully'
            })
        
        messages.success(request, 'Variable range deleted successfully!')
        
    except Exception as e:
        error_msg = f'Error deleting range: {str(e)}'
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error_msg})
        messages.error(request, error_msg)
    
    return redirect('process_variable_ranges_manager', process_id=process.id)

@login_required
def create_sample_ranges(request, process):
    """
    Create sample ranges for all variables in a process
    """
    from .models import ProcessVariable, ProcessVariableRange
    from django.contrib import messages
    
    try:
        variables = process.variables.all()
        ranges_created = 0
        
        for variable in variables:
            # Check if ranges already exist
            if variable.ranges.exists():
                continue
            
            # Create sample ranges based on variable type and name
            ranges_created += create_sample_ranges_for_variable(variable)
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Created {ranges_created} sample ranges',
                'ranges_created': ranges_created
            })
        
        messages.success(request, f'Created {ranges_created} sample ranges!')
        
    except Exception as e:
        error_msg = f'Error creating sample ranges: {str(e)}'
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error_msg})
        messages.error(request, error_msg)
    
    return redirect('process_variable_ranges_manager', process_id=process.id)

def create_sample_ranges_for_variable(variable):
    """
    Create sample ranges for a specific variable
    """
    from .models import ProcessVariableRange
    
    ranges_created = 0
    
    # Stitch Count ranges
    if 'stitch' in variable.variable_name.lower():
        sample_ranges = [
            (1, 1000, Decimal('0.15'), Decimal('1.0'), 1),
            (1001, 5000, Decimal('0.12'), Decimal('1.0'), 2),
            (5001, 15000, Decimal('0.10'), Decimal('1.0'), 3),
            (15001, 30000, Decimal('0.08'), Decimal('1.0'), 4),
            (30001, 50000, Decimal('0.06'), Decimal('1.0'), 5),
        ]
    # Size ranges
    elif 'size' in variable.variable_name.lower() and variable.variable_type == 'number':
        sample_ranges = [
            (1, 5, Decimal('0.50'), Decimal('1.0'), 1),
            (6, 10, Decimal('0.75'), Decimal('1.0'), 2),
            (11, 20, Decimal('1.00'), Decimal('1.0'), 3),
            (21, 30, Decimal('1.50'), Decimal('1.0'), 4),
        ]
    # Color ranges
    elif 'color' in variable.variable_name.lower():
        sample_ranges = [
            (1, 2, Decimal('25.00'), Decimal('1.0'), 1),
            (3, 4, Decimal('40.00'), Decimal('1.0'), 2),
            (5, 6, Decimal('60.00'), Decimal('1.0'), 3),
            (7, 8, Decimal('85.00'), Decimal('1.0'), 4),
            (9, 12, Decimal('120.00'), Decimal('1.0'), 5),
        ]
    # Generic number ranges
    elif variable.variable_type == 'number':
        sample_ranges = [
            (1, 10, Decimal('10.00'), Decimal('1.0'), 1),
            (11, 50, Decimal('8.00'), Decimal('1.0'), 2),
            (51, 100, Decimal('6.00'), Decimal('1.0'), 3),
            (101, 500, Decimal('4.00'), Decimal('1.0'), 4),
            (501, 1000, Decimal('2.00'), Decimal('1.0'), 5),
        ]
    # Generic dropdown ranges
    else:
        sample_ranges = [
            (1, 1, Decimal('20.00'), Decimal('1.0'), 1),
            (2, 2, Decimal('35.00'), Decimal('1.0'), 2),
            (3, 3, Decimal('50.00'), Decimal('1.0'), 3),
            (4, 4, Decimal('70.00'), Decimal('1.0'), 4),
            (5, 5, Decimal('90.00'), Decimal('1.0'), 5),
        ]
    
    # Create the ranges
    for min_val, max_val, price, rate, order in sample_ranges:
        ProcessVariableRange.objects.create(
            variable=variable,
            min_value=Decimal(str(min_val)),
            max_value=Decimal(str(max_val)),
            price=price,
            rate=rate,
            order=order
        )
        ranges_created += 1
    
    return ranges_created

@login_required
def process_list(request):
    """
    List all processes with links to manage variable ranges
    """
    from .models import Process
    
    processes = Process.objects.filter(pricing_type='formula').prefetch_related('variables__ranges')
    
    context = {
        'processes': processes,
    }
    
    return render(request, 'process_list.html', context)

    if search:
        products = products.filter(Q(name__icontains=search) | Q(sku__icontains=search))
    if product_type != 'all':
        products = products.filter(product_type=product_type)
    if availability != 'all':
        products = products.filter(availability=availability)

    products = products.order_by('name')

    editing_product = None
    form = ProductionUpdateForm()

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

        form = ProductionUpdateForm(request.POST, instance=editing_product)
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
            form = ProductionUpdateForm(instance=editing_product)

    context = {
        'current_view': 'production_catalog',
        'products': products,
        'form': form,
        'editing_product': editing_product,
        'search': search,
        'product_type': product_type,
        'availability': availability,
    }
    return render(request, 'product_catalog.html', context)

@login_required
@group_required('Production Team')
def production2_dashboard(request):
    """Production Team dashboard with REAL data"""
    from django.db.models import Q, Count
    from datetime import timedelta
    
    # Get current user
    user = request.user
    
    # ===== JOB COUNTS =====
    total_jobs = Job.objects.count()
    completed_jobs = Job.objects.filter(status='completed').count()
    active_jobs = Job.objects.filter(status__in=['in_progress', 'pending']).count()
    
    # Quotes awaiting approval from PT
    quote_jobs = Quote.objects.filter(
        production_status='pending',
        status='Draft'
    ).count()
    
    # Jobs with issues (overdue or on hold)
    today = timezone.now().date()
    issue_jobs = Job.objects.filter(
        Q(status='on_hold')
        | Q(expected_completion__lt=today, status__in=['pending', 'in_progress'])
    ).count()
    
    # ===== URGENT JOBS =====
    # Jobs due within 3 days
    three_days_from_now = today + timedelta(days=3)
    urgent_jobs = Job.objects.filter(
        status__in=['pending', 'in_progress'],
        expected_completion__lte=three_days_from_now
    ).select_related('client').order_by('expected_completion')[:5]
    
    # Add calculated fields
    for job in urgent_jobs:
        job.product_name = job.product
        days_left = (job.expected_completion - today).days
        if days_left == 0:
            job.urgency_label = "Due Today"
        elif days_left < 0:
            job.urgency_label = f"Overdue by {abs(days_left)} days"
        else:
            job.urgency_label = f"{days_left} days left"
    
    # ===== MY ACTIVE JOBS (for logged-in user) =====
    # Show jobs created by user OR where user is person in charge
    my_active_jobs = Job.objects.filter(
        Q(created_by=user) | 
        Q(person_in_charge__icontains=user.first_name) | 
        Q(person_in_charge__icontains=user.username),
        status__in=['pending', 'in_progress']
    ).select_related('client').order_by('expected_completion')[:5]
    
    # Add status badges and deadline info
    for job in my_active_jobs:
        job.status_class = job.status.replace('_', '-')
        job.status_label = job.get_status_display()
        
        days_until = (job.expected_completion - today).days
        if days_until < 0:
            job.deadline_warning = True
            job.deadline_text = f"Overdue by {abs(days_until)} days"
        elif days_until == 0:
            job.deadline_warning = True
            job.deadline_text = "Due Today"
        else:
            job.deadline_warning = False
            job.deadline_text = job.expected_completion.strftime("%b %d")

    # ===== USER PERFORMANCE METRICS =====
    # Jobs completed by this user (created by or assigned to)
    user_jobs_query = Q(created_by=user) | Q(person_in_charge__icontains=user.first_name) | Q(person_in_charge__icontains=user.username)
    
    user_jobs_total = Job.objects.filter(user_jobs_query).count()
    user_jobs_completed = Job.objects.filter(
        user_jobs_query, status='completed'
    ).count()
    user_completion_rate = (
        round((user_jobs_completed / user_jobs_total) * 100, 1)
        if user_jobs_total > 0
        else 0
    )

    # Average costing time (in hours) for quotes costed by this user
    costed_quotes = Quote.objects.filter(
        costed_by=user,
        production_status__in=['costed', 'sent_to_client', 'in_production', 'completed'],
    )
    total_hours = 0
    count_costed = 0
    for q in costed_quotes:
        # Use created_at -> updated_at as a proxy for costing duration
        if q.created_at and q.updated_at and q.updated_at > q.created_at:
            delta = q.updated_at - q.created_at
            total_hours += delta.total_seconds() / 3600.0
            count_costed += 1

    average_costing_time = round(total_hours / count_costed, 1) if count_costed > 0 else 0.0
    
    context = {
        'current_view': 'production_dashboard',
        'user': user,
        
        # Job counts
        'total_jobs': total_jobs,
        'completed_jobs': completed_jobs,
        'active_jobs': active_jobs,
        'quote_jobs': quote_jobs,
        'issue_jobs': issue_jobs,
        
        # Urgent section
        'urgent_jobs': urgent_jobs,
        
        # My active jobs
        'my_active_jobs': my_active_jobs,
        
        # Performance metrics
        'user_jobs_total': user_jobs_total,
        'user_jobs_completed': user_jobs_completed,
        'user_completion_rate': user_completion_rate,
        'average_costing_time': average_costing_time,
    }
    
    return render(request, 'production2_dashboard.html', context)
@login_required
@group_required('Production Team')
def production_analytics(request):
    """Production-side analytics"""
    # 1. Total Revenue (90d)
    ninety_days_ago = timezone.now().date() - timedelta(days=90)
    
    # Calculate revenue from completed jobs in last 90 days
    completed_jobs_revenue = Job.objects.filter(
        status='completed',
        actual_completion__gte=ninety_days_ago
    ).aggregate(total=Sum('quote__total_amount'))['total'] or 0
    
    # 2. Quote Conversion (Approved / Total Quoted)
    total_quotes_90d = Quote.objects.filter(created_at__gte=ninety_days_ago).count()
    approved_quotes_90d = Quote.objects.filter(
        created_at__gte=ninety_days_ago, 
        status='Approved'
    ).count()
    quote_conversion = (approved_quotes_90d / total_quotes_90d * 100) if total_quotes_90d > 0 else 0
    
    # 3. Avg Profit Margin
    margin_quotes = Quote.objects.filter(
        status='Approved',
        production_cost__gt=0,
        total_amount__gt=0,
        created_at__gte=ninety_days_ago
    )
    
    total_margin_revenue = margin_quotes.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_margin_cost = margin_quotes.aggregate(Sum('production_cost'))['production_cost__sum'] or 0
    
    avg_profit_margin = 0
    if total_margin_revenue > 0:
        avg_profit_margin = ((total_margin_revenue - total_margin_cost) / total_margin_revenue) * 100
        
    # 4. Catalog Health Score
    total_products = Product.objects.count()
    healthy_products = Product.objects.exclude(description='').count()
    catalog_health = (healthy_products / total_products * 100) if total_products > 0 else 0
    
    # 5. Top Products
    top_products = Job.objects.filter(
        status='completed',
        actual_completion__gte=ninety_days_ago
    ).values(
        'product__name'
    ).annotate(
        revenue=Sum('quote__total_amount'),
        count=Count('id')
    ).order_by('-revenue')[:5]
    
    context = {
        'current_view': 'production_analytics',
        'total_revenue': completed_jobs_revenue,
        'quote_conversion': round(quote_conversion, 1),
        'avg_profit_margin': round(avg_profit_margin, 1),
        'catalog_health': round(catalog_health),
        'top_products': top_products,
        'quotes_by_status': Quote.objects.values('production_status').annotate(count=Count('id')),
        'jobs_by_status': Job.objects.values('status').annotate(count=Count('id')),
    }
    return render(request, 'production_analytics.html', context)

@login_required
@group_required('Production Team')
def production_settings(request):
    """Production Team Settings"""
    context = {
        'current_view': 'production_settings',
    }
    return render(request, 'production_settings.html', context)


@login_required
@group_required('Production Team')
def self_quote(request):
    return render(request, 'self_quote.html')
# Add these updated views to your views.py file

@login_required
def notifications(request):
    """Display notifications with mark as read functionality"""
    if request.method == 'POST':
        # Mark specific notification as read
        notif_id = request.POST.get('mark_read')
        if notif_id:
            try:
                notification = Notification.objects.get(id=notif_id, recipient=request.user)
                notification.is_read = True
                notification.save()
                messages.success(request, 'Notification marked as read')
            except Notification.DoesNotExist:
                pass
        else:
            # Mark all as read
            Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
            messages.success(request, 'All notifications marked as read')
        
        return redirect('notifications')
    
    # GET request - show notifications
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')
    
    context = {
        'current_view': 'notifications',
        'notifications': notifications,
    }
    
    return render(request, 'notifications.html', context)


def permission_denied_view(request, *args, **kwargs):
    messages.warning(request, "You don't have access to that section.")
    fallback = 'dashboard'
    if request.user.groups.filter(name='Production Team').exists():
        fallback = 'production2_dashboard'
    return redirect(reverse(fallback))
def login_redirect(request):
    """
    Custom login redirect view that sends users to appropriate dashboard based on their group
    NOTE: This view should NOT have @login_required decorator
    """
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return redirect('login')
    
    user = request.user
    
    # Superusers go to admin
    if user.is_superuser or user.is_staff:
        return redirect('admin_dashboard_index')
    
    # Check groups and redirect accordingly
    if user.groups.filter(name='Production Team').exists():
        return redirect('production2_dashboard')
    elif user.groups.filter(name='Account Manager').exists():
        return redirect('dashboard')
    else:
        # User has no recognized group - show friendly error page instead of redirect loop
        from django.shortcuts import render
        return render(request, 'no_group_error.html', {
            'user': user,
            'message': 'Your account is not assigned to any group. Please contact the administrator to assign you to either "Account Manager" or "Production Team" group.'
        })

from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

def ajax_get_product_image(request, image_id):
    """AJAX endpoint to get product image data"""
    try:
        image = ProductImage.objects.get(id=image_id)
        return JsonResponse({
            'success': True,
            'image_url': image.image.url,
            'file_name': image.image.name.split('/')[-1],
            'file_size': f"{image.image.size / 1024:.1f} KB" if hasattr(image.image, 'size') else 'Unknown',
            'dimensions': 'Unknown',  # You'd need to get actual dimensions
            'alt_text': image.alt_text or '',
            'caption': image.caption or '',
            'image_type': image.image_type or 'product-photo'
        })
    except ProductImage.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Image not found'}, status=404)

@require_POST
def ajax_update_product_image(request, image_id):
    """AJAX endpoint to update product image metadata"""
    try:
        image = ProductImage.objects.get(id=image_id)
        data = json.loads(request.body)
        
        image.alt_text = data.get('alt_text', '')
        image.caption = data.get('caption', '')
        image.image_type = data.get('image_type', 'product-photo')
        image.save()
        
        return JsonResponse({'success': True})
    except ProductImage.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Image not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_POST
def ajax_delete_product_image(request, image_id):
    """AJAX endpoint to delete product image"""
    try:
        image = ProductImage.objects.get(id=image_id)
        image.delete()
        return JsonResponse({'success': True})
    except ProductImage.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Image not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_POST
def ajax_replace_product_image(request, image_id):
    """AJAX endpoint to replace product image"""
    try:
        image = ProductImage.objects.get(id=image_id)
        
        if 'image' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No image file provided'}, status=400)
        
        # Delete old file
        if image.image:
            image.image.delete(save=False)
        
        # Save new file
        image.image = request.FILES['image']
        image.save()
        
        return JsonResponse({
            'success': True,
            'new_image_url': image.image.url
        })
    except ProductImage.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Image not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

        
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

# Add finance decorator after group_required:
def finance_required(view_func):
    """Require Finance group membership"""
    return group_required('Finance')(view_func)

# Add finance dashboard view before login_redirect:


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


# ========== LPO MANAGEMENT VIEWS ==========

@login_required
@group_required('Production Team')
def lpo_list(request):
    """List all LPOs for production team"""
    from clientapp.models import LPO
    
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    sync_filter = request.GET.get('sync', 'all')
    search_query = request.GET.get('search', '').strip()
    
    lpos = LPO.objects.select_related('client', 'quote').order_by('-created_at')
    
    # Apply filters
    if status_filter != 'all':
        lpos = lpos.filter(status=status_filter)
    
    if sync_filter == 'synced':
        lpos = lpos.filter(synced_to_quickbooks=True)
    elif sync_filter == 'not_synced':
        lpos = lpos.filter(synced_to_quickbooks=False)
    
    if search_query:
        lpos = lpos.filter(
            Q(lpo_number__icontains=search_query) |
            Q(client__name__icontains=search_query) |
            Q(client__company__icontains=search_query) |
            Q(quote__quote_id__icontains=search_query)
        )
    
    # Count by status
    status_counts = {
        'all': LPO.objects.count(),
        'pending': LPO.objects.filter(status='pending').count(),
        'approved': LPO.objects.filter(status='approved').count(),
        'in_production': LPO.objects.filter(status='in_production').count(),
        'completed': LPO.objects.filter(status='completed').count(),
        'synced': LPO.objects.filter(synced_to_quickbooks=True).count(),
        'not_synced': LPO.objects.filter(synced_to_quickbooks=False, status='completed').count(),
    }
    
    context = {
        'current_view': 'lpo_list',
        'lpos': lpos,
        'status_filter': status_filter,
        'sync_filter': sync_filter,
        'search_query': search_query,
        'status_counts': status_counts,
    }
    
    return render(request, 'lpo_list.html', context)


@login_required
def lpo_detail(request, lpo_number):
    """View LPO details"""
    from clientapp.models import LPO
    
    lpo = get_object_or_404(LPO, lpo_number=lpo_number)
    
    # Check permissions
    is_am = request.user.groups.filter(name='Account Manager').exists()
    is_production = request.user.groups.filter(name='Production Team').exists()
    
    if not (is_am or is_production or request.user.is_superuser):
        messages.error(request, "You don't have permission to view this LPO")
        return redirect('dashboard')
    
    # Get related job
    job = None
    job_completed = False
    if hasattr(lpo.quote, 'job'):
        job = lpo.quote.job
        job_completed = job.status == 'completed'
    
    # Allow sync when: user is production team, not already synced, and (LPO is completed OR job is completed)
    can_sync = (is_production or is_am) and not lpo.synced_to_quickbooks and (lpo.status == 'completed' or job_completed)
    
    context = {
        'lpo': lpo,
        'quote': lpo.quote,
        'job': job,
        'line_items': lpo.line_items.all(),
        'can_sync': can_sync,
        'current_view': 'lpo_detail',
    }
    
    return render(request, 'lpo_detail.html', context)


@login_required
@group_required('Production Team')
def sync_to_quickbooks(request, lpo_number):
    """Sync LPO to QuickBooks when production is complete"""
    if request.method == 'POST':
        try:
            from clientapp.models import LPO
            
            lpo = get_object_or_404(LPO, lpo_number=lpo_number)
            
            # Check if already synced
            if lpo.synced_to_quickbooks:
                return JsonResponse({
                    'success': False,
                    'message': 'LPO already synced to QuickBooks'
                })
            
            # Check if production is complete (either LPO status or related job)
            job_completed = False
            if hasattr(lpo.quote, 'job') and lpo.quote.job:
                job_completed = lpo.quote.job.status == 'completed'
            
            if lpo.status != 'completed' and not job_completed:
                return JsonResponse({
                    'success': False,
                    'message': 'Production must be completed before syncing to QuickBooks'
                })
            
            # Sync to QuickBooks
            result = lpo.sync_to_quickbooks(request.user)
            
            if result['success']:
                messages.success(request, result['message'])
            
            return JsonResponse(result)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })


@login_required
@group_required('Production Team')
def complete_job(request, pk):
    """Mark job as completed and update LPO status"""
    if request.method == 'POST':
        try:
            job = get_object_or_404(Job, pk=pk)
            
            # Update job status
            job.status = 'completed'
            job.actual_completion = timezone.now().date()
            job.save()
            
            # Update LPO status if exists
            if hasattr(job.quote, 'lpo'):
                lpo = job.quote.lpo
                lpo.status = 'completed'
                lpo.save()
                
                # Create notification for AM to sync to QuickBooks
                if job.client.account_manager:
                    Notification.objects.create(
                        recipient=job.client.account_manager,
                        title=f'Job {job.job_number} Completed',
                        message=f'Job {job.job_number} is complete. LPO {lpo.lpo_number} ready to sync to QuickBooks.',
                        link=reverse('lpo_detail', kwargs={'lpo_number': lpo.lpo_number})
                    )
            
            # Create activity log
            ActivityLog.objects.create(
                client=job.client,
                activity_type='Order',
                title=f'Job {job.job_number} Completed',
                description=f'Production completed for {job.job_name}',
                created_by=request.user
            )
            
            messages.success(request, f'Job {job.job_number} marked as completed!')
            return redirect('job_detail', pk=job.pk)
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('job_detail', pk=pk)
    
    return redirect('job_detail', pk=pk)


@login_required
@group_required('Account Manager')
@login_required
@group_required('Account Manager')
def send_quote(request, quote_id):
    """Send quote to client/lead via email"""
    if request.method == 'POST':
        from .quote_approval_services import QuoteApprovalService
        
        try:
            quote = Quote.objects.filter(quote_id=quote_id).first()
            if not quote:
                return JsonResponse({
                    'success': False,
                    'message': 'Quote not found'
                })
            
            send_method = request.POST.get('send_method', 'email')
            
            if send_method == 'email':
                result = QuoteApprovalService.send_quote_via_email(quote, request)
            elif send_method == 'whatsapp':
                result = QuoteApprovalService.send_quote_via_whatsapp(quote)
            else:
                result = {
                    'success': False,
                    'message': 'Invalid send method'
                }
            
            if result['success']:
                # Create activity log
                if quote.client:
                    ActivityLog.objects.create(
                        client=quote.client,
                        activity_type='Quote',
                        title=f"Quote {quote.quote_id} Sent",
                        description=f"Quote sent via {send_method} to {quote.client.email if quote.client else quote.lead.email}",
                        related_quote=quote,
                        created_by=request.user
                    )
            
            return JsonResponse(result)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

from clientapp.quote_approval_services import QuoteApprovalService
def quote_approval(request, token):
    """
    Public view for quote approval (no login required)
    Client clicks link from email
    GET: Display quote details with approve/request discount options
    POST: Handle approval or price reduction request
    """
    if request.method == 'GET':
        # Display quote details
        result = QuoteApprovalService.get_quote_from_token(token)
        
        if not result['success']:
            from django.http import HttpResponse
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to get quote from token: {token[:20]}..., error: {result.get('message', 'Unknown error')}")
            
            error_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Approval Failed</title>
                <script src="https://cdn.tailwindcss.com"></script>
            </head>
            <body class="bg-gray-50">
                <div class="min-h-screen flex items-center justify-center px-4">
                    <div class="bg-white rounded-lg shadow-lg p-8 max-w-md text-center">
                        <div class="text-6xl mb-4">❌</div>
                        <h1 class="text-2xl font-bold text-gray-900 mb-4">Approval Failed</h1>
                        <p class="text-gray-600 mb-6">{result['message']}</p>
                        <p class="text-sm text-gray-500 mb-4">Please contact us at info@printduka.com for assistance.</p>
                        <p class="text-xs text-gray-400">If you received this link via email, please check that you're using the complete link from the email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            return HttpResponse(error_html)
        
        # Render quote approval page
        quote = result['quote']
        quote_items = result['quote_items']
        totals = result['totals']
        
        context = {
            'quote': quote,
            'quote_items': quote_items,
            'subtotal': totals['subtotal'],
            'vat_amount': totals['vat_amount'],
            'total_amount': totals['total_amount'],
            'total': totals['total_amount'],
            'token': token,
            'token_valid': result['token_valid'],
            'token_used': result['token_used'],
        }
        
        return render(request, 'quote_approval.html', context)
    
    elif request.method == 'POST':
        # Handle approval or price reduction request
        action = request.POST.get('action', 'approve')
        
        if action == 'approve':
            # Call the service to approve the quote
            result = QuoteApprovalService.approve_quote(token)
        elif action == 'request_discount':
            # Handle price reduction request
            discount_notes = request.POST.get('discount_notes', '')
            if not discount_notes:
                from django.http import HttpResponse
                error_html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Request Failed</title>
                    <script src="https://cdn.tailwindcss.com"></script>
                </head>
                <body class="bg-gray-50">
                    <div class="min-h-screen flex items-center justify-center px-4">
                        <div class="bg-white rounded-lg shadow-lg p-8 max-w-md text-center">
                            <div class="text-6xl mb-4">⚠️</div>
                            <h1 class="text-2xl font-bold text-gray-900 mb-4">Request Failed</h1>
                            <p class="text-gray-600 mb-6">Please provide details about your price reduction request.</p>
                            <a href="javascript:history.back()" class="text-blue-600 hover:underline">Go Back</a>
                        </div>
                    </div>
                </body>
                </html>
                """
                return HttpResponse(error_html)
            
            result = QuoteApprovalService.request_price_reduction(token, discount_notes)
        elif action == 'request_adjustment':
            # Handle quote adjustment request
            adjustment_notes = request.POST.get('adjustment_notes', '')
            if not adjustment_notes:
                from django.http import HttpResponse
                error_html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Request Failed</title>
                    <script src="https://cdn.tailwindcss.com"></script>
                </head>
                <body class="bg-gray-50">
                    <div class="min-h-screen flex items-center justify-center px-4">
                        <div class="bg-white rounded-lg shadow-lg p-8 max-w-md text-center">
                            <div class="text-6xl mb-4">⚠️</div>
                            <h1 class="text-2xl font-bold text-gray-900 mb-4">Request Failed</h1>
                            <p class="text-gray-600 mb-6">Please provide details about the adjustments you need.</p>
                            <a href="javascript:history.back()" class="text-blue-600 hover:underline">Go Back</a>
                        </div>
                    </div>
                </body>
                </html>
                """
                return HttpResponse(error_html)
            
            result = QuoteApprovalService.request_quote_adjustment(token, adjustment_notes)
        else:
            result = {'success': False, 'message': 'Invalid action'}
        
        if not result['success']:
            # Approval failed
            from django.http import HttpResponse
            error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Approval Failed</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                }}
                .container {{
                    background: white;
                    padding: 3rem;
                    border-radius: 1rem;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    text-align: center;
                    max-width: 500px;
                }}
                .error-icon {{
                    font-size: 4rem;
                    color: #ef4444;
                    margin-bottom: 1rem;
                }}
                h1 {{
                    color: #1f2937;
                    margin-bottom: 1rem;
                }}
                p {{
                    color: #6b7280;
                    font-size: 1.1rem;
                    line-height: 1.6;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error-icon">❌</div>
                <h1>Approval Failed</h1>
                <p>{result['message']}</p>
                <p style="margin-top: 2rem; font-size: 0.9rem; color: #9ca3af;">
                    Please contact us if you need assistance.
                </p>
            </div>
        </body>
        </html>
            """
            return HttpResponse(error_html)
        
        # Success! Handle different action results
        if action == 'approve':
            # Approval success
            quote = result['quote']
            lpo = result.get('lpo')
            job = result.get('job')
            
            # Return success page
            from django.http import HttpResponse
            success_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Quote Approved</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .container {{
                background: white;
                padding: 3rem;
                border-radius: 1rem;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                text-align: center;
                max-width: 600px;
            }}
            .success-icon {{
                font-size: 4rem;
                color: #10b981;
                margin-bottom: 1rem;
            }}
            h1 {{
                color: #1f2937;
                margin-bottom: 1rem;
            }}
            p {{
                color: #6b7280;
                font-size: 1.1rem;
                line-height: 1.6;
            }}
            .quote-id {{
                background: #f3f4f6;
                padding: 0.5rem 1rem;
                border-radius: 0.5rem;
                font-family: monospace;
                color: #4f46e5;
                font-weight: bold;
                margin: 1rem 0;
            }}
            .details {{
                background: #f9fafb;
                padding: 1.5rem;
                border-radius: 0.5rem;
                margin: 1.5rem 0;
                text-align: left;
            }}
            .detail-row {{
                display: flex;
                justify-content: space-between;
                padding: 0.5rem 0;
                border-bottom: 1px solid #e5e7eb;
            }}
            .detail-row:last-child {{
                border-bottom: none;
            }}
            .detail-label {{
                font-weight: 600;
                color: #4b5563;
            }}
            .detail-value {{
                color: #1f2937;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success-icon">✅</div>
            <h1>Quote Approved Successfully!</h1>
            <p class="quote-id">{quote.quote_id}</p>
            
            <div class="details">
                <div class="detail-row">
                    <span class="detail-label">LPO Number:</span>
                    <span class="detail-value">{lpo.lpo_number if lpo else 'Generated'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Job Number:</span>
                    <span class="detail-value">{job.job_number if job else 'Created'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Product:</span>
                    <span class="detail-value">{quote.product_name}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Quantity:</span>
                    <span class="detail-value">{quote.quantity}</span>
                </div>
            </div>
            
            <p>Thank you for approving your quote! We have:</p>
            <ul style="text-align: left; color: #4b5563; line-height: 2;">
                <li>✅ Generated your Local Purchase Order (LPO)</li>
                <li>✅ Created a production job</li>
                <li>✅ Notified our production team</li>
            </ul>
            
            <p style="margin-top: 2rem;">
                Our production team will begin work on your order shortly. 
                You'll receive updates on the progress.
            </p>
            
            <p style="margin-top: 2rem; font-size: 0.9rem; color: #9ca3af;">
                You can now close this window.
            </p>
        </div>
    </body>
    </html>
    """
    
            return HttpResponse(success_html)
        elif action == 'request_discount':
            # Price reduction request success
            from django.http import HttpResponse
            discount_success_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Request Submitted</title>
                <script src="https://cdn.tailwindcss.com"></script>
            </head>
            <body class="bg-gray-50">
                <div class="min-h-screen flex items-center justify-center px-4">
                    <div class="bg-white rounded-lg shadow-lg p-8 max-w-md text-center">
                        <div class="text-6xl mb-4">✅</div>
                        <h1 class="text-2xl font-bold text-gray-900 mb-4">Request Submitted</h1>
                        <p class="text-gray-600 mb-6">{result['message']}</p>
                        <p class="text-sm text-gray-500">We will review your request and get back to you shortly.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            return HttpResponse(discount_success_html)
        elif action == 'request_adjustment':
            # Quote adjustment request success
            from django.http import HttpResponse
            adjustment_success_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Request Submitted</title>
                <script src="https://cdn.tailwindcss.com"></script>
            </head>
            <body class="bg-gray-50">
                <div class="min-h-screen flex items-center justify-center px-4">
                    <div class="bg-white rounded-lg shadow-lg p-8 max-w-md text-center">
                        <div class="text-6xl mb-4">✅</div>
                        <h1 class="text-2xl font-bold text-gray-900 mb-4">Request Submitted</h1>
                        <p class="text-gray-600 mb-6">{result['message']}</p>
                        <p class="text-sm text-gray-500">We will review your request and send you an updated quote shortly.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            return HttpResponse(adjustment_success_html)



# ===== PRODUCT CATALOG VIEWS =====
"""
Complete Product Management Views
Handles all product creation and editing with multi-tab interface
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.utils.text import slugify
from decimal import Decimal
import decimal
import json

from .models import (
    Product, ProductCategory, ProductSubCategory, ProductFamily,
    ProductTag, Vendor, ProductPricing, ProductVariable,
    ProductVariableOption, ProductImage, ProductVideo,
    ProductDownloadableFile, ProductSEO, ProductReviewSettings,
    ProductFAQ, ProductShipping, ProductLegal, ProductProduction,
    ProductChangeHistory, ActivityLog,
    # NEW: Process integration imports
    Process, ProcessVariable, ProcessTier,
    # Delivery handoff models
    QCInspection, Delivery
)

from .product_forms import (
    ProductGeneralInfoForm, ProductPricingForm, ProductSEOForm,
    ProductShippingForm, ProductLegalForm, ProductProductionForm
)

from django.db import models

def group_required_production(group_name):
    """Decorator to require Production Team group membership"""
    def decorator(view_func):
        def wrapped(request, *args, **kwargs):
            if not request.user.groups.filter(name=group_name).exists():
                messages.error(request, "You don't have permission to access this page.")
                return redirect('production2_dashboard')
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


@login_required
@group_required('Production Team')
def product_catalog(request):
    """List all products - Production Team view"""
    
    search = request.GET.get('search', '').strip()
    category = request.GET.get('category', 'all')
    status = request.GET.get('status', 'all')
    
    products = Product.objects.all()
    
    # Apply filters
    if search:
        products = products.filter(
            models.Q(name__icontains=search) | 
            models.Q(internal_code__icontains=search)
        )
    
    if category != 'all':
        products = products.filter(primary_category__slug=category)
    
    if status != 'all':
        products = products.filter(status=status)
    
    # Get categories for filter dropdown
    categories = ProductCategory.objects.all().order_by('name')
    
    context = {
        'current_view': 'production_catalog',
        'products': products.order_by('-created_at'),
        'categories': categories,
        'search': search,
        'selected_category': category,
        'selected_status': status,
    }
    
    return render(request, 'product_catalog.html', context)



def _get_product_form_context(product, general_form=None):
    """Build context for product create/edit form"""
    from clientapp.product_forms import ProductGeneralInfoForm
    
    if general_form is None:
        if product:
            general_form = ProductGeneralInfoForm(instance=product)
        else:
            general_form = ProductGeneralInfoForm()
    
    # Get processes for pricing integration
    processes = Process.objects.filter(status='active').order_by('process_name')
    
    # Get vendors
    vendors = Vendor.objects.filter(is_active=True).order_by('name')
    
    # Prepare existing variables JSON for editing
    existing_variables_json = '[]'
    if product and hasattr(product, 'variables'):
        try:
            variables_list = list(product.variables.all().values(
                'id', 'name', 'variable_type', 'options', 'default_value', 
                'is_required', 'affects_pricing', 'order'
            ))
            existing_variables_json = json.dumps(variables_list)
        except:
            existing_variables_json = '[]'
    
    context = {
        'current_view': 'production_catalog',
        'product': product,
        'is_edit': product is not None,
        'general_form': general_form,
        'pricing_form': ProductPricingForm(instance=product.pricing if product and hasattr(product, 'pricing') else None),
        'seo_form': ProductSEOForm(instance=product.seo if product and hasattr(product, 'seo') else None),
        'shipping_form': ProductShippingForm(instance=product.shipping if product and hasattr(product, 'shipping') else None),
        'legal_form': ProductLegalForm(instance=product.legal if product and hasattr(product, 'legal') else None),
        'production_form': ProductProductionForm(instance=product.production if product and hasattr(product, 'production') else None),
        'processes': processes,
        'vendors': vendors,
        'existing_variables_json': existing_variables_json,
        'primary_image': product.images.filter(is_primary=True).first() if product else None,
        'existing_images': product.images.filter(is_primary=False).order_by('display_order') if product else [],
        'categories': ProductCategory.objects.all().order_by('name'),
        'subcategories': ProductSubCategory.objects.all().order_by('name'),
        'families': ProductFamily.objects.all().order_by('name'),
        'all_tags': ProductTag.objects.all().order_by('name'),
        'history': product.change_history.all().order_by('-changed_at') if product else [],
    }
    
    return context


# Duplicate function removed - using the complete version at line 4954

# Duplicate function removed - using the complete version at line 5095


# Duplicate function removed - using the complete version at line 5277
    
    # Review Settings
    review_settings, created = ProductReviewSettings.objects.get_or_create(product=product)
    review_settings.enable_reviews = request.POST.get('enable_reviews') == 'on'
    review_settings.require_purchase = request.POST.get('require_purchase') == 'on'
    review_settings.auto_approve_reviews = request.POST.get('auto_approve_reviews') == 'on'
    review_settings.review_reminder = request.POST.get('review_reminder', '7')
    review_settings.save()
    
    # FAQs - Delete existing and create new
    product.faqs.all().delete()
    
    faq_questions = request.POST.getlist('faq_question[]')
    faq_answers = request.POST.getlist('faq_answer[]')
    
    for idx, question in enumerate(faq_questions):
        if question.strip() and idx < len(faq_answers) and faq_answers[idx].strip():
            ProductFAQ.objects.create(
                product=product,
                question=question.strip(),
                answer=faq_answers[idx].strip(),
                display_order=idx,
                is_active=True
            )


def _handle_shipping_tab(request, product):
    """Handle shipping tab"""
    from clientapp.product_forms import ProductShippingForm
    
    # Get or create shipping instance
    shipping, created = ProductShipping.objects.get_or_create(product=product)
    
    shipping_form = ProductShippingForm(request.POST, instance=shipping)
    if shipping_form.is_valid():
        shipping = shipping_form.save(commit=False)
        shipping.product = product
        shipping.save()
    else:
        # Fallback
        shipping.shipping_weight = Decimal(request.POST.get('shipping_weight', '0') or '0')
        shipping.shipping_weight_unit = request.POST.get('shipping_weight_unit', 'kg')
        shipping.save()


def _handle_legal_tab(request, product):
    """Handle legal tab"""
    from clientapp.product_forms import ProductLegalForm
    
    # Get or create legal instance
    legal, created = ProductLegal.objects.get_or_create(product=product)
    
    legal_form = ProductLegalForm(request.POST, instance=legal)
    if legal_form.is_valid():
        legal = legal_form.save(commit=False)
        legal.product = product
        legal.save()


def _handle_production_tab(request, product):
    """Handle production tab - COMPLETE VERSION"""
    from clientapp.product_forms import ProductProductionForm
    
    # Get or create production instance
    production, created = ProductProduction.objects.get_or_create(product=product)
    
    production_form = ProductProductionForm(request.POST, instance=production)
    if production_form.is_valid():
        production = production_form.save(commit=False)
        production.product = product
        production.save()
    else:
        # Fallback to manual saving if form fails for some reason
        production.production_method_detail = request.POST.get('production_method_detail', '')
        production.machine_equipment = request.POST.get('machine_equipment', '')
        production.checklist_artwork = request.POST.get('checklist_artwork') == 'on'
        production.checklist_preflight = request.POST.get('checklist_preflight') == 'on'
        production.checklist_material = request.POST.get('checklist_material') == 'on'
        production.checklist_proofs = request.POST.get('checklist_proofs') == 'on'
        production.save()

# ==================== PRODUCT MANAGEMENT VIEWS ====================
# Complete product creation and editing with all tabs
from django.utils.text import slugify
from django.urls import reverse
import json
from decimal import Decimal

@login_required
@group_required('Production Team')
@transaction.atomic
def product_create(request):
    """Create new product - Multi-tab form"""
    
    if request.method == 'POST':
        try:
            action = request.POST.get('action', 'save_draft')
            next_tab = request.POST.get('next_tab', '')
            
            # TAB 1: GENERAL INFO
            # Create a filtered POST data dict without base_price (it's handled in pricing tab)
            # QueryDict needs special handling - create a new dict excluding base_price
            from django.http import QueryDict
            general_post_data = QueryDict(mutable=True)
            for key in request.POST.keys():
                if key != 'base_price':  # Exclude base_price - handled in pricing tab
                    values = request.POST.getlist(key)
                    for value in values:
                        general_post_data.appendlist(key, value)
            
            try:
                general_form = ProductGeneralInfoForm(general_post_data)
            except (KeyError, AttributeError, ValueError) as e:
                # If error is about base_price, try again with filtered data
                error_str = str(e).lower()
                if 'base_price' in error_str or 'no field named' in error_str:
                    # Create a completely clean QueryDict without base_price
                    from django.http import QueryDict
                    clean_data = QueryDict(mutable=True)
                    for key in request.POST.keys():
                        if key != 'base_price':
                            values = request.POST.getlist(key)
                            for value in values:
                                clean_data.appendlist(key, value)
                    general_form = ProductGeneralInfoForm(clean_data)
                else:
                    raise
            except Exception as e:
                # Log the error for debugging
                import traceback
                print(f"Unexpected error in ProductGeneralInfoForm: {e}")
                print(traceback.format_exc())
                raise
            
            if not general_form.is_valid():
                messages.error(request, 'Please correct the errors in General Info tab')
                for field, errors in general_form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                context = _get_product_form_context(None, general_form=general_form)
                return render(request, 'product_create_edit.html', context)
            
            product = general_form.save(commit=False)
            product.created_by = request.user
            product.updated_by = request.user
            
            # Set customization_level from form (if not already set by form)
            customization_level = request.POST.get('customization_level', 'non_customizable')
            if customization_level:
                product.customization_level = customization_level
            
            # Set status based on action
            if action == 'publish':
                product.status = 'published'
            else:
                product.status = 'draft'
            
            # Save product first (skip validation since base_price will be set in pricing tab)
            # We need the product ID before we can save related objects
            product.save(skip_validation=True)
            general_form.save_m2m()
            
            # Handle dynamic tags
            tag_names = request.POST.getlist('new_tag[]')
            for tag_name in tag_names:
                tag_name = tag_name.strip()
                if tag_name:
                    tag_slug = slugify(tag_name)
                    tag, created = ProductTag.objects.get_or_create(
                        slug=tag_slug,
                        defaults={'name': tag_name}
                    )
                    product.tags.add(tag)
            
            # Handle custom unit
            if product.unit_of_measure == 'other':
                custom_unit = request.POST.get('unit_of_measure_custom', '').strip()
                if custom_unit:
                    product.unit_of_measure_custom = custom_unit
                    product.save()
            
            # Handle all tabs (this will set base_price properly)
            try:
                _handle_pricing_tab(request, product)
            except Exception as e:
                messages.warning(request, f'Error saving pricing: {str(e)}')
            
            try:
                _handle_images_tab(request, product)
            except Exception as e:
                messages.warning(request, f'Error saving images: {str(e)}')
            
            try:
                _handle_seo_tab(request, product)
            except Exception as e:
                messages.warning(request, f'Error saving SEO: {str(e)}')
            
            try:
                _handle_shipping_tab(request, product)
            except Exception as e:
                messages.warning(request, f'Error saving shipping: {str(e)}')
            
            try:
                _handle_legal_tab(request, product)
            except Exception as e:
                messages.warning(request, f'Error saving legal: {str(e)}')
            
            try:
                _handle_production_tab(request, product)
            except Exception as e:
                messages.warning(request, f'Error saving production: {str(e)}')
            
            # Now that all tabs are handled, save again with full validation
            try:
                product.full_clean()  # Validate with proper base_price
                product.save()  # Save with validation
            except ValidationError as e:
                # If validation fails, show errors
                if action == 'publish':
                    product.status = 'draft'
                    product.save(skip_validation=True)
                for field, errors in e.error_dict.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                context = _get_product_form_context(product)
                return render(request, 'product_create_edit.html', context)
            
            # Validate product before publishing
            if action == 'publish':
                # Additional validation for costing processes
                can_publish, error_msg = product.can_be_published()
                if not can_publish:
                    messages.error(request, f'Cannot publish product: {error_msg}')
                    product.status = 'draft'
                    product.save(skip_validation=True)
                    context = _get_product_form_context(product)
                    return render(request, 'product_create_edit.html', context)
            
            # Create history
            ProductChangeHistory.objects.create(
                product=product,
                changed_by=request.user,
                change_type='created',
                notes=f'Product created with status: {product.status}'
            )
            
            # Success message
            if action == 'publish':
                messages.success(request, f'✓ Product "{product.name}" ({product.internal_code}) published successfully!')
            else:
                messages.success(request, f'✓ Product "{product.name}" ({product.internal_code}) saved as draft!')
            
            # Redirect based on next_tab or action
            if next_tab and action != 'publish':
                return redirect(f"{reverse('product_edit', kwargs={'pk': product.pk})}?tab={next_tab}")
            elif action == 'publish':
                # After publish, go to catalog
                return redirect('production_catalog')
            else:
                return redirect('product_edit', pk=product.pk)
            
        except Exception as e:
            messages.error(request, f'Error creating product: {str(e)}')
            import traceback
            traceback.print_exc()
            context = _get_product_form_context(None)
            return render(request, 'product_create_edit.html', context)
    
    # GET request
    context = _get_product_form_context(None)
    return render(request, 'product_create_edit.html', context)


@login_required
@group_required('Production Team')
@transaction.atomic
def product_edit(request, pk):
    """Edit existing product - Multi-tab form"""
    
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        try:
            action = request.POST.get('action', 'save_draft')
            next_tab = request.POST.get('next_tab', '')
            
            # Update general info
            # Create a filtered POST data dict without base_price (it's handled in pricing tab)
            # QueryDict needs special handling - create a new dict excluding base_price
            from django.http import QueryDict
            general_post_data = QueryDict(mutable=True)
            for key in request.POST.keys():
                if key != 'base_price':  # Exclude base_price - handled in pricing tab
                    values = request.POST.getlist(key)
                    for value in values:
                        general_post_data.appendlist(key, value)
            
            try:
                general_form = ProductGeneralInfoForm(general_post_data, instance=product)
            except Exception as e:
                # If error is about base_price, create form without data and add error manually
                if 'base_price' in str(e).lower():
                    general_form = ProductGeneralInfoForm(instance=product)
                    messages.warning(request, 'Note: base_price is handled in Pricing & Variables tab')
                else:
                    raise
            
            if not general_form.is_valid():
                messages.error(request, 'Please correct the errors in General Info tab')
                for field, errors in general_form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                context = _get_product_form_context(product, general_form=general_form)
                return render(request, 'product_create_edit.html', context)
            
            product = general_form.save(commit=False)
            product.updated_by = request.user
            
            # Update customization_level from form
            customization_level = request.POST.get('customization_level', 'non_customizable')
            if customization_level:
                product.customization_level = customization_level
            
            # Update status if publishing
            if action == 'publish':
                old_status = product.status
                product.status = 'published'
                if old_status != 'published':
                    ProductChangeHistory.objects.create(
                        product=product,
                        changed_by=request.user,
                        change_type='published',
                        field_changed='status',
                        old_value=old_status,
                        new_value='published'
                    )
            
            # Save product first (skip validation since base_price will be set in pricing tab)
            product.save(skip_validation=True)
            general_form.save_m2m()
            
            # Handle dynamic tags
            product.tags.clear()
            tag_names = request.POST.getlist('new_tag[]')
            for tag_name in tag_names:
                tag_name = tag_name.strip()
                if tag_name:
                    tag, created = ProductTag.objects.get_or_create(
                        name=tag_name,
                        defaults={'slug': slugify(tag_name)}
                    )
                    product.tags.add(tag)
            
            # Handle custom unit
            if product.unit_of_measure == 'other':
                custom_unit = request.POST.get('unit_of_measure_custom', '').strip()
                if custom_unit:
                    product.unit_of_measure_custom = custom_unit
                    product.save(skip_validation=True)
            
            # Update all tabs (this will set base_price properly)
            try:
                _handle_pricing_tab(request, product)
            except Exception as e:
                messages.warning(request, f'Error saving pricing: {str(e)}')
            
            try:
                _handle_images_tab(request, product)
            except Exception as e:
                messages.warning(request, f'Error saving images: {str(e)}')
            
            try:
                _handle_seo_tab(request, product)
            except Exception as e:
                messages.warning(request, f'Error saving SEO: {str(e)}')
            
            try:
                _handle_shipping_tab(request, product)
            except Exception as e:
                messages.warning(request, f'Error saving shipping: {str(e)}')
            
            try:
                _handle_legal_tab(request, product)
            except Exception as e:
                messages.warning(request, f'Error saving legal: {str(e)}')
            
            try:
                _handle_production_tab(request, product)
            except Exception as e:
                messages.warning(request, f'Error saving production: {str(e)}')
            
            # Now that all tabs are handled, save again with full validation
            try:
                product.full_clean()  # Validate with proper base_price
                product.save()  # Save with validation
            except ValidationError as e:
                # If validation fails, show errors
                if action == 'publish':
                    product.status = 'draft'
                    product.save(skip_validation=True)
                for field, errors in e.error_dict.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                context = _get_product_form_context(product)
                return render(request, 'product_create_edit.html', context)
            
            # Validate product before publishing
            if action == 'publish':
                # Additional validation for costing processes
                can_publish, error_msg = product.can_be_published()
                if not can_publish:
                    messages.error(request, f'Cannot publish product: {error_msg}')
                    product.status = 'draft'
                    product.save(skip_validation=True)
                    context = _get_product_form_context(product)
                    return render(request, 'product_create_edit.html', context)
            
            # Create change history
            ProductChangeHistory.objects.create(
                product=product,
                changed_by=request.user,
                change_type='updated',
                notes=f'Product updated - Action: {action}'
            )
            
            # Success messages
            if action == 'publish':
                messages.success(request, f'✓ Product "{product.name}" published successfully!')
                return redirect('production_catalog')
            else:
                messages.success(request, f'✓ Product "{product.name}" updated successfully!')
            
            # Redirect based on next_tab
            if next_tab:
                return redirect(f"{reverse('product_edit', kwargs={'pk': product.pk})}?tab={next_tab}")
            else:
                return redirect('product_edit', pk=product.pk)
            
        except Exception as e:
            messages.error(request, f'Error updating product: {str(e)}')
            import traceback
            traceback.print_exc()
            return redirect('product_edit', pk=product.pk)
    
    # GET request
    context = _get_product_form_context(product)
    return render(request, 'product_create_edit.html', context)


# ========== HELPER FUNCTIONS ==========

def _get_product_form_context(product, general_form=None):
    """Get context for product form"""
    
    # Existing variables JSON
    existing_variables = []
    if product:
        for var in product.variables.all():
            options = []
            for opt in var.options.all():
                options.append({
                    'value': opt.name,
                    'price_adjustment': float(opt.price_modifier),
                    'is_default': opt.is_default
                })
            existing_variables.append({
                'name': var.name,
                'display_order': var.display_order,
                'variable_type': var.variable_type,
                'pricing_type': var.pricing_type,
                'options': options
            })
    
    context = {
        'current_view': 'production_catalog',
        'general_form': general_form or ProductGeneralInfoForm(instance=product),
        'pricing_form': ProductPricingForm(instance=product.pricing if product and hasattr(product, 'pricing') else None),
        'seo_form': ProductSEOForm(instance=product.seo if product and hasattr(product, 'seo') else None),
        'shipping_form': ProductShippingForm(instance=product.shipping if product and hasattr(product, 'shipping') else None),
        'legal_form': ProductLegalForm(instance=product.legal if product and hasattr(product, 'legal') else None),
        'production_form': ProductProductionForm(instance=product.production if product and hasattr(product, 'production') else None),
        'product': product,
        'is_edit': product is not None,
        'existing_variables_json': json.dumps(existing_variables),
        'primary_image': product.images.filter(is_primary=True).first() if product else None,
        'existing_images': product.images.filter(is_primary=False).order_by('display_order') if product else [],
        'categories': ProductCategory.objects.all().order_by('name'),
        'subcategories': ProductSubCategory.objects.all().order_by('name'),
        'families': ProductFamily.objects.all().order_by('name'),
        'vendors': Vendor.objects.filter(active=True).order_by('name'),
        'all_tags': ProductTag.objects.all().order_by('name'),
        # NEW: Add processes for process selection dropdown
        'processes': Process.objects.filter(status='active').order_by('process_name'),
    }
    
    return context

def _handle_pricing_tab(request, product):
    """Handle pricing and variables tab"""
    
    # Get or create pricing instance
    pricing, created = ProductPricing.objects.get_or_create(product=product)
    
    # Save basic pricing fields
    pricing.pricing_model = request.POST.get('pricing_model', 'variable')
    
    # Base cost - ensure it's never NULL
    base_cost = request.POST.get('base_cost', '').strip()
    if not base_cost or base_cost == '':
        base_cost = '15'  # Default value matching the form
    try:
        pricing.base_cost = Decimal(base_cost)
    except (ValueError, decimal.InvalidOperation):
        pricing.base_cost = Decimal('15')
    
    # Price display format and amount
    pricing.price_display = request.POST.get('price_display', 'from')
    
    # Margins
    try:
        pricing.default_margin = Decimal(request.POST.get('default_margin', '30'))
        pricing.minimum_margin = Decimal(request.POST.get('minimum_margin', '15'))
    except:
        pricing.default_margin = Decimal('30')
        pricing.minimum_margin = Decimal('15')
    
    # Minimum order value
    try:
        pricing.minimum_order_value = Decimal(request.POST.get('minimum_order_value', '0'))
    except:
        pricing.minimum_order_value = Decimal('0')
    
    # Production & Vendor Information
    try:
        pricing.lead_time_value = int(request.POST.get('lead_time_value', '3'))
    except:
        pricing.lead_time_value = 3
    
    pricing.lead_time_unit = request.POST.get('lead_time_unit', 'days')
    pricing.production_method = request.POST.get('production_method', 'digital-offset')
    
    # Handle custom production method
    if pricing.production_method == 'other':
        custom_method = request.POST.get('production_method_custom', '').strip()
        if custom_method:
            pricing.production_method = custom_method
    
    # Primary vendor
    primary_vendor_id = request.POST.get('primary_vendor')
    if primary_vendor_id:
        try:
            pricing.primary_vendor = Vendor.objects.get(id=primary_vendor_id)
        except Vendor.DoesNotExist:
            pass
    
    # Minimum quantity
    try:
        pricing.minimum_quantity = int(request.POST.get('minimum_quantity', '1'))
    except:
        pricing.minimum_quantity = 1
    
    # Rush production
    pricing.rush_available = request.POST.get('rush_available') == 'on'
    
    if pricing.rush_available:
        try:
            pricing.rush_lead_time_value = int(request.POST.get('rush_lead_time_value', '1'))
        except:
            pricing.rush_lead_time_value = 1
        
        pricing.rush_lead_time_unit = request.POST.get('rush_lead_time_unit', 'days')
        
        try:
            pricing.rush_upcharge = Decimal(request.POST.get('rush_upcharge', '0'))
        except:
            pricing.rush_upcharge = Decimal('0')
    
    # Conditional logic and conflict detection
    pricing.enable_conditional_logic = request.POST.get('enable_conditional_logic') == 'on'
    pricing.enable_conflict_detection = request.POST.get('enable_conflict_detection') == 'on'
    
    # Handle tier and formula processes
    tier_process_id = request.POST.get('tier_process', '').strip()
    if tier_process_id:
        try:
            pricing.tier_process = Process.objects.get(id=tier_process_id)
        except Process.DoesNotExist:
            pass
    else:
        pricing.tier_process = None
    
    formula_process_id = request.POST.get('formula_process', '').strip()
    if formula_process_id:
        try:
            pricing.formula_process = Process.objects.get(id=formula_process_id)
        except Process.DoesNotExist:
            pass
    else:
        pricing.formula_process = None
    
    pricing.save()
    
    # Handle Product.base_price based on customization_level
    customization_level = product.customization_level
    base_price_str = request.POST.get('base_price', '').strip()
    
    if customization_level == 'non_customizable':
        # Non-customizable: base_price is REQUIRED
        if not base_price_str:
            # Calculate from base_cost + margin if base_price not provided
            if pricing.base_cost and pricing.return_margin:
                margin = pricing.return_margin / Decimal('100')
                product.base_price = pricing.base_cost * (Decimal('1') + margin)
            else:
                # Use default calculation
                product.base_price = pricing.base_cost * Decimal('1.30')  # 30% default margin
        else:
            try:
                product.base_price = Decimal(base_price_str)
            except (ValueError, decimal.InvalidOperation):
                # Fallback to calculated price
                if pricing.base_cost and pricing.return_margin:
                    margin = pricing.return_margin / Decimal('100')
                    product.base_price = pricing.base_cost * (Decimal('1') + margin)
                else:
                    product.base_price = pricing.base_cost * Decimal('1.30')
    elif customization_level == 'semi_customizable':
        # Semi-customizable: base_price is REQUIRED
        if not base_price_str:
            # Calculate from base_cost + margin if base_price not provided
            if pricing.base_cost and pricing.return_margin:
                margin = pricing.return_margin / Decimal('100')
                product.base_price = pricing.base_cost * (Decimal('1') + margin)
            else:
                product.base_price = pricing.base_cost * Decimal('1.30')
        else:
            try:
                product.base_price = Decimal(base_price_str)
            except (ValueError, decimal.InvalidOperation):
                if pricing.base_cost and pricing.return_margin:
                    margin = pricing.return_margin / Decimal('100')
                    product.base_price = pricing.base_cost * (Decimal('1') + margin)
                else:
                    product.base_price = pricing.base_cost * Decimal('1.30')
    else:  # fully_customizable
        # Fully customizable: base_price must be NULL
        product.base_price = None
    
    product.save(update_fields=['base_price'])
    
    # Handle alternative vendors (many-to-many)
    alt_vendor_ids = request.POST.getlist('alternative_vendors')
    pricing.alternative_vendors.clear()
    for vendor_id in alt_vendor_ids:
        try:
            vendor = Vendor.objects.get(id=vendor_id)
            pricing.alternative_vendors.add(vendor)
        except Vendor.DoesNotExist:
            pass
    
    # Check minimum margin trigger - send notification to admin
    if pricing.default_margin < pricing.minimum_margin:
        from django.contrib.auth.models import User
        admins = User.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                title=f'Margin Approval Required - {product.name}',
                message=f'Product margin ({pricing.default_margin}%) is below minimum ({pricing.minimum_margin}%). Approval required.',
                link=reverse('product_edit', kwargs={'pk': product.pk})
            )
    
    # Handle Product Variables
    variables_json = request.POST.get('product_variables_json')
    if variables_json:
        try:
            # Delete existing variables
            product.variables.all().delete()
            
            # Create new variables
            variables_data = json.loads(variables_json)
            for idx, var_data in enumerate(variables_data):
                variable = ProductVariable.objects.create(
                    product=product,
                    name=var_data.get('name', f'Variable {idx+1}'),
                    display_order=var_data.get('display_order', idx),
                    variable_type=var_data.get('variable_type', 'required'),
                    pricing_type=var_data.get('pricing_type', 'fixed'),
                    is_active=True
                )
                
                for opt_idx, opt_data in enumerate(var_data.get('options', [])):
                    ProductVariableOption.objects.create(
                        variable=variable,
                        name=opt_data.get('value', f'Option {opt_idx+1}'),
                        display_order=opt_idx,
                        is_default=opt_data.get('is_default', False),
                        price_modifier=Decimal(str(opt_data.get('price_adjustment', 0))),
                        is_active=True
                    )
        except json.JSONDecodeError as e:
            messages.warning(request, f"Error processing variables: {str(e)}")

# Add this to your views.py - Update the _handle_images_tab function

def _handle_images_tab(request, product):
    """Handle images and media tab - COMPLETE WORKING VERSION"""
    
    # ===== PRIMARY IMAGE =====
    primary_image = request.FILES.get('primary_image')
    if primary_image:
        # Validate file
        if not primary_image.content_type.startswith('image/'):
            messages.warning(request, 'Primary image must be an image file')
        elif primary_image.size > 2 * 1024 * 1024:  # 2MB limit
            messages.warning(request, 'Primary image must be less than 2MB')
        else:
            # Remove old primary
            ProductImage.objects.filter(product=product, is_primary=True).delete()
            # Create new primary
            ProductImage.objects.create(
                product=product,
                image=primary_image,
                alt_text=request.POST.get('primary_image_alt', product.name),
                is_primary=True,
                display_order=0,
                image_type='product-photo'
            )
    
    # ===== GALLERY IMAGES =====
    gallery_images = request.FILES.getlist('gallery_images')
    if gallery_images:
        # Get max display order
        max_order = product.images.aggregate(
            models.Max('display_order')
        )['display_order__max'] or 0
        
        for idx, img_file in enumerate(gallery_images, start=1):
            # Validate file
            if not img_file.content_type.startswith('image/'):
                continue
            if img_file.size > 2 * 1024 * 1024:
                messages.warning(request, f'{img_file.name} is too large (max 2MB)')
                continue
            
            ProductImage.objects.create(
                product=product,
                image=img_file,
                alt_text=f"{product.name} - Image {max_order + idx}",
                is_primary=False,
                display_order=max_order + idx,
                image_type='product-photo'
            )
    
    # ===== HANDLE IMAGE DELETIONS =====
    delete_image_ids = request.POST.getlist('delete_images[]')
    if delete_image_ids:
        ProductImage.objects.filter(
            product=product,
            id__in=delete_image_ids,
            is_primary=False  # Don't allow deleting primary via this method
        ).delete()
    
    # ===== PRODUCT VIDEOS =====
    # Update existing videos
    for video in product.videos.all():
        video_url = request.POST.get(f'video_url_{video.pk}', '').strip()
        if video_url:
            video.video_url = video_url
            video.video_type = request.POST.get(f'video_type_{video.pk}', 'demo')
            
            # Handle thumbnail update
            thumbnail = request.FILES.get(f'video_thumbnail_{video.pk}')
            if thumbnail:
                video.thumbnail = thumbnail
            
            video.save()
    
    # Add new videos
    new_video_urls = request.POST.getlist('new_video_url[]')
    new_video_types = request.POST.getlist('new_video_type[]')
    new_video_thumbnails = request.FILES.getlist('new_video_thumbnail[]')
    
    for idx, url in enumerate(new_video_urls):
        if url.strip():
            video_data = {
                'product': product,
                'video_url': url.strip(),
                'video_type': new_video_types[idx] if idx < len(new_video_types) else 'demo',
                'display_order': product.videos.count() + idx
            }
            
            # Add thumbnail if provided
            if idx < len(new_video_thumbnails):
                video_data['thumbnail'] = new_video_thumbnails[idx]
            
            ProductVideo.objects.create(**video_data)
    
    # ===== DOWNLOADABLE FILES =====
    # Update existing files
    for file_obj in product.downloadable_files.all():
        file_name = request.POST.get(f'file_name_{file_obj.pk}', '').strip()
        if file_name:
            file_obj.file_name = file_name
            file_obj.file_type = request.POST.get(f'file_type_{file_obj.pk}', file_obj.file_type)
            file_obj.description = request.POST.get(f'file_desc_{file_obj.pk}', '')
            file_obj.save()
    
    # Add new files
    new_files = request.FILES.getlist('new_downloadable_files')
    new_file_names = request.POST.getlist('new_file_name[]')
    new_file_types = request.POST.getlist('new_file_type[]')
    new_file_descriptions = request.POST.getlist('new_file_description[]')
    
    for idx, file in enumerate(new_files):
        # Validate file size (max 10MB)
        if file.size > 10 * 1024 * 1024:
            messages.warning(request, f'{file.name} is too large (max 10MB)')
            continue
        
        # Get file extension
        file_ext = file.name.split('.')[-1].lower()
        
        # Map extension to file type
        file_type_map = {
            'ai': 'illustrator',
            'pdf': 'pdf',
            'psd': 'psd',
            'indd': 'indd',
            'zip': 'zip'
        }
        file_type = new_file_types[idx] if idx < len(new_file_types) else file_type_map.get(file_ext, 'pdf')
        file_name = new_file_names[idx] if idx < len(new_file_names) and new_file_names[idx].strip() else file.name
        file_desc = new_file_descriptions[idx] if idx < len(new_file_descriptions) else ''
        
        ProductDownloadableFile.objects.create(
            product=product,
            file_name=file_name,
            file=file,
            file_type=file_type,
            description=file_desc,
            file_size=file.size,
            display_order=product.downloadable_files.count() + idx
        )

@login_required
@group_required('Production Team')
def product_update_image_metadata(request, image_pk):
    """Update image metadata via AJAX"""
    if request.method == 'POST':
        try:
            image = get_object_or_404(ProductImage, pk=image_pk)
            
            image.alt_text = request.POST.get('alt_text', image.alt_text)
            image.caption = request.POST.get('caption', '')
            image.image_type = request.POST.get('image_type', image.image_type)
            
            # Handle variable associations if provided
            var_id = request.POST.get('associated_variable')
            opt_id = request.POST.get('associated_option')
            
            if var_id:
                try:
                    image.associated_variable_id = int(var_id)
                except (ValueError, TypeError):
                    pass
            
            if opt_id:
                try:
                    image.associated_option_id = int(opt_id)
                except (ValueError, TypeError):
                    pass
            
            image.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Image updated successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def _handle_seo_tab(request, product):
    """Handle SEO and e-commerce tab - COMPLETE VERSION"""
    
    # Get or create SEO instance
    seo, created = ProductSEO.objects.get_or_create(product=product)
    
    # Basic SEO fields
    seo.meta_title = request.POST.get('meta_title', '')[:60]
    seo.meta_description = request.POST.get('meta_description', '')[:160]
    seo.focus_keyword = request.POST.get('focus_keyword', '')
    seo.additional_keywords = request.POST.get('additional_keywords', '')
    
    # Slug handling
    seo.auto_generate_slug = request.POST.get('auto_generate_slug') == 'on'
    if seo.auto_generate_slug or not seo.slug:
        seo.slug = slugify(product.name)
    else:
        seo.slug = slugify(request.POST.get('slug', product.name))
    
    # Display settings
    seo.show_price = request.POST.get('show_price') == 'on'
    seo.price_display_format = request.POST.get('price_display_format', 'from')
    seo.show_stock_status = request.POST.get('show_stock_status', 'in-stock-only')
    
    seo.save()
    
    # Handle related products (many-to-many)
    related_product_ids = request.POST.getlist('related_products')
    seo.related_products.clear()
    for prod_id in related_product_ids:
        try:
            related_prod = Product.objects.get(id=prod_id)
            seo.related_products.add(related_prod)
        except Product.DoesNotExist:
            pass
    
    # Handle upsell products
    upsell_product_ids = request.POST.getlist('upsell_products')
    seo.upsell_products.clear()
    for prod_id in upsell_product_ids:
        try:
            upsell_prod = Product.objects.get(id=prod_id)
            seo.upsell_products.add(upsell_prod)
        except Product.DoesNotExist:
            pass
    
    # Handle frequently bought together
    bundle_product_ids = request.POST.getlist('frequently_bought_together')
    seo.frequently_bought_together.clear()
    for prod_id in bundle_product_ids:
        try:
            bundle_prod = Product.objects.get(id=prod_id)
            seo.frequently_bought_together.add(bundle_prod)
        except Product.DoesNotExist:
            pass
    
    # Review Settings
    review_settings, created = ProductReviewSettings.objects.get_or_create(product=product)
    review_settings.enable_reviews = request.POST.get('enable_reviews') == 'on'
    review_settings.require_purchase = request.POST.get('require_purchase') == 'on'
    review_settings.auto_approve_reviews = request.POST.get('auto_approve_reviews') == 'on'
    review_settings.review_reminder = request.POST.get('review_reminder', '7')
    review_settings.save()
    
    # FAQs - Delete existing and create new
    product.faqs.all().delete()
    
    faq_questions = request.POST.getlist('faq_question[]')
    faq_answers = request.POST.getlist('faq_answer[]')
    
    for idx, question in enumerate(faq_questions):
        if question.strip() and idx < len(faq_answers) and faq_answers[idx].strip():
            ProductFAQ.objects.create(
                product=product,
                question=question.strip(),
                answer=faq_answers[idx].strip(),
                display_order=idx,
                is_active=True
            )


def _handle_production_tab(request, product):
    """Handle production tab - COMPLETE VERSION"""
    
    # Get or create production instance
    production, created = ProductProduction.objects.get_or_create(product=product)
    
    # Production specifications
    production.production_method_detail = request.POST.get('production_method_detail', '')
    production.machine_equipment = request.POST.get('machine_equipment', '')
    
    # Additional production fields (add these to your ProductProduction model if not present)
    # For now, we'll store in production_notes as JSON
    production_data = {
        'print_layout': request.POST.get('print_layout', ''),
        'color_profile': request.POST.get('color_profile', ''),
        'finishing': {
            'lamination': request.POST.get('finishing_lamination') == 'on',
            'packaging': request.POST.get('finishing_packaging') == 'on',
            'die_cutting': request.POST.get('finishing_die_cutting') == 'on',
            'embossing': request.POST.get('finishing_embossing') == 'on',
            'registration': request.POST.get('finishing_registration') == 'on',
            'cutting_accuracy': request.POST.get('finishing_cutting_accuracy') == 'on',
        },
        'quality_control': {
            'color_match': request.POST.get('qc_color_match') == 'on',
            'finish_quality': request.POST.get('qc_finish_quality') == 'on',
            'registration': request.POST.get('qc_registration') == 'on',
            'cutting': request.POST.get('qc_cutting') == 'on',
        },
        'bom': {
            'material1': {
                'type': request.POST.get('bom_mat1_type', ''),
                'sheet_size': request.POST.get('bom_mat1_sheet_size', ''),
                'quantity': request.POST.get('bom_mat1_quantity', ''),
                'supplier': request.POST.get('bom_mat1_supplier', ''),
                'cost_per': request.POST.get('bom_mat1_cost_per', '0'),
            },
            'material2': {
                'type': request.POST.get('bom_mat2_type', ''),
                'width': request.POST.get('bom_mat2_width', ''),
                'length': request.POST.get('bom_mat2_length', ''),
                'supplier': request.POST.get('bom_mat2_supplier', ''),
                'cost_per': request.POST.get('bom_mat2_cost_per', '0'),
            },
            'material3': {
                'type': request.POST.get('bom_mat3_type', ''),
                'coverage': request.POST.get('bom_mat3_coverage', ''),
                'estimated': request.POST.get('bom_mat3_estimated', ''),
            }
        },
        'special_instructions': request.POST.get('production_special_instructions', ''),
    }
    
    # Store as JSON in production_notes
    import json
    production.production_notes = json.dumps(production_data, indent=2)
    
    # Pre-Production Checklist
    production.checklist_artwork = request.POST.get('checklist_artwork') == 'on'
    production.checklist_preflight = request.POST.get('checklist_preflight') == 'on'
    production.checklist_material = request.POST.get('checklist_material') == 'on'
    production.checklist_proofs = request.POST.get('checklist_proofs') == 'on'
    
    production.save()

def _handle_shipping_tab(request, product):
    """Handle shipping tab"""
    
    shipping_form = ProductShippingForm(
        request.POST,
        instance=product.shipping if hasattr(product, 'shipping') else None
    )
    
    if shipping_form.is_valid():
        shipping = shipping_form.save(commit=False)
        shipping.product = product
        shipping.save()


def _handle_legal_tab(request, product):
    """Handle legal tab"""
    
    legal_form = ProductLegalForm(
        request.POST,
        instance=product.legal if hasattr(product, 'legal') else None
    )
    
    if legal_form.is_valid():
        legal = legal_form.save(commit=False)
        legal.product = product
        legal.save()


# ========== AJAX ENDPOINTS ==========

@login_required
@group_required('Production Team')
def product_delete_image(request, product_pk, image_pk):
    """Delete product image via AJAX"""
    
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, pk=product_pk)
            image = get_object_or_404(ProductImage, pk=image_pk, product=product)
            
            if image.is_primary:
                return JsonResponse({
                    'success': False,
                    'message': 'Cannot delete primary image. Upload a new primary image first.'
                })
            
            image.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Image deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@group_required('Production Team')
def calculate_pricing(request):
    """Calculate pricing breakdown via AJAX"""
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            quantity = int(data.get('quantity', 1))
            base_price = Decimal(str(data.get('base_price', 0)))
            margin = Decimal(str(data.get('margin', 30)))
            
            # Get selected variable options
            variable_costs = Decimal('0')
            for var_option in data.get('variable_options', []):
                variable_costs += Decimal(str(var_option.get('price_adjustment', 0)))
            
            # Calculate
            unit_cost = base_price + variable_costs
            subtotal_evp = unit_cost * quantity
            margin_amount = subtotal_evp * (margin / 100)
            customer_pays = subtotal_evp + margin_amount
            per_unit = customer_pays / quantity if quantity > 0 else Decimal('0')
            
            return JsonResponse({
                'success': True,
                'breakdown': {
                    'base_cost': float(base_price * quantity),
                    'variable_costs': float(variable_costs * quantity),
                    'subtotal_evp': float(subtotal_evp),
                    'margin_percentage': float(margin),
                    'margin_amount': float(margin_amount),
                    'customer_pays': float(customer_pays),
                    'per_unit': float(per_unit)
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

# ========== ADMIN DASHBOARD AJAX ENDPOINTS ==========

@login_required
def dismiss_alert(request, alert_id):
    """Dismiss a system alert"""
    if request.method == 'POST':
        try:
            from .models import SystemAlert
            alert = get_object_or_404(SystemAlert, id=alert_id)
            alert.dismiss(request.user)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid method'})


@login_required
def export_dashboard_report(request, report_type):
    """Export dashboard reports to CSV"""
    import csv
    from django.http import HttpResponse
    from datetime import datetime
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="report_{report_type}_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    if report_type == 'products':
        from .admin_dashboard import get_top_selling_products
        products = get_top_selling_products(limit=50)
        
        writer.writerow(['Rank', 'Product Name', 'Total Revenue', 'Total Quantity', 'Order Count'])
        for idx, product in enumerate(products, 1):
            writer.writerow([
                idx,
                product['product_name'],
                product['total_revenue'],
                product['total_quantity'],
                product['order_count']
            ])
    
    elif report_type == 'margins':
        from .admin_dashboard import get_profit_margin_data
        margins = get_profit_margin_data()
        
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Revenue', margins.get('total_revenue', 0)])
        writer.writerow(['Total Cost', margins.get('total_cost', 0)])
        writer.writerow(['Overall Margin %', margins.get('overall_margin', 0)])
    
    return response


# Views for the 4 HTML templates

from django.shortcuts import render
from django.contrib.auth.decorators import login_required



@login_required
def quote_detail2(request, quote_id):
    """Display detailed quote information with REAL data"""
    
    # Get all line items for this quote
    quote_items = Quote.objects.filter(quote_id=quote_id).select_related('client', 'lead', 'created_by')
    
    if not quote_items.exists():
        messages.error(request, f'Quote {quote_id} not found')
        return redirect('my_quotes')
    
    first_quote = quote_items.first()
    
    # Calculate totals
    subtotal = sum(item.unit_price * item.quantity for item in quote_items)
    vat_amount = subtotal * Decimal('0.16') if first_quote.include_vat else Decimal('0')
    total_amount = subtotal + vat_amount
    
    # Determine client
    if first_quote.client:
        client = first_quote.client
        client_name = client.name
        client_email = client.email
        client_phone = client.phone
    elif first_quote.lead:
        client_name = first_quote.lead.name
        client_email = first_quote.lead.email
        client_phone = first_quote.lead.phone
        client = None
    else:
        client_name = "Unknown"
        client_email = "-"
        client_phone = "-"
        client = None
    
    # Calculate progress
    completed_items = sum(1 for item in quote_items if item.production_status == 'completed')
    in_progress_items = sum(1 for item in quote_items if item.production_status == 'in_progress')
    pending_items = sum(1 for item in quote_items if item.production_status == 'pending')
    
    total_items = quote_items.count()
    progress_percentage = int((completed_items / total_items) * 100) if total_items > 0 else 0
    
    # Days remaining
    days_remaining = (first_quote.valid_until - timezone.now().date()).days
    
    # Timeline events
    timeline_events = [
        {
            'title': 'Quote Created',
            'date': first_quote.created_at,
            'completed': True
        },
    ]
    
    if first_quote.production_status in ['costed', 'sent_to_client', 'in_production', 'completed']:
        timeline_events.append({
            'title': 'Costing Completed',
            'date': first_quote.updated_at,
            'completed': True
        })
    
    if first_quote.status == 'Approved':
        timeline_events.append({
            'title': 'Client Approved',
            'date': first_quote.approved_at or first_quote.updated_at,
            'completed': True
        })
    
    context = {
        'current_view': 'quote_detail',
        'quote_id': quote_id,
        'first_quote': first_quote,
        'quote_items': quote_items,
        'client_name': client_name,
        'client_email': client_email,
        'client_phone': client_phone,
        'client': client,
        'account_manager': first_quote.created_by,
        'subtotal': subtotal,
        'vat_amount': vat_amount,
        'total_amount': total_amount,
        'progress_percentage': progress_percentage,
        'completed_items': completed_items,
        'in_progress_items': in_progress_items,
        'pending_items': pending_items,
        'days_remaining': days_remaining,
        'timeline_events': timeline_events,
    }
    
    return render(request, 'quote_detail2.html', context)


from django.views.decorators.http import require_POST

@login_required
@group_required('Production Team')
def quote_action(request, quote_id):
    """Handle PT actions on quotes: Approve or Reject"""
    if request.method == 'POST':
        action = request.POST.get('action')
        quotes = Quote.objects.filter(quote_id=quote_id)
        
        if not quotes.exists():
            messages.error(request, 'Quote not found')
            return redirect('my_quotes')
        
        first_quote = quotes.first()
        
        if action == 'approve':
            # Approve quote for sending to client
            quotes.update(
                production_status='approved',
                status='Ready to Send',
                costed_by=request.user
                # Removed costed_at - field doesn't exist
            )
            
            # Notify the AM who created it
            Notification.objects.create(
                recipient=first_quote.created_by,
                notification_type='quote_pt_approved',
                title=f'✅ Quote {quote_id} Approved by PT',
                message=f'You can now send this quote to the client!',
                link=f'/create/quote?quote_id={quote_id}',
                related_quote_id=quote_id,
                action_url=f'/create/quote?quote_id={quote_id}',
                action_label='Send to Client'
            )
            
            messages.success(request, f'✅ Quote {quote_id} approved!')
            
        elif action == 'reject':
            reason = request.POST.get('reason', 'No reason provided')
            
            # Reject quote
            quotes.update(
                production_status='rejected',
                status='Rejected',
                production_notes=reason
            )
            
            # Notify the AM
            Notification.objects.create(
                recipient=first_quote.created_by,
                notification_type='quote_pt_rejected',
                title=f'❌ Quote {quote_id} Rejected by PT',
                message=f'Reason: {reason}',
                link=f'/create/quote?quote_id={quote_id}',
                related_quote_id=quote_id
            )
            
            messages.warning(request, f'Quote {quote_id} rejected')
        
        return redirect('my_quotes')
    
    # GET request - shouldn't happen
    messages.error(request, 'Invalid request')
    return redirect('my_quotes')

# ========== MY JOBS - UPDATED ==========
@login_required
@group_required('Production Team')
def my_jobs(request):
    """Show jobs for production team"""
    
    # Get all jobs
    jobs = Job.objects.select_related('client').order_by('-created_at')
    
    # Apply filters
    status_filter = request.GET.get('status', '')
    if status_filter:
        jobs = jobs.filter(status=status_filter)
    
    search_query = request.GET.get('search', '').strip()
    if search_query:
        jobs = jobs.filter(
            Q(job_number__icontains=search_query) |
            Q(client__name__icontains=search_query) |
            Q(product__icontains=search_query)
        )
    
    # Prepare jobs data
    today = timezone.now().date()
    jobs_list = []
    
    for job in jobs:
        # Determine status class
        days_until_deadline = (job.expected_completion - today).days
        
        if job.status == 'completed':
            status_class = 'completed'
        elif days_until_deadline < 0:
            status_class = 'urgent'
        elif days_until_deadline <= 2:
            status_class = 'urgent'
        elif job.status == 'in_progress':
            status_class = 'in-progress'
        else:
            status_class = 'on-track'
        
        # Calculate progress
        if job.status == 'completed':
            progress = 100
        elif job.status == 'in_progress':
            progress = 60
        elif job.status == 'pending':
            progress = 20
        else:
            progress = 0
        
        jobs_list.append({
            'id': job.id,
            'job_number': job.job_number,
            'client_name': job.client.name if job.client else 'N/A',
            'product_name': job.product,
            'quantity': job.quantity,
            'status_class': status_class,
            'status_label': job.get_status_display(),
            'deadline': job.expected_completion,
            'deadline_time': job.expected_completion.strftime("%I:%M %p") if hasattr(job.expected_completion, 'strftime') else "12:00 PM",
            'days_remaining': f"{days_until_deadline} days" if days_until_deadline > 0 else f"Overdue by {abs(days_until_deadline)} days",
            'is_overdue': days_until_deadline < 0,
            'progress': progress,
        })
    
    context = {
        'current_view': 'my_jobs',
        'jobs': jobs_list,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'my_jobs.html', context)

@login_required
@group_required('Production Team')
def my_quotes(request):
    """Show quotes for Production Team approval/costing"""
    from django.db.models import Q, Count
    
    # Get all quotes EXCEPT those that have been costed
    # Only show quotes that need costing (pending, in_progress, or completed)
    quotes = Quote.objects.select_related(
        'client', 'lead', 'created_by'
    ).exclude(
        production_status='costed'  # Hide costed quotes
    ).order_by('-created_at')
    
    # Apply filters
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'urgent':
        quotes = quotes.filter(production_status='pending', status='Draft')
    elif status_filter == 'active':
        quotes = quotes.filter(production_status='in_progress')
    elif status_filter == 'completed':
        quotes = quotes.filter(production_status='completed')
    
    search_query = request.GET.get('search', '').strip()
    if search_query:
        quotes = quotes.filter(
            Q(quote_id__icontains=search_query) |
            Q(client__name__icontains=search_query) |
            Q(lead__name__icontains=search_query) |
            Q(product_name__icontains=search_query)
        )
    
    # Calculate snapshot counts (exclude costed quotes)
    active_quotes_count = Quote.objects.filter(
        production_status__in=['pending', 'in_progress']
    ).values('quote_id').distinct().count()
    
    in_costing_count = Quote.objects.filter(
        production_status='in_progress'
    ).values('quote_id').distinct().count()
    
    awaiting_delivery_count = Quote.objects.filter(
        status='Approved',
        production_status='completed'
    ).values('quote_id').distinct().count()
    
    completed_today_count = Quote.objects.filter(
        production_status='completed',
        updated_at__date=timezone.now().date()
    ).values('quote_id').distinct().count()
    
    # Group quotes by quote_id and prepare for template
    quotes_dict = {}
    for quote in quotes:
        if quote.quote_id not in quotes_dict:
            # Determine client name
            client_name = '-'
            if quote.client:
                client_name = quote.client.name
            elif quote.lead:
                client_name = quote.lead.name
            
            # Calculate days remaining
            days_remaining = (quote.valid_until - timezone.now().date()).days
            
            quotes_dict[quote.quote_id] = {
                'id': quote.id,
                'quote_id': quote.quote_id,
                'client_name': client_name,
                'account_manager': quote.created_by.get_full_name() if quote.created_by else '-',
                'total_amount': quote.total_amount,
                'status': quote.production_status,
                'status_display': quote.get_production_status_display(),
                'created_date': quote.created_at,
                'days_remaining': days_remaining,
                'line_items': [],
            }
        
        quotes_dict[quote.quote_id]['line_items'].append({
            'product_name': quote.product_name,
            'quantity': quote.quantity,
            'status': quote.production_status,
        })
    
    quotes_list = list(quotes_dict.values())
    
    context = {
        'current_view': 'my_quotes',
        'quotes': quotes_list,
        'active_quotes_count': active_quotes_count,
        'in_costing_count': in_costing_count,
        'awaiting_delivery_count': awaiting_delivery_count,
        'completed_today_count': completed_today_count,
        'status_filter': status_filter,
        'search_query': search_query,
        'clients': Client.objects.filter(status='Active').order_by('name'),
    }
    
    return render(request, 'my_quotes.html', context)

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import Job, Vendor, VendorQuote, QCInspection
import json

@login_required
def vendor_comparison(request, job_id):
    """
    Vendor comparison page for selecting vendors.
    
    Displays all vendor quotes for a specific job with filtering options
    based on VPS score and lead time. Shows vendor details including:
    - Lead time and cost
    - VPS score and rating
    - Specialties
    - Any notices or special conditions
    """
    job = get_object_or_404(Job, id=job_id)
    
    # Get all vendor quotes for this job
    vendor_quotes = VendorQuote.objects.filter(job=job).select_related('vendor')
    
    # Search filter
    search_query = request.GET.get('search', '').strip()
    if search_query:
        vendor_quotes = vendor_quotes.filter(
            Q(vendor__name__icontains=search_query) |
            Q(vendor__specialties__name__icontains=search_query)
        ).distinct()
    
    # Filter vendors based on VPS score if specified
    vps_filter = request.GET.get('vps_score', 'all')
    if vps_filter != 'all' and vps_filter in ['A', 'B', 'C']:
        vendor_quotes = vendor_quotes.filter(vendor__vps_score=vps_filter)
    
    # Filter by lead time if specified
    lead_time_filter = request.GET.get('lead_time', 'all')
    if lead_time_filter != 'all':
        try:
            lead_time = int(lead_time_filter)
            if lead_time == 5:  # 5+ days
                vendor_quotes = vendor_quotes.filter(lead_time__gte=5)
            else:
                vendor_quotes = vendor_quotes.filter(lead_time=lead_time)
        except ValueError:
            pass
    
    context = {
        'job': job,
        'vendor_quotes': vendor_quotes,
        'total_vendors': VendorQuote.objects.filter(job=job).count(),
        'vps_filter': vps_filter,
        'lead_time_filter': lead_time_filter,
        'search_query': search_query,
    }
    
    return render(request, 'procurement/vendor_comparison.html', context)

# Add these imports at the top
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import base64

# QC Inspection View (WORKING VERSION)
@login_required
@group_required('Production Team')
def qc_inspection(request, inspection_id):
    """
    Quality control inspection page - FULLY FUNCTIONAL
    """
    inspection = get_object_or_404(
        QCInspection.objects.select_related('job', 'vendor', 'job__client', 'inspector'),
        id=inspection_id
    )
    
    job = inspection.job
    vendor = inspection.vendor
    
    # Get vendor's recent QC history
    vendor_history = QCInspection.objects.filter(
        vendor=vendor,
        status='passed'
    ).exclude(
        id=inspection.id
        ).order_by('-created_at')[:3]
    
    # Calculate vendor's average QC score
        # Calculate vendor's pass rate
    if vendor:
        total_inspections = QCInspection.objects.filter(vendor=vendor).count()
        passed_inspections = QCInspection.objects.filter(vendor=vendor, status='passed').count()
        vendor_pass_rate = (passed_inspections / total_inspections * 100) if total_inspections > 0 else 0
    else:
        vendor_pass_rate = 0
    
    # Calculate sampling requirement
    quantity = job.quantity
    if quantity < 100:
        sample_percentage = 20
    elif quantity < 1000:
        sample_percentage = 10
    elif quantity < 5000:
        sample_percentage = 10
    else:
        sample_percentage = 5
    
    required_sample = max(int(quantity * sample_percentage / 100), 1)
    
    context = {
        'current_view': 'qc_inspection',
        'inspection': inspection,
        'job': job,
        'vendor': vendor,
        'vendor_history': vendor_history,
        'vendor_pass_rate': round(vendor_pass_rate),
        'required_sample': required_sample,
        'sample_percentage': sample_percentage,
    }
    
    return render(request, 'quality_control.html', context)


@login_required
@group_required('Production Team')
@require_POST
def submit_qc(request):
    """
    AJAX endpoint to submit QC inspection results - FULLY FUNCTIONAL
    """
    try:
        data = json.loads(request.body)
        inspection_id = data.get('inspection_id')
        
        if not inspection_id:
            return JsonResponse({
                'success': False,
                'message': 'Inspection ID is required'
            }, status=400)
        
        inspection = get_object_or_404(QCInspection, id=inspection_id)
        
        # Update inspection ratings
        inspection.print_quality_score = data.get('print_quality')
        inspection.color_accuracy_score = data.get('color_accuracy')
        inspection.material_quality_score = data.get('material_quality')
        inspection.finishing_quality_score = data.get('finishing_quality')
        inspection.overall_quality_score = data.get('overall_quality')
        
        # Update notes
        inspection.print_quality_notes = data.get('print_quality_notes', '')
        inspection.color_accuracy_notes = data.get('color_accuracy_notes', '')
        inspection.material_quality_notes = data.get('material_quality_notes', '')
        inspection.finishing_quality_notes = data.get('finishing_quality_notes', '')
        inspection.overall_quality_notes = data.get('overall_quality_notes', '')
        
        inspection.delivery_notes = data.get('delivery_notes', '')
        inspection.notes_to_am = data.get('notes_to_am', '')
        
        # Delivery preparation data
        inspection.shelf_location = data.get('shelf_location', '')
        inspection.box_count = data.get('box_count', 1)
        
        # Packaging verification
        inspection.packaging_verified = {
            'all_items_packed': data.get('pack1', False),
            'job_id_label': data.get('pack2', False),
            'quantity_marked': data.get('pack3', False),
            'fragile_stickers': data.get('pack4', False),
        }
        
        # Set decision and status
        decision = data.get('decision')
        inspection.decision = decision
        inspection.status = 'completed'
        inspection.inspector = request.user
        inspection.completed_date = timezone.now()
        
        inspection.save()
        
        # Update vendor VPS score based on decision
        vendor = inspection.vendor
        if decision == 'pass':
            vendor.vps_score_value += 1.0
            messages.success(request, f'✅ QC passed! Vendor VPS +1.0')
        elif decision == 'fail':
            vendor.vps_score_value -= 2.0
            messages.warning(request, f'❌ QC failed. Vendor VPS -2.0')
        
        # Recalculate VPS letter grade
        if vendor.vps_score_value >= 8.0:
            vendor.vps_score = 'A'
        elif vendor.vps_score_value >= 5.0:
            vendor.vps_score = 'B'
        else:
            vendor.vps_score = 'C'
        
        vendor.save()
        
        # Update job status
        job = inspection.job
        if decision == 'pass':
            job.status = 'completed'
            job.actual_completion = timezone.now().date()
        elif decision == 'conditions':
            job.status = 'completed'  # Still completed but with notes
        else:  # fail
            job.status = 'on_hold'
        
        job.save()
        
        # Create notification for AM
        if job.client and job.client.account_manager:
            notification_title = {
                'pass': f'✅ Job {job.job_number} - QC Passed',
                'conditions': f'⚠️ Job {job.job_number} - QC Passed with Conditions',
                'fail': f'❌ Job {job.job_number} - QC Failed'
            }
            
            notification_message = {
                'pass': f'Quality inspection passed ({inspection.overall_score_percentage:.0f}%). Ready for delivery.',
                'conditions': f'Quality inspection passed with conditions. Review notes before delivery.',
                'fail': f'Quality inspection failed. Vendor must rework. Check inspection notes.'
            }
            
            Notification.objects.create(
                recipient=job.client.account_manager,
                notification_type='job_completed' if decision != 'fail' else 'general',
                title=notification_title[decision],
                message=notification_message[decision],
                link=reverse('job_detail', kwargs={'pk': job.pk}),
                related_job=job,
                action_url=reverse('delivery_handoff', kwargs={'job_id': job.id}) if decision == 'pass' else None,
                action_label='Prepare Delivery' if decision == 'pass' else None
            )
        
        # Create activity log
        if job.client:
            ActivityLog.objects.create(
                client=job.client,
                activity_type='Order',
                title=f'QC Inspection Completed - {job.job_number}',
                description=f'QC Decision: {decision.upper()}. Score: {inspection.overall_score_percentage:.0f}%',
                created_by=request.user
            )
        
        logger.info(f'QC inspection {inspection.reference_number} completed by {request.user.username}')
        
        return JsonResponse({
            'success': True,
            'message': 'QC inspection submitted successfully',
            'decision': decision,
            'score': inspection.overall_score_percentage
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f'Error submitting QC: {str(e)}')
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


# Delivery Handoff View (WORKING VERSION)
@login_required
@group_required('Production Team')
def delivery_handoff(request, job_id):
    """
    Delivery handoff page - FULLY FUNCTIONAL
    """
    job = get_object_or_404(Job.objects.select_related('client', 'quote'), id=job_id)
    
    # Get QC inspection if exists
    qc_inspection = QCInspection.objects.filter(job=job).order_by('-created_at').first()
    
    # Check if delivery already exists
    delivery = Delivery.objects.filter(job=job).first()
    
    # Calculate costs
    locked_evp = job.quote.production_cost if job.quote else Decimal('0')
    actual_cost = locked_evp  # You can update this based on actual vendor invoice
    
    # Add VAT
    locked_evp_with_vat = locked_evp * Decimal('1.16')
    actual_cost_with_vat = actual_cost * Decimal('1.16')
    
    context = {
        'current_view': 'delivery',
        'job': job,
        'qc_inspection': qc_inspection,
        'delivery': delivery,
        'locked_evp': locked_evp_with_vat,
        'actual_cost': actual_cost_with_vat,
        'variance': actual_cost_with_vat - locked_evp_with_vat,
        'variance_percentage': ((actual_cost_with_vat - locked_evp_with_vat) / locked_evp_with_vat * 100) if locked_evp_with_vat > 0 else 0,
    }
    
    return render(request, 'delivery.html', context)


@login_required
@group_required('Production Team')
@require_POST
def submit_delivery_handoff(request):
    """
    AJAX endpoint to complete delivery handoff - FULLY FUNCTIONAL
    """
    try:
        data = json.loads(request.body)
        job_id = data.get('job_id')
        
        if not job_id:
            return JsonResponse({
                'success': False,
                'message': 'Job ID is required'
            }, status=400)
        
        job = get_object_or_404(Job, id=job_id)
        
        # Get or create delivery
        delivery, created = Delivery.objects.get_or_create(
            job=job,
            defaults={
                'created_by': request.user
            }
        )
        
        # Update delivery details
        delivery.staging_location = data.get('staging_location', 'shelf-b')
        delivery.notes_to_am = data.get('notes_to_am', '')
        
        # Packaging verification
        delivery.packaging_verified = {
            'boxes_sealed': data.get('boxes_sealed', False),
            'job_labels': data.get('job_labels', False),
            'quantity_marked': data.get('quantity_marked', False),
            'total_quantity': data.get('total_quantity', False),
            'fragile_stickers': data.get('fragile_stickers', False),
        }
        
        # Costs
        delivery.locked_evp = Decimal(str(data.get('locked_evp', 0)))
        delivery.actual_cost = Decimal(str(data.get('actual_cost', 0)))
        
        # Handoff confirmation
        delivery.handoff_confirmed = True
        delivery.handoff_confirmed_at = timezone.now()
        delivery.handoff_confirmed_by = request.user
        
        # Notification settings
        delivery.notify_am = data.get('notify_am', True)
        delivery.notify_via_email = data.get('notify_via_email', True)
        delivery.mark_urgent = data.get('mark_urgent', False)
        
        # Status
        delivery.status = 'staged'
        
        delivery.save()
        
        # Update job status
        job.status = 'completed'
        job.actual_completion = timezone.now().date()
        job.save()
        
        # Notify Account Manager
        if job.client and job.client.account_manager and delivery.notify_am:
            Notification.objects.create(
                recipient=job.client.account_manager,
                notification_type='delivery_ready',
                title=f'📦 Job {job.job_number} Ready for Delivery',
                message=f'Staged at {delivery.get_staging_location_display()}. {delivery.notes_to_am[:100]}',
                link=reverse('job_detail', kwargs={'pk': job.pk}),
                related_job=job,
                action_url=reverse('job_detail', kwargs={'pk': job.pk}),
                action_label='View Job Details'
            )
            
            # Send email if requested
            if delivery.notify_via_email:
                try:
                    from django.core.mail import send_mail
                    send_mail(
                        subject=f'Job {job.job_number} Ready for Delivery',
                        message=f'Job {job.job_number} has been completed and is ready for delivery.\n\nLocation: {delivery.get_staging_location_display()}\n\nNotes: {delivery.notes_to_am}',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[job.client.account_manager.email],
                        fail_silently=True
                    )
                except Exception as e:
                    logger.warning(f'Failed to send delivery email: {str(e)}')
        
        # Create activity log
        if job.client:
            ActivityLog.objects.create(
                client=job.client,
                activity_type='Order',
                title=f'Delivery Handoff Complete - {job.job_number}',
                description=f'Job handed off to AM. Staged at {delivery.get_staging_location_display()}',
                created_by=request.user
            )
        
        logger.info(f'Delivery for {job.job_number} handed off by {request.user.username}')
        
        return JsonResponse({
            'success': True,
            'message': 'Delivery handoff completed successfully',
            'delivery_id': delivery.id,
            'job_number': job.job_number
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f'Error submitting delivery handoff: {str(e)}')
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


# Delivery List View
@login_required
def delivery_list(request):
    """Display list of all deliveries"""
    
    # Check user permissions
    is_production = request.user.groups.filter(name='Production Team').exists()
    is_am = request.user.groups.filter(name='Account Manager').exists()
    
    if is_production:
        # PT sees all deliveries
        deliveries = Delivery.objects.all()
    elif is_am:
        # AM sees only their client deliveries
        deliveries = Delivery.objects.filter(job__client__account_manager=request.user)
    else:
        deliveries = Delivery.objects.none()
    
    # Filter by status
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        deliveries = deliveries.filter(status=status_filter)
    
    # Search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        deliveries = deliveries.filter(
            Q(delivery_number__icontains=search_query) |
            Q(job__job_number__icontains=search_query) |
            Q(job__client__name__icontains=search_query)
        )
    
    deliveries = deliveries.select_related('job', 'job__client', 'qc_inspection').order_by('-created_at')
    
    context = {
        'current_view': 'deliveries',
        'deliveries': deliveries,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'delivery_list.html', context)


@login_required
@require_POST
def select_vendor(request):
    """
    AJAX endpoint to select a vendor and continue to PO creation.
    
    Updates the vendor quote as selected and sets the job's vendor.
    Returns success status and redirect URL.
    """
    try:
        data = json.loads(request.body)
        vendor_quote_id = data.get('vendor_quote_id')
        
        if not vendor_quote_id:
            return JsonResponse({
                'success': False,
                'message': 'Vendor quote ID is required'
            }, status=400)
        
        vendor_quote = get_object_or_404(VendorQuote, id=vendor_quote_id)
        
        # Mark this quote as selected
        vendor_quote.selected = True
        vendor_quote.save()
        
        # Unselect other quotes for this job
        VendorQuote.objects.filter(
            job=vendor_quote.job
        ).exclude(
            id=vendor_quote_id
        ).update(selected=False)
        
        # Update job status and selected vendor
        job = vendor_quote.job
        job.status = 'vendor_selected'
        job.selected_vendor = vendor_quote.vendor
        job.selected_vendor_quote = vendor_quote
        job.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Vendor selected successfully',
            'redirect_url': f'/procurement/purchase-order/{job.id}/'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
def quality_control_list(request):
    """List of QC Inspections"""
    inspections = QCInspection.objects.all().order_by('-created_at')
    return render(request, 'quality_control.html', {'inspections': inspections})

@login_required
def vendor_profile(request, vendor_id):
    """Detailed vendor profile page showing all vendor information."""
    vendor = get_object_or_404(Vendor, id=vendor_id)
    
    # Get vendor's jobs/quotes
    vendor_quotes = VendorQuote.objects.filter(vendor=vendor).select_related('job')
    job_stages = vendor.job_stages.all().select_related('job')
    
    # Statistics
    total_jobs = vendor_quotes.count()
    completed_jobs = vendor_quotes.filter(job__status='Completed').count()
    
    context = {
        'vendor': vendor,
        'vendor_quotes': vendor_quotes,
        'job_stages': job_stages,
        'total_jobs': total_jobs,
        'completed_jobs': completed_jobs,
        'current_view': 'vendor_profile',
    }
    
    return render(request, 'vendor_profile.html', context)

@login_required
def vendor_list(request):
    """Vendor management page - list all vendors and their process links."""
    from clientapp.models import Process
    
    vendors = Vendor.objects.all().order_by('-vps_score_value', 'name')
    
    # Get all active processes for the services section
    processes = Process.objects.filter(status='active').order_by('process_name')
    
    process_links = (
        ProcessVendor.objects.select_related('process')
        .values(
            'vendor_name',
            'vendor_id',
            'process__process_id',
            'process__process_name',
            'minimum_order',
            'standard_lead_time',
            'rush_lead_time',
        )
        .order_by('vendor_name', 'process__process_name')
    )
    
    context = {
        'current_view': 'vendor_list',
        'vendors': vendors,
        'processes': processes,
        'process_links': process_links,
    }
    return render(request, 'vendors_list.html', context)





# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from .models import Process, ProcessTier, ProcessVariable, ProcessVendor, Vendor, VendorTierPricing


def process_list(request):
    """Display list of all processes with filtering"""
    processes = Process.objects.all()  # Show all processes (active, draft, inactive)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        processes = processes.filter(
            Q(process_name__icontains=search_query) |  # ✅ NEW: process_name
            Q(process_id__icontains=search_query)
        )
    
    # Filter by category
    category = request.GET.get('category')
    if category:
        processes = processes.filter(category=category)
    
    # Filter by pricing type
    pricing_type = request.GET.get('pricing_type')  # ✅ NEW: pricing_type
    if pricing_type:
        processes = processes.filter(pricing_type=pricing_type)  # ✅ NEW
    
    # Count by type
    total_processes = processes.count()
    tier_based_count = processes.filter(pricing_type='tier').count()
    formula_based_count = processes.filter(pricing_type='formula').count()
    outsourced_count = processes.filter(category='outsourced').count()
    in_house_count = processes.filter(category='in_house').count()
    
    context = {
        'processes': processes,
        'search_query': search_query,
        'total_processes': total_processes,
        'tier_based_count': tier_based_count,
        'formula_based_count': formula_based_count,
        'outsourced_count': outsourced_count,
        'in_house_count': in_house_count,
    }
    
    return render(request, 'process_list.html', context)



@login_required
def process_create(request):
    """
    Screen 2: Process Editor - Create new process
    Handles both GET (show form) and POST (save data)
    """
    if request.method == 'POST':
        return handle_process_save(request, process=None)

    vendors = Vendor.objects.filter(active=True).order_by('name')
    
    # GET request - show empty form
    context = {
        'mode': 'create',
        'process': None,
        'vendors': vendors
    }
    return render(request, 'process_create.html', context)


@login_required
def process_edit(request, process_id):
    """Edit existing process"""
    process = get_object_or_404(Process, process_id=process_id)
    
    if request.method == 'POST':
        return handle_process_save(request, process=process)
    
    # GET request - show form with existing data
    available_vendors = Vendor.objects.filter(active=True).order_by('name')
    context = {
        'mode': 'edit',
        'process': process,
        'tiers': list(process.tiers.all().values()),
        'variables': list(process.variables.all().values()),
        # Choices for the vendor dropdowns
        'vendors': available_vendors,
        # Existing vendor links for this process (can be used to pre-populate cards)
        'process_vendors': process.process_vendors.all(),
    }
    return render(request, 'process_create.html', context)


@transaction.atomic

def handle_process_save(request, process=None):
    """
    Handle POST data for creating/updating a process
    This is the core function that processes the form submission
    """
    import logging
    from decimal import Decimal
    
    logger = logging.getLogger(__name__)
    
    data = request.POST
    action = data.get('action', 'draft')  # 'draft' or 'activate'

    # Create or update main process
    if process is None:
        process = Process()
        process.created_by = request.user

    # Update basic fields
    process.process_name = data.get('process_name')
    process.description = data.get('description', '')
    process.category = data.get('category')
    process.standard_lead_time = int(data.get('standard_lead_time', 5))

    # Pricing method
    pricing_method = data.get('pricing_method', 'tier')

    if pricing_method == 'formula':
        process.pricing_type = 'formula'
        process.unit_of_measure = None
    else:
        process.pricing_type = 'tier'
        process.unit_of_measure = data.get('unit_of_measure', 'per_piece')

    # Approval settings
    process.approval_type = data.get('approval_settings', 'auto_approve')

    # Status
    process.status = 'active' if action == 'activate' else 'draft'

    process.save()

    # ===== SAVE TIER-BASED PRICING =====
    if process.pricing_type == 'tier':
        process.tiers.all().delete()

        tier_num = 1
        while f'tier{tier_num}_from' in data:
            ProcessTier.objects.create(
                process=process,
                tier_number=tier_num,
                quantity_from=int(data.get(f'tier{tier_num}_from', 0)),
                quantity_to=int(data.get(f'tier{tier_num}_to', 0)),
                price=float(data.get(f'tier{tier_num}_price', 0)),
                cost=float(data.get(f'tier{tier_num}_cost', 0)),
            )
            tier_num += 1

    # ===== SAVE FORMULA-BASED PRICING =====
    if process.pricing_type == 'formula':
        process.variables.all().delete()

        base_cost = data.get('base_cost', 0)
        if base_cost:
            process.base_cost = Decimal(str(base_cost))
        process.save()

        var_num = 1
        while f'variable{var_num}_name' in data:
            var_name = data.get(f'variable{var_num}_name', '').strip()

            if var_name:
                var_type = data.get(f'variable{var_num}_type', 'number')  # NEW
                var_unit = data.get(f'variable{var_num}_unit', '').strip()
                var_price = data.get(f'variable{var_num}_price', 0)
                var_rate = data.get(f'variable{var_num}_rate', 1.0)
                
                # Only get value for number type
                var_value = None
                if var_type == 'number':
                    var_value = data.get(f'variable{var_num}_value', 0)

                try:
                    ProcessVariable.objects.create(
                        process=process,
                        variable_name=var_name,
                        variable_type=var_type,  # NEW
                        unit=var_unit,
                        variable_value=Decimal(str(var_value)) if var_value else None,
                        price=Decimal(str(var_price)),
                        rate=Decimal(str(var_rate)),
                        order=var_num - 1
                    )
                except (ValueError, TypeError, decimal.InvalidOperation) as e:
                    logger.warning(f"Error saving variable {var_name}: {e}")

            var_num += 1

    # ===== SAVE VENDORS =====
    process.process_vendors.all().delete()

    # Vendor 1 (Primary)
    vendor_pk = data.get('vendor1_id')
    if vendor_pk:
        try:
            vendor_obj = Vendor.objects.get(pk=vendor_pk)

            formula_rates = None
            if process.pricing_type == 'formula':
                formula_rates = {
                    'base_rate': float(data.get('vendor1_base_rate', 0) or 0),
                    'rate_per_unit': float(data.get('vendor1_rate_per_unit', 0) or 0),
                    'setup_fee': float(data.get('vendor1_setup_fee', 0) or 0),
                }

            ProcessVendor.objects.create(
                process=process,
                vendor_name=vendor_obj.name,
                vendor_id=data.get(
                    'vendor1_vendor_id',
                    f"VND-{str(vendor_obj.id).zfill(3)}"
                ),
                vps_score=vendor_obj.vps_score_value,
                priority='preferred',
                rush_enabled=data.get('vendor1_rush_enabled') == 'on',
                rush_fee_percentage=float(data.get('vendor1_rush_fee', 0) or 0),
                rush_threshold_days=int(data.get('vendor1_rush_threshold', 3) or 3),
                minimum_order=float(data.get('vendor1_min_order', 0) or 0),
                standard_lead_time=int(data.get('vendor1_standard_days', 5) or 5),
                rush_lead_time=int(data.get('vendor1_rush_days', 2) or 2),
                notes=data.get('vendor1_notes', ''),
                formula_rates=formula_rates,
            )
        except Vendor.DoesNotExist:
            pass

    # Vendor 2 (Alternative)
    vendor2_pk = data.get('vendor2_id')
    if vendor2_pk:
        try:
            vendor2_obj = Vendor.objects.get(pk=vendor2_pk)

            ProcessVendor.objects.create(
                process=process,
                vendor_name=vendor2_obj.name,
                vendor_id=data.get(
                    'vendor2_vendor_id',
                    f"VND-{str(vendor2_obj.id).zfill(3)}"
                ),
                vps_score=vendor2_obj.vps_score_value,
                priority='alternative',
                rush_enabled=data.get('vendor2_rush_enabled') == 'on',
                rush_fee_percentage=float(data.get('vendor2_rush_fee', 0) or 0),
                rush_threshold_days=int(data.get('vendor2_rush_threshold', 3) or 3),
                minimum_order=float(data.get('vendor2_min_order', 0) or 0),
                standard_lead_time=int(data.get('vendor2_standard_days', 5) or 5),
                rush_lead_time=int(data.get('vendor2_rush_days', 2) or 2),
                notes=data.get('vendor2_notes', ''),
                base_rate=float(data.get('vendor2_base_rate', 0) or 0),
                rate_per_unit=float(data.get('vendor2_rate_per_unit', 0) or 0),
                setup_fee=float(data.get('vendor2_setup_fee', 0) or 0),
            )
        except Vendor.DoesNotExist:
            pass

    # Vendor 3 (Backup)
    vendor3_pk = data.get('vendor3_id')
    if vendor3_pk:
        try:
            vendor3_obj = Vendor.objects.get(pk=vendor3_pk)

            ProcessVendor.objects.create(
                process=process,
                vendor_name=vendor3_obj.name,
                vendor_id=data.get(
                    'vendor3_vendor_id',
                    f"VND-{str(vendor3_obj.id).zfill(3)}"
                ),
                vps_score=vendor3_obj.vps_score_value,
                priority='backup',
                rush_enabled=data.get('vendor3_rush_enabled') == 'on',
                rush_fee_percentage=float(data.get('vendor3_rush_fee', 0) or 0),
                rush_threshold_days=int(data.get('vendor3_rush_threshold', 3) or 3),
                minimum_order=float(data.get('vendor3_min_order', 0) or 0),
                standard_lead_time=int(data.get('vendor3_standard_days', 5) or 5),
                rush_lead_time=int(data.get('vendor3_rush_days', 2) or 2),
                notes=data.get('vendor3_notes', ''),
                base_rate=float(data.get('vendor3_base_rate', 0) or 0),
                rate_per_unit=float(data.get('vendor3_rate_per_unit', 0) or 0),
                setup_fee=float(data.get('vendor3_setup_fee', 0) or 0),
            )
        except Vendor.DoesNotExist:
            pass

    # ===== SUCCESS MESSAGE =====
    if action == 'activate':
        messages.success(
            request,
            f'Process "{process.process_name}" has been activated!'
        )
    else:
        messages.success(
            request,
            f'Process "{process.process_name}" saved as draft.'
        )

    return redirect('process_list')


# ===== AJAX ENDPOINTS =====

@login_required
def ajax_generate_process_id(request):
    """Auto-generate Process ID from name (called via AJAX)"""
    name = request.GET.get('name', '')
    if name:
        temp_process = Process(process_name=name)
        process_id = temp_process.generate_process_id()
        return JsonResponse({'process_id': process_id})
    return JsonResponse({'process_id': ''})


@login_required
def ajax_calculate_margin(request):
    """Calculate margin from price and cost (called via AJAX)"""
    try:
        price = float(request.GET.get('price', 0))
        cost = float(request.GET.get('cost', 0))
        
        if price > 0:
            margin_amount = price - cost
            margin_percentage = (margin_amount / price) * 100
            
            # Determine status
            if margin_percentage >= 25:
                status = 'above'
                color = 'green'
                message = 'Above target (25%)'
            elif margin_percentage >= 15:
                status = 'on_target'
                color = 'yellow'
                message = 'On target'
            else:
                status = 'below'
                color = 'red'
                message = 'Below target'
            
            return JsonResponse({
                'margin_amount': round(margin_amount, 2),
                'margin_percentage': round(margin_percentage, 2),
                'status': status,
                'color': color,
                'message': message,
            })
    except Exception as e:
        return JsonResponse({'error': str(e)})
    
    return JsonResponse({'error': 'Invalid data'})

@login_required
@require_POST
def ajax_create_vendor(request):
    """Create or update a Vendor and return it for dropdowns."""
    try:
        payload = json.loads(request.body.decode('utf-8'))
        
        # Get required fields
        name = (payload.get('name') or '').strip()
        email = (payload.get('email') or '').strip()
        phone = (payload.get('phone') or '').strip()
        
        if not name:
            return JsonResponse({
                'success': False, 
                'message': 'Vendor name is required.'
            }, status=400)
        
        if not email:
            return JsonResponse({
                'success': False, 
                'message': 'Email is required.'
            }, status=400)
        
        if not phone:
            return JsonResponse({
                'success': False, 
                'message': 'Phone is required.'
            }, status=400)
        
        # Check if editing existing vendor
        vendor_id = payload.get('vendor_id')
        is_editing = vendor_id and str(vendor_id).strip()
        
        # Get all vendor fields from payload
        contact_person = (payload.get('contact_person') or '').strip()
        business_address = (payload.get('business_address') or payload.get('address') or '').strip()
        tax_pin = (payload.get('tax_pin') or '').strip()
        payment_terms = payload.get('payment_terms', '')
        payment_method = payload.get('payment_method', '')
        services = payload.get('services', '')  # Comma-separated string
        specialization = (payload.get('specialization') or '').strip()
        minimum_order = float(payload.get('minimum_order', 0) or 0)
        lead_time = (payload.get('lead_time') or '').strip()
        rush_capable = payload.get('rush_capable', False)
        quality_rating = payload.get('quality_rating', '')
        reliability_rating = payload.get('reliability_rating', '')
        vps_score = payload.get('vps_score', 'B')
        vps_score_value = float(payload.get('vps_score_value', 5.0))
        rating = float(payload.get('rating', 4.0))
        recommended = payload.get('recommended', False)
        
        if is_editing:
            # Update existing vendor
            try:
                vendor = Vendor.objects.get(id=vendor_id)
                vendor.name = name
                vendor.contact_person = contact_person
                vendor.email = email
                vendor.phone = phone
                vendor.business_address = business_address
                vendor.tax_pin = tax_pin
                vendor.payment_terms = payment_terms
                vendor.payment_method = payment_method
                vendor.services = services
                vendor.specialization = specialization
                vendor.minimum_order = minimum_order
                vendor.lead_time = lead_time
                vendor.rush_capable = rush_capable
                vendor.quality_rating = quality_rating
                vendor.reliability_rating = reliability_rating
                vendor.vps_score = vps_score
                vendor.vps_score_value = vps_score_value
                vendor.rating = rating
                vendor.recommended = recommended
                vendor.save()
                
                return JsonResponse({
                    'success': True,
                    'id': vendor.id,
                    'name': vendor.name,
                    'vps_score_value': str(vendor.vps_score_value),
                    'vps_score': vendor.vps_score,
                    'rating': str(vendor.rating),
                    'message': f'Vendor "{vendor.name}" updated successfully!'
                })
            except Vendor.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Vendor not found.'
                }, status=404)
        else:
            # Create new vendor
            vendor = Vendor.objects.create(
                name=name,
                contact_person=contact_person,
                email=email,
                phone=phone,
                business_address=business_address,
                tax_pin=tax_pin,
                payment_terms=payment_terms,
                payment_method=payment_method,
                services=services,
                specialization=specialization,
                minimum_order=minimum_order,
                lead_time=lead_time,
                rush_capable=rush_capable,
                quality_rating=quality_rating,
                reliability_rating=reliability_rating,
                vps_score=vps_score,
                vps_score_value=vps_score_value,
                rating=rating,
                recommended=recommended,
                active=True,
            )
            
            return JsonResponse({
                'success': True,
                'id': vendor.id,
                'name': vendor.name,
                'vps_score_value': str(vendor.vps_score_value),
                'vps_score': vendor.vps_score,
                'rating': str(vendor.rating),
                'message': f'Vendor "{vendor.name}" created successfully!'
            })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'message': 'Invalid JSON data'
        }, status=400)
    except ValueError as e:
        return JsonResponse({
            'success': False, 
            'message': f'Invalid number format: {str(e)}'
        }, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False, 
            'message': str(e)
        }, status=500)

def delivery_list(request):
    """Display list of all deliveries"""

    return render(request, 'delivery.html')


@login_required
@group_required('Account Manager')
def get_product_price(request, product_id):
    """API endpoint to get product price using centralized pricing resolver"""
    from clientapp.models import resolve_unit_price
    from decimal import Decimal
    
    try:
        product = Product.objects.get(id=product_id)
        
        # Use centralized pricing resolver (this already handles fallback to ProductPricing)
        unit_price = resolve_unit_price(product)
        
        # Get base_price for display (use resolved price if base_price is not set)
        base_price = product.base_price
        if (base_price is None or base_price == 0) and hasattr(product, 'pricing'):
            # If base_price not set, calculate from ProductPricing.base_cost with margin
            if product.pricing.base_cost:
                cost = product.pricing.base_cost
                margin = product.pricing.return_margin if hasattr(product.pricing, 'return_margin') else Decimal('30')
                base_price = cost * (Decimal('1') + (margin / Decimal('100')))
        
        return JsonResponse({
            'success': True,
            'id': product.id,
            'name': product.name,
            'internal_code': product.internal_code,
            'customization_level': product.customization_level,
            'base_price': float(base_price) if base_price else None,
            'unit_price': float(unit_price) if unit_price else 0,
            'has_costing_process': product.has_costing_process(),
            'is_published': product.status == 'published' and product.is_visible
        })
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Product not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@group_required('Account Manager')
def api_product_catalog(request):
    """Product catalog API endpoint for Account Managers - returns pricing metadata"""
    from clientapp.models import resolve_unit_price
    
    try:
        # Return all active products (not archived) - production team may add products that aren't published yet
        # Account Managers should see all products added by production team
        products = Product.objects.filter(
            status__in=['draft', 'published']  # Include both draft and published, exclude archived
        ).select_related('pricing').order_by('name')
        
        # Apply search filter if provided
        search = request.GET.get('search', '').strip()
        if search:
            products = products.filter(
                Q(name__icontains=search) | 
                Q(internal_code__icontains=search)
            )
        
        # Build response with pricing metadata
        results = []
        for product in products:
            unit_price = resolve_unit_price(product)
            results.append({
                'id': product.id,
                'name': product.name,
                'internal_code': product.internal_code,
                'customization_level': product.customization_level,
                'base_price': float(product.base_price) if product.base_price else None,
                'unit_price': float(unit_price),
                'has_costing_process': product.has_costing_process(),
            })
        
        return JsonResponse({
            'success': True,
            'count': len(results),
            'products': results
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def ajax_create_vendor(request):
    """Create a new Vendor from the Process editor and return it for dropdowns."""
    try:
        payload = json.loads(request.body.decode('utf-8'))
        name = (payload.get('name') or '').strip()
        email = (payload.get('email') or '').strip() or 'vendor@example.com'
        phone = (payload.get('phone') or '').strip() or 'N/A'
        address = (payload.get('address') or '').strip()
        
        if not name:
            return JsonResponse({
                'success': False, 
                'message': 'Vendor name is required.'
            }, status=400)

        # Create vendor with default VPS score
        vendor = Vendor.objects.create(
            name=name,
            email=email,
            phone=phone,
            address=address,
            vps_score='B',  # Default grade
            vps_score_value=5.0,  # Default score
            rating=4.0,  # Default rating
            active=True,
        )

        return JsonResponse({
            'success': True,
            'id': vendor.id,
            'name': vendor.name,
            'vps_score_value': str(vendor.vps_score_value),
            'message': f'Vendor "{vendor.name}" created successfully!'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False, 
            'message': str(e)
        }, status=500)

# ========== PROCESS-PRODUCT INTEGRATION HELPER FUNCTIONS ==========

def import_process_variables_to_product(process, product):
    """
    Import variables from a Process to a Product
    Returns the number of variables imported
    """
    imported_count = 0
    
    if process.pricing_type == 'formula':
        # For formula-based pricing, import formula variables
        process_variables = process.variables.all()
        
        for pv in process_variables:
            # Check if variable already exists
            existing = ProductVariable.objects.filter(
                product=product,
                name=pv.variable_name
            ).first()
            
            if not existing:
                # Create new product variable
                ProductVariable.objects.create(
                    product=product,
                    name=pv.variable_name,
                    variable_type='required',
                    pricing_type='increment',
                    source_process_variable=pv,
                    display_order=pv.order
                )
                imported_count += 1
                
    elif process.pricing_type == 'tier':
        # For tier-based pricing, import quantity as a variable
        quantity_var, created = ProductVariable.objects.get_or_create(
            product=product,
            name='Quantity',
            defaults={
                'variable_type': 'required',
                'pricing_type': 'fixed',
                'display_order': 0
            }
        )
        
        if created:
            # Create options from process tiers
            tiers = process.tiers.all().order_by('tier_number')
            for i, tier in enumerate(tiers):
                ProductVariableOption.objects.create(
                    variable=quantity_var,
                    name=f"{tier.quantity_from}-{tier.quantity_to} pieces",
                    display_order=i,
                    price_modifier=tier.price
                )
            imported_count += 1
    
    return imported_count


def ajax_process_variables(request, process_id):
    """
    AJAX endpoint to fetch process variables
    """
    try:
        process = Process.objects.get(id=process_id)
        
        variables_data = []
        
        if process.pricing_type == 'formula':
            for var in process.variables.all():
                variables_data.append({
                    'id': var.id,
                    'name': var.variable_name,
                    'type': var.variable_type,
                    'unit': var.unit,
                    'min_value': str(var.min_value) if var.min_value else None,
                    'max_value': str(var.max_value) if var.max_value else None,
                    'default_value': str(var.default_value) if var.default_value else None,
                    'description': var.description
                })
        elif process.pricing_type == 'tier':
            # Return tier information
            for tier in process.tiers.all():
                variables_data.append({
                    'tier_number': tier.tier_number,
                    'quantity_from': tier.quantity_from,
                    'quantity_to': tier.quantity_to,
                    'cost': str(tier.cost),
                    'price': str(tier.price)
                })
        
        return JsonResponse({
            'success': True,
            'pricing_type': process.pricing_type,
            'variables': variables_data
        })
        
    except Process.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Process not found'
        }, status=404)


# Add to clients/views.py

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Avg, Q
from datetime import datetime, timedelta
from decimal import Decimal

@staff_member_required
def admin_dashboard_index(request):
    """Main admin dashboard with real-time statistics"""
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    this_week_start = today - timedelta(days=today.weekday())
    
    # Calculate KPIs
    total_clients = Client.objects.filter(status='Active').count()
    quotes_this_month = Quote.objects.filter(created_at__gte=this_month_start).values('quote_id').distinct().count()
    jobs_in_production = Job.objects.filter(status__in=['pending', 'in_progress']).count()
    
    # Revenue this month
    monthly_revenue = Quote.objects.filter(
        status='Approved',
        approved_at__gte=this_month_start
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    # Pending approvals
    pending_approvals = Quote.objects.filter(
        production_status='pending'
    ).values('quote_id').distinct().count()
    
    # Overdue jobs
    overdue_jobs = Job.objects.filter(
        expected_completion__lt=today,
        status__in=['pending', 'in_progress']
    ).count()
    
    # Completed this week
    completed_this_week = Job.objects.filter(
        status='completed',
        actual_completion__gte=this_week_start
    ).count()
    
    # Pending payments
    pending_payments = LPO.objects.filter(
        status__in=['approved', 'in_production']
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    # Vendor performance
    avg_vendor_score = Vendor.objects.filter(active=True).aggregate(
        avg=Avg('vps_score_value')
    )['avg'] or 0
    
    # Profit margin calculation
    approved_quotes = Quote.objects.filter(status='Approved', production_cost__isnull=False)
    total_revenue_for_margin = approved_quotes.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_cost_for_margin = approved_quotes.aggregate(Sum('production_cost'))['production_cost__sum'] or 0
    profit_margin = ((total_revenue_for_margin - total_cost_for_margin) / total_revenue_for_margin * 100) if total_revenue_for_margin > 0 else 0
    
    # Growth calculations (compare to last month)
    last_month_clients = Client.objects.filter(
        status='Active',
        created_at__gte=last_month_start,
        created_at__lt=this_month_start
    ).count()
    clients_growth = ((total_clients - last_month_clients) / last_month_clients * 100) if last_month_clients > 0 else 0
    
    # Recent alerts
    recent_alerts = SystemAlert.objects.filter(
        is_active=True,
        is_dismissed=False
    ).order_by('-created_at')[:5]
    
    # Recent activity
    recent_activity = ActivityLog.objects.select_related(
        'client', 'created_by'
    ).order_by('-created_at')[:10]

     # 1. Revenue Trend (Last 6 Months)
    revenue_trend_data = []
    revenue_labels = []
    for i in range(5, -1, -1):
        month_date = today.replace(day=1) - timedelta(days=i*30)
        # Adjust to first day of that month
        m_start = month_date.replace(day=1)
        # End of that month
        if m_start.month == 12:
            m_end = m_start.replace(year=m_start.year+1, month=1, day=1) - timedelta(days=1)
        else:
            m_end = m_start.replace(month=m_start.month+1, day=1) - timedelta(days=1)
            
        rev = Quote.objects.filter(
            status='Approved',
            approved_at__gte=m_start,
            approved_at__lte=m_end
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        revenue_trend_data.append(float(rev))
        revenue_labels.append(m_start.strftime('%b'))

    # 2. Production by Category (Job Types)
    job_types = Job.objects.values('job_type').annotate(count=Count('id')).order_by('-count')
    category_labels = [item['job_type'].replace('_', ' ').title() for item in job_types]
    category_data = [item['count'] for item in job_types]
    if not category_data: # Fallback if no data
        category_labels = ['No Data']
        category_data = [0]

    # 3. Weekly Jobs Overview (Last 7 Days)
    weekly_labels = []
    completed_data = []
    in_progress_data = []
    delayed_data = []
    
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        weekly_labels.append(day.strftime('%a'))
        
        # Completed on this day
        completed = Job.objects.filter(
            status='completed',
            actual_completion=day
        ).count()
        completed_data.append(completed)
        
        # In Progress (Active on this day)
        in_progress = Job.objects.filter(
            status__in=['in_progress', 'pending'],
            created_at__date__lte=day
        ).count()
        in_progress_data.append(in_progress)
        
        # Delayed (Overdue as of this day)
        delayed = Job.objects.filter(
            status__in=['in_progress', 'pending'],
            expected_completion__lt=day
        ).count()
        delayed_data.append(delayed)
    
    context = {
        'total_clients': total_clients,
        'clients_growth': round(clients_growth, 1),
        'quotes_this_month': quotes_this_month,
        'quotes_growth': 8,  # Calculate based on your logic
        'jobs_in_production': jobs_in_production,
        'monthly_revenue': monthly_revenue,
        'revenue_growth': 12,  # Calculate based on your logic
        'pending_approvals': pending_approvals,
        'overdue_jobs': overdue_jobs,
        'overdue_change': -2,
        'completed_this_week': completed_this_week,
        'completed_growth': 15,
        'pending_payments': pending_payments,
        'avg_vendor_score': round(avg_vendor_score, 1),
        'vendor_score_change': 3,
        'profit_margin': round(profit_margin, 1),
        'unread_alerts': recent_alerts.count(),
        'recent_alerts': recent_alerts,
        'recent_activity': recent_activity,

        # Chart Data (JSON)
        'revenue_labels': json.dumps(revenue_labels),
        'revenue_data': json.dumps(revenue_trend_data),
        'category_labels': json.dumps(category_labels),
        'category_data': json.dumps(category_data),
        'weekly_labels': json.dumps(weekly_labels),
        'weekly_completed': json.dumps(completed_data),
        'weekly_in_progress': json.dumps(in_progress_data),
        'weekly_delayed': json.dumps(delayed_data),
    }
    
    
    return render(request, 'admin/index.html', context)


# Add CRUD views for each section
@staff_member_required
def admin_clients_list(request):
    """List all clients with filters"""
    from django.contrib.auth.models import Group
    
    clients = Client.objects.all().order_by('-created_at')
    
    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter:
        clients = clients.filter(status=status_filter)
    
    search = request.GET.get('search', '').strip()
    if search:
        clients = clients.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(client_id__icontains=search)
        )
    
    # Get account managers for the dropdown
    account_managers = User.objects.filter(groups__name='Account Manager').order_by('first_name')
    
    context = {
        'clients': clients,
        'status_filter': status_filter,
        'search': search,
        'account_managers': account_managers,
    }
    return render(request, 'admin/clients_list.html', context)


@staff_member_required
def admin_quotes_list(request):
    """List all quotes"""
    quotes = Quote.objects.select_related('client', 'lead').order_by('-created_at')
    
    context = {'quotes': quotes}
    return render(request, 'admin/quotes_list.html', context)


@staff_member_required
def admin_jobs_list(request):
    """List all jobs"""
    jobs = Job.objects.select_related('client').order_by('-created_at')
    
    context = {'jobs': jobs}
    return render(request, 'admin/jobs_list.html', context)


@staff_member_required
def admin_products_list(request):
    """List all products"""
    products = Product.objects.all().order_by('-created_at')
    
    context = {'products': products}
    return render(request, 'admin/products_list.html', context)


@staff_member_required
def admin_vendors_list(request):
    """List all vendors"""
    vendors = Vendor.objects.all().order_by('-vps_score_value')
    
    context = {'vendors': vendors}
    return render(request, 'admin/vendors_list.html', context)


# API Endpoints for Admin Dashboard CRUD Operations
@staff_member_required
@require_POST
def api_admin_create_client(request):
    """Create a new client via API"""
    try:
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        status = request.POST.get('status', 'Active')
        
        if not name or not email:
            return JsonResponse({'success': False, 'message': 'Name and email are required'}, status=400)
        
        # Check if email already exists
        if Client.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': 'Email already exists'}, status=400)
        
        client = Client.objects.create(
            name=name,
            email=email,
            phone=phone,
            status=status
        )
        
        # Log activity
        ActivityLog.objects.create(
            activity_type='Client Created',
            title=f'New client {name} created',
            description=f'Client {name} was created by admin',
            client=client,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Client created successfully',
            'client_id': client.id
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_member_required
def admin_leads_list(request):
    """List all leads for admin"""
    leads = Lead.objects.all().order_by('-created_at')
    status_filter = request.GET.get('status')
    if status_filter:
        leads = leads.filter(status=status_filter)

    search = request.GET.get('search', '').strip()
    if search:
        leads = leads.filter(
            Q(lead_name__icontains=search) |
            Q(email__icontains=search) |
            Q(company_name__icontains=search)
        )

    context = {'leads': leads, 'status_filter': status_filter, 'search': search}
    return render(request, 'admin/leads_list.html', context)


@staff_member_required
def admin_processes_list(request):
    processes = Process.objects.all().order_by('-created_at')
    context = {'processes': processes}
    return render(request, 'admin/processes_list.html', context)


@staff_member_required
def admin_qc_list(request):
    qcs = QCInspection.objects.select_related('job').order_by('-created_at')
    context = {'qcs': qcs}
    return render(request, 'admin/qc_list.html', context)


@staff_member_required
def admin_deliveries_list(request):
    deliveries = Delivery.objects.select_related('job').order_by('-created_at')
    context = {'deliveries': deliveries}
    return render(request, 'admin/deliveries_list.html', context)


@staff_member_required
def admin_lpos_list(request):
    lpos = LPO.objects.select_related('client').order_by('-created_at')
    context = {'lpos': lpos}
    return render(request, 'admin/lpos_list.html', context)


@staff_member_required
def admin_payments_list(request):
    payments = Payment.objects.select_related('client').order_by('-created_at')
    context = {'payments': payments}
    return render(request, 'admin/payments_list.html', context)


@staff_member_required
def admin_analytics(request):
    """
    Enhanced Analytics View
    Aggregates data from various helper functions in admin_dashboard.py
    """
    from .admin_dashboard import (
        get_dashboard_stats, 
        get_sales_performance_trend,
        get_profit_margin_data, 
        get_outstanding_receivables,
        get_payment_collection_rate, 
        get_staff_performance,
        get_time_based_insights, 
        get_top_products,
        get_order_status_distribution
    )
    import json
    
    # Fetch all analytics data
    context = {
        'title': 'Analytics Overview',
        'dashboard_stats': get_dashboard_stats(),
        'sales_trend': json.dumps(get_sales_performance_trend(months=12), default=str),
        'order_distribution': json.dumps(get_order_status_distribution()),
        'profit_margins': get_profit_margin_data(),
        'receivables': get_outstanding_receivables(),
        'collection_rate': get_payment_collection_rate(),
        'staff_performance': get_staff_performance(),
        'time_insights': get_time_based_insights(),
        'top_products': get_top_products(limit=10),
    }
    return render(request, 'admin/analytics.html', context)


# Add this import at the top with other models
from .models import SystemSetting

@staff_member_required
def admin_settings(request):
    """
    System Settings View with Persistence
    """
    # Define default settings
    default_settings = {
        'site_title': 'Print Duka MIS',
        'support_email': 'support@printduka.com',
        'currency': 'KES',
        'timezone': 'Africa/Nairobi',
        'maintenance_mode': 'False',
        'allow_registration': 'True',
        'email_on_order': 'True',
        'email_on_quote': 'True',
        'daily_digest': 'False',
    }

    if request.method == 'POST':
        try:
            # Iterate through POST data and update settings
            for key, value in request.POST.items():
                if key in default_settings:
                    SystemSetting.objects.update_or_create(
                        key=key,
                        defaults={'value': value}
                    )
            
            # Handle checkboxes (unchecked checkboxes don't send POST data)
            checkbox_settings = ['maintenance_mode', 'allow_registration', 'email_on_order', 'email_on_quote', 'daily_digest']
            for key in checkbox_settings:
                if key not in request.POST:
                    SystemSetting.objects.update_or_create(
                        key=key,
                        defaults={'value': 'False'}
                    )
            
            messages.success(request, 'System settings updated successfully.')
        except Exception as e:
            messages.error(request, f'Error saving settings: {str(e)}')
            
        return redirect('admin_settings')
        
    # Load current settings from DB, falling back to defaults
    current_settings = default_settings.copy()
    db_settings = SystemSetting.objects.filter(key__in=default_settings.keys())
    for setting in db_settings:
        current_settings[setting.key] = setting.value

    # Convert boolean strings to actual booleans for the template
    def to_bool(val):
        return str(val).lower() == 'true'

    context = {
        'title': 'System Settings',
        'system_settings': {
            'site_title': current_settings['site_title'],
            'support_email': current_settings['support_email'],
            'currency': current_settings['currency'],
            'timezone': current_settings['timezone'],
            'maintenance_mode': to_bool(current_settings['maintenance_mode']),
            'allow_registration': to_bool(current_settings['allow_registration']),
        },
        'notification_settings': {
            'email_on_order': to_bool(current_settings['email_on_order']),
            'email_on_quote': to_bool(current_settings['email_on_quote']),
            'daily_digest': to_bool(current_settings['daily_digest']),
        }
    }
    return render(request, 'admin/settings.html', context)

@staff_member_required
def admin_users_list(request):
    """List all users and groups for admin management"""
    from django.contrib.auth.models import Group
    
    users = User.objects.all().order_by('username')
    groups = Group.objects.all().order_by('name')
    
    context = {
        'users': users,
        'groups': groups,
    }
    return render(request, 'admin/users_list.html', context)




@staff_member_required
def admin_alerts_list(request):
    alerts = SystemAlert.objects.filter(is_active=True).order_by('-created_at')
    context = {'alerts': alerts}
    return render(request, 'admin/alerts_list.html', context)


@staff_member_required
@require_POST
def api_admin_update_client(request, client_id):
    """Update an existing client via API"""
    try:
        client = get_object_or_404(Client, id=client_id)
        
        client.name = request.POST.get('name', client.name)
        client.email = request.POST.get('email', client.email)
        client.phone = request.POST.get('phone', client.phone)
        client.status = request.POST.get('status', client.status)
        
        client.save()
        
        # Log activity
        ActivityLog.objects.create(
            activity_type='Client Updated',
            title=f'Client {client.name} updated',
            description=f'Client {client.name} was updated by admin',
            client=client,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Client updated successfully',
            'client_id': client.id
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_member_required
@require_POST
def api_admin_delete_client(request, client_id):
    """Delete a client via API"""
    try:
        client = get_object_or_404(Client, id=client_id)
        
        # Log activity before deletion
        ActivityLog.objects.create(
            activity_type='Client Deleted',
            title=f'Client {client.name} deleted',
            description=f'Client {client.name} was deleted by admin',
            client=client,
            created_by=request.user
        )
        
        client_name = client.name
        client.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Client {client_name} deleted successfully'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_member_required
def api_admin_dashboard_data(request):
    """API endpoint for real-time dashboard data polling with real data"""
    from .admin_dashboard import get_dashboard_stats
    
    try:
        stats = get_dashboard_stats()
        
        today = timezone.now().date()
        
        # ===== REVENUE TREND (Last 6 Months) =====
        revenue_trend = []
        current_date = today.replace(day=1)  # Start of current month
        
        for i in range(5, -1, -1):
            # Calculate month start and end
            if i == 0:
                month_start = current_date
                month_end = today
            else:
                # Go back i months
                temp_date = current_date
                for _ in range(i):
                    temp_date = temp_date - timedelta(days=1)
                    temp_date = temp_date.replace(day=1)
                month_start = temp_date
                # Get last day of month
                next_month = month_start + timedelta(days=32)
                month_end = (next_month.replace(day=1) - timedelta(days=1))
            
            # Sum revenue from approved quotes and completed LPOs
            quote_revenue = Quote.objects.filter(
                status__in=['Approved', 'Completed'],
                approved_at__gte=month_start,
                approved_at__lte=month_end
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            lpo_revenue = LPO.objects.filter(
                status__in=['approved', 'completed'],
                created_at__gte=month_start,
                created_at__lte=month_end
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            monthly_total = float(quote_revenue or 0) + float(lpo_revenue or 0)
            revenue_trend.append(monthly_total)
        
        # ===== PRODUCTION BY CATEGORY (Product distribution) =====
        # Get product counts by category or type
        from .models import Product, ProductTag, JobProduct
        
        category_data = []
        category_labels = []
        
        # If products have tags or categories, group by them
        product_counts = Product.objects.values(
            'product_category'  # Or use tags if available
        ).annotate(count=Count('id')).order_by('-count')[:5]
        
        if product_counts.exists():
            for item in product_counts:
                category = item.get('product_category', 'Uncategorized')
                category_labels.append(category)
                category_data.append(item['count'])
        else:
            # Fallback: get production by job types/products in recent jobs
            job_products = JobProduct.objects.filter(
                job__created_at__gte=today - timedelta(days=30)
            ).values('product__name').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            
            if job_products.exists():
                for item in job_products:
                    category_labels.append(item['product__name'])
                    category_data.append(item['count'])
            else:
                # Last fallback: use generic data
                category_labels = ['Products', 'Services', 'Other']
                category_data = [Product.objects.count(), 0, 0]
        
        production_by_category = category_data if category_data else [1, 1, 1]
        
        # ===== WEEKLY JOBS OVERVIEW (Last 6 days) =====
        weekly_jobs = {
            'completed': [],
            'in_progress': [],
            'delayed': []
        }
        
        # Get job counts for last 6 days by status
        for i in range(5, -1, -1):
            day = today - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0)
            day_end = day.replace(hour=23, minute=59, second=59)
            
            completed_count = Job.objects.filter(
                status__in=['completed', 'Completed', 'done', 'Done'],
                updated_at__date=day
            ).count()
            
            in_progress_count = Job.objects.filter(
                status__in=['in_progress', 'In Progress', 'pending', 'Pending'],
                updated_at__date=day
            ).count()
            
            # For delayed jobs, check if they have exceeded deadline
            overdue_count = Job.objects.filter(
                status__in=['in_progress', 'In Progress', 'pending', 'Pending'],
                deadline__lt=day,
                updated_at__date=day
            ).count()
            
            weekly_jobs['completed'].append(completed_count)
            weekly_jobs['in_progress'].append(in_progress_count)
            weekly_jobs['delayed'].append(overdue_count)
        
        # ===== CALCULATE KPI STATS =====
        # Total clients
        total_clients = Client.objects.count()
        
        # Quotes this month
        quotes_this_month = Quote.objects.filter(
            created_at__gte=today.replace(day=1)
        ).count()
        
        # Jobs in production
        jobs_in_production = Job.objects.filter(
            status__in=['in_progress', 'In Progress', 'pending', 'Pending']
        ).count()
        
        # Monthly revenue
        monthly_start = today.replace(day=1)
        monthly_revenue = Quote.objects.filter(
            status__in=['Approved', 'Completed'],
            approved_at__gte=monthly_start
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        monthly_revenue_lpo = LPO.objects.filter(
            created_at__gte=monthly_start,
            status__in=['approved', 'completed']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        monthly_revenue = float(monthly_revenue or 0) + float(monthly_revenue_lpo or 0)
        
        # Pending approvals
        pending_approvals = Quote.objects.filter(
            status__in=['Pending', 'pending', 'Draft', 'draft']
        ).count()
        
        # Overdue jobs
        overdue_jobs = Job.objects.filter(
            status__in=['in_progress', 'In Progress', 'pending', 'Pending'],
            deadline__lt=today
        ).count()
        
        return JsonResponse({
            'success': True,
            'total_clients': total_clients,
            'quotes_this_month': quotes_this_month,
            'jobs_in_production': jobs_in_production,
            'monthly_revenue': monthly_revenue,
            'pending_approvals': pending_approvals,
            'overdue_jobs': overdue_jobs,
            'revenue_trend': revenue_trend,
            'production_by_category': production_by_category,
            'weekly_jobs': weekly_jobs
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

# Add this import at the top if not present
from .models import ActivityLog

@staff_member_required
def admin_activity_list(request):
    """List all activity logs"""
    activities = ActivityLog.objects.select_related('client', 'created_by').order_by('-created_at')
    
    # Optional: Add filtering
    activity_type = request.GET.get('type')
    if activity_type:
        activities = activities.filter(activity_type=activity_type)
        
    search = request.GET.get('search')
    if search:
        activities = activities.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search) |
            Q(client__name__icontains=search)
        )
        
    paginator = Paginator(activities, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'activity_type': activity_type,
        'search': search
    }
    return render(request, 'admin/activity_list.html', context)


from django.db.models import Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta

# ... existing imports ...

@login_required
def production_settings(request):
    """View for Production Team Settings"""
    # You can add logic here to save settings if needed
    if request.method == 'POST':
        # Handle form submission here
        messages.success(request, 'Settings updated successfully.')
        return redirect('production_settings')
        
    context = {
        'title': 'Production Settings',
        'user': request.user,
    }
    return render(request, 'production_settings.html', context)

@login_required
def production_analytics(request):
    """View for Production Team Analytics"""
    # Calculate date ranges
    today = timezone.now()
    thirty_days_ago = today - timedelta(days=30)
    
    # Fetch relevant jobs
    all_jobs = Job.objects.all() # Filter by production team if needed
    recent_jobs = all_jobs.filter(created_at__gte=thirty_days_ago)
    
    # Calculate KPIs
    total_jobs_month = recent_jobs.count()
    completed_jobs = recent_jobs.filter(status='completed').count()
    
    # Calculate On-Time Rate (Example logic)
    on_time_jobs = recent_jobs.filter(status='completed', actual_completion__lte=F('expected_completion')).count()

    on_time_rate = (on_time_jobs / completed_jobs * 100) if completed_jobs > 0 else 100
    
    # Calculate Average Lead Time
    # This is a placeholder calculation
    avg_lead_time = 3.5 # Days
    
    context = {
        'title': 'Production Analytics',
        'total_jobs_month': total_jobs_month,
        'completion_rate': (completed_jobs / total_jobs_month * 100) if total_jobs_month > 0 else 0,
        'on_time_rate': on_time_rate,
        'avg_lead_time': avg_lead_time,
        'recent_jobs': recent_jobs.order_by('-created_at')[:5],
    }
    return render(request, 'production_analytics.html', context)