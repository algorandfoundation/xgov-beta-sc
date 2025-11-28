# xGov Architecture Integrations

The xGov Architecture supports integrations with external on-chain Applications,
especially those related to vote delegation of xGovs or the vote of the xGov Council.

Third parties and Applications can rely on the xGov Registry [ARC-56 App Spec](./deployment.md#app-specs)
to build:

- The App Client for direct ABI calls to the xGov Registry, or

- The App Interface for internal C2C [ABI calls](https://algorandfoundation.github.io/puya/lg-calling-apps.html#alternative-ways-to-use-arc4-abi-call)
to the xGov Registry from their Applications.

To integrate the xGov Registry, you can follow these steps:

1. Download the xGov Registry [ARC-56 App Spec](./deployment.md#app-specs) or add
the `xgov-beta-sc` as git submodule to your project.

1. Use the `algokit generate client ...` to call the xGov Registry with a direct
ABI call using the App Client.

1. Use the `puyapy-clientgen` utility to call the xGov Registry with an inner `abi_call()`
using the App Interface.
