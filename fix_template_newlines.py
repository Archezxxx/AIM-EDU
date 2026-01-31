import re
import os

file_path = r'C:\Users\ariet\OneDrive\Desktop\AM - EDU 2.0\analytics\templates\analytics\schools.html'

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Original length: {len(content)}")

# Fix 1: The explicit split at the beginning
# {% trans "All Schools" %}{%
# endif %}
pattern1 = re.compile(r'({% trans "All Schools" %}{%)\s*\n\s*(endif %})')
content = pattern1.sub(r'{% trans "All Schools" %}{% endif %}', content)

# Fix 2: The split inside the second title
# {% trans "All
# Schools" %}
pattern2 = re.compile(r'{% trans "All\s*\n\s*Schools" %}')
content = pattern2.sub(r'{% trans "All Schools" %}', content)

# Fix 3: Split tags ending with {%
# e.g. ...{% endif %}">{%
# trans "Exams" %}
# We look for {% at end of line (ignoring whitespace), and next line completing it.
def fix_split_tag_match(match):
    return match.group(1).rstrip() + ' ' + match.group(2).lstrip()

# Match {% followed by whitespace/newline, then tag content, then %}
# Use a specific regex for the patterns we saw
# Capture: (...{%) \n (   tag content %})
pattern_generic = re.compile(r'(.*{%)\s*\n\s*(.*%}.*)')
# This is a bit risky if it matches too much, but let's iterate line by line for safety

lines = content.split('\n')
fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    stripped = line.rstrip()
    
    # Check for split {% at end
    if stripped.endswith('{%'):
        if i + 1 < len(lines):
            next_line = lines[i+1].strip()
            # If next line completes the tag (heuristically)
            if next_line.endswith('%}') or next_line.endswith('%}</a>') or next_line.endswith('%}</option>'):
                 print(f"Fixing match at line {i+1}: {stripped} + {next_line}")
                 fixed_lines.append(stripped + ' ' + next_line)
                 i += 2
                 continue

    # Check for split inside trans tag: {% trans "All
    if 'trans "All' in line and not line.endswith('All Schools" %}'):
         if i + 1 < len(lines) and 'Schools" %}' in lines[i+1]:
             print(f"Fixing trans split at line {i+1}")
             fixed_lines.append(line.rstrip() + ' ' + lines[i+1].lstrip())
             i += 2
             continue
             
    fixed_lines.append(line)
    i += 1

new_content = '\n'.join(fixed_lines)

print(f"New length: {len(new_content)}")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Finished fixing templates.")
