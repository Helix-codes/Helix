use anchor_lang::prelude::*;

pub mod error;
pub mod instructions;
pub mod state;

use instructions::*;

declare_id!("HeLiX1111111111111111111111111111111111111");

/// Helix Storage Program
/// 
/// A Solana program for managing permanent encrypted file storage metadata.
/// Files are stored on Arweave via Irys, while this program maintains
/// on-chain records for access control, sharing, and verification.
#[program]
pub mod helix_storage {
    use super::*;

    /// Initialize the global storage registry.
    /// Can only be called once by the program deployer.
    /// 
    /// # Arguments
    /// * `ctx` - The context containing the registry account and authority
    /// * `base_fee_lamports` - Base fee in lamports for file registration
    pub fn initialize(ctx: Context<Initialize>, base_fee_lamports: u64) -> Result<()> {
        instructions::initialize::handler(ctx, base_fee_lamports)
    }

    /// Register a new file after successful Arweave upload.
    /// Creates an on-chain record linking the wallet to the Arweave transaction.
    /// 
    /// # Arguments
    /// * `ctx` - The context containing file record and owner accounts
    /// * `transaction_id` - The Arweave transaction ID (43 chars)
    /// * `encrypted_name` - Client-encrypted filename (optional)
    /// * `mime_type` - MIME type of the file
    /// * `size` - File size in bytes
    /// * `is_encrypted` - Whether the file content is encrypted
    pub fn register_file(
        ctx: Context<RegisterFile>,
        transaction_id: String,
        encrypted_name: Option<String>,
        mime_type: String,
        size: u64,
        is_encrypted: bool,
    ) -> Result<()> {
        instructions::register_file::handler(
            ctx,
            transaction_id,
            encrypted_name,
            mime_type,
            size,
            is_encrypted,
        )
    }

    /// Create a share link for an existing file.
    /// Allows the file owner to grant access to other wallets.
    /// 
    /// # Arguments
    /// * `ctx` - The context containing share link and file accounts
    /// * `recipient` - Optional specific wallet to grant access
    /// * `expires_at` - Optional Unix timestamp for expiration
    /// * `max_downloads` - Optional maximum download count
    /// * `encrypted_key` - Encrypted decryption key for the recipient
    pub fn create_share(
        ctx: Context<CreateShare>,
        recipient: Option<Pubkey>,
        expires_at: Option<i64>,
        max_downloads: Option<u32>,
        encrypted_key: Option<String>,
    ) -> Result<()> {
        instructions::create_share::handler(
            ctx,
            recipient,
            expires_at,
            max_downloads,
            encrypted_key,
        )
    }

    /// Revoke an existing share link.
    /// Only the original file owner can revoke shares.
    /// 
    /// # Arguments
    /// * `ctx` - The context containing share link to revoke
    pub fn revoke_share(ctx: Context<RevokeShare>) -> Result<()> {
        instructions::create_share::revoke_handler(ctx)
    }

    /// Increment download count for a share link.
    /// Called when a recipient downloads the shared file.
    /// 
    /// # Arguments
    /// * `ctx` - The context containing share link to update
    pub fn record_download(ctx: Context<RecordDownload>) -> Result<()> {
        instructions::create_share::record_download_handler(ctx)
    }

    /// Update file metadata.
    /// Only the file owner can update their file records.
    /// 
    /// # Arguments
    /// * `ctx` - The context containing file record to update
    /// * `encrypted_name` - New encrypted filename (optional)
    pub fn update_file(ctx: Context<UpdateFile>, encrypted_name: Option<String>) -> Result<()> {
        instructions::register_file::update_handler(ctx, encrypted_name)
    }

    /// Mark a file as deleted in the registry.
    /// Note: This does not delete the file from Arweave (permanent by design).
    /// 
    /// # Arguments
    /// * `ctx` - The context containing file record to mark as deleted
    pub fn delete_file(ctx: Context<DeleteFile>) -> Result<()> {
        instructions::register_file::delete_handler(ctx)
    }
}
