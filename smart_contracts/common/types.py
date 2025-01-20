import typing

from algopy import arc4

# corresponds to CID_LENGTH in ./constants.py. We cannot use a variable here because as it causes type errors which
# fails compilation.
Cid = arc4.StaticArray[arc4.Byte, typing.Literal[59]]

# corresponds to COMMITTEE_ID_LENGTH in ./constants.py. We cannot use a variable here because as it causes type errors
# which fails compilation.
CommitteeId = arc4.StaticArray[arc4.Byte, typing.Literal[36]]


Error = arc4.String


class VoterBox(arc4.Struct, kw_only=True):
    votes: arc4.UInt64  # Outstanding votes to be used as Approval or Rejection
    voted: arc4.Bool  # Whether the voter has voted
