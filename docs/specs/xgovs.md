# xGovs

An xGov **MUST** have an Algorand Address.

An xGov **MUST** provide a Voting Address.

It is **RECOMMENDED** to provide a Voting Address different from the xGov Address,
to facilitate voting operation on behalf of the xGov Address (supposed to be secure
and less accessible).

The xGov Address and the current Voting Address **MAY** update the Voting Address.

The xGov Address **MAY** unsubscribe itself from being an xGov.

{{#include ../_include/styles.md:note}}
> xGov Address can be associated with any Account type. This ensures the compatibility
> and inclusivity of xGov participation (direct or delegated).

## Subscription

The xGov Registry provides two xGov (un)subscription procedures:

- **Self-Subscription**: the xGov Address **MUST** call the xGov Registry.

- **Managed-Subscription**: the ownership of the xGov _App_ Address is verified off-chain,
by the Algorand Foundation, according to a pre-defined trust model. The Managed-Onboarding/Offboarding
is executed in two steps:

  1. Users issue a [(Un)Subscription Request](#xgov-managed-subscription) to (un)subscribe, declaring
  the xGov App Address, the Application Owner Address, and a [Relation Type](./xgov-relation-types.md)
  (enumerative that identifies a pre-defined trust model).

  1. The Algorand Foundation verifies the declared and accountable xGov/Owner Addresses
  relationship off-chain (based on the [Relation Type](./xgov-relation-types.md))
  and eventually approves it.

{{#include ../_include/styles.md:note}}
> For further details about _existing_ and _new_ Relation Types, refer to the [Relation
> Types section](./xgov-relation-types.md).

An xGov Fee **MUST** be paid to the xGov Treasury for the subscription or subscription
request or unsubscription request.

{{#include ../_include/styles.md:note}}
> The xGov Manager **MAY** update the xGov Fee.

The xGov Fee has the following scope:

1. Minimal deterrent for Sybil attacks;

1. Covering the xGov Box MBR (see below).

## xGov Box

An xGov is associated with a Box on the xGov Registry, called _xGov Box_.

xGov Box ID is equal to: `[X||<xgov address>]`, where `X` is a domain separation
prefix and `||` denotes concatenation.

An xGov Box has the following ABI schema:

```json
{
    "voting_addr": "address",
    "voted_proposals": "uint64",
    "last_vote_timestamp": "uint64",
    "subscription_round": "uint64"
}
```

The xGov Fee **MUST NOT** be lower than the xGov Box MBR.

### xGov Self-Subscription

The xGov Fee **MUST** be paid to the xGov Treasury upon xGov Box creation.

The xGov Fee **MAY NOT** be paid by the xGov Address.

The Voting Address declared on subscription **MUST BE** assigned to the xGov Box.

### xGov Managed-Subscription

An xGov (Un)Subscription Request is associated with a Box on the xGov Registry, called
_xGov (Un)Subscription Request Box_.

The xGov Fee **MUST** be paid to the xGov Treasury upon xGov (Un)Subscription Request
Box creation.

The xGov Fee **MAY NOT** be paid by the xGov Address.

xGov Subscription Request Box ID is equal to: `[R||<counter>]`, where `R` is a domain
separation prefix, `<counter>` is a global counter for pending requests, and `||`
denotes concatenation.

xGov Unsubscription Request Box ID is equal to: `[RU||<counter>]`, where `RU` is a domain
separation prefix, `<counter>` is a global counter for pending unsubscription requests, and `||`
denotes concatenation.

An xGov (Un)Subscription Request Box has the following ABI schema:

```json
{
    "xgov_addr": "address",
    "owner_addr": "address",
    "relation_type": "uint64"
}
```

The xGov (Un)Subscription Request **MUST** be performed by the Owner Address.

The xGov Fee **MUST NOT** be lower than the xGov (Un)Subscribe Request Box MBR.

If the Algorand Foundation approves the subscription request:

1. The xGov Subscription Request Box **MUST** be destroyed;

1. An xGov Box **MUST** be created using the xGov Address declared on the subscription
request.

1. The Owner Address declared on the subscription request **MUST** be assigned to
the Voting Address in the created xGov Box.

If the Algorand Foundation approves the unsubscription request:

1. The xGov Unsubscription Request Box **MUST** be destroyed;

1. The xGov Box of the xGov address **MUST** be destroyed.
