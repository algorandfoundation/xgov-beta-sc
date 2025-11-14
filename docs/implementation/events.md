# Events

The xGov Architecture provides the following classes of [ARC-28](https://dev.algorand.co/arc-standards/arc-0028)
events:

- **xGov Registry Events**, emitted by the [xGov Registry singleton application](../specs/xgov-registry.md).

- **Proposal Events**, emitted by the [Proposal applications](../specs/proposal.md).

Clients can subscribe to these ARC-28 events using the [AlgoKit Subscriber Library](https://dev.algorand.co/algokit/subscribers/typescript/overview/#arc-28-event-subscription-and-reads).

## xGov Registry Events

### `XGovSubscribed`

An xGov subscribed (either through self-onboarding or managed onboarding).

| ARGUMENT |   TYPE    | DESCRIPTION                        |
|:---------|:---------:|:-----------------------------------|
| xGov     | `address` | The address of the subscribed xGov |
| Delegate | `address` | The address of the delegated voter |

### `XGovUnsubscribed`

An xGov unsubscribed (either through self-onboarding or managed onboarding).

| ARGUMENT  |   TYPE    | DESCRIPTION                          |
|:----------|:---------:|:-------------------------------------|
| xGov      | `address` | The address of the unsubscribed xGov |

### `ProposerSubscribed`

A Proposer subscribed.

| ARGUMENT  |   TYPE    | DESCRIPTION                            |
|:----------|:---------:|:---------------------------------------|
| Proposer  | `address` | The address of the subscribed Proposer |

### `ProposerKYC`

A Proposer KYC status update.

| ARGUMENT  |   TYPE    | DESCRIPTION                              |
|:----------|:---------:|:-----------------------------------------|
| Proposer  | `address` | The address of the unsubscribed Proposer |
| Valid KYC |  `bool`   | The Proposer KYC is valid                |

### `NewCommittee`

A new xGov Committee has been elected.

| ARGUMENT     |    TYPE    | DESCRIPTION         |
|:-------------|:----------:|:--------------------|
| Committee ID | `byte[32]` | ARC-86 Committee ID |
| Size         |  `uint32`  | Committee members   |
| Votes        |  `uint32`  | Committee votes     |

### `NewProposal`

A new Proposal has been opened.

| ARGUMENT    |   TYPE    | DESCRIPTION             |
|:------------|:---------:|:------------------------|
| Proposal ID | `uint64`  | Proposal Application ID |
| Proposer    | `address` | Proposer address        |

## Proposal Events

### `Opened`

The Proposal has been opened.

| ARGUMENT         |   TYPE   | DESCRIPTION                                |
|:-----------------|:--------:|:-------------------------------------------|
| Funding Type     | `uint8`  | Enum: Retroactive (`10`), Proactive (`20`) |
| Requested Amount | `uint64` | Requested Amount (microALGO)               |
| Category         | `uint8`  | Small (`10`), Medium (`20`), Large (`30`)  |

### `Submitted`

The Proposal has been submitted for voting.

| ARGUMENT              |   TYPE   | DESCRIPTION                                 |
|:----------------------|:--------:|:--------------------------------------------|
| Vote Opening          | `uint64` | Vote Opening UNIX timestamp                 |
| Vote Closing          | `uint64` | Vote Closing UNIX timestamp                 |
| Quorum Voters         | `uint32` | Democratic Quorum (voters) required to pass |
| Weighted Quorum Votes | `uint32` | Weighted Quorum (votes) required to pass    |

### `Vote`

A vote has been cast on the Proposal.

| ARGUMENT         |   TYPE    | DESCRIPTION                          |
|:-----------------|:---------:|:-------------------------------------|
| xGov             | `address` | xGov address that expressed the vote |
| Total Voters     | `uint32`  | Voters so far                        |
| Total Approvals  | `uint32`  | Approval votes so far                |
| Total Rejections | `uint32`  | Rejections votes so far              |
| Total Nulls      | `uint32`  | Null votes so far                    |

### `Scrutiny`

The vote has been scrutinized.

| ARGUMENT   |  TYPE  | DESCRIPTION                                                                 |
|:-----------|:------:|:----------------------------------------------------------------------------|
| Approved   | `bool` | The Proposal has been approved (both quorums reached and majority approved) |
| Plebiscite | `bool` | All Committee members voted                                                 |

### `Review`

The xGov Council has reviewed the Proposal.

| ARGUMENT |  TYPE  | DESCRIPTION                               |
|:---------|:------:|:------------------------------------------|
| Veto     | `bool` | The proposal has been blocked with a veto |
