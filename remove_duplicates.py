#!/usr/bin/env python3

with open('clientapp/views.py', 'r', encoding='utf-8') as f:
    content = f.readlines()

# Find the second submit_qc function (around line 6152)
start_line = 6151  # @login_required
end_line = 6245    # next function starts here

# Remove the duplicate submit_qc function (lines 6152-6244)
new_content = []
skip_until_line = None

for i, line in enumerate(content):
    line_num = i + 1
    
    # Skip lines from the duplicate function
    if line_num >= start_line and line_num < end_line:
        continue
    else:
        new_content.append(line)

# Write the cleaned content back
with open('clientapp/views.py', 'w', encoding='utf-8') as f:
    f.writelines(new_content)

print(f"Removed duplicate submit_qc function (lines {start_line}-{end_line-1})")