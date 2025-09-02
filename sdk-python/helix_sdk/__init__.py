"""
Helix SDK - Python client for permanent encrypted storage on Solana + Arweave

This SDK provides:
- Wallet-based authentication
- AES-256-GCM encryption
- File operations (upload, download, list, delete)
- Share link management
- Arweave integration via Irys

Example usage:
    from helix_sdk import HelixClient
    
    client = HelixClient(keypair_path="~/.config/solana/id.json")
    await client.authenticate()
    
    result = await client.upload_file("document.pdf", encrypt=True)
    print(f"Uploaded: {result.arweave_url}")
"""

from helix_sdk.client import HelixClient, HelixClientConfig
from helix_sdk.encryption import (
    HelixEncryption,
    generate_key,
    encrypt_data,
    decrypt_data,
    export_key,
    import_key,
)

__version__ = "0.1.0"
__author__ = "Helix Team"
__all__ = [
    "HelixClient",
    "HelixClientConfig",
    "HelixEncryption",
    "generate_key",
    "encrypt_data",
    "decrypt_data",
    "export_key",
    "import_key",
]
