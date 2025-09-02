# Helix Storage SDK

A comprehensive SDK suite for permanent encrypted storage on Solana and Arweave.

## Architecture

```
                                    HELIX ARCHITECTURE
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                           CLIENT LAYER                                   │
    │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐          │
    │  │  TypeScript SDK │  │   Python SDK    │  │   Rust Program  │          │
    │  │  (Browser/Node) │  │   (AI Agents)   │  │    (On-chain)   │          │
    │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘          │
    └───────────┼────────────────────┼────────────────────┼────────────────────┘
                │                    │                    │
    ┌───────────┼────────────────────┼────────────────────┼────────────────────┐
    │           ▼                    ▼                    ▼                    │
    │  ┌─────────────────────────────────────────────────────────────────┐    │
    │  │                     HELIX API LAYER                              │    │
    │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │    │
    │  │  │   Auth   │  │  Files   │  │  Share   │  │  Upload  │         │    │
    │  │  │ (Nonce)  │  │  (CRUD)  │  │  (Links) │  │  (Irys)  │         │    │
    │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘         │    │
    │  └─────────────────────────────────────────────────────────────────┘    │
    │                           TRANSACTION LAYER                              │
    └──────────────────────────────────────────────────────────────────────────┘
                │                    │                    │
    ┌───────────┼────────────────────┼────────────────────┼────────────────────┐
    │           ▼                    ▼                    ▼                    │
    │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐          │
    │  │     SOLANA      │  │      IRYS       │  │    ARWEAVE      │          │
    │  │   (Payments)    │  │   (Bundler)     │  │   (Storage)     │          │
    │  │   (Registry)    │  │                 │  │   (Permanent)   │          │
    │  └─────────────────┘  └─────────────────┘  └─────────────────┘          │
    │                           STORAGE LAYER                                  │
    └──────────────────────────────────────────────────────────────────────────┘
```

## Components

### Rust Solana Program

On-chain program for file registry and access control.

**Location:** `programs/helix-storage/`

```rust
use anchor_lang::prelude::*;

#[account]
pub struct FileRecord {
    pub owner: Pubkey,
    pub transaction_id: String,
    pub encrypted_name: Option<String>,
    pub mime_type: String,
    pub size: u64,
    pub is_encrypted: bool,
    pub created_at: i64,
}

#[account]
pub struct ShareLink {
    pub file: Pubkey,
    pub owner: Pubkey,
    pub recipient: Option<Pubkey>,
    pub expires_at: Option<i64>,
    pub max_downloads: Option<u32>,
    pub download_count: u32,
}
```

**Build:**

```bash
cd programs/helix-storage
cargo build-sbf
```

### TypeScript SDK

Browser and Node.js client for web applications.

**Location:** `sdk/typescript/`

```typescript
import { HelixClient } from '@helix/sdk';

const client = new HelixClient({
  network: 'mainnet-beta',
  apiBaseUrl: 'https://helix.storage'
});

await client.connect(walletAdapter);
await client.authenticate();

const result = await client.uploadFile(fileBuffer, {
  name: 'document.pdf',
  mimeType: 'application/pdf',
  encrypt: true
});

console.log(`Stored at: ${result.arweaveUrl}`);
console.log(`Encryption key: ${result.encryptionKey}`);
```

**Encryption Example:**

```typescript
import { HelixEncryption } from '@helix/sdk';

const encryption = new HelixEncryption();

const key = await encryption.generateKey();
const encrypted = await encryption.encrypt(fileData, key);
const keyString = await encryption.exportKey(key);

const decrypted = await encryption.decrypt(encrypted.data, key);
```

**Build from source:**

```bash
cd sdk/typescript
npm install
npm run build
```

### Python SDK

Client for AI agents and automated systems.

**Location:** `sdk-python/`

```python
from helix_sdk import HelixClient

client = HelixClient.from_keypair_file("~/.config/solana/id.json")

async with client:
    await client.authenticate()
    
    result = await client.upload_file(
        "document.pdf",
        encrypt=True
    )
    
    print(f"Stored at: {result.arweave_url}")
    print(f"Key: {result.encryption_key}")
```

**Encryption Example:**

```python
from helix_sdk import HelixEncryption, generate_key, encrypt_data

enc = HelixEncryption()

key = enc.generate_key()
encrypted = enc.encrypt(data, key)
key_b64 = enc.export_key(key)

decrypted = enc.decrypt(encrypted, key)
```

**Install from source:**

```bash
cd sdk-python
pip install -e .
```

## Installation

### From Source (Recommended)

Clone the repository and build each component:

```bash
git clone https://github.com/Helix-codes/helix-storage.git
cd helix-storage
```

**Rust Program:**

```bash
cd programs/helix-storage
cargo build-sbf
```

**TypeScript SDK:**

```bash
cd sdk/typescript
npm install
npm run build
```

**Python SDK:**

```bash
cd sdk-python
pip install -e .
```

### Dependencies

**Rust:**
- Rust 1.70+
- Solana CLI 1.17+
- Anchor 0.29.0

**TypeScript:**
- Node.js 18+
- npm or yarn

**Python:**
- Python 3.9+
- pip

## API Reference

### Authentication

Wallet-based authentication using message signing.

```
GET  /api/auth/nonce?wallet={address}  -> { nonce: string }
POST /api/auth/verify                  -> { token: string }
```

### Files

```
GET    /api/files              -> { files: FileRecord[], total, page, pageSize }
POST   /api/files              -> FileRecord
DELETE /api/files/{id}         -> void
```

### Sharing

```
POST /api/share                -> { shareLink: ShareLink }
GET  /api/share/{id}           -> ShareLink
```

## Security

### Encryption

- Algorithm: AES-256-GCM
- Key: 256-bit CSPRNG
- IV: 96-bit random per encryption
- Format: [IV (12 bytes)][Ciphertext][Auth Tag (16 bytes)]

### Key Management

- Keys generated client-side
- Never transmitted to server
- Stored in browser localStorage / local file
- One key per file

## Data Flow

```
1. File Selected
   └─> Browser FileReader API loads into memory

2. Encryption (if enabled)
   └─> AES-256-GCM with random key
   └─> Key stored locally

3. Cost Calculation
   └─> Irys API returns storage cost in SOL

4. Upload
   └─> Wallet signs Solana transaction
   └─> Irys uploads to Arweave
   └─> Returns transaction ID

5. Registry
   └─> Metadata saved to Helix API
   └─> On-chain record created

6. Access
   └─> arweave.net/{transactionId}
   └─> Decrypt with stored key
```

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

See CONTRIBUTING.md for details.
