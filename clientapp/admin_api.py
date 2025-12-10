"""
Comprehensive CRUD API endpoints for admin dashboard
Handles leads, processes, deliveries, LPOs, payments, QC, vendors, products with:
- Full CRUD operations (create, read, update, delete)
- Permission checks (staff_member_required + POST checks)
- Pagination and filtering
- Error handling and logging
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
import json


def staff_required(view_func):
    """Decorator to check if user is staff"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return JsonResponse({'success': False, 'message': 'Staff access required'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


# ===== CLIENTS CRUD =====
@staff_required
@require_http_methods(["POST"])
def api_admin_create_client(request):
    """Create a new client"""
    from clientapp.models import Client
    
    try:
        # Get all fields from request
        client_type = request.POST.get('client_type', 'B2B')
        name = request.POST.get('name', '').strip()
        company = request.POST.get('company', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        vat_tax_id = request.POST.get('vat_tax_id', '').strip()
        kra_pin = request.POST.get('kra_pin', '').strip()
        address = request.POST.get('address', '').strip()
        industry = request.POST.get('industry', '').strip()
        payment_terms = request.POST.get('payment_terms', 'Prepaid' if client_type == 'B2C' else 'Net 30')
        credit_limit = request.POST.get('credit_limit', 0)
        default_markup = request.POST.get('default_markup', 30)
        risk_rating = request.POST.get('risk_rating', 'Low')
        is_reseller = request.POST.get('is_reseller') == 'on'
        delivery_address = request.POST.get('delivery_address', '').strip()
        delivery_instructions = request.POST.get('delivery_instructions', '').strip()
        preferred_channel = request.POST.get('preferred_channel', 'Email')
        lead_source = request.POST.get('lead_source', '').strip()
        account_manager_id = request.POST.get('account_manager')
        status = request.POST.get('status', 'Active')
        
        # Validation
        if not name:
            return JsonResponse({'success': False, 'message': 'Client name is required'}, status=400)
        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required'}, status=400)
        if not phone:
            return JsonResponse({'success': False, 'message': 'Phone number is required'}, status=400)
        
        # Create client
        client = Client.objects.create(
            client_type=client_type,
            name=name,
            company=company,
            email=email,
            phone=phone,
            vat_tax_id=vat_tax_id,
            kra_pin=kra_pin,
            address=address,
            industry=industry,
            payment_terms=payment_terms,
            credit_limit=credit_limit or 0,
            default_markup=default_markup or 30,
            risk_rating=risk_rating,
            is_reseller=is_reseller,
            delivery_address=delivery_address,
            delivery_instructions=delivery_instructions,
            preferred_channel=preferred_channel,
            lead_source=lead_source,
            status=status,
            account_manager_id=account_manager_id if account_manager_id else None,
            onboarded_by=request.user
        )
        
        # Log activity
        from .models import ActivityLog
        ActivityLog.objects.create(
            activity_type='Client Created',
            title=f'Client {client.name} created',
            description=f'New client {client.name} ({client.client_type}) created by admin',
            client=client,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'id': client.id,
            'message': f'Client {client.name} created successfully'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_required
@require_http_methods(["GET"])
def api_admin_get_client(request, client_id):
    """Get client details for editing"""
    from clientapp.models import Client
    
    try:
        client = Client.objects.get(id=client_id)
        
        return JsonResponse({
            'success': True,
            'id': client.id,
            'client_id': client.client_id,
            'client_type': client.client_type,
            'name': client.name,
            'company': client.company,
            'email': client.email,
            'phone': client.phone,
            'vat_tax_id': client.vat_tax_id,
            'kra_pin': client.kra_pin,
            'address': client.address,
            'industry': client.industry,
            'payment_terms': client.payment_terms,
            'credit_limit': float(client.credit_limit),
            'default_markup': float(client.default_markup),
            'risk_rating': client.risk_rating,
            'is_reseller': client.is_reseller,
            'delivery_address': client.delivery_address or '',
            'delivery_instructions': client.delivery_instructions or '',
            'preferred_channel': client.preferred_channel,
            'lead_source': client.lead_source,
            'account_manager': client.account_manager_id if client.account_manager else None,
            'status': client.status,
        })
    
    except Client.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Client not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_required
@require_http_methods(["POST"])
def api_admin_update_client(request, client_id):
    """Update an existing client"""
    from clientapp.models import Client
    
    try:
        client = Client.objects.get(id=client_id)
        
        # Update all fields
        client.client_type = request.POST.get('client_type', client.client_type)
        client.name = request.POST.get('name', client.name).strip()
        client.company = request.POST.get('company', client.company).strip()
        client.email = request.POST.get('email', client.email).strip()
        client.phone = request.POST.get('phone', client.phone).strip()
        client.vat_tax_id = request.POST.get('vat_tax_id', client.vat_tax_id).strip()
        client.kra_pin = request.POST.get('kra_pin', client.kra_pin).strip()
        client.address = request.POST.get('address', client.address).strip()
        client.industry = request.POST.get('industry', client.industry).strip()
        client.payment_terms = request.POST.get('payment_terms', client.payment_terms)
        client.credit_limit = request.POST.get('credit_limit', client.credit_limit) or 0
        client.default_markup = request.POST.get('default_markup', client.default_markup) or 30
        client.risk_rating = request.POST.get('risk_rating', client.risk_rating)
        client.is_reseller = request.POST.get('is_reseller') == 'on'
        client.delivery_address = request.POST.get('delivery_address', client.delivery_address).strip()
        client.delivery_instructions = request.POST.get('delivery_instructions', client.delivery_instructions).strip()
        client.preferred_channel = request.POST.get('preferred_channel', client.preferred_channel)
        client.lead_source = request.POST.get('lead_source', client.lead_source).strip()
        client.status = request.POST.get('status', client.status)
        
        # Update account manager
        account_manager_id = request.POST.get('account_manager')
        if account_manager_id:
            client.account_manager_id = account_manager_id
        
        client.save()
        
        # Log activity
        from .models import ActivityLog
        ActivityLog.objects.create(
            activity_type='Client Updated',
            title=f'Client {client.name} updated',
            description=f'Client {client.name} was updated by admin',
            client=client,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Client {client.name} updated successfully'
        })
    
    except Client.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Client not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_required
@require_http_methods(["POST"])
def api_admin_delete_client(request, client_id):
    """Delete a client"""
    from clientapp.models import Client
    
    try:
        client = Client.objects.get(id=client_id)
        client_name = client.name
        
        # Log activity before deletion
        from .models import ActivityLog
        ActivityLog.objects.create(
            activity_type='Client Deleted',
            title=f'Client {client_name} deleted',
            description=f'Client {client_name} was deleted by admin',
            client=client,
            created_by=request.user
        )
        
        client.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Client {client_name} deleted successfully'
        })
    
    except Client.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Client not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# ===== LEADS CRUD =====
