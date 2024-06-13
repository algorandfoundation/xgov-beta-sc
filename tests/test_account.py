from models.account import Account


def test_pass_pay(faucet: Account) -> None:
    faucet.pay(faucet, 0)
