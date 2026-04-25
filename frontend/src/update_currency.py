import os
import glob

directory = r'e:\VVCE\Websites\Symbiot 2026\PRixGEn\frontend\src\components'
for file_path in glob.glob(os.path.join(directory, '*.js')):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'en-US' in content or "'USD'" in content or '"USD"' in content:
        content = content.replace("'en-US'", "'en-IN'")
        content = content.replace('"en-US"', '"en-IN"')
        content = content.replace("'USD'", "'INR'")
        content = content.replace('"USD"', '"INR"')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated {file_path}')
