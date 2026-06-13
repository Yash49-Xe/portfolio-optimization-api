import sqlite3
import pandas as pd
import numpy as np
from scipy.optimize import minimize

DB_PATH = "wealth.db"
FALLBACK_RISK_FREE_RATE = 0.02

def _get_risk_free_rate(conn: sqlite3.Connection) -> float:
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS treasury_rates (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                date      TEXT    NOT NULL UNIQUE,
                rate_10yr REAL    NOT NULL
            )
        """)
        conn.commit()
        cursor.execute("SELECT rate_10yr FROM treasury_rates ORDER BY date DESC LIMIT 1")
        row = cursor.fetchone()
        cursor.close()

        if row is not None:
            rate = float(row[0]) / 100  # FMP returns percent (e.g. 4.35), convert to decimal
            print(f"[OPTIMIZER] Using live risk-free rate: {rate:.4f} ({rate*100:.2f}%)")
            return rate
        else:
            print(f"[OPTIMIZER] No treasury rate in DB. Using fallback: {FALLBACK_RISK_FREE_RATE}")
            return FALLBACK_RISK_FREE_RATE

    except Exception as e:
        print(f"[OPTIMIZER WARNING] Could not read treasury rate: {e}. Using fallback.")
        return FALLBACK_RISK_FREE_RATE

def _calculate_metrics(
    weights: np.ndarray,
    mean_returns: pd.Series,
    cov_matrix: pd.DataFrame
) -> tuple[float, float]:
    """Return (annualised portfolio return, annualised portfolio std dev)."""
    p_return = float(np.sum(mean_returns * weights))
    p_risk   = float(np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))))
    return p_return, p_risk

def _negative_sharpe(
    weights: np.ndarray,
    mean_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    risk_free_rate: float
) -> float:
    p_return, p_risk = _calculate_metrics(weights, mean_returns, cov_matrix)

    if p_risk == 0:
        return 0.0

    return -(p_return - risk_free_rate) / p_risk

def run_optimization() -> dict:
    print("[OPTIMIZER] Loading market data from SQLite...")

    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query("SELECT date, ticker, price FROM market_data", conn)

    if df.empty:
        conn.close()
        raise ValueError(
            "Market data table is empty. "
            "Wait for the background sync worker to finish its first fetch from FMP."
        )

    risk_free_rate = _get_risk_free_rate(conn)
    conn.close()

    df = df.drop_duplicates(subset=["date", "ticker"], keep="last")

    df_pivot = df.pivot(index="date", columns="ticker", values="price").sort_index()

    min_rows = 30
    df_pivot = df_pivot.dropna(thresh=min_rows, axis=1)

    if df_pivot.shape[1] < 2:
        raise ValueError(
            "Not enough tickers with sufficient history to build a portfolio. "
            f"Need at least 2 tickers with {min_rows}+ rows each."
        )
    
    df_pivot = df_pivot.dropna()

    if len(df_pivot) < 2:
        raise ValueError(
            "Not enough date rows after cleaning. "
            "Ensure the sync worker has fetched overlapping historical data for all tickers."
        )

    returns = df_pivot.pct_change().dropna()

    if returns.empty:
        raise ValueError("Return calculation produced an empty DataFrame. Check price data integrity.")

    mean_returns = returns.mean() * 252
    cov_matrix   = returns.cov()  * 252
    num_assets   = len(mean_returns)

    print(f"[OPTIMIZER] Running SLSQP optimisation on {num_assets} assets "
          f"using {len(returns)} trading days of data.")

    constraints = [{"type": "eq", "fun": lambda x: np.sum(x) - 1}]
    bounds      = tuple((0.0, 1.0) for _ in range(num_assets))
    initial_guess = [1.0 / num_assets] * num_assets

    result = minimize(
        _negative_sharpe,
        initial_guess,
        args=(mean_returns, cov_matrix, risk_free_rate),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-9}
    )

    if not result.success:
        raise RuntimeError(
            f"SLSQP optimisation failed to converge: {result.message}. "
            "Try with more historical data or a different asset universe."
        )

    opt_weights = result.x
    opt_return, opt_risk = _calculate_metrics(opt_weights, mean_returns, cov_matrix)
    sharpe = (opt_return - risk_free_rate) / opt_risk if opt_risk > 0 else 0.0

    allocation = {
        ticker: round(float(weight) * 100, 2)
        for ticker, weight in zip(df_pivot.columns, opt_weights)
        if weight > 0.01
    }

    return {
        "risk_free_rate_used_percent": round(risk_free_rate * 100, 4),
        "expected_annual_return_percent": round(opt_return * 100, 2),
        "annual_risk_percent": round(opt_risk * 100, 2),
        "sharpe_ratio": round(sharpe, 4),
        "num_assets_in_universe": num_assets,
        "num_trading_days_used": len(returns),
        "optimal_allocation_percent": allocation,
    }