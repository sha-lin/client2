# Clients Admin Portal - Quick Testing Guide

## 🧪 How to Test the Clients CRUD Implementation

---

## Prerequisites
- Django development server running (`python manage.py runserver`)
- Admin user account (staff=True) logged in
- Access to admin dashboard at `/admin-dashboard/`

---

## 1. Testing CREATE (Add New Client)

### Test Case 1.1: Create B2B Client
**Steps:**
1. Navigate to Admin Dashboard → Business Tab → Clients Management
2. Click "Add New Client" button (blue button at top-right)
3. Modal opens with empty form
4. Fill in the form:
   - **Client Type:** Select "B2B" radio button
   - **Client Name:** "TechCorp Ltd"
   - **Company:** "Technology Solutions Inc"
   - **Email:** "sales@techcorp.com"
   - **Phone:** "+254700000001"
   - **VAT/Tax ID:** "P001234567A"
   - **KRA PIN:** "A001234567B"
   - **Industry:** "Technology"
   - **Business Address:** "123 Tech Street, Nairobi, Kenya"
   - **Payment Terms:** "Net 30" (should default to this for B2B)
   - **Credit Limit:** "50000"
   - **Default Markup:** "35"
   - **Risk Rating:** "Low"
   - **Is Reseller:** Check this box
   - **Delivery Address:** "456 Logistics Hub, Nairobi"
   - **Delivery Instructions:** "Gate code: 1234, Contact: John Doe"
   - **Preferred Channel:** "Email"
   - **Lead Source:** "Website"
   - **Account Manager:** Select an account manager from dropdown
   - **Status:** "Active"

5. Click "Save Client" button
6. **Expected Result:** 
   - Modal closes
   - Page refreshes
   - New client appears in the table
   - Success message shown (may be brief)

### Test Case 1.2: Create B2C Client
**Steps:**
1. Click "Add New Client" button again
2. Fill in with B2C data:
   - **Client Type:** Select "B2C" radio button
   - **Client Name:** "Jane Smith"
   - **Company:** (leave empty)
   - **Email:** "jane.smith@email.com"
   - **Phone:** "+254700000002"
   - Other fields as desired
3. Note: Payment Terms should default to "Prepaid" for B2C
4. Click "Save Client"
5. **Expected Result:** 
   - New B2C client created
   - Appears in list with B2C designation

### Test Case 1.3: Validation Testing
**Steps:**
1. Click "Add New Client"
2. Leave "Client Name" empty
3. Fill in Email and Phone
4. Click "Save Client"
5. **Expected Result:** Error message "Client name is required"

**Repeat for:**
- Missing Email → "Email is required"
- Missing Phone → "Phone number is required"

---

## 2. Testing READ (View/Edit Modal Population)

### Test Case 2.1: Open Existing Client for Editing
**Steps:**
1. In Clients list, locate the "TechCorp Ltd" client you created
2. Click the "Edit" button (pencil icon) for that client
3. Modal opens with title "Edit Client"
4. **Expected Result:**
   - All form fields are populated with existing values
   - Client Type shows "B2B" selected
   - All text fields show saved values
   - Account Manager dropdown shows selected value
   - Status shows "Active"
   - Reseller checkbox is checked (if you checked it)

### Test Case 2.2: Verify All Fields Populated
**Check these fields are populated correctly:**
- [ ] Client Name: "TechCorp Ltd"
- [ ] Company: "Technology Solutions Inc"
- [ ] Email: "sales@techcorp.com"
- [ ] Phone: "+254700000001"
- [ ] VAT/Tax ID: "P001234567A"
- [ ] KRA PIN: "A001234567B"
- [ ] Industry: "Technology"
- [ ] Address: "123 Tech Street, Nairobi, Kenya"
- [ ] Payment Terms: "Net 30"
- [ ] Credit Limit: "50000"
- [ ] Default Markup: "35"
- [ ] Risk Rating: "Low"
- [ ] Is Reseller: Checked
- [ ] Delivery Address: "456 Logistics Hub, Nairobi"
- [ ] Delivery Instructions: "Gate code: 1234, Contact: John Doe"
- [ ] Preferred Channel: "Email"
- [ ] Lead Source: "Website"
- [ ] Account Manager: Shows the assigned manager
- [ ] Status: "Active"

---

## 3. Testing UPDATE (Modify Existing Client)

### Test Case 3.1: Update Client Type
**Steps:**
1. Open "TechCorp Ltd" for editing (click Edit)
2. Change Client Type from "B2B" to "B2C"
3. Click "Save Client"
4. **Expected Result:**
   - Modal closes
   - Page refreshes
   - Client still shows in list
   - When you edit again, B2C is selected

### Test Case 3.2: Update Payment Terms
**Steps:**
1. Open "TechCorp Ltd" for editing
2. Change Payment Terms from "Net 30" to "Net 60"
3. Click "Save Client"
4. **Expected Result:**
   - Change is saved
   - Opening edit shows "Net 60" selected

### Test Case 3.3: Update Account Manager
**Steps:**
1. Open "TechCorp Ltd" for editing
2. Change Account Manager to a different person
3. Click "Save Client"
4. **Expected Result:**
   - Change is saved
   - Opening edit shows new account manager selected

### Test Case 3.4: Update Markup & Credit Limit
**Steps:**
1. Open "TechCorp Ltd" for editing
2. Change Default Markup to "40"
3. Change Credit Limit to "75000"
4. Click "Save Client"
5. **Expected Result:**
   - Changes saved
   - Next edit shows new values

### Test Case 3.5: Update Delivery Details
**Steps:**
1. Open "TechCorp Ltd" for editing
2. Change Delivery Address to "789 New Location, Mombasa"
3. Change Instructions to "New gate code: 9876"
4. Click "Save Client"
5. **Expected Result:**
   - Changes saved
   - Next edit shows new values

