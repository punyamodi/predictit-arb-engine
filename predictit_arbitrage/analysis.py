from .models import Market, NearMiss


def compute_near_misses(markets: list) -> list:
    results = []

    for market in markets:
        if market.status != "Open":
            continue

        prices = [
            c.best_buy_no
            for c in market.contracts
            if c.status == "Open" and c.best_buy_no is not None
        ]

        if len(prices) < 2:
            continue

        n = len(prices)
        total = sum(prices)
        raw_margin = (n - 1) - total

        results.append(
            NearMiss(
                market_id=market.market_id,
                market_name=market.name,
                raw_margin=round(raw_margin, 4),
                sum_prices=round(total, 4),
                contract_count=n,
                strategy="buy_all_no",
            )
        )

    results.sort(key=lambda x: x.raw_margin, reverse=True)
    return results


def market_summary(markets: list) -> dict:
    open_markets = [m for m in markets if m.status == "Open"]
    total_contracts = sum(len(m.contracts) for m in open_markets)
    return {
        "total_markets": len(markets),
        "open_markets": len(open_markets),
        "total_contracts": total_contracts,
    }