@staff_required
@require_http_methods(["POST"])
def api_admin_create_lead(request):
    """Create a new lead"""
    from clientapp.models import Lead
    
    try:
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        source = request.POST.get('source', '')
        product_interest = request.POST.get('product_interest', '').strip()
        preferred_contact = request.POST.get('preferred_contact', 'Email')
        follow_up_date = request.POST.get('follow_up_date', '')
        status = request.POST.get('status', 'New')
        notes = request.POST.get('notes', '').strip()
        
        # Validation
        if not name:
            return JsonResponse({'success': False, 'message': 'Lead name is required'}, status=400)
        if not phone:
            return JsonResponse({'success': False, 'message': 'Phone number is required'}, status=400)
        
        # Create lead
        lead = Lead.objects.create(
            name=name,
            email=email,
            phone=phone,
            source=source,
            product_interest=product_interest,
            preferred_contact=preferred_contact,
            follow_up_date=follow_up_date if follow_up_date else None,
            status=status,
            notes=notes,
            created_by=request.user
        )
        
        # Log activity
        from .models import ActivityLog
        ActivityLog.objects.create(
            activity_type='Note',
            title=f'Lead {lead.name} created',
            description=f'New lead {lead.name} created by admin',
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'id': lead.id,
            'message': f'Lead {lead.name} created successfully'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_required
@require_http_methods(["GET"])
def api_admin_get_lead(request, lead_id):
    """Get lead details for editing"""
    from clientapp.models import Lead
    
    try:
        lead = Lead.objects.get(id=lead_id)
        
        return JsonResponse({
            'success': True,
            'id': lead.id,
            'lead_id': lead.lead_id,
            'name': lead.name,
            'email': lead.email,
            'phone': lead.phone,
            'source': lead.source,
            'product_interest': lead.product_interest,
            'preferred_contact': lead.preferred_contact,
            'follow_up_date': lead.follow_up_date.isoformat() if lead.follow_up_date else '',
            'status': lead.status,
            'notes': lead.notes or '',
        })
    
    except Lead.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Lead not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_required
@require_http_methods(["POST"])
def api_admin_update_lead(request, lead_id):
    """Update an existing lead"""
    from clientapp.models import Lead
    
    try:
        lead = Lead.objects.get(id=lead_id)
        
        # Update fields
        lead.name = request.POST.get('name', lead.name).strip()
        lead.email = request.POST.get('email', lead.email).strip()
        lead.phone = request.POST.get('phone', lead.phone).strip()
        lead.source = request.POST.get('source', lead.source)
        lead.product_interest = request.POST.get('product_interest', lead.product_interest).strip()
        lead.preferred_contact = request.POST.get('preferred_contact', lead.preferred_contact)
        lead.status = request.POST.get('status', lead.status)
        lead.notes = request.POST.get('notes', lead.notes).strip()
        
        follow_up_date = request.POST.get('follow_up_date', '')
        if follow_up_date:
            lead.follow_up_date = follow_up_date
        
        lead.save()
        
        # Log activity
        from .models import ActivityLog
        ActivityLog.objects.create(
            activity_type='Note',
            title=f'Lead {lead.name} updated',
            description=f'Lead {lead.name} was updated by admin',
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Lead {lead.name} updated successfully'
        })
    
    except Lead.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Lead not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_required
