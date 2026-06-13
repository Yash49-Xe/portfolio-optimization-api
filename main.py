import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from optimizer import run_optimization
from fetch_real_data import update_market_data

SYNC_INTERVAL_SECONDS = 86400

async def scheduled_sync() -> None:
    while True:
        print("[BACKGROUND WORKER] Starting sync cycle...")
        try:
            await asyncio.to_thread(update_market_data)
        except Exception as e:
            print(f"[BACKGROUND WORKER ERROR] Sync cycle failed: {e}")

        print(f"[BACKGROUND WORKER] Next sync in {SYNC_INTERVAL_SECONDS // 3600} hours.")
        await asyncio.sleep(SYNC_INTERVAL_SECONDS)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[STARTUP] Launching background sync worker...")
    task = asyncio.create_task(scheduled_sync())

    yield

    print("[SHUTDOWN] Cancelling background sync worker...")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="Automated Wealth & Portfolio Optimization API",
    description=(
        "Asynchronous microservice that ingests real-time market data from FMP "
        "and computes optimal capital allocation using SciPy's SLSQP algorithm "
        "to maximise the Sharpe Ratio."
    ),
    version="1.1.0",
    lifespan=lifespan,
)


@app.get("/", tags=["Health"])
def home():
    return {"message": "Wealth Optimization Engine is running."}


@app.get("/api/v1/optimize", tags=["Optimization"])
async def get_optimal_portfolio():
    try:
        results = await asyncio.to_thread(run_optimization)
        return {"status": "success", "data": results}
    except ValueError as e:
        return JSONResponse(status_code=422, content={"status": "error", "message": str(e)})
    except RuntimeError as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)