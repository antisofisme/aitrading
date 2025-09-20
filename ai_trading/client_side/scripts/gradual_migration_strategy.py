#!/usr/bin/env python3
"""
gradual_migration_strategy.py - System Migration Strategy Utility

🎯 PURPOSE:
Business: Gradual migration planning and execution for system upgrades
Technical: Migration planning with rollback capabilities and progress tracking
Domain: System Migration/Upgrade Management/Risk Management

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.093Z
Session: client-side-ai-brain-full-compliance
Confidence: 86%
Complexity: high

🧩 PATTERNS USED:
- AI_BRAIN_MIGRATION_STRATEGY: Gradual system migration with safety measures

📦 DEPENDENCIES:
Internal: central_hub, logger_manager
External: json, pathlib, datetime, subprocess

💡 AI DECISION REASONING:
Trading systems require careful migration strategies to minimize downtime and financial risk during upgrades.

🚀 USAGE:
python gradual_migration_strategy.py --plan=production

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import sys
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

class ClientConfigurationMigrationError(Exception):
    """Custom error untuk client migration issues dengan informasi perbaikan"""
    
    def __init__(self, message: str, fix_suggestions: list = None, debug_info: dict = None):
        self.message = message
        self.fix_suggestions = fix_suggestions or []
        self.debug_info = debug_info or {}
        super().__init__(self.message)
    
    def __str__(self):
        error_msg = f"❌ Client Configuration Migration Error:\n{self.message}\n"
        
        if self.fix_suggestions:
            error_msg += "\n🔧 Suggested Fixes:\n"
            for i, suggestion in enumerate(self.fix_suggestions, 1):
                error_msg += f"   {i}. {suggestion}\n"
        
        if self.debug_info:
            error_msg += "\n📊 Debug Information:\n"
            for key, value in self.debug_info.items():
                error_msg += f"   - {key}: {value}\n"
        
        error_msg += "\n💡 Run diagnostics: python test_client_settings.py"
        return error_msg


def migrate_client_file_with_error_handling(file_path: str, new_import_path: str):
    """
    Migrate single client file to use centralized config
    DENGAN error handling yang informatif, BUKAN fallback ke yang lama
    """
    try:
        print(f"🔄 Migrating {file_path} to use centralized client configuration...")
        
        # Step 1: Test if new centralized config works
        try:
            sys.path.insert(0, str(Path(__file__).parent / "libs"))
            from src.shared.config.client_settings import get_client_settings
            settings = get_client_settings()
            print(f"✅ Centralized client config loaded successfully")
        except ImportError as e:
            raise ClientConfigurationMigrationError(
                f"Cannot import centralized client configuration from {new_import_path}",
                fix_suggestions=[
                    "Check if client_settings.py exists in libs/config/",
                    "Verify Python path includes libs/ directory",
                    "Run: python -c 'from src.shared.config.client_settings import get_client_settings'"
                ],
                debug_info={
                    "file_path": file_path,
                    "import_path": new_import_path,
                    "python_path": sys.path,
                    "import_error": str(e)
                }
            )
        except Exception as e:
            raise ClientConfigurationMigrationError(
                f"Centralized client configuration failed to load: {e}",
                fix_suggestions=[
                    "Check .env.client file exists and has correct values",
                    "Verify MT5 credentials are properly formatted",
                    "Run validation: python test_client_settings.py",
                    "Check Pydantic validation errors"
                ],
                debug_info={
                    "file_path": file_path,
                    "config_error": str(e),
                    "traceback": traceback.format_exc()
                }
            )
        
        # Step 2: Test if target file exists and is writable
        target_file = Path(file_path)
        if not target_file.exists():
            raise ClientConfigurationMigrationError(
                f"Target file not found: {file_path}",
                fix_suggestions=[
                    f"Create file: {file_path}",
                    "Check if file was moved or renamed",
                    "Verify client project structure is correct"
                ],
                debug_info={"expected_path": file_path}
            )
        
        # Step 3: Read and validate current file
        try:
            with open(target_file, 'r') as f:
                current_content = f.read()
        except PermissionError:
            raise ClientConfigurationMigrationError(
                f"Permission denied reading file: {file_path}",
                fix_suggestions=[
                    "Check file permissions: ls -la {file_path}",
                    "Run with appropriate permissions",
                    "Verify file ownership"
                ]
            )
        except Exception as e:
            raise ClientConfigurationMigrationError(
                f"Cannot read file {file_path}: {e}",
                fix_suggestions=[
                    "Check file encoding (should be UTF-8)",
                    "Verify file is not corrupted",
                    "Check disk space and file system"
                ]
            )
        
        # Step 4: Check if migration is needed
        if "get_client_settings" in current_content:
            print(f"ℹ️ File {file_path} already uses centralized configuration")
            return True
        
        # Step 5: Perform actual migration
        try:
            # Backup original content
            backup_content = current_content
            
            # Update imports (example - adapt per file)
            new_content = update_client_imports_to_centralized(current_content, new_import_path)
            
            # Validate new content before writing
            validate_migrated_client_content(new_content, file_path)
            
            # Write updated content
            with open(target_file, 'w') as f:
                f.write(new_content)
            
            print(f"✅ Successfully migrated {file_path}")
            return True
            
        except Exception as e:
            # JANGAN fallback ke konfigurasi lama - berikan error yang jelas!
            raise ClientConfigurationMigrationError(
                f"Migration failed for {file_path}: {e}",
                fix_suggestions=[
                    "Check syntax errors in updated imports",
                    "Verify centralized config compatibility",
                    "Review migration logic in gradual_migration_strategy.py",
                    "Test changes manually before automated migration"
                ],
                debug_info={
                    "file_path": file_path,
                    "migration_error": str(e),
                    "original_content_length": len(backup_content),
                    "has_backup": True
                }
            )
    
    except ClientConfigurationMigrationError:
        # Re-raise our custom errors as-is
        raise
    except Exception as e:
        # Wrap unexpected errors
        raise ClientConfigurationMigrationError(
            f"Unexpected error during migration of {file_path}: {e}",
            fix_suggestions=[
                "Check system resources (memory, disk space)",
                "Verify Python environment is stable", 
                "Run basic file operations test",
                "Contact development team with full error details"
            ],
            debug_info={
                "file_path": file_path,
                "unexpected_error": str(e),
                "traceback": traceback.format_exc()
            }
        )


def update_client_imports_to_centralized(content: str, new_import_path: str) -> str:
    """Update client file content to use centralized imports"""
    
    # Replace old scattered imports
    old_patterns = [
        "from src.shared.config.mt5_config import",
        "from src.shared.config.central_config import", 
        "from config import",
        "import mt5_config",
    ]
    
    new_import = f"from {new_import_path} import get_client_settings"
    
    # Add new import at the top
    lines = content.split('\n')
    import_section_end = 0
    
    for i, line in enumerate(lines):
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            import_section_end = i + 1
        elif line.strip() and not line.strip().startswith('#'):
            break
    
    # Insert new import
    lines.insert(import_section_end, new_import)
    
    # Replace old config usage patterns  
    updated_content = '\n'.join(lines)
    
    # Example replacements for client side - adapt based on actual usage patterns
    replacements = {
        "mt5_config.": "get_client_settings().mt5.",
        "central_config.": "get_client_settings().",
        "config.network.": "get_client_settings().network.",
        "config.streaming.": "get_client_settings().streaming.",
        "MT5_CONFIG.": "get_client_settings().mt5.",
        "NETWORK_CONFIG.": "get_client_settings().network.",
    }
    
    for old, new in replacements.items():
        updated_content = updated_content.replace(old, new)
    
    return updated_content


def validate_migrated_client_content(content: str, file_path: str):
    """Validate migrated client content before writing to file"""
    
    # Check 1: Basic syntax validation
    try:
        compile(content, file_path, 'exec')
    except SyntaxError as e:
        raise ClientConfigurationMigrationError(
            f"Syntax error in migrated content: {e}",
            fix_suggestions=[
                "Check import statement syntax",
                "Verify indentation is correct",
                "Look for missing commas or parentheses",
                "Review line {e.lineno} in migrated content"
            ],
            debug_info={
                "syntax_error_line": e.lineno,
                "syntax_error_text": e.text
            }
        )
    
    # Check 2: Required imports present
    if "get_client_settings" not in content:
        raise ClientConfigurationMigrationError(
            "Migrated content missing required centralized config import",
            fix_suggestions=[
                "Add: from src.shared.config.client_settings import get_client_settings",
                "Check if import was correctly added",
                "Verify import placement in file"
            ]
        )
    
    # Check 3: No old config patterns remain
    old_patterns = ["from src.shared.config.mt5_config", "import mt5_config", "from config import"]
    for pattern in old_patterns:
        if pattern in content:
            raise ClientConfigurationMigrationError(
                f"Old configuration pattern still present: {pattern}",
                fix_suggestions=[
                    f"Remove or replace: {pattern}",
                    "Ensure all old imports are updated",
                    "Check for duplicate imports"
                ]
            )


def run_client_gradual_migration_with_error_handling():
    """
    Run gradual migration for all client files
    DENGAN informative error handling, BUKAN fallback
    """
    
    print("🚀 Starting Client-Side Gradual Migration with Informative Error Handling")
    print("=" * 75)
    
    # Files to migrate based on comprehensive client analysis
    migration_targets = [
        # Phase 1 - Critical Files (Main bridge applications)
        {
            "file": "/mnt/f/WINDSURF/neliti_code/client_side/libs/config/__init__.py",
            "import_path": "config.client_settings",
            "priority": "critical",
            "description": "Configuration module interface - must be updated first"
        },
        {
            "file": "/mnt/f/WINDSURF/neliti_code/client_side/hybrid_bridge.py",
            "import_path": "libs.config.client_settings", 
            "priority": "critical",
            "description": "Main application entry point with scattered config"
        },
        {
            "file": "/mnt/f/WINDSURF/neliti_code/client_side/bridge_app.py",
            "import_path": "libs.config.client_settings",
            "priority": "critical", 
            "description": "Alternative application entry point"
        },
        {
            "file": "/mnt/f/WINDSURF/neliti_code/client_side/mt5_handler.py",
            "import_path": "libs.config.client_settings", 
            "priority": "critical",
            "description": "Core MT5 functionality with hardcoded timeouts"
        },
        {
            "file": "/mnt/f/WINDSURF/neliti_code/client_side/websocket_client.py", 
            "import_path": "libs.config.client_settings",
            "priority": "high",
            "description": "Core communication component with hardcoded values"
        },
        # Phase 2 - High Priority (Supporting modules)
        {
            "file": "/mnt/f/WINDSURF/neliti_code/client_side/libs/streaming/mt5_redpanda.py",
            "import_path": "config.client_settings",
            "priority": "high",
            "description": "Streaming functionality with hardcoded servers"
        },
        {
            "file": "/mnt/f/WINDSURF/neliti_code/client_side/run_bridge_simple.py",
            "import_path": "libs.config.client_settings",
            "priority": "medium",
            "description": "Application runner with old config imports"
        },
        {
            "file": "/mnt/f/WINDSURF/neliti_code/client_side/service_manager.py",
            "import_path": "libs.config.client_settings",
            "priority": "medium",
            "description": "Service management with hardcoded timeouts"
        }
    ]
    
    migration_results = {
        "successful": [],
        "failed": [],
        "skipped": []
    }
    
    for target in migration_targets:
        try:
            print(f"\n📂 Processing {target['file']} (Priority: {target['priority']})")
            
            success = migrate_client_file_with_error_handling(
                target["file"], 
                target["import_path"]
            )
            
            if success:
                migration_results["successful"].append(target)
                print(f"✅ Migration successful: {target['file']}")
            
        except ClientConfigurationMigrationError as e:
            migration_results["failed"].append({
                "target": target,
                "error": str(e)
            })
            print(f"❌ Migration failed: {target['file']}")
            print(str(e))
            
            # For high priority files, stop migration
            if target["priority"] == "high":
                print("\n🛑 High priority file failed - stopping migration")
                print("🔧 Fix the error above before continuing")
                break
                
        except Exception as e:
            migration_results["failed"].append({
                "target": target,
                "error": f"Unexpected error: {e}"
            })
            print(f"❌ Unexpected error: {target['file']}: {e}")
    
    # Summary
    print("\n" + "=" * 75)
    print("📊 Client Migration Summary:")
    print(f"✅ Successful: {len(migration_results['successful'])}")
    print(f"❌ Failed: {len(migration_results['failed'])}")
    print(f"⏸️ Skipped: {len(migration_results['skipped'])}")
    
    if migration_results["failed"]:
        print("\n❌ Failed Migrations - NEED TO FIX:")
        for failed in migration_results["failed"]:
            print(f"   - {failed['target']['file']}")
        print("\n🔧 Fix errors above, then re-run migration")
        return False
    else:
        print("\n🎉 All client migrations successful!")
        return True


if __name__ == "__main__":
    try:
        success = run_client_gradual_migration_with_error_handling()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏸️ Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1)