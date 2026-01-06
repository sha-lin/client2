"""
PDF Generation Utilities using xhtml2pdf 
"""
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from xhtml2pdf import pisa
import logging

logger = logging.getLogger(__name__)


class QuotePDFGenerator:
    """Generate PDF quotes using xhtml2pdf (pure Python)"""
    
    @staticmethod
    def generate_quote_pdf(quote_id, request=None):
        """
        Generate a PDF for a quote
        
        Args:
            quote_id: Quote ID to generate PDF for
            request: Django request object (optional, for absolute URLs)
            
        Returns:
            BytesIO: PDF file buffer
        """
        from clientapp.models import Quote
        
        try:
            from clientapp.models import QuoteLineItem
            
            # Get quote
            quote = Quote.objects.filter(quote_id=quote_id).select_related('client', 'lead').first()
            
            if not quote:
                raise ValueError(f"Quote {quote_id} not found")
            
            # Get line items (preferred) or fallback to old quote records
            line_items = QuoteLineItem.objects.filter(quote=quote).order_by('order', 'created_at')
            
            # Calculate totals from line items (using snapshot prices)
            if line_items.exists():
                subtotal = sum(float(item.line_total) for item in line_items)
                quotes = []  # For backward compatibility
            else:
                # Fallback: use old quote records
                quotes = Quote.objects.filter(quote_id=quote_id).select_related('client', 'lead')
                subtotal = sum(float(q.total_amount) for q in quotes)
                line_items = []
            
            vat_amount = subtotal * 0.16 if quote.include_vat else 0
            total_amount = subtotal + vat_amount
            
            # Prepare recipient information
            if quote.client:
                recipient_name = quote.client.company or quote.client.name
                recipient_email = quote.client.email
                recipient_phone = quote.client.phone
            elif quote.lead:
                recipient_name = quote.lead.name
                recipient_email = quote.lead.email
                recipient_phone = quote.lead.phone
            else:
                recipient_name = 'N/A'
                recipient_email = ''
                recipient_phone = ''
            
            # Prepare quote items for PDF template
            quote_items = []
            if line_items.exists():
                for item in line_items:
                    quote_items.append({
                        'product_name': item.product_name,
                        'quantity': item.quantity,
                        'unit_price': float(item.unit_price),
                        'total_amount': float(item.line_total),
                    })
            else:
                # Fallback to old quote records
                for q in quotes:
                    quote_items.append({
                        'product_name': q.product_name,
                        'quantity': q.quantity,
                        'unit_price': float(q.unit_price),
                        'total_amount': float(q.total_amount),
                    })
            
            # Get company logo 
            from django.conf import settings
            import os
            logo_path = None
            if hasattr(settings, 'COMPANY_LOGO_PATH') and settings.COMPANY_LOGO_PATH:
                logo_path = settings.COMPANY_LOGO_PATH
            else:
                # Try to find logo in static files
                static_root = getattr(settings, 'STATIC_ROOT', None)
                if static_root:
                    logo_path = os.path.join(static_root, 'logo.png')
                    if not os.path.exists(logo_path):
                        logo_path = os.path.join(static_root, 'logo.jpg')
                        if not os.path.exists(logo_path):
                            logo_path = None
            
            # Prepare context for template
            context = {
                'quote_id': quote_id,
                'quote': quote,
                'quotes': quotes,  # For backward compatibility
                'line_items': line_items,  
                'quote_items': quote_items,  # Formatted for PDF template
                'first_quote': quote,
                'client': quote.client,
                'lead': quote.lead,
                'recipient_name': recipient_name,
                'recipient_email': recipient_email,
                'recipient_phone': recipient_phone,
                'created_by': quote.created_by.get_full_name() if quote.created_by else 'System',
                'quote_date': quote.quote_date,
                'valid_until': quote.valid_until,
                'subtotal': subtotal,
                'vat_amount': vat_amount,
                'total_amount': total_amount,
                'total': total_amount,  # Alias for template
                'include_vat': quote.include_vat,
                'notes': quote.notes,
                'company_name': getattr(settings, 'COMPANY_NAME', 'PrintDuka'),
                'company_email': getattr(settings, 'COMPANY_EMAIL', 'info@printduka.com'),
                'company_phone': getattr(settings, 'COMPANY_PHONE', '+254 XXX XXX XXX'),
                'company_address': getattr(settings, 'COMPANY_ADDRESS', ''),
                'company_logo_path': logo_path,
                'generated_at': timezone.now(),
            }
            
            # Render HTML template
            html_string = render_to_string('pdf/quote_pdf.html', context)
            
            # Create PDF
            pdf_buffer = BytesIO()
            pisa_status = pisa.CreatePDF(
                html_string,
                dest=pdf_buffer,
                encoding='UTF-8'
            )
            
            if pisa_status.err:
                raise Exception(f"Error creating PDF: {pisa_status.err}")
            
            pdf_buffer.seek(0)
            return pdf_buffer
            
        except Exception as e:
            logger.error(f"Error generating PDF for quote {quote_id}: {e}")
            raise
    
    @staticmethod
    def download_quote_pdf(quote_id, request=None):
        """
        Generate and return PDF as HTTP response for download
        
        Args:
            quote_id: Quote ID to generate PDF for
            request: Django request object
            
        Returns:
            HttpResponse: PDF file response
        """
        try:
            pdf_file = QuotePDFGenerator.generate_quote_pdf(quote_id, request)
            
            # Create HTTP response
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="Quote_{quote_id}.pdf"'
            
            return response
            
        except Exception as e:
            logger.error(f"Error downloading PDF for quote {quote_id}: {e}")
            # Return error response
            response = HttpResponse(f"Error generating PDF: {str(e)}", status=500)
            return response