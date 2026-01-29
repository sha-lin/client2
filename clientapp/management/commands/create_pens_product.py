from django.core.management.base import BaseCommand
from clientapp.models import Product, ProductPricing, ProductVariable, ProductVariableOption, ProductImage, QuantityPricing, User
from decimal import Decimal

class Command(BaseCommand):
    help = 'Create a test Pens product'

    def handle(self, *args, **options):
        # Get admin user or first user
        try:
            admin_user = User.objects.filter(is_staff=True).first() or User.objects.first()
        except:
            self.stdout.write(self.style.ERROR("No user found in database!"))
            return

        # Create the main Product
        product = Product.objects.create(
            name="Pens",
            short_description="Premium quality ballpoint pens perfect for corporate gifts and promotional items",
            long_description="""Our premium ballpoint pens are ideal for bulk corporate orders and promotional campaigns. Available in multiple colors and with custom printing options. High-quality construction ensures smooth writing experience with consistent ink flow. Perfect for businesses looking to distribute branded merchandise.""",
            
            primary_category="Writing Instruments",
            sub_category="Ballpoint Pens",
            product_type="physical",
            product_family="Premium Pens",
            
            customization_level="semi_customizable",
            
            # Technical Specifications
            unit_of_measure="pieces",
            weight=Decimal("8"),
            weight_unit="gsm",
            length=Decimal("14"),
            width=Decimal("1.2"),
            height=Decimal("1.2"),
            dimension_unit="cm",
            warranty="satisfaction-guarantee",
            country_of_origin="china",
            
            # Pricing
            base_price=Decimal("0.30"),
            
            # Stock
            stock_status="made_to_order",
            
            created_by=admin_user
        )

        self.stdout.write(self.style.SUCCESS(f"✓ Created Product: {product.name} (ID: {product.id})"))

        # Create ProductPricing (main pricing configuration)
        pricing = ProductPricing.objects.create(
            product=product,
            pricing_model="variable",
            base_cost=Decimal("0.15"),
            price_display="from",
            default_margin=Decimal("50"),
            minimum_margin=Decimal("35"),
            lead_time_value=7,
            lead_time_unit="days",
            production_method="digital-offset",
            minimum_quantity=100
        )
        
        self.stdout.write(f"✓ Created ProductPricing configuration")

        # Create Quantity-Based Pricing Tiers
        pricing_tiers = [
            {
                "min_quantity": 100,
                "max_quantity": 499,
                "unit_price": Decimal("0.45"),
            },
            {
                "min_quantity": 500,
                "max_quantity": 999,
                "unit_price": Decimal("0.38"),
            },
            {
                "min_quantity": 1000,
                "max_quantity": None,
                "unit_price": Decimal("0.32"),
            }
        ]

        for tier in pricing_tiers:
            qty_pricing = QuantityPricing.objects.create(
                product=product,
                **tier
            )
            max_qty = tier['max_quantity'] if tier['max_quantity'] else "∞"
            self.stdout.write(f"✓ Created Quantity Tier: {tier['min_quantity']}-{max_qty} units @ KES {tier['unit_price']}/unit")

        # Create Product Variables (Customization Options)
        # 1. Pen Color
        pen_color = ProductVariable.objects.create(
            product=product,
            name="Pen Color",
            variable_type="optional",
            pricing_type="none",
            display_order=1
        )

        color_options = [
            "Blue",
            "Black",
            "Red",
            "Green",
            "Silver"
        ]

        for idx, option in enumerate(color_options):
            ProductVariableOption.objects.create(
                variable=pen_color,
                name=option,
                display_order=idx + 1
            )

        self.stdout.write(f"✓ Created Variable: Pen Color (5 options)")

        # 2. Imprint Method
        imprint_method = ProductVariable.objects.create(
            product=product,
            name="Imprint Method",
            variable_type="required",
            pricing_type="fixed",
            display_order=2
        )

        method_options = [
            "Screen Printing",
            "Laser Engraving",
            "Embossing"
        ]

        for idx, option in enumerate(method_options):
            ProductVariableOption.objects.create(
                variable=imprint_method,
                name=option,
                display_order=idx + 1
            )

        self.stdout.write(f"✓ Created Variable: Imprint Method (3 methods)")

        # 3. Imprint Text/Design
        imprint_text = ProductVariable.objects.create(
            product=product,
            name="Imprint Text/Design",
            variable_type="required",
            pricing_type="none",
            display_order=3
        )

        ProductVariableOption.objects.create(
            variable=imprint_text,
            name="Text Input",
            display_order=1
        )

        self.stdout.write(f"✓ Created Variable: Imprint Text/Design (text input)")

        # Create Gallery Images
        images = [
            {
                "alt_text": "Premium ballpoint pens - multiple colors available",
                "display_order": 1,
                "is_primary": True
            },
            {
                "alt_text": "Pens available in multiple color options",
                "display_order": 2,
                "is_primary": False
            },
            {
                "alt_text": "Example of screen printed custom logo on pen",
                "display_order": 3,
                "is_primary": False
            },
            {
                "alt_text": "Pens packaged in bulk quantities ready for shipping",
                "display_order": 4,
                "is_primary": False
            },
            {
                "alt_text": "Premium ballpoint pen in action",
                "display_order": 5,
                "is_primary": False
            }
        ]

        for idx, img in enumerate(images):
            # Using placeholder image URL
            image = ProductImage.objects.create(
                product=product,
                image="products/pen_" + str(idx+1) + ".jpg",
                alt_text=img["alt_text"],
                display_order=img["display_order"],
                is_primary=img["is_primary"]
            )

        self.stdout.write(f"✓ Created {len(images)} Gallery Images")

        output = f"""
{self.style.SUCCESS('='*70)}
{self.style.SUCCESS('SUCCESS! Product "Pens" created')}
{self.style.SUCCESS('='*70)}

Product ID: {product.id}
View at: http://localhost:8000/products/{product.id}/

Product Details:
  - Name: {product.name}
  - Category: {product.primary_category}
  - Customization Level: Semi-Customizable
  - Unit of Measure: {product.unit_of_measure}
  - Weight: {product.weight} {product.weight_unit}
  - Dimensions: {product.length} × {product.width} × {product.height} {product.dimension_unit}
  - Warranty: {product.warranty}
  - Country of Origin: {product.country_of_origin}
  - Pricing Tiers: 3 (100-499, 500-999, 1000+)
  - Product Variables: 3 (Color, Imprint Method, Imprint Text)
  - Gallery Images: {len(images)}
  - Featured: {product.feature_product}
  - Available: {product.is_visible}
"""
        self.stdout.write(output)
