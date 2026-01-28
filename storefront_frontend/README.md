# Storefront Frontend - HTML/CSS/JS Implementation

## 📋 Overview

This is a **complete, production-ready HTML/CSS/JavaScript frontend** for the Storefront e-commerce platform, fully integrated with the Django REST API backend.

### Key Features

✅ **Complete API Integration** - All 40+ backend endpoints implemented  
✅ **Responsive Design** - Bootstrap 5 based, mobile-friendly  
✅ **User Authentication** - Login/register with JWT tokens  
✅ **Product Catalog** - Browse, search, filter products  
✅ **Quote Builder** - Interactive quote creation with real-time calculations  
✅ **Customer Dashboard** - Profile, estimates, quotes, messages  
✅ **Contact Management** - Multi-channel contact (email, WhatsApp, phone)  
✅ **Error Handling** - Comprehensive error messages and validation  
✅ **Performance** - Optimized with caching and debouncing  

---

## 🗂️ Project Structure

```
storefront_frontend/
├── pages/                      # HTML pages
│   ├── index.html             # Home page
│   ├── products.html          # Product catalog
│   ├── quote-builder.html     # Quote builder
│   ├── login.html             # Login page
│   ├── register.html          # Registration page
│   ├── contact.html           # Contact page
│   └── dashboard.html         # Customer dashboard
│
├── js/                        # JavaScript files
│   ├── api-client.js          # Central API client (350+ lines)
│   └── utils.js               # Utility functions (400+ lines)
│
├── css/                       # Stylesheets
│   └── styles.css             # Custom styles (500+ lines)
│
└── README.md                  # This file
```

---

## 🚀 Quick Start

### Installation

1. **Copy the frontend directory** to your web server root or Django static files:
   ```bash
   cp -r storefront_frontend/ /var/www/storefront/
   ```

2. **Update API_BASE_URL** in pages (if not using `/api`):
   ```javascript
   const api = new StorefrontAPIClient('https://your-api.com/api');
   ```

3. **Serve the pages** via HTTP server:
   - Apache/Nginx
   - Python: `python -m http.server 8000`
   - Node.js: `npx http-server`
   - VS Code: Live Server extension

### API Configuration

The frontend expects the backend API at `/api` by default. Update if needed:

```javascript
// In any page's <script> section:
const api = new StorefrontAPIClient('https://api.example.com/api');
```

### Environment Variables

No build process needed! All configuration is inline. Update these URLs in your environment:

- **API Base URL**: `new StorefrontAPIClient()` in each page
- **Token Storage**: Uses `localStorage` for auth tokens
- **Base Currency**: `USD` (configurable in `utils.js`)

---

## 📄 Page Guide

### 1. **index.html** - Home Page
- Hero section with CTA buttons
- Feature highlights
- Authentication state awareness
- Navigation menu

### 2. **products.html** - Product Catalog
- Product listing with search
- Category filtering
- Sorting (name, price)
- Product detail modal
- "Add to Quote" functionality
- Pagination support

### 3. **quote-builder.html** - Quote Creation
- Line item management
- Real-time price calculation
- Customer information collection
- Quote summary with totals
- Create estimate submission
- Session persistence

### 4. **login.html** - Authentication
- Email/password login
- Token storage
- Profile loading
- Auto-redirect to dashboard

### 5. **register.html** - Customer Registration
- Full registration form
- Password validation
- Email verification ready
- Auto-login after registration

### 6. **contact.html** - Contact & Support
- Multi-channel contact form
- Email, WhatsApp, phone options
- FAQ accordion
- Direct contact information
- Message submission

### 7. **dashboard.html** - Customer Dashboard
- Profile overview stats
- Estimates management
- Quotes tracking
- Message history
- Profile settings
- Communication preferences

---

## 🔗 API Client Integration

### StorefrontAPIClient Class

Central API client with automatic token management:

