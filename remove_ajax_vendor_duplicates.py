#!/usr/bin/env python3

with open('clientapp/views.py', 'r', encoding='utf-8') as f:
    content = f.readlines()

# Find the second ajax_create_vendor function (around line 6702)
start_line = 6702  # @require_POST
end_line = 6810    # next function starts here (ajax_process_variables)

# Remove the duplicate ajax_create_vendor function (lines 6702-6809)
new_content = []

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

print(f"Removed duplicate ajax_create_vendor function (lines {start_line}-{end_line-1})")