"""Demo run of the Multi-Counterparty Trade Management Platform."""
from datetime import date

from mctmp.manager import TradeManager
from mctmp.models import Counterparty, Side
from mctmp.reports import blotter, counterparty_summary
from mctmp.repository import Repository


def main():
    today = date(2026, 10, 30)
    prices = {"AAPL": 190.0, "MSFT": 420.0, "GOLD": 2650.0}
    mgr = TradeManager(Repository(), prices, today)

    mgr.add_counterparty(Counterparty("CP001", "Alpha Bank", "AA", 1_000_000, netting_agreement=True))
    mgr.add_counterparty(Counterparty("CP002", "Beta Fund", "BBB", 30_000, netting_agreement=False))
    mgr.add_counterparty(Counterparty("CP003", "Gamma Corp", "A", 500_000, netting_agreement=True))

    nov, dec = date(2026, 11, 15), date(2026, 12, 15)
    mgr.submit_trade("CP001", "AAPL", Side.BUY, 1_000, 185.0, nov)
    mgr.submit_trade("CP001", "MSFT", Side.SELL, 500, 410.0, dec)
    mgr.submit_trade("CP001", "GOLD", Side.BUY, 100, 2600.0, today)          # due today
    mgr.submit_trade("CP002", "AAPL", Side.BUY, 2_000, 180.0, nov)           # exceeds Beta limit
    mgr.post_collateral("CP002", 20_000)
    mgr.submit_trade("CP002", "AAPL", Side.BUY, 2_000, 180.0, nov)           # OK with collateral
    mgr.submit_trade("CP999", "AAPL", Side.BUY, 10, 190.0, nov)              # unknown counterparty
    mgr.suspend_counterparty("CP003")
    mgr.submit_trade("CP003", "MSFT", Side.BUY, 100, 415.0, nov)             # suspended

    print("=== Trade blotter ===")
    print(blotter(mgr))
    print("\n=== Counterparty exposure ===")
    print(counterparty_summary(mgr))

    print("\n=== Settling due trades ===")
    for trade_id, cash in mgr.settle_due_trades().items():
        print(f"Trade {trade_id} settled, cash flow {cash:,.2f}")

    print("\n=== Counterparty exposure after settlement ===")
    print(counterparty_summary(mgr))


if __name__ == "__main__":
    main()
