# Bug Bounty

The Algorand Foundation offers a bug bounty focused on the smart contracts that
power the xGov Beta program.

This initiative aims to enhance the security and robustness of the xGov Beta architecture
by leveraging the expertise of the white-hat hacker community.

The bug bounty program rewards participants who successfully identify and privately
report vulnerabilities within the xGov Beta [smart contracts implementation](https://github.com/algorandfoundation/xgov-beta-sc).

Rewards (in ALGO) will be tiered based on the criticality of the discovered flaws,
categorized as follows:

| SEVERITY | DESCRIPTION                                                                                                 | REWARD AMOUNT         |
|:---------|:------------------------------------------------------------------------------------------------------------|:----------------------|
| High     | Bugs that could lead to the loss of user-committed funds in Proposals.                                      | \\( 50{,}000 \\) ALGO |
| Medium   | Flaws that could result in the loss of xGov Treasury funds.                                                 | \\( 30{,}000 \\) ALGO |
| Low      | Issues that might lead to an inconsistent state (e.g., unauthorized voting, bypassing process gates, etc.). | \\( 15{,}000 \\) ALGO |

We encourage all interested security researchers to participate and contribute to
the secure evolution of the xGov platform.

## Private Disclosure Process

To ensure the security of the xGov platform, we require all vulnerability findings
to be disclosed privately.

Please follow these guidelines:

1. **Reporting Channel:** All bug reports **MUST** be submitted to the dedicated
Algorand Foundation security email address: [security@algorand.foundation](mailto:security@algorand.foundation).

1. **Confidentiality:** All communications and information shared during the disclosure
process **MUST** be kept confidential.

1. **No Public Disclosure:** Please do not publicly disclose any vulnerability until
it has been patched and approved for public release by the Algorand Foundation.
Unauthorized public disclosure will result in disqualification from the bug bounty
program.

1. **Documentation:** Your report should be as detailed as possible, including:
   - Repository version and commit hash.
   - A clear description of the vulnerability.
   - Steps to reproduce the vulnerability.
   - Any relevant proof-of-concept code or scripts.
   - The potential impact of the vulnerability.
   - Recommendations for remediation, if applicable.
   - A template table with finding logs on the source code references, example:

| FINDING ID | SEVERITY | LOCATION (path-to-file:line-number)                                      | DESCRIPTION | PROPOSED SOLUTION (Optional) |
|:----------:|:---------|:-------------------------------------------------------------------------|:------------|:-----------------------------|
|   H-001    | High     | `smart_contracts/xgov_registry/contract.py:42`                           | ...         | ...                          |
|   L-001    | Low      | `smart_contracts/artifacts/xgov_registry/XGovRegistry.approval.teal:420` | ...         | ...                          |

Upon receiving your report, the Algorand Foundation security team will acknowledge
the receipt and begin the validation process.

The security team will communicate with you regularly regarding the status of your
submission and any necessary follow-up.
