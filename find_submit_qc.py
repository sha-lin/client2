#!/usr/bin/env python3

with open('clientapp/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find all submit_qc function definitions
for i, line in enumerate(lines):
    if 'def submit_qc(' in line:
        print(f'submit_qc found at line {i+1}: {line.strip()}')