"""
Test package for Import Manager
"""

# Test configuration
pytest_plugins = ['pytest_asyncio']

# Test utilities
import tempfile
from pathlib import Path

def create_temp_test_file(content, filename="test_file.json", directory=None):
    """Create temporary test file with content"""
    if directory is None:
        directory = tempfile.gettempdir()
    
    file_path = Path(directory) / filename
    with open(file_path, 'w') as f:
        if isinstance(content, dict):
            import json
            json.dump(content, f)
        else:
            f.write(content)
    
    return str(file_path)