"""
Storefront API ViewSets
Product catalog, estimate quotes, customer auth, messaging, chatbot
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal
import uuid

from clientapp.models import (
    StorefrontProduct, EstimateQuote, StorefrontCustomer,
    StorefrontMessage, ChatbotConversation, QuotePricingSnapshot,
    ProductionUnit, Lead, Quote
)
from clientapp.storefront_serializers import (
    StorefrontProductSerializer, EstimateQuoteSerializer,
    EstimateQuoteCreateSerializer, StorefrontCustomerSerializer,
    StorefrontCustomerUpdateSerializer, StorefrontMessageSerializer,
    ContactEmailSerializer, ContactWhatsAppSerializer,
    CallRequestSerializer, ChatbotMessageSerializer,
    ChatbotMessageResponseSerializer, ChatbotConversationSerializer,
    ProductionUnitSerializer, ProductionUnitCreateSerializer,
    QuotePricingSnapshotSerializer, CustomerPreferencesSerializer,
    CustomerRegistrationSerializer, EstimateQuoteShareSerializer,
    ProductPriceCalculationSerializer
)


# ============================================================================
# PRODUCTS & CATALOG
# ============================================================================

class StorefrontProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public product catalog endpoint
    No authentication required
    """
    queryset = StorefrontProduct.objects.filter(storefront_visible=True)
    serializer_class = StorefrontProductSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['category', 'featured']
    search_fields = ['name', 'description_short']
    ordering_fields = ['sort_order', 'rating', 'base_price', 'name']
    ordering = ['sort_order', '-featured']
    
    def get_queryset(self):
        """Filter products"""
        queryset = super().get_queryset()
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(base_price__gte=Decimal(min_price))
        if max_price:
            queryset = queryset.filter(base_price__lte=Decimal(max_price))
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description_short__icontains=search)
            )
        
        return queryset.order_by('sort_order', '-featured')
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def calculate_price(self, request, pk=None):
        """Calculate price for product with given options"""
        product = self.get_object()
        serializer = ProductPriceCalculationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        quantity = serializer.validated_data['quantity']
        turnaround = serializer.validated_data['turnaround_time']
        
        # Get unit price based on quantity
        unit_price = product.get_price_for_quantity(quantity)
        
        # Add turnaround surcharge
        surcharge = Decimal('0.00')
        if turnaround == 'rush':
            surcharge = product.turnaround_rush_surcharge * quantity
        elif turnaround == 'expedited':
            surcharge = product.turnaround_expedited_surcharge * quantity
        
        line_total = (unit_price * quantity) + surcharge
        
        return Response({
            'product_id': product.product_id,
            'quantity': quantity,
            'unit_price': str(unit_price),
            'surcharge': str(surcharge),
            'line_total': str(line_total),
            'turnaround_time': turnaround
        })


# ============================================================================
# ESTIMATE QUOTES
# ============================================================================

