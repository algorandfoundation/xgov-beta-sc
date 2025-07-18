# Roles

## xGov Manager

The xGov Manager is an Algorand Address controlled by the Algorand Foundation.

It represents the _root of trust_ for the xGov process.

The xGov Manager **MAY** be rotated by the current xGov Manager.

The xGov Manager **MUST** provide an [xGov Committee Manager](#xgov-committee-manager)
Address.

The xGov Manager **MAY** update the xGov Committee Manager.

The xGov Manager **MUST** provide an [xGov Daemon](#xgov-daemon) Address.

The xGov Manager **MAY** update the xGov Daemon.

The xGov Manager **MUST** provide an [xGov Council](#xgov-council) Address.

The xGov Manager **MAY** update the xGov Council.

The xGov Manager **MUST** provide an [xGov Payor](#xgov-payor).

The xGov Manager **MAY** update the xGov Payor Address.

The xGov Manager **MUST** provide an [xGov Subscriber](#xgov-subscriber) Address.

The xGov Manager **MAY** update the xGov Subscriber.

The xGov Manager **MUST** provide a [KYC Provider](./proposers.md#kyc) Address.

The xGov Manager **MAY** update the KYC Provider.

The xGov Manager **MAY** pause the xGov Registry.

The xGov Manager **MAY** pause the creation of new Proposals.

The xGov Manager **MAY** update the rules of the xGov Registry at any time.

The xGov Manager **MAY** reconfigure the parameters of the xGov Registry.

The xGov Manager **MUST NOT** reconfigure the xGov Registry in case of pending Proposals.

The xGov Manager **MAY** execute administrative withdrawals of outstanding funds
from the [xGov Treasury](./xgov-treasury.md).

## xGov Committee Manager

The xGov Committee Manager is an Algorand Address controlled by the Algorand Foundation.

The xGov Committee Manager **SHALL** declare the xGov Committee currently in charge
on the xGov Registry.

## xGov Daemon

The xGov Daemon is an Algorand Address controlled by the Algorand Foundation (back-end).

The xGov Daemon **SHALL** assign the xGov Committee currently in charge (and their
voting power) to Proposals once submitted.

The xGov Daemon **SHALL** delete the xGov Committee assigned to a Proposal once the
voting is over (see [Proposal Finalization section](./proposal-finalization.md)).

## xGov Council

The xGov Council is an Algorand Address representing a group of elected councilors.

The xGov Council **MUST** have an odd number of councilors.

The xGov Council **MAY** apply a veto against approved proposals according to the
_terms and conditions_ of the xGov process.

The xGov Council majority vote is **REQUIRED** to apply a veto against approved
proposals.

## xGov Payor

The xGov Payor is an Algorand Address controlled by the Algorand Foundation.

The xGov Payor **MAY** disburse payments for approved and reviewed proposals if
there are enough funds in the xGov Treasury.

## xGov Subscriber

The xGov Subscriber is an Algorand Address controlled by the Algorand Foundation.

The xGov Subscriber **MAY** onboard xGovs who cannot execute a self-subscription
(e.g., due to contract immutability or other restrictions).
