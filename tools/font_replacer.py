import os

# Replacements mapping for updating theme fonts
REPLACEMENTS = {
    '"Geist-Bold"': '"Unbounded-Bold"',
    '"Geist-Medium"': '"Montserrat-Medium"',
    '"Geist"': '"Montserrat-Regular"'
}

def process_dir(target_path: str):
    """Walks through target directory and replaces fonts in python files."""
    for root, dirs, files in os.walk(target_path):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = content
                for old, new in REPLACEMENTS.items():
                    new_content = new_content.replace(old, new)
                    
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f'Updated {filepath}')

if __name__ == '__main__':
    # Resolve absolute path to the UI directory relative to this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ui_dir = os.path.normpath(os.path.join(current_dir, '../ui'))
    
    print(f"Scanning directory: {ui_dir}")
    process_dir(ui_dir)
    print("Font replacement scan completed.")
