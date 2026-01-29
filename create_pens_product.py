#!/usr/bin/env python
"""
Create a test 'Pens' product for verifying the product creation and detail page workflow
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'client.settings')
django.setup()

from clientapp.models import Product, ProductCategory, ProductPricing, ProductCustomization, ProductCustomizationOption, ProductImage, User
from decimal import Decimal

# Get or create category
category, _ = ProductCategory.objects.get_or_create(
    name="Writing Instruments",
    defaults={
        'slug': 'writing-instruments',
        'description': 'Writing instruments and office supplies'
    }
)

# Get admin user or first user
try:
    admin_user = User.objects.filter(is_staff=True).first() or User.objects.first()
except:
    print("No user found in database!")
    exit(1)

# Create the main Product
product = Product.objects.create(
    name="Pens",
    slug="pens",
    category=category,
    short_description="Premium quality ballpoint pens perfect for corporate gifts and promotional items",
    long_description="""Our premium ballpoint pens are ideal for bulk corporate orders and promotional campaigns. Available in multiple colors and with custom printing options. High-quality construction ensures smooth writing experience with consistent ink flow. Perfect for businesses looking to distribute branded merchandise.""",
    brand="Premium Pens Co.",
    
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
    
    # E-commerce & SEO
    meta_title="Premium Ballpoint Pens | Bulk Corporate Gifts | Custom Printing",
    meta_description="High-quality ballpoint pens for corporate gifts and promotional items. Available for bulk orders with custom printing options. Fast shipping and competitive pricing.",
    meta_keywords="ballpoint pens, promotional pens, corporate gifts, custom printing, bulk pens, branded merchandise",
    is_featured=True,
    is_available=True,
    
    created_by=admin_user
)

print(f"✓ Created Product: {product.name} (ID: {product.id})")

# Create Pricing Tiers
pricing_tiers = [
    {
        "min_quantity": 100,
        "max_quantity": 499,
        "unit_price": Decimal("0.45"),
        "setup_fee": Decimal("25"),
        "lead_time_days": 7
    },
    {
        "min_quantity": 500,
        "max_quantity": 999,
        "unit_price": Decimal("0.38"),
        "setup_fee": Decimal("25"),
        "lead_time_days": 8
    },
    {
        "min_quantity": 1000,
        "max_quantity": 999999,
        "unit_price": Decimal("0.32"),
        "setup_fee": Decimal("50"),
        "lead_time_days": 10
    }
]

for tier in pricing_tiers:
    pricing = ProductPricing.objects.create(
        product=product,
        **tier
    )
    print(f"✓ Created Pricing: {tier['min_quantity']}-{tier['max_quantity']} units @ ${tier['unit_price']}/unit (Setup: ${tier['setup_fee']})")

# Create Customization Options
# 1. Pen Color
pen_color = ProductCustomization.objects.create(
    product=product,
    name="Pen Color",
    description="Select the color of the pen",
    customization_type="color",
    is_required=False,
    price_modifier=Decimal("0"),
    lead_time_addition=0
)

color_options = [
    {"value": "blue", "label": "Blue"},
    {"value": "black", "label": "Black"},
    {"value": "red", "label": "Red"},
    {"value": "green", "label": "Green"},
    {"value": "silver", "label": "Silver"}
]

for option in color_options:
    ProductCustomizationOption.objects.create(
        customization=pen_color,
        value=option["value"],
        label=option["label"]
    )

print(f"✓ Created Customization: Pen Color (5 options)")

# 2. Imprint Method
imprint_method = ProductCustomization.objects.create(
    product=product,
    name="Imprint Method",
    description="Choose how you want your design imprinted",
    customization_type="selection",
    is_required=True,
    price_modifier=Decimal("0.05"),
    lead_time_addition=2
)

method_options = [
    {"value": "screen-printing", "label": "Screen Printing", "price": "0.05", "lead_time": 2},
    {"value": "laser-engraving", "label": "Laser Engraving", "price": "0.15", "lead_time": 3},
    {"value": "embossing", "label": "Embossing", "price": "0.10", "lead_time": 2}
]

for option in method_options:
    ProductCustomizationOption.objects.create(
        customization=imprint_method,
        value=option["value"],
        label=option["label"],
        price_modifier=Decimal(option["price"]),
        lead_time_addition=option["lead_time"]
    )

print(f"✓ Created Customization: Imprint Method (3 methods with price/lead time modifiers)")

# 3. Imprint Text/Design
imprint_text = ProductCustomization.objects.create(
    product=product,
    name="Imprint Text/Design",
    description="Enter your company name or logo design details (max 100 characters)",
    customization_type="text",
    is_required=True,
    max_characters=100,
    price_modifier=Decimal("0"),
    lead_time_addition=0
)

ProductCustomizationOption.objects.create(
    customization=imprint_text,
    value="text-input",
    label="Text Input"
)

print(f"✓ Created Customization: Imprint Text/Design (text input, max 100 chars)")

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
    # Using placeholder image URL - in real scenario you'd upload actual images
    image = ProductImage.objects.create(
        product=product,
        image="products/pen_" + str(idx+1) + ".jpg",  # Placeholder path
        alt_text=img["alt_text"],
        display_order=img["display_order"],
        is_primary=img["is_primary"]
    )
    print(f"✓ Created Image {idx+1}: {img['alt_text']}")

print("\n" + "="*70)
print(f"SUCCESS! Product 'Pens' created with ID: {product.id}")
print("="*70)
print(f"\nAccess product detail page at: http://localhost:8000/products/{product.id}/")
print("\nProduct Details:")
print(f"  - Name: {product.name}")
print(f"  - Category: {product.category.name}")
print(f"  - Unit of Measure: {product.unit_of_measure}")
print(f"  - Weight: {product.weight} {product.weight_unit}")
print(f"  - Dimensions: {product.length} × {product.width} × {product.height} {product.dimension_unit}")
print(f"  - Warranty: {product.warranty}")
print(f"  - Country of Origin: {product.country_of_origin}")
print(f"  - Pricing Tiers: 3 (100-499, 500-999, 1000+)")
print(f"  - Customization Options: 3 (Color, Imprint Method, Imprint Text)")
print(f"  - Gallery Images: 5")
print(f"  - Featured: {product.is_featured}")
print(f"  - Available: {product.is_available}")
