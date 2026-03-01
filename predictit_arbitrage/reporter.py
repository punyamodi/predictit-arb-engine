import csv
import json
import sys
from dataclasses import asdict
from typing import TextIO

from .models import ArbitrageOpportunity, NearMiss


def _line(width: int = 60) -> str:
    return "-" * width


def _header(title: str, width: int = 60) -> str:
    return f"{'=' * width}\n  {title}\n{'=' * width}"


def print_opportunities(
    opportunities: list,
    limit: int = 10,
    stream: TextIO = sys.stdout,
) -> None:
    if not opportunities:
        stream.write("No arbitrage opportunities found in current live markets.\n")
        return

    stream.write(_header(f"Found {len(opportunities)} Arbitrage Opportunities") + "\n\n")

    for i, opp in enumerate(opportunities[:limit], start=1):
        stream.write(f"[{i}] {opp.market_name}\n")
        stream.write(f"    Strategy  : {opp.strategy.replace('_', ' ').title()}\n")
        stream.write(f"    Investment: ${opp.investment:.2f}\n")
        stream.write(f"    Profit    : ${opp.guaranteed_profit:.2f}\n")
        stream.write(f"    ROI       : {opp.roi_percent:.2f}%\n")
        if opp.market_url:
            stream.write(f"    URL       : {opp.market_url}\n")
        stream.write("    Orders:\n")
        for order in opp.orders:
            stream.write(
                f"      Buy {order.quantity:4d} NO  '{order.contract_name}'"
                f"  @ ${order.price:.2f}  (cost: ${order.cost:.2f})\n"
            )
        stream.write(_line() + "\n")

    stream.write("\n")


def print_near_misses(
    near_misses: list,
    limit: int = 5,
    stream: TextIO = sys.stdout,
) -> None:
    if not near_misses:
        return

    count = min(limit, len(near_misses))
    stream.write(_header(f"Top {count} Near-Miss Markets (closest to profitability)") + "\n\n")

    for nm in near_misses[:limit]:
        stream.write(f"  {nm.market_name}\n")
        stream.write(
            f"    Raw margin: ${nm.raw_margin:+.4f}  |  "
            f"Sum NO prices: ${nm.sum_prices:.4f}  |  "
            f"Contracts: {nm.contract_count}\n"
        )

    stream.write("\n")


def print_summary(summary: dict, stream: TextIO = sys.stdout) -> None:
    stream.write(
        f"Markets: {summary['open_markets']} open / {summary['total_markets']} total  |  "
        f"Contracts: {summary['total_contracts']}\n\n"
    )


def export_json(opportunities: list, path: str) -> None:
    records = [asdict(opp) for opp in opportunities]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2)


def export_csv(opportunities: list, path: str) -> None:
    rows = []
    for opp in opportunities:
        for order in opp.orders:
            rows.append(
                {
                    "market_id": opp.market_id,
                    "market_name": opp.market_name,
                    "strategy": opp.strategy,
                    "investment": opp.investment,
                    "guaranteed_profit": opp.guaranteed_profit,
                    "roi_percent": opp.roi_percent,
                    "contract_name": order.contract_name,
                    "price": order.price,
                    "quantity": order.quantity,
                    "cost": order.cost,
                    "timestamp": opp.timestamp,
                }
            )

    if not rows:
        return

    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
