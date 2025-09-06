import os
import re

EXCLUDED_DIRS = {
    '.venv',
    '.idea',
    '.git',
    '__pycache__',
    'External Libraries',
    'Scratches and Consoles'
}

EXCLUDED_EXTENSIONS = ['jpeg', 'ttf', 'otf', 'png', 'jpg']

EXT_PATTERN = re.compile(rf'^.*\.({"|".join(EXCLUDED_EXTENSIONS)})$', re.IGNORECASE)

def should_ignore(file_name: str) -> bool:
    if file_name in EXCLUDED_DIRS:
        return True
    if EXT_PATTERN.match(file_name):
        return True
    return False

def print_tree(path='.', prefix='', output_file=None, is_last=True):
    try:
        entries = sorted(
            [e for e in os.listdir(path) if not should_ignore(e) and not os.path.islink(os.path.join(path, e))],
            key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower())
        )
    except PermissionError:
        return

    for index, entry in enumerate(entries):
        full_path = os.path.join(path, entry)
        is_last_entry = index == len(entries) - 1
        connector = '└── ' if is_last_entry else '├── '
        line = f"{prefix}{connector}{entry}\n"
        output_file.write(line)

        if os.path.isdir(full_path):
            extension = '    ' if is_last_entry else '│   '
            print_tree(full_path, prefix + extension, output_file, is_last_entry)

with open('project_tree.txt', 'w', encoding='utf-8') as f:
    print_tree('..', '', f)
