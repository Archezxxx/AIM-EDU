
import os
import re

file_path = r'C:\Users\ariet\OneDrive\Desktop\AM - EDU 2.0\analytics\templates\analytics\students.html'

def fix_students_template():
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define replacements for missing spaces around ==
    replacements = [
        (r'{% if selected_school.pk==s.pk %}', r'{% if selected_school.pk == s.pk %}'),
        (r'{% if grade_filter==g %}', r'{% if grade_filter == g %}'),
        (r'{% if section_filter==s %}', r'{% if section_filter == s %}'),
    ]

    new_content = content
    for pattern, replacement in replacements:
        if pattern in new_content:
            print(f"Replacing '{pattern}' with '{replacement}'")
            new_content = new_content.replace(pattern, replacement)
        else:
             # Try regex if exact string match fails due to variations
             regex_pattern = pattern.replace('==', r'\s*==\s*') 
             # Escape braces for regex
             regex_pattern =  re.escape(pattern.replace('==', 'TEMP')).replace('TEMP', r'\s*==\s*')
             # Actually, simpler manual regex construction:
             if 'selected_school.pk==s.pk' in pattern:
                 p = r'{%\s*if\s+selected_school\.pk\s*==\s*s\.pk\s*%}'
                 r = r'{% if selected_school.pk == s.pk %}'
                 new_content = re.sub(p, r, new_content)

             if 'grade_filter==g' in pattern:
                 p = r'{%\s*if\s+grade_filter\s*==\s*g\s*%}'
                 r = r'{% if grade_filter == g %}'
                 new_content = re.sub(p, r, new_content)

             if 'section_filter==s' in pattern:
                 p = r'{%\s*if\s+section_filter\s*==\s*s\s*%}'
                 r = r'{% if section_filter == s %}'
                 new_content = re.sub(p, r, new_content)

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Successfully updated students.html with correct spacing.")
    else:
        print("No changes needed or patterns not found.")

if __name__ == "__main__":
    fix_students_template()
