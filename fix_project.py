
import os

file_path = r'c:\Users\ariet\OneDrive\Desktop\AM - EDU 2.0\schools\templates\schools\school_list.html'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the specific faulty lines
    new_content = content.replace('{% if status=="active" %}', '{% if status == "active" %}')
    new_content = new_content.replace('{% if status=="inactive" %}', '{% if status == "inactive" %}')
    
    if content == new_content:
        print("No changes made. Pattern not found?")
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Successfully patched {file_path}")

except Exception as e:
    print(f"Error: {e}")