class EstimateQuoteViewSet(viewsets.ModelViewSet):
    """
    Draft/Estimate quotes created from storefront
    Public creation (no auth), AM can access & modify
    """
    queryset = EstimateQuote.objects.all()
    permission_classes = [permissions.AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return EstimateQuoteCreateSerializer
        return EstimateQuoteSerializer
    
    def create(self, request, *args, **kwargs):
        """Create estimate quote (no auth required)"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        estimate = serializer.instance
        
        # Create pricing snapshot
        QuotePricingSnapshot.objects.create(
            estimate_quote=estimate,
            snapshot_type='estimate_created',
            base_amount=estimate.subtotal,
            total_amount=estimate.total_amount
        )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def by_token(self, request):
        """Get estimate by share token (public)"""
        token = request.query_params.get('token')
        if not token:
            return Response(
                {'detail': 'token query param required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            estimate = EstimateQuote.objects.get(share_token=token)
        except EstimateQuote.DoesNotExist:
            return Response(
                {'detail': 'Estimate not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(estimate)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def share(self, request):
        """Share estimate quote via WhatsApp/Email"""
        estimate_id = request.data.get('estimate_id')
        channel = request.data.get('channel')
        
        if not estimate_id or not channel:
            return Response(
                {'detail': 'estimate_id and channel required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            estimate = EstimateQuote.objects.get(estimate_id=estimate_id)
        except EstimateQuote.DoesNotExist:
            return Response(
                {'detail': 'Estimate not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update status
        estimate.status = 'shared_with_am'
        estimate.shared_via = channel
        estimate.share_timestamp = timezone.now()
        estimate.save()
        
        # TODO: Send via WhatsApp/Email (integration in Phase 2)
        # - Generate share link
        # - Send message to sales team
        # - Create notification
        
        return Response({
            'success': True,
            'estimate_id': estimate.estimate_id,
            'share_link': f"http://storefront.example.com/quotes/{estimate.share_token}",
            'message': f'Estimate shared via {channel}'
        })
    
    @action(detail=False, methods=['post'])
    def convert_to_quote(self, request):
        """
        Convert estimate to official quote (for AM or registered customer)
        Creates Lead and Quote in system
        """
        estimate_id = request.data.get('estimate_id')
        adjust_data = request.data.get('adjustments', {})
        
        try:
            estimate = EstimateQuote.objects.get(estimate_id=estimate_id)
        except EstimateQuote.DoesNotExist:
            return Response(
                {'detail': 'Estimate not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Use adjusted data if provided, else use original
        final_amount = Decimal(str(adjust_data.get('total_amount', estimate.total_amount)))
        
        # Create Lead from customer info
        lead_id = f"LD-{timezone.now().year}-{EstimateQuote.objects.count():05d}"
        lead = Lead.objects.create(
            lead_id=lead_id,
            name=estimate.customer_name,
            email=estimate.customer_email,
            phone=estimate.customer_phone,
            source='Storefront',
            status='Qualified',
            preferred_client_type='B2B'
        )
        
        # Create Quote
        quote = Quote.objects.create(
            quote_id=f"QT-{timezone.now().year}-{Quote.objects.count():05d}",
            lead=lead,
            status='Draft',
            total_amount=final_amount,
            created_by=request.user if request.user.is_authenticated else None,
            source='storefront_shared'
        )
        
        # Archive estimate
        estimate.status = 'converted_to_quote'
        estimate.converted_quote_id = quote.quote_id
        estimate.save()
        
        # Create pricing snapshot
        QuotePricingSnapshot.objects.create(
            estimate_quote=estimate,
            quote_id=quote.quote_id,
            snapshot_type='quote_created',
            base_amount=estimate.subtotal,
            adjustments=adjust_data,
            total_amount=final_amount,
            applied_by=request.user if request.user.is_authenticated else None
        )
        
        return Response({
            'success': True,
            'lead_id': lead.lead_id,
            'quote_id': quote.quote_id,
            'message': 'Estimate converted to official quote'
        })


# ============================================================================
# CUSTOMER AUTHENTICATION & PROFILES
# ============================================================================

class CustomerRegistrationView(APIView):
    """Register new storefront customer"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Register customer"""
        serializer = CustomerRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Create user
        user = serializer.save()
        
        # Create storefront customer profile
        customer = StorefrontCustomer.objects.create(
            user=user,
            phone=request.data.get('phone', ''),
            company=request.data.get('company', '')
        )
        
        # TODO: Send verification email
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'message': 'Registration successful. Please verify your email.',
            'user_id': user.id,
            'customer_id': customer.customer_id,
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh)
        }, status=status.HTTP_201_CREATED)


