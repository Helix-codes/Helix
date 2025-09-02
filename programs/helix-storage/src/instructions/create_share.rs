use anchor_lang::prelude::*;

use crate::error::{validate_optional_string_length, HelixError};
use crate::state::{
    FileRecord, ShareCreated, ShareLink, ShareRevoked, StorageRegistry,
    FILE_SEED, MAX_ENCRYPTED_KEY_LEN, REGISTRY_SEED, SHARE_SEED,
};

/// Accounts required for creating a share link
#[derive(Accounts)]
pub struct CreateShare<'info> {
    /// The storage registry (for stats)
    #[account(
        mut,
        seeds = [REGISTRY_SEED],
        bump = registry.bump
    )]
    pub registry: Account<'info, StorageRegistry>,

    /// The file being shared
    #[account(
        mut,
        seeds = [FILE_SEED, file_record.transaction_id.as_bytes()],
        bump = file_record.bump,
        has_one = owner
    )]
    pub file_record: Account<'info, FileRecord>,

    /// The share link to create (PDA)
    #[account(
        init,
        payer = owner,
        space = ShareLink::LEN,
        seeds = [
            SHARE_SEED,
            file_record.key().as_ref(),
            &registry.total_shares.to_le_bytes()
        ],
        bump
    )]
    pub share_link: Account<'info, ShareLink>,

    /// The file owner (payer)
    #[account(mut)]
    pub owner: Signer<'info>,

    /// System program for account creation
    pub system_program: Program<'info, System>,
}

/// Handler for the create_share instruction
/// 
/// Creates a new share link for a file, allowing access to specified recipients.
/// 
/// # Arguments
/// * `ctx` - The CreateShare context
/// * `recipient` - Optional specific wallet that can access (None = public)
/// * `expires_at` - Optional Unix timestamp for expiration
/// * `max_downloads` - Optional maximum download count
/// * `encrypted_key` - Encrypted decryption key for the recipient
/// 
/// # Returns
/// * `Result<()>` - Success or error
pub fn handler(
    ctx: Context<CreateShare>,
    recipient: Option<Pubkey>,
    expires_at: Option<i64>,
    max_downloads: Option<u32>,
    encrypted_key: Option<String>,
) -> Result<()> {
    let registry = &mut ctx.accounts.registry;
    let file_record = &mut ctx.accounts.file_record;
    let share_link = &mut ctx.accounts.share_link;
    let clock = Clock::get()?;

    // Validate file is not deleted
    require!(!file_record.is_deleted, HelixError::CannotShareDeletedFile);

    // Validate expiration if provided
    if let Some(exp) = expires_at {
        require!(exp > clock.unix_timestamp, HelixError::ExpirationInPast);
    }

    // Validate max downloads if provided
    if let Some(max) = max_downloads {
        require!(max > 0, HelixError::InvalidMaxDownloads);
    }

    // Validate encrypted key length
    validate_optional_string_length(
        &encrypted_key,
        MAX_ENCRYPTED_KEY_LEN,
        HelixError::EncryptedKeyTooLong,
    )?;

    // Initialize share link
    share_link.file = file_record.key();
    share_link.owner = ctx.accounts.owner.key();
    share_link.recipient = recipient;
    share_link.encrypted_key = encrypted_key;
    share_link.expires_at = expires_at;
    share_link.max_downloads = max_downloads;
    share_link.download_count = 0;
    share_link.is_revoked = false;
    share_link.created_at = clock.unix_timestamp;
    share_link.bump = ctx.bumps.share_link;
    share_link._reserved = [0u8; 16];

    // Update file record share count
    file_record.share_count = file_record
        .share_count
        .checked_add(1)
        .ok_or(HelixError::ArithmeticOverflow)?;

    // Update registry stats
    registry.total_shares = registry
        .total_shares
        .checked_add(1)
        .ok_or(HelixError::ArithmeticOverflow)?;

    // Emit event
    emit!(ShareCreated {
        file: file_record.key(),
        owner: share_link.owner,
        recipient,
        expires_at,
        timestamp: clock.unix_timestamp,
    });

    msg!(
        "Share link created for file {} by {}",
        file_record.transaction_id,
        share_link.owner
    );

    Ok(())
}

