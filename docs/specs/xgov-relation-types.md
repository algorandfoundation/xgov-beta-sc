# Relation Types

A _Relation Type_ identifies the _trust model_ and the off-chain verification process
of the xGov App Address _ownership_ for a [Managed-Subscription](./xgovs.md#subscription).

## New Relation Type Request

A request for a new Relation Type **SHALL** be submitted by the Application Creator
opening a [new _Relation Type Request_ issue](https://github.com/algorandfoundation/xgov-beta-sc/issues/new/choose).

A Relation Type **MUST** be approved by the Algorand Foundation.

## Available Relation Type

The following enumerative `relation_type` (`uint64`) are currently available:

| RELATION TYPE | ENUM |
|:--------------|:----:|
| Réti Pooling  | `1`  |
| Compx LST     | `2`  |

### Relation Type 1: Réti Pooling

Réti Validators are created by an _immutable_ factory contract.

A Validator is uniquely owned by an immutable _Owner Address_.

Each Validator may control several Staking Pools, which participate in Algorand
consensus.

To request a Managed Subscription for a Réti Staking Pool:

- The `relation_type` **MUST** be set to `1`;
- The `owner_addr` **MUST** be set to the Validator Owner Address;
- The `xgov_addr` **MUST** be set to the Staking Pool Address.

### Relation Type 2: Compx LST

TBD
