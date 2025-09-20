#!/usr/bin/env python3
import re

# Read the file
with open('tradingview_scraper.py', 'r') as f:
    content = f.read()

print("Original syntax errors found:")
syntax_errors = re.findall(r'str\(e\)\)["\)\}]*', content)
for error in syntax_errors:
    print(f"- {error}")

# Fix all common patterns
content = re.sub(r'str\(e\)\}\)"\)', 'str(e)}")', content)
content = re.sub(r'str\(e\)\}\)\)', 'str(e)}")', content) 
content = re.sub(r'str\(e\)\)"\)', 'str(e)}")', content)
content = re.sub(r'extracted_events\}\)"\)', 'extracted_events})")', content)
content = re.sub(r'str\(e\)\)\)', 'str(e)}")', content)

# Write back the corrected content
with open('tradingview_scraper.py', 'w') as f:
    f.write(content)

print("Fixed f-string syntax errors")

# Try to compile to check
try:
    compile(content, 'tradingview_scraper.py', 'exec')
    print("✅ Syntax is now valid!")
except SyntaxError as e:
    print(f"❌ Still has syntax error: {e}")
    print(f"Line {e.lineno}: {e.text}")