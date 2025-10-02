from algosdk.encoding import decode_address

from smart_contracts.council.config import MEMBERS_KEY_PREFIX, VOTES_KEY_PREFIX


def members_box_name(address: str) -> bytes:
    return MEMBERS_KEY_PREFIX + decode_address(address)  # type: ignore


def votes_box_name(pid: int) -> bytes:
    return VOTES_KEY_PREFIX + pid.to_bytes(8, "big")
