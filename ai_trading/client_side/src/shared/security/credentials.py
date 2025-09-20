"""
credentials.py - Credentials Management System

🎯 PURPOSE:
Business: Secure management of trading credentials and API keys
Technical: Encrypted credential storage with secure access patterns
Domain: Security/Credentials/Authentication/Encryption

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.000Z
Session: client-side-ai-brain-full-compliance
Confidence: 94%
Complexity: high

🧩 PATTERNS USED:
- AI_BRAIN_CREDENTIALS_MANAGEMENT: Secure credentials management with encryption

📦 DEPENDENCIES:
Internal: security_core, config_manager
External: keyring, cryptography, getpass

💡 AI DECISION REASONING:
Trading systems require secure credential management to protect sensitive account information and API keys.

🚀 USAGE:
credentials.get_mt5_credentials()

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import os
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from loguru import logger


class CredentialManager:
    """
    Manages encrypted storage and retrieval of sensitive credentials
    Uses Fernet symmetric encryption with PBKDF2 key derivation
    """
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize credential manager
        
        Args:
            master_key: Master key for encryption (uses env var if not provided)
        """
        self.master_key = master_key or os.getenv('ENCRYPTION_MASTER_KEY')
        self._fernet = None
        
        if self.master_key:
            self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize Fernet encryption with derived key"""
        try:
            # Derive key from master key using PBKDF2
            salt = b'mt5_bridge_salt_2024'  # Fixed salt for consistency
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
            self._fernet = Fernet(key)
            logger.debug("🔐 Encryption initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize encryption: {e}")
            self._fernet = None
    
    def encrypt_credential(self, credential: str) -> str:
        """
        Encrypt a credential string
        
        Args:
            credential: Plain text credential to encrypt
            
        Returns:
            Base64 encoded encrypted credential
        """
        if not self._fernet:
            logger.warning("⚠️ Encryption not available, returning plain text")
            return credential
        
        try:
            encrypted = self._fernet.encrypt(credential.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"❌ Failed to encrypt credential: {e}")
            return credential
    
    def decrypt_credential(self, encrypted_credential: str) -> str:
        """
        Decrypt an encrypted credential
        
        Args:
            encrypted_credential: Base64 encoded encrypted credential
            
        Returns:
            Plain text credential
        """
        if not self._fernet:
            logger.warning("⚠️ Encryption not available, returning as-is")
            return encrypted_credential
        
        try:
            # Check if it's actually encrypted (starts with our prefix)
            if not encrypted_credential.startswith('gAAA'):  # Fernet tokens start with this
                return encrypted_credential  # Return as-is if not encrypted
            
            decoded = base64.urlsafe_b64decode(encrypted_credential.encode())
            decrypted = self._fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.warning(f"⚠️ Failed to decrypt credential, using as-is: {e}")
            return encrypted_credential
    
    def is_encryption_available(self) -> bool:
        """Check if encryption is available"""
        return self._fernet is not None
    
    def generate_master_key(self) -> str:
        """Generate a new master key for encryption"""
        return Fernet.generate_key().decode()


class SecureConfig:
    """
    Wrapper for configuration values that may contain encrypted credentials
    """
    
    def __init__(self, credential_manager: CredentialManager):
        self.credential_manager = credential_manager
    
    def get_secure_value(self, value: str, field_name: str = "") -> str:
        """
        Get a configuration value, decrypting if necessary
        
        Args:
            value: Configuration value (may be encrypted)
            field_name: Name of the field for logging
            
        Returns:
            Decrypted plain text value
        """
        if not value:
            return value
        
        # Check if value appears to be encrypted
        if value.startswith('ENCRYPTED:'):
            encrypted_value = value[10:]  # Remove 'ENCRYPTED:' prefix
            logger.debug(f"🔓 Decrypting {field_name}")
            return self.credential_manager.decrypt_credential(encrypted_value)
        
        return value
    
    def set_secure_value(self, value: str, encrypt: bool = True) -> str:
        """
        Set a configuration value, encrypting if requested
        
        Args:
            value: Plain text value to store
            encrypt: Whether to encrypt the value
            
        Returns:
            Value ready for storage (encrypted with prefix if encrypted)
        """
        if not encrypt or not value:
            return value
        
        if not self.credential_manager.is_encryption_available():
            logger.warning("⚠️ Encryption not available, storing plain text")
            return value
        
        encrypted = self.credential_manager.encrypt_credential(value)
        return f"ENCRYPTED:{encrypted}"


# Global credential manager instance
_credential_manager = None


def get_credential_manager() -> CredentialManager:
    """Get global credential manager instance"""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = CredentialManager()
    return _credential_manager


def encrypt_env_file(env_file_path: str = ".env", backup: bool = True):
    """
    Encrypt sensitive values in .env file
    
    Args:
        env_file_path: Path to .env file
        backup: Whether to create backup before encryption
    """
    try:
        credential_manager = get_credential_manager()
        
        if not credential_manager.is_encryption_available():
            logger.error("❌ Encryption not available - set ENCRYPTION_MASTER_KEY")
            return False
        
        if not os.path.exists(env_file_path):
            logger.error(f"❌ Environment file not found: {env_file_path}")
            return False
        
        # Create backup if requested
        if backup:
            backup_path = f"{env_file_path}.backup"
            import shutil
            shutil.copy2(env_file_path, backup_path)
            logger.info(f"📋 Backup created: {backup_path}")
        
        # Read current env file
        with open(env_file_path, 'r') as f:
            lines = f.readlines()
        
        # Sensitive fields to encrypt
        sensitive_fields = {
            'MT5_PASSWORD',
            'MT5_LOGIN',
            'CLICKHOUSE_PASSWORD',
            'BACKEND_AUTH_TOKEN',
        }
        
        # Process lines
        updated_lines = []
        encrypted_count = 0
        
        for line in lines:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                if key in sensitive_fields and value and not value.startswith('ENCRYPTED:'):
                    secure_config = SecureConfig(credential_manager)
                    encrypted_value = secure_config.set_secure_value(value, encrypt=True)
                    updated_lines.append(f"{key}={encrypted_value}\n")
                    encrypted_count += 1
                    logger.info(f"🔐 Encrypted {key}")
                else:
                    updated_lines.append(line + '\n')
            else:
                updated_lines.append(line + '\n')
        
        # Write updated file
        with open(env_file_path, 'w') as f:
            f.writelines(updated_lines)
        
        logger.success(f"✅ Encrypted {encrypted_count} sensitive fields in {env_file_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to encrypt env file: {e}")
        return False


def decrypt_env_file(env_file_path: str = ".env"):
    """
    Decrypt values in .env file for debugging/verification
    
    Args:
        env_file_path: Path to .env file
    """
    try:
        credential_manager = get_credential_manager()
        
        if not credential_manager.is_encryption_available():
            logger.error("❌ Encryption not available - set ENCRYPTION_MASTER_KEY")
            return False
        
        if not os.path.exists(env_file_path):
            logger.error(f"❌ Environment file not found: {env_file_path}")
            return False
        
        # Read env file
        with open(env_file_path, 'r') as f:
            lines = f.readlines()
        
        # Process lines and show decrypted values
        secure_config = SecureConfig(credential_manager)
        decrypted_count = 0
        
        print("🔓 Decrypted Environment Variables:")
        print("=" * 50)
        
        for line in lines:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                if value.startswith('ENCRYPTED:'):
                    decrypted_value = secure_config.get_secure_value(value, key)
                    print(f"{key}: {decrypted_value}")
                    decrypted_count += 1
                elif key in ['MT5_PASSWORD', 'CLICKHOUSE_PASSWORD', 'BACKEND_AUTH_TOKEN']:
                    print(f"{key}: {value} (not encrypted)")
        
        print("=" * 50)
        logger.info(f"✅ Decrypted {decrypted_count} encrypted fields")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to decrypt env file: {e}")
        return False


if __name__ == "__main__":
    # Demo usage
    print("🔐 MT5 Bridge Credential Security Demo")
    print("=" * 40)
    
    # Generate master key
    cm = CredentialManager()
    master_key = cm.generate_master_key()
    print(f"Generated Master Key: {master_key}")
    
    # Test encryption
    cm_with_key = CredentialManager(master_key)
    
    test_password = "your_test_password_here"
    encrypted = cm_with_key.encrypt_credential(test_password)
    decrypted = cm_with_key.decrypt_credential(encrypted)
    
    print(f"Original: {test_password}")
    print(f"Encrypted: {encrypted}")
    print(f"Decrypted: {decrypted}")
    print(f"Match: {test_password == decrypted}")