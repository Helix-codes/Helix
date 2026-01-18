use anchor_lang::prelude::*;

/// Maximum length of Arweave transaction ID (base64url encoded)
pub const MAX_TRANSACTION_ID_LEN: usize = 43;

/// Maximum length of encrypted filename
pub const MAX_ENCRYPTED_NAME_LEN: usize = 256;

/// Maximum length of MIME type string
pub const MAX_MIME_TYPE_LEN: usize = 128;

/// Maximum length of encrypted key for sharing
pub const MAX_ENCRYPTED_KEY_LEN: usize = 512;

/// Seed for StorageRegistry PDA
pub const REGISTRY_SEED: &[u8] = b"registry";

/// Seed for FileRecord PDA
pub const FILE_SEED: &[u8] = b"file";

/// Seed for ShareLink PDA
pub const SHARE_SEED: &[u8] = b"share";

/// Global storage registry configuration.
/// Stores program-wide settings and authority information.
#[account]
#[derive(Default)]
pub struct StorageRegistry {
    /// Program authority who can update settings
    pub authority: Pubkey,
    
    /// Base fee in lamports for file registration
    pub base_fee_lamports: u64,
    
    /// Total number of files registered
    pub total_files: u64,
    
    /// Total number of active share links
    pub total_shares: u64,
    
    /// Whether new registrations are paused
    pub is_paused: bool,
    
    /// Bump seed for PDA derivation
    pub bump: u8,
    
    /// Reserved space for future upgrades
    pub _reserved: [u8; 64],
}

impl StorageRegistry {
    pub const LEN: usize = 8  // discriminator
        + 32  // authority
        + 8   // base_fee_lamports
        + 8   // total_files
        + 8   // total_shares
        + 1   // is_paused
        + 1   // bump
        + 64; // reserved
}

/// Individual file record linking a wallet to an Arweave transaction.
/// Stores metadata and access control information.
#[account]
pub struct FileRecord {
    /// Owner's wallet address
    pub owner: Pubkey,
    
    /// Arweave transaction ID (43 characters)
    pub transaction_id: String,
    
    /// Client-encrypted filename (optional)
    pub encrypted_name: Option<String>,
    
    /// MIME type of the file
    pub mime_type: String,
    
    /// File size in bytes
    pub size: u64,
    
    /// Whether the file content is encrypted
    pub is_encrypted: bool,
    
    /// Whether the file is marked as deleted
    pub is_deleted: bool,
    
    /// Unix timestamp when file was registered
    pub created_at: i64,
    
    /// Unix timestamp of last update
    pub updated_at: i64,
    
    /// Number of active share links
    pub share_count: u32,
    
    /// Bump seed for PDA derivation
    pub bump: u8,
    
    /// Reserved space for future upgrades
    pub _reserved: [u8; 32],
}

impl FileRecord {
    pub const LEN: usize = 8  // discriminator
        + 32  // owner
        + 4 + MAX_TRANSACTION_ID_LEN  // transaction_id (string)
        + 1 + 4 + MAX_ENCRYPTED_NAME_LEN  // encrypted_name (option + string)
        + 4 + MAX_MIME_TYPE_LEN  // mime_type (string)
        + 8   // size
        + 1   // is_encrypted
        + 1   // is_deleted
        + 8   // created_at
        + 8   // updated_at
        + 4   // share_count
        + 1   // bump
        + 32; // reserved

    /// Check if the file is accessible (not deleted)
    pub fn is_accessible(&self) -> bool {
        !self.is_deleted
    }

    /// Get the Arweave URL for this file
    pub fn arweave_url(&self) -> String {
        format!("https://arweave.net/{}", self.transaction_id)
    }
}

/// Share link for granting access to a file.
/// Supports time-based expiration and download limits.
#[account]
pub struct ShareLink {
    /// The file being shared
    pub file: Pubkey,
    
    /// Owner who created the share
    pub owner: Pubkey,
    
    /// Specific recipient wallet (None = public link)
    pub recipient: Option<Pubkey>,
    
    /// Encrypted decryption key (for encrypted files)
    pub encrypted_key: Option<String>,
    
    /// Unix timestamp when share expires (None = never)
    pub expires_at: Option<i64>,
    
    /// Maximum number of downloads allowed (None = unlimited)
    pub max_downloads: Option<u32>,
    
    /// Current download count
    pub download_count: u32,
    
    /// Whether the share is revoked
    pub is_revoked: bool,
    
    /// Unix timestamp when share was created
    pub created_at: i64,
    
    /// Bump seed for PDA derivation
    pub bump: u8,
    
    /// Reserved space for future upgrades
    pub _reserved: [u8; 16],
}

impl ShareLink {
    pub const LEN: usize = 8  // discriminator
        + 32  // file
        + 32  // owner
        + 1 + 32  // recipient (option + pubkey)
        + 1 + 4 + MAX_ENCRYPTED_KEY_LEN  // encrypted_key (option + string)
        + 1 + 8   // expires_at (option + i64)
        + 1 + 4   // max_downloads (option + u32)
        + 4   // download_count
        + 1   // is_revoked
        + 8   // created_at
        + 1   // bump
        + 16; // reserved

    /// Check if the share link is still valid
    pub fn is_valid(&self, current_timestamp: i64) -> bool {
        if self.is_revoked {
            return false;
        }

        if let Some(expires_at) = self.expires_at {
            if current_timestamp > expires_at {
                return false;
            }
        }

        if let Some(max) = self.max_downloads {
            if self.download_count >= max {
                return false;
            }
        }

        true
    }

    /// Check if a given wallet can access this share
    pub fn can_access(&self, wallet: &Pubkey, current_timestamp: i64) -> bool {
        if !self.is_valid(current_timestamp) {
            return false;
        }

        match &self.recipient {
            Some(recipient) => wallet == recipient,
            None => true, // Public link
        }
    }

    /// Increment download count and check if still valid
    pub fn record_download(&mut self) -> bool {
        self.download_count = self.download_count.saturating_add(1);
        
        if let Some(max) = self.max_downloads {
            self.download_count <= max
        } else {
            true
        }
    }
}

/// Event emitted when a new file is registered
#[event]
pub struct FileRegistered {
    pub owner: Pubkey,
    pub transaction_id: String,
    pub size: u64,
    pub is_encrypted: bool,
    pub timestamp: i64,
}

/// Event emitted when a share link is created
#[event]
pub struct ShareCreated {
    pub file: Pubkey,
    pub owner: Pubkey,
    pub recipient: Option<Pubkey>,
    pub expires_at: Option<i64>,
    pub timestamp: i64,
}

/// Event emitted when a share link is revoked
#[event]
pub struct ShareRevoked {
    pub share: Pubkey,
    pub owner: Pubkey,
    pub timestamp: i64,
}

/// Event emitted when a file is marked as deleted
#[event]
pub struct FileDeleted {
    pub file: Pubkey,
    pub owner: Pubkey,
    pub timestamp: i64,
}

// Account structures
