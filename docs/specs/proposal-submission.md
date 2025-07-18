# Discussion

The Proposer **MAY** update the Proposal Metadata during the discussion phase.

The Proposer **SHALL NOT** change the Proposal _required_ fields (e.g., the requested
amount) during the discussion phase.

To change the Proposal _required_ fields, the Proposer **MUST** drop the Proposal
Draft and open a new one.

# Submission

The Proposer **SHALL** submit the Draft Proposal after the minimum discussion period
(depending on the [Proposal _funding size_](./proposal.md#funding-sizes)).

The xGov Daemon **MAY** finalize the Draft Proposal if it becomes stale (the Proposer
does not submit the Draft).

The Proposal **MUST NOT** be submitted without Metadata.

Upon proposal submission, a percentage of the Open Proposal Fee **SHALL** be transferred
from the Proposal Escrow to the xGov Daemon to cover the operation fees.

{{#include ../.include/styles.md:note}}
> The xGov Manager **MAY** update the percentage of the Open Proposal Fee transferred
> to the xGov Daemon.

## xGov Committee Assignment

The xGov Daemon **SHALL** assign the xGov Committee of the Submitted Proposal.

The assigned xGov Committee **MUST** have the size (total members) and voting power
(total votes) of the xGov Committee ID (see [xGov Committee section](./xgov-committee.md)).

The Proposal status **MUST** be set to Voting once the xGov Committee is completely
assigned.

### Voters

The xGov Committee Voters are represented by a set of Boxes on the Proposal Application
(one box per xGov Committee Member), called the _Voter Box_.

The xGov Daemon **SHALL** create _all_ the Voter Boxes once the Proposal is Submitted.

Voter Box MBR **MUST** be covered by the Partial Open Proposal Fee.

Voter Box ID is equal to `[V||<xgov address>]`, where `V` is a domain separation
prefix, `<xgov address>` is the same as used by the xGov upon subscription, and
`||` denotes concatenation.

A Voter Box has the following ABI schema:

```json
{
    "votes": "unit32",
    "voted": "bool"
}
```

### Vote Opening

The Submitted Proposal **MUST** be promoted to Voting once the xGov Committee has
been completely assigned.

The duration of the voting session depends on the Proposal _funding sizes_.

The Voting Proposal **MUST** stay open until either:

- All the xGov Committee members have voted, or

- The voting duration expires.
