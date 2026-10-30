"""Simple in-memory storage for counterparties and trades."""
from typing import Dict, List, Optional

from .models import Counterparty, Status, Trade


class Repository:
    def __init__(self):
        self._counterparties: Dict[str, Counterparty] = {}
        self._trades: Dict[int, Trade] = {}
        self._next_id = 1

    # counterparties
    def add_counterparty(self, cp: Counterparty) -> None:
        if cp.cp_id in self._counterparties:
            raise ValueError(f"Counterparty {cp.cp_id} already exists")
        self._counterparties[cp.cp_id] = cp

    def get_counterparty(self, cp_id: str) -> Optional[Counterparty]:
        return self._counterparties.get(cp_id)

    def counterparties(self) -> List[Counterparty]:
        return list(self._counterparties.values())

    # trades
    def next_trade_id(self) -> int:
        tid = self._next_id
        self._next_id += 1
        return tid

    def save_trade(self, trade: Trade) -> None:
        self._trades[trade.trade_id] = trade

    def get_trade(self, trade_id: int) -> Optional[Trade]:
        return self._trades.get(trade_id)

    def trades(self) -> List[Trade]:
        return sorted(self._trades.values(), key=lambda t: t.trade_id)

    def open_trades(self, cp_id: str) -> List[Trade]:
        return [t for t in self.trades() if t.counterparty_id == cp_id and t.status == Status.APPROVED]
