# Treasury

The xGov Treasury is an Algorand Address controlled by the xGov Registry.

## Treasury Inflows

- Governance funds from the Algorand Foundation;

- xGov Fee deposits from xGovs on subscription/request;

- Proposer Fees from Proposers on subscription;

- Open Proposal Fees from Proposers on proposal submission;

- Proposal Commitment from Proposal Escrows if a veto is applied to the Proposal.

## Treasury Outflows

- Partial Open Proposal Fees to Proposal Escrow on Proposal submission;

- Proposal Funds to the Proposer on proposal payment;

- Algorand Foundation withdrawals of outstanding funds.

## Treasury MBRs

- Treasury Application Account;

- xGov Boxes;

- Proposer Boxes;

- Created Proposal Applications.

{{#include ../_include/styles.md:note}}
> Partial Open Proposal Fees are equal to the Open Proposal Fee discounted by the
> Proposal Application MBR.