class CustomerProfileViewSet(viewsets.ViewSet):
    """Customer profile management"""
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Get current user's profile"""
        try:
            customer = StorefrontCustomer.objects.get(user=request.user)
        except StorefrontCustomer.DoesNotExist:
            return Response(
                {'detail': 'Customer profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = StorefrontCustomerSerializer(customer)
        return Response(serializer.data)
    
    def update(self, request):
        """Update customer profile"""
        try:
            customer = StorefrontCustomer.objects.get(user=request.user)
        except StorefrontCustomer.DoesNotExist:
            return Response(
                {'detail': 'Customer profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = StorefrontCustomerUpdateSerializer(
            customer, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def update_preferences(self, request):
        """Update communication preferences"""
        try:
            customer = StorefrontCustomer.objects.get(user=request.user)
        except StorefrontCustomer.DoesNotExist:
            return Response(
                {'detail': 'Customer profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CustomerPreferencesSerializer(
            customer, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'preferences': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# MESSAGING & CONTACT
# ============================================================================

class ContactEmailView(APIView):
    """Send email to sales"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Send email inquiry"""
        serializer = ContactEmailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Create message record
        message = StorefrontMessage.objects.create(
            message_type='email_inquiry',
            channel='email',
            customer_name=data['name'],
            customer_email=data['email'],
            customer_phone=data.get('phone', ''),
            subject=data['subject'],
            message_content=data['message'],
            status='new'
        )
        
        # TODO: Send email to sales team
        
        return Response({
            'success': True,
            'message_id': message.message_id,
            'message': 'Email sent. Sales team will respond shortly.'
        })


class ContactWhatsAppView(APIView):
    """Initiate WhatsApp contact"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Create WhatsApp contact message"""
        serializer = ContactWhatsAppSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Create message record
        message = StorefrontMessage.objects.create(
            message_type='whatsapp_inquiry',
            channel='whatsapp',
            customer_name=data['name'],
            customer_phone=data['phone'],
            message_content=data['message'],
            status='new'
        )
        
        # TODO: Send WhatsApp message
        
        return Response({
            'success': True,
            'message_id': message.message_id,
            'whatsapp_link': f"https://wa.me/{request.data.get('phone')}"
        })


class CallRequestView(APIView):
    """Request a phone call"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Create call request"""
        serializer = CallRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Create message record
        message = StorefrontMessage.objects.create(
            message_type='call_request',
            channel='phone',
            customer_name=data['name'],
            customer_phone=data['phone'],
            message_content=f"Call request for {data['preferred_time']}",
            status='new'
        )
        
        # TODO: Send notification to sales team
        
        return Response({
            'success': True,
            'message_id': message.message_id,
            'message': 'Call request received. Sales team will contact you shortly.'
        })


class StorefrontMessageViewSet(viewsets.ModelViewSet):
    """List and manage storefront messages (for AM)"""
    queryset = StorefrontMessage.objects.all()
    serializer_class = StorefrontMessageSerializer
    permission_classes = [permissions.IsAuthenticated]  # TODO: IsAccountManager
    
    def get_queryset(self):
        """Filter messages for assigned AM"""
        queryset = super().get_queryset()
        
        # Show assigned to current user or unassigned
        queryset = queryset.filter(
            Q(assigned_to=self.request.user) | Q(assigned_to__isnull=True)
        )
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def assign_to_me(self, request, pk=None):
        """Assign message to current user"""
        message = self.get_object()
        message.assigned_to = request.user
        message.status = 'in_progress'
        message.save()
        
        return Response({
            'success': True,
            'assigned_to': message.assigned_to.get_full_name()
        })
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark message as resolved"""
        message = self.get_object()
        message.status = 'resolved'
        message.response_message = request.data.get('response', '')
        message.response_at = timezone.now()
        message.save()
        
        return Response({'success': True, 'status': 'resolved'})


# ============================================================================
# CHATBOT
# ============================================================================

class ChatbotMessageView(APIView):
    """Chatbot message endpoint"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Send message to chatbot"""
        serializer = ChatbotMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        message_text = serializer.validated_data['message']
        conversation_id = serializer.validated_data.get('conversation_id', '')
        
        # Get or create conversation
        if conversation_id:
            try:
                conversation = ChatbotConversation.objects.get(
                    conversation_id=conversation_id
                )
            except ChatbotConversation.DoesNotExist:
                conversation = ChatbotConversation.objects.create(
                    conversation_id=conversation_id,
                    session_id=request.session.get('session_key', str(uuid.uuid4()))
                )
        else:
            conversation = ChatbotConversation.objects.create(
                session_id=request.session.get('session_key', str(uuid.uuid4()))
            )
        
        # Add customer message
        conversation.messages.append({
            'timestamp': timezone.now().isoformat(),
            'sender': 'customer',
            'text': message_text,
            'action': None
        })
        
        # TODO: Process message with chatbot AI/intent matching
        # For now, return simple response
        bot_response = "Thank you for your message. A sales team member will respond shortly."
        
        # Add bot response
        conversation.messages.append({
            'timestamp': timezone.now().isoformat(),
            'sender': 'bot',
            'text': bot_response,
            'action': None
        })
        
        conversation.save()
        
        return Response({
            'conversation_id': conversation.conversation_id,
            'response': bot_response,
            'suggestions': [
                'View Products',
                'Create Quote',
                'Speak to Sales'
            ]
        })


class ChatbotConversationViewSet(viewsets.ReadOnlyModelViewSet):
    """View chatbot conversations (for analytics)"""
    queryset = ChatbotConversation.objects.all()
    serializer_class = ChatbotConversationSerializer
    permission_classes = [permissions.IsAuthenticated]  # TODO: IsAccountManager


# ============================================================================
# PRODUCTION UNITS
# ============================================================================

class ProductionUnitViewSet(viewsets.ModelViewSet):
    """Job production units (for PT)"""
    queryset = ProductionUnit.objects.all()
    permission_classes = [permissions.IsAuthenticated]  # TODO: IsProductionTeam
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ProductionUnitCreateSerializer
        return ProductionUnitSerializer
    
    def get_queryset(self):
        """Filter production units for job"""
        job_id = self.request.query_params.get('job_id')
        if job_id:
            return ProductionUnit.objects.filter(job_id=job_id)
        return super().get_queryset()
    
    @action(detail=True, methods=['post'])
    def send_po(self, request, pk=None):
        """Send PO to vendor"""
        unit = self.get_object()
        
        # TODO: Generate and send PO
        
        unit.status = 'po_sent'
        unit.save()
        
        return Response({
            'success': True,
            'unit_id': unit.unit_id,
            'message': 'PO sent to vendor'
        })
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get unit progress"""
        unit = self.get_object()
        
        return Response({
            'unit_id': unit.unit_id,
            'status': unit.status,
            'progress_percentage': self._calculate_progress(unit),
            'timeline': {
                'expected_start': unit.expected_start_date,
                'expected_end': unit.expected_end_date,
                'actual_start': unit.actual_start_date,
                'actual_end': unit.actual_end_date
            }
        })
    
    def _calculate_progress(self, unit):
        """Calculate production unit progress"""
        status_map = {
            'pending_po': 0,
            'po_sent': 25,
            'accepted': 50,
            'in_progress': 75,
            'completed': 100,
            'delayed': 60,
            'cancelled': 0
        }
        return status_map.get(unit.status, 0)
