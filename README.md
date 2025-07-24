# xGov Beta Architecture

Documentation: <https://tbd/>

## Deployments

| Network  |                 xGov Registry                 |
|:---------|:---------------------------------------------:|
| Main Net |     [TBD](https://lora.algokit.io/app-id)     |
| Test Net | [TBD](https://lora.algokit.io/testnet/app-id) |

| App Spec      | Link                                                                                                                                    |
|:--------------|:----------------------------------------------------------------------------------------------------------------------------------------|
| xGov Registry | [AppSpec](https://github.com/algorandfoundation/xgov-beta-sc/blob/main/smart_contracts/artifacts/xgov_registry/XGovRegistry.arc56.json) |
| Proposal      | [AppSpec](https://github.com/algorandfoundation/xgov-beta-sc/blob/main/smart_contracts/artifacts/proposal/Proposal.arc56.json)          |
| xGov Council  | [AppSpec](https://github.com/algorandfoundation/xgov-beta-sc/blob/main/smart_contracts/artifacts/proposal/Council.arc56.json)           |

1. Download the App Spec JSON file;
1. Navigate to the [Lora App Lab](https://lora.algokit.io/testnet/app-lab);
1. Create the App Interface using the existing App ID and App Spec JSON;
1. Explore the xGov Architecture interfaces.

## Local Setup and Tests

The xGov Architecture project is developed with [AlgoKit](https://algorand.co/algokit).

- Install AlgoKit
- Set up your virtual environment (managed with [Poetry](https://python-poetry.org/))

```shell
algokit bootstrap all
```

- Start your Algorand LocalNet (requires [Docker](https://www.docker.com/get-started/))

```shell
algokit localnet start
```

- Run tests (managed with PyTest)

```shell
algokit project run test
```

or, for verbose results:

```shell
poetry run pytest -s -v tests/<contract_name>/<test_case>.py
```

## How to contribute

Refer to xGov Architecture documentation!
