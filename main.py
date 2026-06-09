import asyncio
from fastapi import FastAPI
from optimizer import run_optimization
from fetch_real_data import update_market_data

app = FastAPI(title="Wealth Optimization API")

async def scheduled_sync():
    while True:
        update_market_data()
        
        await asyncio.sleep(3600)

@app.on_event("startup")
async def startup_event():
    print("Starting up Background Sync Worker...")
    asyncio.create_task(scheduled_sync())

@app.get("/")
def home():
    return {"message": "Wealth Optimization Engine is running."}

@app.get("/api/v1/optimize")
def get_optimal_portfolio():
    try:
        results = run_optimization()
        return {"status": "success", "data": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}