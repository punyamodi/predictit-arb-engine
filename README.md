# PredictIt Arb Engine

A Python engine that scans [PredictIt](https://www.predictit.org) markets for risk-free arbitrage opportunities using linear programming.

## How It Works

In a mutually exclusive market with N candidates, exactly one wins. Buying "NO" on every candidate guarantees a payout from N-1 losing contracts. When the total cost of the NO portfolio is low enough, the net payout after fees exceeds the investment regardless of outcome.

### Arbitrage Detection Pipeline

```mermaid
flowchart TD
    A([Start]) --> B[Fetch PredictIt API]
    B --> C{Cache valid?}
    C -->|Yes| D[Return cached data]
    C -->|No| E[HTTP GET with retry]
    E --> F[Store in cache]
    F --> D
    D --> G[Parse markets and contracts]
    G --> H{Market status = Open?}
    H -->|No| I[Skip]
    H -->|Yes| J{At least 2 NO prices?}
    J -->|No| I
    J -->|Yes| K[Solve LP — maximize min-profit]
    K --> L{LP feasible and pi > 0?}
    L -->|No| M[Near-miss candidate]
    L -->|Yes| N[Integer scale search]
    N --> O{Guaranteed profit > threshold?}
    O -->|No| M
    O -->|Yes| P[Record opportunity]
    P --> Q([Output results])
    M --> Q
```

### Buy-All-NO Strategy

```mermaid
flowchart LR
    subgraph Market ["Election Market  (N candidates)"]
        C1["Candidate A  NO @ $0.60"]
        C2["Candidate B  NO @ $0.60"]
        C3["Candidate C  NO @ $0.60"]
    end

    subgraph Portfolio ["Your Portfolio"]
        B1["Buy q₁ NO shares"]
        B2["Buy q₂ NO shares"]
        B3["Buy q₃ NO shares"]
    end

    subgraph Outcome ["Any Outcome (e.g. A wins)"]
        W["A wins → NO(A) pays $0"]
        L1["B loses → NO(B) pays $1"]
        L2["C loses → NO(C) pays $1"]
    end

    C1 --> B1
    C2 --> B2
    C3 --> B3
    B1 --> W
    B2 --> L1
    B3 --> L2
    L1 --> P["Net Payout > Investment"]
    L2 --> P
```

### Fee Model

```
Gross payout per winning share  =  $1.00
Fee (10% of profit)             =  0.10 × (1 - price)
Net payout per winning share    =  1 - 0.10 × (1 - price)

Example at price $0.60:
  Net payout = 1 - 0.10 × 0.40 = $0.96
```

### LP Formulation

```mermaid
block-beta
  columns 3
  OBJ["Maximize π"]:3
  C1["Profit_j ≥ π   ∀ j"]:3
  C2["Σ qᵢ · pᵢ = 100  (normalise)"]:3
  C3["qᵢ ≥ 0"]:3
```

### Module Architecture

```mermaid
graph TD
    CLI["main.py  CLI"] --> DAT["data.py  fetch + cache"]
    CLI --> ENG["engine.py  LP + integer search"]
    CLI --> ANA["analysis.py  near-misses"]
    CLI --> REP["reporter.py  console / JSON / CSV"]
    DAT --> API["PredictIt REST API"]
    ENG --> LP["PuLP  CBC solver"]
    DAT --> MDL["models.py  typed dataclasses"]
    ENG --> MDL
    ANA --> MDL
    REP --> MDL
    CLI --> CFG["config.py  Config dataclass"]
    ENG --> CFG
    DAT --> CFG
```

## Sample Output

```
Markets: 142 open / 148 total  |  Contracts: 891

============================================================
  Found 2 Arbitrage Opportunities
============================================================

[1] Who will win the 2026 Senate seat in Ohio?
    Strategy  : Buy All No
    Investment: $284.00
    Profit    : $16.40
    ROI       : 5.77%
    Orders:
      Buy   80 NO  'Candidate A'  @ $0.55  (cost: $44.00)
      Buy  107 NO  'Candidate B'  @ $0.75  (cost: $80.25)
      Buy  188 NO  'Candidate C'  @ $0.85  (cost: $159.80)
------------------------------------------------------------
```

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

| Flag | Default | Description |
|------|---------|-------------|
| `--fee RATE` | `0.10` | Platform fee rate applied to profits |
| `--budget USD` | `850` | Maximum investment per opportunity in dollars |
| `--limit N` | `10` | Number of top opportunities to display |
| `--near-misses N` | `5` | Near-miss markets shown when no opportunities found |
| `--export-json PATH` | — | Export results to a JSON file |
| `--export-csv PATH` | — | Export results to a CSV file |
| `--no-cache` | off | Bypass the in-memory API response cache |
| `--timeout SECS` | `30` | API request timeout in seconds |
| `--retries N` | `3` | Maximum API retry attempts with exponential backoff |
| `--log-level LEVEL` | `WARNING` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

**Examples:**

```bash
python main.py --budget 500 --export-json results.json
python main.py --log-level INFO --near-misses 10
python main.py --no-cache --export-csv trades.csv
```

## Project Structure

```
predictit_arbitrage/
    config.py       Configuration dataclass with all tunable parameters
    models.py       Typed dataclasses — Contract, Market, TradeOrder, ArbitrageOpportunity, NearMiss
    data.py         API client with exponential-backoff retry and TTL caching
    engine.py       LP solver (PuLP CBC) and integer scale search
    analysis.py     Near-miss ranking and market summary statistics
    reporter.py     Console tables and JSON / CSV export
main.py             CLI entry point (argparse)
demo.py             Offline sample demo — no network required
```

## Limitations

- PredictIt's 10% fee significantly compresses margins; genuine arbitrage is rare in efficient markets.
- Trade execution is manual; prices may slip between scan time and order placement.
- PredictIt imposes an $850 position limit per contract.

