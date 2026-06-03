# xGov Architecture Integrations

The xGov Architecture supports integrations with external on-chain Applications,
especially those related to vote delegation of xGovs or the vote of the xGov Council.

Third parties and Applications can rely on the xGov Registry [ARC-56 App Spec](./deployment.md#app-specs)
to build:

- The App Client for direct ABI calls to the xGov Registry, or

- The App Interface for internal C2C [ABI calls](https://algorandfoundation.github.io/puya/lg-calling-apps.html#alternative-ways-to-use-arc4-abi-call)
to the xGov Registry from their Applications.

To integrate the xGov contracts, you can follow these steps:

1. Choose one of these integration paths:

   - **Generate clients from the ARC-56 App Spec**: add `xgov-beta-sc` as a git
     submodule in your project, or otherwise consume the relevant
     [ARC-56 App Spec](./deployment.md#app-specs) as a dependency.

   - **Download pre-generated clients**: copy the already generated App Client
     (`contract_client.py`) and AVM Client (`contract_avm_client.py`) from the
     smart contract artifact folders in this repository.

1. If you generate Python or TypeScript clients from the ARC-56 App Spec:

   - Use `algokit generate client ...` to generate the App Client for direct
     ABI calls.

   - Use `puyapy-clientgen` to generate the AVM Client for inner
     `abi_call()` usage from your application.

1. If you download the pre-generated Python clients, use the artifact folders for
the relevant contract:

   - [xGov Registry App Client](https://github.com/algorandfoundation/xgov-beta-sc/tree/main/smart_contracts/artifacts/xgov_registry/x_gov_registry_client.py)
   - [xGov Registry AVM Client](https://github.com/algorandfoundation/xgov-beta-sc/tree/main/smart_contracts/artifacts/xgov_registry/x_gov_registry_avm_client.py)

   - [Proposal App Client](https://github.com/algorandfoundation/xgov-beta-sc/tree/main/smart_contracts/artifacts/proposal/proposal_client.py)
   - [Proposal AVM Client](https://github.com/algorandfoundation/xgov-beta-sc/tree/main/smart_contracts/artifacts/proposal/proposal_avm_client.py)

   - [Council App Client](https://github.com/algorandfoundation/xgov-beta-sc/tree/main/smart_contracts/artifacts/council/council_client.py)
   - [Council AVM Client](https://github.com/algorandfoundation/xgov-beta-sc/tree/main/smart_contracts/artifacts/council/council_avm_client.py)
