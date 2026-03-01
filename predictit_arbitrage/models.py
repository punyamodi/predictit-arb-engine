from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Contract:
    contract_id: int
    contract_name: str
    short_name: str
    status: str
    last_trade_price: Optional[float]
    best_buy_yes: Optional[float]
    best_buy_no: Optional[float]
    best_sell_yes: Optional[float]
    best_sell_no: Optional[float]
    last_close_price: Optional[float]
    date_end: Optional[str]


@dataclass
class Market:
    market_id: int
    name: str
    status: str
    url: str
    contracts: list = field(default_factory=list)


@dataclass
class TradeOrder:
    contract_name: str
    price: float
    quantity: int
    cost: float


@dataclass
class ArbitrageOpportunity:
    market_id: int
    market_name: str
    market_url: str
    investment: float
    guaranteed_profit: float
    roi_percent: float
    orders: list
    strategy: str
    timestamp: str


@dataclass
class NearMiss:
    market_id: int
    market_name: str
    raw_margin: float
    sum_prices: float
    contract_count: int
    strategy: str
