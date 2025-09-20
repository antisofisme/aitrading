#!/usr/bin/env python3
import re

def fix_all_fstring_errors(filepath):
    """Fix all f-string syntax errors in the file"""
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # List of all line numbers with syntax errors and their fixes
    fixes = [
        # Pattern: logger.debug(f"... - error: {str(e)")
        (r'logger\.debug\(f"([^"]*){str\(e\)"\)', r'logger.debug(f"\1{str(e)}")'),
        
        # Pattern: logger.debug(f"... - error: {str(e)")) (extra parenthesis)
        (r'logger\.debug\(f"([^"]*){str\(e\)"\)\)', r'logger.debug(f"\1{str(e)}")'),
        
        # Pattern: logger.debug(f"... - {len(extracted_events})") (missing quote)
        (r'logger\.debug\(f"([^"]*){len\(extracted_events\)\"\)', r'logger.debug(f"\1{len(extracted_events)}")'),
        
        # Pattern: Any remaining incomplete f-strings
        (r'str\(e\)"\)', r'str(e)}")'),
        (r'str\(e\)\"\)\)', r'str(e)}")'),
    ]
    
    print("Original content preview:")
    lines = content.split('\n')
    for i, line in enumerate(lines[375:380], 376):
        print(f"{i}: {line}")
    
    # Apply all fixes
    for pattern, replacement in fixes:
        old_content = content
        content = re.sub(pattern, replacement, content)
        if content != old_content:
            print(f"Applied fix: {pattern} -> {replacement}")
    
    # Manual fixes for specific patterns
    manual_fixes = [
        ('str(e)\")', 'str(e)})'),
        ('{str(e)})', '{str(e)})'),
    ]
    
    for old, new in manual_fixes:
        if old in content:
            content = content.replace(old, new)
            print(f"Applied manual fix: {old} -> {new}")
    
    # Write back
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Fixed f-string errors in {filepath}")
    
    # Test compilation
    try:
        compile(content, filepath, 'exec')
        print("✅ Syntax is now valid!")
        return True
    except SyntaxError as e:
        print(f"❌ Still has syntax error: {e}")
        print(f"Line {e.lineno}: {e.text}")
        return False

if __name__ == "__main__":
    fix_all_fstring_errors("tradingview_scraper.py")