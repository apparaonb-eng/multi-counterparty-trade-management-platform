"""Text reports: trade blotter and counterparty exposure summary."""
from .exposure import exposure_breakdown
from .manager import TradeManager


def blotter(mgr: TradeManager) -> str:
    head = (f"{'ID':<4}{'CP':<7}{'Instr':<7}{'Side':<5}{'Qty':>8}{'Price':>10}"
            f"{'Notional':>14}{'Settle':>12}  {'Status':<10}Reason")
    lines = [head, "-" * 110]
    for t in mgr.repo.trades():
        lines.append(f"{t.trade_id:<4}{t.counterparty_id:<7}{t.instrument:<7}{t.side.value:<5}"
                     f"{t.quantity:>8,.0f}{t.price:>10,.2f}{t.notional:>14,.0f}"
                     f"{t.settlement_date.isoformat():>12}  {t.status.value:<10}{t.reason}")
    return "\n".join(lines)


def counterparty_summary(mgr: TradeManager) -> str:
    head = (f"{'CP':<7}{'Name':<16}{'Rtg':<5}{'Netting':<9}{'Open':>5}{'NetMTM':>12}"
            f"{'Collat':>11}{'Exposure':>12}{'Limit':>12}{'Util%':>7}")
    lines = [head, "-" * len(head)]
    for cp in mgr.repo.counterparties():
        b = exposure_breakdown(cp, mgr.repo.open_trades(cp.cp_id), mgr.prices)
        util = 100 * b["exposure"] / cp.credit_limit if cp.credit_limit else 0.0
        lines.append(f"{cp.cp_id:<7}{cp.name:<16}{cp.rating:<5}{'Yes' if cp.netting_agreement else 'No':<9}"
                     f"{b['open_trades']:>5}{b['net_mtm']:>12,.0f}{b['collateral']:>11,.0f}"
                     f"{b['exposure']:>12,.0f}{cp.credit_limit:>12,.0f}{util:>6.1f}%")
    return "\n".join(lines)
