"""
Helix Client - Main client for interacting with Helix storage

Provides wallet authentication, file operations, and encryption management
for AI agents and automated systems.
"""

from __future__ import annotations

import asyncio
import base64
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

import httpx
from nacl.signing import SigningKey, VerifyKey
from solders.keypair import Keypair
from solders.pubkey import Pubkey

from helix_sdk.encryption import HelixEncryption


@dataclass
class HelixClientConfig:
    """Configuration for HelixClient"""
    
    api_base_url: str = "https://heyx-production.up.railway.app"
    rpc_endpoint: str = "https://api.mainnet-beta.solana.com"
    timeout: float = 30.0
    debug: bool = False


@dataclass
class FileRecord:
    """File record from the Helix API"""
    
    id: str
    transaction_id: str
    mime_type: str
    size: int
    is_encrypted: bool
    created_at: str
    encrypted_name: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class ShareLink:
    """Share link details"""
    
    id: str
    url: str
    download_count: int
    created_at: str
    expires_at: Optional[str] = None
    max_downloads: Optional[int] = None


@dataclass
class UploadResult:
    """Result from file upload"""
    
    transaction_id: str
    arweave_url: str
    file_id: str
    encryption_key: Optional[str] = None


class HelixClient:
    """
    Main client for interacting with Helix permanent encrypted storage.
    
    Designed for use by AI agents and automated systems that need
    programmatic access to Helix storage.
    
    Example:
        >>> client = HelixClient.from_keypair_file("~/.config/solana/id.json")
        >>> await client.authenticate()
        >>> files = await client.list_files()
        >>> for f in files:
        ...     print(f.transaction_id)
    """
    
    def __init__(
        self,
        keypair: Keypair,
        config: Optional[HelixClientConfig] = None,
    ):
        """
        Initialize the Helix client.
        
        Args:
            keypair: Solana keypair for authentication
            config: Client configuration options
        """
        self.keypair = keypair
        self.config = config or HelixClientConfig()
        self.encryption = HelixEncryption()
        self._auth_token: Optional[str] = None
        self._http_client: Optional[httpx.AsyncClient] = None
    
    @classmethod
    def from_keypair_file(
        cls,
        path: str | Path,
        config: Optional[HelixClientConfig] = None,
    ) -> HelixClient:
        """
        Create a client from a keypair JSON file.
        
        Args:
            path: Path to the keypair JSON file
            config: Client configuration options
            
        Returns:
            Configured HelixClient instance
        """
        path = Path(path).expanduser()
        with open(path, "r") as f:
            secret_key = json.load(f)
        
        if isinstance(secret_key, list):
            keypair = Keypair.from_bytes(bytes(secret_key))
        else:
            raise ValueError("Invalid keypair format")
        
        return cls(keypair=keypair, config=config)
    
    @classmethod
    def from_secret_key(
        cls,
        secret_key: bytes,
        config: Optional[HelixClientConfig] = None,
    ) -> HelixClient:
        """
        Create a client from raw secret key bytes.
        
        Args:
            secret_key: 64-byte secret key
            config: Client configuration options
            
        Returns:
            Configured HelixClient instance
        """
        keypair = Keypair.from_bytes(secret_key)
        return cls(keypair=keypair, config=config)
    
    @property
    def wallet_address(self) -> str:
        """Get the wallet address as a string."""
        return str(self.keypair.pubkey())
    
    @property
    def is_authenticated(self) -> bool:
        """Check if the client has a valid auth token."""
        return self._auth_token is not None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self.config.api_base_url,
                timeout=self.config.timeout,
            )
        return self._http_client
    
    def _get_headers(self) -> dict[str, str]:
        """Build request headers."""
        headers = {"Content-Type": "application/json"}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        return headers
    
    def _log(self, message: str) -> None:
        """Log a debug message."""
        if self.config.debug:
            print(f"[Helix] {message}")
    
    async def authenticate(self) -> str:
        """
        Authenticate with the Helix API using wallet signature.
        
        Returns:
            JWT token for authenticated requests
            
        Raises:
            httpx.HTTPError: If authentication fails
        """
        client = await self._get_client()
        
        response = await client.get(
            f"/api/auth/nonce?wallet={self.wallet_address}"
        )
        response.raise_for_status()
        nonce = response.json()["nonce"]
        self._log(f"Got nonce: {nonce}")
        
        message = f"Sign in to Helix: {nonce}"
        message_bytes = message.encode("utf-8")
        
        signature = self.keypair.sign_message(message_bytes)
        signature_b64 = base64.b64encode(bytes(signature)).decode("utf-8")
        self._log("Message signed")
        
        response = await client.post(
            "/api/auth/verify",
            json={
                "wallet": self.wallet_address,
                "signature": signature_b64,
                "nonce": nonce,
            },
        )
        response.raise_for_status()
        
        self._auth_token = response.json()["token"]
        self._log("Authentication successful")
        
        return self._auth_token
    
    async def list_files(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> list[FileRecord]:
        """
        List all files for the authenticated wallet.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            List of file records
        """
        if not self.is_authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        client = await self._get_client()
        response = await client.get(
            "/api/files",
            params={"page": page, "pageSize": page_size},
            headers=self._get_headers(),
        )
        response.raise_for_status()
        
        data = response.json()
        return [
            FileRecord(
                id=f["id"],
                transaction_id=f["transactionId"],
                encrypted_name=f.get("encryptedName"),
                mime_type=f["mimeType"],
                size=f["size"],
                is_encrypted=f["isEncrypted"],
                created_at=f["createdAt"],
                updated_at=f.get("updatedAt"),
            )
            for f in data["files"]
        ]
    
    async def get_file(self, file_id: str) -> FileRecord:
        """
        Get a single file record by ID.
        
        Args:
            file_id: File record ID
            
        Returns:
            File record
        """
        if not self.is_authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        client = await self._get_client()
        response = await client.get(
            f"/api/files/{file_id}",
            headers=self._get_headers(),
        )
        response.raise_for_status()
        
        f = response.json()
        return FileRecord(
            id=f["id"],
            transaction_id=f["transactionId"],
            encrypted_name=f.get("encryptedName"),
            mime_type=f["mimeType"],
            size=f["size"],
            is_encrypted=f["isEncrypted"],
            created_at=f["createdAt"],
            updated_at=f.get("updatedAt"),
        )
    
    async def upload_file(
        self,
        file_path: str | Path,
        encrypt: bool = True,
        mime_type: Optional[str] = None,
    ) -> UploadResult:
        """
        Upload a file with optional encryption.
        
        Args:
            file_path: Path to the file to upload
            encrypt: Whether to encrypt the file
            mime_type: MIME type (auto-detected if not provided)
            
        Returns:
            Upload result with transaction ID and encryption key
        """
        if not self.is_authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        file_path = Path(file_path).expanduser()
        
        with open(file_path, "rb") as f:
            data = f.read()
        
        if mime_type is None:
            mime_type = self._guess_mime_type(file_path)
        
        encryption_key: Optional[str] = None
        
        if encrypt:
            key = self.encryption.generate_key()
            data = self.encryption.encrypt(data, key)
            encryption_key = self.encryption.export_key(key)
            self._log("File encrypted")
        
        transaction_id = await self._upload_to_arweave(data, mime_type)
        self._log(f"Uploaded to Arweave: {transaction_id}")
        
        encrypted_name: Optional[str] = None
        if encrypt and encryption_key:
            key = self.encryption.import_key(encryption_key)
            name_bytes = file_path.name.encode("utf-8")
            encrypted_name_bytes = self.encryption.encrypt(name_bytes, key)
            encrypted_name = base64.b64encode(encrypted_name_bytes).decode("utf-8")
        
        client = await self._get_client()
        response = await client.post(
            "/api/files",
            json={
                "transactionId": transaction_id,
                "encryptedName": encrypted_name,
                "mimeType": mime_type,
                "size": len(data),
                "isEncrypted": encrypt,
            },
            headers=self._get_headers(),
        )
        response.raise_for_status()
        
        file_record = response.json()
        self._log("File record created")
        
        return UploadResult(
            transaction_id=transaction_id,
            arweave_url=f"https://arweave.net/{transaction_id}",
            file_id=file_record["id"],
            encryption_key=encryption_key,
        )
    
    async def upload_bytes(
        self,
        data: bytes,
        filename: str,
        mime_type: str,
        encrypt: bool = True,
    ) -> UploadResult:
        """
        Upload raw bytes with optional encryption.
        
        Args:
            data: Raw bytes to upload
            filename: Original filename
            mime_type: MIME type
            encrypt: Whether to encrypt
            
        Returns:
            Upload result
        """
        if not self.is_authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        encryption_key: Optional[str] = None
        upload_data = data
        
        if encrypt:
            key = self.encryption.generate_key()
            upload_data = self.encryption.encrypt(data, key)
            encryption_key = self.encryption.export_key(key)
            self._log("Data encrypted")
        
        transaction_id = await self._upload_to_arweave(upload_data, mime_type)
        self._log(f"Uploaded to Arweave: {transaction_id}")
        
        encrypted_name: Optional[str] = None
        if encrypt and encryption_key:
            key = self.encryption.import_key(encryption_key)
            name_bytes = filename.encode("utf-8")
            encrypted_name_bytes = self.encryption.encrypt(name_bytes, key)
            encrypted_name = base64.b64encode(encrypted_name_bytes).decode("utf-8")
        
        client = await self._get_client()
        response = await client.post(
            "/api/files",
            json={
                "transactionId": transaction_id,
                "encryptedName": encrypted_name,
                "mimeType": mime_type,
                "size": len(upload_data),
                "isEncrypted": encrypt,
            },
            headers=self._get_headers(),
        )
        response.raise_for_status()
        
        file_record = response.json()
        self._log("File record created")
        
        return UploadResult(
            transaction_id=transaction_id,
            arweave_url=f"https://arweave.net/{transaction_id}",
            file_id=file_record["id"],
            encryption_key=encryption_key,
        )
    
    async def download_file(
        self,
        transaction_id: str,
        encryption_key: Optional[str] = None,
    ) -> bytes:
        """
        Download and optionally decrypt a file.
        
        Args:
            transaction_id: Arweave transaction ID
            encryption_key: Base64 encryption key for decryption
            
        Returns:
            Decrypted file data
        """
        url = f"https://arweave.net/{transaction_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.content
        
        if encryption_key:
            key = self.encryption.import_key(encryption_key)
            data = self.encryption.decrypt(data, key)
            self._log("File decrypted")
        
        return data
    
    async def delete_file(self, file_id: str) -> None:
        """
        Delete a file record (does not delete from Arweave).
        
        Args:
            file_id: File record ID
        """
        if not self.is_authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        client = await self._get_client()
        response = await client.delete(
            f"/api/files/{file_id}",
            headers=self._get_headers(),
        )
        response.raise_for_status()
        self._log(f"File deleted: {file_id}")
    
    async def create_share_link(
        self,
        file_id: str,
        expires_at: Optional[str] = None,
        max_downloads: Optional[int] = None,
        encrypted_key: Optional[str] = None,
    ) -> ShareLink:
        """
        Create a share link for a file.
        
        Args:
            file_id: File record ID
            expires_at: ISO timestamp for expiration
            max_downloads: Maximum number of downloads
            encrypted_key: Encrypted decryption key
            
        Returns:
            Share link details
        """
        if not self.is_authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        client = await self._get_client()
        response = await client.post(
            "/api/share",
            json={
                "fileId": file_id,
                "expiresAt": expires_at,
                "maxDownloads": max_downloads,
                "encryptedKey": encrypted_key,
            },
            headers=self._get_headers(),
        )
        response.raise_for_status()
        
        data = response.json()["shareLink"]
        return ShareLink(
            id=data["id"],
            url=data["url"],
            expires_at=data.get("expiresAt"),
            max_downloads=data.get("maxDownloads"),
            download_count=data.get("downloadCount", 0),
            created_at=data["createdAt"] if "createdAt" in data else "",
        )
    
    async def _upload_to_arweave(self, data: bytes, mime_type: str) -> str:
        """
        Upload data to Arweave via the Helix API.
        
        This is a simplified implementation that delegates to the server.
        For direct Irys integration, additional setup is required.
        """
        client = await self._get_client()
        
        response = await client.post(
            "/api/upload",
            content=data,
            headers={
                **self._get_headers(),
                "Content-Type": mime_type,
            },
        )
        response.raise_for_status()
        
        return response.json()["transactionId"]
    
    def _guess_mime_type(self, path: Path) -> str:
        """Guess MIME type from file extension."""
        suffix = path.suffix.lower()
        mime_types = {
            ".txt": "text/plain",
            ".html": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".xml": "application/xml",
            ".pdf": "application/pdf",
            ".zip": "application/zip",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".mp3": "audio/mpeg",
            ".mp4": "video/mp4",
            ".webm": "video/webm",
        }
        return mime_types.get(suffix, "application/octet-stream")
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None
    
    async def __aenter__(self) -> HelixClient:
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

# v0.1.0