/// Accounts required for revoking a share link
#[derive(Accounts)]
pub struct RevokeShare<'info> {
    /// The storage registry (for stats)
    #[account(
        mut,
        seeds = [REGISTRY_SEED],
        bump = registry.bump
    )]
    pub registry: Account<'info, StorageRegistry>,

    /// The file record
    #[account(
        mut,
        seeds = [FILE_SEED, file_record.transaction_id.as_bytes()],
        bump = file_record.bump
    )]
    pub file_record: Account<'info, FileRecord>,

    /// The share link to revoke
    #[account(
        mut,
        constraint = share_link.owner == owner.key() @ HelixError::UnauthorizedOwner,
        constraint = share_link.file == file_record.key() @ HelixError::InvalidShareLink
    )]
    pub share_link: Account<'info, ShareLink>,

    /// The share owner
    pub owner: Signer<'info>,
}

/// Handler for revoking a share link
pub fn revoke_handler(ctx: Context<RevokeShare>) -> Result<()> {
    let registry = &mut ctx.accounts.registry;
    let file_record = &mut ctx.accounts.file_record;
    let share_link = &mut ctx.accounts.share_link;
    let clock = Clock::get()?;

    // Validate share is not already revoked
    require!(!share_link.is_revoked, HelixError::ShareRevoked);

    // Mark as revoked
    share_link.is_revoked = true;

    // Update file record share count
    file_record.share_count = file_record.share_count.saturating_sub(1);

    // Update registry stats
    registry.total_shares = registry.total_shares.saturating_sub(1);

    // Emit event
    emit!(ShareRevoked {
        share: ctx.accounts.share_link.key(),
        owner: share_link.owner,
        timestamp: clock.unix_timestamp,
    });

    msg!(
        "Share link revoked: {} by {}",
        ctx.accounts.share_link.key(),
        share_link.owner
    );

    Ok(())
}

/// Accounts required for recording a download
#[derive(Accounts)]
pub struct RecordDownload<'info> {
    /// The share link being used
    #[account(mut)]
    pub share_link: Account<'info, ShareLink>,

    /// The wallet downloading (must match recipient if specified)
    pub downloader: Signer<'info>,
}

/// Handler for recording a download
pub fn record_download_handler(ctx: Context<RecordDownload>) -> Result<()> {
    let share_link = &mut ctx.accounts.share_link;
    let clock = Clock::get()?;

    // Validate share link is valid
    require!(
        share_link.is_valid(clock.unix_timestamp),
        HelixError::InvalidShareLink
    );

    // Validate access if recipient is specified
    require!(
        share_link.can_access(&ctx.accounts.downloader.key(), clock.unix_timestamp),
        HelixError::ShareAccessDenied
    );

    // Record the download
    let still_valid = share_link.record_download();
    require!(still_valid, HelixError::MaxDownloadsReached);

    msg!(
        "Download recorded for share link. Count: {}",
        share_link.download_count
    );

    Ok(())
}

/// Accounts for validating share access (read-only)
#[derive(Accounts)]
pub struct ValidateAccess<'info> {
    /// The share link to validate
    pub share_link: Account<'info, ShareLink>,

    /// The file record
    #[account(
        seeds = [FILE_SEED, file_record.transaction_id.as_bytes()],
        bump = file_record.bump
    )]
    pub file_record: Account<'info, FileRecord>,
}

/// Check if a wallet can access a shared file
pub fn validate_access(ctx: &Context<ValidateAccess>, wallet: &Pubkey) -> Result<bool> {
    let share_link = &ctx.accounts.share_link;
    let file_record = &ctx.accounts.file_record;
    let clock = Clock::get()?;

    // Check file is not deleted
    if file_record.is_deleted {
        return Ok(false);
    }

    // Check share link validity
    Ok(share_link.can_access(wallet, clock.unix_timestamp))
}
