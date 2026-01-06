"""
QuickBooks Service - Handles all QuickBooks API interactions
"""
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from quickbooks.objects.invoice import Invoice
from quickbooks.objects.customer import Customer
from quickbooks.objects.item import Item
from quickbooks.objects.invoice import InvoiceLine, SalesItemLineDetail
from quickbooks.objects.base import EmailAddress, PhysicalAddress
from .helpers import get_qb_client
from .models import QuickBooksToken
import logging
from quickbooks.objects.account import Account


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
                address = PhysicalAddress()
                address.Line1 = client_obj.address[:500]  # QB has char limits
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
                line = InvoiceLine()
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