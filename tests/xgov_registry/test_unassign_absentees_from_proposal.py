import pytest
from algokit_utils import (
    AlgoAmount,
    AlgorandClient,
    CommonAppCallParams,
    LogicError,
    SigningAccount,
)

from smart_contracts.artifacts.proposal.proposal_client import ProposalClient
from smart_contracts.artifacts.xgov_registry.x_gov_registry_client import (
    ConfigXgovRegistryArgs,
    DeclareCommitteeArgs,
    GetXgovBoxArgs,
    OpenProposalArgs,
    SubscribeXgovArgs,
    XGovRegistryClient,
    XGovRegistryConfig,
)
from smart_contracts.errors import std_errors as err
from tests.common import (
    DEFAULT_COMMITTEE_ID,
    DEFAULT_COMMITTEE_MEMBERS,
    DEFAULT_COMMITTEE_VOTES,
    CommitteeMember,
)
from tests.proposal.common import (
    REQUESTED_AMOUNT,
    absence_tolerance,
    get_locked_amount,
    scrutinize_proposal,
    unassign_absentees,
)
from tests.xgov_registry.common import LOW_ABSENCE_TOLERANCE, get_open_proposal_fee
from tests.xgov_registry.conftest import (
    _ensure_funded,
    _open_and_upload_draft,
    _payment,
    _submit_and_assign,
)


@pytest.fixture(scope="function")
def low_absence_xgov_registry_client(
    committee_manager: SigningAccount,
    xgov_registry_config_dict: dict,  # type: ignore[type-arg]
    xgov_registry_client_committee_not_declared: XGovRegistryClient,
) -> XGovRegistryClient:
    xgov_registry_config_dict["absence_tolerance"] = LOW_ABSENCE_TOLERANCE
    xgov_registry_client_committee_not_declared.send.config_xgov_registry(
        args=ConfigXgovRegistryArgs(
            config=XGovRegistryConfig(**xgov_registry_config_dict)  # type: ignore[arg-type]
        )
    )
    xgov_registry_client_committee_not_declared.send.declare_committee(
        args=DeclareCommitteeArgs(
            committee_id=DEFAULT_COMMITTEE_ID,
            size=DEFAULT_COMMITTEE_MEMBERS,
            votes=DEFAULT_COMMITTEE_VOTES,
        ),
        params=CommonAppCallParams(sender=committee_manager.address),
    )
    return xgov_registry_client_committee_not_declared


@pytest.fixture(scope="function")
def low_absence_subscribed_committee(
    algorand_client: AlgorandClient,
    committee: list[CommitteeMember],
    low_absence_xgov_registry_client: XGovRegistryClient,
) -> list[CommitteeMember]:
    xgov_fee = AlgoAmount(
        micro_algo=low_absence_xgov_registry_client.state.global_state.xgov_fee
    )
    min_balance = AlgoAmount(algo=xgov_fee.algo * 2)
    for cm in committee:
        _ensure_funded(
            algorand_client,
            cm.account,
            min_spending_balance=min_balance,
            min_funding_increment=xgov_fee,
        )
        low_absence_xgov_registry_client.send.subscribe_xgov(
            args=SubscribeXgovArgs(
                payment=_payment(
                    algorand_client,
                    sender=cm.account.address,
                    receiver=low_absence_xgov_registry_client.app_address,
                    amount=xgov_fee,
                ),
                voting_address=cm.account.address,
            ),
            params=CommonAppCallParams(sender=cm.account.address),
        )
    return committee


@pytest.fixture(scope="function")
def low_absence_voting_proposal_client(
    algorand_client: AlgorandClient,
    min_fee_times_3: AlgoAmount,
    proposer: SigningAccount,
    xgov_daemon: SigningAccount,
    low_absence_xgov_registry_client: XGovRegistryClient,
    low_absence_subscribed_committee: list[CommitteeMember],
) -> ProposalClient:
    open_proposal_fee = get_open_proposal_fee(low_absence_xgov_registry_client)
    _ensure_funded(
        algorand_client,
        proposer,
        min_spending_balance=AlgoAmount(algo=2 * open_proposal_fee.algo),
        min_funding_increment=open_proposal_fee,
    )

    proposal_app_id = low_absence_xgov_registry_client.send.open_proposal(
        args=OpenProposalArgs(
            payment=_payment(
                algorand_client,
                sender=proposer.address,
                receiver=low_absence_xgov_registry_client.app_address,
                amount=open_proposal_fee,
            )
        ),
        params=CommonAppCallParams(sender=proposer.address, static_fee=min_fee_times_3),
    ).abi_return

    proposal_client = ProposalClient(
        algorand=algorand_client,
        app_id=proposal_app_id,  # type: ignore[arg-type]
        default_sender=proposer.address,
    )

    locked_amount = get_locked_amount(REQUESTED_AMOUNT)
    _ensure_funded(
        algorand_client,
        proposer,
        min_spending_balance=locked_amount,
        min_funding_increment=locked_amount,
    )
    _open_and_upload_draft(
        algorand_client=algorand_client,
        proposal_client=proposal_client,
        proposer=proposer,
        locked_amount=locked_amount,
        requested_amount_micro_algo=REQUESTED_AMOUNT.amount_in_micro_algo,
    )

    _submit_and_assign(
        proposal_client=proposal_client,
        xgov_registry_client=low_absence_xgov_registry_client,
        proposer=proposer,
        committee=low_absence_subscribed_committee,
        xgov_daemon=xgov_daemon,
    )
    return proposal_client


