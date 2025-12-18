#!/usr/bin/env python3

def extract_function(content, function_name):
    """Extract a function from content"""
    start_pattern = f"def {function_name}("
    start = content.find(start_pattern)
    if start == -1:
        return None
    
    # Find the end of the function (next def or end of file)
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
        i += 1
    
    return content[start:i].strip()

# Read the views.py file
with open('clientapp/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract both submit_qc functions
qc_function1 = extract_function(content, 'submit_qc')

# Remove the first function and find the second
content_without_first = content[qc_function1.find('def submit_qc(') + len(qc_function1):]
qc_function2 = extract_function(content_without_first, 'submit_qc')

if qc_function1:
    print("=== FIRST SUBMIT_QC FUNCTION (Line ~5744) ===")
    print(qc_function1)
    print("\n" + "="*70 + "\n")

if qc_function2:
    print("=== SECOND SUBMIT_QC FUNCTION (Line ~6153) ===")
    print(qc_function2)
else:
    print("Second function not found")