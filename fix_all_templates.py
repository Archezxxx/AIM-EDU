import os
import re

# Directory to search (current directory)
BASE_DIR = os.getcwd()

def fix_template_syntax(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Regex to find '==' without spaces around it, likely inside {% if ... %}
        # This is a simple heuristic: looks for non-space char, then ==, then non-space char
        # correctly handles {{ ... }} variables too if they use == (though rare in print tags)
        # We focus on capturing the pattern and enforcing spaces.
        
        # Pattern: (anything not space)==(anything not space)
        # We want to replace it with \1 == \2
        # Use a lookbehind and lookahead to check for missing spaces
        
        # Simple replacement strategies for known patterns seen in logs
        # 1. foo==bar -> foo == bar
        # 2. foo=='bar' -> foo == 'bar'
        
        # Improve regex: Find `==` that is NOT surrounded by spaces
        # We replace `==` with ` == ` and then collapse multiple spaces just in case, 
        # but a safer way is specific patterns.
        
        # Regex explanation:
        # (?<=\S)==(?=\S) matches == preceded and followed by non-whitespace
        # (?<=\s)==(?=\S) matches == preceded by space, followed by non-whitespace
        # (?<=\S)==(?=\s) matches == preceded by non-whitespace, followed by space
        
        new_content = content
        
        # Fix: "foo==bar" -> "foo == bar"
        new_content = re.sub(r'(?<=\S)==(?=\S)', ' == ', new_content)
        
        # Fix: "foo ==bar" -> "foo == bar"
        new_content = re.sub(r'(?<=\s)==(?=\S)', ' == ', new_content)

        # Fix: "foo== bar" -> "foo == bar"
        new_content = re.sub(r'(?<=\S)==(?=\s)', ' == ', new_content)

        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed syntax in: {file_path}")
            return True
        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

count = 0
print(f"Scanning for templates in {BASE_DIR}...")
for root, dirs, files in os.walk(BASE_DIR):
    # Skip venv and .git
    if 'venv' in root or '.git' in root or '__pycache__' in root:
        continue
        
    for file in files:
        if file.endswith('.html'):
            full_path = os.path.join(root, file)
            if fix_template_syntax(full_path):
                count += 1

print(f"Finished. Fixed {count} files.")
