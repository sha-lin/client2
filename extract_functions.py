#!/usr/bin/env python3

def extract_function(content, function_name):
    """Extract a function from content"""
    start_pattern = f"def {function_name}("
    start = content.find(start_pattern)
    if start == -1:
        return None
    
    # Find the end of the function (next def or end of file)
    indent_level = None
    i = start
    while i < len(content):
        if content[i] == '\n':
            # Look at the next non-empty line to determine function boundary
            j = i + 1
            while j < len(content) and content[j] in ' \t\n':
                j += 1
            
            if j < len(content) and content[j] not in '\n':
                # Check if this line starts a new function at the same or higher level
                if content[j:j+4] == 'def ':
                    # Found next function, this is our end
                    break
                elif content[j:j+1] == '@':
                    # Decorator, continue
                    pass
                else:
                    # Regular line, continue
                    pass
        i += 1
    
    return content[start:i].strip()

# Read the views.py file
with open('clientapp/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract both functions
qc_function = extract_function(content, 'qc_inspection')
delivery_function = extract_function(content, 'delivery_handoff')

if qc_function:
    print("=== QC_INSPECTION FUNCTION ===")
    print(qc_function)
    print("\n" + "="*50 + "\n")

if delivery_function:
    print("=== DELIVERY_HANDOFF FUNCTION ===")
    print(delivery_function)
else:
    print("delivery_handoff function not found")