"""
Management command to populate storefront with sample products.
Usage: python manage.py populate_storefront_products
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
from clientapp.models import StorefrontProduct


class Command(BaseCommand):
    help = 'Populate storefront with sample products'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting product population...'))

        products_data = [
            {
                'product_id': 'PROD-BC-001',
                'name': 'Business Cards - Standard',
                'description_short': 'Premium business cards on 350gsm card',
                'description_long': 'High-quality business cards printed on premium 350gsm card. Available in full color. Turnaround: 7 days standard, 3 days rush.',
                'category': 'business_cards',
                'base_price': Decimal('2500.00'),
                'price_range_min': Decimal('2500.00'),
                'price_range_max': Decimal('19000.00'),
                'pricing_tiers': [
                    {'min_qty': 100, 'max_qty': 250, 'price_per_unit': '25.00'},
                    {'min_qty': 251, 'max_qty': 500, 'price_per_unit': '21.00'},
                    {'min_qty': 501, 'max_qty': 1000, 'price_per_unit': '19.00'},
                    {'min_qty': 1001, 'max_qty': 999999, 'price_per_unit': '17.00'},
                ],
                'storefront_visible': True,
                'show_price': True,
                'featured': True,
                'customization_level': 'fully_customizable',
                'available_customizations': {
                    'size': ['50x90mm', '85x55mm'],
                    'color': ['Full Color', 'B&W'],
                    'finish': ['Matte', 'Glossy', 'Embossed']
                },
                'turnaround_standard_days': 7,
                'turnaround_rush_days': 3,
                'turnaround_rush_surcharge': Decimal('1000.00'),
                'turnaround_expedited_days': 1,
                'turnaround_expedited_surcharge': Decimal('2500.00'),
                'minimum_order_quantity': 100,
                'rating': Decimal('4.8'),
                'review_count': 127,
            },
            {
                'product_id': 'PROD-TSHIRT-001',
                'name': 'Branded T-Shirts',
                'description_short': 'Custom printed T-shirts in various sizes',
                'description_long': 'Premium quality T-shirts with custom screen printing or embroidery. Available in various sizes and colors.',
                'category': 't_shirts',
                'base_price': Decimal('500.00'),
                'price_range_min': Decimal('500.00'),
                'price_range_max': Decimal('3500.00'),
                'pricing_tiers': [
                    {'min_qty': 50, 'max_qty': 100, 'price_per_unit': '500.00'},
                    {'min_qty': 101, 'max_qty': 250, 'price_per_unit': '450.00'},
                    {'min_qty': 251, 'max_qty': 500, 'price_per_unit': '400.00'},
                    {'min_qty': 501, 'max_qty': 999999, 'price_per_unit': '350.00'},
                ],
                'storefront_visible': True,
                'featured': True,
                'customization_level': 'fully_customizable',
                'available_customizations': {
                    'size': ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
                    'color': ['Black', 'White', 'Red', 'Blue', 'Green'],
                    'printing': ['Screen Print', 'Embroidery', 'Direct Print']
                },
                'turnaround_standard_days': 10,
                'turnaround_rush_days': 5,
                'turnaround_rush_surcharge': Decimal('2000.00'),
                'turnaround_expedited_days': 2,
                'turnaround_expedited_surcharge': Decimal('4000.00'),
                'minimum_order_quantity': 50,
                'rating': Decimal('4.5'),
                'review_count': 89,
            },
            {
                'product_id': 'PROD-BANNER-001',
                'name': 'Vinyl Banners',
                'description_short': 'Custom printed vinyl banners',
                'description_long': 'High-quality vinyl banners with weather-resistant printing. Perfect for outdoor advertising.',
                'category': 'signage',
                'base_price': Decimal('3000.00'),
                'price_range_min': Decimal('3000.00'),
                'price_range_max': Decimal('25000.00'),
                'pricing_tiers': [
                    {'min_qty': 1, 'max_qty': 5, 'price_per_unit': '3000.00'},
                    {'min_qty': 6, 'max_qty': 20, 'price_per_unit': '2800.00'},
                ],
                'storefront_visible': True,
                'featured': True,
                'customization_level': 'fully_customizable',
                'turnaround_standard_days': 5,
                'turnaround_rush_days': 2,
                'turnaround_rush_surcharge': Decimal('1500.00'),
                'minimum_order_quantity': 1,
                'rating': Decimal('4.7'),
                'review_count': 156,
            },
        ]

        count = 0
        for product_data in products_data:
            product, created = StorefrontProduct.objects.get_or_create(
                product_id=product_data['product_id'],
                defaults=product_data
            )
            if created:
                count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {product.name}')
                )
            else:
                self.stdout.write(f'- Already exists: {product.name}')

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Successfully created {count} products!')
        )
