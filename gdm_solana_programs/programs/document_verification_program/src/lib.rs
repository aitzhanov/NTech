use anchor_lang::prelude::*;

declare_id!("CEDTERJ724BMEcUauM4GdFKH3P11fLRqvLULUoVoC5g9");

#[program]
pub mod document_verification_program {
    use super::*;

    pub fn register_document_hash(ctx: Context<RegisterDocument>, document_id: String, parent_contract_id: String, hash: String, version: u64) -> Result<()> {
        let doc = &mut ctx.accounts.document;
        require!(!doc.is_initialized, ErrorCode::AlreadyInitialized);
        doc.document_id = document_id;
        doc.parent_contract_id = parent_contract_id;
        doc.document_hash = hash;
        doc.version = version;
        doc.status = DocumentStatus::HashRegistered;
        doc.authority = ctx.accounts.authority.key();
        doc.is_initialized = true;
        let now = Clock::get()?.unix_timestamp;
        doc.created_at = now;
        doc.updated_at = now;
        Ok(())
    }

    pub fn confirm_document(ctx: Context<UpdateDocument>, version: u64) -> Result<()> {
        let doc = &mut ctx.accounts.document;
        doc.validate_transition(DocumentStatus::Validated)?;
        doc.enforce_version(version)?;
        doc.status = DocumentStatus::Validated;
        doc.version = version;
        doc.updated_at = Clock::get()?.unix_timestamp;
        Ok(())
    }

    pub fn reject_document(ctx: Context<UpdateDocument>, version: u64) -> Result<()> {
        let doc = &mut ctx.accounts.document;
        doc.validate_transition(DocumentStatus::Rejected)?;
        doc.enforce_version(version)?;
        doc.status = DocumentStatus::Rejected;
        doc.version = version;
        doc.updated_at = Clock::get()?.unix_timestamp;
        Ok(())
    }

    pub fn mark_document_mismatch(ctx: Context<UpdateDocument>, version: u64) -> Result<()> {
        let doc = &mut ctx.accounts.document;
        doc.validate_transition(DocumentStatus::MismatchDetected)?;
        doc.enforce_version(version)?;
        doc.status = DocumentStatus::MismatchDetected;
        doc.version = version;
        doc.updated_at = Clock::get()?.unix_timestamp;
        Ok(())
    }

    pub fn supersede_document(ctx: Context<UpdateDocument>, version: u64) -> Result<()> {
        let doc = &mut ctx.accounts.document;
        doc.validate_transition(DocumentStatus::Superseded)?;
        doc.enforce_version(version)?;
        doc.status = DocumentStatus::Superseded;
        doc.version = version;
        doc.updated_at = Clock::get()?.unix_timestamp;
        Ok(())
    }
}

#[account]
pub struct DocumentState {
    pub document_id: String,
    pub parent_contract_id: String,
    pub document_hash: String,
    pub version: u64,
    pub status: DocumentStatus,
    pub authority: Pubkey,
    pub is_initialized: bool,
    pub bump: u8,
    pub created_at: i64,
    pub updated_at: i64,
}

impl DocumentState {
    pub fn validate_transition(&self, new: DocumentStatus) -> Result<()> {
        match (&self.status, &new) {
            (DocumentStatus::HashRegistered, DocumentStatus::UnderVerification) => Ok(()),
            (DocumentStatus::UnderVerification, DocumentStatus::Validated) => Ok(()),
            (DocumentStatus::UnderVerification, DocumentStatus::Rejected) => Ok(()),
            (DocumentStatus::UnderVerification, DocumentStatus::MismatchDetected) => Ok(()),
            (DocumentStatus::Validated, DocumentStatus::Finalized) => Ok(()),
            (DocumentStatus::MismatchDetected, DocumentStatus::Superseded) => Ok(()),
            (DocumentStatus::Rejected, DocumentStatus::Superseded) => Ok(()),
            _ => err!(ErrorCode::InvalidTransition),
        }
    }
    pub fn enforce_version(&self, incoming: u64) -> Result<()> {
        require!(incoming > self.version, ErrorCode::VersionConflict);
        Ok(())
    }
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, PartialEq, Eq)]
pub enum DocumentStatus { Created, HashRegistered, UnderVerification, Validated, MismatchDetected, Rejected, Superseded, Finalized }

#[derive(Accounts)]
#[instruction(document_id: String, version: u64)]
pub struct RegisterDocument<'info> {
    #[account(init, payer = authority, space = 600, seeds = [b"document", document_id.as_bytes(), &version.to_le_bytes()], bump)]
    pub document: Account<'info, DocumentState>,
    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct UpdateDocument<'info> {
    #[account(mut, has_one = authority)]
    pub document: Account<'info, DocumentState>,
    pub authority: Signer<'info>,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Already initialized")] AlreadyInitialized,
    #[msg("Invalid state transition")] InvalidTransition,
    #[msg("Version conflict")] VersionConflict,
    #[msg("Invalid authority")] InvalidAuthority,
}
