# Automated Wealth & Portfolio Optimization API

A high-performance, asynchronous backend microservice designed to ingest real-time market data and mathematically calculate the optimal distribution of capital. It maximizes financial returns while minimizing risk using the Sharpe Ratio.

Built with **FastAPI**, this engine utilizes an automated background worker to sync live market data from the **Financial Modeling Prep (FMP) API** into a localized **SQLite** database. The core mathematical brain leverages **Pandas** for financial metric extraction and **SciPy**'s SLSQP optimization algorithm to dynamically balance a multi-asset portfolio.

---

## System Architecture

This system solves the "External API Latency" problem by completely decoupling data ingestion from API requests. Client response times remain under 5 milliseconds.

1. **The Async Worker (`fetch_real_data.py`):** An `asyncio` background loop wakes up on a set interval, securely authenticates with the FMP API using environment variables, pulls thousands of rows of intraday/daily closing prices, and updates the local database. It includes automated error handling for rate limits and paywalls.
2. **The Stateful Storage (`wealth.db`):** A highly optimized local SQLite database that stores historical time-series data.
3. **The Quantitative Engine (`optimizer.py`):** Uses Pandas and NumPy to calculate historical volatility and expected returns, feeding a covariance matrix into a SciPy minimization algorithm to find the peak of the Efficient Frontier.
4. **The Gateway (`main.py`):** A FastAPI server that executes the pipeline and serves the mathematically optimal portfolio allocation.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI, Uvicorn (Async Server) |
| Database | SQLite3 |
| Data Engineering | Pandas, NumPy |
| Mathematical Optimization | SciPy |
| Market Data Ingestion | Financial Modeling Prep (FMP) API via `requests` |
| Security | `python-dotenv` |

---

## Project Structure

```text
automated-wealth-api/
│
├── main.py                # FastAPI app & background sync worker
├── optimizer.py           # SciPy math engine & Sharpe ratio calculus
├── fetch_real_data.py     # FMP API data ingestion script
├── requirements.txt       # Environment dependencies
├── .gitignore             # Secures local DB and virtual environments
└── README.md              # Project documentation
```

> **Note:** `wealth.db` and `.env` are intentionally excluded from version control to protect local state and private API keys.

---

## Quick Start

Follow these steps to clone the repository, configure your API keys, and boot the live optimization server.

### 1. Clone the repository

```bash
git clone https://github.com/Yash49-Xe/automated-wealth-api.git
cd automated-wealth-api
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

This API requires a free API key from [Financial Modeling Prep](https://financialmodelingprep.com/). Create a file named `.env` in the root directory and add your key:

```
FMP_API_KEY=your_actual_api_key_here
```

### 4. Start the server

The architecture includes an automated `asyncio` background worker — no manual database setup is required. On startup, the worker authenticates with FMP, downloads historical data, builds the SQLite database, and opens the API.

```bash
python -m uvicorn main:app --reload
```

---

## API Usage

Once the server is running, navigate to `http://127.0.0.1:8000/docs` for the interactive Swagger UI, or send a `GET` request directly to the endpoint.

### Endpoint

```
GET /api/v1/optimize
```

### Sample Response

```json
{
  "status": "success",
  "data": {
    "expected_annual_return_percent": 25.01,
    "annual_risk_percent": 14.55,
    "sharpe_ratio": 1.58,
    "optimal_allocation": {
      "AAPL": 1.82,
      "GOOGL": 22.20,
      "JPM": 31.37,
      "WMT": 21.52
    }
  }
}
```

---

## Configuration & Rate Limits

By default, the background worker in `main.py` may be set to a fast refresh rate for local testing.

> **Important:** FMP's Free Tier enforces a strict limit of **250 API calls per day**.

If deploying to a live cloud server running continuously, it is strongly recommended to increase the `asyncio.sleep()` interval in `main.py` to prevent IP rate-limiting. Suggested values:

| Interval | Value |
|---|---|
| 1 hour | `3600` |
| 6 hours | `21600` |