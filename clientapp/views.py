from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from .models import Lead, Client
from .forms import LeadForm, ClientForm


def dashboard(request):
    """Dashboard view with statistics - Real-time data"""
    from django.db.models import Count
    from datetime import datetime, timedelta
    
    # Get current counts
    total_leads = Lead.objects.count()
    converted_leads = Lead.objects.filter(status='Converted').count()
    active_clients = Client.objects.filter(status='Active').count()
    b2b_clients = Client.objects.filter(client_type='B2B').count()
    
    # Calculate percentage changes (compared to last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    # Top Product Interests from actual lead data
    product_interests = Lead.objects.exclude(product_interest='').values('product_interest').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Calculate percentages
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
        # Default data if no products yet
        top_products = [
            {'name': 'Business Cards', 'interest': 85},
            {'name': 'Brochures', 'interest': 72},
            {'name': 'Banners & Signage', 'interest': 68},
            {'name': 'Packaging', 'interest': 54},
            {'name': 'Corporate Stationery', 'interest': 45},
        ]
    
    # Recent activity - Mix of leads and clients
    recent_activity = []
    
    # Recent clients
    recent_clients = Client.objects.order_by('-created_at')[:2]
    for client in recent_clients:
        time_diff = datetime.now() - client.created_at.replace(tzinfo=None)
        if time_diff.days > 0:
            time_str = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
        elif time_diff.seconds // 3600 > 0:
            hours = time_diff.seconds // 3600
            time_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            minutes = time_diff.seconds // 60
            time_str = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        
        recent_activity.append({
            'client': client.company if client.company else client.name,
            'action': 'Profile Activated',
            'time': time_str,
            'type': client.client_type
        })
    
    # Recent leads
    recent_leads = Lead.objects.filter(status='Qualified').order_by('-created_at')[:2]
    for lead in recent_leads:
        time_diff = datetime.now() - lead.created_at.replace(tzinfo=None)
        if time_diff.days > 0:
            time_str = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
        elif time_diff.seconds // 3600 > 0:
            hours = time_diff.seconds // 3600
            time_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            minutes = time_diff.seconds // 60
            time_str = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        
        recent_activity.append({
            'client': lead.name,
            'action': 'Lead Qualified',
            'time': time_str,
            'type': 'B2C'
        })
    
    # Sort by most recent
    recent_activity = sorted(recent_activity, key=lambda x: x['time'])[:4]
    
    # Lifecycle status - Real data
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
        'total_leads': total_leads,
        'converted_leads': converted_leads,
        'active_clients': active_clients,
        'b2b_clients': b2b_clients,
        'recent_activity': recent_activity,
        'top_products': top_products,
        'dormant_clients': dormant_clients,
        'inactive_clients': inactive_clients,
        'avg_onboarding': avg_onboarding,
    }
    return render(request, 'dashboard.html', context)


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
    
    context = {
        'current_view': 'leads',
        'leads': leads,
        'form': form,
        'search_query': search_query,
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
    """Client onboarding workflow"""
    prefilled_data = request.session.pop('prefilled_lead', None)
    
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, f'Client {client.client_id} created successfully!')
            return redirect('client_list')
        else:
            messages.error(request, 'Please fill in all required fields')
    else:
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

def client_profile(request, pk):
    client = get_object_or_404(Client, pk=pk)
    return render(request, 'client_profile.html', {'client': client})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from .models import Client, Lead, Quote
from decimal import Decimal
import json


