$$
\newcommand {\abs}[1] {\lvert #1 \rvert}
\newcommand \A {\mathcal{A}}
\newcommand \N {\mathbb{N}}
\newcommand \Comm {\mathsf{Comm}}
\newcommand \Addr {\mathrm{Addr}}
\newcommand \Members {\mathrm{Members}}
\newcommand \Votes {\mathrm{Votes}}
$$

# xGov Committee

xGov Committees are responsible for voting on Proposals.

The formalization of xGov Committees and their voting power, as defined by [ARC-0086](http://arc.algorand.foundation/ARCs/arc-0086),
is provided below.

## Preliminaries

Let

- \\( \A \\) be the (finite) set of Algorand addresses;
- \\( \N \\) be the set of non–negative integers;
- \\( g \\) be the network Genesis Hash;
- \\( R \in \N \\) be the Application ID of the xGov Registry;
- \\( B_c \in \N \\) be the block at which the xGov Registry was created.

A _governance period_ is a pair \\( (B_i, B_f) \in \N^2 \\) such that

$$
\begin{align}
  B_i &\equiv 0 \pmod{10^6}, \\\\
  B_f &\equiv 0 \pmod{10^6}, \\\\
  B_f &> B_c, \\\\
  B_f &> B_i.
\end{align}
$$

## xGovs and Voting Power

An _xGov_ is an address \\( a \in \mathcal{A} \\) that has acknowledged the xGov
Registry and is therefore eligible to acquire voting power.

For a fixed governance period \\( (B_i, B_f) \\), the _voting power_ of an xGov
\\( a \\) in that governance period is the integer

$$
w(a; B_i, B_f) \in \N,
$$

defined as the number of blocks proposed by address \\( a \\) in the range
\\( [B_i, B_f) \\)[^1].

## Definition of xGov Committee

Fix an xGov Registry \\( (g, R, B_c) \\) and a governance period \\( (B_i, B_f) \\)
as above.

An _xGov Committee_ for \\( (g, R, B_c, B_i, B_f) \\) is a finite set

$$
C \subseteq \A \times \N_{>0},
$$

of address–weight pairs \\( (a, v) \\) such that:

<!-- markdownlint-disable MD013 -->
$$
\begin{align}
  &\textbf{eligibility} &&
    \forall (a, v) \in C, a \text{ is an eligible xGov in some block of } [B_c, B_f), \\\\
  &\textbf{voting power} &&
    \forall (a, v) \in C, v = w(a; B_i, B_f), \\\\
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

The _number of xGov Committee members_ (or _cardinality_ of the xGov Committee) is
defined as

$$
\Members(\Comm) := \abs{\Addr(C)} = \abs{C}.
$$

This value corresponds to the `totalMembers` field in the [ARC-86 canonical JSON
representation](http://arc.algorand.foundation/ARCs/arc-0086#representation) of the
xGov Committee.

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

This value corresponds to the `totalVotes` field in the [ARC-86 canonical JSON representation](http://arc.algorand.foundation/ARCs/arc-0086#representation)
of the xGov Committee.

Optionally, the _relative vote_ of a member \\( a \in \Addr(C) \\) is

$$
\mathrm{share}_C(a) := \frac{v_C(a)}{\Votes(\Comm)},
$$

whenever \\( \Votes(\Comm) > 0 \\).

## xGov Committee ID

An xGov Committee is identified by the Committee ID, as defined in [ARC-86 canonical
JSON representation](http://arc.algorand.foundation/ARCs/arc-0086#representation).

## Selection

The xGov Committee selection and the assignment of their voting power is performed
by the Algorand Foundation.

## Declaration

The xGov Committee Manager **SHALL** declare on the xGov Registry:

- The current Committee ID;

- The current xGov Committee Members;

- The current xGov Committee Voting Power.

## Assignment to Proposal

The xGov Daemon **SHALL** assign the current xGov Committee to Proposals upon creation
(see [Proposal Creation section](./proposal-creation.md)).

---

[^1]: If \\( a \\) is not eligible as an xGov in \\( [B_c,B_f) \\), its voting power
is implicitly taken to be zero, and it is not included in the xGov Committee.
