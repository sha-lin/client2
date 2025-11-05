import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from .forms import LeadForm, ClientForm
from .models import Lead, Client, ClientContact, ComplianceDocument


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

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Client, Lead, ClientContact, ComplianceDocument, ActivityLog
from .forms import ClientForm

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
                email = request.POST.get('email_b2c', '').strip()  # Required
                phone = request.POST.get('phone_b2c', '').strip()  # Required
                preferred_channel = request.POST.get('preferred_channel_b2c', 'Email')
                lead_source = request.POST.get('lead_source_b2c', '')
                
                # Validate required B2C fields (only name, email, phone)
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
                
                # Create B2C client - Single step, no complexity
                client = Client.objects.create(
                    client_type='B2C',
                    company=company if company else '',  # Optional
                    name=name,
                    email=email,
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



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from decimal import Decimal
from .models import Quote, Client, Lead, ActivityLog


@login_required
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
            unit_price = Decimal(request.POST.get('unit_price', '0'))
            include_vat = request.POST.get('include_vat') == 'on'
            payment_terms = request.POST.get('payment_terms', 'Prepaid')
            status = request.POST.get('status', 'Draft')
            notes = request.POST.get('notes', '')
            terms = request.POST.get('terms', '')
            valid_until_str = request.POST.get('valid_until')
            quote_date_str = request.POST.get('quote_date')

            if not product_name:
                messages.error(request, "Product name is required.")
                return redirect('create_quote')

            # Set dates
            quote_date = timezone.now().date()
            valid_until = quote_date + timedelta(days=30)
            if quote_date_str:
                quote_date = timezone.datetime.fromisoformat(quote_date_str).date()
            if valid_until_str:
                valid_until = timezone.datetime.fromisoformat(valid_until_str).date()

            # Calculate totals
            subtotal = unit_price * quantity
            vat_amount = subtotal * Decimal('0.16') if include_vat else Decimal('0')
            total_amount = subtotal + vat_amount

            # Create quote
            quote = Quote.objects.create(
                client=client,
                lead=lead,
                product_name=product_name,
                quantity=quantity,
                unit_price=unit_price,
                total_amount=total_amount,
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
            entity = client or lead
            entity_name = client.name if client else lead.name

            ActivityLog.objects.create(
                client=client if client else None,
                activity_type='Quote',
                title=f"Quote {quote.quote_id} Created",
                description=f"Quote for {product_name} (x{quantity}) totaling KES {total_amount:,.2f}",
                related_quote=quote,
                created_by=request.user
            )

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

    today = timezone.now().date()
    default_valid_until = today + timedelta(days=30)

    context = {
        'clients': clients,
        'leads': leads,
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
    }

    return render(request, 'client_profile.html', context)

def update_quote_status(request, quote_id):
    """Update quote status via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
            loss_reason = data.get('loss_reason', '')
            
            # Get all quotes with this quote_id (grouped items)
            quotes = Quote.objects.filter(quote_id=quote_id)
            
            if not quotes.exists():
                return JsonResponse({'success': False, 'error': 'Quote not found'}, status=404)
            
            # Update all quotes in the group
            for quote in quotes:
                quote.status = new_status
                if new_status == 'Approved':
                    quote.approved_at = timezone.now()
                if new_status == 'Lost' and loss_reason:
                    quote.loss_reason = loss_reason
                quote.save()
            
            # Log activity
            first_quote = quotes.first()
            if first_quote.client:
                ActivityLog.objects.create(
                    client=first_quote.client,
                    activity_type='Quote',
                    title=f"Quote {quote_id} Status Updated",
                    description=f"Status changed to {new_status}",
                    related_quote=first_quote,
                    created_by=request.user
                )
                
                # Update client last activity
                first_quote.client.last_activity = timezone.now()
                first_quote.client.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Quote status updated to {new_status}'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)



def quote_detail(request, quote_id):
    """View detailed quote with all items"""
    # Get all quotes with this quote_id
    quotes = Quote.objects.filter(quote_id=quote_id).order_by('id')
    
    if not quotes.exists():
        messages.error(request, 'Quote not found')
        return redirect('dashboard')
    
    first_quote = quotes.first()
    
    # Calculate totals
    subtotal = sum(q.selling_price * q.quantity for q in quotes)
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
    
    return render(request, 'quotes_list.html', context)


def quote_detail(request, quote_id):
    """View quote details"""
    quote = get_object_or_404(Quote, quote_id=quote_id)
    
    context = {
        'quote': quote,
    }
    
    return render(request, 'quote_detail.html', context)



def delete_quote(request, quote_id):
    """Delete a quote"""
    if request.method == 'POST':
        quote = get_object_or_404(Quote, quote_id=quote_id)
        quote.delete()
        messages.success(request, 'Quote deleted successfully')
        return redirect('quotes_list')
    
    return redirect('quotes_list')
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Client, Job, ActivityLog
from .forms import JobForm

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Client, Job, ActivityLog


def create_job(request):
    """Create a new production job - Compatible with current Job model"""
    if request.method == 'POST':
        try:
            # Get client
            client_id = request.POST.get('client_id')
            if not client_id:
                messages.error(request, 'Please select a client')
                return redirect('create_job')
            
            client = get_object_or_404(Client, id=client_id)
            
            # Get basic job details
            job_number = request.POST.get('job_number', '').strip()
            job_name = request.POST.get('job_name', '').strip()
            job_type = request.POST.get('job_type', '').strip()
            person_in_charge = request.POST.get('person_in_charge', '').strip()
            status = request.POST.get('status', 'Pending')
            notes = request.POST.get('notes', '')
            
            # Validation
            if not all([job_name, person_in_charge]):
                messages.error(request, 'Please fill in job name and person in charge')
                return redirect('create_job')
            
            # Collect all products (up to 3)
            products_list = []
            for i in range(1, 4):  # Check products 1, 2, 3
                product_name = request.POST.get(f'product_name_{i}', '').strip()
                if product_name:  # Only process if product name exists
                    quantity = request.POST.get(f'quantity_{i}', '1')
                    unit = request.POST.get(f'unit_{i}', 'pcs')
                    specifications = request.POST.get(f'specifications_{i}', '')
                    
                    products_list.append({
                        'name': product_name,
                        'quantity': quantity,
                        'unit': unit,
                        'specs': specifications
                    })
            
            if not products_list:
                messages.error(request, 'Please add at least one product')
                return redirect('create_job')
            
            # Create job with first product
            main_product = products_list[0]
            
            # Combine product name with job details for the product field
            product_description = f"{job_name} - {main_product['name']}"
            if len(products_list) > 1:
                product_description += f" (+{len(products_list) - 1} more)"
            
            # Create the job
            job = Job.objects.create(
                client=client,
                product=product_description,
                quantity=int(main_product['quantity']),
                person_in_charge=person_in_charge,
                status=status
            )
            
            # Build detailed description for activity log
            job_details = f"Job Number: {job_number}\n"
            job_details += f"Job Name: {job_name}\n"
            job_details += f"Job Type: {job_type}\n"
            job_details += f"Person in Charge: {person_in_charge}\n"
            job_details += f"Status: {status}\n\n"
            
            job_details += "Products:\n"
            for idx, prod in enumerate(products_list, 1):
                job_details += f"{idx}. {prod['name']} - Qty: {prod['quantity']} {prod['unit']}\n"
                if prod['specs']:
                    job_details += f"   Specifications: {prod['specs']}\n"
            
            # Add dates if available
            start_date = request.POST.get('start_date')
            expected_completion = request.POST.get('expected_completion')
            delivery_date = request.POST.get('delivery_date')
            delivery_method = request.POST.get('delivery_method')
            
            if start_date:
                job_details += f"\nStart Date: {start_date}"
            if expected_completion:
                job_details += f"\nExpected Completion: {expected_completion}"
            if delivery_date:
                job_details += f"\nDelivery Date: {delivery_date}"
            if delivery_method:
                job_details += f"\nDelivery Method: {delivery_method}"
            
            # Add notes
            if notes:
                job_details += f"\n\nNotes:\n{notes}"
            
            # Log activity
            ActivityLog.objects.create(
                client=client,
                activity_type='Order',
                title=f"New Job Created - {job_number or job_name}",
                description=job_details,
                created_by=request.user
            )
            
            # Update client's last activity
            client.last_activity = timezone.now()
            client.save()
            
            messages.success(
                request, 
                f"Job '{job_name}' created successfully for {client.name}!"
            )
            return redirect('client_profile', pk=client.id)
            
        except Exception as e:
            messages.error(request, f'Error creating job: {str(e)}')
            import traceback
            print(traceback.format_exc())  # For debugging
            return redirect('create_job')
    
    # GET request - show form
    clients = Client.objects.filter(status='Active').order_by('name')
    
    context = {
        'clients': clients,
        'current_year': timezone.now().year,
    }
    
    return render(request, 'create_job.html', context)


def job_detail(request, pk):
    """View and update an existing job until it’s completed"""
    job = get_object_or_404(Job, pk=pk)
    client = job.client

    if request.method == 'POST':
        try:
            # Basic updates
            job.product = request.POST.get('product', job.product)
            job.quantity = request.POST.get('quantity', job.quantity)
            job.person_in_charge = request.POST.get('person_in_charge', job.person_in_charge)
            job.status = request.POST.get('status', job.status)
            
            # Optional: notes or other fields you had in the form
            notes = request.POST.get('notes', '')
            if notes:
                job.notes = notes

            # Once status hits "Delivery", mark as completed
            if job.status.lower() == "delivery":
                job.is_completed = True

            job.save()

            # Log activity
            ActivityLog.objects.create(
                client=client,
                activity_type='Order Update',
                title=f"Job Updated - {job.product}",
                description=f"Job status updated to {job.status}.",
                created_by=request.user
            )

            messages.success(request, f"Job updated successfully for {client.name}!")
            return redirect('job_detail', pk=job.pk)

        except Exception as e:
            messages.error(request, f"Error updating job: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return redirect('job_detail', pk=job.pk)

    # GET request – show the form pre-filled
    clients = Client.objects.filter(status='Active').order_by('name')

    context = {
        'clients': clients,
        'job': job,
        'is_update': True,  # used in template to switch mode
    }

    return render(request, 'create_job.html', context)


from django.shortcuts import render

def quote_management(request):
    return render(request, 'quote_management.html')

def product_catalog(request):
    return render(request, 'product_catalog.html')

def production_dashboard(request):
    return render(request, 'production_dashboard.html')

def analytics(request):
    return render(request, 'analytics.html')


def base_view(request):
    return render(request, 'base2.html')

def production2_dashboard(request):
    """Production Team Dashboard"""
    return render(request, 'production2_dashboard.html')

def quote_review_queue(request):
    """Quote Review Queue for Production Team"""
    return render(request, 'quote_review.html')

def production_catalog(request):
    """Product Catalog Management"""
    return render(request, 'production_catalog.html')

def production_analytics(request):
    """Analytics Dashboard"""
    return render(request, 'production_analytics.html')
