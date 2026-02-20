# Treasury

The xGov Treasury is an Algorand Address controlled by the xGov Registry.

## Treasury Inflows

| FLOW                        | FROM            | TO            |             AMOUNT             | METHOD                     | CONDITION                      |
|:----------------------------|:----------------|:--------------|:------------------------------:|:---------------------------|:-------------------------------|
| Deposit Proposals Funds     | Anyone          | xGov Treasury |              Any               | `deposit_funds`            |                                |
| xGov Subscription           | Anyone          | xGov Treasury |            xGov Fee            | `subscribe_xgov`           |                                |
| xGov Subscription Request   | Anyone          | xGov Treasury |            xGov Fee            | `request_subscribe_xgov`   |                                |
| xGov Unsubscription Request | Anyone          | xGov Treasury |            xGov Fee            | `request_unsubscribe_xgov` |                                |
| Proposer Subscription       | Anyone          | xGov Treasury |          Proposer Fee          | `subscribe_proposer`       |                                |
| Open Proposal               | Anyone          | xGov Treasury |       Open Proposal Fee        | `open_proposal`            |                                |
| Slash Proposal Commitment   | Proposal Escrow | xGov Treasury |    Proposal Locked Deposit     | `review` (on Proposal)     | Veto is applied (`block=True`) |
| Claim Voters MBR            | Proposal Escrow | xGov Treasury |         Voters Box MBR         | `finalize_proposal`        |                                |
| Close Out Proposal          | Proposal Escrow | xGov Treasury | Metadata Box MBR + App Account | `delete` (on Proposal)     |                                |

## Treasury Outflows

| FLOW                     | FROM          | TO              |                       AMOUNT                       | METHOD                     | CONDITION            |
|:-------------------------|:--------------|:----------------|:--------------------------------------------------:|:---------------------------|:---------------------|
| Open Proposal            | xGov Treasury | Proposal Escrow |                Partial Proposal Fee                | `open_proposal`            |                      |
| Pay Proposal             | xGov Treasury | Proposer        |                  Requested Amount                  | `pay_grant_proposal`       | Proposal is approved |
| Withdraw Proposal Funds  | xGov Treasury | xGov Manager    |          Up to available Proposals Funds           | `withdraw_funds`           |                      |
| Withdraw Available Funds | xGov Treasury | xGov Payor      | Available funds, excluding MBR and Proposals Funds | `withdraw_available_funds` |                      |

{{#include ../_include/styles.md:note}}
> Partial Open Proposal Fees are equal to the Open Proposal Fee discounted by the
> Proposal Application MBR.

{{#include ../_include/styles.md:note}}
> The `get_available_funds` getter returns the available funds in the Treasury,
> excluding MBRs and Proposals Funds.

## Treasury MBRs

- Treasury Application Account;

- xGov Boxes;

- Proposer Boxes;

- Created Proposal Applications.
