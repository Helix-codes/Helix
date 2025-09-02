use anchor_lang::prelude::*;

use crate::error::{
    validate_mime_type, validate_optional_string_length, validate_string_length,
    validate_transaction_id, HelixError,
};
use crate::state::{
    FileDeleted, FileRecord, FileRegistered, StorageRegistry, FILE_SEED,
    MAX_ENCRYPTED_NAME_LEN, MAX_MIME_TYPE_LEN, MAX_TRANSACTION_ID_LEN, REGISTRY_SEED,
};

/// Accounts required for registering a new file
#[derive(Accounts)]
#[instruction(transaction_id: String)]
pub struct RegisterFile<'info> {
    /// The storage registry (for validation and stats)
    #[account(
        mut,
        seeds = [REGISTRY_SEED],
        bump = registry.bump
    )]
    pub registry: Account<'info, StorageRegistry>,

    /// The file record to create (PDA derived from tx_id)
    #[account(
        init,
        payer = owner,
        space = FileRecord::LEN,
        seeds = [FILE_SEED, transaction_id.as_bytes()],
        bump
    )]
    pub file_record: Account<'info, FileRecord>,

    /// The file owner (payer)
    #[account(mut)]
    pub owner: Signer<'info>,

    /// System program for account creation
    pub system_program: Program<'info, System>,
}

/// Handler for the register_file instruction
/// 
/// Creates a new file record linking the owner's wallet to an Arweave transaction.
/// This should be called after successfully uploading a file to Arweave via Irys.
/// 
/// # Arguments
/// * `ctx` - The RegisterFile context
/// * `transaction_id` - The Arweave transaction ID (43 chars)
/// * `encrypted_name` - Optional client-encrypted filename
/// * `mime_type` - The file's MIME type
/// * `size` - File size in bytes
/// * `is_encrypted` - Whether the file content is encrypted
/// 
/// # Returns
/// * `Result<()>` - Success or error
pub fn handler(
    ctx: Context<RegisterFile>,
    transaction_id: String,
    encrypted_name: Option<String>,
    mime_type: String,
    size: u64,
    is_encrypted: bool,
) -> Result<()> {
    let registry = &mut ctx.accounts.registry;
    let file_record = &mut ctx.accounts.file_record;
    let clock = Clock::get()?;

    // Validate registry is not paused
    require!(!registry.is_paused, HelixError::RegistryPaused);

    // Validate inputs
    validate_string_length(&transaction_id, MAX_TRANSACTION_ID_LEN, HelixError::TransactionIdTooLong)?;
    validate_transaction_id(&transaction_id)?;
    validate_optional_string_length(&encrypted_name, MAX_ENCRYPTED_NAME_LEN, HelixError::EncryptedNameTooLong)?;
    validate_string_length(&mime_type, MAX_MIME_TYPE_LEN, HelixError::MimeTypeTooLong)?;
    validate_mime_type(&mime_type)?;
    require!(size > 0, HelixError::InvalidFileSize);

    // Initialize file record
    file_record.owner = ctx.accounts.owner.key();
    file_record.transaction_id = transaction_id.clone();
    file_record.encrypted_name = encrypted_name;
    file_record.mime_type = mime_type;
    file_record.size = size;
    file_record.is_encrypted = is_encrypted;
    file_record.is_deleted = false;
    file_record.created_at = clock.unix_timestamp;
    file_record.updated_at = clock.unix_timestamp;
    file_record.share_count = 0;
    file_record.bump = ctx.bumps.file_record;
    file_record._reserved = [0u8; 32];

    // Update registry stats
    registry.total_files = registry
        .total_files
        .checked_add(1)
        .ok_or(HelixError::ArithmeticOverflow)?;

    // Emit event
    emit!(FileRegistered {
        owner: file_record.owner,
        transaction_id,
        size,
        is_encrypted,
        timestamp: clock.unix_timestamp,
    });

    msg!(
        "File registered: {} by {}",
        file_record.transaction_id,
        file_record.owner
    );

    Ok(())
}

/// Accounts required for updating a file record
#[derive(Accounts)]
pub struct UpdateFile<'info> {
    /// The file record to update
    #[account(
        mut,
        seeds = [FILE_SEED, file_record.transaction_id.as_bytes()],
        bump = file_record.bump,
        has_one = owner
    )]
    pub file_record: Account<'info, FileRecord>,

    /// The file owner
    pub owner: Signer<'info>,
}

/// Handler for updating file metadata
pub fn update_handler(ctx: Context<UpdateFile>, encrypted_name: Option<String>) -> Result<()> {
    let file_record = &mut ctx.accounts.file_record;
    let clock = Clock::get()?;

    // Validate file is not deleted
    require!(!file_record.is_deleted, HelixError::FileAlreadyDeleted);

    // Validate encrypted name length
    validate_optional_string_length(
        &encrypted_name,
        MAX_ENCRYPTED_NAME_LEN,
        HelixError::EncryptedNameTooLong,
    )?;

    // Update fields
    file_record.encrypted_name = encrypted_name;
    file_record.updated_at = clock.unix_timestamp;

    msg!(
        "File updated: {} at {}",
        file_record.transaction_id,
        clock.unix_timestamp
    );

    Ok(())
}

/// Accounts required for deleting a file record
#[derive(Accounts)]
pub struct DeleteFile<'info> {
    /// The storage registry (for stats)
    #[account(
        mut,
        seeds = [REGISTRY_SEED],
        bump = registry.bump
    )]
    pub registry: Account<'info, StorageRegistry>,

    /// The file record to mark as deleted
    #[account(
        mut,
        seeds = [FILE_SEED, file_record.transaction_id.as_bytes()],
        bump = file_record.bump,
        has_one = owner
    )]
    pub file_record: Account<'info, FileRecord>,

    /// The file owner
    pub owner: Signer<'info>,
}

/// Handler for marking a file as deleted
/// 
/// Note: This only marks the file as deleted in the on-chain registry.
/// The actual file content on Arweave remains permanent by design.
pub fn delete_handler(ctx: Context<DeleteFile>) -> Result<()> {
    let registry = &mut ctx.accounts.registry;
    let file_record = &mut ctx.accounts.file_record;
    let clock = Clock::get()?;

    // Validate file is not already deleted
    require!(!file_record.is_deleted, HelixError::FileAlreadyDeleted);

    // Mark as deleted
    file_record.is_deleted = true;
    file_record.updated_at = clock.unix_timestamp;

    // Update registry stats (decrement if tracking active files)
    registry.total_files = registry.total_files.saturating_sub(1);

    // Emit event
    emit!(FileDeleted {
        file: ctx.accounts.file_record.key(),
        owner: file_record.owner,
        timestamp: clock.unix_timestamp,
    });

    msg!(
        "File marked as deleted: {} by {}",
        file_record.transaction_id,
        file_record.owner
    );

    Ok(())
}

/// Accounts for querying file info (read-only)
#[derive(Accounts)]
#[instruction(transaction_id: String)]
pub struct GetFile<'info> {
    /// The file record to query
    #[account(
        seeds = [FILE_SEED, transaction_id.as_bytes()],
        bump = file_record.bump
    )]
    pub file_record: Account<'info, FileRecord>,
}
