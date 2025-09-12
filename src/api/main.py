from fastapi import FastAPI, Query, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import time
from decimal import Decimal

from pydantic import BaseModel

class EchoRequest(BaseModel):
    message: str

from .config import get_settings
from .database import check_database_connection, check_vector_extension, get_database_session
from ..models import Base, Course
from ..models.schemas import (
    CourseCreateRequest, CourseResponse,
    CourseEmbeddingRequest, CourseEmbeddingResponse
)
from ..services.embedding import get_embedding_service
from ..services.scheduler import get_scheduler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
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
    
    # Start scheduler for embedding processing
    scheduler = get_scheduler()
    await scheduler.start()
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down Travel AI API...")
    await scheduler.stop()

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

# 임베딩 API
@app.post("/embed/course", response_model=CourseEmbeddingResponse)
async def generate_course_embeddings(course_data: CourseEmbeddingRequest):
    """코스 데이터에 대한 임베딩 생성 (Spring WebClient용)"""
    import time
    start_time = time.time()
    
    try:
        # 임베딩 서비스로 벡터 생성
        embedding_service = get_embedding_service()
        embeddings = embedding_service.encode_course_data(
            title=course_data.course_name,
            description=course_data.course_description,
            category=course_data.category or ""
        )
        
        processing_time = (time.time() - start_time) * 1000  # ms 단위
        
        return CourseEmbeddingResponse(
            course_name=course_data.course_name,
            course_description=course_data.course_description,
            embeddings=embeddings,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"코스 임베딩 생성 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate course embeddings: {str(e)}"
        )

# 코스 관련 API  
@app.post("/course", response_model=dict)
async def create_course_with_embeddings(
    course_data: CourseCreateRequest,
    db: AsyncSession = Depends(get_database_session)
):
    """코스 생성 및 임베딩 저장"""
    try:
        # 임베딩 서비스로 벡터 생성
        embedding_service = get_embedding_service()
        embeddings = embedding_service.encode_course_data(
            title=course_data.title,
            description=course_data.description,
            category=course_data.category or ""
        )
        
        # 새 코스 생성 (새로운 스키마에 맞춰)
        course = Course(
            course_name=course_data.title,
            user_id=1,  # 임시 user_id, 실제로는 요청에서 받아야 함
            course_description=course_data.description,
            course_category=course_data.category,
            embedding_vector=embeddings["combined_embedding"]
        )
        
        db.add(course)
        await db.commit()
        await db.refresh(course)
        
        return {
            "course_id": course.course_id,
            "course_name": course.course_name,
            "course_category": course.course_category,
            "embedding_generated": True,
            "created_at": course.created_at
        }
        
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Course already exists"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"코스 생성 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create course: {str(e)}"
        )

# Utility Endpoints
@app.get("/embeddings/info", response_model=dict)
async def get_embedding_info():
    """Get information about the embedding model and service."""
    try:
        embedding_service = get_embedding_service()
        return {
            "model_name": "BM-K/KoSimCSE-roberta",
            "vector_dimension": 768,
            "language": "Korean (ko)",
            "description": "Korean-optimized sentence embeddings using SimCSE with RoBERTa",
            "supported_operations": [
                "Course semantic search",
                "Place contextual recommendations", 
                "Time-aware embeddings",
                "Location-based similarity"
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get embedding service info: {str(e)}"
        )

# 스케줄러 관리 API
@app.get("/scheduler/status")
async def get_scheduler_status():
    """스케줄러 상태 조회"""
    scheduler = get_scheduler()
    return {
        "scheduler_running": scheduler.is_running,
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None
            }
            for job in scheduler.scheduler.get_jobs()
        ] if scheduler.is_running else []
    }

@app.post("/scheduler/process-now")
async def trigger_embedding_processing():
    """즉시 null embedding 처리 실행"""
    try:
        scheduler = get_scheduler()
        if not scheduler.is_running:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Scheduler is not running"
            )
        
        # 백그라운드에서 즉시 실행
        import asyncio
        asyncio.create_task(scheduler.process_null_embeddings())
        
        return {"message": "Embedding processing triggered successfully"}
        
    except Exception as e:
        logger.error(f"Failed to trigger embedding processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger embedding processing: {str(e)}"
        )