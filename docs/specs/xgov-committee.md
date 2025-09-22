# xGov Committee

xGov Committees are responsible for voting on Proposals.

## Selection

The xGov Committee selection and the assignment of their voting power is performed
by the Algorand Foundation, based on the selection criteria defined in [ARC-0086](http://arc.algorand.foundation/ARCs/arc-0086).

An xGov Committee is identified by the Committee ID, as defined in [ARC-0086](http://arc.algorand.foundation/ARCs/arc-0086#representation).

## Declaration

The xGov Committee Manager **SHALL** declare on the xGov Registry:

- The current Committee ID;

- The current xGov Committee Total Members;

- The current xGov Committee Total Votes.

## Assignment to Proposal

The xGov Daemon **SHALL** assign the current xGov Committee to Proposals upon creation
(see [Proposal Creation section](./proposal-creation.md)).
