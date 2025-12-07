# General Info Section - Implementation Summary

## STATUS: Models ✅ | Forms ✅ | Template ⚠️ | Views ❌ | JavaScript ❌

---

## COMPLETED CHANGES

### ✅ 1. Models (clientapp/models.py)
- Added 'other' to UNIT_CHOICES
- Changed primary_category from ForeignKey to CharField
- Changed sub_category from ForeignKey to CharField  
- Changed product_family from ForeignKey to CharField
- Added unit_of_measure_custom field
- Updated save() method for auto-code generation

### ✅ 2. Forms (clientapp/product_forms.py)
- Updated ProductGeneralInfoForm fields list
- Changed widgets for category/family to TextInput
- Added unit_of_measure_custom field and widget
- Updated clean_internal_code() method

---

## REMAINING CHANGES NEEDED

### ⚠️ 3. TEMPLATE (clientapp/templates/product_create_edit.html)

**NOTE:** The template file may have been corrupted. Please restore from backup first:
`product_create_edit.html.backup`

Then make these changes:

#### Change 3.1: Primary Category (Around line 202-212)
**Find:**
```html
<select name="primary_category" required...>
    <option value="print-products" selected>Print Products</option>
    ...
</select>
```

**Replace with:**
```html
{{ general_form.primary_category }}
{% if general_form.primary_category.errors %}
<p class="text-xs text-red-600 mt-1">{{ general_form.primary_category.errors.0 }}</p>
{% endif %}
<p class="text-xs text-gray-500 mt-1">e.g., Print Products, Signage, Apparel</p>
```

#### Change 3.2: Sub-Category (Around line 213-223)
**Find:**
```html
<select name="sub_category" required...>
    <option value="business-cards" selected>Business Cards</option>
    ...
</select>
```

**Replace with:**
```html
{{ general_form.sub_category }}
{% if general_form.sub_category.errors %}
<p class="text-xs text-red-600 mt-1">{{ general_form.sub_category.errors.0 }}</p>
{% endif %}
<p class="text-xs text-gray-500 mt-1">e.g., Business Cards, Flyers, Brochures</p>
```

#### Change 3.3: Product Family (Around line 247-255)
**Find:**
```html
<select name="product_family"...>
    <option value="business-cards-family" selected>Business Cards Family</option>
    ...
</select>
```

**Replace with:**
```html
{{ general_form.product_family }}
{% if general_form.product_family.errors %}
<p class="text-xs text-red-600 mt-1">{{ general_form.product_family.errors.0 }}</p>
{% endif %}
<p class="text-xs text-gray-500 mt-1">e.g., Business Cards Family</p>
```

#### Change 3.4: Tags Section (Around line 257-294)
**Find:**
```html
<div>
    <label class="block text-sm font-medium text-gray-900 mb-2">Tags</label>
    <div class="flex flex-wrap gap-2 mb-2">
        <span class="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 text-sm rounded">
            business-cards
            <button type="button" class="text-gray-500 hover:text-gray-700">×</button>
        </span>
        <!-- ... more static tags ... -->
    </div>
    <div class="flex gap-2">
        <input type="text" name="new_tag" placeholder="Add tag and press Enter"...>
        <button type="button"...>Add</button>
    </div>
</div>
```

**Replace with:**
```html
<div>
    <label class="block text-sm font-medium text-gray-900 mb-2">Tags</label>
    <div id="tags-container" class="flex flex-wrap gap-2 mb-2">
        <!-- Tags will be added here dynamically -->
    </div>
    <div class="flex gap-2">
        <input type="text" id="new_tag_input" placeholder="Add tag and press Enter"
            class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
        <button type="button" id="add_tag_btn"
            class="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50">
            Add
        </button>
    </div>
</div>
```

#### Change 3.5: Unit of Measure (Around line 353-363)
**Find:**
```html
<div>
    <label class="block text-sm font-medium text-gray-900 mb-1">Unit of Measure</label>
    <select name="unit_of_measure"...>
        <option value="pieces" selected>Pieces</option>
        <option value="packs">Packs</option>
        <option value="sets">Sets</option>
        <option value="sqm">m²</option>
    </select>
</div>
```

**Replace with:**
```html
<div>
    <label class="block text-sm font-medium text-gray-900 mb-1">Unit of Measure</label>
    {{ general_form.unit_of_measure }}
    {% if general_form.unit_of_measure.errors %}
    <p class="text-xs text-red-600 mt-1">{{ general_form.unit_of_measure.errors.0 }}</p>
    {% endif %}
    
    <!-- Custom unit input (shown when "Other" is selected) -->
    <div id="custom_unit_container" class="mt-2" style="display: none;">
        {{ general_form.unit_of_measure_custom }}
        {% if general_form.unit_of_measure_custom.errors %}
        <p class="text-xs text-red-600 mt-1">{{ general_form.unit_of_measure_custom.errors.0 }}</p>
        {% endif %}
    </div>
</div>
```

