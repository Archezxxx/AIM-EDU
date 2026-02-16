"""Fix Django template syntax errors in exam_detail.html"""

path = r'c:\Users\ariet\OneDrive\Desktop\AM - EDU 2.0\zipgrade\templates\zipgrade\exam_detail.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the sort comparisons - add spaces around ==
content = content.replace("{% if sort=='-percentage' %}", "{% if sort == '-percentage' %}")
content = content.replace("{% if sort=='percentage' %}", "{% if sort == 'percentage' %}")
content = content.replace("{% if sort=='zipgrade_last_name' %}", "{% if sort == 'zipgrade_last_name' %}")
content = content.replace("{% if sort=='zipgrade_student_id' %}", "{% if sort == 'zipgrade_student_id' %}")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Template fixed successfully!')
