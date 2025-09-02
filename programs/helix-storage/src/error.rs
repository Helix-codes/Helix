use anchor_lang::prelude::*;

/// Custom errors for the Helix Storage program
#[error_code]
pub enum HelixError {
    /// The transaction ID exceeds maximum allowed length
    #[msg("Transaction ID exceeds maximum length of 43 characters")]
    TransactionIdTooLong,

    /// The encrypted name exceeds maximum allowed length
    #[msg("Encrypted name exceeds maximum length of 256 characters")]
    EncryptedNameTooLong,

    /// The MIME type exceeds maximum allowed length
    #[msg("MIME type exceeds maximum length of 128 characters")]
    MimeTypeTooLong,

    /// The encrypted key exceeds maximum allowed length
    #[msg("Encrypted key exceeds maximum length of 512 characters")]
    EncryptedKeyTooLong,

    /// The file size must be greater than zero
    #[msg("File size must be greater than zero")]
    InvalidFileSize,

    /// The transaction ID format is invalid
    #[msg("Invalid transaction ID format")]
    InvalidTransactionId,

    /// The caller is not the owner of this file
    #[msg("Unauthorized: caller is not the file owner")]
    UnauthorizedOwner,

    /// The caller is not the program authority
    #[msg("Unauthorized: caller is not the program authority")]
    UnauthorizedAuthority,

    /// The file has already been marked as deleted
    #[msg("File has already been deleted")]
    FileAlreadyDeleted,

    /// The file record was not found
    #[msg("File record not found")]
    FileNotFound,

    /// The share link has expired
    #[msg("Share link has expired")]
    ShareExpired,

    /// The share link has reached maximum downloads
    #[msg("Share link has reached maximum downloads")]
    MaxDownloadsReached,

    /// The share link has been revoked
    #[msg("Share link has been revoked")]
    ShareRevoked,

    /// The share link does not permit this wallet
    #[msg("Share link does not permit access from this wallet")]
    ShareAccessDenied,

    /// The share link is not valid
    #[msg("Share link is not valid")]
    InvalidShareLink,

    /// The expiration timestamp is in the past
    #[msg("Expiration timestamp must be in the future")]
    ExpirationInPast,

    /// Max downloads must be greater than zero
    #[msg("Max downloads must be greater than zero")]
    InvalidMaxDownloads,

    /// The registry has been paused
    #[msg("Registry is paused, new registrations are not allowed")]
    RegistryPaused,

    /// A file with this transaction ID already exists
    #[msg("A file with this transaction ID already exists")]
    DuplicateTransactionId,

    /// Arithmetic overflow occurred
    #[msg("Arithmetic overflow")]
    ArithmeticOverflow,

    /// The share link already exists
    #[msg("A share link with these parameters already exists")]
    DuplicateShareLink,

    /// Cannot share a deleted file
    #[msg("Cannot create share link for a deleted file")]
    CannotShareDeletedFile,

    /// Invalid MIME type format
    #[msg("Invalid MIME type format")]
    InvalidMimeType,
}

/// Validate Arweave transaction ID format
/// Transaction IDs are 43 characters, base64url encoded
pub fn validate_transaction_id(tx_id: &str) -> Result<()> {
    if tx_id.len() != 43 {
        return Err(HelixError::InvalidTransactionId.into());
    }

    // Check for valid base64url characters
    for c in tx_id.chars() {
        if !c.is_ascii_alphanumeric() && c != '-' && c != '_' {
            return Err(HelixError::InvalidTransactionId.into());
        }
    }

    Ok(())
}

/// Validate MIME type format
/// Basic validation for "type/subtype" format
pub fn validate_mime_type(mime: &str) -> Result<()> {
    if mime.is_empty() || !mime.contains('/') {
        return Err(HelixError::InvalidMimeType.into());
    }

    let parts: Vec<&str> = mime.split('/').collect();
    if parts.len() != 2 || parts[0].is_empty() || parts[1].is_empty() {
        return Err(HelixError::InvalidMimeType.into());
    }

    Ok(())
}

/// Validate string length against maximum
pub fn validate_string_length(s: &str, max_len: usize, error: HelixError) -> Result<()> {
    if s.len() > max_len {
        return Err(error.into());
    }
    Ok(())
}

/// Validate optional string length against maximum
pub fn validate_optional_string_length(
    s: &Option<String>,
    max_len: usize,
    error: HelixError,
) -> Result<()> {
    if let Some(val) = s {
        validate_string_length(val, max_len, error)?;
    }
    Ok(())
}
