import os

file_path = r"C:\Users\ariet\OneDrive\Desktop\AM - EDU 2.0\analytics\templates\analytics\students.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace typical problem patterns
new_content = content.replace("selected_school.pk==s.pk", "selected_school.pk == s.pk")
new_content = new_content.replace("grade_filter==g", "grade_filter == g")
new_content = new_content.replace("section_filter==s", "section_filter == s")
new_content = new_content.replace('{% trans "Clear" %}', '{% trans "Clear" %}') # Should already be fixed but good to ensure

# Force write
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Successfully patched {file_path}")
print("Line 50 check:")
lines = new_content.splitlines()
print(lines[49]) # 0-indexed, so 49 is line 50
