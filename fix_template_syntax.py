import os
import re

def fix_django_template_syntax(root_dir):
    """
    Scans for HTML files in the given directory and fixes Django template syntax errors,
    specifically improperly spaced comparison operators within {% ... %} tags.
    """
    html_files_count = 0
    fixed_files_count = 0
    errors_fixed_count = 0

    # Operators to fix: ==, !=, <=, >=, >, <
    # We prioritize multi-char operators first to avoid double replacement
    # Regex logic: 
    # Look for the operator surrounded by non-spaces, or one side non-space, inside {% %}
    
    operators = ['==', '!=', '<=', '>=']
    single_operators = ['<', '>'] # Handle separately if needed, but < and > can be part of HTML tags, so strictly only inside {% %}

    print(f"Scanning directory: {root_dir}...")

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip virtualenvs and git
        if 'venv' in dirpath or '.git' in dirpath or '__pycache__' in dirpath or 'node_modules' in dirpath:
            continue

        for filename in filenames:
            if filename.endswith('.html'):
                html_files_count += 1
                filepath = os.path.join(dirpath, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                     try:
                        with open(filepath, 'r', encoding='cp1251') as f:
                            content = f.read()
                     except:
                        print(f"Skipping file due to encoding issue: {filepath}")
                        continue
                
                original_content = content
                
                def fix_tag_content(match):
                    tag_full = match.group(0) # {% ... %}
                    tag_inner = match.group(1) # content inside
                    
                    # Fix multi-char operators: ==, !=, <=, >=
                    # Pattern: anything not a space, followed by op, followed by anything
                    # But we want to ensure spaces.
                    
                    # Fix '=='
                    # Replace "val1==val2" with "val1 == val2"
                    # We use negative lookbehind/ahead to ensure we don't mess up existing spaces too much or other Ops
                    
                    new_inner = tag_inner
                    
                    # List of ops to ensure spacing around
                    ops = ['==', '!=', '>=', '<=']
                    for op in ops:
                        # Escape op for regex
                        e_op = re.escape(op)
                        # Regex: 
                        # 1. No space before: (\S)(==) -> \1 ==
                        # 2. No space after: (==)(\S) -> == \2
                        
                        # Pass 1: Add space before if missing
                        # Negative lookbehind for space
                        new_inner = re.sub(f'(?<=\S){e_op}', f' {op}', new_inner)
                        
                        # Pass 2: Add space after if missing
                        # Negative lookahead for space/end of string
                        # Note: after Pass 1, op might have a space before it now.
                        # We match the op literal again.
                        new_inner = re.sub(f'{e_op}(?=\S)', f'{op} ', new_inner)

                    # For single char ops > and <, it's trickier because they might be part of filters or other syntax?
                    # Generally in {% if %} tags they are explicitly comparisons.
                    # Let's check for < and > only if strictly inside "if" block?
                    # For safety, let's stick to the requested "== type" errors which are usually equality/inequality.
                    # The user specifically mentioned errors like "show_unknown=='0'".
                    
                    if new_inner != tag_inner:
                        return f"{{%{new_inner}%}}"
                    return tag_full

                # Regex to find Django block tags {% ... %}
                # We use lazy matching explicitly
                new_content = re.sub(r'\{%(.+?)%\}', fix_tag_content, content, flags=re.DOTALL)
                
                if new_content != original_content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Fixed: {filepath}")
                    fixed_files_count += 1
                    errors_fixed_count += 1 # Rough counting
    
    print("-" * 30)
    print(f"Scan complete.")
    print(f"HTML files scanned: {html_files_count}")
    print(f"Files fixed: {fixed_files_count}")

if __name__ == "__main__":
    current_dir = os.getcwd()
    fix_django_template_syntax(current_dir)
