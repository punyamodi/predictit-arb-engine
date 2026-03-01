from dataclasses import dataclass


@dataclass
class Config:
    api_url: str = "https://www.predictit.org/api/marketdata/all/"
    fee_rate: float = 0.10
    max_budget: float = 850.0
    max_scale: int = 850
    min_profit_threshold: float = 0.01
    request_timeout: int = 30
    max_retries: int = 3
    cache_ttl_seconds: int = 300
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