#### Change 3.6: Save & Next Button (Around line 442-449)
**Find:**
```html
<div class="flex items-center justify-between">
    <button type="button" class="px-4 py-2 text-gray-700 hover:text-gray-900">
        Save Draft
    </button>
    <button type="submit" class="px-6 py-2 bg-black text-white rounded-md hover:bg-gray-800">
        Save & Next →
    </button>
</div>
```

**Replace with:**
```html
<div class="flex items-center justify-between">
    <button type="button" onclick="saveDraft()" class="px-4 py-2 text-gray-700 hover:text-gray-900">
        Save Draft
    </button>
    <button type="button" onclick="saveAndNext('pricing')" class="px-6 py-2 bg-black text-white rounded-md hover:bg-gray-800">
        Save & Next →
    </button>
</div>
```

#### Change 3.7: Add JavaScript (At the END of file, before {% endblock %})
**Add this entire block:**

```html
<script>
// ==================== GENERAL INFO TAB JAVASCRIPT ====================
document.addEventListener('DOMContentLoaded', function() {
    
    // ===== AUTO-GENERATE INTERNAL CODE =====
    const nameInput = document.querySelector('input[name="name"]');
    const codeInput = document.querySelector('input[name="internal_code"]');
    const autoGenCheckbox = document.querySelector('input[name="auto_generate_code"]');
    
    if (nameInput && codeInput && autoGenCheckbox) {
        autoGenCheckbox.checked = true;
        codeInput.readOnly = true;
        
        nameInput.addEventListener('input', function() {
            if (autoGenCheckbox.checked) {
                generateInternalCode();
            }
        });
        
        autoGenCheckbox.addEventListener('change', function() {
            if (this.checked) {
                codeInput.readOnly = true;
                generateInternalCode();
            } else {
                codeInput.readOnly = false;
            }
        });
        
        if (nameInput.value && autoGenCheckbox.checked) {
            generateInternalCode();
        }
    }
    
    function generateInternalCode() {
        const name = nameInput.value.trim();
        if (!name) {
            codeInput.value = '';
            return;
        }
        
        const words = name.split(' ').filter(w => w.length > 0);
        let prefix = 'PRD-';
        
        if (words.length >= 2) {
            prefix += words[0].substring(0, 2).toUpperCase() + words[1].substring(0, 2).toUpperCase();
        } else if (words.length === 1) {
            prefix += words[0].substring(0, Math.min(3, words[0].length)).toUpperCase();
        }
        
        codeInput.value = prefix + '-001';
    }
    
    // ===== UNIT OF MEASURE "OTHER" TOGGLE =====
    const unitSelect = document.querySelector('select[name="unit_of_measure"]');
    const customUnitContainer = document.getElementById('custom_unit_container');
    
    if (unitSelect && customUnitContainer) {
        unitSelect.addEventListener('change', function() {
            if (this.value === 'other') {
                customUnitContainer.style.display = 'block';
            } else {
                customUnitContainer.style.display = 'none';
            }
        });
        
        if (unitSelect.value === 'other') {
            customUnitContainer.style.display = 'block';
        }
    }
    
    // ===== TAGS FUNCTIONALITY =====
    const tagInput = document.getElementById('new_tag_input');
    const addTagBtn = document.getElementById('add_tag_btn');
    const tagsContainer = document.getElementById('tags-container');
    
    if (tagInput && addTagBtn && tagsContainer) {
        addTagBtn.addEventListener('click', function() {
            addTag();
        });
        
        tagInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                addTag();
            }
        });
        
        function addTag() {
            const tagValue = tagInput.value.trim();
            if (!tagValue) return;
            
            const existingTags = Array.from(tagsContainer.querySelectorAll('input[name="tags[]"]'))
                .map(input => input.value);
            if (existingTags.includes(tagValue)) {
                alert('Tag already added');
                return;
            }
            
            const tagSpan = document.createElement('span');
            tagSpan.className = 'inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 text-sm rounded';
            tagSpan.innerHTML = `
                ${tagValue}
                <button type="button" class="text-gray-500 hover:text-gray-700 remove-tag">×</button>
                <input type="hidden" name="tags[]" value="${tagValue}">
            `;
            
            tagSpan.querySelector('.remove-tag').addEventListener('click', function() {
                tagSpan.remove();
            });
            
            tagsContainer.appendChild(tagSpan);
            tagInput.value = '';
        }
    }
    
    // ===== RICH TEXT EDITOR BUTTONS =====
    const longDescTextarea = document.querySelector('textarea[name="long_description"]');
    const editorButtons = document.querySelectorAll('.border-b.border-gray-300 button');
    
    if (longDescTextarea && editorButtons.length > 0) {
        editorButtons.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                const buttonText = this.textContent.trim();
                const start = longDescTextarea.selectionStart;
                const end = longDescTextarea.selectionEnd;
                const selectedText = longDescTextarea.value.substring(start, end);
                
                let wrappedText = '';
                switch(buttonText) {
                    case 'Bold':
                        wrappedText = `**${selectedText || 'bold text'}**`;
                        break;
                    case 'Italic':
                        wrappedText = `*${selectedText || 'italic text'}*`;
                        break;
                    case 'List':
                        wrappedText = `\n- ${selectedText || 'list item'}`;
                        break;
                    case 'Link':
                        const url = prompt('Enter URL:', 'https://');
                        if (url) wrappedText = `[${selectedText || 'link text'}](${url})`;
                        break;
                }
                
                if (wrappedText) {
                    longDescTextarea.value = longDescTextarea.value.substring(0, start) + wrappedText + longDescTextarea.value.substring(end);
                    const newPos = start + wrappedText.length;
                    longDescTextarea.setSelectionRange(newPos, newPos);
                    longDescTextarea.focus();
                }
            });
        });
    }
});

// ===== SAVE AND NAVIGATE FUNCTIONS =====
function saveAndNext(nextTab) {
    const form = document.getElementById('productForm');
    const actionInput = document.getElementById('form_action');
    actionInput.value = 'save_and_next';
    
    let nextTabInput = document.querySelector('input[name="next_tab"]');
    if (!nextTabInput) {
        nextTabInput = document.createElement('input');
        nextTabInput.type = 'hidden';
        nextTabInput.name = 'next_tab';
        form.appendChild(nextTabInput);
    }
    nextTabInput.value = nextTab;
    
    form.submit();
}

function saveDraft() {
    const form = document.getElementById('productForm');
    const actionInput = document.getElementById('form_action');
    actionInput.value = 'save_draft';
    form.submit();
}
</script>
```

