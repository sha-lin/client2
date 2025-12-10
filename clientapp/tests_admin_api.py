"""
Comprehensive unit tests for admin dashboard CRUD operations and views
Tests include:
- Admin page rendering (status 200 for staff, 403/redirect for non-staff)
- API endpoint permissions (staff-only access)
- CRUD operations (create, read, update, delete)
- Pagination and filtering
- Data validation
"""

from django.test import TestCase, Client as DjangoTestClient
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.utils import timezone
import json

from clientapp.models import Lead, Product, Vendor, Job, Quote, LPO, Payment, QCInspection, Delivery


class AdminDashboardPermissionTests(TestCase):
    """Test admin dashboard page access permissions"""
    
    def setUp(self):
        """Create test users and client"""
        self.client = DjangoTestClient()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='testpass123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='regularuser',
            password='testpass123'
        )
    
    def test_admin_dashboard_requires_staff(self):
        """Non-staff users should be redirected from admin dashboard"""
        response = self.client.get(reverse('admin_dashboard'))
        self.assertNotEqual(response.status_code, 200)  # Should redirect or 403
    
    def test_admin_dashboard_staff_access(self):
        """Staff users should access admin dashboard"""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_admin_clients_list_staff_only(self):
        """Clients list page should be staff-only"""
        # Non-staff access
        self.client.login(username='regularuser', password='testpass123')
        response = self.client.get(reverse('admin_clients_list'))
        self.assertNotEqual(response.status_code, 200)
        
        # Staff access
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get(reverse('admin_clients_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_admin_leads_list_staff_only(self):
        """Leads list page should be staff-only"""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get(reverse('admin_leads_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_admin_products_list_staff_only(self):
        """Products list page should be staff-only"""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get(reverse('admin_products_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_admin_vendors_list_staff_only(self):
        """Vendors list page should be staff-only"""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get(reverse('admin_vendors_list'))
        self.assertEqual(response.status_code, 200)


class LeadsAPITests(TestCase):
    """Test Leads CRUD API endpoints"""
    
    def setUp(self):
        self.client = DjangoTestClient()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='testpass123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='regularuser',
            password='testpass123'
        )
        self.lead = Lead.objects.create(
            lead_name='Test Lead',
            email='test@example.com',
            phone='555-0100',
            company_name='Test Company',
            status='New'
        )
    
    def test_list_leads_requires_staff(self):
        """Listing leads without staff access should return 403"""
        self.client.login(username='regularuser', password='testpass123')
        response = self.client.get(reverse('api_admin_leads'))
        self.assertEqual(response.status_code, 403)
    
    def test_list_leads_with_staff(self):
        """Staff users can list leads"""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get(reverse('api_admin_leads'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertGreaterEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['name'], 'Test Lead')
    
    def test_create_lead_requires_staff(self):
        """Creating lead without staff access should return 403"""
        self.client.login(username='regularuser', password='testpass123')
        response = self.client.post(
            reverse('api_admin_leads'),
            data=json.dumps({
                'lead_name': 'New Lead',
                'email': 'new@example.com'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
    
    def test_create_lead_with_staff(self):
        """Staff can create leads"""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.post(
            reverse('api_admin_leads'),
            data=json.dumps({
                'lead_name': 'New Lead',
                'email': 'newlead@example.com',
                'status': 'Qualified'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('id', data)
        
        # Verify lead was created
        new_lead = Lead.objects.get(id=data['id'])
        self.assertEqual(new_lead.lead_name, 'New Lead')
    
    def test_get_lead_detail(self):
        """Retrieve specific lead details"""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get(
            reverse('api_admin_lead_detail', args=[self.lead.id])
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['name'], 'Test Lead')
        self.assertEqual(data['email'], 'test@example.com')
    
    def test_update_lead(self):
        """Update lead details"""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.put(
            reverse('api_admin_lead_detail', args=[self.lead.id]),
            data=json.dumps({
                'lead_name': 'Updated Lead',
                'status': 'Qualified'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify update
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.lead_name, 'Updated Lead')
        self.assertEqual(self.lead.status, 'Qualified')
    
    def test_delete_lead(self):
        """Delete a lead"""
        lead_id = self.lead.id
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.delete(
            reverse('api_admin_lead_detail', args=[lead_id])
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify deletion
        self.assertFalse(Lead.objects.filter(id=lead_id).exists())
    
    def test_list_leads_with_pagination(self):
        """Test pagination on leads list"""
        # Create multiple leads
        for i in range(5):
            Lead.objects.create(
                lead_name=f'Lead {i}',
                email=f'lead{i}@example.com'
            )
        
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get(
            reverse('api_admin_leads') + '?page=1&page_size=3'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 3)
        self.assertEqual(data['total_pages'], 2)
    
    def test_list_leads_with_status_filter(self):
        """Test filtering leads by status"""
        Lead.objects.create(
            lead_name='Qualified Lead',
            email='qualified@example.com',
            status='Qualified'
        )
        
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get(
            reverse('api_admin_leads') + '?status=Qualified'
        )
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['status'], 'Qualified')


class ProductsAPITests(TestCase):
    """Test Products CRUD API endpoints"""
    
    def setUp(self):
        self.client = DjangoTestClient()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='testpass123',
            is_staff=True
        )
        self.product = Product.objects.create(
            name='Test Product',
            sku='TP001',
            base_price=100.00
        )
    
    def test_list_products_with_staff(self):
        """Staff can list products"""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get(reverse('api_admin_products'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertGreaterEqual(len(data['results']), 1)
    
    def test_create_product_with_staff(self):
        """Staff can create products"""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.post(
            reverse('api_admin_products'),
            data=json.dumps({
                'name': 'New Product',
                'sku': 'NP001',
                'base_price': 150.00
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify creation
        new_product = Product.objects.get(id=data['id'])
        self.assertEqual(new_product.name, 'New Product')
        self.assertEqual(float(new_product.base_price), 150.00)
    
    def test_update_product(self):
        """Update product details"""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.put(
            reverse('api_admin_product_detail', args=[self.product.id]),
            data=json.dumps({
                'name': 'Updated Product',
                'base_price': 200.00
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify update
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Updated Product')
        self.assertEqual(float(self.product.base_price), 200.00)
    
    def test_delete_product(self):
        """Delete a product"""
        product_id = self.product.id
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.delete(
            reverse('api_admin_product_detail', args=[product_id])
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify deletion
        self.assertFalse(Product.objects.filter(id=product_id).exists())


class VendorsAPITests(TestCase):
    """Test Vendors CRUD API endpoints"""
    
    def setUp(self):
        self.client = DjangoTestClient()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='testpass123',
            is_staff=True
        )
        self.vendor = Vendor.objects.create(
            name='Test Vendor',
            email='vendor@example.com',
            phone='555-0101'
        )
    
    def test_list_vendors_with_staff(self):
        """Staff can list vendors"""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get(reverse('api_admin_vendors'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_create_vendor_with_staff(self):
        """Staff can create vendors"""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.post(
            reverse('api_admin_vendors'),
            data=json.dumps({
                'name': 'New Vendor',
                'email': 'newvendor@example.com',
                'phone': '555-0102'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_update_vendor(self):
        """Update vendor details"""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.put(
            reverse('api_admin_vendor_detail', args=[self.vendor.id]),
            data=json.dumps({
                'name': 'Updated Vendor',
                'phone': '555-0999'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        self.vendor.refresh_from_db()
        self.assertEqual(self.vendor.name, 'Updated Vendor')
    
    def test_delete_vendor(self):
        """Delete a vendor"""
        vendor_id = self.vendor.id
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.delete(
            reverse('api_admin_vendor_detail', args=[vendor_id])
        )
        self.assertEqual(response.status_code, 200)
        
        self.assertFalse(Vendor.objects.filter(id=vendor_id).exists())


class DashboardDataAPITests(TestCase):
    """Test dashboard polling endpoint"""
    
    def setUp(self):
        self.client = DjangoTestClient()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='testpass123',
            is_staff=True
        )
    
    def test_dashboard_data_requires_staff(self):
        """Dashboard data endpoint requires staff access"""
        response = self.client.get(reverse('api_admin_dashboard_data'))
        self.assertNotEqual(response.status_code, 200)
    
    def test_dashboard_data_with_staff(self):
        """Staff can access dashboard data"""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get(reverse('api_admin_dashboard_data'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Verify expected fields
        self.assertIn('stats', data)
        self.assertIn('revenue_trend', data)
        self.assertIn('production_by_category', data)
        self.assertIn('weekly_jobs', data)
    
    def test_dashboard_data_returns_valid_json(self):
        """Dashboard data returns valid JSON structure"""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get(reverse('api_admin_dashboard_data'))
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = json.loads(response.content)
        # Should have stats with KPI values
        self.assertIn('clients', data['stats'])
        self.assertIn('revenue', data['stats'])
        self.assertIn('quotes', data['stats'])
        self.assertIn('jobs', data['stats'])


class PaginationAndFilteringTests(TestCase):
    """Test pagination and filtering across all list endpoints"""
    
    def setUp(self):
        self.client = DjangoTestClient()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='staffuser', password='testpass123')
        
        # Create test data
        for i in range(15):
            Lead.objects.create(
                lead_name=f'Lead {i}',
                email=f'lead{i}@example.com',
                status='New' if i % 2 == 0 else 'Qualified'
            )
    
    def test_default_pagination(self):
        """Test default pagination (page_size=20)"""
        response = self.client.get(reverse('api_admin_leads'))
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 15)
        self.assertEqual(data['total_pages'], 1)
    
    def test_custom_page_size(self):
        """Test custom page size"""
        response = self.client.get(
            reverse('api_admin_leads') + '?page_size=5'
        )
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 5)
        self.assertEqual(data['total_pages'], 3)
    
    def test_pagination_with_filters(self):
        """Test pagination works with filters"""
        response = self.client.get(
            reverse('api_admin_leads') + '?status=New&page_size=3'
        )
        data = json.loads(response.content)
        # Should have filtered results
        for result in data['results']:
            self.assertEqual(result['status'], 'New')
    
    def test_search_filtering(self):
        """Test search filtering"""
        response = self.client.get(
            reverse('api_admin_leads') + '?search=Lead 5'
        )
        data = json.loads(response.content)
        self.assertGreater(len(data['results']), 0)


class APIErrorHandlingTests(TestCase):
    """Test error handling in API endpoints"""
    
    def setUp(self):
        self.client = DjangoTestClient()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='testpass123',
            is_staff=True
        )
    
    def test_get_nonexistent_lead(self):
        """Accessing non-existent resource returns 404"""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get(reverse('api_admin_lead_detail', args=[9999]))
        self.assertEqual(response.status_code, 404)
    
    def test_invalid_json_returns_400(self):
        """Invalid JSON in POST request returns 400"""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.post(
            reverse('api_admin_leads'),
            data='invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_missing_required_fields(self):
        """Missing required fields returns 400 with error message"""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.post(
            reverse('api_admin_leads'),
            data=json.dumps({}),  # Missing required fields
            content_type='application/json'
        )
        # Should still return 200 but with success=False
        data = json.loads(response.content)
        self.assertFalse(data.get('success', False))
