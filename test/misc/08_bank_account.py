from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class Tx:
    ts: int
    type: str
    amount: float
    desc: str


class Account:
    def __init__(self, name: str, initial: float = 0.0):
        self.name = name
        self.balance = float(initial)
        self.ledger: List[Tx] = []

    def deposit(self, amount: float, ts: int) -> None:
        self.balance += amount
        self.ledger.append(Tx(ts, "deposit", amount, "manual"))

    def withdraw(self, amount: float, ts: int) -> None:
        if amount > self.balance:
            raise ValueError("insufficient")
        self.balance -= amount
        self.ledger.append(Tx(ts, "withdraw", amount, "manual"))

    def apply_interest(self, rate: float, ts: int) -> None:
        earned = self.balance * rate
        self.balance += earned
        self.ledger.append(Tx(ts, "interest", earned, f"{rate*100:.2f}%"))


class Bank:
    def __init__(self):
        self.accounts: Dict[str, Account] = {}
        self.time = 0

    def create(self, name: str, initial: float = 0.0) -> None:
        self.accounts[name] = Account(name, initial)

    def transfer(self, a: str, b: str, amount: float) -> None:
        self.time += 1
        self.accounts[a].withdraw(amount, self.time)
        self.accounts[b].deposit(amount, self.time)
        self.accounts[a].ledger[-1].type = "transfer_out"
        self.accounts[b].ledger[-1].type = "transfer_in"
        self.accounts[a].ledger[-1].desc = b
        self.accounts[b].ledger[-1].desc = a

    def monthly_interest(self, rate: float) -> None:
        self.time += 1
        for acc in self.accounts.values():
            acc.apply_interest(rate, self.time)

    def print_summary(self) -> str:
        lines = []
        for acc in sorted(self.accounts.values(), key=lambda a: a.name):
            lines.append(f"{acc.name} balance={acc.balance:.2f}")
        return "\n".join(lines)


def main() -> None:
    bank = Bank()
    bank.create("alice", 100)
    bank.create("bob", 50)
    bank.accounts["alice"].deposit(80, 0)
    bank.transfer("alice", "bob", 40)
    bank.monthly_interest(0.01)
    print(bank.print_summary())
    print("alice ledger", [vars(t) for t in bank.accounts["alice"].ledger])


if __name__ == "__main__":
    main()


def account_balance_summary(accounts: dict[str, Account]) -> dict[str, float]:
    return {name: acc.balance for name, acc in accounts.items()}


def _ledger_totals(accounts: dict[str, Account]) -> dict[str, float]:
    out: dict[str, float] = {}
    for name, acc in accounts.items():
        out[name] = sum(tx.amount for tx in acc.ledger)
    return out


def _bank_demo() -> None:
    bank = Bank()
    bank.create("carol", 300)
    bank.create("dave", 120)
    bank.transfer("carol", "dave", 50)
    bank.monthly_interest(0.005)
    print("balances", account_balance_summary(bank.accounts))
    print("ledger_totals", _ledger_totals(bank.accounts))


if __name__ == "__main__":
    _bank_demo()
