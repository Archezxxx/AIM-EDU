import os

file_path = r'c:\Users\ariet\OneDrive\Desktop\AM - EDU 2.0\schools\templates\schools\school_list.html'

print(f"Reading file: {file_path}")
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if the error exists
    if 'status=="active"' in content:
        print("Found incorrect syntax 'status==\"active\"'. Fixing...")
        content = content.replace('status=="active"', 'status == "active"')
    
    if 'status=="inactive"' in content:
        print("Found incorrect syntax 'status==\"inactive\"'. Fixing...")
        content = content.replace('status=="inactive"', 'status == "inactive"')
        
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("File updated successfully.")
    
except Exception as e:
    print(f"Error detected: {e}")
