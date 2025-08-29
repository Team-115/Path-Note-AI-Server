from fastapi import FastAPI, Query, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from pydantic import BaseModel

from .config import get_settings
from .database import check_database_connection, check_vector_extension, get_database_session
from ..models import Base, Customer, Content
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings() # config파일 로드

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Travel AI API...")
    
    # Check database connection
    if await check_database_connection():
        logger.info("✓ Database connection successful")
    else:
        logger.error("✗ Database connection failed")
    
    # Check pgvector extension
    if await check_vector_extension():
        logger.info("✓ pgvector extension is available")
    else:
        logger.warning("⚠ pgvector extension not found")
    
    yield
    logger.info("Shutting down Travel AI API...")

app = FastAPI(
    title=settings.api_title,
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "name": settings.api_title,
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    db_status = await check_database_connection()
    vector_status = await check_vector_extension()
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "vector_extension": "available" if vector_status else "unavailable"
    }

@app.get("/health/database")
async def health_database():
    """Detailed database health check."""
    db_connected = await check_database_connection()
    vector_available = await check_vector_extension()
    
    return {
        "database": {
            "connected": db_connected,
            "url": settings.database_url.split("@")[1] if "@" in settings.database_url else "hidden"
        },
        "vector_extension": {
            "available": vector_available
        },
        "status": "ok" if db_connected and vector_available else "error"
    }