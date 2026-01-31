import os
import struct
import sys

def generate_mo(pofile, mofile):
    try:
        with open(pofile, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"File not found: {pofile}")
        return

    mess = {}
    current_msgid = None
    current_msgstr = None
    state = None # 'msgid', 'msgstr'

    def unescape(s):
        # Handle basic escapes found in PO files
        s = s.replace('\\n', '\n')
        s = s.replace('\\"', '"')
        s = s.replace('\\t', '\t')
        s = s.replace('\\\\', '\\')
        return s

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            continue
        
        if line.startswith('msgid '):
            # Save previous
            if current_msgid is not None and current_msgstr is not None:
                mess[current_msgid] = current_msgstr
            
            clean_line = line[6:].strip()
            if clean_line.startswith('"') and clean_line.endswith('"'):
                current_msgid = unescape(clean_line[1:-1])
            else:
                current_msgid = "" # Fallback
            current_msgstr = None
            state = 'msgid'
        elif line.startswith('msgstr '):
            clean_line = line[7:].strip()
            if clean_line.startswith('"') and clean_line.endswith('"'):
                current_msgstr = unescape(clean_line[1:-1])
            else:
                current_msgstr = ""
            state = 'msgstr'
        elif line.startswith('"') and line.endswith('"'):
            content = unescape(line[1:-1])
            if state == 'msgid':
                current_msgid += content
            elif state == 'msgstr':
                current_msgstr += content

    # Save last
    if current_msgid is not None and current_msgstr is not None:
        mess[current_msgid] = current_msgstr

    # Create MO file
    # Magic number: 0x950412de
    # Version: 0
    
    # We need to sort keys
    keys = sorted(mess.keys())
    
    # Original strings table
    otable = b''
    ttable = b''
    strings_content = b''
    
    # We will put all strings after the tables
    # Header (28) + OTable (N*8) + TTable (N*8)
    num_strings = len(keys)
    string_offset_base = 28 + (num_strings * 8) * 2
    
    current_offset = string_offset_base
    
    # Pass 1: Original strings
    for k in keys:
        k_enc = k.encode('utf-8') + b'\0'
        length = len(k_enc) - 1
        otable += struct.pack('II', length, current_offset)
        strings_content += k_enc
        current_offset += len(k_enc)
        
    # Pass 2: Translated strings
    for k in keys:
        v_enc = mess[k].encode('utf-8') + b'\0'
        length = len(v_enc) - 1
        ttable += struct.pack('II', length, current_offset)
        strings_content += v_enc
        current_offset += len(v_enc)
    
    header = struct.pack('I', 0x950412de) # magic
    header += struct.pack('I', 0) # revision
    header += struct.pack('I', num_strings)
    header += struct.pack('I', 28) # offset of original strings table
    header += struct.pack('I', 28 + num_strings * 8) # offset of trans strings table
    header += struct.pack('I', 0) # size of hash table
    header += struct.pack('I', 0) # offset of hash table
        
    try:
        with open(mofile, 'wb') as f:
            f.write(header)
            f.write(otable)
            f.write(ttable)
            f.write(strings_content)
        print(f"Compiled {pofile} to {mofile} ({num_strings} messages)")
    except Exception as e:
        print(f"Error writing mofile: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python compile_mo.py <pofile> <mofile>")
    else:
        generate_mo(sys.argv[1], sys.argv[2])
