import re
import uuid
from re import Pattern

from algokit_utils import AlgoAmount, AlgorandClient, PaymentParams
from algosdk.v2client.algod import AlgodClient

from smart_contracts.errors import std_errors as err


def get_last_round(algod_client: AlgodClient) -> int:
    return algod_client.status()["last-round"]  # type: ignore


def get_latest_timestamp(algod_client: AlgodClient) -> int:
    return algod_client.block_info(get_last_round(algod_client))["block"]["ts"]  # type: ignore


def round_warp(to_round: int | None = None) -> None:
    """
    Fastforward directly `to_round` or advance by 1 round.

    Args:
        to_round (Optional): Round to advance to
    """
    algorand_client = AlgorandClient.default_localnet()
    algorand_client.set_suggested_params_cache_timeout(0)
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
                note=uuid.uuid4().hex.encode("utf-8"),
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


def compile_error_regex(error: str) -> Pattern[str]:
    return re.compile(f"{error}\\s+<-- Error")


ERROR_TO_REGEX: dict[str, Pattern[str]] = {
    getattr(err, name): compile_error_regex(getattr(err, name))  # type: ignore
    for name in dir(err)
    if not name.startswith("__") and isinstance(getattr(err, name), str)  # type: ignore
}
