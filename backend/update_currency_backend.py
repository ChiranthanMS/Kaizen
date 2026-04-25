import os
import glob

directory = r'e:\VVCE\Websites\Symbiot 2026\PRixGEn\backend'
for root, dirs, files in os.walk(directory):
    if 'venv' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            if "'USD'" in content or '"USD"' in content:
                content = content.replace("'USD'", "'INR'")
                content = content.replace('"USD"', '"INR"')
                
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f'Updated {file_path}')