@pytest.fixture(scope="function")
def low_absence_rejected_proposal_client(
    min_fee_times_2: AlgoAmount,
    no_role_account: SigningAccount,
    low_absence_voting_proposal_client: ProposalClient,
) -> ProposalClient:
    scrutinize_proposal(
        no_role_account,
        low_absence_voting_proposal_client,
        min_fee_times_2,
    )
    return low_absence_voting_proposal_client


@pytest.mark.parametrize(
    "proposal_fixture", ["rejected_proposal_client", "approved_proposal_client"]
)
def test_unassign(
    xgov_registry_client: XGovRegistryClient,
    proposal_fixture: str,
    request: pytest.FixtureRequest,
) -> None:
    proposal_client: ProposalClient = request.getfixturevalue(proposal_fixture)

    absentees = proposal_client.state.box.voters.get_map()

    before = absence_tolerance(xgov_registry_client, absentees)

    composer = xgov_registry_client.new_group()
    unassign_absentees(composer, proposal_client.app_id, absentees, op_up_count=3)
    composer.send()

    after = absence_tolerance(xgov_registry_client, absentees)

    assert after == {a: before[a] - 1 for a in absentees}


def test_unassign_and_delete(
    low_absence_xgov_registry_client: XGovRegistryClient,
    low_absence_rejected_proposal_client: ProposalClient,
) -> None:
    absentees = list(
        low_absence_rejected_proposal_client.state.box.voters.get_map().keys()
    )
    before_xgovs = low_absence_xgov_registry_client.state.global_state.xgovs

    for address in absentees:
        get_xgov_box, exists = low_absence_xgov_registry_client.send.get_xgov_box(
            args=GetXgovBoxArgs(xgov_address=address)
        ).abi_return
        assert exists
        assert get_xgov_box[1] == LOW_ABSENCE_TOLERANCE

    composer = low_absence_xgov_registry_client.new_group()
    unassign_absentees(
        composer,
        low_absence_rejected_proposal_client.app_id,
        absentees,
        op_up_count=3,
    )
    composer.send()

    after_xgovs = low_absence_xgov_registry_client.state.global_state.xgovs
    assert after_xgovs == before_xgovs - len(absentees)

    for address in absentees:
        _, exists = low_absence_xgov_registry_client.send.get_xgov_box(
            args=GetXgovBoxArgs(xgov_address=address)
        ).abi_return
        assert not exists


def test_unassign_with_unsubscribed_xgov(
    committee: list[CommitteeMember],
    xgov_registry_client: XGovRegistryClient,
    rejected_proposal_client: ProposalClient,
) -> None:
    absentees = rejected_proposal_client.state.box.voters.get_map()

    unsub_addr = next(iter(absentees))  # pick one absentee key
    kept_addrs = [a for a in absentees if a != unsub_addr]

    before = absence_tolerance(xgov_registry_client, absentees)

    unsub_member = next(m for m in committee if m.account.address == unsub_addr)
    xgov_registry_client.send.unsubscribe_xgov(
        params=CommonAppCallParams(sender=unsub_member.account.address)
    )

    composer = xgov_registry_client.new_group()
    unassign_absentees(
        composer, rejected_proposal_client.app_id, absentees, op_up_count=3
    )
    composer.send()

    after = absence_tolerance(xgov_registry_client, kept_addrs)

    assert after == {a: before[a] - 1 for a in kept_addrs}


def test_paused_registry(
    xgov_registry_client: XGovRegistryClient,
    rejected_proposal_client: ProposalClient,
) -> None:
    xgov_registry_client.send.pause_registry()
    composer = xgov_registry_client.new_group()
    unassign_absentees(
        composer,
        rejected_proposal_client.app_id,
        [],
    )
    with pytest.raises(LogicError, match=err.PAUSED_REGISTRY):
        composer.send()


def test_invalid_proposal(
    xgov_registry_client: XGovRegistryClient,
) -> None:
    composer = xgov_registry_client.new_group()
    unassign_absentees(
        composer,
        xgov_registry_client.app_id,
        [],
    )
    with pytest.raises(LogicError, match=err.INVALID_PROPOSAL):
        composer.send()


def test_wrong_proposal_status(
    xgov_registry_client: XGovRegistryClient,
    voting_proposal_client: ProposalClient,
) -> None:
    composer = xgov_registry_client.new_group()
    unassign_absentees(
        composer,
        voting_proposal_client.app_id,
        [],
    )
    with pytest.raises(LogicError, match=err.WRONG_PROPOSAL_STATUS):
        composer.send()


def test_unassign_twice(
    xgov_registry_client: XGovRegistryClient,
    rejected_proposal_client: ProposalClient,
) -> None:
    absentees = list(rejected_proposal_client.state.box.voters.get_map().keys())
    absentees.append(absentees[1])  # duplicate absentee to trigger error
    composer = xgov_registry_client.new_group()
    unassign_absentees(
        composer, rejected_proposal_client.app_id, absentees, op_up_count=3
    )
    with pytest.raises(LogicError, match=err.VOTER_NOT_FOUND):
        composer.send()
