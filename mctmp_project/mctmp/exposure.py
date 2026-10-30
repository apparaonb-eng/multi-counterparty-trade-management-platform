"""Credit exposure calculation per counterparty.

exposure = current replacement cost + potential future add-on - collateral
- With a netting agreement, trade MTMs are summed first (floored at zero).
- Without netting, only positive MTMs count (gains are not offset by losses).
- Add-on is a flat percentage of open notional.
"""
from typing import Dict, List

from .models import Counterparty, Trade

ADDON_RATE = 0.05


def trade_mtm(trade: Trade, prices: Dict[str, float]) -> float:
    """Mark-to-market gain (+) or loss (-) from our point of view."""
    return trade.sign * trade.quantity * (prices[trade.instrument] - trade.price)


def exposure_breakdown(cp: Counterparty, open_trades: List[Trade], prices: Dict[str, float]) -> dict:
    mtms = [trade_mtm(t, prices) for t in open_trades]
    gross_positive = sum(m for m in mtms if m > 0)
    net_mtm = sum(mtms)
    current = max(net_mtm, 0.0) if cp.netting_agreement else gross_positive
    addon = ADDON_RATE * sum(t.notional for t in open_trades)
    exposure = max(current + addon - cp.collateral_held, 0.0)
    return {
        "open_trades": len(open_trades),
        "net_mtm": net_mtm,
        "current_exposure": current,
        "addon": addon,
        "collateral": cp.collateral_held,
        "exposure": exposure,
    }


def counterparty_exposure(cp: Counterparty, open_trades: List[Trade], prices: Dict[str, float]) -> float:
    return exposure_breakdown(cp, open_trades, prices)["exposure"]
