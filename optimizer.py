import sqlite3
import pandas as pd
import numpy as np
from scipy.optimize import minimize

print("Loading data from SQLite...")
conn = sqlite3.connect("wealth.db")
df = pd.read_sql_query("SELECT * FROM market_data", conn)
conn.close()

df_pivot = df.pivot(index="date", columns="ticker", values="price")

returns = df_pivot.pct_change().dropna()

mean_returns = returns.mean() * 252
cov_matrix = returns.cov() * 252

def calculate_metrics(weights, mean_returns, cov_matrix):
    p_return = np.sum(mean_returns * weights)
    p_risk = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    return p_return, p_risk

def negative_sharpe_ratio(weights, mean_returns, cov_matrix, risk_free_rate=0.02):
    p_return, p_risk = calculate_metrics(weights, mean_returns, cov_matrix)
    return - (p_return - risk_free_rate) / p_risk

def run_optimization():
    num_assets = len(mean_returns)
    args = (mean_returns, cov_matrix)
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0, 1) for asset in range(num_assets))
    initial_guess = num_assets * [1. / num_assets]

    result = minimize(negative_sharpe_ratio, initial_guess, args=args,
                      method='SLSQP', bounds=bounds, constraints=constraints)

    allocation = {}
    for ticker, weight in zip(df_pivot.columns, result.x):
        if weight > 0.01:
            allocation[ticker] = round(weight * 100, 2)
            
    opt_return, opt_risk = calculate_metrics(result.x, mean_returns, cov_matrix)
    
    return {
        "expected_annual_return_percent": round(opt_return * 100, 2),
        "annual_risk_percent": round(opt_risk * 100, 2),
        "sharpe_ratio": round((opt_return - 0.02) / opt_risk, 2),
        "optimal_allocation(in %)": allocation
    }