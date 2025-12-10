# Dashboard Real-Time Polling - Implementation & Testing Guide

## Overview
The admin dashboard uses **short polling** (not WebSockets) to provide real-time KPI updates every 30 seconds. This document explains the architecture and how to verify it's working.

---

## Architecture

### Client-Side (Browser)
**Location**: `clientapp/templates/admin/index.html` (lines 800-900)

```javascript
// Polling function - executes every 30 seconds
setInterval(function() {
    fetch('/api/admin/dashboard/data/')
        .then(response => response.json())
        .then(data => {
            updateKPICards(data.stats);
            updateCharts(data);
        })
        .catch(error => console.error('Polling error:', error));
}, 30000);  // 30000 milliseconds = 30 seconds
```

**What happens**:
1. Browser makes GET request to `/api/admin/dashboard/data/`
2. Server returns JSON with KPI stats + chart data
3. JavaScript updates DOM with new values
4. Chart.js updates chart visualizations
5. Repeats every 30 seconds

### Server-Side (Django)
**Location**: `clientapp/views.py` function `api_admin_dashboard_data()`

```python
@staff_member_required
def api_admin_dashboard_data(request):
    """Returns real-time dashboard data for polling"""
    # 1. Get KPI statistics
    stats = get_dashboard_stats()
    
    # 2. Calculate revenue trend (last 6 months)
    revenue_trend = calculate_revenue_trend()
    
    # 3. Get production by category
    production_by_category = get_production_by_category()
    
    # 4. Get weekly jobs overview
    weekly_jobs = get_weekly_jobs()
    
    # 5. Return JSON response
    return JsonResponse({
        'stats': stats,
        'revenue_trend': revenue_trend,
        'production_by_category': production_by_category,
        'weekly_jobs': weekly_jobs
    })
```

### URL Routing
**Location**: `clientapp/urls.py`

```python
path('api/admin/dashboard/data/', views.api_admin_dashboard_data, name='api_admin_dashboard_data'),
```

---

## Testing the Polling Endpoint

### Method 1: Browser Developer Tools

1. **Open Admin Dashboard**
   - Navigate to `http://localhost:8000/admin-dashboard/`
   
2. **Open Developer Console**
   - Press `F12` (or right-click → Inspect)
   - Go to "Network" tab
   
3. **Observe Polling Requests**
   - Look for requests to `dashboard/data` endpoint
   - Should see one every 30 seconds
   - Status should be `200 OK`
   
4. **Verify Response Data**
   - Click on `dashboard/data` request
   - Go to "Response" tab
   - Should see JSON like:
     ```json
     {
       "stats": {
         "clients": 42,
         "quotes": 156,
         "jobs": 89,
         "revenue": 45678.90,
         "pending": 12,
         "overdue": 3
       },
       "revenue_trend": [...],
       "production_by_category": [...],
       "weekly_jobs": [...]
     }
     ```
   
5. **Monitor Chart Updates**
   - Keep Network tab open
   - Watch KPI cards and charts update after each request
   - Refresh dashboard to reset polling timer

### Method 2: Command Line with curl

```bash
# Test polling endpoint once
curl -b "sessionid=YOUR_SESSION_ID" \
  http://localhost:8000/api/admin/dashboard/data/

# Pretty-print JSON response
curl -b "sessionid=YOUR_SESSION_ID" \
  http://localhost:8000/api/admin/dashboard/data/ | python -m json.tool

# Check response headers
curl -i http://localhost:8000/api/admin/dashboard/data/
```

**Expected response**:
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 1234

{
  "stats": { ... },
  "revenue_trend": [ ... ],
  ...
}
```

### Method 3: Python Script (Simulating Polling)

```python
import requests
import time
import json

# Login first to get session
session = requests.Session()
session.post('http://localhost:8000/admin-login/', {
    'username': 'admin_user',
    'password': 'password'
})

# Simulate polling (30-second intervals)
for i in range(5):  # 5 polls = 2.5 minutes
    response = session.get('http://localhost:8000/api/admin/dashboard/data/')
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nPoll #{i+1} - Timestamp: {time.strftime('%H:%M:%S')}")
        print(f"Clients: {data['stats']['clients']}")
        print(f"Revenue: ${data['stats']['revenue']}")
    else:
        print(f"Error: {response.status_code}")
    
    if i < 4:
        time.sleep(30)  # Wait 30 seconds before next poll
