# 📌 QUICK REFERENCE CARD - Copy & Paste Guide

## ✅ COMPLETED
- models.py: ✓ Added process field to ProductPricing
- models.py: ✓ Added source_process_variable to ProductVariable

---

## 🔧 TODO - Copy & Paste These Exact Code Snippets

### 1️⃣ MIGRATION (Run in terminal)
```bash
python manage.py makemigrations clientapp --name add_process_integration
python manage.py migrate
```

---

### 2️⃣ HTML (product_create_edit.html ~line563, BEFORE "Production & Vendor Information")
Copy lines 20-115 from IMPLEMENTATION_CODE_SNIPPETS.py

---

### 3️⃣ JAVASCRIPT (product_create_edit.html, near bottom before {% endblock %})
Copy lines 125-250 from IMPLEMENTATION_CODE_SNIPPETS.py

---

### 4️⃣ VIEWS - Add at TOP of views.py
```python
from .models import Process, ProcessVariable, ProcessTier, ProductVariableOption
```

---

### 5️⃣ VIEWS - In product_create() function, ADD:
```python
# Get processes for dropdown
processes = Process.objects.filter(status='active').order_by('process_name')

# In context dictionary, ADD:
context = {
    # existing items...
    'processes': processes,
}
```

---

### 6️⃣ VIEWS - Add these 2 NEW FUNCTIONS (copy from IMPLEMENTATION_CODE_SNIPPETS.py lines 280-380):
```python
def import_process_variables_to_product(process, product):
   # ... full code in IMPLEMENTATION_CODE_SNIPPETS.py

def ajax_process_variables(request, process_id):
    # ... full code in IMPLEMENTATION_CODE_SNIPPETS.py
```

---

### 7️⃣ URLS (clientapp/urls.py) - ADD to urlpatterns:
```python
path('ajax/process/<int:process_id>/variables/', ajax_process_variables, name='ajax_process_variables'),
```

---

## 🧪 TEST
1. Create a process in /processes/create
2. Create product → Pricing tab → Select process
3. Check "Auto-import variables"  
4. Save → Verify variables imported

---

## 📁 FILES TO EDIT
1. ✅ models.py (DONE)
2. product_create_edit.html (2 sections)
3. views.py (3 changes)
4. urls.py (1 line)

TOTAL: 4 files, ~6 edits, ~20 minutes

See IMPLEMENTATION_CODE_SNIPPETS.py for exact code!
