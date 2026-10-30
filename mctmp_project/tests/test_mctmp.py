import unittest
from datetime import date

from mctmp.manager import PlatformError, TradeManager
from mctmp.models import Counterparty, Side, Status
from mctmp.repository import Repository

TODAY = date(2026, 10, 30)
LATER = date(2026, 12, 1)


def make_mgr(netting=False, limit=100_000):
    mgr = TradeManager(Repository(), {"AAPL": 190.0, "MSFT": 420.0}, TODAY)
    mgr.add_counterparty(Counterparty("CP1", "Test Bank", "A", limit, netting_agreement=netting))
    return mgr


class MctmpTests(unittest.TestCase):
    def test_trade_within_limit_is_approved(self):
        t = make_mgr().submit_trade("CP1", "AAPL", Side.BUY, 100, 190.0, LATER)
        self.assertEqual(t.status, Status.APPROVED)

    def test_trade_over_limit_is_rejected(self):
        t = make_mgr(limit=500).submit_trade("CP1", "AAPL", Side.BUY, 100, 190.0, LATER)
        self.assertEqual(t.status, Status.REJECTED)
        self.assertIn("Credit limit", t.reason)

    def test_unknown_counterparty_rejected(self):
        t = make_mgr().submit_trade("NOPE", "AAPL", Side.BUY, 1, 190.0, LATER)
        self.assertEqual(t.status, Status.REJECTED)

    def test_suspended_counterparty_rejected(self):
        mgr = make_mgr()
        mgr.suspend_counterparty("CP1")
        self.assertEqual(mgr.submit_trade("CP1", "AAPL", Side.BUY, 1, 190.0, LATER).status, Status.REJECTED)

    def test_netting_reduces_exposure(self):
        # long AAPL (+gain) and short MSFT (-loss) offset when netting applies
        results = {}
        for netting in (False, True):
            mgr = make_mgr(netting=netting, limit=10**9)
            mgr.submit_trade("CP1", "AAPL", Side.BUY, 1000, 180.0, LATER)   # +10,000
            mgr.submit_trade("CP1", "MSFT", Side.BUY, 1000, 430.0, LATER)   # -10,000
            results[netting] = mgr.exposure("CP1")
        self.assertLess(results[True], results[False])

    def test_collateral_reduces_exposure(self):
        mgr = make_mgr(limit=10**9)
        mgr.submit_trade("CP1", "AAPL", Side.BUY, 1000, 180.0, LATER)
        before = mgr.exposure("CP1")
        mgr.post_collateral("CP1", 5_000)
        self.assertAlmostEqual(before - mgr.exposure("CP1"), 5_000)

    def test_settle_and_cancel_rules(self):
        mgr = make_mgr()
        due = mgr.submit_trade("CP1", "AAPL", Side.BUY, 10, 190.0, TODAY)
        cash = mgr.settle_due_trades()
        self.assertAlmostEqual(cash[due.trade_id], -1900.0)
        with self.assertRaises(PlatformError):
            mgr.cancel_trade(due.trade_id)


if __name__ == "__main__":
    unittest.main()