def create_quote(request):
    """View for creating a new quote"""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get form data
                quote_type = request.POST.get('quote_type')
                client_id = request.POST.get('client_id')
                lead_id = request.POST.get('lead_id')
                
                # Validate client or lead selection
                client = None
                lead = None
                
                if quote_type == 'client' and client_id:
                    client = get_object_or_404(Client, id=client_id)
                elif quote_type == 'lead' and lead_id:
                    lead = get_object_or_404(Lead, id=lead_id)
                else:
                    messages.error(request, 'Please select a valid client or lead')
                    return redirect('create_quote')
                
                # Get quote details
                quote_number = request.POST.get('quote_number')
                quote_date = request.POST.get('quote_date')
                valid_until = request.POST.get('valid_until')
                payment_terms = request.POST.get('payment_terms', 'Prepaid')
                status = request.POST.get('status', 'Draft')
                notes = request.POST.get('notes', '')
                terms = request.POST.get('terms', '')
                include_vat = request.POST.get('include_vat') == 'on'
                
                # Get client details
                client_name = request.POST.get('client_name')
                client_email = request.POST.get('client_email')
                client_phone = request.POST.get('client_phone')
                client_address = request.POST.get('client_address')
                
                # Get items count
                item_count = int(request.POST.get('item_count', 0))
                
                if item_count == 0:
                    messages.error(request, 'Please add at least one item to the quote')
                    return redirect('create_quote')
                
                # Calculate totals
                subtotal = Decimal('0')
                created_quotes = []
                
                # Create quotes for each item
                for i in range(1, item_count + 1):
                    description = request.POST.get(f'description_{i}')
                    
                    # Only process if description exists (item wasn't deleted)
                    if description and description.strip():
                        quantity = int(request.POST.get(f'quantity_{i}', 1))
                        cost = Decimal(request.POST.get(f'cost_{i}', 0))
                        markup = Decimal(request.POST.get(f'markup_{i}', 30))
                        price = Decimal(request.POST.get(f'price_{i}', 0))
                        amount = Decimal(request.POST.get(f'amount_{i}', 0))
                        
                        # Add to subtotal
                        subtotal += amount
                        
                        # Create quote with custom quote_id if provided
                        quote = Quote(
                            client=client,
                            lead=lead,
                            product_name=description,
                            quantity=quantity,
                            cost_price=cost,
                            markup_percentage=markup,
                            selling_price=price,
                            status=status,
                            notes=notes,
                            created_by=request.user
                        )
                        
                        # Set custom quote_id if provided and it's the first item
                        if i == 1 and quote_number:
                            quote.quote_id = quote_number
                        
                        # Set dates
                        if quote_date:
                            quote.quote_date = quote_date
                        if valid_until:
                            quote.valid_until = valid_until
                        
                        quote.save()
                        created_quotes.append(quote)
                
                # Add VAT if included
                if include_vat:
                    vat_amount = subtotal * Decimal('0.16')
                    total_amount = subtotal + vat_amount
                else:
                    total_amount = subtotal
                
                # Update all quotes with the same quote_id (for grouped items)
                if created_quotes:
                    main_quote_id = created_quotes[0].quote_id
                    for quote in created_quotes[1:]:
                        quote.quote_id = main_quote_id
                        quote.save()
                
                # Success message based on status
                if status == 'Draft':
                    messages.success(request, f'Quote saved as draft! Quote ID: {created_quotes[0].quote_id}')
                else:
                    messages.success(request, f'Quote created successfully! Quote ID: {created_quotes[0].quote_id}')
                
                # Redirect based on quote type
                if client:
                    return redirect('client_profile', pk=client.pk)
                elif lead:
                    return redirect('lead_intake')
                else:
                    return redirect('dashboard')
                
        except Exception as e:
            messages.error(request, f'Error creating quote: {str(e)}')
            return redirect('create_quote')
    
    # GET request - show form
    clients = Client.objects.filter(status='Active').order_by('name')
    leads = Lead.objects.exclude(status__in=['Converted', 'Lost']).order_by('-created_at')
    
    # Set default dates
    today = timezone.now().date()
    default_valid_until = today + timedelta(days=30)
    
    context = {
        'clients': clients,
        'leads': leads,
        'current_year': timezone.now().year,
        'today': today.isoformat(),
        'default_valid_until': default_valid_until.isoformat(),
    }
    
    return render(request, 'create_quote.html', context)


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

def quotes_list(request):
    """List all quotes"""
    quotes = Quote.objects.select_related('client', 'lead', 'created_by').order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        quotes = quotes.filter(status=status_filter)
    
    context = {
        'quotes': quotes,
        'status_filter': status_filter,
    }
    
    return render(request, 'clients/quotes_list.html', context)


def quote_detail(request, quote_id):
    """View quote details"""
    quote = get_object_or_404(Quote, quote_id=quote_id)
    
    context = {
        'quote': quote,
    }
    
    return render(request, 'clients/quote_detail.html', context)



def delete_quote(request, quote_id):
    """Delete a quote"""
    if request.method == 'POST':
        quote = get_object_or_404(Quote, quote_id=quote_id)
        quote.delete()
        messages.success(request, 'Quote deleted successfully')
        return redirect('quotes_list')
    
    return redirect('quotes_list')

from .forms import JobForm
def create_job(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.save()

            # Log activity for tracking
            ActivityLog.objects.create(
                client=job.client,
                activity_type='Order',
                title=f"New Job Created - {job.product}",
                description=f"A new job ({job.product}) with quantity {job.quantity} was created and assigned to {job.person_in_charge}.",
                created_by=request.user
            )

            # Update client's last_activity timestamp
            job.client.last_activity = job.created_at
            job.client.save()

            messages.success(request, f"Job '{job.product}' has been successfully created for {job.client.name}.")
            return redirect('client_profile', pk=job.client.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = JobForm()

    context = {
        'form': form,
        'clients': Client.objects.all().order_by('name'),
        'users': Client._meta.get_field('account_manager').remote_field.model.objects.all(),
    }
    return render(request, 'create_job.html', context)