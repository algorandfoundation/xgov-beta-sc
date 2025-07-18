# Proposers

A Proposer **MUST** have an Algorand Address.

## KYC

A Proposer **MUST** have a valid or invalid KYC status, defined by a KYC process.

The Proposer KYC status **MUST** have an expiration date.

The KYC Provider **SHALL** update the Proposer KYC status after the KYC process.

The KYC Provider **MAY** update the Proposer KYC during its validity.

The Proposer KYC **MUST** be valid and not expired to receive Proposal funding.

## Subscription

A Proposer Fee **MUST** be paid to the xGov Treasury for the subscription.

{{#include ../.include/styles.md:note}}
> The xGov Manager **MAY** modify the Proposer Fee. The Proposer Fee is used for
> the KYC process cost and to cover the Proposer Box MBR (see below).

## Proposer Box

A Proposer is associated with a Box on the xGov Registry, called _Proposer Box_.

The Proposer Fee **MUST** be paid to the xGov Treasury upon creating the Proposer
Box.

The Proposer **SHOULD** pay the Proposer Fee.

Proposer Box ID is equal to `[P||<proposer address>]`, where `P` is a domain separation
prefix and `||` denotes concatenation.

A Proposer Box has the following ABI schema:

```json
{
    "active_proposal": "bool",
    "kyc_status": "bool",
    "kyc_expiring": "uint64"
}
```

The Proposer Fee **MUST NOT** be lower than the Proposer Box MBR.
