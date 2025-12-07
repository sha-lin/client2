# Template Changes for General Info Section

## ✅ COMPLETED CHANGES:
- ✅ Models updated (auto_generate_code, unit_of_measure_custom, category fields as CharField)
- ✅ Forms updated (TextInput widgets for categories, unit_of_measure_custom field)
- ✅ Views updated (tag handling, custom unit handling, tab navigation)

## 🔧 REMAINING TEMPLATE CHANGES:

### File: `clientapp/templates/product_create_edit.html`

---

### CHANGE 1: Update Tags Section (Lines 222-259)
**Location:** Find the Tags section around line 222

**REPLACE THIS:**
```html
                <div>
                    <label class="block text-sm font-medium text-gray-900 mb-2">Tags</label>
                    <div class="flex flex-wrap gap-2 mb-2">
                        <span
                            class="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 text-sm rounded">
                            business-cards
                            <button type="button" class="text-gray-500 hover:text-gray-700">×</button>
                        </span>
                        <!-- ... more hardcoded tags ... -->
                    </div>
                    <div class="flex gap-2">
                        <input type="text" name="new_tag" placeholder="Add tag and press Enter"
                            class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                        <button type="button"
                            class="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50">
                            Add
                        </button>
                    </div>
                </div>
```

**WITH THIS:**
```html
                <div>
                    <label class="block text-sm font-medium text-gray-900 mb-2">Tags</label>
                    <div id="tags-container" class="flex flex-wrap gap-2 mb-2">
                        {% if product %}
                            {% for tag in product.tags.all %}
                            <span class="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 text-sm rounded">
                                {{ tag.name }}
                                <button type="button" class="text-gray-500 hover:text-gray-700" onclick="this.parentElement.remove()">×</button>
                                <input type="hidden" name="tags[]" value="{{ tag.name }}">
                            </span>
                            {% endfor %}
                        {% endif %}
                    </div>
                    <div class="flex gap-2">
                        <input type="text" id="new_tag_input" name="new_tag" placeholder="Add tag and press Enter"
                            class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                        <button type="button" id="add_tag_btn"
                            class="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50">
                            Add
                        </button>
                    </div>
                </div>
```

---

### CHANGE 2: Update "Save & Next" Button (Line ~412)
**Location:** Find the "Save & Next" button around line 412

**REPLACE THIS:**
```html
            <button type="submit" class="px-6 py-2 bg-black text-white rounded-md hover:bg-gray-800">
                Save & Next →
            </button>
```

**WITH THIS:**
```html
            <button type="button" onclick="saveAndNext('pricing')" class="px-6 py-2 bg-black text-white rounded-md hover:bg-gray-800">
                Save & Next →
            </button>
```

---

### CHANGE 3: Add Hidden Input for Form Action
**Location:** Right after the opening `<form>` tag (around line 91-92)

**ADD THIS AFTER `{% csrf_token %}`:**
```html
        <input type="hidden" id="form_action" name="action" value="save_draft">
```

---

### CHANGE 4: Add JavaScript at the END of the file
**Location:** Find the `{% block extra_js %}` section at the very end of the file

**ADD THIS JAVASCRIPT** (before the closing `</script>` tag):

