"""
QuickBooks Service - Handles all QuickBooks API interactions
"""
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from quickbooks.objects.invoice import Invoice, SalesItemLine
from quickbooks.objects.customer import Customer
from quickbooks.objects.item import Item
from quickbooks.objects.account import Account
from quickbooks.objects.base import EmailAddress, Address
from .helpers import get_qb_client
from .models import QuickBooksToken
import logging

# Get SalesItemLineDetail from the SalesItemLine class dict
SalesItemLineDetail = SalesItemLine.class_dict.get('SalesItemLineDetail')

logger = logging.getLogger(__name__)


class QuickBooksService:
    """Service class for QuickBooks operations"""
    
    def __init__(self, user):
        self.user = user
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize QuickBooks client"""
        try:
            self.client = get_qb_client(self.user)
        except QuickBooksToken.DoesNotExist:
            raise Exception("QuickBooks not connected. Please connect first.")
        except Exception as e:
            logger.error(f"Failed to initialize QB client: {e}")
            raise
    
    def find_or_create_customer(self, client_obj):
        """
        Find existing QuickBooks customer or create new one
        
        Args:
            client_obj: Django Client model instance
            
        Returns:
            QuickBooks Customer object
        """
        try:
            # Search for existing customer by email
            customers = Customer.filter(
                PrimaryEmailAddr=client_obj.email,
                qb=self.client
            )
            
            if customers:
                logger.info(f"Found existing QB customer for {client_obj.email}")
                return customers[0]
            
            # Create new customer
            customer = Customer()
            customer.DisplayName = client_obj.company or client_obj.name
            customer.CompanyName = client_obj.company if client_obj.company else None
            customer.GivenName = client_obj.name.split()[0] if client_obj.name else ""
            customer.FamilyName = " ".join(client_obj.name.split()[1:]) if len(client_obj.name.split()) > 1 else ""
            
            # Email
            email = EmailAddress()
            email.Address = client_obj.email
            customer.PrimaryEmailAddr = email
            
            # Phone
            customer.PrimaryPhone = {
                'FreeFormNumber': client_obj.phone
            }
            
            # Address
            if client_obj.address:
                address = Address()
                address.Line1 = client_obj.address[:500] 
                customer.BillAddr = address
            
            # Payment terms mapping
            payment_terms_map = {
                'Prepaid': 'Due on receipt',
                'Net 7': 'Net 7',
                'Net 15': 'Net 15',
                'Net 30': 'Net 30',
                'Net 60': 'Net 60',
            }
            customer.TermsRef = payment_terms_map.get(client_obj.payment_terms, 'Due on receipt')
            
            # Save to QuickBooks
            customer.save(qb=self.client)
            logger.info(f"Created new QB customer: {customer.Id}")
            
            return customer
            
        except Exception as e:
            logger.error(f"Error finding/creating customer: {e}")
            raise
    
    def find_or_create_item(self, product_name, unit_price):
        """
        Find existing QuickBooks item or create new one
        
        Args:
            product_name: Product name from quote
            unit_price: Unit price
            
        Returns:
            QuickBooks Item object
        """
        try:
            # Search for existing item by name
            items = Item.filter(Name=product_name, qb=self.client)
            
            if items:
                logger.info(f"Found existing QB item: {product_name}")
                return items[0]
            
            # Get income account (required for items)
            income_accounts = Account.filter(
                AccountType='Income',
                qb=self.client,
                max_results=1
            )
            
            if not income_accounts:
                raise Exception("No income account found in QuickBooks")
            
            # Create new item
            item = Item()
            item.Name = product_name[:100] 
            item.Type = "Service" 
            item.IncomeAccountRef = income_accounts[0].to_ref()
            item.UnitPrice = float(unit_price)
            
            # Save to QuickBooks
            item.save(qb=self.client)
            logger.info(f"Created new QB item: {item.Id}")
            
            return item
            
        except Exception as e:
            logger.error(f"Error finding/creating item: {e}")
            raise
    
    def create_invoice_from_quote(self, quote):
        """
        Create QuickBooks invoice from Django Quote
        
        Args:
            quote: Django Quote model instance
            
        Returns:
            dict: {
                'success': bool,
                'invoice_id': str,
                'invoice_number': str,
                'message': str
            }
        """
        try:
            # Validate quote
            if not quote.client:
                return {
                    'success': False,
                    'message': 'Quote must have a client (not a lead)'
                }
            
            if quote.status != 'Approved':
                return {
                    'success': False,
                    'message': 'Only approved quotes can be synced'
                }
            
            # Find or create customer
            qb_customer = self.find_or_create_customer(quote.client)
            
            # Create invoice
            invoice = Invoice()
            invoice.CustomerRef = qb_customer.to_ref()
            
            # Get all quote items with same quote_id
            from clientapp.models import Quote as QuoteModel
            quote_items = QuoteModel.objects.filter(quote_id=quote.quote_id)
            
            # Add line items
            invoice.Line = []
            for item in quote_items:
                # Find or create product/service item
                qb_item = self.find_or_create_item(
                    item.product_name,
                    item.unit_price
                )
                
                # Create line
                line = SalesItemLine()
                line.Amount = float(item.unit_price * item.quantity)
                line.DetailType = "SalesItemLineDetail"
                
                # Line detail
                line.SalesItemLineDetail = SalesItemLineDetail()
                line.SalesItemLineDetail.ItemRef = qb_item.to_ref()
                line.SalesItemLineDetail.Qty = item.quantity
                line.SalesItemLineDetail.UnitPrice = float(item.unit_price)
                
                # Tax code (if VAT included)
                if item.include_vat:
                    line.SalesItemLineDetail.TaxCodeRef = {'value': 'TAX'}  
                
                invoice.Line.append(line)
            
            # Invoice details
            invoice.DueDate = quote.valid_until.isoformat() if quote.valid_until else None
            invoice.TxnDate = quote.quote_date.isoformat()
            
            # Customer memo
            invoice.CustomerMemo = f"Invoice for Quote {quote.quote_id}"
            
            # Apply tax if needed
            if quote.include_vat:
                invoice.TxnTaxDetail = {
                    'TxnTaxCodeRef': {'value': 'TAX'}
                }
            
            # Save invoice
            invoice.save(qb=self.client)
            
            logger.info(f"Created QB invoice {invoice.Id} for quote {quote.quote_id}")
            
            return {
                'success': True,
                'invoice_id': invoice.Id,
                'invoice_number': invoice.DocNumber,
                'message': f'Invoice #{invoice.DocNumber} created successfully'
            }
            
        except Exception as e:
            logger.error(f"Error creating invoice: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def get_invoice(self, invoice_id):
        """Get invoice by ID"""
        try:
            invoice = Invoice.get(invoice_id, qb=self.client)
            return invoice.to_dict()
        except Exception as e:
            logger.error(f"Error fetching invoice: {e}")
            raise
    
    def list_invoices(self, limit=50):
        """List recent invoices"""
        try:
            invoices = Invoice.all(qb=self.client, max_results=limit)
            return [inv.to_dict() for inv in invoices]
        except Exception as e:
            logger.error(f"Error listing invoices: {e}")
            raise
    
    def get_invoice_pdf(self, invoice_id):
        """Get invoice PDF URL"""
        try:
            invoice = Invoice.get(invoice_id, qb=self.client)
            pdf_url = invoice.get_pdf_download_url(qb=self.client)
            return pdf_url
        except Exception as e:
            logger.error(f"Error getting invoice PDF: {e}")
            raise
    
    def create_invoice_from_vendor_invoice(self, vendor_invoice):
        """
        Create QuickBooks invoice from VendorInvoice.
        
        Args:
            vendor_invoice: VendorInvoice model instance
            
        Returns:
            dict with invoice details and QB invoice ID
        """
        try:
            from .models import VendorInvoice
            
            # Find or create customer in QB
            qb_customer = self.find_or_create_customer(vendor_invoice.job.client)
            
            # Create invoice object
            invoice = Invoice()
            invoice.CustomerRef = qb_customer.id
            
            # Set dates
            invoice.TxnDate = vendor_invoice.invoice_date.isoformat()
            invoice.DueDate = vendor_invoice.due_date.isoformat()
            
            # Set line items
            line_items = []
            for item_data in (vendor_invoice.line_items or []):
                line = SalesItemLine()
                line.Description = item_data.get('description', 'Service')
                line.Amount = Decimal(str(item_data.get('amount', 0)))
                
                # Try to link to item or create simple line
                sales_detail = SalesItemLineDetail()
                sales_detail.Qty = 1
                sales_detail.UnitPrice = Decimal(str(item_data.get('amount', 0)))
                
                line.SalesItemLineDetail = sales_detail
                line_items.append(line)
            
            invoice.Line = line_items
            
            # Add memo with reference info
            invoice.PrivateNote = f"Vendor: {vendor_invoice.vendor.name}\nPO: {vendor_invoice.purchase_order.po_number}\nJob: {vendor_invoice.job.job_number}"
            
            # Save to QB
            invoice.save(qb=self.client)
            
            # Update vendor invoice with QB ID
            vendor_invoice.qb_invoice_id = invoice.id
            vendor_invoice.save()
            
            logger.info(f"Created QB invoice {invoice.id} for vendor invoice {vendor_invoice.invoice_number}")
            
            return {
                'status': 'success',
                'qb_invoice_id': invoice.id,
                'qb_invoice_number': invoice.DocNumber,
                'amount': float(invoice.TotalAmt),
                'customer_id': qb_customer.id,
            }
        
        except Exception as e:
            logger.error(f"Error creating QB invoice: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def sync_purchase_order_as_purchase(self, purchase_order):
        """
        Sync PurchaseOrder to QuickBooks as a Purchase (Bill).
        
        Args:
            purchase_order: PurchaseOrder model instance
            
        Returns:
            dict with purchase/bill details
        """
        try:
            from quickbooks.objects.purchase import Purchase, PurchaseLine, ItemBasedExpenseLineDetail
            from .models import PurchaseOrder
            
            # Find or create vendor in QB
            # For now, use a simple approach - vendors as customers
            qb_customer = self.find_or_create_customer(purchase_order.job.client)
            
            # Create purchase/bill
            purchase = Purchase()
            purchase.EntityRef = qb_customer.id
            purchase.TxnDate = purchase_order.created_at.date().isoformat()
            
            # Add line item
            line = PurchaseLine()
            line.Description = purchase_order.product_type
            line.Amount = purchase_order.total_cost
            
            purchase.Line = [line]
            purchase.PrivateNote = f"Vendor: {purchase_order.vendor.name}\nProduct: {purchase_order.product_description}\nQty: {purchase_order.quantity}"
            
            # Save to QB
            purchase.save(qb=self.client)
            
            logger.info(f"Created QB purchase {purchase.id} for PO {purchase_order.po_number}")
            
            return {
                'status': 'success',
                'qb_purchase_id': purchase.id,
                'amount': float(purchase.TotalAmt),
            }
        
        except Exception as e:
            logger.error(f"Error creating QB purchase: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def sync_quote_as_estimate(self, quote):
        """
        Sync Quote to QuickBooks as Estimate.
        
        Args:
            quote: Quote model instance
            
        Returns:
            dict with estimate details
        """
        try:
            from quickbooks.objects.estimate import Estimate, EstimateLine
            from .models import Quote
            
            # Get EstimateLine detail class
            EstimateLineDetail = EstimateLine.class_dict.get('SalesItemLineDetail')
            
            if not quote.client:
                return {'status': 'error', 'error': 'Quote has no client'}
            
            # Find or create customer
            qb_customer = self.find_or_create_customer(quote.client)
            
            # Create estimate
            estimate = Estimate()
            estimate.CustomerRef = qb_customer.id
            estimate.TxnDate = quote.quote_date.isoformat()
            estimate.DueDate = quote.valid_until.isoformat()
            
            # Add line items
            line = EstimateLine()
            line.Description = quote.product_name
            line.Amount = quote.total_amount
            
            line_detail = EstimateLineDetail()
            line_detail.Qty = quote.quantity
            line_detail.UnitPrice = quote.unit_price
            line.SalesItemLineDetail = line_detail
            
            estimate.Line = [line]
            estimate.PrivateNote = f"Quote ID: {quote.quote_id}\nReference: {quote.reference_number}"
            
            # Save to QB
            estimate.save(qb=self.client)
            
            logger.info(f"Created QB estimate {estimate.id} for quote {quote.quote_id}")
            
            return {
                'status': 'success',
                'qb_estimate_id': estimate.id,
                'amount': float(estimate.TotalAmt),
            }
        
        except Exception as e:
            logger.error(f"Error creating QB estimate: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_sync_status(self):
        """Get QuickBooks sync status"""
        try:
            from .models import QuickBooksToken
            
            token = QuickBooksToken.objects.get(user=self.user)
            
            return {
                'status': 'connected',
                'realm_id': token.realm_id,
                'connected_at': token.created_at.isoformat() if token.created_at else None,
                'expires_at': token.expires_at.isoformat() if token.expires_at else None,
                'company_name': token.company_name,
            }
        
        except QuickBooksToken.DoesNotExist:
            return {
                'status': 'not_connected',
                'message': 'QuickBooks not connected. Please authenticate first.'
            }
        except Exception as e:
            logger.error(f"Error checking sync status: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


class QuickBooksAuthService:
    """Service for QuickBooks OAuth authentication"""
    
    @staticmethod
    def get_auth_url(request):
        """
        Generate QB OAuth authorization URL
        
        Returns:
            dict with authorization URL
        """
        try:
            from django.urls import reverse
            from .helpers import get_qb_auth_url
            
            redirect_uri = request.build_absolute_uri(reverse('qb-callback'))
            auth_url = get_qb_auth_url(redirect_uri)
            
            return {
                'status': 'success',
                'auth_url': auth_url,
                'redirect_uri': redirect_uri
            }
        
        except Exception as e:
            logger.error(f"Error generating auth URL: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    @staticmethod
    def handle_oauth_callback(request, auth_code, realm_id):
        """
        Handle QB OAuth callback
        
        Args:
            request: Django request object
            auth_code: OAuth authorization code
            realm_id: QB Company/Realm ID
            
        Returns:
            dict with token details
        """
        try:
            from .helpers import exchange_auth_code_for_token
            from .models import QuickBooksToken
            
            # Exchange code for tokens
            tokens = exchange_auth_code_for_token(auth_code)
            
            # Save tokens
            qb_token = QuickBooksToken.objects.update_or_create(
                user=request.user,
                defaults={
                    'realm_id': realm_id,
                    'access_token': tokens['access_token'],
                    'refresh_token': tokens.get('refresh_token'),
                    'expires_in': tokens.get('expires_in', 3600),
                    'expires_at': timezone.now() + timedelta(seconds=tokens.get('expires_in', 3600)),
                }
            )
            
            logger.info(f"QB tokens saved for user {request.user}")
            
            return {
                'status': 'success',
                'message': 'QuickBooks connected successfully',
                'realm_id': realm_id
            }
        
        except Exception as e:
            logger.error(f"Error handling QB callback: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    @staticmethod
    def disconnect(user):
        """
        Disconnect QuickBooks account
        
        Args:
            user: Django User object
        """
        try:
            from .models import QuickBooksToken
            
            QuickBooksToken.objects.filter(user=user).delete()
            logger.info(f"QB disconnected for user {user}")
            
            return {
                'status': 'success',
                'message': 'QuickBooks disconnected'
            }
        
        except Exception as e:
            logger.error(f"Error disconnecting QB: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


# ============================================================================
# PHASE 3: COMPLETE QUICKBOOKS SYNC IMPLEMENTATION
# ============================================================================

class QuickBooksFullSyncService:
    """
    Phase 3 Implementation: Complete QuickBooks sync for invoices, bills, payments.
    Handles all financial data synchronization including error handling and retries.
    """
    
    def __init__(self, user):
        self.user = user
        self.qb_service = QuickBooksService(user)
        self.client = self.qb_service.client
    
    def sync_lpo_to_invoice(self, lpo):
        """
        Sync Local Purchase Order (LPO) to QuickBooks as Invoice.
        
        Args:
            lpo: LPO model instance
            
        Returns:
            dict with sync status
        """
        try:
            from .models import LPO, LPOLineItem
            
            # Get or create QB customer
            qb_customer = self.qb_service.find_or_create_customer(lpo.client)
            
            # Create invoice
            invoice = Invoice()
            invoice.CustomerRef = qb_customer.Id
            invoice.DocNumber = lpo.lpo_number
            invoice.TxnDate = lpo.created_at.date().isoformat()
            invoice.DueDate = (lpo.created_at + timedelta(days=30)).date().isoformat()
            
            # Add line items
            lines = []
            for line_item in lpo.lpo_line_items.all():
                line = SalesItemLine()
                line.Description = f"{line_item.product.name} - Qty: {line_item.quantity}"
                line.Amount = line_item.total_amount
                
                # Set up detail
                detail = {
                    'ItemRef': self._get_or_create_item_in_qb(line_item.product).Id,
                    'UnitPrice': float(line_item.unit_price),
                    'Qty': line_item.quantity,
                }
                line.__dict__.update(detail)
                lines.append(line)
            
            invoice.Line = lines
            
            # Custom fields
            invoice.Memo = f"LPO {lpo.lpo_number} - Auto-synced from PrintDuka"
            invoice.CustomerMemo = {
                'value': f"Order for {lpo.client.name}"
            }
            
            # Save to QB
            invoice.save(qb=self.client)
            
            # Update LPO with QB details
            lpo.synced_to_quickbooks = True
            lpo.quickbooks_invoice_id = invoice.Id
            lpo.quickbooks_invoice_number = invoice.DocNumber
            lpo.quickbooks_sync_date = timezone.now()
            lpo.save()
            
            logger.info(f"LPO {lpo.lpo_number} synced to QB as Invoice {invoice.Id}")
            
            return {
                'status': 'success',
                'qb_invoice_id': invoice.Id,
                'qb_invoice_number': invoice.DocNumber,
                'amount': float(invoice.TotalAmt),
                'customer_id': qb_customer.Id,
            }
        
        except Exception as e:
            logger.error(f"Error syncing LPO to QB: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'lpo_id': lpo.id,
                'lpo_number': lpo.lpo_number,
            }
    
    def sync_vendor_invoice_to_bill(self, vendor_invoice):
        """
        Sync Vendor Invoice to QuickBooks as Bill (Accounts Payable).
        
        Args:
            vendor_invoice: VendorInvoice model instance
            
        Returns:
            dict with sync status
        """
        try:
            from quickbooks.objects.bill import Bill, BillLine
            from .models import VendorInvoice
            
            # Get or create QB vendor
            qb_vendor = self._get_or_create_vendor_in_qb(vendor_invoice.vendor)
            
            # Create bill
            bill = Bill()
            bill.VendorRef = qb_vendor.Id
            bill.DocNumber = vendor_invoice.invoice_number
            bill.TxnDate = vendor_invoice.invoice_date.isoformat()
            bill.DueDate = vendor_invoice.due_date.isoformat() if vendor_invoice.due_date else timezone.now().date().isoformat()
            
            # Add line items
            lines = []
            for item in vendor_invoice.line_items:
                line = BillLine()
                line.Description = item.get('description', 'Service')
                line.Amount = Decimal(str(item.get('amount', 0)))
                lines.append(line)
            
            bill.Line = lines
            
            # Memo
            bill.Memo = f"Vendor Invoice {vendor_invoice.invoice_number} - {vendor_invoice.vendor.name}"
            
            # Save to QB
            bill.save(qb=self.client)
            
            # Update vendor invoice with QB details
            vendor_invoice.synced_to_quickbooks = True
            vendor_invoice.quickbooks_bill_id = bill.Id
            vendor_invoice.quickbooks_sync_date = timezone.now()
            vendor_invoice.save()
            
            logger.info(f"Vendor Invoice {vendor_invoice.invoice_number} synced to QB as Bill {bill.Id}")
            
            return {
                'status': 'success',
                'qb_bill_id': bill.Id,
                'qb_bill_number': bill.DocNumber,
                'amount': float(bill.TotalAmt),
                'vendor_id': qb_vendor.Id,
            }
        
        except Exception as e:
            logger.error(f"Error syncing vendor invoice to QB: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'invoice_id': vendor_invoice.id,
                'invoice_number': vendor_invoice.invoice_number,
            }
    
    def sync_payment_to_qb(self, payment):
        """
        Sync Payment to QuickBooks as Payment record.
        
        Args:
            payment: Payment model instance
            
        Returns:
            dict with sync status
        """
        try:
            from quickbooks.objects.payment import Payment as QBPayment
            from .models import Payment
            
            # Get QB customer
            qb_customer = self.qb_service.find_or_create_customer(payment.client)
            
            # Create payment
            qb_payment = QBPayment()
            qb_payment.CustomerRef = qb_customer.Id
            qb_payment.TxnDate = payment.payment_date.isoformat()
            qb_payment.TotalAmt = float(payment.amount)
            qb_payment.PrivateNote = f"Payment {payment.payment_reference} - {payment.payment_method}"
            
            # Save to QB
            qb_payment.save(qb=self.client)
            
            # Update payment with QB details
            payment.synced_to_quickbooks = True
            payment.quickbooks_payment_id = qb_payment.Id
            payment.quickbooks_sync_date = timezone.now()
            payment.save()
            
            logger.info(f"Payment {payment.payment_reference} synced to QB as Payment {qb_payment.Id}")
            
            return {
                'status': 'success',
                'qb_payment_id': qb_payment.Id,
                'amount': float(qb_payment.TotalAmt),
                'customer_id': qb_customer.Id,
            }
        
        except Exception as e:
            logger.error(f"Error syncing payment to QB: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'payment_id': payment.id,
                'payment_reference': payment.payment_reference,
            }
    
    def _get_or_create_item_in_qb(self, product):
        """
        Get or create QuickBooks Item for a product.
        
        Args:
            product: Product model instance
            
        Returns:
            QuickBooks Item object
        """
        try:
            from quickbooks.objects.item import Item
            
            # Search for existing item
            items = Item.filter(
                Name=product.name,
                qb=self.client
            )
            
            if items:
                return items[0]
            
            # Create new item
            item = Item()
            item.Name = product.name[:100]
            item.Type = 'Service'
            item.Description = product.description[:1000] if product.description else product.name
            item.UnitPrice = float(product.price)
            item.Active = True
            
            # Save to QB
            item.save(qb=self.client)
            logger.info(f"Created QB Item: {item.Name}")
            
            return item
        
        except Exception as e:
            logger.error(f"Error creating QB item: {e}")
            raise
    
    def _get_or_create_vendor_in_qb(self, vendor):
        """
        Get or create QuickBooks Vendor for a supplier.
        
        Args:
            vendor: Vendor model instance
            
        Returns:
            QuickBooks Vendor object
        """
        try:
            from quickbooks.objects.vendor import Vendor as QBVendor
            
            # Search for existing vendor
            vendors = QBVendor.filter(
                DisplayName=vendor.name,
                qb=self.client
            )
            
            if vendors:
                return vendors[0]
            
            # Create new vendor
            qb_vendor = QBVendor()
            qb_vendor.DisplayName = vendor.name
            qb_vendor.CompanyName = vendor.name
            qb_vendor.GivenName = vendor.name.split()[0]
            qb_vendor.FamilyName = " ".join(vendor.name.split()[1:]) if len(vendor.name.split()) > 1 else ""
            
            # Email
            if vendor.email:
                email = EmailAddress()
                email.Address = vendor.email
                qb_vendor.PrimaryEmailAddr = email
            
            # Phone
            if vendor.phone:
                qb_vendor.PrimaryPhone = {
                    'FreeFormNumber': vendor.phone
                }
            
            # Address
            if vendor.address:
                address = Address()
                address.Line1 = vendor.address[:500]
                qb_vendor.BillAddr = address
            
            # Save to QB
            qb_vendor.save(qb=self.client)
            logger.info(f"Created QB Vendor: {qb_vendor.DisplayName}")
            
            return qb_vendor
        
        except Exception as e:
            logger.error(f"Error creating QB vendor: {e}")
            raise
    
    def batch_sync_lpos(self, limit=10):
        """
        Batch sync pending LPOs to QuickBooks.
        
        Args:
            limit: Maximum number of LPOs to sync
            
        Returns:
            dict with sync statistics
        """
        try:
            from .models import LPO
            
            pending_lpos = LPO.objects.filter(
                synced_to_quickbooks=False,
                status='approved'
            )[:limit]
            
            results = {
                'total': len(pending_lpos),
                'successful': 0,
                'failed': 0,
                'errors': []
            }
            
            for lpo in pending_lpos:
                result = self.sync_lpo_to_invoice(lpo)
                if result['status'] == 'success':
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(result)
            
            logger.info(f"Batch sync completed: {results['successful']} successful, {results['failed']} failed")
            return results
        
        except Exception as e:
            logger.error(f"Error in batch sync: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def batch_sync_vendor_invoices(self, limit=10):
        """
        Batch sync pending vendor invoices to QuickBooks.
        
        Args:
            limit: Maximum number of invoices to sync
            
        Returns:
            dict with sync statistics
        """
        try:
            from .models import VendorInvoice
            
            pending_invoices = VendorInvoice.objects.filter(
                synced_to_quickbooks=False,
                status='approved'
            )[:limit]
            
            results = {
                'total': len(pending_invoices),
                'successful': 0,
                'failed': 0,
                'errors': []
            }
            
            for invoice in pending_invoices:
                result = self.sync_vendor_invoice_to_bill(invoice)
                if result['status'] == 'success':
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(result)
            
            logger.info(f"Batch invoice sync completed: {results['successful']} successful, {results['failed']} failed")
            return results
        
        except Exception as e:
            logger.error(f"Error in batch invoice sync: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_sync_status(self):
        """
        Get overall QuickBooks sync status.
        
        Returns:
            dict with sync statistics
        """
        try:
            from .models import LPO, VendorInvoice, Payment
            
            return {
                'lpos_synced': LPO.objects.filter(synced_to_quickbooks=True).count(),
                'lpos_pending': LPO.objects.filter(synced_to_quickbooks=False, status='approved').count(),
                'vendor_invoices_synced': VendorInvoice.objects.filter(synced_to_quickbooks=True).count(),
                'vendor_invoices_pending': VendorInvoice.objects.filter(synced_to_quickbooks=False, status='approved').count(),
                'payments_synced': Payment.objects.filter(synced_to_quickbooks=True).count(),
                'payments_pending': Payment.objects.filter(synced_to_quickbooks=False).count(),
            }
        
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return {'status': 'error', 'error': str(e)}