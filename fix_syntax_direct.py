import os

file_path = r'c:\Users\ariet\OneDrive\Desktop\AM - EDU 2.0\schools\templates\schools\school_list.html'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content.replace('status=="active"', 'status == "active"')
    new_content = new_content.replace('status=="inactive"', 'status == "inactive"')

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Successfully fixed syntax in {file_path}")
    else:
        print("No matches found to replace. File might be already fixed or patterns don't match.")

except Exception as e:
    print(f"Error: {e}")
