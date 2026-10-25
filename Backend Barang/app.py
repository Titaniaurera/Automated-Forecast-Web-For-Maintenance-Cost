from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.gi import router as gi_router
from routes.gr import router as gr_router
from routes.stock import router as stock_router
from routes.projection import router as projection_router
from routes.forecast import router as forecast_router


app = FastAPI(
    title="Forecast Material API",
    version="1.0.0"
)


# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# ROUTER
# ==========================================

app.include_router(
    gi_router
)

app.include_router(
    gr_router
)

app.include_router(
    stock_router
)

app.include_router(
    projection_router
)

app.include_router(
    forecast_router
)


# ==========================================
# HOME
# ==========================================

@app.get("/")
def home():

    return {
        "message": "Forecast Material API Running 🚀"
    }
