#!/usr/bin/env python3

with open('clientapp/templates/delivery.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Lines 580-600:")
for i in range(579, 600):
    if i < len(lines):
        print(f'{i+1}: {repr(lines[i])}')