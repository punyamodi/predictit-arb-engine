import logging
from datetime import datetime, timezone
from typing import Optional

import pulp

from .config import Config
from .models import ArbitrageOpportunity, Market, TradeOrder

logger = logging.getLogger(__name__)


def _net_payout(price: float, fee: float) -> float:
    return 1.0 - fee * (1.0 - price)


def _solve_lp_no(prices: list, fee: float) -> Optional[list]:
    n = len(prices)
    net = [_net_payout(p, fee) for p in prices]

    prob = pulp.LpProblem("no_arb", pulp.LpMaximize)
    q = [pulp.LpVariable(f"q{i}", lowBound=0) for i in range(n)]
    pi = pulp.LpVariable("pi")

    investment = pulp.lpSum(q[i] * prices[i] for i in range(n))

    prob += pi
    for j in range(n):
        revenue_j = pulp.lpSum(q[i] * net[i] for i in range(n) if i != j)
        prob += (revenue_j - investment) >= pi
    prob += investment == 100.0

    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))

    if status != 1 or pulp.value(pi) <= 0:
        return None
    return [pulp.value(v) for v in q]


def _best_integer_solution(
    fractions: list,
    prices: list,
    fee: float,
    max_budget: float,
    max_scale: int,
    min_profit: float,
) -> Optional[dict]:
    n = len(prices)
    net = [_net_payout(p, fee) for p in prices]
    best = None

    for scale in range(1, max_scale + 1):
        for mode in ("round", "ceil", "floor"):
            if mode == "round":
                q_int = [int(round(x * scale)) for x in fractions]
            elif mode == "ceil":
                q_int = [int(x * scale + 0.999) for x in fractions]
            else:
                q_int = [int(x * scale) for x in fractions]

            if min(q_int) <= 0:
                continue

            investment = sum(q_int[i] * prices[i] for i in range(n))
            if investment <= 0 or investment > max_budget:
                continue

            profits = [
                sum(q_int[i] * net[i] for i in range(n) if i != j) - investment
                for j in range(n)
            ]
            guaranteed = min(profits)

            if guaranteed > min_profit:
                roi = guaranteed / investment
                if best is None or roi > best["roi"]:
                    best = {
                        "quantities": q_int,
                        "investment": round(investment, 2),
                        "guaranteed_profit": round(guaranteed, 2),
                        "roi": roi,
                        "roi_percent": round(roi * 100, 2),
                    }

    return best


def find_arbitrage_no(market: Market, config: Config) -> Optional[ArbitrageOpportunity]:
    eligible = [
        c for c in market.contracts
        if c.status == "Open" and c.best_buy_no is not None
    ]
    if len(eligible) < 2:
        return None

    prices = [c.best_buy_no for c in eligible]
    fractions = _solve_lp_no(prices, config.fee_rate)
    if fractions is None:
        return None

    result = _best_integer_solution(
        fractions,
        prices,
        config.fee_rate,
        config.max_budget,
        config.max_scale,
        config.min_profit_threshold,
    )
    if result is None:
        return None

    orders = [
        TradeOrder(
            contract_name=eligible[i].contract_name,
            price=prices[i],
            quantity=result["quantities"][i],
            cost=round(prices[i] * result["quantities"][i], 2),
        )
        for i in range(len(eligible))
        if result["quantities"][i] > 0
    ]

    return ArbitrageOpportunity(
        market_id=market.market_id,
        market_name=market.name,
        market_url=market.url,
        investment=result["investment"],
        guaranteed_profit=result["guaranteed_profit"],
        roi_percent=result["roi_percent"],
        orders=orders,
        strategy="buy_all_no",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def scan_all_markets(markets: list, config: Config) -> list:
    open_markets = [m for m in markets if m.status == "Open"]
    logger.info("Scanning %d open markets", len(open_markets))

    opportunities = []
    for market in open_markets:
        opp = find_arbitrage_no(market, config)
        if opp:
            logger.info("Opportunity in '%s': ROI=%.2f%%", market.name, opp.roi_percent)
            opportunities.append(opp)

    opportunities.sort(key=lambda x: x.roi_percent, reverse=True)
    logger.info("Total opportunities found: %d", len(opportunities))
    return opportunities
