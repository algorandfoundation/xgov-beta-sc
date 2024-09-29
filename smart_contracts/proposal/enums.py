from typing import Final

# Proposal Status
STATUS_EMPTY: Final[int] = (
    0  # Empty structure (default values) for a new proposal, waiting for initialization
)
STATUS_DRAFT: Final[int] = (
    10  # An Empty proposal is initialized (and updated) from the xGov Portal
)
STATUS_FINAL: Final[int] = (
    20  # Draft is submitted to vote by the Proposer after minimum discussion time
)
STATUS_VOTING: Final[int] = (
    25  # Final proposal is open to vote until the voting session expires
)
STATUS_APPROVED: Final[int] = 30  # Approved at the end of voting phase
STATUS_REJECTED: Final[int] = 40  # Rejected at the end of voting phase
STATUS_FUNDED: Final[int] = 50  # Proposal has been funded
STATUS_BLOCKED: Final[int] = 60  # Blocked with veto, the Grant Proposal can not be paid
STATUS_DELETE: Final[int] = 70  # Proposal life cycle is complete and could be deleted

# Proposal Category
CATEGORY_NULL: Final[int] = 0  # Null category
CATEGORY_SMALL: Final[int] = 10  # Small category
CATEGORY_MEDIUM: Final[int] = 20  # Medium category
CATEGORY_LARGE: Final[int] = 33  # Large category

# Funding Type
FUNDING_NULL: Final[int] = 0  # Null funding type
FUNDING_PROACTIVE: Final[int] = 10  # Proactive funding type
FUNDING_RETROACTIVE: Final[int] = 20  # Retroactive funding type
