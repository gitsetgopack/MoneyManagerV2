"""
This module defines the main FastAPI application for Money Manager.
"""

from contextlib import asynccontextmanager

import uvicorn
from config import API_BIND_HOST, API_BIND_PORT
from fastapi import FastAPI

from api.routers import accounts, analytics, categories, expenses, users


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifespan function that handles app startup and shutdown"""
    yield
    # Handles the shutdown event to close the MongoDB client
    await users.shutdown_db_client()


app = FastAPI(lifespan=lifespan)

# Include routers for different functionalities
app.include_router(users.router)
app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(expenses.router)
app.include_router(analytics.router)

if __name__ == "__main__":
    uvicorn.run("app:app", host=API_BIND_HOST, port=API_BIND_PORT, reload=True)
