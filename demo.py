import sys

from predictit_arbitrage.config import Config
from predictit_arbitrage.engine import find_arbitrage_no
from predictit_arbitrage.models import Contract, Market
from predictit_arbitrage.reporter import print_opportunities


def run_sample_demo() -> int:
    config = Config()

    sample_data = [
        ("Candidate A", 0.60),
        ("Candidate B", 0.60),
        ("Candidate C", 0.60),
    ]

    contracts = [
        Contract(
            contract_id=i,
            contract_name=name,
            short_name=name,
            status="Open",
            last_trade_price=price,
            best_buy_yes=1.0 - price,
            best_buy_no=price,
            best_sell_yes=None,
            best_sell_no=None,
            last_close_price=price,
            date_end=None,
        )
        for i, (name, price) in enumerate(sample_data)
    ]

    market = Market(
        market_id=1,
        name="Sample Election (Offline Demo)",
        status="Open",
        url="",
        contracts=contracts,
    )

    opp = find_arbitrage_no(market, config)

    if opp:
        print_opportunities([opp])
        return 0

    print("No arbitrage opportunity found for sample data.")
    return 1


if __name__ == "__main__":
    sys.exit(run_sample_demo())