---

### ❌ 4. VIEWS (clientapp/views.py)

#### Change 4.1: Update product_create view (Around line 2669)
**After `product.save()` and before any redirect, add:**

```python
# Handle tags
from django.utils.text import slugify
tag_names = request.POST.getlist('tags[]')
for tag_name in tag_names:
    tag_name = tag_name.strip()
    if tag_name:
        tag, created = ProductTag.objects.get_or_create(
            name=tag_name,
            defaults={'slug': slugify(tag_name)}
        )
        product.tags.add(tag)

# Handle custom unit of measure
unit_of_measure = request.POST.get('unit_of_measure')
if unit_of_measure == 'other':
    custom_unit = request.POST.get('unit_of_measure_custom', '').strip()
    if custom_unit:
        product.unit_of_measure_custom = custom_unit
        product.save()
```

#### Change 4.2: Update redirect in product_create (Around line 2847)
**Find:**
```python
return redirect('product_edit', pk=product.pk)
```

**Replace with:**
```python
# Check if we should navigate to next tab
next_tab = request.POST.get('next_tab', '')
if action == 'save_and_next' and next_tab:
    messages.success(request, f'Product "{product.name}" saved! Continue with {next_tab.title()} section.')
    return redirect(f"{reverse('product_edit', kwargs={'pk': product.pk})}?tab={next_tab}")
else:
    return redirect('product_edit', pk=product.pk)
```

#### Change 4.3: Update product_edit view (Around line 2915)
**After `product.save()`, add the same tag and custom unit handling:**

```python
# Handle tags - clear existing and add new ones
from django.utils.text import slugify
product.tags.clear()
tag_names = request.POST.getlist('tags[]')
for tag_name in tag_names:
    tag_name = tag_name.strip()
    if tag_name:
        tag, created = ProductTag.objects.get_or_create(
            name=tag_name,
            defaults={'slug': slugify(tag_name)}
        )
        product.tags.add(tag)

# Handle custom unit of measure
unit_of_measure = request.POST.get('unit_of_measure')
if unit_of_measure == 'other':
    custom_unit = request.POST.get('unit_of_measure_custom', '').strip()
    if custom_unit:
        product.unit_of_measure_custom = custom_unit
        product.save()
```

#### Change 4.4: Update redirect in product_edit (Around line 3017)
**Find:**
```python
return redirect('product_edit', pk=product.pk)
```

**Replace with:**
```python
# Check if we should navigate to next tab
next_tab = request.POST.get('next_tab', '')
if next_tab:
    messages.success(request, f'Product "{product.name}" updated! Continue with {next_tab.title()} section.')
    return redirect(f"{reverse('product_edit', kwargs={'pk': product.pk})}?tab={next_tab}")
else:
    return redirect('product_edit', pk=product.pk)
```

---

## TESTING CHECKLIST

After making all changes:

1. ✅ Restart Django server
2. ✅ Navigate to product creation page
3. ✅ Test auto-code generation (type product name, check code updates)
4. ✅ Test category/family text inputs (type freely)
5. ✅ Test tag add/remove functionality
6. ✅ Test unit of measure "Other" option (select Other, enter custom unit)
7. ✅ Test rich text editor buttons (Bold, Italic, List, Link)
8. ✅ Test Save & Next button (should save and go to Pricing tab)
9. ✅ Test Save Draft button
10. ✅ Verify data is saved to database correctly

---

## NOTES

- The template file may have been corrupted during automated edits
- Restore from `product_create_edit.html.backup` before making changes
- Make changes carefully, one section at a time
- Test after each major change
- Keep a backup of your working files

---

Generated: 2025-11-24
