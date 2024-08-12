import typing

from algopy import arc4

# corresponds to CID_LENGTH in ./constants.py. We cannot use a variable here because as it causes type errors which
# fails compilation.
Cid = arc4.StaticArray[arc4.Byte, typing.Literal[59]]

# corresponds to COMMITTEE_ID_LENGTH in ./constants.py. We cannot use a variable here because as it causes type errors
# which fails compilation.
CommitteeId = arc4.StaticArray[arc4.Byte, typing.Literal[32]]


# class XGovRegistryConfig(arc4.Struct):
#     """XGov Registry Configuration"""
#     min_requested_amount: arc4.UInt64  # Minimum requested amount in Algos
#     max_requested_amount_small: arc4.UInt64  # Maximum requested amount for small proposals in Algos
#     max_requested_amount_medium: arc4.UInt64  # Maximum requested amount for medium proposals in Algos
#     max_requested_amount_large: arc4.UInt64  # Maximum requested amount for large proposals in Algos
#
#     discussion_duration_small: arc4.UInt64  # Discussion duration for small proposals in weeks
#     discussion_duration_medium: arc4.UInt64  # Discussion duration for medium proposals in weeks
#     discussion_duration_large: arc4.UInt64  # Discussion duration for large proposals in weeks
