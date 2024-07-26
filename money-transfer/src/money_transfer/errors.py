class NotEnoughFundsError(Exception):
    def __init__(self, account_id: int) -> None:
        super().__init__(f"Account {account_id} does not have enough money")


class VersionConflictError(Exception):
    def __init__(self) -> None:
        super().__init__("Someone else got here first.")
