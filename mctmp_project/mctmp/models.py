"""Domain models: counterparties and trades."""
from dataclasses import dataclass
from datetime import date
from enum import Enum


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class Status(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SETTLED = "SETTLED"
    CANCELLED = "CANCELLED"


@dataclass
class Counterparty:
    cp_id: str
    name: str
    rating: str                 # e.g. AAA, A, BBB
    credit_limit: float         # max allowed net credit exposure
    netting_agreement: bool = False
    collateral_held: float = 0.0
    active: bool = True


@dataclass
class Trade:
    trade_id: int
    counterparty_id: str
    instrument: str
    side: Side
    quantity: float
    price: float
    trade_date: date
    settlement_date: date
    status: Status = Status.PENDING
    reason: str = ""

    @property
    def notional(self) -> float:
        return self.quantity * self.price

    @property
    def sign(self) -> int:
        return 1 if self.side == Side.BUY else -1
