import typing

from algopy import arc4

# corresponds to CID_LENGTH in ./constants.py. We cannot use a variable here because as it causes type errors which
# fails compilation.
Cid = arc4.StaticArray[arc4.Byte, typing.Literal[59]]

# corresponds to COMMITTEE_ID_LENGTH in ./constants.py. We cannot use a variable here because as it causes type errors
# which fails compilation.
CommitteeId = arc4.StaticArray[arc4.Byte, typing.Literal[32]]
