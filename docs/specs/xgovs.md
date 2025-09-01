# xGovs

An xGov **MUST** have an Algorand Address.

An xGov **MUST** provide a Voting Address.

It is **RECOMMENDED** to provide a Voting Address different from the xGov Address,
to facilitate voting operation on behalf of the xGov Address (supposed to be secure
and less accessible).

The xGov Address and the current Voting Address **MAY** update the Voting Address.

{{#include ../.include/styles.md:note}}
> xGov Address can be associated with any Account type. This ensures the compatibility
> and inclusivity of xGov participation (direct or delegated).

## Subscription

The xGov Registry provides two xGov subscription procedures:

- **Self-Subscription**: the xGov Address **MUST** call the xGov Registry.

- **Managed-Subscription**: the ownership of the xGov App Address is verified off-chain,
by the Algorand Foundation, according to a pre-defined trust model. The Managed-Onboarding
is executed in two steps:

  1. Users issue a Subscription Request, declaring the xGov Address, the Owner Address,
  and a Relation Type (enumerative that identifies a pre-defined trust model).

  1. The Algorand Foundation verifies the declared and accountable xGov/Owner Addresses
  relationship off-chain (based on the Relation Type) and eventually approves it.

{{#include ../.include/styles.md:note}}
> At the time of writing, the only Relation Type value is `1`, dedicated to the Reti
> Pool protocol.

An xGov Fee **MUST** be paid to the xGov Treasury for the subscription or subscription
request.

{{#include ../.include/styles.md:note}}
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

An xGov Subscription Request is associated with a Box on the xGov Registry, called
_xGov Subscription Request Box_.

The xGov Fee **MUST** be paid to the xGov Treasury upon xGov Subscription Request
Box creation.

The xGov Fee **MAY NOT** be paid by the xGov Address.

xGov Subscription Request Box ID is equal to: `[R||<counter>]`, where `R` is a domain
separation prefix, `<counter>` is a global counter for pending requests, and `||`
denotes concatenation.

An xGov Subscription Request Box has the following ABI schema:

```json
{
    "xgov_addr": "address",
    "owner_addr": "address",
    "relation_type": "uint64"
}
```

The xGov Fee **MUST NOT** be lower than the xGov Subscribe Request Box MBR.

If the Algorand Foundation approves the subscription request:

1. The xGov Subscription Request Box **MUST** be destroyed;

1. An xGov Box **MUST** be created using the xGov Address declared on the subscription
request.

1. The Owner Address declared on the subscription request **MUST** be assigned to
the Voting Address in the created xGov Box.

#### Relation Types

The following enumerative `relation_type` (`uint64`) are currently defined:

| RELATION TYPE | ENUM |
|:--------------|:----:|
| Reti Pooling  | `1`  |
| Compx LST     | `2`  |
