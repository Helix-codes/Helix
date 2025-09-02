use anchor_lang::prelude::*;

use crate::state::{StorageRegistry, REGISTRY_SEED};

/// Accounts required for initializing the storage registry
#[derive(Accounts)]
pub struct Initialize<'info> {
    /// The storage registry account to initialize (PDA)
    #[account(
        init,
        payer = authority,
        space = StorageRegistry::LEN,
        seeds = [REGISTRY_SEED],
        bump
    )]
    pub registry: Account<'info, StorageRegistry>,

    /// The authority who will manage the registry
    #[account(mut)]
    pub authority: Signer<'info>,

    /// System program for account creation
    pub system_program: Program<'info, System>,
}

/// Handler for the initialize instruction
/// 
/// Creates the global storage registry with initial configuration.
/// This should only be called once after program deployment.
/// 
/// # Arguments
/// * `ctx` - The Initialize context
/// * `base_fee_lamports` - Initial base fee for file registration
/// 
/// # Returns
/// * `Result<()>` - Success or error
pub fn handler(ctx: Context<Initialize>, base_fee_lamports: u64) -> Result<()> {
    let registry = &mut ctx.accounts.registry;
    let clock = Clock::get()?;

    registry.authority = ctx.accounts.authority.key();
    registry.base_fee_lamports = base_fee_lamports;
    registry.total_files = 0;
    registry.total_shares = 0;
    registry.is_paused = false;
    registry.bump = ctx.bumps.registry;
    registry._reserved = [0u8; 64];

    msg!(
        "Helix Storage Registry initialized at {} by {}",
        clock.unix_timestamp,
        registry.authority
    );

    Ok(())
}

/// Accounts required for updating registry configuration
#[derive(Accounts)]
pub struct UpdateRegistry<'info> {
    /// The storage registry account
    #[account(
        mut,
        seeds = [REGISTRY_SEED],
        bump = registry.bump,
        has_one = authority
    )]
    pub registry: Account<'info, StorageRegistry>,

    /// The authority updating the registry
    pub authority: Signer<'info>,
}

/// Update the base fee for file registration
pub fn update_fee_handler(ctx: Context<UpdateRegistry>, new_fee: u64) -> Result<()> {
    let registry = &mut ctx.accounts.registry;
    let old_fee = registry.base_fee_lamports;
    registry.base_fee_lamports = new_fee;

    msg!(
        "Base fee updated from {} to {} lamports",
        old_fee,
        new_fee
    );

    Ok(())
}

/// Pause or unpause the registry
pub fn set_paused_handler(ctx: Context<UpdateRegistry>, paused: bool) -> Result<()> {
    let registry = &mut ctx.accounts.registry;
    registry.is_paused = paused;

    msg!(
        "Registry paused status set to: {}",
        paused
    );

    Ok(())
}

/// Transfer authority to a new wallet
pub fn transfer_authority_handler(
    ctx: Context<UpdateRegistry>,
    new_authority: Pubkey,
) -> Result<()> {
    let registry = &mut ctx.accounts.registry;
    let old_authority = registry.authority;
    registry.authority = new_authority;

    msg!(
        "Authority transferred from {} to {}",
        old_authority,
        new_authority
    );

    Ok(())
}
