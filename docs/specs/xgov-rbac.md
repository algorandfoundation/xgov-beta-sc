# Roles

## xGov Manager

The xGov Manager is an Algorand Address controlled by the Algorand Foundation.

It represents the _root of trust_ for the xGov process.

### RBAC

The xGov Manager **MAY** rotate itself.

The xGov Manager **MUST** provide and **MAY** update the [xGov Committee Manager](#xgov-committee-manager)
Address.

The xGov Manager **MUST** provide and **MAY** update the [xGov Daemon](#xgov-daemon)
Address.

The xGov Manager **MUST** provide and **MAY** update the [xGov Council](#xgov-council)
Address.

The xGov Manager **MUST** provide and **MAY** update the [xGov Payor](#xgov-payor).

The xGov Manager **MUST** provide and **MAY** update the [xGov Subscriber](#xgov-subscriber)
Address.

The xGov Manager **MUST** provide and **MAY** update the [KYC Provider](./proposers.md#kyc)
Address.

### Configuration and Updates

The xGov Manager **MAY** pause the [xGov Registry](./xgov-registry.md).

The xGov Manager **MAY** pause the creation of new [Proposals](./proposal.md).

The xGov Manager **MAY** update the xGov Registry anytime.

The xGov Manager **MAY** reconfigure the parameters of the xGov Registry.

### Treasury Management

The xGov Manager **MAY** execute withdrawals of outstanding funds from the [xGov
Treasury](./xgov-treasury.md).

## xGov Committee Manager

The xGov Committee Manager is an Algorand Address controlled by the Algorand Foundation.

The xGov Committee Manager **SHALL** declare the xGov Committee currently in charge
on the xGov Registry (see [xGov Committee section](./xgov-committee.md#declaration)).

## xGov Daemon

The xGov Daemon is an Algorand Address controlled by the Algorand Foundation (back-end).

The xGov Daemon **SHALL** assign the xGov Committee currently in charge (voters
and their voting power) to open Proposals.

The xGov Daemon **SHOULD** delete absentees (voters) after Proposals scrutiny.

## xGov Council

The xGov Council is an Algorand Address representing a group of elected Councilors.

The xGov Council **MUST** have an odd number of Councilors.

The xGov Council **MUST** review approved Proposals (see [Proposal review section](./proposal-vote.md#review)).

The xGov Council **MAY** apply a veto against approved Proposals according to the
_terms and conditions_ of the xGov process.

The xGov Council majority vote is **REQUIRED** to apply a veto against approved
proposals.

## xGov Payor

The xGov Payor is an Algorand Address controlled by the Algorand Foundation.

The xGov Payor **MAY** disburse the requested funds for approved and reviewed Proposals
if there are enough funds in the xGov Treasury.

## xGov Subscriber

The xGov Subscriber is an Algorand Address controlled by the Algorand Foundation.

The xGov Subscriber **MAY** onboard or offboard xGovs who cannot execute a self-subscription
or self-unsubscription (e.g., due to contract immutability or other restrictions).
