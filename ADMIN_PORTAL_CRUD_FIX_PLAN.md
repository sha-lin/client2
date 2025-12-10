# Admin Portal CRUD Fix Plan

## Current Status

### ✅ WORKING (Full CRUD with modals):
1. **SYSTEM: Users** - Complete CRUD with modal forms
2. **BUSINESS: Clients** - Complete CRUD with modal forms  
3. **BUSINESS: Leads** - Complete CRUD with modal forms
4. **BUSINESS: Quotes** - Modal form created (needs table button fixes)
5. **BUSINESS: Products** - Modal form created (needs table button fixes)

### ⏳ NEEDS FIXING (API endpoints exist but no modal forms):
1. **OPERATIONS: Jobs** - api_admin_jobs endpoint exists (missing create/read/update/delete)
2. **OPERATIONS: Vendors** - api_admin_vendors endpoint exists (missing create/read/update/delete)
3. **OPERATIONS: Processes** - NO API endpoint (needs full implementation)
4. **OPERATIONS: QC** - api_admin_qc_inspections endpoint exists (missing create/read/update/delete)
5. **OPERATIONS: Deliveries** - api_admin_deliveries endpoint exists (missing create/read/update/delete)
6. **FINANCIAL: LPOs** - api_admin_lpos endpoint exists (missing create/read/update/delete)
7. **FINANCIAL: Payments** - api_admin_payments endpoint exists (missing create/read/update/delete)
8. **FINANCIAL: Analytics** - Read-only (no CRUD needed, display only)
9. **SYSTEM: System Alerts** - Read-only (admin cannot create/edit)
10. **SYSTEM: Settings** - Configuration page (admin cannot create/edit)

## Fix Strategy

For each tab that needs CRUD:

### Phase 1: Quotes & Products (COMPLETE IMMEDIATELY)
- Add view modal to display all details
- Update table action buttons to use edit/delete functions
- Ensure no external redirects

### Phase 2: Jobs, Vendors, QC, Deliveries (THIS SPRINT)
- Add individual CRUD API endpoints (create, get, update, delete)
- Add modal form to template
- Add JavaScript functions (openCreateModal, openEditModal, submitForm, deleteItem, closeModal)
- Add view modal for detailed viewing
- Update table with action buttons (Edit, Delete, View)

### Phase 3: Processes, LPOs, Payments (THIS SPRINT)
- Create missing API endpoints if needed
- Add modal forms to templates
- Add CRUD JavaScript functions
- Update tables with action buttons

## Template Structure for Each Tab

Each template should have:

```html
<!-- Button in header -->
<button onclick="openCreateModal()" class="btn btn-primary">+ New [Item]</button>

<!-- Create/Edit Modal -->
<div id="itemModal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h2 id="modalTitle">Add New Item</h2>
            <button class="modal-close" onclick="closeModal()">×</button>
        </div>
        <form id="itemForm" onsubmit="submitForm(event)">
            {% csrf_token %}
            <input type="hidden" id="itemId" name="item_id" value="">
            <!-- All form fields here -->
        </form>
    </div>
</div>

<!-- View Modal (for read-only detailed view) -->
<div id="viewModal" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h2>Item Details</h2>
            <button class="modal-close" onclick="closeViewModal()">×</button>
        </div>
        <div id="viewContent" style="padding: 24px;">
            <!-- Details displayed here -->
        </div>
    </div>
</div>

<!-- Table with action buttons -->
<table>
    <thead>...</thead>
    <tbody>
        {% for item in items %}
        <tr>
            <!-- Item data -->
            <td>
                <button data-action="view" data-id="{{ item.id }}" class="btn btn-sm">👁️ View</button>
                <button data-action="edit" data-id="{{ item.id }}" class="btn btn-sm">✎ Edit</button>
                <button data-action="delete" data-id="{{ item.id }}" class="btn btn-sm">✕ Delete</button>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<!-- JavaScript functions -->
<script>
    function openCreateModal() { /* ... */ }
    function openEditModal(id) { /* ... */ }
    function openViewModal(id) { /* ... */ }
    function closeModal() { /* ... */ }
    function closeViewModal() { /* ... */ }
    function submitForm(event) { /* ... */ }
    function deleteItem(id) { /* ... */ }
</script>
```

## API Endpoint Requirements

Each model needs 4 CRUD endpoints:

1. **CREATE** - POST `/api/admin/[resource]/create/`
   - Accepts form data
   - Validates required fields
   - Returns: `{success: true/false, id: int, message: str}`

2. **READ** - GET `/api/admin/[resource]/<int:id>/get/`
   - Returns all fields as JSON
   - Used to populate edit form

3. **UPDATE** - POST `/api/admin/[resource]/<int:id>/update/`
   - Updates fields
   - Returns: `{success: true/false, message: str}`

4. **DELETE** - POST `/api/admin/[resource]/<int:id>/delete/`
   - Deletes record
   - Returns: `{success: true/false, message: str}`

## Implementation Order (Priority)

1. **TODAY - Critical fixes:**
   - ✅ Quotes: Fix table buttons, add view modal
   - ✅ Products: Fix table buttons, add view modal
   - 🔄 Jobs: Add CRUD endpoints + modal form
   - 🔄 Vendors: Add CRUD endpoints + modal form

2. **NEXT - High priority:**
   - QC: Add CRUD endpoints + modal form
   - Deliveries: Add CRUD endpoints + modal form
   - LPOs: Add CRUD endpoints + modal form
   - Payments: Add CRUD endpoints + modal form

3. **LATER - Low priority:**
   - Processes: Assess if needs CRUD or is config only
   - Analytics: Confirm read-only, no changes needed
   - Alerts: Confirm read-only, no changes needed
   - Settings: Confirm config-only, no changes needed

## URL Routing Notes

All routes must be ordered: SPECIFIC ROUTES BEFORE GENERIC ROUTES

Example correct order:
```python
path('api/admin/jobs/create/', ...)      # Specific - FIRST
path('api/admin/jobs/<int:id>/get/', ...) # Specific - FIRST
path('api/admin/jobs/<int:id>/update/', ...) # Specific - FIRST
path('api/admin/jobs/<int:id>/delete/', ...) # Specific - FIRST
path('api/admin/jobs/', ...)             # Generic - AFTER specific
```

This prevents redirect loops from generic routes matching specific ones.

