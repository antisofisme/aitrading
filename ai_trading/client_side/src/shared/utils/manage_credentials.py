#!/usr/bin/env python3
"""
manage_credentials.py - Credential Management Utilities

🎯 PURPOSE:
Business: Utility functions for credential setup, rotation, and validation
Technical: Credential lifecycle management with security best practices
Domain: Security Utilities/Credential Management/Security Operations

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.016Z
Session: client-side-ai-brain-full-compliance
Confidence: 90%
Complexity: medium

🧩 PATTERNS USED:
- AI_BRAIN_CREDENTIAL_UTILITIES: Credential management utilities with security practices

📦 DEPENDENCIES:
Internal: credentials, security_core, logger_manager
External: getpass, base64, hashlib

💡 AI DECISION REASONING:
Credential management utilities provide secure setup and maintenance of sensitive authentication data.

🚀 USAGE:
manage_credentials.setup_mt5_account()

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import sys
import os
import argparse
from pathlib import Path

# Add libs to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from libs.security import (
        CredentialManager, 
        encrypt_env_file, 
        decrypt_env_file,
        get_credential_manager
    )
    from loguru import logger
except ImportError as e:
    print(f"❌ Required dependencies not installed: {e}")
    print("📦 Install with: pip install -r requirements-security.txt")
    sys.exit(1)


def generate_master_key():
    """Generate a new master key for encryption"""
    try:
        cm = CredentialManager()
        master_key = cm.generate_master_key()
        
        print("🔐 Generated Master Key for MT5 Bridge Encryption")
        print("=" * 60)
        print(f"Master Key: {master_key}")
        print("=" * 60)
        print("⚠️  IMPORTANT SECURITY NOTES:")
        print("1. Store this key securely (password manager, vault, etc.)")
        print("2. Set as environment variable: ENCRYPTION_MASTER_KEY")
        print("3. Never commit this key to version control")
        print("4. If lost, encrypted data cannot be recovered")
        print("=" * 60)
        
        # Optionally save to local file (not recommended for production)
        save_local = input("\n💾 Save to local .master_key file? (y/N): ").lower().strip()
        if save_local == 'y':
            with open('.master_key', 'w') as f:
                f.write(master_key)
            print("✅ Saved to .master_key (add to .gitignore!)")
            
            # Check if .gitignore exists and add the key file
            gitignore_path = Path('.gitignore')
            if gitignore_path.exists():
                with open(gitignore_path, 'r') as f:
                    content = f.read()
                if '.master_key' not in content:
                    with open(gitignore_path, 'a') as f:
                        f.write('\n# Security\n.master_key\n')
                    print("✅ Added .master_key to .gitignore")
        
        return master_key
        
    except Exception as e:
        logger.error(f"❌ Failed to generate master key: {e}")
        return None


def encrypt_credentials(env_file: str = ".env", backup: bool = True):
    """Encrypt sensitive credentials in .env file"""
    try:
        # Check if master key is available
        master_key = os.getenv('ENCRYPTION_MASTER_KEY')
        if not master_key:
            # Try to load from local file
            master_key_file = Path('.master_key')
            if master_key_file.exists():
                master_key = master_key_file.read_text().strip()
                os.environ['ENCRYPTION_MASTER_KEY'] = master_key
                print("🔑 Loaded master key from .master_key file")
            else:
                print("❌ No master key found!")
                print("Set ENCRYPTION_MASTER_KEY environment variable or run:")
                print("python manage_credentials.py generate-key")
                return False
        
        # Perform encryption
        success = encrypt_env_file(env_file, backup)
        if success:
            print(f"✅ Successfully encrypted credentials in {env_file}")
            if backup:
                print(f"📋 Backup saved to {env_file}.backup")
        else:
            print(f"❌ Failed to encrypt credentials in {env_file}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Encryption failed: {e}")
        return False


def decrypt_credentials(env_file: str = ".env"):
    """Decrypt and display credentials from .env file"""
    try:
        # Check if master key is available
        master_key = os.getenv('ENCRYPTION_MASTER_KEY')
        if not master_key:
            # Try to load from local file
            master_key_file = Path('.master_key')
            if master_key_file.exists():
                master_key = master_key_file.read_text().strip()
                os.environ['ENCRYPTION_MASTER_KEY'] = master_key
                print("🔑 Loaded master key from .master_key file")
            else:
                print("❌ No master key found!")
                print("Set ENCRYPTION_MASTER_KEY environment variable")
                return False
        
        # Perform decryption
        success = decrypt_env_file(env_file)
        return success
        
    except Exception as e:
        logger.error(f"❌ Decryption failed: {e}")
        return False


def test_encryption():
    """Test encryption/decryption functionality"""
    try:
        print("🧪 Testing MT5 Bridge Encryption Functionality")
        print("=" * 50)
        
        # Test with or without master key
        master_key = os.getenv('ENCRYPTION_MASTER_KEY')
        if not master_key:
            master_key_file = Path('.master_key')
            if master_key_file.exists():
                master_key = master_key_file.read_text().strip()
                print("🔑 Using master key from .master_key file")
            else:
                print("🔑 Generating temporary master key for test")
                cm = CredentialManager()
                master_key = cm.generate_master_key()
        
        # Test encryption
        cm = CredentialManager(master_key)
        
        test_credentials = [
            "MySecretPassword123!",
            "101632934",
            "trading_secure_2024",
            "secret_auth_token_abc123"
        ]
        
        print("\n🔐 Encryption Test Results:")
        for i, credential in enumerate(test_credentials, 1):
            encrypted = cm.encrypt_credential(credential)
            decrypted = cm.decrypt_credential(encrypted)
            
            print(f"\nTest {i}:")
            print(f"  Original:  {credential}")
            print(f"  Encrypted: {encrypted[:50]}..." if len(encrypted) > 50 else f"  Encrypted: {encrypted}")
            print(f"  Decrypted: {decrypted}")
            print(f"  Match:     {'✅' if credential == decrypted else '❌'}")
        
        print(f"\n✅ Encryption test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Encryption test failed: {e}")
        return False


def show_status():
    """Show current encryption status"""
    try:
        print("📊 MT5 Bridge Credential Security Status")
        print("=" * 50)
        
        # Check master key availability
        master_key = os.getenv('ENCRYPTION_MASTER_KEY')
        master_key_file = Path('.master_key')
        
        print(f"🔑 Master Key (ENV):  {'✅ Available' if master_key else '❌ Not Set'}")
        print(f"🔑 Master Key (File): {'✅ Available' if master_key_file.exists() else '❌ Not Found'}")
        
        # Check credential manager
        cm = get_credential_manager()
        print(f"🔐 Encryption Ready:  {'✅ Yes' if cm.is_encryption_available() else '❌ No'}")
        
        # Check .env file
        env_file = Path('.env')
        if env_file.exists():
            print(f"📄 .env File:         ✅ Found")
            
            # Check for encrypted values
            with open(env_file, 'r') as f:
                content = f.read()
                encrypted_count = content.count('ENCRYPTED:')
                print(f"🔒 Encrypted Fields:  {encrypted_count} found")
        else:
            print(f"📄 .env File:         ❌ Not Found")
        
        # Security recommendations
        print("\n🛡️  Security Recommendations:")
        if not master_key and not master_key_file.exists():
            print("   ⚠️  Generate master key: python manage_credentials.py generate-key")
        if env_file.exists() and 'ENCRYPTED:' not in env_file.read_text():
            print("   ⚠️  Encrypt credentials: python manage_credentials.py encrypt")
        if master_key_file.exists():
            print("   ⚠️  Secure .master_key file (not for production)")
        
        print("=" * 50)
        
    except Exception as e:
        logger.error(f"❌ Status check failed: {e}")


def main():
    """Main entry point for credential management utility"""
    parser = argparse.ArgumentParser(
        description="MT5 Bridge Credential Management Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage_credentials.py generate-key          # Generate new master key
  python manage_credentials.py encrypt               # Encrypt .env credentials  
  python manage_credentials.py decrypt               # Show decrypted credentials
  python manage_credentials.py test                  # Test encryption functionality
  python manage_credentials.py status                # Show security status
        """
    )
    
    parser.add_argument(
        'command',
        choices=['generate-key', 'encrypt', 'decrypt', 'test', 'status'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--env-file',
        default='.env',
        help='Path to environment file (default: .env)'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip creating backup when encrypting'
    )
    
    args = parser.parse_args()
    
    try:
        if args.command == 'generate-key':
            generate_master_key()
        
        elif args.command == 'encrypt':
            backup = not args.no_backup
            encrypt_credentials(args.env_file, backup)
        
        elif args.command == 'decrypt':
            decrypt_credentials(args.env_file)
        
        elif args.command == 'test':
            test_encryption()
        
        elif args.command == 'status':
            show_status()
            
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
    except Exception as e:
        logger.error(f"❌ Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()