```

---

## Troubleshooting Polling Issues

### Problem 1: "Dashboard/data returns 404"

**Symptoms**:
- Network tab shows red error
- Response: `{"detail": "Not found."}`

**Solutions**:
```bash
# 1. Verify URL is correct
python manage.py shell
>>> from django.urls import reverse
>>> reverse('api_admin_dashboard_data')
'/api/admin/dashboard/data/'

# 2. Check URL is in urls.py
grep -n "api_admin_dashboard_data" clientapp/urls.py

# 3. Verify view function exists
grep -n "def api_admin_dashboard_data" clientapp/views.py
```

### Problem 2: "403 Forbidden on polling endpoint"

**Symptoms**:
- Network shows `403 Forbidden`
- Response: `{'success': false, 'message': 'Staff access required'}`

**Solutions**:
```python
# Ensure user is staff
python manage.py shell
>>> from django.contrib.auth.models import User
>>> user = User.objects.get(username='your_username')
>>> print(f"Is staff: {user.is_staff}")
>>> user.is_staff = True
>>> user.save()
>>> print("Updated - now user is staff")

# Verify session is active
>>> from django.contrib.sessions.models import Session
>>> sessions = Session.objects.all()
>>> for session in sessions:
>>>     print(session.session_key)
```

### Problem 3: "Polling requests aren't being made"

**Symptoms**:
- No requests to `/api/admin/dashboard/data/` in Network tab
- KPI cards never update

**Solutions**:

1. **Check JavaScript is running**:
   - Open console (F12)
   - Type: `setInterval(function() { console.log('polling'); }, 1000);`
   - Should see "polling" printed every second

2. **Verify JavaScript in template**:
   ```bash
   grep -A 5 "setInterval" clientapp/templates/admin/index.html
   ```
   Should show polling code

3. **Check for JavaScript errors**:
   - Console tab should be clear (no red errors)
   - Look for syntax errors in dashboard template

4. **Verify fetch API works**:
   ```javascript
   // Type in console:
   fetch('/api/admin/dashboard/data/')
       .then(r => r.json())
       .then(d => console.log(d))
   ```

### Problem 4: "KPI cards show 0 or N/A"

**Symptoms**:
- Polling requests return 200
- Response has data
- But dashboard still shows 0 or blank

**Solutions**:

1. **Check `updateKPICards()` function**:
   ```javascript
   // Type in console:
   console.log(document.querySelector('[data-kpi="clients"]'));
   // Should show the DOM element
   ```

2. **Verify data attributes**:
   ```bash
   grep -n "data-kpi=" clientapp/templates/admin/index.html
   ```
   Should show attributes like `data-kpi="clients"`, `data-kpi="revenue"`, etc.

3. **Manually trigger update** (from console):
   ```javascript
   // Fetch and update
   fetch('/api/admin/dashboard/data/')
       .then(r => r.json())
       .then(data => {
           console.log('Data received:', data);
           updateKPICards(data.stats);
       });
   ```

### Problem 5: "Charts aren't updating"

**Symptoms**:
- KPI cards update fine
- Charts show static data
- No chart animations

**Solutions**:

1. **Verify Chart.js is loaded**:
   ```javascript
   // Type in console:
   console.log(Chart);
   // Should show Chart.js library object
   ```

2. **Check chart objects exist**:
   ```javascript
   // Type in console:
   console.log(window.revenueChart);
   console.log(window.categoryChart);
   console.log(window.weeklyChart);
   // All should be Chart objects, not undefined
   ```

3. **Manually update a chart**:
   ```javascript
   // Type in console:
   if (window.revenueChart) {
       window.revenueChart.data.datasets[0].data = [100, 200, 150];
       window.revenueChart.update();
       console.log('Chart updated');
   }
   ```

---

## Monitoring & Diagnostics

### Server-Side Logging

Add logging to track polling:

```python
# In admin_api.py or views.py
import logging
logger = logging.getLogger(__name__)

