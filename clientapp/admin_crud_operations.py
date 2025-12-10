"""
Admin CRUD Operations - Django Admin-style views for all models
Implements full CRUD functionality (List, Detail, Add, Edit, Delete) for each model
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Q, Count
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse

from .models import (
    Client, Lead, Quote, Product, Job, Vendor, Process, LPO,
    Payment, User
)
from .forms import (
    ClientForm, LeadForm, QuoteForm, ProductForm
)


# ==================== CLIENTS ====================

@staff_member_required
def admin_clients_list(request):
    """Display all clients in admin list view"""
    search = request.GET.get('q', '')
    status = request.GET.get('status', '')
    page = request.GET.get('page', 1)
    
    queryset = Client.objects.all()
    
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search) |
            Q(client_id__icontains=search)
        )
    
    if status:
        queryset = queryset.filter(status=status)
    
    queryset = queryset.order_by('-created_at')
    paginator = Paginator(queryset, 25)
    
    try:
        page_obj = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)
    
    context = {
        'title': 'Clients',
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'total_count': queryset.count(),
        'add_url': reverse('admin_client_add'),
    }
    return render(request, 'admin/clients_list.html', context)


@staff_member_required
def admin_client_detail(request, pk):
    """View/Edit a client"""
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, f'Client "{client.name}" updated successfully')
            return redirect('admin_client_detail', pk=client.pk)
    else:
        form = ClientForm(instance=client)
    
    context = {
        'object': client,
        'form': form,
        'title': f'Edit Client: {client.name}',
    }
    return render(request, 'admin/detail_view.html', context)


@staff_member_required
def admin_client_add(request):
    """Add a new client"""
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, f'Client "{client.name}" created successfully')
            return redirect('admin_client_detail', pk=client.pk)
    else:
        form = ClientForm()
    
    context = {
        'form': form,
        'title': 'Add Client',
        'is_add': True,
    }
    return render(request, 'admin/detail_view.html', context)


@staff_member_required
def admin_client_delete(request, pk):
    """Delete a client"""
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        client_name = client.name
        client.delete()
        messages.success(request, f'Client "{client_name}" deleted successfully')
        return redirect('admin_clients_list')
    
    context = {
        'object': client,
        'title': f'Delete Client: {client.name}',
    }
    return render(request, 'admin/delete_confirm.html', context)


# ==================== LEADS ====================

@staff_member_required
def admin_leads_list(request):
    """Display all leads in admin list view"""
    search = request.GET.get('q', '')
    status = request.GET.get('status', '')
    source = request.GET.get('source', '')
    page = request.GET.get('page', 1)
    
    queryset = Lead.objects.all()
    
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search) |
            Q(lead_id__icontains=search)
        )
    
    if status:
        queryset = queryset.filter(status=status)
    if source:
        queryset = queryset.filter(source=source)
    
    queryset = queryset.order_by('-created_at')
    paginator = Paginator(queryset, 25)
    
    try:
        page_obj = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)
    
    context = {
        'title': 'Leads',
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'source': source,
        'total_count': queryset.count(),
        'add_url': reverse('admin_lead_add'),
    }
    return render(request, 'admin/leads_list.html', context)


@staff_member_required
def admin_lead_detail(request, pk):
    """View/Edit a lead"""
    lead = get_object_or_404(Lead, pk=pk)
    
    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            messages.success(request, f'Lead "{lead.name}" updated successfully')
            return redirect('admin_lead_detail', pk=lead.pk)
    else:
        form = LeadForm(instance=lead)
    
    context = {
        'object': lead,
        'form': form,
        'title': f'Edit Lead: {lead.name}',
    }
    return render(request, 'admin/detail_view.html', context)


@staff_member_required
def admin_lead_add(request):
    """Add a new lead"""
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            lead = form.save(commit=False)
            lead.created_by = request.user
            lead.save()
            messages.success(request, f'Lead "{lead.name}" created successfully')
            return redirect('admin_lead_detail', pk=lead.pk)
    else:
        form = LeadForm()
    
    context = {
        'form': form,
        'title': 'Add Lead',
        'is_add': True,
    }
    return render(request, 'admin/detail_view.html', context)


@staff_member_required
def admin_lead_delete(request, pk):
    """Delete a lead"""
    lead = get_object_or_404(Lead, pk=pk)
    
    if request.method == 'POST':
        lead_name = lead.name
        lead.delete()
        messages.success(request, f'Lead "{lead_name}" deleted successfully')
        return redirect('admin_leads_list')
    
    context = {
        'object': lead,
        'title': f'Delete Lead: {lead.name}',
    }
    return render(request, 'admin/delete_confirm.html', context)


# ==================== QUOTES ====================

@staff_member_required
def admin_quotes_list(request):
    """Display all quotes in admin list view"""
    search = request.GET.get('q', '')
    status = request.GET.get('status', '')
    page = request.GET.get('page', 1)
    
    queryset = Quote.objects.all()
    
    if search:
        queryset = queryset.filter(
            Q(quote_id__icontains=search) |
            Q(product_name__icontains=search) |
            Q(client__name__icontains=search)
        )
    
    if status:
        queryset = queryset.filter(status=status)
    
    queryset = queryset.order_by('-quote_date')
    paginator = Paginator(queryset, 25)
    
    try:
        page_obj = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)
    
    context = {
        'title': 'Quotes',
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'total_count': queryset.count(),
        'add_url': reverse('admin_quote_add'),
    }
    return render(request, 'admin/quotes_list.html', context)


@staff_member_required
def admin_quote_detail(request, pk):
    """View/Edit a quote"""
    quote = get_object_or_404(Quote, pk=pk)
    
    if request.method == 'POST':
        form = QuoteForm(request.POST, instance=quote)
        if form.is_valid():
            form.save()
            messages.success(request, f'Quote "{quote.quote_id}" updated successfully')
            return redirect('admin_quote_detail', pk=quote.pk)
    else:
        form = QuoteForm(instance=quote)
    
    context = {
        'object': quote,
        'form': form,
        'title': f'Edit Quote: {quote.quote_id}',
    }
    return render(request, 'admin/detail_view.html', context)


@staff_member_required
def admin_quote_add(request):
    """Add a new quote"""
    if request.method == 'POST':
        form = QuoteForm(request.POST)
        if form.is_valid():
            quote = form.save(commit=False)
            quote.created_by = request.user
            quote.save()
            messages.success(request, f'Quote "{quote.quote_id}" created successfully')
            return redirect('admin_quote_detail', pk=quote.pk)
    else:
        form = QuoteForm()
    
    context = {
        'form': form,
        'title': 'Add Quote',
        'is_add': True,
    }
    return render(request, 'admin/detail_view.html', context)


@staff_member_required
def admin_quote_delete(request, pk):
    """Delete a quote"""
    quote = get_object_or_404(Quote, pk=pk)
    
    if request.method == 'POST':
        quote_id = quote.quote_id
        quote.delete()
        messages.success(request, f'Quote "{quote_id}" deleted successfully')
        return redirect('admin_quotes_list')
    
    context = {
        'object': quote,
        'title': f'Delete Quote: {quote.quote_id}',
    }
    return render(request, 'admin/delete_confirm.html', context)


# ==================== PRODUCTS ====================

@staff_member_required
def admin_products_list(request):
    """Display all products in admin list view"""
    search = request.GET.get('q', '')
    category = request.GET.get('category', '')
    page = request.GET.get('page', 1)
    
    queryset = Product.objects.all()
    
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(product_id__icontains=search) |
            Q(description__icontains=search)
        )
    
    if category:
        queryset = queryset.filter(product_category=category)
    
    queryset = queryset.order_by('-created_at')
    paginator = Paginator(queryset, 25)
    
    try:
        page_obj = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)
    
    context = {
        'title': 'Products',
        'page_obj': page_obj,
        'search': search,
        'category': category,
        'total_count': queryset.count(),
        'add_url': reverse('admin_product_add'),
    }
    return render(request, 'admin/products_list.html', context)


@staff_member_required
def admin_product_detail(request, pk):
    """View/Edit a product"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Product "{product.name}" updated successfully')
            return redirect('admin_product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)
    
    context = {
        'object': product,
        'form': form,
        'title': f'Edit Product: {product.name}',
    }
    return render(request, 'admin/detail_view.html', context)


@staff_member_required
def admin_product_add(request):
    """Add a new product"""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" created successfully')
            return redirect('admin_product_detail', pk=product.pk)
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'title': 'Add Product',
        'is_add': True,
    }
    return render(request, 'admin/detail_view.html', context)


