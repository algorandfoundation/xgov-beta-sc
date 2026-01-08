# Algorand xGov Beta

This document describes the architecture of the xGov process (Beta).

Specifically, the architecture aims to solve the following main requirement:

> The xGov process is _a trustless_ voting system to manage grant proposals funding
> and polls for the Algorand ecosystem.

The design takes a step towards this end goal, which is a _fully decentralized application_
relying uniquely on a front-end and the Algorand Virtual Machine (AVM).

The current design minimizes the trust model and the off-chain footprint to a few
operations, carried out by a back-end controlled by the Algorand Foundation, which
could be pushed on the AVM in future iterations.

It is worth noting that the residual trusted off-chain operations are _fully accountable_
on the Algorand public Ledger.

## Motivation

The old xGov process (Alpha) has shown some weaknesses concerning the incentive
alignment, the gamification risks of the voting system, and low-quality proposals.

Moreover, the old grant proposal submission and funding mechanism were based on
a per-quarter schedule, making the whole process slow and inflexible.

Therefore, a more robust process with a continuous stream of grant proposals, votes,
and funding is desirable.

Finally, given the shift of the Algorand protocol towards consensus incentivization,
the xGov (Beta) voting power will be based on active consensus participation instead
of ALGO locking periods (Alpha).
