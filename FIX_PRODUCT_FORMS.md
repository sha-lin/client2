# URGENT FIX NEEDED - product_forms.py is corrupted

## Problem:
The `product_forms.py` file got corrupted during automated edits. You need to manually fix it.

## Solution:

### STEP 1: Restore the file structure
The file is missing the class definition. Around line 16-17, you'll see orphaned widget definitions.

### STEP 2: Find this corrupted section (around line 16):
```python
)

                'placeholder': 'Premium Business Cards',
                'required': True
            }),
            'internal_code': forms.TextInput(attrs={
```

### STEP 3: Replace it with:
```python
)


# ==================== PRODUCT GENERAL INFO FORM ====================

class ProductGeneralInfoForm(forms.ModelForm):
    """Form for General Product Information"""
    
    class Meta:
        model = Product
        fields = [
            # Basic Information
            'name', 'internal_code',
            'short_description', 'long_description', 'technical_specs',
            
            # Classification
            'primary_category', 'sub_category', 'product_family',
            'product_type', 'tags',
            
            # Status & Visibility
            'status', 'is_visible', 'visibility',
            'feature_product', 'bestseller_badge', 'new_arrival',
            'new_arrival_expires', 'on_sale_badge',
            
            # Product Attributes
            'unit_of_measure', 'unit_of_measure_custom', 'weight', 'weight_unit',
            'length', 'width', 'height', 'dimension_unit',
            'warranty', 'country_of_origin',
            
            # Notes
            'internal_notes', 'client_notes',
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Premium Business Cards',
                'required': True
            }),
            'internal_code': forms.TextInput(attrs={
```

### STEP 4: Remove the `auto_generate_code` widget
Find and DELETE these lines (around line 25-28):
```python
            'auto_generate_code': forms.CheckboxInput(attrs={
                'class': 'rounded',
                'checked': 'checked'
            }),
```

## After fixing, run:
```bash
python manage.py makemigrations clientapp
python manage.py migrate
```

## This will:
1. Fix the corrupted file structure
2. Remove the auto_generate_code field from the form (since it's now editable=False in the model)
3. Allow migrations to run successfully
4. Enable auto-generation of internal codes in both admin and frontend
