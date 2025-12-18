#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'client.settings')
django.setup()

from django.contrib.auth.models import User

try:
    user = User.objects.get(username='prod_user')
    print(f'User found: {user.username}')
    print(f'Email: {user.email}')
    print(f'Is active: {user.is_active}')
    print(f'Is staff: {user.is_staff}')
    print(f'Groups: {[g.name for g in user.groups.all()]}')
    print(f'Password set: {user.has_usable_password()}')
except User.DoesNotExist:
    print('prod_user not found')
except Exception as e:
    print(f'Error: {e}')