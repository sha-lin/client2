"""
PDF Generation Utilities using xhtml2pdf (pure Python, no GTK required)
"""
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import render_to_string
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
            # Get all quote items with this quote_id
            quotes = Quote.objects.filter(quote_id=quote_id).select_related('client', 'lead')
            
            if not quotes.exists():
                raise ValueError(f"Quote {quote_id} not found")
            
            first_quote = quotes.first()
            
            # Calculate totals
            subtotal = sum(q.total_amount for q in quotes)
            vat_amount = subtotal * 0.16 if first_quote.include_vat else 0
            total_amount = subtotal + vat_amount
            
            # Prepare context for template
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