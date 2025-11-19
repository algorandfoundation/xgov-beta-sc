# Escrow

The Proposal Escrow is an Address controlled by the Proposal Application.

## Escrow Inflows

| FLOW                        | FROM          | TO              |         AMOUNT          | METHOD                             | CONDITION |
|:----------------------------|:--------------|:----------------|:-----------------------:|:-----------------------------------|:----------|
| Open Proposal               | xGov Treasury | Proposal Escrow |  Partial Proposal Fee   | `open_proposal` (on xGov Registry) |           |
| Deposit Proposal Commitment | Proposer      | Proposal Escrow | Proposal Locked Deposit | `open`                             |           |

## Escrow Outflows

| FLOW                       | FROM            | TO            |             AMOUNT             | METHOD     | CONDITION                           |
|:---------------------------|:----------------|:--------------|:------------------------------:|:-----------|:------------------------------------|
| Operations Funding         | Proposal Escrow | xGov Daemon   |     % of Open Proposal Fee     | `submit`   |                                     |
| Return Proposal Commitment | Proposal Escrow | Proposer      |    Proposal Locked Deposit     | `drop`     | Proposal is dropped                 |
| Return Proposal Commitment | Proposal Escrow | Proposer      |    Proposal Locked Deposit     | `scrutiny` | Proposal is rejected                |
| Return Proposal Commitment | Proposal Escrow | Proposer      |    Proposal Locked Deposit     | `finalize` | Proposal is dropped for staleness   |
| Return Proposal Commitment | Proposal Escrow | Proposer      |    Proposal Locked Deposit     | `review`   | Veto is not applied (`block=False`) |
| Slash Proposal Commitment  | Proposal Escrow | xGov Treasury |    Proposal Locked Deposit     | `review`   | Veto is applied (`block=True`)      |
| Claim Voters MBR           | Proposal Escrow | xGov Treasury |         Voters Box MBR         | `finalize` |                                     |
| Close Out Proposal         | Proposal Escrow | xGov Treasury | Metadata Box MBR + App Account | `delete`   |                                     |

## Escrow MBRs

- Proposal Application Account

- Metadata Box

- xGov Committee Voters Boxes
