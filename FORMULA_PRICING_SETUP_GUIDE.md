# Formula-Based Pricing Setup Guide

## Issue Resolved ✅

Your formula-based pricing wasn't showing in the calculation breakdown because **ProcessVariableRange** records were missing for your formula-based processes.

## What Was Fixed

1. **Frontend JavaScript**: Updated the pricing calculation to handle formula processes even when variables aren't loaded
2. **Backend Logic**: Added comprehensive debugging to track the issue
3. **Missing Component**: Identified that ProcessVariableRange records were needed but not configured

## Solutions Provided

### 1. **Quick Setup Script** (Python Script)
File: `setup_process_variable_ranges.py`

Run this script to automatically create sample ranges for embroidery processes:

```bash
python setup_process_variable_ranges.py
```

**What it does:**
- Finds all formula-based processes with "embroidery" in the name
- Creates sample variables (Stitch Count, Design Size, Position, Thread Colors, Fabric Type)
- Generates appropriate pricing ranges for each variable type
- Provides comprehensive ranges based on industry standards

### 2. **Web Interface** (Recommended)
Access via: `/processes/` → "Manage Ranges"

**Features:**
- Visual interface to manage variable ranges
- Add/edit/delete ranges easily
- Create sample ranges with one click
- Real-time feedback and validation

**How to use:**
1. Go to `/processes/` in your browser
2. Find your embroidery process (or any formula-based process)
3. Click "Manage Ranges"
4. Use "Create Sample Ranges" for quick setup
5. Or manually add ranges using the "Add Range" button

### 3. **Django Admin Interface**
Access via: `/admin/` → ProcessVariableRange

**Features:**
- Full CRUD operations
- Advanced filtering and search
- Bulk operations

## Setting Up Embroidery Process Ranges

### Sample Ranges for Common Embroidery Variables

#### **Stitch Count** (stitches)
```
Range 1: 1-1,000 stitches → KES 0.15 × 1.0
Range 2: 1,001-5,000 stitches → KES 0.12 × 1.0  
Range 3: 5,001-15,000 stitches → KES 0.10 × 1.0
Range 4: 15,001-30,000 stitches → KES 0.08 × 1.0
Range 5: 30,001+ stitches → KES 0.06 × 1.0
```

#### **Design Size** (cm)
```
Range 1: 1-5 cm → KES 0.50 × 1.0
Range 2: 6-10 cm → KES 0.75 × 1.0
Range 3: 11-20 cm → KES 1.00 × 1.0
Range 4: 21-30 cm → KES 1.50 × 1.0
```

#### **Thread Colors** (colors)
```
Range 1: 1-2 colors → KES 25.00 × 1.0
Range 2: 3-4 colors → KES 40.00 × 1.0
Range 3: 5-6 colors → KES 60.00 × 1.0
Range 4: 7-8 colors → KES 85.00 × 1.0
Range 5: 9-12 colors → KES 120.00 × 1.0
```

#### **Position** (dropdown)
```
Range 1: Chest → KES 50.00 × 1.0
Range 2: Sleeve → KES 75.00 × 1.0
Range 3: Back → KES 100.00 × 1.0
Range 4: Collar → KES 125.00 × 1.0
Range 5: Pocket → KES 60.00 × 1.0
```

## How the Calculation Works

**Formula:** `(Price × Rate) × Quantity = Total Cost`

**Example Calculation:**
- Stitch Count: 50 stitches
- Quantity: 200 pieces
- Range: 1-1,000 stitches = KES 0.15 × 1.0
- Calculation: (0.15 × 1.0) × 200 = KES 30.00

## Step-by-Step Setup Instructions

### Option 1: Use the Web Interface (Recommended)

1. **Access the interface:**
   - Go to: `/processes/`
   - Find your formula-based process
   - Click "Manage Ranges"

2. **Quick setup:**
   - Click "Create Sample Ranges" button
   - This creates intelligent ranges based on variable names
   - Review and adjust prices as needed

3. **Manual setup (if needed):**
   - Click "Add Range" for each variable
   - Fill in Min Value, Max Value, Price, Rate, Order
   - Save and test

### Option 2: Run the Python Script

1. **Navigate to your project directory:**
   ```bash
   cd /path/to/your/django/project
   ```

2. **Run the setup script:**
   ```bash
   python setup_process_variable_ranges.py
   ```

3. **Review the output:**
   - Check which ranges were created
   - Adjust prices according to your actual costing

### Option 3: Use Django Admin

1. **Access admin:**
   - Go to: `/admin/`
   - Login with admin credentials

2. **Navigate to ProcessVariableRange:**
   - Click "ProcessVariableRange" in the admin panel
   - Click "Add ProcessVariableRange"

3. **Create ranges manually:**
   - Select the Variable (process variable)
   - Set Min Value, Max Value, Price, Rate
   - Save

## Testing Your Setup

1. **Go to Product Creation:**
   - Navigate to a product with formula-based pricing
   - Go to "Pricing & Variables" tab
   - Select your formula-based process

2. **Test the calculation:**
   - Go to "Test Your Pricing" section
   - Enter variable values (e.g., Stitch Count: 50)
   - Click "Calculate Pricing"
   - You should now see formula-based costs in the breakdown

3. **Expected result:**
   ```
   CALCULATION BREAKDOWN:
   Base Cost (500 × KES 0): KES 0
   Tier 1 Cost (500 × KES 2,000): KES 1,000,000
   Stitch Count Cost: KES 7.50  ← NEW! Formula-based pricing
   Subtotal EVP: KES 1,000,007.50
   ```

## Common Issues & Solutions

### Issue: "No ranges found for this variable"
**Solution:** Ensure you've created ProcessVariableRange records for that variable

### Issue: "Variable not found in process"
**Solution:** Check that the variable name matches exactly (case-sensitive)

### Issue: "No applicable range found"
**Solution:** Check that your test value falls within the min/max range of your configured ranges

### Issue: Calculation shows 0 for formula cost
**Solution:** Verify that:
- ProcessVariableRange records exist
- Test values are within configured ranges
- Variable names match between frontend and backend

## Best Practices

1. **Start with sample ranges** and adjust prices to match your actual costs
2. **Use meaningful variable names** (e.g., "Stitch Count" instead of "Variable1")
3. **Set appropriate min/max values** to cover all possible inputs
4. **Use the Order field** to prioritize ranges when values might overlap
5. **Test with real values** to ensure calculations are accurate
6. **Document your pricing logic** for future reference

## Files Modified/Created

1. **Frontend:** `clientapp/templates/product_create_edit.html`
   - Fixed JavaScript pricing calculation logic
   - Added debugging for troubleshooting

2. **Backend:** `clientapp/ajax_views.py`
   - Added comprehensive debugging to backend calculation

3. **Web Interface:** 
   - `clientapp/views.py` - Added variable range management views
   - `clientapp/templates/process_list.html` - Process listing interface
   - `clientapp/templates/process_variable_ranges_manager.html` - Range management interface

4. **Admin:** `clientapp/admin.py`
   - Added admin interfaces for Process, ProcessVariable, ProcessVariableRange

5. **URLs:** `clientapp/urls.py`
   - Added routes for the new web interface

6. **Setup Script:** `setup_process_variable_ranges.py`
   - Automated script for creating sample ranges

## Next Steps

1. **Choose your preferred method** (web interface recommended)
2. **Set up ranges for your embroidery process**
3. **Test the pricing calculation** in product creation
4. **Adjust prices** to match your actual costing structure
5. **Add ranges for other formula-based processes** as needed

Your formula-based pricing should now appear correctly in the calculation breakdown! 🎉