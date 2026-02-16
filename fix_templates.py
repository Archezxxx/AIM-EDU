import re
import os

def fix_template(filepath):
    """Fix Django template syntax - add spaces around == in {% if %} conditions"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Fix patterns like: variable=='value' -> variable == 'value'
    # And: variable=="value" -> variable == "value"
    content = re.sub(r"(\w+)==(')", r"\1 == \2", content)
    content = re.sub(r'(\w+)==(")', r'\1 == \2', content)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {filepath}")
        return True
    else:
        print(f"No changes needed: {filepath}")
        return False

# Fix exam_detail.html
fix_template(r'zipgrade/templates/zipgrade/exam_detail.html')

# Verify
print("\nVerifying fix:")
with open(r'zipgrade/templates/zipgrade/exam_detail.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i in range(100, 120):
        if i < len(lines) and '==' in lines[i]:
            print(f"{i+1}: {lines[i].rstrip()[:80]}")