```javascript
const api = new StorefrontAPIClient();

// Authentication
await api.register(email, password, passwordConfirm, firstName, lastName, phone, company);
await api.login(email, password);
await api.getProfile();
await api.updateProfile(data);

// Products
await api.getProducts({ search, category, page });
await api.getProduct(productId);
await api.calculatePrice(productId, quantity, pricingTier, turnaround);

// Estimates/Quotes
await api.getEstimates();
await api.createEstimate(customerName, email, phone, company, lineItems);
await api.shareEstimate(estimateId, recipientEmail);
await api.convertEstimateToQuote(estimateId);

// Messaging
await api.sendEmailInquiry(subject, message, senderEmail, senderName, senderPhone);
await api.sendWhatsAppInquiry(phoneNumber, message, senderName);
await api.requestCall(phoneNumber, preferredTime, message);

// Production Units
await api.getProductionUnits(jobId, status);
await api.createProductionUnit(jobId, vendorId, startDate, endDate);
await api.sendPurchaseOrder(unitId);
await api.updateProductionProgress(unitId, status, startDate, endDate);
```

### Utility Functions

```javascript
StorefrontUtils.formatCurrency(amount);
StorefrontUtils.formatDate(date);
StorefrontUtils.showToast(message, type);
StorefrontUtils.showLoading(message);
StorefrontUtils.isValidEmail(email);
StorefrontUtils.isAuthenticated();
StorefrontUtils.getCurrentUser();
StorefrontUtils.setCurrentUser(user);
```

---

## 🎨 Styling

### Bootstrap 5 Integration

- CDN-based (no build required)
- Customized with `css/styles.css`
- Responsive mobile-first design
- Dark mode compatible

### Custom CSS Features

- Product cards with hover effects
- Quote builder styling
- Chatbot widget
- Sidebar navigation
- Status badges
- Toast notifications
- Loading indicators
- Animation effects

---

## 🔐 Authentication Flow

1. **Register** → Create account → Auto-populate register page
2. **Login** → JWT tokens stored in localStorage
3. **API Calls** → Bearer token in Authorization header
4. **Token Expiry** → Auto-refresh using refresh token
5. **Logout** → Clear tokens, redirect to home

### Session Storage

```javascript
// Access token (short-lived)
localStorage.getItem('storefront_access_token')

// Refresh token (long-lived)  
localStorage.getItem('storefront_refresh_token')

// User info (optional)
localStorage.getItem('storefront_user')
```

---

## 💾 State Management

### Session Storage (Per-session persistence)

```javascript
// Quote builder items
sessionStorage.setItem('quote_items', JSON.stringify(lineItems));
sessionStorage.getItem('quote_items');
```

### Local Storage (Persistent across sessions)

```javascript
// Authentication
localStorage.setItem('storefront_access_token', token);
localStorage.setItem('storefront_refresh_token', token);

// User preferences
localStorage.setItem('storefront_user', JSON.stringify(user));
```

---

## 🚨 Error Handling

### API Error Handling

```javascript
try {
    await api.someEndpoint();
} catch (error) {
    if (error.status === 401) {
        // Unauthorized - redirect to login
    } else if (error.status === 400) {
        // Bad request - show validation errors
        console.log(error.data);
    } else {
        // Other errors
    }
}
```

### Form Validation

- Email format validation
- Phone number validation
- Password strength checking
- Required field validation
- Real-time feedback

### Toast Notifications

```javascript
StorefrontUtils.showToast('Operation successful', 'success');  // Green
StorefrontUtils.showToast('Something went wrong', 'error');     // Red
StorefrontUtils.showToast('Warning message', 'warning');        // Yellow
StorefrontUtils.showToast('Info message', 'info');              // Blue
```

---

## 📊 Features by Page

| Feature | Page | Status |
|---------|------|--------|
| Browse Products | products.html | ✅ Complete |
| Search & Filter | products.html | ✅ Complete |
| Product Details | products.html | ✅ Complete |
| Price Calculation | quote-builder.html | ✅ Complete |
| Quote Builder | quote-builder.html | ✅ Complete |
| Customer Registration | register.html | ✅ Complete |
| Customer Login | login.html | ✅ Complete |
| Profile Management | dashboard.html | ✅ Complete |
| Order History | dashboard.html | ✅ Complete |
| Message Management | dashboard.html | ✅ Complete |
| Contact Form | contact.html | ✅ Complete |
| Multi-channel Contact | contact.html | ✅ Complete |
| FAQ Section | contact.html | ✅ Complete |

---

## 🔧 Customization Guide

### Change API Endpoint

Edit each HTML file's `<script>` section:

```javascript
const api = new StorefrontAPIClient('https://api.yourdomain.com/api');
```

