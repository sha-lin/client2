#!/usr/bin/env python3

with open('clientapp/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print('=== FIRST PRODUCTION_SETTINGS FUNCTION (around line 3484) ===')
for i in range(3480, 3500):
    if i < len(lines):
        print(f'{i+1}: {lines[i].strip()}')

print('\n=== SECOND PRODUCTION_SETTINGS FUNCTION (around line 7600) ===')
for i in range(7595, 7620):
    if i < len(lines):
        print(f'{i+1}: {lines[i].strip()}')