# Admin Portal - Quick Start & Testing Guide

## 🚀 QUICK START (5 minutes)

### 1. Restart Django Server
```bash
# If running, press Ctrl+C to stop
python manage.py runserver
```

### 2. Access Admin Dashboard
```
http://localhost:8000/admin-dashboard/
```

### 3. Navigate Tabs
Click on any tab under:
- **BUSINESS** → Clients, Leads, Quotes, Products
- **OPERATIONS** → Jobs, Vendors, Processes, QC, Deliveries
- **FINANCIAL** → LPOs, Payments, Analytics
- **SYSTEM** → Users

---

## ✅ TESTING CHECKLIST

### Test Clients Tab
- [ ] Navigate to `/admin-dashboard/clients/`
- [ ] See table of existing clients
- [ ] Search by name using search box
- [ ] Filter by status (Active/Inactive)
- [ ] Click "+ New" button
- [ ] Modal appears with form
- [ ] Fill in name and email
- [ ] Click "Save"
- [ ] New client appears in list
- [ ] Click "Edit" on any client
- [ ] Modal shows current data
- [ ] Update a field
- [ ] Save changes
- [ ] Verify update in list
- [ ] Click "Delete" on a client
- [ ] Confirm deletion
- [ ] Client removed from list

### Test Leads Tab
- [ ] Navigate to `/admin-dashboard/leads/`
- [ ] See table of leads
- [ ] Test search functionality
- [ ] Test source filter
- [ ] Test CRUD operations (Create, Read, Update, Delete)

### Test Quotes Tab
- [ ] Navigate to `/admin-dashboard/quotes/`
- [ ] See table of quotes with amounts
- [ ] Test search for quote ID
- [ ] Test status filter
- [ ] Test CRUD operations

### Test Products Tab
- [ ] Navigate to `/admin-dashboard/products/`
- [ ] See product list with prices
- [ ] Search by product name
- [ ] Test CRUD operations

### Test Other Tabs
- [ ] Jobs - test job_status filter
- [ ] Vendors - test active/inactive status
- [ ] Processes - test search
- [ ] Quality Control - test status filter
- [ ] Deliveries - test status filter
- [ ] LPOs - test status filter
- [ ] Payments - test payment_status filter
- [ ] Users - test is_active filter
- [ ] Analytics - view KPI metrics

---

## 🐛 TROUBLESHOOTING

### Issue: "No such table" error
**Solution:**
```bash
python manage.py migrate
python manage.py runserver
```

### Issue: 403 Forbidden
**Cause:** Not logged in as staff/admin
**Solution:**
1. Log in to Django admin first: `http://localhost:8000/admin/`
2. Use superuser account
3. Then access admin dashboard

### Issue: Sidebar not showing correctly
**Solution:**
1. Clear browser cache (Ctrl+Shift+Del)
2. Hard refresh (Ctrl+F5)
3. Try in incognito mode

### Issue: Modal doesn't open
**Cause:** JavaScript error
**Solution:**
1. Press F12 to open DevTools
2. Check Console for errors
3. Look for red error messages
4. Report the error

### Issue: Form doesn't save
**Cause:** CSRF token missing
**Solution:**
1. Make sure logged in as staff user
2. Check browser cookies
3. Try different browser

### Issue: Search not working
**Solution:**
1. Click "Search" button (not just Enter)
2. Try simpler search terms
3. Check spelling

### Issue: Pagination not working
**Solution:**
1. Make sure you have more than 25 items
2. Click pagination links carefully
3. URL should update with `?page=2`

---

## 🔍 BROWSER CONSOLE DEBUGGING

Press F12 to open DevTools:

### Check Network Tab
1. Click "Network" tab
2. Perform action (Create/Edit/Delete)
3. Look for POST request to `/api/admin/...`
4. Click request to see details
5. Check Status (should be 200 or 201)
6. Check Response (should have `"success": true`)

### Check Console Tab
1. Click "Console" tab
2. Should show no red errors
3. Look for alert or console.log messages
4. If red errors, click to see details