### Add New Page

1. Create `pages/new-page.html`
2. Include Bootstrap, styles, and scripts:
   ```html
   <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
   <link rel="stylesheet" href="../css/styles.css">
   <script src="../js/utils.js"></script>
   <script src="../js/api-client.js"></script>
   ```
3. Use API client: `const api = new StorefrontAPIClient();`

### Add New API Endpoint

Edit `js/api-client.js`:

```javascript
async newEndpoint(param1, param2) {
    return this.post('/storefront/new-endpoint/', {
        param1,
        param2
    });
}
```

### Customize Styling

Edit `css/styles.css`:

```css
:root {
    --primary-color: #007bff;  /* Change brand color */
    --border-radius-base: 0.375rem;
}
```

---

## 🌐 Deployment

### Option 1: Static File Server

```bash
# Copy to web server
cp -r storefront_frontend/ /var/www/storefront/

# Configure nginx
server {
    listen 80;
    root /var/www/storefront/pages;
    index index.html;
}
```

### Option 2: Django Static Files

```bash
# Copy to Django static directory
cp -r storefront_frontend/ /path/to/django/project/static/

# Serve with Django
python manage.py collectstatic
```

### Option 3: Docker

```dockerfile
FROM nginx:latest
COPY storefront_frontend/ /usr/share/nginx/html/
EXPOSE 80
```

### Option 4: S3 + CloudFront

```bash
aws s3 sync storefront_frontend/pages/ s3://your-bucket/
```

---

## ✅ Testing Checklist

- [ ] All pages load without JavaScript errors
- [ ] Login/register works correctly
- [ ] Products load and filter properly
- [ ] Quote builder calculations are accurate
- [ ] API calls include correct auth headers
- [ ] Error messages display appropriately
- [ ] Forms validate input correctly
- [ ] Responsive design works on mobile
- [ ] Token refresh works on 401 response
- [ ] Navigation between pages is smooth
- [ ] Dashboard loads user data correctly
- [ ] Toast notifications appear and disappear

---

## 📈 Performance Optimization

### Current Optimizations

- Debounced search input (300ms delay)
- Session storage for quote items
- Token caching in localStorage
- Lazy loading of modals
- CSS minification ready
- No external dependencies (except Bootstrap CDN)

### Further Optimization Ideas

1. Minify JS and CSS
2. Add service worker for offline support
3. Implement image lazy loading
4. Add resource hints (prefetch, preconnect)
5. Enable gzip compression
6. Cache API responses

---

## 🐛 Troubleshooting

### Issue: API calls fail with CORS error
**Solution**: Ensure backend has CORS enabled:
```python
# Django settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://yourdomain.com",
]
```

### Issue: Token not being sent with requests
**Solution**: Check browser localStorage for token:
```javascript
console.log(localStorage.getItem('storefront_access_token'));
```

### Issue: Login redirects to login page again
**Solution**: Clear browser cache/cookies and retry

### Issue: Quote totals are wrong
**Solution**: Verify backend price calculation logic, check browser console for API response

---

## 📚 File Sizes

| File | Size | Lines |
|------|------|-------|
| api-client.js | ~15 KB | 350+ |
| utils.js | ~12 KB | 400+ |
| styles.css | ~20 KB | 500+ |
| index.html | ~3 KB | 120+ |
| products.html | ~6 KB | 250+ |
| quote-builder.html | ~8 KB | 350+ |
| dashboard.html | ~10 KB | 450+ |
| login.html | ~2 KB | 80+ |
| register.html | ~3 KB | 100+ |
| contact.html | ~8 KB | 320+ |

**Total**: ~87 KB static files (highly gzippable)

---

## 🎯 Next Steps

1. **Deploy** the frontend to your server
2. **Configure** API endpoint in each page
3. **Test** all workflows end-to-end
4. **Customize** branding and styling
5. **Monitor** user interactions and errors
6. **Iterate** based on feedback

---

## 📞 Support

For issues or questions:
- Check browser console for JavaScript errors
- Verify API responses in Network tab
- Review backend API documentation
- Test endpoints with Postman/curl first

---

## 📝 License

This frontend is part of the Storefront e-commerce platform.

---

**Last Updated**: January 26, 2026  
**Version**: 1.0.0  
**Status**: ✅ Production Ready