@require_http_methods(["POST"])
def api_admin_delete_lead(request, lead_id):
    """Delete a lead"""
    from clientapp.models import Lead
    
    try:
        lead = Lead.objects.get(id=lead_id)
        lead_name = lead.name
        
        # Log activity before deletion
        from .models import ActivityLog
        ActivityLog.objects.create(
            activity_type='Note',
            title=f'Lead {lead_name} deleted',
            description=f'Lead {lead_name} was deleted by admin',
            created_by=request.user
        )
        
        lead.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Lead {lead_name} deleted successfully'
        })
    
    except Lead.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Lead not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# ===== QUOTES CRUD =====
@staff_required
@require_http_methods(["POST"])
def api_admin_create_quote(request):
    """Create a new quote"""
    from clientapp.models import Quote, Client, Lead
    
    try:
        product_name = request.POST.get('product_name', '').strip()
        quantity = int(request.POST.get('quantity', 1))
        unit_price = float(request.POST.get('unit_price', 0))
        payment_terms = request.POST.get('payment_terms', 'Prepaid')
        include_vat = request.POST.get('include_vat') == 'on'
        valid_until = request.POST.get('valid_until', '')
        status = request.POST.get('status', 'Draft')
        notes = request.POST.get('notes', '').strip()
        terms = request.POST.get('terms', '').strip()
        client_id = request.POST.get('client')
        lead_id = request.POST.get('lead')
        
        # Validation
        if not product_name:
            return JsonResponse({'success': False, 'message': 'Product name is required'}, status=400)
        if quantity < 1:
            return JsonResponse({'success': False, 'message': 'Quantity must be at least 1'}, status=400)
        
        # Create quote
        quote = Quote.objects.create(
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
            payment_terms=payment_terms,
            include_vat=include_vat,
            valid_until=valid_until if valid_until else None,
            status=status,
            notes=notes,
            terms=terms,
            client_id=client_id if client_id else None,
            lead_id=lead_id if lead_id else None,
            created_by=request.user
        )
        
        # Log activity
        from .models import ActivityLog
        if quote.client:
            ActivityLog.objects.create(
                activity_type='Quote',
                title=f'Quote {quote.quote_id} created for {quote.product_name}',
                description=f'New quote {quote.quote_id} created by admin',
                client=quote.client,
                related_quote=quote,
                created_by=request.user
            )
        
        return JsonResponse({
            'success': True,
            'id': quote.id,
            'message': f'Quote {quote.quote_id} created successfully'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_required
@require_http_methods(["GET"])
def api_admin_get_quote(request, quote_id):
    """Get quote details for editing"""
    from clientapp.models import Quote
    
    try:
        quote = Quote.objects.get(id=quote_id)
        
        return JsonResponse({
            'success': True,
            'id': quote.id,
            'quote_id': quote.quote_id,
            'product_name': quote.product_name,
            'quantity': quote.quantity,
            'unit_price': float(quote.unit_price),
            'total_amount': float(quote.total_amount),
            'payment_terms': quote.payment_terms,
            'include_vat': quote.include_vat,
            'valid_until': quote.valid_until.isoformat() if quote.valid_until else '',
            'status': quote.status,
            'notes': quote.notes or '',
            'terms': quote.terms or '',
            'client': quote.client_id if quote.client else None,
            'lead': quote.lead_id if quote.lead else None,
        })
    
    except Quote.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Quote not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_required
@require_http_methods(["POST"])
def api_admin_update_quote(request, quote_id):
    """Update an existing quote"""
    from clientapp.models import Quote
    
    try:
        quote = Quote.objects.get(id=quote_id)
        
        # Update fields
        quote.product_name = request.POST.get('product_name', quote.product_name).strip()
        quote.quantity = int(request.POST.get('quantity', quote.quantity))
        quote.unit_price = float(request.POST.get('unit_price', quote.unit_price))
        quote.payment_terms = request.POST.get('payment_terms', quote.payment_terms)
        quote.include_vat = request.POST.get('include_vat') == 'on'
        quote.status = request.POST.get('status', quote.status)
        quote.notes = request.POST.get('notes', quote.notes).strip()
        quote.terms = request.POST.get('terms', quote.terms).strip()
        
        valid_until = request.POST.get('valid_until', '')
        if valid_until:
            quote.valid_until = valid_until
        
        client_id = request.POST.get('client')
        if client_id:
            quote.client_id = client_id
        
        lead_id = request.POST.get('lead')
        if lead_id:
            quote.lead_id = lead_id
        
        quote.save()
        
        # Log activity
        from .models import ActivityLog
        if quote.client:
            ActivityLog.objects.create(
                activity_type='Quote',
                title=f'Quote {quote.quote_id} updated',
                description=f'Quote {quote.quote_id} was updated by admin',
                client=quote.client,
                related_quote=quote,
                created_by=request.user
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Quote {quote.quote_id} updated successfully'
        })
    
    except Quote.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Quote not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_required
@require_http_methods(["POST"])
def api_admin_delete_quote(request, quote_id):
    """Delete a quote"""
    from clientapp.models import Quote
    
    try:
        quote = Quote.objects.get(id=quote_id)
        quote_ref = quote.quote_id
        client = quote.client
        
        # Log activity before deletion
        from .models import ActivityLog
        if client:
            ActivityLog.objects.create(
                activity_type='Quote',
                title=f'Quote {quote_ref} deleted',
                description=f'Quote {quote_ref} was deleted by admin',
                client=client,
                created_by=request.user
            )
        
        quote.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Quote {quote_ref} deleted successfully'
        })
    
    except Quote.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Quote not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# ===== PRODUCTS CRUD =====
