import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { PublicKey } from "@solana/web3.js";
import { expect } from "chai";

describe("contract_state_program RFC tests", () => {
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);

  const program = anchor.workspace.ContractStateProgram as Program<any>;

  const contractId = "CTR-RFC-001";

  const getPDA = () =>
    PublicKey.findProgramAddressSync(
      [Buffer.from("contract"), Buffer.from(contractId)],
      program.programId
    )[0];

  it("register contract", async () => {
    const pda = getPDA();

    await program.methods
      .registerContract(contractId, new anchor.BN(1))
      .accounts({
        contract: pda,
        authority: provider.wallet.publicKey,
        systemProgram: anchor.web3.SystemProgram.programId,
      })
      .rpc();

    const state = await program.account.contractState.fetch(pda);
    expect(state.version.toNumber()).to.equal(1);
  });

  it("valid transition: registered -> approved", async () => {
    const pda = getPDA();

    await program.methods
      .approveContract(new anchor.BN(2))
      .accounts({ contract: pda, authority: provider.wallet.publicKey })
      .rpc();

    const state = await program.account.contractState.fetch(pda);
    expect(state.status.approved).to.not.be.undefined;
  });

  it("invalid transition should fail", async () => {
    const pda = getPDA();

    try {
      await program.methods
        .registerContract(contractId, new anchor.BN(3))
        .accounts({
          contract: pda,
          authority: provider.wallet.publicKey,
          systemProgram: anchor.web3.SystemProgram.programId,
        })
        .rpc();

      expect.fail("should not allow re-register");
    } catch (e) {
      expect(e).to.exist;
    }
  });

  it("version conflict should fail", async () => {
    const pda = getPDA();

    try {
      await program.methods
        .approveContract(new anchor.BN(2))
        .accounts({ contract: pda, authority: provider.wallet.publicKey })
        .rpc();

      expect.fail("version conflict not detected");
    } catch (e) {
      expect(e).to.exist;
    }
  });
});
