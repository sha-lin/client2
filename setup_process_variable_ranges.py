#!/usr/bin/env python3
"""
Process Variable Ranges Setup Script
===================================

This script helps you set up ProcessVariableRange records for your formula-based processes.
Especially useful for processes like embroidery that have multiple variables (stitch count, size, position, etc.)

Usage:
1. Run this script in your Django environment
2. It will create sample ranges for common embroidery variables
3. You can modify the ranges based on your actual pricing structure

Variables typically needed for embroidery:
- Stitch Count (stitches)
- Design Size (cm) 
- Position (chest, sleeve, back, etc.)
- Thread Colors
- Fabric Type
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'client.settings')
django.setup()

from clientapp.models import Process, ProcessVariable, ProcessVariableRange

def setup_embroidery_process_ranges():
    """
    Setup comprehensive variable ranges for embroidery processes
    """
    print("=== Setting up Embroidery Process Variable Ranges ===\n")
    
    # Find embroidery processes
    embroidery_processes = Process.objects.filter(
        pricing_type='formula',
        process_name__icontains='embroidery'
    )
    
    if not embroidery_processes.exists():
        print("No embroidery processes found!")
        print("   Make sure you have created a formula-based process with 'embroidery' in the name")
        return
    
    for process in embroidery_processes:
        print(f"Setting up ranges for: {process.process_name} (ID: {process.process_id})")
        
        # Get or create variables for this process
        variables = process.variables.all()
        if not variables.exists():
            print(f"   No variables found for {process.process_name}")
            print(f"       Creating sample variables...")
            create_sample_embroidery_variables(process)
            variables = process.variables.all()
        
        for variable in variables:
            print(f"   Setting up ranges for variable: {variable.variable_name}")
            
            # Check if ranges already exist
            existing_ranges = variable.ranges.all()
            if existing_ranges.exists():
                print(f"      Ranges already exist ({existing_ranges.count()} ranges)")
                continue
            
            # Create appropriate ranges based on variable type
            ranges_created = create_variable_ranges(variable)
            print(f"      Created {ranges_created} ranges")
        print()

def create_sample_embroidery_variables(process):
    """
    Create sample variables for embroidery processes
    """
    print(f"      Creating sample variables for {process.process_name}...")
    
    sample_variables = [
        {
            'variable_name': 'Stitch Count',
            'variable_type': 'number',
            'unit': 'stitches',
            'min_value': 1,
            'max_value': 50000,
            'default_value': 1000,
            'order': 1
        },
        {
            'variable_name': 'Design Size',
            'variable_type': 'number', 
            'unit': 'cm',
            'min_value': 1,
            'max_value': 30,
            'default_value': 5,
            'order': 2
        },
        {
            'variable_name': 'Position',
            'variable_type': 'dropdown',
            'unit': '',
            'min_value': None,
            'max_value': None,
            'default_value': None,
            'order': 3
        },
        {
            'variable_name': 'Thread Colors',
            'variable_type': 'number',
            'unit': 'colors',
            'min_value': 1,
            'max_value': 12,
            'default_value': 2,
            'order': 4
        },
        {
            'variable_name': 'Fabric Type',
            'variable_type': 'dropdown',
            'unit': '',
            'min_value': None,
            'max_value': None,
            'default_value': None,
            'order': 5
        }
    ]
    
    created_count = 0
    for var_data in sample_variables:
        # Check if variable already exists
        existing = ProcessVariable.objects.filter(
            process=process,
            variable_name=var_data['variable_name']
        ).first()
        
        if not existing:
            ProcessVariable.objects.create(process=process, **var_data)
            created_count += 1
            print(f"        Created variable: {var_data['variable_name']}")
        else:
            print(f"        Variable already exists: {var_data['variable_name']}")
    
    print(f"      Created {created_count} new variables")
    return created_count

def create_variable_ranges(variable):
    """
    Create pricing ranges for a specific variable based on its type and name
    """
    ranges_created = 0
    
    # Stitch Count ranges (most common embroidery variable)
    if 'stitch' in variable.variable_name.lower():
        ranges_created = create_stitch_count_ranges(variable)
    
    # Design Size ranges
    elif 'size' in variable.variable_name.lower() and variable.variable_type == 'number':
        ranges_created = create_size_ranges(variable)
    
    # Position ranges (dropdown)
    elif 'position' in variable.variable_name.lower() and variable.variable_type == 'dropdown':
        ranges_created = create_position_ranges(variable)
    
    # Thread Colors ranges
    elif 'color' in variable.variable_name.lower():
        ranges_created = create_thread_color_ranges(variable)
    
    # Fabric Type ranges (dropdown)
    elif 'fabric' in variable.variable_name.lower() and variable.variable_type == 'dropdown':
        ranges_created = create_fabric_type_ranges(variable)
    
    # Generic number ranges for other variables
    elif variable.variable_type == 'number':
        ranges_created = create_generic_number_ranges(variable)
    
    # Generic dropdown for other dropdown variables
    elif variable.variable_type == 'dropdown':
        ranges_created = create_generic_dropdown_ranges(variable)
    
    return ranges_created

def create_stitch_count_ranges(variable):
    """
    Create pricing ranges for stitch count
    Typical embroidery pricing: more stitches = higher cost
    """
    ranges = [
        # (min, max, price, rate, order)
        (1, 1000, Decimal('0.15'), Decimal('1.0'), 1),      # Small designs
        (1001, 5000, Decimal('0.12'), Decimal('1.0'), 2),   # Medium designs  
        (5001, 15000, Decimal('0.10'), Decimal('1.0'), 3),  # Large designs
        (15001, 30000, Decimal('0.08'), Decimal('1.0'), 4), # Very large designs
        (30001, 50000, Decimal('0.06'), Decimal('1.0'), 5), # Maximum size
    ]
    
    return create_ranges_from_data(variable, ranges)

def create_size_ranges(variable):
    """
    Create pricing ranges for design size (in cm)
    """
    ranges = [
        (1, 5, Decimal('0.50'), Decimal('1.0'), 1),     # Small (1-5cm)
        (6, 10, Decimal('0.75'), Decimal('1.0'), 2),    # Medium (6-10cm)
        (11, 20, Decimal('1.00'), Decimal('1.0'), 3),   # Large (11-20cm)
        (21, 30, Decimal('1.50'), Decimal('1.0'), 4),   # Extra Large (21-30cm)
    ]
    
    return create_ranges_from_data(variable, ranges)

def create_position_ranges(variable):
    """
    Create pricing ranges for embroidery position
    Different positions have different difficulty levels
    """
    ranges = [
        # For dropdown variables, we use price as fixed cost and rate as multiplier
        (1, 1, Decimal('50.00'), Decimal('1.0'), 1),     # Chest - easiest
        (2, 2, Decimal('75.00'), Decimal('1.0'), 2),     # Sleeve - medium
        (3, 3, Decimal('100.00'), Decimal('1.0'), 3),    # Back - harder
        (4, 4, Decimal('125.00'), Decimal('1.0'), 4),    # Collar - hardest
        (5, 5, Decimal('60.00'), Decimal('1.0'), 5),     # Pocket - medium
    ]
    
    return create_ranges_from_data(variable, ranges)

def create_thread_color_ranges(variable):
    """
    Create pricing ranges for number of thread colors
    More colors = more thread changes = higher cost
    """
    ranges = [
        (1, 2, Decimal('25.00'), Decimal('1.0'), 1),      # 1-2 colors
        (3, 4, Decimal('40.00'), Decimal('1.0'), 2),      # 3-4 colors
        (5, 6, Decimal('60.00'), Decimal('1.0'), 3),      # 5-6 colors
        (7, 8, Decimal('85.00'), Decimal('1.0'), 4),      # 7-8 colors
        (9, 12, Decimal('120.00'), Decimal('1.0'), 5),    # 9-12 colors
    ]
    
    return create_ranges_from_data(variable, ranges)

def create_fabric_type_ranges(variable):
    """
    Create pricing ranges for fabric type
    Different fabrics have different difficulty levels
    """
    ranges = [
        (1, 1, Decimal('30.00'), Decimal('1.0'), 1),      # Cotton - easiest
        (2, 2, Decimal('45.00'), Decimal('1.0'), 2),      # Polyester - medium
        (3, 3, Decimal('60.00'), Decimal('1.0'), 3),      # Denim - harder
        (4, 4, Decimal('80.00'), Decimal('1.0'), 4),      # Leather - hardest
        (5, 5, Decimal('40.00'), Decimal('1.0'), 5),      # Blends - medium
    ]
    
    return create_ranges_from_data(variable, ranges)

def create_generic_number_ranges(variable):
    """
    Create generic pricing ranges for number variables
    """
    ranges = [
        (1, 10, Decimal('10.00'), Decimal('1.0'), 1),
        (11, 50, Decimal('8.00'), Decimal('1.0'), 2),
        (51, 100, Decimal('6.00'), Decimal('1.0'), 3),
        (101, 500, Decimal('4.00'), Decimal('1.0'), 4),
        (501, 1000, Decimal('2.00'), Decimal('1.0'), 5),
    ]
    
    return create_ranges_from_data(variable, ranges)

def create_generic_dropdown_ranges(variable):
    """
    Create generic pricing ranges for dropdown variables
    """
    ranges = [
        (1, 1, Decimal('20.00'), Decimal('1.0'), 1),
        (2, 2, Decimal('35.00'), Decimal('1.0'), 2),
        (3, 3, Decimal('50.00'), Decimal('1.0'), 3),
        (4, 4, Decimal('70.00'), Decimal('1.0'), 4),
        (5, 5, Decimal('90.00'), Decimal('1.0'), 5),
    ]
    
    return create_ranges_from_data(variable, ranges)

def create_ranges_from_data(variable, ranges_data):
    """
    Create ProcessVariableRange records from data tuple
    """
    ranges_created = 0
    for min_val, max_val, price, rate, order in ranges_data:
        # Handle None values for min/max
        min_value = Decimal(str(min_val)) if min_val is not None else None
        max_value = Decimal(str(max_val)) if max_val is not None else None
        
        range_obj = ProcessVariableRange.objects.create(
            variable=variable,
            min_value=min_value,
            max_value=max_value,
            price=price,
            rate=rate,
            order=order
        )
        ranges_created += 1
        
        range_str = f"Range {order}: {min_val}-{max_val}"
        if variable.unit:
            range_str += f" {variable.unit}"
        print(f"         {range_str} -> KES {price} x {rate}")
    
    return ranges_created

def show_process_summary():
    """
    Show summary of all processes and their variable ranges
    """
    print("\n" + "="*60)
    print("PROCESS VARIABLE RANGES SUMMARY")
    print("="*60)
    
    processes = Process.objects.filter(pricing_type='formula').prefetch_related('variables__ranges')
    
    for process in processes:
        print(f"\nProcess: {process.process_name} (ID: {process.process_id})")
        
        variables = process.variables.all()
        if not variables.exists():
            print("   No variables configured")
            continue
            
        for variable in variables:
            ranges_count = variable.ranges.count()
            status = "OK" if ranges_count > 0 else "NO"
            print(f"   {status} {variable.variable_name}: {ranges_count} ranges")
            
            if ranges_count > 0:
                for range_obj in variable.ranges.order_by('order'):
                    range_str = f"{range_obj.min_value}-{range_obj.max_value}"
                    if variable.unit:
                        range_str += f" {variable.unit}"
                    print(f"      {range_str}: KES {range_obj.price} × {range_obj.rate}")

def main():
    """
    Main function to setup process variable ranges
    """
    print("Process Variable Ranges Setup")
    print("=" * 40)
    
    # Check if we have any formula-based processes
    formula_processes = Process.objects.filter(pricing_type='formula')
    if not formula_processes.exists():
        print("No formula-based processes found!")
        print("   Create a process with pricing_type='formula' first")
        return
    
    print(f"Found {formula_processes.count()} formula-based processes")
    
    # Setup ranges for embroidery processes
    setup_embroidery_process_ranges()
    
    # Show summary
    show_process_summary()
    
    print(f"\nSetup complete!")
    print(f"\nNext steps:")
    print(f"   1. Review the ranges created above")
    print(f"   2. Adjust prices according to your actual costing")
    print(f"   3. Test the pricing calculation in your product creation")
    print(f"   4. Add more ranges for other processes as needed")

if __name__ == '__main__':
    main()