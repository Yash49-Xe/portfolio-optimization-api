# Automated Wealth & Portfolio Optimization API

A high-performance, asynchronous backend microservice designed to ingest real-time market data and mathematically calculate the optimal distribution of capital. It maximizes financial returns while minimizing risk using the Sharpe Ratio.

Built with **FastAPI**, this engine utilizes an automated background worker to sync live market data into a localized **SQLite** database. The core mathematical engine leverages **Pandas** for financial metric extraction and **SciPy**'s SLSQP optimization algorithm to dynamically balance a multi-asset portfolio.

---

## System Architecture

This system solves the external API latency problem by completely decoupling data ingestion from API requests, keeping response times under 5 milliseconds.

1. **Async Worker (`fetch_real_data.py`):** An `asyncio` background loop wakes up on a set interval, securely pulls thousands of rows of live daily closing prices via the Yahoo Finance API, and updates the local database.
2. **Stateful Storage (`wealth.db`):** A local SQLite database that stores historical time-series data.
3. **Quantitative Engine (`optimizer.py`):** Uses Pandas and NumPy to calculate historical volatility and expected returns, feeding a covariance matrix into a SciPy minimization algorithm to find the peak of the Efficient Frontier.
4. **Gateway (`main.py`):** A FastAPI server that executes the pipeline and serves the optimal portfolio allocation.

---

## Tech Stack

| Category | Libraries / Tools |
|---|---|
| Framework | FastAPI, Uvicorn |
| Database | SQLite3 |
| Data Engineering | Pandas, NumPy |
| Mathematical Optimization | SciPy |
| Market Data Ingestion | yfinance |

---

## Project Structure

```text
automated-wealth-api/
│
├── main.py                # FastAPI app & background sync worker
├── optimizer.py           # SciPy optimization engine & Sharpe ratio calculations
├── fetch_real_data.py     # Yahoo Finance data ingestion script
├── requirements.txt       # Project dependencies
├── .gitignore             # Excludes local DB and virtual environments
└── README.md              # Project documentation
```

> `wealth.db` is automatically generated on server boot and is excluded from version control via `.gitignore`.

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

### 3. Start the server

The background `asyncio` worker runs automatically on startup — no manual database initialization is required. It will download historical data, build the SQLite database, and open the API.

```bash
python -m uvicorn main:app --reload
```

---

## API Usage

Once the server is running, navigate to `http://127.0.0.1:8000/docs` for the interactive Swagger UI, or send a `GET` request directly to the endpoint.

**Endpoint:** `GET /api/v1/optimize`

**Sample Response:**

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
      "PG": 23.09,
      "WMT": 21.52
    }
  }
}
```

---

## Configuration

By default, the background worker in `main.py` uses `asyncio.sleep(300)` (1-minute intervals) for rapid local testing. For production deployments, it is recommended to increase this interval — for example, `21600` (6 hours) — to avoid rate-limiting from the Yahoo Finance API.