@staff_required
def api_admin_dashboard_data(request):
    logger.info(f"Polling request from {request.user.username}")
    
    stats = get_dashboard_stats()
    revenue_trend = calculate_revenue_trend()
    
    logger.debug(f"Stats: {stats}")
    
    return JsonResponse({
        'stats': stats,
        'revenue_trend': revenue_trend,
        ...
    })
```

Check logs:
```bash
# View Django logs
tail -f logs/django.log | grep "Polling"
```

### Client-Side Debugging

Add console logging to polling function:

```javascript
setInterval(function() {
    const timestamp = new Date().toLocaleTimeString();
    console.log(`[${timestamp}] Polling for dashboard data...`);
    
    fetch('/api/admin/dashboard/data/')
        .then(response => {
            console.log(`Response status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log('Data received:', data);
            updateKPICards(data.stats);
            updateCharts(data);
            console.log('Dashboard updated');
        })
        .catch(error => {
            console.error('Polling error:', error);
        });
}, 30000);
```

### Performance Monitoring

Track polling performance:

```javascript
setInterval(function() {
    const startTime = performance.now();
    
    fetch('/api/admin/dashboard/data/')
        .then(response => response.json())
        .then(data => {
            const endTime = performance.now();
            const duration = (endTime - startTime).toFixed(2);
            console.log(`Polling took ${duration}ms`);
            
            if (duration > 5000) {
                console.warn('Polling is slow! Check server performance');
            }
        });
}, 30000);
```

---

## Optimization Tips

### 1. Reduce Polling Frequency
If your data doesn't change often:
```javascript
// Change from 30 seconds to 60 seconds
setInterval(function() { ... }, 60000);
```

### 2. Only Fetch Changed Data
Instead of fetching all data every time:
```python
# Return a smaller response with timestamp
@staff_required
def api_admin_dashboard_data(request):
    last_update = request.GET.get('since')
    
    if last_update:
        # Only return updated stats since timestamp
        stats = get_dashboard_stats_since(last_update)
    else:
        stats = get_dashboard_stats()
    
    return JsonResponse({
        'stats': stats,
        'timestamp': timezone.now().isoformat()
    })
```

### 3. Implement Conditional Updates
Only update UI if data actually changed:
```javascript
let lastStats = null;

fetch('/api/admin/dashboard/data/')
    .then(r => r.json())
    .then(data => {
        if (JSON.stringify(data.stats) !== JSON.stringify(lastStats)) {
            updateKPICards(data.stats);
            lastStats = data.stats;
        }
    });
```

### 4. Use WebSockets for Lower Latency
If polling doesn't meet your needs, upgrade to WebSockets:
- Library: `django-channels`
- Benefits: True real-time, lower bandwidth, instant updates
- Tradeoff: More complex setup

---

## Testing Checklist

- [ ] Admin dashboard loads without errors
- [ ] Network tab shows polling requests to `/api/admin/dashboard/data/`
- [ ] Polling requests occur every 30 seconds
- [ ] Response status is `200 OK`
- [ ] Response contains valid JSON
- [ ] KPI card values match API response
- [ ] Charts visualize data correctly
- [ ] Charts update every 30 seconds
- [ ] No JavaScript errors in console
- [ ] Console log shows successful polls (if logging enabled)
- [ ] Works for multiple staff users simultaneously
- [ ] Stops polling when user leaves dashboard
- [ ] Polling resumes when returning to dashboard

---

## Production Deployment Notes

1. **HTTPS Required**: All polling requests should use HTTPS
2. **CORS**: If API is on different domain, configure CORS headers
3. **Rate Limiting**: Consider adding throttling (e.g., max 10 requests/minute per user)
4. **Caching**: For frequently-fetched data, consider caching with Redis
5. **Monitoring**: Set up alerts if polling fails for >2 minutes
6. **Load Testing**: Test with multiple concurrent users polling simultaneously

---

## Further Reading

- Django docs: https://docs.djangoproject.com/en/3.2/ref/request-response/
- Chart.js docs: https://www.chartjs.org/
- Fetch API: https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API
- WebSockets alternative: https://channels.readthedocs.io/
