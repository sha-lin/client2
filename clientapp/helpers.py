from intuitlib.client import AuthClient
from quickbooks import QuickBooks
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import QuickBooksToken
import os

def get_qb_client(user):
    """
    Returns an authenticated QuickBooks client for the given user.
    """
    # FOR DEVELOPMENT ONLY - Allow OAuth over HTTP
    if settings.DEBUG:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    token = QuickBooksToken.objects.get(user=user)

    auth_client = AuthClient(
        client_id=settings.QB_CLIENT_ID,
        client_secret=settings.QB_CLIENT_SECRET,
        environment=settings.QB_ENVIRONMENT,
        redirect_uri=settings.QB_REDIRECT_URI,
    )

    # Set tokens
    auth_client.access_token = token.access_token
    auth_client.refresh_token = token.refresh_token

    # Refresh if expired or expiring soon (within 5 minutes)
    if token.expires_at <= timezone.now() + timedelta(minutes=5):
        try:
            auth_client.refresh()
            
            # Update stored tokens
            token.access_token = auth_client.access_token
            token.refresh_token = auth_client.refresh_token
            token.expires_at = timezone.now() + timedelta(seconds=auth_client.expires_in)
            token.save()
        except Exception as e:
            print(f"Token refresh failed: {e}")
            raise

    # QuickBooks client
    client = QuickBooks(
        auth_client=auth_client,
        refresh_token=token.refresh_token,
        company_id=token.realm_id
    )

    return client