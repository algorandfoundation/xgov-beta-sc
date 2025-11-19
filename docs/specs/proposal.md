# Proposal

A Proposal is a funding request from the xGov Treasury, which is approved or rejected
by the xGov Committee vote and reviewed by the xGov Council.

A Proposal consists of:

- Proposal Application, with **REQUIRED** data;

- Proposal metadata.

The Proposal Application is created and funded by the xGov Registry App (see [Creation
section](./proposal-creation.md)) through the Open Proposal Fee.

## Lifecycle

The Proposal life cycle has four phases:

1. [Creation](./proposal-creation.md);

2. [Discussion](./proposal-submission.md#discussion) & [Submission](./proposal-submission.md#submission);

3. [Vote](./proposal-vote.md) & [Review](./proposal-vote.md#review);

4. [Finalization](./proposal-finalization.md).

## Funding Types

The Proposals have two different _funding types_:

1. **Retroactive**

   - Claim: _“I have done X, which has benefited the Algorand ecosystem because
   of Y metrics, I would like to receive Z as compensation for the work”_.

   - Positive outcome: funding is immediately disbursed if the Proposal is approved
   by the xGov Committee vote, and the xGov Council does not apply a veto according
   to the terms and conditions.

2. **Proactive** (NOT AVAILABLE YET)

   - Claim: _“I want to do X, it has the potential Y for the Algorand ecosystem,
   I would like to receive Z staggered behind these milestones”_.

   - Positive outcome: funding will be disbursed if the Proposal is approved by the
   xGov Committee vote, after milestone reviews from the xGov Council, and if the
   xGov Council does not apply a veto according to terms and conditions.

## Funding Sizes

Proposals have different _funding sizes_ based on the requested funding amount.

The Proposal’s _requested amount_ (\\( A \\)) **MUST** be bounded as follows:

|                                |               Small                |               Medium                |                Large                |
|:-------------------------------|:----------------------------------:|:-----------------------------------:|:-----------------------------------:|
| Requested Amount               |  \\( A_\min ≤ A < A_{S,\max} \\)   | \\( A_{S,\max} ≤ A < A_{M,\max} \\) | \\( A_{M,\max} ≤ A ≤ A_{L,\max} \\) |

The _funding size_ defines the timing of the Proposal lifecycle.

|                                |              Small              |               Medium                |                Large                |
|:-------------------------------|:-------------------------------:|:-----------------------------------:|:-----------------------------------:|
| Discussion time                |           \\( D_S \\)           |             \\( D_M \\)             |             \\( D_L \\)             |
| Voting time (after discussion) |           \\( V_S \\)           |             \\( V_M \\)             |             \\( V_L \\)             |

The _requested amount_ defines voting quorums of the Proposal as follows:

- \\( Q(A) \\, Democratic Quorum (1 xGov, 1 Vote)

$$
Q(A) = Q_\min + \frac{\Delta Q}{\Delta A} \times (A - A_\min)
$$

- \\( Q_w(A) \\, Weighted Quorum

$$
Q_w(A) = Q_{w,\min} + \frac{\Delta Q_w}{\Delta A} \times (A - A_\min)
$$

Where:

- \\( \Delta Q = Q_\max - Q_\min \\)
- \\( \Delta Q_w = Q_{w,\max} - Q_{w,\min} \\)
- \\( \Delta A = A_{L,\max} - A_\min \\)

{{#include ../_include/styles.md:note}}
> Refer to the [Proposal implementation configuration](../implementation/configuration.md)
> for the parameters’ value.

## Metadata

The Proposal Metadata byte length **MUST NOT** exceed 30 kB.

The Proposal Metadata is stored in a Box on the Proposal Application, called _Metadata
Box_.

The Proposal Metadata Box ID is equal to `metadata`.

The Proposal Metadata Box body has no ABI schema (raw bytes).

## Finite-State Machine

A Proposal **SHALL** be in one of the following enumerated statuses:

| Status      |  Enum  | Description                                                                                                                                                                          |
|:------------|:------:|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `EMPTY`     |  `0`   | The xGov Registry creates an empty proposal, the Proposer **SHOULD** open a draft (or it **SHOULD** be finalized for staleness)                                                      |
| `DRAFT`     |  `10`  | The Proposer **MAY** submit (with updated metadata) or drop the draft (or it **SHOULD** be finalized for staleness)                                                                  |
| `SUBMITTED` |  `20`  | The xGov Daemon **SHALL** assign the xGov Committee to the submitted proposal, which is then opened to vote                                                                          |
| `VOTING`    |  `25`  | The xGov Committee **MAY** vote the proposal until the voting session expires                                                                                                        |
| `APPROVED`  |  `30`  | The outcome of the vote scrutiny (quorum and majority) approved the proposal, the absentees **SHALL** be deleted, the xGov Council **SHALL** review it                               |
| `REJECTED`  |  `40`  | The outcome of the vote scrutiny (quorum and majority) rejected the proposal, the absentees **SHALL** be deleted, it **SHOULD** be finalized                                         |
| `REVIEWED`  |  `45`  | The xGov Council positively reviewed the approved proposal (T&C, etc.), the locked amount **MUST** be returned to the Proposer, the xGov Payor **MAY** disburse the requested amount |
| `BLOCKED`   |  `60`  | The xGov Council blocked the approved proposal with veto, it **SHOULD** be finalized, the locked amount **MUST** be slashed, the requested amount **MUST NOT** be paid               |
| `FUNDED`    |  `50`  | The xGov Payor paid the requested amount, it **SHOULD** be finalized                                                                                                                 |
| `FINALIZED` | `bool` | The proposal life cycle is terminated and **MAY** be deleted                                                                                                                         |

{{#include ../_include/styles.md:note}}
> The `FINALIZED` boolean flag is not an enumerated state, since it can be superposed
> to several states (i.e., `EMPTY`, `DRAFT`, `REJECTED`, `BLOCKED`, and `FUNDED`).
> Example: a Proposal can be `FUNDED` and `FINALIZED`.

![Proposal Finite-State Machine](../_images/proposal-state-machine.svg "Proposal Finite-State Machine")

## Escrow

The Proposal Escrow is an Address controlled by the Proposal Application.

### Escrow Inflows

- Partial Open Proposal Fees from xGov Treasury

- Proposal Commitment Lock from the Proposer

### Escrow Outflows

- Operation Funds to xGov Daemon on Proposal submission

- Proposal Commitment Lock to the Proposer if the Proposal is not blocked with a
veto or to the xGov Treasury otherwise

- Decommissioned MBRs to xGov Treasury

### Escrow MBRs

- Proposal Application Account

- Metadata Box

- xGov Committee Voters Boxes
