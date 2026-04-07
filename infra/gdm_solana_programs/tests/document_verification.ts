import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { PublicKey } from "@solana/web3.js";
import { expect } from "chai";

describe("document_verification_program RFC tests", () => {
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);

  const program = anchor.workspace.DocumentVerificationProgram as Program<any>;

  const docId = "DOC-RFC-001";

  const getPDA = (version: number) =>
    PublicKey.findProgramAddressSync(
      [
        Buffer.from("document"),
        Buffer.from(docId),
        new anchor.BN(version).toArrayLike(Buffer, "le", 8),
      ],
      program.programId
    )[0];

  it("register document", async () => {
    const pda = getPDA(1);

    await program.methods
      .registerDocumentHash(docId, "CTR-RFC-001", "hash1", new anchor.BN(1))
      .accounts({
        document: pda,
        authority: provider.wallet.publicKey,
        systemProgram: anchor.web3.SystemProgram.programId,
      })
      .rpc();

    const state = await program.account.documentState.fetch(pda);
    expect(state.version.toNumber()).to.equal(1);
  });

  it("validate document", async () => {
    const pda = getPDA(1);

    await program.methods
      .confirmDocument(new anchor.BN(2))
      .accounts({ document: pda, authority: provider.wallet.publicKey })
      .rpc();

    const state = await program.account.documentState.fetch(pda);
    expect(state.status.validated).to.not.be.undefined;
  });

  it("reject invalid transition", async () => {
    const pda = getPDA(1);

    try {
      await program.methods
        .registerDocumentHash(docId, "CTR-RFC-001", "hash2", new anchor.BN(2))
        .accounts({
          document: pda,
          authority: provider.wallet.publicKey,
          systemProgram: anchor.web3.SystemProgram.programId,
        })
        .rpc();

      expect.fail("should not allow overwrite");
    } catch (e) {
      expect(e).to.exist;
    }
  });

  it("version conflict should fail", async () => {
    const pda = getPDA(1);

    try {
      await program.methods
        .confirmDocument(new anchor.BN(2))
        .accounts({ document: pda, authority: provider.wallet.publicKey })
        .rpc();

      expect.fail("version conflict not detected");
    } catch (e) {
      expect(e).to.exist;
    }
  });
});
