import io
with io.open('dashboard/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Mojibake characters caused by Windows codepages
content = content.replace('â€¢', '•')
content = content.replace('âž”', '➔')
content = content.replace('âœ…', '✅')
content = content.replace('âš ï¸', '⚠️')
content = content.replace('âš ', '⚠️')

with io.open('dashboard/app.py', 'w', encoding='utf-8') as f:
    f.write(content)