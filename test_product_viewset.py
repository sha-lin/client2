#!/usr/bin/env python
"""
Automated smoke test for ProductViewSet endpoints.
Tests authentication, CRUD, file uploads, pricing, and workflow actions.

Run with: python manage.py shell < test_product_viewset.py
Or: python test_product_viewset.py
"""

import os
import sys
import django
from io import BytesIO
from PIL import Image
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'client.settings')
django.setup()

# Add testserver to ALLOWED_HOSTS for tests
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from clientapp.models import Product, ProductPricing

class ProductViewSetSmokeTest(APITestCase):
    """Smoke tests for ProductViewSet endpoints"""
    
    @classmethod
    def setUpTestData(cls):
        """Create test user with Production Team permission"""
        # Create Production Team group if it doesn't exist
        pt_group, _ = Group.objects.get_or_create(name='Production Team')
        
        # Get or create test user
        cls.user, _ = User.objects.get_or_create(
            username='test_pt_user',
            defaults={
                'email': 'test@printduka.com',
            }
        )
        if not cls.user.has_usable_password():
            cls.user.set_password('testpass123')
            cls.user.save()
        
        cls.user.groups.add(pt_group)
        
    def setUp(self):
        """Set up test client and authenticate"""
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
    def create_sample_image(self, name='test.jpg', size=(400, 400)):
        """Create a simple test image"""
        img = Image.new('RGB', size, color='red')
        img_file = BytesIO()
        img.save(img_file, format='JPEG')
        img_file.seek(0)
        return SimpleUploadedFile(
            name=name,
            content=img_file.read(),
            content_type='image/jpeg'
        )
    
    def test_01_create_product(self):
        """Test: POST /api/v1/products/ - Create a product"""
        print("\n[TEST 1] Creating product...")
        
        payload = {
            'name': 'Test Product A4 Flyer',
            'internal_code': 'TEST-A4-FLYER-001',
            'description': 'A4 full color flyer',
            'base_price': '50.00',
            'customization_level': 'partially_customizable',
            'primary_category': 'flyers',
            'status': 'draft',
        }
        
        response = self.client.post('/api/v1/products/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        
        global product_id
        product_id = response.data['id']
        print(f"✅ Product created: ID={product_id}")
        print(f"   Response: {response.data}")
        return product_id
    
    def test_02_retrieve_product(self):
        """Test: GET /api/v1/products/{id}/ - Retrieve product"""
        print("\n[TEST 2] Retrieving product...")
        
        # First create a product
        product = Product.objects.create(
            name='Retrieve Test Product',
            internal_code='TEST-RETRIEVE-001',
            base_price=Decimal('100.00'),
            customization_level='partially_customizable',
            created_by=self.user,
            updated_by=self.user
        )
        
        response = self.client.get(f'/api/v1/products/{product.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Retrieve Test Product')
        
        print(f"✅ Product retrieved successfully")
        print(f"   Name: {response.data['name']}, Status: {response.data.get('status')}")
    
    def test_03_update_product(self):
        """Test: PATCH /api/v1/products/{id}/ - Update product"""
        print("\n[TEST 3] Updating product...")
        
        product = Product.objects.create(
            name='Update Test Product',
            internal_code='TEST-UPDATE-001',
            base_price=Decimal('75.00'),
            customization_level='partially_customizable',
            created_by=self.user,
            updated_by=self.user
        )
        
        payload = {
            'name': 'Updated Product Name',
            'description': 'This description was updated',
        }
        
        response = self.client.patch(f'/api/v1/products/{product.id}/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Product Name')
        
        print(f"✅ Product updated successfully")
        print(f"   New name: {response.data['name']}")
    
    def test_04_upload_primary_image(self):
        """Test: POST /api/v1/products/{id}/upload-primary-image/"""
        print("\n[TEST 4] Uploading primary image...")
        
        product = Product.objects.create(
            name='Image Upload Test',
            internal_code='TEST-IMG-001',
            base_price=Decimal('50.00'),
            customization_level='partially_customizable',
            created_by=self.user,
            updated_by=self.user
        )
        
        image_file = self.create_sample_image('primary.jpg')
        
        response = self.client.post(
            f'/api/v1/products/{product.id}/upload-primary-image/',
            {'image': image_file, 'alt_text': 'Primary product image'},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertTrue(response.data['is_primary'])
        
        print(f"✅ Primary image uploaded successfully")
        print(f"   Image ID: {response.data['id']}, Primary: {response.data['is_primary']}")
    
    def test_05_upload_gallery_images(self):
        """Test: POST /api/v1/products/{id}/upload-gallery-images/ (bulk)"""
        print("\n[TEST 5] Uploading gallery images (bulk)...")
        
        product = Product.objects.create(
            name='Gallery Upload Test',
            internal_code='TEST-GAL-001',
            base_price=Decimal('50.00'),
            customization_level='partially_customizable',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create 2 test images
        images = [
            self.create_sample_image(f'gallery_{i}.jpg')
            for i in range(2)
        ]
        
        response = self.client.post(
            f'/api/v1/products/{product.id}/upload-gallery-images/',
            {'images': images},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['count'], 2)
        
        print(f"✅ Gallery images uploaded: {response.data['count']} images")
        print(f"   Message: {response.data['message']}")
    
    def test_06_add_video(self):
        """Test: POST /api/v1/products/{id}/add-video/"""
        print("\n[TEST 6] Adding video...")
        
        product = Product.objects.create(
            name='Video Test Product',
            internal_code='TEST-VID-001',
            base_price=Decimal('50.00'),
            customization_level='partially_customizable',
            created_by=self.user,
            updated_by=self.user
        )
        
        payload = {
            'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'title': 'Product Demo Video'
        }
        
        response = self.client.post(
            f'/api/v1/products/{product.id}/add-video/',
            payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['type'], 'youtube')
        
        print(f"✅ Video added successfully")
        print(f"   Type: {response.data['type']}, URL: {response.data['url'][:50]}...")
    
    def test_07_calculate_price(self):
        """Test: POST /api/v1/products/{id}/calculate-price/"""
        print("\n[TEST 7] Calculating price...")
        
        product = Product.objects.create(
            name='Pricing Test',
            internal_code='TEST-PRICE-001',
            base_price=Decimal('100.00'),
            customization_level='partially_customizable',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Create pricing info
        ProductPricing.objects.create(
            product=product,
            base_cost=Decimal('50.00'),
            return_margin=Decimal('30.00')
        )
        
        payload = {
            'quantity': 100,
            'include_breakdown': True
        }
        
        response = self.client.post(
            f'/api/v1/products/{product.id}/calculate-price/',
            payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('unit_price', response.data)
        self.assertIn('total_price', response.data)
        self.assertEqual(int(float(response.data['quantity'])), 100)
        
        print(f"✅ Price calculated successfully")
        print(f"   Qty: {response.data['quantity']}, Unit: ${response.data['unit_price']}, Total: ${response.data['total_price']}")
    
    def test_08_publish_product(self):
        """Test: POST /api/v1/products/{id}/publish/"""
        print("\n[TEST 8] Publishing product...")
        
        product = Product.objects.create(
            name='Publish Test',
            internal_code='TEST-PUB-001',
            base_price=Decimal('50.00'),
            customization_level='partially_customizable',
            status='draft',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Need to add pricing for publish validation
        ProductPricing.objects.create(
            product=product,
            base_cost=Decimal('25.00')
        )
        
        response = self.client.post(
            f'/api/v1/products/{product.id}/publish/',
            {},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'published')
        
        print(f"✅ Product published successfully")
        print(f"   Status: {response.data['status']}, Message: {response.data['message']}")
    
    def test_09_archive_product(self):
        """Test: POST /api/v1/products/{id}/archive/"""
        print("\n[TEST 9] Archiving product...")
        
        product = Product.objects.create(
            name='Archive Test',
            internal_code='TEST-ARC-001',
            base_price=Decimal('50.00'),
            customization_level='partially_customizable',
            status='published',
            created_by=self.user,
            updated_by=self.user
        )
        
        response = self.client.post(
            f'/api/v1/products/{product.id}/archive/',
            {},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'archived')
        
        print(f"✅ Product archived successfully")
        print(f"   Status: {response.data['status']}")
    
    def test_10_save_draft(self):
        """Test: POST /api/v1/products/{id}/save-draft/"""
        print("\n[TEST 10] Saving product as draft...")
        
        product = Product.objects.create(
            name='Draft Test',
            internal_code='TEST-DRF-001',
            base_price=Decimal('50.00'),
            customization_level='partially_customizable',
            status='published',
            created_by=self.user,
            updated_by=self.user
        )
        
        payload = {
            'name': 'Updated Draft Name',
            'description': 'New draft description'
        }
        
        response = self.client.post(
            f'/api/v1/products/{product.id}/save-draft/',
            payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'draft')
        
        print(f"✅ Product saved as draft successfully")
        print(f"   Status: {response.data['status']}")
    
    def test_11_change_history(self):
        """Test: GET /api/v1/products/{id}/change-history/"""
        print("\n[TEST 11] Viewing change history...")
        
        product = Product.objects.create(
            name='History Test',
            internal_code='TEST-HIS-001',
            base_price=Decimal('50.00'),
            customization_level='partially_customizable',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Publish to create a change history entry
        product.status = 'published'
        product.save()
        
        response = self.client.get(
            f'/api/v1/products/{product.id}/change-history/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('changes', response.data)
        self.assertEqual(response.data['product_id'], product.id)
        
        print(f"✅ Change history retrieved successfully")
        print(f"   Product: {response.data['product_name']}, Total changes: {response.data['total_changes']}")


def run_all_tests():
    """Run all smoke tests"""
    print("=" * 80)
    print("PRODUCTVIEWSET SMOKE TEST SUITE")
    print("=" * 80)
    
    import unittest
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(ProductViewSetSmokeTest)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 80)
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED")
        print(f"   Ran {result.testsRun} tests successfully")
    else:
        print("❌ SOME TESTS FAILED")
        print(f"   Tests run: {result.testsRun}")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")
        if result.failures:
            print("\nFailures:")
            for test, trace in result.failures:
                print(f"  - {test}: {trace[:100]}")
        if result.errors:
            print("\nErrors:")
            for test, trace in result.errors:
                print(f"  - {test}: {trace[:100]}")
    print("=" * 80)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
