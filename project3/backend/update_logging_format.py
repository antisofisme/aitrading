#!/usr/bin/env python3
"""
Update logging format across all active services
Changes: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
To: '%(asctime)s - %(name)s\n%(levelname)s - %(message)s'
"""

import os
import re
from pathlib import Path

# Old format pattern
OLD_FORMAT = r"'%(asctime)s - %(name)s - %(levelname)s - %(message)s'"
NEW_FORMAT = r"'%(asctime)s - %(name)s\\n%(levelname)s - %(message)s'"

# Files to update (active services only, skip _archived)
FILES_TO_UPDATE = [
    "00-data-ingestion/dukascopy-historical-downloader/src/main.py",
    "00-data-ingestion/external-data-collector/src/main.py",
    "00-data-ingestion/polygon-historical-downloader/src/main.py",
    "00-data-ingestion/polygon-live-collector/src/main.py",
    "02-data-processing/data-bridge/src/main.py",
    "02-data-processing/tick-aggregator/src/main.py",
]

def update_logging_format(file_path: Path):
    """Update logging format in a single file"""
    print(f"Processing: {file_path}")

    if not file_path.exists():
        print(f"  ❌ File not found: {file_path}")
        return False

    # Read file content
    content = file_path.read_text()

    # Check if old format exists
    if OLD_FORMAT not in content and "%(asctime)s - %(name)s - %(levelname)s - %(message)s" not in content:
        print(f"  ⏭️  No old format found, skipping")
        return False

    # Replace old format with new format
    new_content = content.replace(
        "'%(asctime)s - %(name)s - %(levelname)s - %(message)s'",
        "'%(asctime)s - %(name)s\\n%(levelname)s - %(message)s'"
    )

    # Also replace with double quotes
    new_content = new_content.replace(
        '"%(asctime)s - %(name)s - %(levelname)s - %(message)s"',
        '"%(asctime)s - %(name)s\\n%(levelname)s - %(message)s"'
    )

    # Write back
    if new_content != content:
        file_path.write_text(new_content)
        print(f"  ✅ Updated successfully")
        return True
    else:
        print(f"  ⏭️  No changes needed")
        return False

def main():
    """Main update function"""
    backend_path = Path(__file__).parent
    updated_count = 0

    print("🔄 Updating logging format across all services...\n")

    for relative_path in FILES_TO_UPDATE:
        full_path = backend_path / relative_path
        if update_logging_format(full_path):
            updated_count += 1

    print(f"\n✅ Update complete! {updated_count} files updated.")

if __name__ == "__main__":
    main()
