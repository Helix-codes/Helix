"""
AES-256-GCM encryption utilities for Helix

Provides symmetric encryption for file content and metadata,
compatible with the TypeScript SDK.
"""

from __future__ import annotations

import os
import base64
from typing import Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


IV_LENGTH = 12
KEY_LENGTH = 32
TAG_LENGTH = 16


class HelixEncryption:
    """
    Encryption utilities for AES-256-GCM.
    
    Compatible with Web Crypto API used in the TypeScript SDK.
    
    Example:
        >>> enc = HelixEncryption()
        >>> key = enc.generate_key()
        >>> encrypted = enc.encrypt(b"secret data", key)
        >>> decrypted = enc.decrypt(encrypted, key)
    """
    
    def generate_key(self) -> bytes:
        """
        Generate a new random 256-bit encryption key.
        
        Returns:
            32-byte random key
        """
        return os.urandom(KEY_LENGTH)
    
    def encrypt(self, data: bytes, key: bytes) -> bytes:
        """
        Encrypt data with AES-256-GCM.
        
        The IV is prepended to the ciphertext, matching the format
        used by the TypeScript SDK.
        
        Args:
            data: Data to encrypt
            key: 32-byte encryption key
            
        Returns:
            IV + ciphertext + auth tag
        """
        if len(key) != KEY_LENGTH:
            raise ValueError(f"Key must be {KEY_LENGTH} bytes")
        
        iv = os.urandom(IV_LENGTH)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(iv, data, None)
        
        return iv + ciphertext
    
    def decrypt(self, encrypted_data: bytes, key: bytes) -> bytes:
        """
        Decrypt data encrypted with AES-256-GCM.
        
        Expects the IV to be prepended to the ciphertext.
        
        Args:
            encrypted_data: IV + ciphertext + auth tag
            key: 32-byte decryption key
            
        Returns:
            Decrypted data
        """
        if len(key) != KEY_LENGTH:
            raise ValueError(f"Key must be {KEY_LENGTH} bytes")
        
        if len(encrypted_data) < IV_LENGTH + TAG_LENGTH:
            raise ValueError("Encrypted data too short")
        
        iv = encrypted_data[:IV_LENGTH]
        ciphertext = encrypted_data[IV_LENGTH:]
        
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(iv, ciphertext, None)
    
    def export_key(self, key: bytes) -> str:
        """
        Export a key to base64 string for storage.
        
        Args:
            key: Raw key bytes
            
        Returns:
            Base64 encoded key
        """
        return base64.b64encode(key).decode("utf-8")
    
    def import_key(self, key_string: str) -> bytes:
        """
        Import a key from base64 string.
        
        Args:
            key_string: Base64 encoded key
            
        Returns:
            Raw key bytes
        """
        key = base64.b64decode(key_string)
        if len(key) != KEY_LENGTH:
            raise ValueError(f"Invalid key length: expected {KEY_LENGTH} bytes")
        return key
    
    def encrypt_string(self, text: str, key: bytes) -> str:
        """
        Encrypt a string and return base64 encoded result.
        
        Args:
            text: String to encrypt
            key: Encryption key
            
        Returns:
            Base64 encoded encrypted data
        """
        data = text.encode("utf-8")
        encrypted = self.encrypt(data, key)
        return base64.b64encode(encrypted).decode("utf-8")
    
    def decrypt_string(self, encrypted_b64: str, key: bytes) -> str:
        """
        Decrypt a base64 encoded string.
        
        Args:
            encrypted_b64: Base64 encoded encrypted data
            key: Decryption key
            
        Returns:
            Decrypted string
        """
        encrypted = base64.b64decode(encrypted_b64)
        decrypted = self.decrypt(encrypted, key)
        return decrypted.decode("utf-8")


def generate_key() -> bytes:
    """Generate a new random 256-bit encryption key."""
    return os.urandom(KEY_LENGTH)


def encrypt_data(data: bytes, key: bytes) -> bytes:
    """
    Encrypt data with AES-256-GCM.
    
    Args:
        data: Data to encrypt
        key: 32-byte encryption key
        
    Returns:
        IV + ciphertext + auth tag
    """
    if len(key) != KEY_LENGTH:
        raise ValueError(f"Key must be {KEY_LENGTH} bytes")
    
    iv = os.urandom(IV_LENGTH)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, data, None)
    
    return iv + ciphertext


def decrypt_data(encrypted_data: bytes, key: bytes) -> bytes:
    """
    Decrypt data encrypted with AES-256-GCM.
    
    Args:
        encrypted_data: IV + ciphertext + auth tag
        key: 32-byte decryption key
        
    Returns:
        Decrypted data
    """
    if len(key) != KEY_LENGTH:
        raise ValueError(f"Key must be {KEY_LENGTH} bytes")
    
    if len(encrypted_data) < IV_LENGTH + TAG_LENGTH:
        raise ValueError("Encrypted data too short")
    
    iv = encrypted_data[:IV_LENGTH]
    ciphertext = encrypted_data[IV_LENGTH:]
    
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(iv, ciphertext, None)


def export_key(key: bytes) -> str:
    """Export a key to base64 string."""
    return base64.b64encode(key).decode("utf-8")


def import_key(key_string: str) -> bytes:
    """Import a key from base64 string."""
    key = base64.b64decode(key_string)
    if len(key) != KEY_LENGTH:
        raise ValueError(f"Invalid key length: expected {KEY_LENGTH} bytes")
    return key


def derive_key_from_password(
    password: str,
    salt: bytes,
    iterations: int = 100000,
) -> bytes:
    """
    Derive an encryption key from a password using PBKDF2.
    
    Args:
        password: User password
        salt: Random salt (should be stored with encrypted data)
        iterations: Number of PBKDF2 iterations
        
    Returns:
        32-byte derived key
    """
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=iterations,
    )
    
    return kdf.derive(password.encode("utf-8"))


def generate_salt(length: int = 16) -> bytes:
    """Generate a random salt for key derivation."""
    return os.urandom(length)


class KeyStorage:
    """
    Simple key storage for managing encryption keys.
    
    Keys are stored in memory with optional file backup.
    """
    
    def __init__(self):
        self._keys: dict[str, bytes] = {}
    
    def store(self, transaction_id: str, key: bytes) -> None:
        """Store a key for a transaction."""
        self._keys[transaction_id] = key
    
    def get(self, transaction_id: str) -> bytes | None:
        """Get a stored key by transaction ID."""
        return self._keys.get(transaction_id)
    
    def delete(self, transaction_id: str) -> bool:
        """Delete a stored key."""
        if transaction_id in self._keys:
            del self._keys[transaction_id]
            return True
        return False
    
    def export_all(self) -> dict[str, str]:
        """Export all keys as base64 strings."""
        return {
            tx_id: export_key(key)
            for tx_id, key in self._keys.items()
        }
    
    def import_all(self, keys: dict[str, str]) -> None:
        """Import keys from base64 strings."""
        for tx_id, key_b64 in keys.items():
            self._keys[tx_id] = import_key(key_b64)
    
    def save_to_file(self, path: str) -> None:
        """Save keys to a JSON file."""
        import json
        from pathlib import Path
        
        data = self.export_all()
        Path(path).write_text(json.dumps(data, indent=2))
    
    def load_from_file(self, path: str) -> None:
        """Load keys from a JSON file."""
        import json
        from pathlib import Path
        
        data = json.loads(Path(path).read_text())
        self.import_all(data)

# Encryption utilities
