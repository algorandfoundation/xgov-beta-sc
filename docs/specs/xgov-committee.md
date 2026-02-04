$$
\newcommand {\abs}[1] {\lvert #1 \rvert}
\newcommand \A {\mathcal{A}}
\newcommand \N {\mathbb{N}}
\newcommand \Comm {\mathsf{Comm}}
\newcommand \Addr {\mathrm{Addr}}
\newcommand \Members {\mathrm{Members}}
\newcommand \Votes {\mathrm{Votes}}
\newcommand \xGov {\mathbf{x}}
$$

# xGov Committee

xGov Committees are responsible for voting on Proposals.

The formalization of xGov Committees and their voting power, as defined by [ARC-0086](https://dev.algorand.co/arc-standards/arc-0086/),
is provided below.

## Preliminaries

Let

- \\( \A \\) be the (finite) set of Algorand addresses;
- \\( \N \\) be the set of non–negative integers;
- \\( g \\) be the network Genesis Hash;
- \\( R \in \N \\) be the Application ID of the xGov Registry;
- \\( B_c \in \N \\) be the block at which the xGov Registry was created.

## Governance Period

A _governance period_ is a pair \\( (B_i, B_f) \in \N^2 \\) such that

$$
\begin{align}
  B_i &\equiv 0 \pmod{10^6}, \\\\
  B_f &\equiv 0 \pmod{10^6}, \\\\
  B_f &> B_c, \\\\
  B_f &> B_i.
\end{align}
$$

And is intended as a range of blocks \\( [B_i; B_f) \\) (\\( B_i \\) included,
\\( B_f \\) excluded).

> \\( B_i < B_c \\) is valid and denotes a period across the xGov Registry creation.

## xGovs and Voting Power

An _xGov_ is an address \\( a \in \A \\) that has acknowledged the xGov Registry
on block \\( h \\) and is therefore associated with an _active_ xGov Status.

The xGov Status **MAY** be _deactivated_ on block \\( r \\) for address \\( a \\),
either by themself (unsubscribing from the xGov Registry) or by the xGov Registry
rules.

The xGov Status is defined by the triplet \\( \xGov = (a, h, k) \\) (represented
on the xGov Registry as an xGov Box).

> Once the xGov Registry has recorded an acknowledgement with \\( h ≥ B_c \\), the
> address \\( a \\) is considered an _active_ xGov for every governance period
> \\( (B_i, B_f) \\) such that \\( h \in [B_c; B_f) \\) and \\( k \neq 0 \\); in
> particular, it is not necessary to re-acknowledge the xGov Registry for subsequent
> governance periods.

For a governance period \\( (B_i, B_f) \\), an xGov \\( \xGov \\) is _eligible_
in \\( [B_c; B_f) \\) if and only if:

- \\( a \\) has proposed at least one block in \\( [B_i; B_f) \\), and
- \\( B_c ≤ h < B_f \\), and
- \\( k = 0 \\) or \\( k \ge B_f \\).

For a fixed governance period \\( (B_i, B_f) \\), the _voting power_ of an eligible
xGov \\( \xGov \\) in that governance period is the integer

$$
w(\xGov, B_i, B_f) \in \N,
$$

defined as the number of blocks proposed by an eligible xGov \\( a \\) in the governance
period \\( [B_i; B_f) \\)[^1].

> If an _active_ xGov \(( a \\) has acknowledged the xGov Registry at some
> \\( h \in [B_c; B_f) \\) and has proposed one or more blocks in
> \\( [B_i; B_f) \\), then all such proposals in \\( [B_i; B_f) \\) contribute to
> its voting power, including those that occurred before \\( h \\).

## Definition of xGov Committee

Fix an xGov Registry \\( (g, R, B_c) \\) and a governance period
\\( (B_i, B_f) \\) as above.

An _xGov Committee_ for \\( (g, R, B_c, B_i, B_f) \\) is a finite set

$$
C \subseteq \A \times \N_{>0},
$$

of address–weight pairs \\( (a, v) \\) such that:

<!-- markdownlint-disable MD013 -->
$$
\begin{align}
  &\textbf{eligibility} &&
    \forall (a, v) \in C, a \text{ is an eligible xGov in } [B_c; B_f), \\\\
  &\textbf{voting power} &&
    \forall (a, v) \in C, v = w(\xGov B_i, B_f), \\\\
  &\textbf{uniqueness} &&
    (a_1, v_1), (a_2, v_2) \in C \text{ and } a_1 = a_2 \Rightarrow v_1 = v_2.
\end{align}
$$
<!-- markdownlint-enable MD013 -->

The corresponding _xGov Committee_ object is the tuple

$$
\Comm := (g, R, B_c, B_i, B_f, C).
$$

For convenience, we write

$$
\Addr(C) := \\{ a \in \A \mid \exists v>0, (a, v) \in C \\}
$$

for the set of xGov Committee members (addresses) induced by \\( C \\).

### xGov Committee Members

The _number of xGov Committee members_ (or _cardinality_ of the xGov Committee)
is defined as

$$
\Members(\Comm) := \abs{\Addr(C)} = \abs{C}.
$$

This value corresponds to the `totalMembers` field in the [ARC-86 canonical JSON
representation](https://dev.algorand.co/arc-standards/arc-0086/#representation)
of the xGov Committee.

### xGov Committee Voting Power

The _voting power function_ of the xGov Committee is the map

$$
v_C : \Addr(C) \to \N_{>0}, \qquad
v_C(a) := v \text{ such that } (a, v) \in C.
$$

The _total committee voting power_ is

$$
\Votes(\Comm) := \sum_{(a, v) \in C} v = \sum_{a \in \Addr(C)} v_C(a).
$$

This value corresponds to the `totalVotes` field in the [ARC-86 canonical JSON representation](https://dev.algorand.co/arc-standards/arc-0086/#representation)
of the xGov Committee.

Optionally, the _relative vote_ of a member \\( a \in \Addr(C) \\) is

$$
\mathrm{share}_C(a) := \frac{v_C(a)}{\Votes(\Comm)},
$$

whenever \\( \Votes(\Comm) > 0 \\).

## xGov Committee ID

An xGov Committee is identified by the _Committee ID_, as defined in [ARC-86 canonical
JSON representation](https://dev.algorand.co/arc-standards/arc-0086/#representation).

## Selection

The xGov Committee selection procedure and the assignment of their voting power
is performed by the Algorand Foundation.

> See the selected [Committees](https://github.com/algorandfoundation/xgov-committees)
> published by the Algorand Foundation.

## Declaration

Given the xGov Committee for the governance period \\( [Bi; Bf) \\), the xGov Committee
Manager **SHALL** declare on the xGov Registry:

- The Committee ID;

- The xGov Committee Members \\( \Members(\Comm) \\);

- The xGov Committee Voting Power \\( \Votes(\Comm) \\).

within the Committee Grace Period after \\( B_f \\).

If the xGov Committee Manager fails to declare the xGov Committee within the Committee
Grace Period, the xGov Committee is considered _stale_ and Proposals are suspended.

{{#include ../_include/styles.md:note}}
> Refer to the [xGov Registry configuration](../implementation/configuration.md)
> for the Committee Grace Period value.

## Assignment to Proposal

The xGov Daemon **SHALL** assign the current xGov Committee to Proposals upon creation
(see [Proposal Creation section](./proposal-creation.md)).

---

[^1]: If \\( a \\) is not eligible as an xGov in \\( [B_c; B_f) \\), its voting power
is implicitly taken to be zero, and it is not included in the xGov Committee.
