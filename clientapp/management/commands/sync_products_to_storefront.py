"""
Management command to sync visible products from Product model to StorefrontProduct.
This syncs all products marked as is_visible=True in the Product model to StorefrontProduct.

Usage: python manage.py sync_products_to_storefront
       python manage.py sync_products_to_storefront --force (to overwrite existing)
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from decimal import Decimal
from clientapp.models import Product, StorefrontProduct


class Command(BaseCommand):
    help = 'Sync visible products from Product model to StorefrontProduct'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            help='Overwrite existing StorefrontProduct records',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        self.stdout.write(self.style.SUCCESS('Starting product sync from Product to StorefrontProduct...'))
        self.stdout.write('')

        # Get all visible products
        visible_products = Product.objects.filter(is_visible=True, status='published')
        
        if not visible_products.exists():
            self.stdout.write(self.style.WARNING('No visible published products found to sync!'))
            return

        self.stdout.write(f'Found {visible_products.count()} visible products to sync')
        self.stdout.write('')

        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        for product in visible_products:
            try:
                # Use internal_code as product_id, or generate one
                product_id = product.internal_code or f"PROD-{product.id}"
                
                # Prepare data for StorefrontProduct
                storefront_data = {
                    'name': product.name,
                    'description_short': product.short_description or '',
                    'description_long': product.long_description or '',
                    'category': product.primary_category or 'uncategorized',
                    'storefront_visible': True,  # Only sync visible products
                    'show_price': True,
                    'featured': product.feature_product or product.bestseller_badge,
                    'customization_level': product.customization_level or 'semi_customizable',
                    'available_customizations': {},
                }

                # Try to get base price from ProductPricing
                base_price = Decimal('0.00')
                try:
                    pricing = product.productpricing_set.first()
                    if pricing and pricing.base_cost:
                        # Apply default margin to get customer-facing price
                        base_price = pricing.base_cost * (1 + Decimal(pricing.default_margin or 0.3))
                except:
                    pass
                
                storefront_data['base_price'] = base_price or Decimal('100.00')
                storefront_data['price_range_min'] = storefront_data['base_price']
                storefront_data['price_range_max'] = storefront_data['base_price'] * 3

                # Get or create StorefrontProduct
                storefront_product, created = StorefrontProduct.objects.get_or_create(
                    product_id=product_id,
                    defaults=storefront_data
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ CREATED: {product.name} (ID: {product_id})')
                    )
                elif force:
                    # Update existing record
                    for field, value in storefront_data.items():
                        setattr(storefront_product, field, value)
                    storefront_product.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ UPDATED: {product.name} (ID: {product_id})')
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(f'- SKIPPED: {product.name} (already exists, use --force to update)')

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ ERROR syncing {product.name}: {str(e)}')
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== SYNC COMPLETE ==='))
        self.stdout.write(f'Created:  {created_count}')
        self.stdout.write(f'Updated:  {updated_count}')
        self.stdout.write(f'Skipped:  {skipped_count}')
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Errors:   {error_count}'))
        
        total_in_storefront = StorefrontProduct.objects.filter(storefront_visible=True).count()
        self.stdout.write(f'Total visible products in storefront: {total_in_storefront}')