@staff_member_required
def admin_product_delete(request, pk):
    """Delete a product"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully')
        return redirect('admin_products_list')
    
    context = {
        'object': product,
        'title': f'Delete Product: {product.name}',
    }
    return render(request, 'admin/delete_confirm.html', context)


# ==================== JOBS ====================

@staff_member_required
def admin_jobs_list(request):
    """Display all jobs in admin list view"""
    search = request.GET.get('q', '')
    status = request.GET.get('status', '')
    page = request.GET.get('page', 1)
    
    queryset = Job.objects.all()
    
    if search:
        queryset = queryset.filter(
            Q(job_number__icontains=search) |
            Q(quote__quote_id__icontains=search)
        )
    
    if status:
        queryset = queryset.filter(job_status=status)
    
    queryset = queryset.order_by('-created_at')
    paginator = Paginator(queryset, 25)
    
    try:
        page_obj = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)
    
    context = {
        'title': 'Jobs',
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'total_count': queryset.count(),
    }
    return render(request, 'admin/jobs_list.html', context)


# @staff_member_required
# def admin_job_detail(request, pk):
#     """View/Edit a job"""
#     job = get_object_or_404(Job, pk=pk)
#     
#     if request.method == 'POST':
#         form = JobForm(request.POST, instance=job)
#         if form.is_valid():
#             form.save()
#             messages.success(request, f'Job "{job.job_number}" updated successfully')
#             return redirect('admin_job_detail', pk=job.pk)
#     else:
#         form = JobForm(instance=job)
#     
#     context = {
#         'object': job,
#         'form': form,
#         'title': f'Edit Job: {job.job_number}',
#     }
#     return render(request, 'admin/detail_view.html', context)


# @staff_member_required
# def admin_job_add(request):
#     """Add a new job"""
#     if request.method == 'POST':
#         form = JobForm(request.POST)
#         if form.is_valid():
#             job = form.save(commit=False)
#             job.created_by = request.user
#             job.save()
#             messages.success(request, f'Job "{job.job_number}" created successfully')
#             return redirect('admin_job_detail', pk=job.pk)
#     else:
#         form = JobForm()
#     
#     context = {
#         'form': form,
#         'title': 'Add Job',
#         'is_add': True,
#     }
#     return render(request, 'admin/detail_view.html', context)


# JobForm not available - these views are disabled
# @staff_member_required
# def admin_job_detail(request, pk):
#     """View/Edit a job - DISABLED: JobForm not found"""
#     pass

# @staff_member_required
# def admin_job_add(request):
#     """Add a new job - DISABLED: JobForm not found"""
#     pass

# @staff_member_required
# def admin_job_delete(request, pk):
#     """Delete a job - DISABLED: JobForm not found"""
#     pass




# ==================== VENDORS ====================

@staff_member_required
def admin_vendors_list(request):
    """Display all vendors in admin list view"""
    search = request.GET.get('q', '')
    status = request.GET.get('status', '')
    page = request.GET.get('page', 1)
    
    queryset = Vendor.objects.all()
    
    if search:
        queryset = queryset.filter(
            Q(vendor_id__icontains=search) |
            Q(name__icontains=search) |
            Q(email__icontains=search)
        )
    
    if status:
        queryset = queryset.filter(status=status)
    
    queryset = queryset.order_by('-created_at')
    paginator = Paginator(queryset, 25)
    
    try:
        page_obj = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)
    
    context = {
        'title': 'Vendors',
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'total_count': queryset.count(),
    }
    return render(request, 'admin/vendors_list.html', context)


# VendorForm not available - these views are disabled
# @staff_member_required
# def admin_vendor_detail(request, pk):
#     """View/Edit a vendor - DISABLED: VendorForm not found"""
#     pass

# @staff_member_required
# def admin_vendor_add(request):
#     """Add a new vendor - DISABLED: VendorForm not found"""
#     pass

# @staff_member_required
# def admin_vendor_delete(request, pk):
#     """Delete a vendor - DISABLED: VendorForm not found"""
#     pass



# ==================== PROCESSES ====================

@staff_member_required
def admin_processes_list(request):
    """Display all processes in admin list view"""
    search = request.GET.get('q', '')
    status = request.GET.get('status', '')
    page = request.GET.get('page', 1)
    
    queryset = Process.objects.all()
    
    if search:
        queryset = queryset.filter(
            Q(process_code__icontains=search) |
            Q(process_name__icontains=search)
        )
    
    if status:
        queryset = queryset.filter(is_active=status.lower() == 'active')
    
    queryset = queryset.order_by('-created_at')
    paginator = Paginator(queryset, 25)
    
    try:
        page_obj = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)
    
    context = {
        'title': 'Processes',
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'total_count': queryset.count(),
    }
    return render(request, 'admin/processes_list.html', context)


# ProcessForm not available - these views are disabled
# @staff_member_required
# def admin_process_detail(request, pk):
#     """View/Edit a process - DISABLED: ProcessForm not found"""
#     pass

# @staff_member_required
# def admin_process_add(request):
#     """Add a new process - DISABLED: ProcessForm not found"""
#     pass

# @staff_member_required
# def admin_process_delete(request, pk):
#     """Delete a process - DISABLED: ProcessForm not found"""
#     pass



# ==================== LPOS ====================

@staff_member_required
def admin_lpos_list(request):
    """Display all LPOs in admin list view"""
    search = request.GET.get('q', '')
    status = request.GET.get('status', '')
    page = request.GET.get('page', 1)
    
    queryset = LPO.objects.all()
    
    if search:
        queryset = queryset.filter(
            Q(lpo_number__icontains=search) |
            Q(client__name__icontains=search)
        )
    
    if status:
        queryset = queryset.filter(status=status)
    
    queryset = queryset.order_by('-created_at')
    paginator = Paginator(queryset, 25)
    
    try:
        page_obj = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)
    
    context = {
        'title': 'LPOs',
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'total_count': queryset.count(),
        'add_url': reverse('admin_lpo_add'),
    }
    return render(request, 'admin/lpos_list.html', context)


@staff_member_required
def admin_lpo_detail(request, pk):
    """View/Edit an LPO"""
    lpo = get_object_or_404(LPO, pk=pk)
    
    if request.method == 'POST':
        form = LPO_Form(request.POST, instance=lpo)
        if form.is_valid():
            form.save()
            messages.success(request, f'LPO "{lpo.lpo_number}" updated successfully')
            return redirect('admin_lpo_detail', pk=lpo.pk)
    else:
        from .forms import LPO_Form
        form = LPO_Form(instance=lpo)
    
    context = {
        'object': lpo,
        'form': form,
        'title': f'Edit LPO: {lpo.lpo_number}',
    }
    return render(request, 'admin/detail_view.html', context)


@staff_member_required
def admin_lpo_add(request):
    """Add a new LPO"""
    from .forms import LPO_Form
    
    if request.method == 'POST':
        form = LPO_Form(request.POST)
        if form.is_valid():
            lpo = form.save(commit=False)
            lpo.created_by = request.user
            lpo.save()
            messages.success(request, f'LPO "{lpo.lpo_number}" created successfully')
            return redirect('admin_lpo_detail', pk=lpo.pk)
    else:
        form = LPO_Form()
    
    context = {
        'form': form,
        'title': 'Add LPO',
        'is_add': True,
    }
    return render(request, 'admin/detail_view.html', context)


@staff_member_required
def admin_lpo_delete(request, pk):
    """Delete an LPO"""
    lpo = get_object_or_404(LPO, pk=pk)
    
    if request.method == 'POST':
        lpo_number = lpo.lpo_number
        lpo.delete()
        messages.success(request, f'LPO "{lpo_number}" deleted successfully')
        return redirect('admin_lpos_list')
    
    context = {
        'object': lpo,
        'title': f'Delete LPO: {lpo.lpo_number}',
    }
    return render(request, 'admin/delete_confirm.html', context)


# ==================== PAYMENTS ====================

@staff_member_required
def admin_payments_list(request):
    """Display all payments in admin list view"""
    search = request.GET.get('q', '')
    status = request.GET.get('status', '')
    page = request.GET.get('page', 1)
    
    queryset = Payment.objects.all()
    
    if search:
        queryset = queryset.filter(
            Q(payment_id__icontains=search) |
            Q(client__name__icontains=search)
        )
    
    if status:
        queryset = queryset.filter(status=status)
    
    queryset = queryset.order_by('-created_at')
    paginator = Paginator(queryset, 25)
    
    try:
        page_obj = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)
    
    context = {
        'title': 'Payments',
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'total_count': queryset.count(),
        'add_url': reverse('admin_payment_add'),
    }
    return render(request, 'admin/payments_list.html', context)


@staff_member_required
def admin_payment_detail(request, pk):
    """View/Edit a payment"""
    payment = get_object_or_404(Payment, pk=pk)
    
    if request.method == 'POST':
        from .forms import PaymentForm
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, f'Payment "{payment.payment_id}" updated successfully')
            return redirect('admin_payment_detail', pk=payment.pk)
    else:
        from .forms import PaymentForm
        form = PaymentForm(instance=payment)
    
    context = {
        'object': payment,
        'form': form,
        'title': f'Edit Payment: {payment.payment_id}',
    }
    return render(request, 'admin/detail_view.html', context)


@staff_member_required
def admin_payment_add(request):
    """Add a new payment"""
    from .forms import PaymentForm
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save()
            messages.success(request, f'Payment "{payment.payment_id}" created successfully')
            return redirect('admin_payment_detail', pk=payment.pk)
    else:
        form = PaymentForm()
    
    context = {
        'form': form,
        'title': 'Add Payment',
        'is_add': True,
    }
    return render(request, 'admin/detail_view.html', context)


@staff_member_required
def admin_payment_delete(request, pk):
    """Delete a payment"""
    payment = get_object_or_404(Payment, pk=pk)
    
    if request.method == 'POST':
        payment_id = payment.payment_id
        payment.delete()
        messages.success(request, f'Payment "{payment_id}" deleted successfully')
        return redirect('admin_payments_list')
    
    context = {
        'object': payment,
        'title': f'Delete Payment: {payment.payment_id}',
    }
    return render(request, 'admin/delete_confirm.html', context)


# ==================== USERS ====================

@staff_member_required
def admin_users_list(request):
    """Display all users in admin list view"""
    search = request.GET.get('q', '')
    is_staff = request.GET.get('is_staff', '')
    page = request.GET.get('page', 1)
    
    queryset = User.objects.all()
    
    if search:
        queryset = queryset.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    if is_staff:
        queryset = queryset.filter(is_staff=is_staff.lower() == 'true')
    
    queryset = queryset.order_by('-date_joined')
    paginator = Paginator(queryset, 25)
    
    try:
        page_obj = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)
    
    context = {
        'title': 'Users',
        'page_obj': page_obj,
        'search': search,
        'is_staff': is_staff,
        'total_count': queryset.count(),
        'add_url': reverse('admin_user_add'),
    }
    return render(request, 'admin/users_list.html', context)


@staff_member_required
def admin_user_detail(request, pk):
    """View/Edit a user"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        from django.contrib.auth.forms import UserChangeForm
        form = UserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User "{user.username}" updated successfully')
            return redirect('admin_user_detail', pk=user.pk)
    else:
        from django.contrib.auth.forms import UserChangeForm
        form = UserChangeForm(instance=user)
    
    context = {
        'object': user,
        'form': form,
        'title': f'Edit User: {user.username}',
    }
    return render(request, 'admin/detail_view.html', context)


