# Votes

xGovs vote **MUST BE** either _“Approve”_, _“Reject”_, _“Null”_, or _“Boycott”_.

xGovs **MAY** abstain from voting.

xGovs **SHALL** vote once per Proposal: the allocation of _“Approve”_, _“Reject”_,
and _“Null”_ votes **MUST** be simultaneous.

Vote usage **MAY** be partial. Unused votes are default _“Null”_.

Vote is a _“Boycott”_ vote when the number of _“Approve”_ votes equals the xGov voting power and the number of _“Reject”_ votes equals the xGov voting power.

Vote is invalid and rejected by the xGov Registry if the sum of _“Approve”_, _“Reject”_, and _“Null”_ votes is not equal to the xGov voting power and the vote is not a _“Boycott”_.

Vote **SHALL NOT** be modified.

{{#include ../_include/styles.md:example}}
> Pooled Vote Example: Let's have an xGov Staking Pool with `N` votes. The Pool
> **SHOULD** collect poolers’ opinions _before_ expressing the Pool vote accordingly.
> Once the Pool is ready to vote, the allocation of `N` votes among _“Approve”_,
> _“Reject”_, or _“Null”_ is simultaneous and can no longer be modified.

Vote **MUST BE** sent either by the xGov Address or the Voting Address.

## Scrutiny

A Submitted Proposal is Approved _if and only if_ all the following conditions hold:

- A _democratic quorum_ of all xGov Committee (one xGov, one vote) is reached. _“Null”_
votes **affect** this quorum. _“Boycott”_ votes **do not affect** this quorum.

- A _weighted quorum_ of all xGov Committee voting power is reached. _“Null”_ votes
**affect** this quorum. _“Boycott”_ votes **do not affect** this quorum.

- The _relative majority_ of _“Approve”_ over _“Reject”_ votes is reached. _“Null”_
votes **do not affect** the relative majority. _“Boycott”_ votes **do not affect** the relative majority.

And it is Rejected otherwise.

The Commitment Lock **MUST** be returned to the Proposer if the Proposal is Rejected.

The xGov Daemon **SHALL** delete Voter Boxes of absentees xGovs.

## Review

All Voter Box **MUST** be deleted before reviewing the Proposal.

The xGov Council **MUST** review Approved Proposals.

The xGov Council **MAY** apply a veto to an Approved Proposal.

An Approved Proposal is considered either:

- Blocked, if the **veto is applied**;

- Reviewed, if the **veto is not applied**.

In case of a Blocked Proposal:

- The requested amount **MUST NOT** be paid.

- The Commitment Lock **MUST** be transferred (slashed) from the Proposal Escrow
to the xGov Treasury.

In case of a Reviewed Proposal:

- The Commitment Lock **MUST** be returned from the Proposal Escrow to the Proposer.
