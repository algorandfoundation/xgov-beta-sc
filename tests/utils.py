from typing import Optional

from algokit_utils import AlgorandClient, PaymentParams, AlgoAmount
from algosdk.v2client.algod import AlgodClient


def get_last_round(algod_client: AlgodClient) -> int:
    return algod_client.status()["last-round"]  # type: ignore


def get_latest_timestamp(algod_client: AlgodClient) -> int:
    return algod_client.block_info(get_last_round(algod_client))["block"]["ts"]  # type: ignore


def round_warp(to_round: Optional[int] = None) -> None:
    """
    Fastforward directly `to_round` or advance by 1 round.

    Args:
        to_round (Optional): Round to advance to
    """
    algorand_client = AlgorandClient.default_localnet()
    dispenser = algorand_client.account.localnet_dispenser()
    if to_round is not None:
        last_round = get_last_round(algorand_client.client.algod)
        assert to_round > last_round
        n_rounds = to_round - last_round
    else:
        n_rounds = 1
    for _ in range(n_rounds):
        algorand_client.send.payment(
            PaymentParams(
                signer=dispenser.signer,
                sender=dispenser.address,
                receiver=dispenser.address,
                amount=AlgoAmount(micro_algo=0),
            )
        )


def time_warp(to_timestamp: int) -> None:
    """
    Fastforward directly `to_timestamp`

    Args:
        to_timestamp: Timestamp to advance to
    """
    algorand_client = AlgorandClient.default_localnet()
    offset = to_timestamp - get_latest_timestamp(algorand_client.client.algod)
    if offset > 0:
        algorand_client.client.algod.set_timestamp_offset(offset)
    round_warp()
    algorand_client.client.algod.set_timestamp_offset(0)