@staff_member_required
def admin_user_add(request):
    """Add a new user"""
    from django.contrib.auth.forms import UserCreationForm
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User "{user.username}" created successfully')
            return redirect('admin_user_detail', pk=user.pk)
    else:
        form = UserCreationForm()
    
    context = {
        'form': form,
        'title': 'Add User',
        'is_add': True,
    }
    return render(request, 'admin/detail_view.html', context)


@staff_member_required
def admin_user_delete(request, pk):
    """Delete a user"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User "{username}" deleted successfully')
        return redirect('admin_users_list')
    
    context = {
        'object': user,
        'title': f'Delete User: {user.username}',
    }
    return render(request, 'admin/delete_confirm.html', context)


# ==================== VIEW-ONLY LIST VIEWS ====================

@staff_member_required
def admin_qc_list(request):
    """Display all QC records (view only)"""
    search = request.GET.get('q', '')
    status = request.GET.get('status', '')
    page = request.GET.get('page', 1)
    
    from .models import QC
    queryset = QC.objects.all()
    
    if search:
        queryset = queryset.filter(
            Q(qc_id__icontains=search) |
            Q(job__job_number__icontains=search)
        )
    
    if status:
        queryset = queryset.filter(status=status)
    
    queryset = queryset.order_by('-created_at')
    paginator = Paginator(queryset, 25)
    
    try:
        page_obj = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)
    
    context = {
        'title': 'QC Records',
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'total_count': queryset.count(),
    }
    return render(request, 'admin/qc_list.html', context)


@staff_member_required
def admin_deliveries_list(request):
    """Display all deliveries (view only)"""
    search = request.GET.get('q', '')
    status = request.GET.get('status', '')
    page = request.GET.get('page', 1)
    
    from .models import Delivery
    queryset = Delivery.objects.all()
    
    if search:
        queryset = queryset.filter(
            Q(delivery_id__icontains=search) |
            Q(job__job_number__icontains=search)
        )
    
    if status:
        queryset = queryset.filter(status=status)
    
    queryset = queryset.order_by('-created_at')
    paginator = Paginator(queryset, 25)
    
    try:
        page_obj = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)
    
    context = {
        'title': 'Deliveries',
        'page_obj': page_obj,
        'search': search,
        'status': status,
        'total_count': queryset.count(),
    }
    return render(request, 'admin/deliveries_list.html', context)


@staff_member_required
def admin_alerts_list(request):
    """Display all system alerts (view only)"""
    search = request.GET.get('q', '')
    severity = request.GET.get('severity', '')
    page = request.GET.get('page', 1)
    
    from .models import Alert
    queryset = Alert.objects.all()
    
    if search:
        queryset = queryset.filter(
            Q(message__icontains=search) |
            Q(alert_type__icontains=search)
        )
    
    if severity:
        queryset = queryset.filter(severity=severity)
    
    queryset = queryset.order_by('-created_at')
    paginator = Paginator(queryset, 25)
    
    try:
        page_obj = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)
    
    context = {
        'title': 'System Alerts',
        'page_obj': page_obj,
        'search': search,
        'severity': severity,
        'total_count': queryset.count(),
    }
    return render(request, 'admin/alerts_list.html', context)