---

## 4. Testing DELETE (Remove Client)

### Test Case 4.1: Delete Client
**Steps:**
1. In Clients list, find any test client you want to delete
2. Click the delete button (trash icon) for that client
3. Browser shows confirmation: "Are you sure?" or similar
4. Click OK/Confirm
5. **Expected Result:**
   - Client removed from list
   - Page remains on Clients page
   - Client no longer appears in list

### Test Case 4.2: Verify Deleted Client Cannot Be Edited
**Steps:**
1. Try to directly access the deleted client's edit URL
2. **Expected Result:** 
   - Error message "Client not found" or 404 error

---

## 5. Testing SPECIAL SCENARIOS

### Test Case 5.1: Leave Optional Fields Empty
**Steps:**
1. Create new client
2. Fill ONLY required fields:
   - Client Type
   - Client Name
   - Email
   - Phone
3. Leave all other fields empty
4. Click "Save Client"
5. **Expected Result:**
   - Client created successfully
   - Optional fields are empty/have defaults

### Test Case 5.2: Test with Special Characters
**Steps:**
1. Create client with special characters in name:
   - "ABC & Co. Ltd"
2. Address with special characters:
   - "123 O'Neill St, Suite #456"
3. Fill other fields normally
4. Click "Save Client"
5. **Expected Result:**
   - Special characters saved correctly
   - Display correctly when editing

### Test Case 5.3: Test Long Text Input
**Steps:**
1. Edit a client
2. Put long text in Address field (500+ characters)
3. Put long text in Delivery Instructions
4. Save
5. **Expected Result:**
   - Long text saved and retrieved correctly
   - Text appears in edit form properly

### Test Case 5.4: Test Account Manager Assignment
**Steps:**
1. Create new client
2. Leave Account Manager empty
3. Save
4. Edit the client
5. Assign Account Manager
6. Save
7. **Expected Result:**
   - First save: Account Manager is empty
   - After update: Account Manager is assigned
   - Shows correctly in edit form

### Test Case 5.5: Test Different Status Values
**Steps:**
1. Create client with Status = "Active"
2. Edit and change to "Dormant"
3. Save
4. Edit again and change to "Inactive"
5. Save
6. **Expected Result:**
   - All status values save correctly
   - Editing shows the selected status

---

## 6. DATABASE VERIFICATION

### Check ActivityLog
**Steps:**
1. Access Django admin or database viewer
2. Check ActivityLog table for entries with:
   - activity_type: "Client Created", "Client Updated", "Client Deleted"
   - title: Should reference client name
   - created_by: Should show admin user who performed action
3. **Expected Result:**
   - Log entry for each create/update/delete operation
   - Timestamps are correct
   - User information is accurate

### Check Client Table
**Steps:**
1. Access database directly (e.g., via Django admin)
2. Navigate to Client table
3. Find clients you created
4. **Expected Result:**
   - All 20 fields populated correctly
   - No null values where data was entered
   - Relationships correct (account_manager_id)

---

## 7. ERROR SCENARIOS

### Test Case 7.1: Network Error Handling
**Steps:**
1. Open edit modal for a client
2. Close DevTools/Network tab (simulate offline)
3. Try to submit form
4. **Expected Result:**
   - Error message displayed
   - User can try again

### Test Case 7.2: Invalid Account Manager ID
**Steps:**
1. Edit client HTML in DevTools
2. Change account_manager value to invalid ID (e.g., 99999)
3. Submit form
4. **Expected Result:**
   - Error message or field validation
   - Client not saved

---

## 8. PERFORMANCE TESTING

### Test Case 8.1: Large List Performance
**Steps:**
1. Create 20+ clients using the form
2. Go to Clients Management page
3. Check load time (should be under 2 seconds)
4. Scroll through list
5. **Expected Result:**
   - Page loads smoothly
   - No lag when scrolling
   - All clients visible

### Test Case 8.2: Edit Modal Loading
**Steps:**
1. Click Edit on a client
2. **Expected Result:**
   - Modal opens within 1 second
   - Form populated within 1 second
   - No "loading" delays

---

## 9. BROWSER COMPATIBILITY

Test on:
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari
- [ ] Edge

**Expected Result:** Form works consistently across browsers

---

## 10. MOBILE/RESPONSIVE TESTING

**Steps:**
1. Test on mobile device or using DevTools device emulation
2. Click "Add New Client"
3. Scroll through form on mobile
4. Fill in data
5. Submit form

**Expected Result:**
- Form is readable on mobile
- Fields are touch-friendly
- Modal is properly sized
- No horizontal scrolling needed

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Form doesn't open | JavaScript error | Check browser console for errors |
| Fields don't populate on edit | API endpoint issue | Verify `/api/admin/clients/{id}/get/` returns data |
| Submit fails silently | CSRF token missing | Ensure form includes `{% csrf_token %}` |
| Client created but not visible | Page not refreshed | Check if `location.reload()` is called |
| Account manager dropdown empty | Query filter wrong | Verify users have 'Account Manager' group |
| Error "Staff access required" | User not staff | Verify user has `is_staff=True` |

---

## Success Criteria

✅ All test cases pass  
✅ No errors in browser console  
✅ No errors in Django console  
✅ All CRUD operations work  
✅ Data persists after refresh  
✅ Activity logs created for all operations  
✅ Form validation works as expected  
✅ Special characters handled correctly  
✅ Performance acceptable  
✅ Responsive on mobile devices  

---

**When all tests pass, Clients Management page CRUD is complete and ready for production.** 🎉

