from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from functools import wraps
from django.conf import settings

from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
from intuitlib.exceptions import AuthClientError

# Import QuickBooks objects
from quickbooks.objects.invoice import Invoice
from quickbooks.objects.customer import Customer
from quickbooks.objects.account import Account
from quickbooks.objects.item import Item

from .models import QuickBooksToken
from .helpers import get_qb_client


def connect_quickbooks(request):
    auth_client = AuthClient(
        client_id=settings.QB_CLIENT_ID,
        client_secret=settings.QB_CLIENT_SECRET,
        environment=settings.QB_ENVIRONMENT,
        redirect_uri=settings.QB_REDIRECT_URI
    )

    auth_url = auth_client.get_authorization_url([Scopes.ACCOUNTING])
    return redirect(auth_url)


@login_required
def quickbooks_callback(request):
    code = request.GET.get('code')
    realm_id = request.GET.get('realmId')

    if not code or not realm_id:
        messages.error(request, "Missing code or realm ID from QuickBooks.")
        return redirect('dashboard')

    auth_client = AuthClient(
        client_id=settings.QB_CLIENT_ID,
        client_secret=settings.QB_CLIENT_SECRET,
        environment=settings.QB_ENVIRONMENT,
        redirect_uri=settings.QB_REDIRECT_URI
    )

    try:
        auth_client.get_bearer_token(code, realm_id=realm_id)
        
        # Tokens are stored on the auth_client object
        access_token = auth_client.access_token
        refresh_token = auth_client.refresh_token
        expires_in = auth_client.expires_in
        
        if not access_token or not refresh_token:
            messages.error(request, "QuickBooks did not return valid tokens.")
            return redirect('dashboard')
        
        # Save or update tokens in DB
        QuickBooksToken.objects.update_or_create(
            user=request.user,
            defaults={
                'access_token': access_token,
                'refresh_token': refresh_token,
                'realm_id': realm_id,
                'expires_at': timezone.now() + timedelta(seconds=expires_in)
            }
        )
        
        messages.success(request, "Successfully connected to QuickBooks!")
        return redirect('accounting_dashboard')
        
    except AuthClientError as e:
        print("QuickBooks OAuth token exchange failed:", e)
        messages.error(request, f"QuickBooks OAuth failed: {e}")
        return redirect('dashboard')


def group_required(group_name, allow_superuser=False):
    """
    Require authenticated user to belong to group_name.
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
            if user.groups.filter(name='Finance').exists():
                fallback_name = 'analytics_dashboard'
            return redirect(reverse(fallback_name))
        return _wrapped
    return decorator


@login_required
@group_required('Production Team')
def accounting_dashboard(request):
    return render(request, 'finance_dashboard.html')

@login_required
@group_required('Production Team')
def analytics_dashboard(request):
    return render(request, 'analytics_dashboard.html')


@login_required
@group_required('Production Team')
def get_invoices(request):
    try:
        client = get_qb_client(request.user)
        
        # Correct way to query invoices
        invoices = Invoice.all(qb=client, max_results=50)
        
        # Convert to list of dictionaries
        data = [invoice.to_dict() for invoice in invoices]
        
        return JsonResponse(data, safe=False)
    except QuickBooksToken.DoesNotExist:
        return JsonResponse({'error': 'QuickBooks not connected'}, status=400)
    except Exception as e:
        print(f"Error fetching invoices: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@group_required('Production Team')
def get_customers(request):
    try:
        client = get_qb_client(request.user)
        customers = Customer.all(qb=client, max_results=100)
        data = [customer.to_dict() for customer in customers]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

import requests
@login_required
@group_required('Production Team')
def get_balance_sheet(request):
    try:
        client = get_qb_client(request.user)
        token_obj = QuickBooksToken.objects.get(user=request.user)
        realm_id = token_obj.realm_id

        url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/reports/BalanceSheet"
        
        params = request.GET.dict()  # optional filters like 'start_date', 'end_date'
        headers = {
            'Authorization': f'Bearer {client.auth_client.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        return JsonResponse(response.json(), safe=False)
        
    except QuickBooksToken.DoesNotExist:
        return JsonResponse({'error': 'QuickBooks not connected'}, status=400)
    except requests.exceptions.HTTPError as e:
        error_message = e.response.text if e.response else str(e)
        return JsonResponse({
            'error': f'QuickBooks API error: {e.response.status_code if e.response else "Unknown"}',
            'message': error_message
        }, status=e.response.status_code if e.response else 500)
    except Exception as e:
        print(f"Error fetching balance sheet: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)