### Example: Create fails
1. Network shows POST 400 or 500
2. Response shows error message
3. Check what fields were sent
4. Verify form data is correct

---

## 📊 DATA REQUIREMENTS

### Clients Need (Minimum)
- name (required)
- email (required)
- phone (optional)
- status (optional, defaults to 'active')

### Leads Need
- name (required)
- email (required)
- status (optional)
- source (optional)

### Quotes Need
- quote_id (auto-generated)
- product_name (required)
- client (optional)
- quantity (required)
- unit_price (required)
- status (optional)

---

## 🎯 COMMON WORKFLOWS

### Create a New Client
1. Go to `/admin-dashboard/clients/`
2. Click "+ New"
3. Fill: Name, Email, Phone
4. Click "Save"
5. Page refreshes, client appears at top

### Search for Client
1. Go to `/admin-dashboard/clients/`
2. Type client name in search box
3. Click "Search"
4. Table updates to show matches

### Update Client Status
1. Go to `/admin-dashboard/clients/`
2. Click "Edit" on the client
3. Change status dropdown
4. Click "Save"
5. Status updates in list

### Delete Old Record
1. Go to relevant tab
2. Click "Delete" button
3. Confirm "Are you sure?"
4. Record removed

---

## 🔐 SECURITY NOTES

### Only Staff Can Access
- All views require `@staff_member_required`
- Logged in users can see `/admin-dashboard/`
- Regular users redirected to login

### CSRF Protection
- All POST requests validate CSRF token
- Browser automatically sends token
- Same-origin policy enforced

### Data Validation
- All models validate on save
- Foreign keys checked
- Required fields enforced

---

## 📈 PERFORMANCE NOTES

### Pagination
- 25 items per page (configurable)
- Speeds up page load
- Reduces database queries

### Search
- Searches all relevant fields
- Case-insensitive
- Partial matches supported

### Filters
- Drop-down filters reduce data
- Faster than searching
- Can combine search + filter

---

## 🆘 WHEN TO CONTACT SUPPORT

Include these details:
1. **URL**: What page were you on?
2. **Action**: What did you click?
3. **Error**: Screenshot of error or console error
4. **Expected**: What should happen?
5. **Actual**: What actually happened?

Example:
```
URL: /admin-dashboard/clients/
Action: Clicked "+ New" button
Error: Modal didn't open
Expected: Modal with form appears
Actual: Nothing happened
Browser Console: 404 error for /api/admin/...
```

---

## ✨ FEATURE IDEAS FOR FUTURE

- [ ] Bulk actions (select multiple, delete all)
- [ ] Export to CSV
- [ ] Import from CSV
- [ ] Print lists
- [ ] Dark mode toggle
- [ ] Column visibility toggle
- [ ] Custom date range filters
- [ ] Advanced search
- [ ] Activity audit log
- [ ] Email notifications
- [ ] Webhooks
- [ ] API documentation
- [ ] Mobile app
- [ ] Real-time updates
- [ ] Dashboard widgets

---

## 📞 QUICK HELP LINKS

- Django Admin Docs: https://docs.djangoproject.com/en/stable/ref/contrib/admin/
- Bootstrap Pagination: https://getbootstrap.com/docs/5.0/components/pagination/
- CSRF Tokens: https://docs.djangoproject.com/en/stable/middleware/csrf/

---

## ✅ VERIFICATION CHECKLIST

Before considering complete:

- [ ] All tabs accessible from navigation
- [ ] Each tab shows data in table
- [ ] Search works on at least one tab
- [ ] Filter works on at least one tab
- [ ] Can create new record
- [ ] Can edit existing record
- [ ] Can delete record with confirmation
- [ ] Pagination works (if >25 items)
- [ ] No JavaScript console errors
- [ ] Responsive on different screen sizes
- [ ] Works in Chrome, Firefox, Safari
- [ ] Staff-only access enforced

---

## 🎉 YOU'RE ALL SET!

Your admin portal is ready for production use. 

**Start here:** `http://localhost:8000/admin-dashboard/`

Enjoy your new Django admin-style interface with your custom UI!