```javascript
// Auto-generate internal code based on product name
const nameInput = document.querySelector('input[name="name"]');
const codeInput = document.querySelector('input[name="internal_code"]');
const autoGenCheckbox = document.querySelector('input[name="auto_generate_code"]');

if (nameInput && codeInput && autoGenCheckbox) {
    nameInput.addEventListener('input', function() {
        if (autoGenCheckbox.checked) {
            generateInternalCode();
        }
    });
    
    autoGenCheckbox.addEventListener('change', function() {
        if (this.checked) {
            generateInternalCode();
        }
    });
}

function generateInternalCode() {
    const name = nameInput.value.trim();
    if (!name) return;
    
    const words = name.split(' ');
    let prefix = 'PRD-';
    
    if (words.length >= 2) {
        prefix += words[0].substring(0, 2).toUpperCase() + words[1].substring(0, 2).toUpperCase();
    } else {
        prefix += name.substring(0, 3).toUpperCase();
    }
    
    codeInput.value = prefix + '-001';
    codeInput.readOnly = true;
}

// Handle Unit of Measure "Other" option
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
    
    // Check on page load
    if (unitSelect.value === 'other') {
        customUnitContainer.style.display = 'block';
    }
}

// Tags functionality
const tagInput = document.getElementById('new_tag_input');
const addTagBtn = document.getElementById('add_tag_btn');
const tagsContainer = document.getElementById('tags-container');

if (tagInput && addTagBtn && tagsContainer) {
    // Add tag on button click
    addTagBtn.addEventListener('click', function() {
        addTag();
    });
    
    // Add tag on Enter key
    tagInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            addTag();
        }
    });
    
    function addTag() {
        const tagValue = tagInput.value.trim();
        if (!tagValue) return;
        
        // Create tag element
        const tagSpan = document.createElement('span');
        tagSpan.className = 'inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 text-sm rounded';
        tagSpan.innerHTML = `
            ${tagValue}
            <button type="button" class="text-gray-500 hover:text-gray-700" onclick="this.parentElement.remove()">×</button>
            <input type="hidden" name="tags[]" value="${tagValue}">
        `;
        
        tagsContainer.appendChild(tagSpan);
        tagInput.value = '';
    }
}

// Rich text editor buttons for long description
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
                    wrappedText = `**${selectedText}**`;
                    break;
                case 'Italic':
                    wrappedText = `*${selectedText}*`;
                    break;
                case 'List':
                    wrappedText = `\n- ${selectedText}`;
                    break;
                case 'Link':
                    const url = prompt('Enter URL:');
                    if (url) wrappedText = `[${selectedText}](${url})`;
                    break;
            }
            
            if (wrappedText) {
                longDescTextarea.value = longDescTextarea.value.substring(0, start) + wrappedText + longDescTextarea.value.substring(end);
            }
        });
    });
}

// Save and navigate to next tab
function saveAndNext(nextTab) {
    const form = document.getElementById('productForm');
    const actionInput = document.getElementById('form_action');
    actionInput.value = 'save_and_next';
    
    // Add hidden field to indicate next tab
    const nextTabInput = document.createElement('input');
    nextTabInput.type = 'hidden';
    nextTabInput.name = 'next_tab';
    nextTabInput.value = nextTab;
    form.appendChild(nextTabInput);
    
    form.submit();
}

// Save as draft
function saveDraft() {
    const form = document.getElementById('productForm');
    const actionInput = document.getElementById('form_action');
    actionInput.value = 'save_draft';
    form.submit();
}

// Update existing submitForm function to work with new system
function submitForm(action) {
    const form = document.getElementById('productForm');
    const actionInput = document.getElementById('form_action');
    actionInput.value = action;
    form.submit();
}
```

---

## 📝 NOTES:
1. The Primary Category, Sub-Category, and Product Family fields are already using Django form rendering (`{{ general_form.field_name }}`), so they will automatically be text inputs since we updated the form widgets.

2. The Unit of Measure field also uses Django form rendering, so the "Other" option will appear automatically. However, you need to add the custom unit input field if it's not already there.

3. All backend changes (models, forms, views) are complete and working.

4. After making these template changes, test thoroughly:
   - Auto-code generation
   - Tag adding/removing
   - Rich text editor buttons
   - Save & Next navigation
   - Unit of Measure "Other" option

## ✅ TESTING CHECKLIST:
- [ ] Auto-generate code works when typing product name
- [ ] Can add tags using "Add" button
- [ ] Can remove tags by clicking ×
- [ ] Tags are saved with the product
- [ ] Rich text editor buttons work (Bold, Italic, List, Link)
- [ ] "Save & Next" navigates to Pricing & Variables tab
- [ ] Unit of Measure "Other" shows custom input field
- [ ] Form saves correctly and data persists