@staff_required
@require_http_methods(["POST"])
def api_admin_create_product(request):
    """Create a new product"""
    from clientapp.models import Product
    
    try:
        name = request.POST.get('name', '').strip()
        short_description = request.POST.get('short_description', '').strip()
        long_description = request.POST.get('long_description', '').strip()
        technical_specs = request.POST.get('technical_specs', '').strip()
        primary_category = request.POST.get('primary_category', '').strip()
        sub_category = request.POST.get('sub_category', '').strip()
        product_type = request.POST.get('product_type', 'physical')
        product_family = request.POST.get('product_family', '').strip()
        status = request.POST.get('status', 'draft')
        is_visible = request.POST.get('is_visible') == 'on'
        visibility = request.POST.get('visibility', 'catalog-search')
        feature_product = request.POST.get('feature_product') == 'on'
        bestseller_badge = request.POST.get('bestseller_badge') == 'on'
        new_arrival = request.POST.get('new_arrival') == 'on'
        unit_of_measure = request.POST.get('unit_of_measure', 'pieces')
        weight = request.POST.get('weight') or None
        weight_unit = request.POST.get('weight_unit', 'kg')
        length = request.POST.get('length') or None
        width = request.POST.get('width') or None
        height = request.POST.get('height') or None
        dimension_unit = request.POST.get('dimension_unit', 'cm')
        warranty = request.POST.get('warranty', 'satisfaction-guarantee')
        country_of_origin = request.POST.get('country_of_origin', 'kenya')
        internal_notes = request.POST.get('internal_notes', '').strip()
        client_notes = request.POST.get('client_notes', '').strip()
        
        # Validation
        if not name:
            return JsonResponse({'success': False, 'message': 'Product name is required'}, status=400)
        if not short_description:
            return JsonResponse({'success': False, 'message': 'Short description is required'}, status=400)
        
        # Create product
        product = Product.objects.create(
            name=name,
            short_description=short_description,
            long_description=long_description,
            technical_specs=technical_specs,
            primary_category=primary_category,
            sub_category=sub_category,
            product_type=product_type,
            product_family=product_family,
            status=status,
            is_visible=is_visible,
            visibility=visibility,
            feature_product=feature_product,
            bestseller_badge=bestseller_badge,
            new_arrival=new_arrival,
            unit_of_measure=unit_of_measure,
            weight=weight,
            weight_unit=weight_unit,
            length=length,
            width=width,
            height=height,
            dimension_unit=dimension_unit,
            warranty=warranty,
            country_of_origin=country_of_origin,
            internal_notes=internal_notes,
            client_notes=client_notes,
            created_by=request.user,
            updated_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'id': product.id,
            'message': f'Product {product.name} created successfully'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_required
@require_http_methods(["GET"])
def api_admin_get_product(request, product_id):
    """Get product details for editing"""
    from clientapp.models import Product
    
    try:
        product = Product.objects.get(id=product_id)
        
        return JsonResponse({
            'success': True,
            'id': product.id,
            'internal_code': product.internal_code,
            'name': product.name,
            'short_description': product.short_description,
            'long_description': product.long_description,
            'technical_specs': product.technical_specs,
            'primary_category': product.primary_category,
            'sub_category': product.sub_category,
            'product_type': product.product_type,
            'product_family': product.product_family,
            'status': product.status,
            'is_visible': product.is_visible,
            'visibility': product.visibility,
            'feature_product': product.feature_product,
            'bestseller_badge': product.bestseller_badge,
            'new_arrival': product.new_arrival,
            'unit_of_measure': product.unit_of_measure,
            'weight': float(product.weight) if product.weight else None,
            'weight_unit': product.weight_unit,
            'length': float(product.length) if product.length else None,
            'width': float(product.width) if product.width else None,
            'height': float(product.height) if product.height else None,
            'dimension_unit': product.dimension_unit,
            'warranty': product.warranty,
            'country_of_origin': product.country_of_origin,
            'internal_notes': product.internal_notes or '',
            'client_notes': product.client_notes or '',
        })
    
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_required
@require_http_methods(["POST"])
def api_admin_update_product(request, product_id):
    """Update an existing product"""
    from clientapp.models import Product
    
    try:
        product = Product.objects.get(id=product_id)
        
        # Update fields
        product.name = request.POST.get('name', product.name).strip()
        product.short_description = request.POST.get('short_description', product.short_description).strip()
        product.long_description = request.POST.get('long_description', product.long_description).strip()
        product.technical_specs = request.POST.get('technical_specs', product.technical_specs).strip()
        product.primary_category = request.POST.get('primary_category', product.primary_category).strip()
        product.sub_category = request.POST.get('sub_category', product.sub_category).strip()
        product.product_type = request.POST.get('product_type', product.product_type)
        product.product_family = request.POST.get('product_family', product.product_family).strip()
        product.status = request.POST.get('status', product.status)
        product.is_visible = request.POST.get('is_visible') == 'on'
        product.visibility = request.POST.get('visibility', product.visibility)
        product.feature_product = request.POST.get('feature_product') == 'on'
        product.bestseller_badge = request.POST.get('bestseller_badge') == 'on'
        product.new_arrival = request.POST.get('new_arrival') == 'on'
        product.unit_of_measure = request.POST.get('unit_of_measure', product.unit_of_measure)
        product.weight_unit = request.POST.get('weight_unit', product.weight_unit)
        product.dimension_unit = request.POST.get('dimension_unit', product.dimension_unit)
        product.warranty = request.POST.get('warranty', product.warranty)
        product.country_of_origin = request.POST.get('country_of_origin', product.country_of_origin)
        product.internal_notes = request.POST.get('internal_notes', product.internal_notes).strip()
        product.client_notes = request.POST.get('client_notes', product.client_notes).strip()
        product.updated_by = request.user
        
        # Handle numeric fields
        weight = request.POST.get('weight')
        if weight:
            product.weight = float(weight)
        
        length = request.POST.get('length')
        if length:
            product.length = float(length)
        
        width = request.POST.get('width')
        if width:
            product.width = float(width)
        
        height = request.POST.get('height')
        if height:
            product.height = float(height)
        
        product.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Product {product.name} updated successfully'
        })
    
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_required
@require_http_methods(["POST"])
def api_admin_delete_product(request, product_id):
    """Delete a product"""
    from clientapp.models import Product
    
    try:
        product = Product.objects.get(id=product_id)
        product_name = product.name
        
        product.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Product {product_name} deleted successfully'
        })
    
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_required
@require_http_methods(["GET", "POST"])
def api_admin_leads(request):
    """List leads with pagination/filtering or create new lead"""
    from clientapp.models import Lead
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lead = Lead.objects.create(
                lead_name=data.get('lead_name'),
                email=data.get('email'),
                phone=data.get('phone', ''),
                company_name=data.get('company_name', ''),
                status=data.get('status', 'New')
            )
            return JsonResponse({'success': True, 'id': lead.id, 'message': 'Lead created'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    # GET: List with pagination
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    status_filter = request.GET.get('status')
    search = request.GET.get('search', '').strip()
    
    queryset = Lead.objects.all().order_by('-created_at')
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if search:
        queryset = queryset.filter(
            Q(lead_name__icontains=search) |
            Q(email__icontains=search) |
            Q(company_name__icontains=search)
        )
    
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    
    return JsonResponse({
        'success': True,
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page,
        'results': [
            {'id': l.id, 'name': l.lead_name, 'email': l.email, 'status': l.status}
            for l in page_obj
        ]
    })


@staff_required
@require_http_methods(["GET", "PUT", "DELETE"])
def api_admin_lead_detail(request, lead_id):
    """Get, update, or delete a specific lead"""
    from clientapp.models import Lead
    
    lead = get_object_or_404(Lead, id=lead_id)
    
    if request.method == 'GET':
        return JsonResponse({
            'success': True,
            'id': lead.id,
            'name': lead.lead_name,
            'email': lead.email,
            'phone': lead.phone,
            'company': lead.company_name,
            'status': lead.status
        })
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            lead.lead_name = data.get('lead_name', lead.lead_name)
            lead.email = data.get('email', lead.email)
            lead.phone = data.get('phone', lead.phone)
            lead.company_name = data.get('company_name', lead.company_name)
            lead.status = data.get('status', lead.status)
            lead.save()
            return JsonResponse({'success': True, 'message': 'Lead updated'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    elif request.method == 'DELETE':
        lead_name = lead.lead_name
        lead.delete()
        return JsonResponse({'success': True, 'message': f'Lead {lead_name} deleted'})


# ===== PRODUCTS CRUD =====
@staff_required
@require_http_methods(["GET", "POST"])
def api_admin_products(request):
    """List products with pagination or create"""
    from clientapp.models import Product
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product = Product.objects.create(
                name=data.get('name'),
                sku=data.get('sku', ''),
                base_price=data.get('base_price', 0),
                status=data.get('status', 'draft')
            )
            return JsonResponse({'success': True, 'id': product.id, 'message': 'Product created'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    status_filter = request.GET.get('status')
    search = request.GET.get('search', '').strip()
    
    queryset = Product.objects.all().order_by('-created_at')
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if search:
        queryset = queryset.filter(Q(name__icontains=search) | Q(sku__icontains=search))
    
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    
    return JsonResponse({
        'success': True,
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page,
        'results': [
            {'id': p.id, 'name': p.name, 'sku': p.sku, 'price': float(p.base_price), 'status': p.status}
            for p in page_obj
        ]
    })


@staff_required
@require_http_methods(["GET", "PUT", "DELETE"])
def api_admin_product_detail(request, product_id):
    """Get, update, or delete a product"""
    from clientapp.models import Product
    
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'GET':
        return JsonResponse({
            'success': True,
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'price': float(product.base_price),
            'status': product.status
        })
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            product.name = data.get('name', product.name)
            product.sku = data.get('sku', product.sku)
            product.base_price = data.get('base_price', product.base_price)
            product.status = data.get('status', product.status)
            product.save()
            return JsonResponse({'success': True, 'message': 'Product updated'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    elif request.method == 'DELETE':
        product_name = product.name
        product.delete()
        return JsonResponse({'success': True, 'message': f'Product {product_name} deleted'})


# ===== VENDORS CRUD =====
@staff_required
@require_http_methods(["GET", "POST"])
def api_admin_vendors(request):
    """List vendors with pagination or create"""
    from clientapp.models import Vendor
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            vendor = Vendor.objects.create(
                name=data.get('name'),
                email=data.get('email', ''),
                phone=data.get('phone', ''),
                active=data.get('active', True)
            )
            return JsonResponse({'success': True, 'id': vendor.id, 'message': 'Vendor created'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    status_filter = request.GET.get('status')
    search = request.GET.get('search', '').strip()
    
    queryset = Vendor.objects.all().order_by('-created_at')
    if status_filter == 'active':
        queryset = queryset.filter(active=True)
    elif status_filter == 'inactive':
        queryset = queryset.filter(active=False)
    if search:
        queryset = queryset.filter(Q(name__icontains=search) | Q(email__icontains=search))
    
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    
    return JsonResponse({
        'success': True,
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page,
        'results': [
            {'id': v.id, 'name': v.name, 'email': v.email, 'phone': v.phone, 'active': v.active}
            for v in page_obj
        ]
    })


@staff_required
@require_http_methods(["GET", "PUT", "DELETE"])
def api_admin_vendor_detail(request, vendor_id):
    """Get, update, or delete a vendor"""
    from clientapp.models import Vendor
    
    vendor = get_object_or_404(Vendor, id=vendor_id)
    
    if request.method == 'GET':
        return JsonResponse({
            'success': True,
            'id': vendor.id,
            'name': vendor.name,
            'email': vendor.email,
            'phone': vendor.phone,
            'active': vendor.active
        })
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            vendor.name = data.get('name', vendor.name)
            vendor.email = data.get('email', vendor.email)
            vendor.phone = data.get('phone', vendor.phone)
            vendor.active = data.get('active', vendor.active)
            vendor.save()
            return JsonResponse({'success': True, 'message': 'Vendor updated'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    elif request.method == 'DELETE':
        vendor_name = vendor.name
        vendor.delete()
        return JsonResponse({'success': True, 'message': f'Vendor {vendor_name} deleted'})


# ===== LPOS CRUD =====
@staff_required
@require_http_methods(["GET"])
def api_admin_lpos(request):
    """List LPOs with pagination/filtering"""
    from clientapp.models import LPO
    
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    status_filter = request.GET.get('status')
    
    queryset = LPO.objects.select_related('client').order_by('-created_at')
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    
    return JsonResponse({
        'success': True,
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page,
        'results': [
            {
                'id': l.id,
                'lpo_number': l.lpo_number,
                'client': l.client.name if l.client else '',
                'total_amount': float(l.total_amount),
                'status': l.status
            }
            for l in page_obj
        ]
    })


# ===== PAYMENTS CRUD =====
@staff_required
@require_http_methods(["GET"])
def api_admin_payments(request):
    """List payments with pagination"""
    from clientapp.models import Payment
    
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    status_filter = request.GET.get('status')
    
    queryset = Payment.objects.select_related('client').order_by('-created_at')
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    
    return JsonResponse({
        'success': True,
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page,
        'results': [
            {
                'id': p.id,
                'reference': p.reference,
                'client': p.client.name if p.client else '',
                'amount': float(p.amount),
                'status': p.status
            }
            for p in page_obj
        ]
    })


# ===== QC INSPECTIONS CRUD =====
@staff_required
@require_http_methods(["GET"])
def api_admin_qc_inspections(request):
    """List QC inspections with pagination"""
    from clientapp.models import QCInspection
    
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    status_filter = request.GET.get('status')
    
    queryset = QCInspection.objects.select_related('job').order_by('-created_at')
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    
    return JsonResponse({
        'success': True,
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page,
        'results': [
            {
                'id': q.id,
                'job_id': q.job.id if q.job else None,
                'inspector': q.inspector.get_full_name if q.inspector else '',
                'status': q.status
            }
            for q in page_obj
        ]
    })


# ===== DELIVERIES CRUD =====
@staff_required
@require_http_methods(["GET"])
def api_admin_deliveries(request):
    """List deliveries with pagination"""
    from clientapp.models import Delivery
    
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    status_filter = request.GET.get('status')
    
    queryset = Delivery.objects.select_related('job').order_by('-created_at')
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    
    return JsonResponse({
        'success': True,
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page,
        'results': [
            {
                'id': d.id,
                'job_id': d.job.id if d.job else None,
                'recipient_name': d.recipient_name,
                'status': d.status
            }
            for d in page_obj
        ]
    })


# ===== USERS CRUD =====
@staff_required
@require_http_methods(["POST"])
def api_admin_create_user(request):
    """Create a new user"""
    from django.contrib.auth.models import Group, User as DjangoUser
    
    try:
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password = request.POST.get('password', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        groups_list = request.POST.get('groups_list', '[]')
        
        # Validate username
        if not username:
            return JsonResponse({'success': False, 'message': 'Username is required'}, status=400)
        
        if DjangoUser.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'message': 'Username already exists'}, status=400)
        
        # Validate email
        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required'}, status=400)
        
        if DjangoUser.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': 'Email already exists'}, status=400)
        
        # Create user
        user = DjangoUser.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password if password else 'TempPassword123!',
            is_active=is_active,
            is_staff=is_staff,
            is_superuser=is_superuser
        )
        
        # Assign groups
        import json
        try:
            group_ids = json.loads(groups_list)
            groups = Group.objects.filter(id__in=group_ids)
            user.groups.set(groups)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Log activity
        from .models import ActivityLog
        ActivityLog.objects.create(
            activity_type='User Created',
            title=f'User {username} created',
            description=f'User account {username} was created by admin',
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'id': user.id,
            'message': f'User {username} created successfully'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_required
@require_http_methods(["GET"])
def api_admin_get_user(request, user_id):
    """Get user details for editing"""
    from django.contrib.auth.models import User as DjangoUser
    
    try:
        user = DjangoUser.objects.get(id=user_id)
        
        return JsonResponse({
            'success': True,
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'groups': list(user.groups.values_list('id', flat=True))
        })
    
    except DjangoUser.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_required
@require_http_methods(["POST"])
def api_admin_update_user(request, user_id):
    """Update an existing user"""
    from django.contrib.auth.models import Group, User as DjangoUser
    
    try:
        user = DjangoUser.objects.get(id=user_id)
        
        # Update basic fields
        email = request.POST.get('email', user.email).strip()
        first_name = request.POST.get('first_name', user.first_name).strip()
        last_name = request.POST.get('last_name', user.last_name).strip()
        
        # Validate email uniqueness
        if email != user.email and DjangoUser.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': 'Email already in use'}, status=400)
        
        # Update password if provided
        password = request.POST.get('password', '').strip()
        
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.is_active = request.POST.get('is_active') == 'on'
        user.is_staff = request.POST.get('is_staff') == 'on'
        user.is_superuser = request.POST.get('is_superuser') == 'on'
        
        if password:
            user.set_password(password)
        
        user.save()
        
        # Update groups
        groups_list = request.POST.get('groups_list', '[]')
        import json
        try:
            group_ids = json.loads(groups_list)
            groups = Group.objects.filter(id__in=group_ids)
            user.groups.set(groups)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Log activity
        from .models import ActivityLog
        ActivityLog.objects.create(
            activity_type='User Updated',
            title=f'User {user.username} updated',
            description=f'User account {user.username} was updated by admin',
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': f'User {user.username} updated successfully'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@staff_required
@require_http_methods(["POST"])
def api_admin_delete_user(request, user_id):
    """Delete a user"""
    from django.contrib.auth.models import User as DjangoUser
    
    try:
        user = DjangoUser.objects.get(id=user_id)
        
        # Prevent deleting the current user
        if user.id == request.user.id:
            return JsonResponse({
                'success': False,
                'message': 'You cannot delete your own user account'
            }, status=400)
        
        username = user.username
        
        # Log activity before deletion
        from .models import ActivityLog
        ActivityLog.objects.create(
            activity_type='User Deleted',
            title=f'User {username} deleted',
            description=f'User account {username} was deleted by admin',
            created_by=request.user
        )
        
        user.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'User {username} deleted successfully'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

