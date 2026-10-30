"""Trade management workflow: submit -> approve/reject -> settle/cancel."""
from datetime import date
from typing import Dict

from .exposure import counterparty_exposure
from .models import Counterparty, Side, Status, Trade
from .repository import Repository


class PlatformError(Exception):
    pass


class TradeManager:
    def __init__(self, repo: Repository, prices: Dict[str, float], today: date):
        self.repo = repo
        self.prices = prices
        self.today = today

    # ---- counterparties --------------------------------------------------
    def add_counterparty(self, cp: Counterparty) -> None:
        self.repo.add_counterparty(cp)

    def post_collateral(self, cp_id: str, amount: float) -> None:
        cp = self._counterparty(cp_id)
        cp.collateral_held += amount

    def suspend_counterparty(self, cp_id: str) -> None:
        self._counterparty(cp_id).active = False

    # ---- trades ----------------------------------------------------------
    def submit_trade(self, cp_id: str, instrument: str, side: Side, quantity: float,
                     price: float, settlement_date: date) -> Trade:
        trade = Trade(self.repo.next_trade_id(), cp_id, instrument, side, quantity, price,
                      self.today, settlement_date)
        errors = self._validate(trade)
        if not errors:
            cp = self.repo.get_counterparty(cp_id)
            projected = counterparty_exposure(cp, self.repo.open_trades(cp_id) + [trade], self.prices)
            if projected > cp.credit_limit:
                errors.append(f"Credit limit breached: projected exposure {projected:,.2f} "
                              f"> limit {cp.credit_limit:,.2f}")
        if errors:
            trade.status, trade.reason = Status.REJECTED, "; ".join(errors)
        else:
            trade.status = Status.APPROVED
        self.repo.save_trade(trade)
        return trade

    def cancel_trade(self, trade_id: int) -> Trade:
        trade = self._trade(trade_id)
        if trade.status != Status.APPROVED:
            raise PlatformError(f"Trade {trade_id} is {trade.status.value}; only APPROVED trades can be cancelled")
        trade.status = Status.CANCELLED
        return trade

    def settle_due_trades(self) -> Dict[int, float]:
        """Settle all approved trades due today or earlier. Returns cash flow per trade
        (negative = we pay cash for a BUY, positive = we receive cash for a SELL)."""
        cash = {}
        for t in self.repo.trades():
            if t.status == Status.APPROVED and t.settlement_date <= self.today:
                t.status = Status.SETTLED
                cash[t.trade_id] = -t.sign * t.notional
        return cash

    def exposure(self, cp_id: str) -> float:
        cp = self._counterparty(cp_id)
        return counterparty_exposure(cp, self.repo.open_trades(cp_id), self.prices)

    # ---- internals -------------------------------------------------------
    def _validate(self, t: Trade) -> list:
        errors = []
        cp = self.repo.get_counterparty(t.counterparty_id)
        if cp is None:
            return [f"Unknown counterparty '{t.counterparty_id}'"]
        if not cp.active:
            errors.append(f"Counterparty '{cp.name}' is suspended")
        if t.quantity <= 0:
            errors.append("Quantity must be positive")
        if t.price <= 0:
            errors.append("Price must be positive")
        if t.instrument not in self.prices:
            errors.append(f"No market price for '{t.instrument}'")
        if t.settlement_date < t.trade_date:
            errors.append("Settlement date cannot be before trade date")
        return errors

    def _counterparty(self, cp_id: str) -> Counterparty:
        cp = self.repo.get_counterparty(cp_id)
        if cp is None:
            raise PlatformError(f"Unknown counterparty '{cp_id}'")
        return cp

    def _trade(self, trade_id: int) -> Trade:
        t = self.repo.get_trade(trade_id)
        if t is None:
            raise PlatformError(f"Trade {trade_id} not found")
        return t
