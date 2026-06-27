import os
import struct
import sys

def parse_po(po_path: str) -> dict:
    """
    Parses a .po file into a dictionary of {msgid: msgstr}.
    Handles multi-line strings and unescapes standard sequences.
    """
    translations = {}
    with open(po_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_id = None
    current_str = None
    in_id = False
    in_str = False

    def unescape(s: str) -> str:
        # Resolve common escaped characters
        return s.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        if line.startswith('msgid'):
            # Save previous translation if completed
            if current_id is not None and current_str is not None:
                translations[unescape(current_id)] = unescape(current_str)
            current_id = None
            current_str = None

            in_id = True
            in_str = False
            parts = line.split('msgid', 1)
            content = parts[1].strip()
            if content.startswith('"') and content.endswith('"'):
                current_id = content[1:-1]
            else:
                current_id = ""

        elif line.startswith('msgstr'):
            in_id = False
            in_str = True
            parts = line.split('msgstr', 1)
            content = parts[1].strip()
            if content.startswith('"') and content.endswith('"'):
                current_str = content[1:-1]
            else:
                current_str = ""

        elif line.startswith('"') and line.endswith('"'):
            content = line[1:-1]
            if in_id:
                current_id += content
            elif in_str:
                current_str += content

    # Save final translation block
    if current_id is not None and current_str is not None:
        translations[unescape(current_id)] = unescape(current_str)

    return translations

def write_mo(mo_path: str, translations: dict):
    """
    Compiles a dictionary of translations and writes it in standard GNU gettext binary .mo format.
    """
    keys = sorted(translations.keys())
    num_strings = len(keys)

    # Offset calculations:
    # Header size: 28 bytes
    # Key descriptor table size: num_strings * 8 bytes (each is: string_length, string_offset)
    # Translation descriptor table size: num_strings * 8 bytes
    # Total metadata offsets: 28 + (N * 8) + (N * 8)
    keys_table_offset = 28
    trans_table_offset = keys_table_offset + (num_strings * 8)
    raw_data_offset = trans_table_offset + (num_strings * 8)

    keys_table = []
    trans_table = []
    raw_data = bytearray()

    current_offset = raw_data_offset

    # Populate raw data for keys
    for key in keys:
        key_bytes = key.encode('utf-8')
        key_len = len(key_bytes)
        keys_table.append((key_len, current_offset))
        raw_data.extend(key_bytes + b'\x00')
        current_offset += key_len + 1

    # Populate raw data for translations
    for key in keys:
        val_bytes = translations[key].encode('utf-8')
        val_len = len(val_bytes)
        trans_table.append((val_len, current_offset))
        raw_data.extend(val_bytes + b'\x00')
        current_offset += val_len + 1

    # Write binary file
    with open(mo_path, 'wb') as f:
        # Magic number: 0x950412de (little endian), version: 0, count: N, offset tables, hashes (0)
        f.write(struct.pack('<Iiiiiii', 0x950412de, 0, num_strings, keys_table_offset, trans_table_offset, 0, 0))
        
        # Write descriptor table for keys
        for length, offset in keys_table:
            f.write(struct.pack('<ii', length, offset))
            
        # Write descriptor table for translations
        for length, offset in trans_table:
            f.write(struct.pack('<ii', length, offset))
            
        # Write packed raw strings
        f.write(raw_data)

def compile_all():
    """Finds all vidos.po files in the locales folder and compiles them to vidos.mo."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.normpath(os.path.join(current_dir, '..'))
    locales_dir = os.path.join(root_dir, 'locales')

    if not os.path.exists(locales_dir):
        print(f"Locales directory not found: {locales_dir}")
        return

    compiled_count = 0
    for root, dirs, files in os.walk(locales_dir):
        for file in files:
            if file.endswith('.po'):
                po_path = os.path.join(root, file)
                mo_path = po_path[:-3] + '.mo'
                
                print(f"Parsing: {os.path.relpath(po_path, root_dir)}")
                try:
                    translations = parse_po(po_path)
                    if not translations:
                        print(f"  Warning: No translation strings found in {file}")
                        continue
                    
                    write_mo(mo_path, translations)
                    print(f"  Compiled successfully -> {os.path.relpath(mo_path, root_dir)} ({len(translations)} strings)")
                    compiled_count += 1
                except Exception as e:
                    print(f"  Error compiling {file}: {e}", file=sys.stderr)

    print(f"\nCompilation complete. Compiled {compiled_count} translation catalog(s).")

if __name__ == '__main__':
    compile_all()
