import argparse
import logging
import sys

from predictit_arbitrage.analysis import compute_near_misses, market_summary
from predictit_arbitrage.config import Config
from predictit_arbitrage.data import fetch_market_data, parse_markets
from predictit_arbitrage.engine import scan_all_markets
from predictit_arbitrage.reporter import (
    export_csv,
    export_json,
    print_near_misses,
    print_opportunities,
    print_summary,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="predictit-arbitrage",
        description="Scan PredictIt markets for risk-free arbitrage using linear programming.",
    )
    parser.add_argument(
        "--fee",
        type=float,
        default=0.10,
        metavar="RATE",
        help="Platform fee rate applied to profits (default: 0.10)",
    )
    parser.add_argument(
        "--budget",
        type=float,
        default=850.0,
        metavar="USD",
        help="Maximum investment budget in dollars (default: 850)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        metavar="N",
        help="Number of top opportunities to display (default: 10)",
    )
    parser.add_argument(
        "--near-misses",
        type=int,
        default=5,
        metavar="N",
        dest="near_misses",
        help="Near-miss markets to show when no opportunities are found (default: 5)",
    )
    parser.add_argument(
        "--export-json",
        metavar="PATH",
        dest="export_json",
        help="Export results to a JSON file",
    )
    parser.add_argument(
        "--export-csv",
        metavar="PATH",
        dest="export_csv",
        help="Export results to a CSV file",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        dest="no_cache",
        help="Bypass in-memory response cache",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        metavar="SECS",
        help="API request timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        metavar="N",
        help="Maximum API retry attempts (default: 3)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="WARNING",
        dest="log_level",
        help="Logging verbosity (default: WARNING)",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    config = Config(
        fee_rate=args.fee,
        max_budget=args.budget,
        request_timeout=args.timeout,
        max_retries=args.retries,
        cache_ttl_seconds=0 if args.no_cache else 300,
    )

    try:
        raw_data = fetch_market_data(config)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    markets = parse_markets(raw_data)
    summary = market_summary(markets)
    print_summary(summary)

    opportunities = scan_all_markets(markets, config)
    print_opportunities(opportunities, limit=args.limit)

    if not opportunities:
        near_misses = compute_near_misses(markets)
        print_near_misses(near_misses, limit=args.near_misses)

    if args.export_json:
        export_json(opportunities, args.export_json)
        print(f"Exported JSON to {args.export_json}")

    if args.export_csv:
        export_csv(opportunities, args.export_csv)
        print(f"Exported CSV to {args.export_csv}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
