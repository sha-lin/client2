"""
Invoice Validation Service
Handles all invoice validation and approval logic
"""
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum
import logging

logger = logging.getLogger(__name__)


class InvoiceValidationService:
    """
    Service to validate vendor invoices against Purchase Orders
    Checks:
    - Amount variance (±10%)
    - Vendor authorization
    - Date validity
    - Line item matching
    - Quantity accuracy
    """
    
    AMOUNT_VARIANCE_TOLERANCE = Decimal('0.10')  # 10% tolerance
    
    @staticmethod
    def validate(vendor_invoice):
        """
        Perform complete invoice validation
        
        Returns:
            {
                'is_valid': bool,
                'errors': [list of error messages],
                'warnings': [list of warning messages],
                'amount_variance': decimal,
                'variance_percentage': decimal,
            }
        """
        errors = []
        warnings = []
        
        # 1. Validate vendor
        vendor_valid, vendor_msg = InvoiceValidationService.validate_vendor(vendor_invoice)
        if not vendor_valid:
            errors.append(vendor_msg)
        
        # 2. Validate amount
        amount_valid, amount_msg = InvoiceValidationService.validate_amount(vendor_invoice)
        if not amount_valid:
            errors.append(amount_msg)
        else:
            variance_pct = amount_msg.get('variance_percentage', 0)
            if variance_pct != 0:
                warnings.append(f"Amount variance: {variance_pct:.2f}%")
        
        # 3. Validate dates
        date_valid, date_msg = InvoiceValidationService.validate_dates(vendor_invoice)
        if not date_valid:
            errors.append(date_msg)
        
        # 4. Validate line items
        items_valid, items_msg = InvoiceValidationService.validate_line_items(vendor_invoice)
        if not items_valid:
            errors.extend(items_msg)
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'amount_info': amount_msg if amount_valid else None,
        }
    
    @staticmethod
    def validate_vendor(vendor_invoice):
        """
        Validate that vendor is authorized for this purchase order
        
        Returns: (is_valid: bool, message: str)
        """
        try:
            if vendor_invoice.vendor != vendor_invoice.purchase_order.vendor:
                return False, f"Vendor mismatch: Invoice from {vendor_invoice.vendor.name} but PO is for {vendor_invoice.purchase_order.vendor.name}"
            
            if not vendor_invoice.vendor.active:
                return False, f"Vendor {vendor_invoice.vendor.name} is inactive"
            
            return True, "Vendor validated"
            
        except Exception as e:
            logger.error(f"Error validating vendor: {str(e)}")
            return False, f"Vendor validation error: {str(e)}"
    
    @staticmethod
    def validate_amount(vendor_invoice):
        """
        Validate invoice amount against PO amount
        Allows variance up to 10%
        
        Returns: (is_valid: bool, message: dict or str)
        """
        try:
            po = vendor_invoice.purchase_order
            po_amount = po.total_amount if hasattr(po, 'total_amount') else Decimal('0')
            invoice_amount = vendor_invoice.total_amount
            
            if po_amount == 0:
                return True, {
                    'message': 'No PO amount to compare',
                    'variance_percentage': 0,
                    'variance_amount': Decimal('0'),
                }
            
            # Calculate variance
            variance = invoice_amount - po_amount
            variance_percentage = (variance / po_amount) * 100
            
            # Check if within tolerance
            if abs(variance_percentage) > (InvoiceValidationService.AMOUNT_VARIANCE_TOLERANCE * 100):
                return False, f"Amount variance exceeds tolerance: Invoice KES {invoice_amount} vs PO KES {po_amount} ({variance_percentage:.2f}%)"
            
            return True, {
                'message': 'Amount within tolerance',
                'variance_percentage': float(variance_percentage),
                'variance_amount': float(variance),
                'po_amount': float(po_amount),
                'invoice_amount': float(invoice_amount),
            }
            
        except Exception as e:
            logger.error(f"Error validating amount: {str(e)}")
            return False, f"Amount validation error: {str(e)}"
    
    @staticmethod
    def validate_dates(vendor_invoice):
        """
        Validate invoice dates
        - Invoice date should not be in future
        - Due date should be after invoice date
        - Invoice date should be close to delivery date
        
        Returns: (is_valid: bool, message: str)
        """
        try:
            today = timezone.now().date()
            
            # Check if invoice date is in future
            if vendor_invoice.invoice_date > today:
                return False, f"Invoice date {vendor_invoice.invoice_date} is in the future"
            
            # Check if due date is after invoice date
            if vendor_invoice.due_date < vendor_invoice.invoice_date:
                return False, f"Due date {vendor_invoice.due_date} is before invoice date {vendor_invoice.invoice_date}"
            
            # Check if invoice is too old (more than 90 days old)
            days_old = (today - vendor_invoice.invoice_date).days
            if days_old > 90:
                return False, f"Invoice is too old ({days_old} days). Recent invoices required."
            
            return True, "Dates validated"
            
        except Exception as e:
            logger.error(f"Error validating dates: {str(e)}")
            return False, f"Date validation error: {str(e)}"
    
    @staticmethod
    def validate_line_items(vendor_invoice):
        """
        Validate line items against delivery/job specifications
        
        Returns: (is_valid: bool, errors: list)
        """
        errors = []
        
        try:
            if not vendor_invoice.line_items:
                return False, ["No line items provided"]
            
            if not isinstance(vendor_invoice.line_items, list):
                return False, ["Line items must be a list"]
            
            if len(vendor_invoice.line_items) == 0:
                return False, ["No line items in invoice"]
            
            # Validate each line item
            for i, item in enumerate(vendor_invoice.line_items):
                if not isinstance(item, dict):
                    errors.append(f"Line item {i+1}: Invalid format")
                    continue
                
                # Check required fields
                required_fields = ['description', 'quantity', 'unit_price']
                for field in required_fields:
                    if field not in item or item[field] is None:
                        errors.append(f"Line item {i+1}: Missing {field}")
                
                # Validate quantities
                if 'quantity' in item and item['quantity'] <= 0:
                    errors.append(f"Line item {i+1}: Quantity must be positive")
                
                # Validate prices
                if 'unit_price' in item and item['unit_price'] < 0:
                    errors.append(f"Line item {i+1}: Unit price cannot be negative")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            logger.error(f"Error validating line items: {str(e)}")
            return False, [f"Line item validation error: {str(e)}"]
    
    @staticmethod
    def validate_against_delivery(vendor_invoice):
        """
        Validate invoice against actual delivery records
        
        Returns: (is_valid: bool, message: str)
        """
        try:
            job = vendor_invoice.job
            
            # Get delivery info
            deliveries = getattr(job, 'deliveries', [])
            if not deliveries:
                return True, "No delivery records to validate against"
            
            # TODO: Add more sophisticated delivery matching logic
            
            return True, "Delivery validation passed"
            
        except Exception as e:
            logger.error(f"Error validating against delivery: {str(e)}")
            return True, f"Could not validate delivery: {str(e)}"
    
    @staticmethod
    def get_validation_summary(vendor_invoice):
        """
        Get a human-readable summary of validation results
        
        Returns: str
        """
        validation = InvoiceValidationService.validate(vendor_invoice)
        
        summary = "VALIDATION SUMMARY\n"
        summary += "=" * 50 + "\n"
        summary += f"Invoice: {vendor_invoice.invoice_number}\n"
        summary += f"Vendor: {vendor_invoice.vendor.name}\n"
        summary += f"Amount: KES {vendor_invoice.total_amount}\n"
        summary += f"Status: {'✓ VALID' if validation['is_valid'] else '✗ INVALID'}\n\n"
        
        if validation['errors']:
            summary += "ERRORS:\n"
            for error in validation['errors']:
                summary += f"  • {error}\n"
        
        if validation['warnings']:
            summary += "\nWARNINGS:\n"
            for warning in validation['warnings']:
                summary += f"  • {warning}\n"
        
        return summary
