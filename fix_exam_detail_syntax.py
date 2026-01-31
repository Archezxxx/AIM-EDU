import os

file_path = r'c:\Users\ariet\OneDrive\Desktop\AM - EDU 2.0\zipgrade\templates\zipgrade\exam_detail.html'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replacements for specific syntax errors
    replacements = [
        ("show_unknown=='0'", "show_unknown == '0'"),
        ("show_unknown=='1'", "show_unknown == '1'"),
        ("sort=='-percentage'", "sort == '-percentage'"),
        ("sort=='percentage'", "sort == 'percentage'"),
        ("sort=='zipgrade_last_name'", "sort == 'zipgrade_last_name'"),
        ("sort=='zipgrade_student_id'", "sort == 'zipgrade_student_id'"),
    ]

    new_content = content
    for old, new in replacements:
        new_content = new_content.replace(old, new)

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Successfully fixed syntax errors in exam_detail.html")
    else:
        print("No changes needed or patterns not found.")

except Exception as e:
    print(f"Error: {e}")
