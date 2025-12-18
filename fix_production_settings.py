#!/usr/bin/env python3

with open('clientapp/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the first incomplete production_settings function
first_function_start = content.find('@login_required\n@group_required(\'Production Team\')\ndef production_settings(request):')
first_function_end = content.find('\n\n@login_required\n@group_required(\'Production Team\')\ndef self_quote(request):')

if first_function_start != -1 and first_function_end != -1:
    # Remove the first incomplete function
    content = content[:first_function_start] + content[first_function_end:]
    print(f"Removed first production_settings function")

# Find and replace the second incomplete production_settings function
second_function_start = content.find('@login_required\ndef production_settings(request):')
second_function_end = content.find('\n\n@login_required\ndef production_analytics(request):')

if second_function_start != -1 and second_function_end != -1:
    # Remove the second incomplete function
    content = content[:second_function_start] + content[second_function_end:]
    print(f"Removed second production_settings function")

# Add the new complete function
new_function = '''@login_required
@group_required('Production Team')
def production_settings(request):
    """View for Production Team Settings - Enhanced with proper form handling"""
    from django.contrib.auth.models import User
    
    # Handle form submission
    if request.method == 'POST':
        try:
            user = request.user
            
            # Update profile information
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            
            # Update phone number
            if hasattr(user, 'profile'):
                user.profile.phone = request.POST.get('phone', '')
                
                # Update notification preferences
                user.profile.notify_new_jobs = request.POST.get('notify_new_jobs') == 'on'
                user.profile.notify_deadlines = request.POST.get('notify_deadlines') == 'on'
                user.profile.notify_qc = request.POST.get('notify_qc') == 'on'
                user.profile.notify_deliveries = request.POST.get('notify_deliveries') == 'on'
                user.profile.notify_system = request.POST.get('notify_system') == 'on'
                
                # Update workflow preferences
                user.profile.default_view = request.POST.get('default_view', 'kanban')
                user.profile.items_per_page = int(request.POST.get('items_per_page', '25'))
                user.profile.date_format = request.POST.get('date_format', 'dd/mm/yyyy')
                user.profile.time_format = request.POST.get('time_format', '12')
                
                user.profile.save()
            
            # Handle password change
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            
            if new_password:
                if user.check_password(current_password):
                    if new_password == confirm_password:
                        user.set_password(new_password)
                    else:
                        messages.error(request, 'New passwords do not match.')
                        return redirect('production_settings')
                else:
                    messages.error(request, 'Current password is incorrect.')
                    return redirect('production_settings')
            
            user.save()
            messages.success(request, 'Settings updated successfully!')
            return redirect('production_settings')
            
        except Exception as e:
            messages.error(request, f'Error updating settings: {str(e)}')
            return redirect('production_settings')
    
    # Prepare context for GET request
    context = {
        'current_view': 'production_settings',
        'user': request.user,
    }
    return render(request, 'production_settings.html', context)


'''

# Insert the new function after the imports and before other functions
imports_end = content.find('\ndef notifications(request):')
if imports_end != -1:
    content = content[:imports_end] + new_function + content[imports_end:]
    print("Added new complete production_settings function")
else:
    print("Could not find insertion point for new function")

# Write the updated content back
with open('clientapp/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Production settings function has been fixed!")