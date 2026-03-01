# PredictIt Arbitrage Engine

A Python engine that scans [PredictIt](https://www.predictit.org) markets for risk-free arbitrage opportunities using linear programming.

## Strategy

In a mutually exclusive market with N candidates, exactly one wins. Buying "NO" on every candidate guarantees a payout from N-1 losing contracts. When the total cost of the NO portfolio is low enough, the net payout after fees exceeds the investment regardless of the outcome.

The engine solves for the optimal share quantities using **linear programming** (via PuLP), then performs an integer search over scaled solutions to find the highest-ROI trade that fits within the position limit.

**Fee model**: PredictIt charges 10% on profits. Net payout per share = `1 - 0.10 * (1 - price)`.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

**Live market scan:**

```bash
python main.py
```

**Offline demo (no network required):**

```bash
python demo.py
```

**CLI options:**

```
--fee RATE          Platform fee rate (default: 0.10)
--budget USD        Max investment budget in dollars (default: 850)
--limit N           Opportunities to display (default: 10)
--near-misses N     Near-miss markets when no opportunities found (default: 5)
--export-json PATH  Export results to JSON
--export-csv PATH   Export results to CSV
--no-cache          Bypass in-memory API response cache
--timeout SECS      API request timeout (default: 30)
--retries N         Max API retry attempts (default: 3)
--log-level LEVEL   DEBUG | INFO | WARNING | ERROR (default: WARNING)
```

**Examples:**

```bash
python main.py --budget 500 --fee 0.10 --export-json results.json
python main.py --log-level INFO --near-misses 10
```

## Project Structure

```
predictit_arbitrage/
    config.py     Configuration dataclass
    models.py     Typed data models
    data.py       API client with retry and caching
    engine.py     LP solver and integer search
    analysis.py   Near-miss analysis and market statistics
    reporter.py   Console, JSON and CSV output
main.py           CLI entry point
demo.py           Offline demo with sample data
```

## Limitations

- PredictIt's 10% fee significantly compresses margins; genuine arbitrage is rare.
- Trade execution is manual; prices may move between scan and placement.
- PredictIt imposes a $850 position limit per contract.

