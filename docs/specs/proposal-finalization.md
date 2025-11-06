# Finalization

## Payment

The xGov Payor **MAY** pay a Reviewed Proposal and promote it to Funded.

If the Proposal is Funded:

- The requested amount **MUST BE** transferred from the xGov Treasury to its Proposer.

## Finalize

The xGov Daemon **SHOULD** finalize:

- Empty and Draft Proposals, after a stale period,

- Funded, Rejected, or Blocked Proposals.

If a Draft Proposal is finalized, the Commitment Lock **MUST** be returned to the
Proposer.

The xGov Daemon **SHALL** delete the Voter Boxes of Funded, Rejected, or Blocked
Proposals.

All Voter Box **MUST** be deleted before finalizing the Proposal.

Outstanding balance of the Proposal Escrow **MUST** be returned to the xGov Treasury.

## Delete

The xGov Manager **MAY** delete Finalized Proposals.

The Proposal Metadata **MUST** be deleted before deletion (Empty Proposals are an
exception).

Proposal Escrow **MUST** be closed to the xGov Treasury before deletion.
