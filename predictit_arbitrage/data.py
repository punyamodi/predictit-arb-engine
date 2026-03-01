import logging
import time
from datetime import datetime, timezone
from typing import Optional

import requests

from .config import Config
from .models import Contract, Market

logger = logging.getLogger(__name__)

_cache: dict = {}


def _cache_valid(key: str, ttl: int) -> bool:
    if key not in _cache or ttl == 0:
        return False
    age = (datetime.now(timezone.utc) - _cache[key]["at"]).total_seconds()
    return age < ttl


def fetch_market_data(config: Config) -> dict:
    key = "market_data"
    if _cache_valid(key, config.cache_ttl_seconds):
        logger.debug("Returning cached market data")
        return _cache[key]["data"]

    headers = {
        "User-Agent": config.user_agent,
        "Accept": "application/json",
    }

    last_exc: Optional[Exception] = None
    for attempt in range(1, config.max_retries + 1):
        try:
            logger.info("Fetching market data attempt %d/%d", attempt, config.max_retries)
            resp = requests.get(config.api_url, headers=headers, timeout=config.request_timeout)
            resp.raise_for_status()
            data = resp.json()
            _cache[key] = {"data": data, "at": datetime.now(timezone.utc)}
            logger.info("Fetched %d markets", len(data.get("markets", [])))
            return data
        except requests.RequestException as exc:
            last_exc = exc
            logger.warning("Attempt %d failed: %s", attempt, exc)
            if attempt < config.max_retries:
                time.sleep(2**attempt)

    raise RuntimeError(
        f"Failed to fetch market data after {config.max_retries} attempts: {last_exc}"
    )


def parse_markets(data: dict) -> list:
    if "markets" not in data:
        raise ValueError("Unexpected API response: 'markets' key not found")

    markets = []
    for raw in data["markets"]:
        contracts = [
            Contract(
                contract_id=c["id"],
                contract_name=c["name"],
                short_name=c.get("shortName", ""),
                status=c.get("status", ""),
                last_trade_price=c.get("lastTradePrice"),
                best_buy_yes=c.get("bestBuyYesCost"),
                best_buy_no=c.get("bestBuyNoCost"),
                best_sell_yes=c.get("bestSellYesCost"),
                best_sell_no=c.get("bestSellNoCost"),
                last_close_price=c.get("lastClosePrice"),
                date_end=c.get("dateEnd"),
            )
            for c in raw.get("contracts", [])
        ]
        markets.append(
            Market(
                market_id=raw["id"],
                name=raw["name"],
                status=raw.get("status", ""),
                url=raw.get("url", ""),
                contracts=contracts,
            )
        )
    return markets
