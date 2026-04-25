use anchor_lang::prelude::*;

declare_id!("Ctrt1111111111111111111111111111111111111");

#[program]
pub mod contract_state_program {
    use super::*;

    pub fn register_contract(ctx: Context<RegisterContract>, contract_id: String, version: u64) -> Result<()> {
        let state = &mut ctx.accounts.contract;
        require!(!state.is_initialized, ErrorCode::AlreadyInitialized);
        state.contract_id = contract_id;
        state.status = ContractStatus::Registered;
        state.version = version;
        state.authority = ctx.accounts.authority.key();
        state.is_initialized = true;
        let now = Clock::get()?.unix_timestamp;
        state.created_at = now;
        state.updated_at = now;
        Ok(())
    }

    pub fn approve_contract(ctx: Context<UpdateContract>, version: u64) -> Result<()> {
        let state = &mut ctx.accounts.contract;
        state.validate_transition(ContractStatus::Approved)?;
        state.enforce_version(version)?;
        state.status = ContractStatus::Approved;
        state.version = version;
        state.updated_at = Clock::get()?.unix_timestamp;
        Ok(())
    }

    pub fn block_contract(ctx: Context<UpdateContract>, version: u64) -> Result<()> {
        let state = &mut ctx.accounts.contract;
        state.validate_transition(ContractStatus::Blocked)?;
        state.enforce_version(version)?;
        state.status = ContractStatus::Blocked;
        state.version = version;
        state.updated_at = Clock::get()?.unix_timestamp;
        Ok(())
    }

    pub fn mark_contract_fulfilled(ctx: Context<UpdateContract>, version: u64) -> Result<()> {
        let state = &mut ctx.accounts.contract;
        state.validate_transition(ContractStatus::Fulfilled)?;
        state.enforce_version(version)?;
        state.status = ContractStatus::Fulfilled;
        state.version = version;
        state.updated_at = Clock::get()?.unix_timestamp;
        Ok(())
    }

    pub fn mark_contract_disputed(ctx: Context<UpdateContract>, version: u64) -> Result<()> {
        let state = &mut ctx.accounts.contract;
        state.validate_transition(ContractStatus::Disputed)?;
        state.enforce_version(version)?;
        state.status = ContractStatus::Disputed;
        state.version = version;
        state.updated_at = Clock::get()?.unix_timestamp;
        Ok(())
    }
}

#[account]
pub struct ContractState {
    pub contract_id: String,
    pub status: ContractStatus,
    pub version: u64,
    pub authority: Pubkey,
    pub is_initialized: bool,
    pub bump: u8,
    pub created_at: i64,
    pub updated_at: i64,
}

impl ContractState {
    pub fn validate_transition(&self, new: ContractStatus) -> Result<()> {
        match (&self.status, &new) {
            (ContractStatus::Registered, ContractStatus::UnderReview) => Ok(()),
            (ContractStatus::UnderReview, ContractStatus::Approved) => Ok(()),
            (ContractStatus::UnderReview, ContractStatus::Blocked) => Ok(()),
            (ContractStatus::Approved, ContractStatus::Fulfilled) => Ok(()),
            (ContractStatus::Approved, ContractStatus::Disputed) => Ok(()),
            (ContractStatus::Disputed, ContractStatus::Finalized) => Ok(()),
            (ContractStatus::Fulfilled, ContractStatus::Finalized) => Ok(()),
            (_, ContractStatus::Blocked) => Ok(()),
            _ => err!(ErrorCode::InvalidTransition),
        }
    }
    pub fn enforce_version(&self, incoming: u64) -> Result<()> {
        require!(incoming > self.version, ErrorCode::VersionConflict);
        Ok(())
    }
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, PartialEq, Eq)]
pub enum ContractStatus { Draft, Registered, UnderReview, Approved, Blocked, Fulfilled, Disputed, Finalized }

#[derive(Accounts)]
#[instruction(contract_id: String)]
pub struct RegisterContract<'info> {
    #[account(init, payer = authority, space = 512, seeds = [b"contract", contract_id.as_bytes()], bump)]
    pub contract: Account<'info, ContractState>,
    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct UpdateContract<'info> {
    #[account(mut, has_one = authority)]
    pub contract: Account<'info, ContractState>,
    pub authority: Signer<'info>,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Already initialized")] AlreadyInitialized,
    #[msg("Invalid state transition")] InvalidTransition,
    #[msg("Version conflict")] VersionConflict,
    #[msg("Invalid authority")] InvalidAuthority,
}
