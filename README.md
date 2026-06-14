# Automated Wealth & Portfolio Optimization API

A high-performance, asynchronous backend microservice that ingests real-time market data and computes the optimal distribution of capital across a multi-asset portfolio. It maximizes risk-adjusted returns using the Sharpe Ratio as the objective function.

Built with **FastAPI**, the engine runs an automated background worker that syncs live market data and treasury rates from the **Financial Modeling Prep (FMP) API** into a local **SQLite** database. The optimization layer uses **Pandas** and **NumPy** for financial metric computation and **SciPy**'s SLSQP algorithm to solve the portfolio allocation problem on the Efficient Frontier.

---

## System Architecture

The system decouples data ingestion from request handling, eliminating external API latency from the critical path. The optimizer reads exclusively from a local database, keeping response times consistently low.

1. **Data Ingestion Worker (`fetch_real_data.py`):** An `asyncio` background task wakes on a 24-hour interval, authenticates with the FMP API via environment variables, pulls historical EOD closing prices for all configured tickers, and upserts the latest 10-year US Treasury rate. All network and parsing errors are handled gracefully without crashing the server.
2. **Stateful Storage (`wealth.db`):** A local SQLite database persisting historical price time-series, treasury rates, and transaction records. WAL journal mode is enabled for concurrent read performance.
3. **Quantitative Engine (`optimizer.py`):** Computes annualized returns and a covariance matrix from daily price data, then minimizes the negative Sharpe Ratio via SciPy's SLSQP algorithm. The risk-free rate is sourced live from the database; a fallback of 2% is used if no rate is available.
4. **API Gateway (`main.py`):** A FastAPI server that offloads the blocking optimization computation to a thread pool via `asyncio.to_thread`, keeping the event loop non-blocking.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI, Uvicorn |
| Database | SQLite3 (WAL mode) |
| Data Engineering | Pandas, NumPy |
| Mathematical Optimization | SciPy (SLSQP) |
| Market Data Ingestion | Financial Modeling Prep (FMP) API via `httpx` |
| Environment Management | `python-dotenv` |

---

## Asset Universe

The following tickers are configured in `fetch_real_data.py` by default:

`AAPL`, `MSFT`, `GOOGL`, `AMZN`, `JPM`, `V`, `WMT`, `SPY`, `BTCUSD`, `ETHUSD`

---

## Project Structure

```text
automated-wealth-api/
│
├── main.py                # FastAPI app, lifespan manager, background sync worker
├── optimizer.py           # SciPy optimization engine, Sharpe ratio computation
├── fetch_real_data.py     # FMP API ingestion: EOD prices and treasury rates
├── setup_db.py            # One-time database schema initialization
├── requirements.txt       # Python dependencies
├── .gitignore             # Excludes wealth.db, .env, and virtual environments
└── README.md              # Project documentation
```

> `wealth.db` and `.env` are intentionally excluded from version control to protect local state and private API keys.

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Yash49-Xe/portfolio-optimization-api.git
cd portfolio-optimization-api
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Obtain a free API key from [Financial Modeling Prep](https://financialmodelingprep.com/). Create a `.env` file in the project root:

```
FMP_API_KEY=your_actual_api_key_here
```

### 4. Initialize the database

Run the setup script once to create `wealth.db` and provision all required tables:

```bash
python setup_db.py
```

### 5. Start the server

```bash
python -m uvicorn main:app --host 0.0.0.0 --reload
```

On startup, the background worker authenticates with FMP, downloads historical EOD price data and the current treasury rate, and populates the database. The `/api/v1/optimize` endpoint becomes meaningful once the first sync cycle completes.

---

## API Usage

The interactive Swagger UI is available at `http://127.0.0.1:8000/docs` once the server is running.

### Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/api/v1/optimize` | Run Sharpe Ratio optimization and return optimal allocation |

### Sample Response

```json
{
  "status": "success",
  "data": {
    "risk_free_rate_used_percent": 4.35,
    "expected_annual_return_percent": 25.01,
    "annual_risk_percent": 14.55,
    "sharpe_ratio": 1.4158,
    "num_assets_in_universe": 10,
    "num_trading_days_used": 252,
    "optimal_allocation_percent": {
      "GOOGL": 22.20,
      "JPM": 31.37,
      "WMT": 21.52,
      "SPY": 24.91
    }
  }
}
```

### Error Responses

| Status | Cause |
|---|---|
| `422` | Market data table is empty or has insufficient history |
| `500` | SLSQP optimizer failed to converge |

---

## Configuration & Rate Limits

The background sync worker runs on a **24-hour interval** (`SYNC_INTERVAL_SECONDS = 86400` in `main.py`).

> **Important:** FMP's Free Tier enforces a limit of **250 API calls per day.** With 10 configured tickers plus one treasury rate call, each sync cycle consumes 11 calls. The default 24-hour interval is safe for continuous deployment.

If you reduce the interval for local testing, ensure you do not exceed the daily quota:

| Interval | Value | Daily cycles |
|---|---|---|
| 24 hours | `86400` | 1 |
| 6 hours | `21600` | 4 |
| 1 hour | `3600` | 24 |