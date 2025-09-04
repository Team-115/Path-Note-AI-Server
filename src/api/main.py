from fastapi import FastAPI, Query, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import time
from decimal import Decimal

from pydantic import BaseModel

from .config import get_settings
from .database import check_database_connection, check_vector_extension, get_database_session
from ..models import Base, CourseVector, PlaceVector
from ..models.schemas import (
    CourseCreateRequest, CourseResponse, 
    PlaceCreateRequest, PlaceResponse,
    BatchProcessResponse, EmbeddingResponse
)
from ..services.embedding import get_embedding_service
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

import pdb; pdb.set_trace()

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


# Course Vector Endpoints
@app.post("/courses", response_model=CourseResponse)
async def create_course_with_embeddings(
    course_data: CourseCreateRequest,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Create a new course with KoSimCSE-roberta embeddings.
    
    This endpoint:
    1. Takes course data (title, description, category, etc.)
    2. Generates multiple types of embeddings using KoSimCSE-roberta
    3. Stores the course with all embeddings in the database
    """
    start_time = time.time()
    
    try:
        # Get embedding service
        embedding_service = get_embedding_service()
        
        # Generate embeddings
        embeddings = embedding_service.encode_course_data(
            title=course_data.title,
            description=course_data.description,
            category=course_data.category or ""
        )
        
        # Create CourseVector instance
        course_vector = CourseVector(
            mysql_course_id=course_data.mysql_course_id,
            title_embedding=embeddings["title_embedding"],
            description_embedding=embeddings["description_embedding"],
            combined_embedding=embeddings["combined_embedding"],
            title_embedding_norm=embeddings["title_embedding_norm"],
            combined_embedding_norm=embeddings["combined_embedding_norm"],
            semantic_tags=embeddings["semantic_tags"],
            region=course_data.region,
            duration_minutes=course_data.duration_minutes
        )
        
        # Save to database
        db.add(course_vector)
        await db.commit()
        await db.refresh(course_vector)
        
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        logger.info(f"Created course {course_data.mysql_course_id} with embeddings in {processing_time:.2f}ms")
        
        return course_vector
        
    except IntegrityError as e:
        await db.rollback()
        if "duplicate key" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Course with mysql_course_id {course_data.mysql_course_id} already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create course: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create course with embeddings"
        )


@app.post("/courses/batch", response_model=BatchProcessResponse)
async def create_courses_batch(
    courses: List[CourseCreateRequest],
    db: AsyncSession = Depends(get_database_session)
):
    """
    Create multiple courses with embeddings in batch.
    
    Processes multiple courses efficiently by generating embeddings
    for all courses and then saving them in a single transaction.
    """
    start_time = time.time()
    embedding_service = get_embedding_service()
    
    successful = 0
    failed = 0
    errors = []
    
    try:
        course_vectors = []
        
        for course_data in courses:
            try:
                # Generate embeddings
                embeddings = embedding_service.encode_course_data(
                    title=course_data.title,
                    description=course_data.description,
                    category=course_data.category or ""
                )
                
                # Create CourseVector instance
                course_vector = CourseVector(
                    mysql_course_id=course_data.mysql_course_id,
                    title_embedding=embeddings["title_embedding"],
                    description_embedding=embeddings["description_embedding"],
                    combined_embedding=embeddings["combined_embedding"],
                    title_embedding_norm=embeddings["title_embedding_norm"],
                    combined_embedding_norm=embeddings["combined_embedding_norm"],
                    semantic_tags=embeddings["semantic_tags"],
                    region=course_data.region,
                    duration_minutes=course_data.duration_minutes
                )
                
                course_vectors.append(course_vector)
                successful += 1
                
            except Exception as e:
                failed += 1
                errors.append(f"Course {course_data.mysql_course_id}: {str(e)}")
                logger.error(f"Failed to process course {course_data.mysql_course_id}: {e}")
        
        # Bulk insert
        if course_vectors:
            db.add_all(course_vectors)
            await db.commit()
        
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Batch processed {len(courses)} courses in {processing_time:.2f}ms")
        
        return BatchProcessResponse(
            total_processed=len(courses),
            successful=successful,
            failed=failed,
            errors=errors
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Batch processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch processing failed"
        )


@app.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    db: AsyncSession = Depends(get_database_session)
):
    """Get course by MySQL course ID."""
    stmt = select(CourseVector).where(CourseVector.mysql_course_id == course_id)
    result = await db.execute(stmt)
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with id {course_id} not found"
        )
    
    return course


# Place Vector Endpoints
@app.post("/places", response_model=PlaceResponse)
async def create_place_with_embeddings(
    place_data: PlaceCreateRequest,
    db: AsyncSession = Depends(get_database_session)
):
    """
    Create a new place with KoSimCSE-roberta embeddings.
    
    This endpoint:
    1. Takes place data (name, category, location, etc.)
    2. Generates location-aware and time-contextual embeddings
    3. Stores the place with all embeddings in the database
    """
    start_time = time.time()
    
    try:
        # Get embedding service
        embedding_service = get_embedding_service()
        
        # Generate embeddings
        embeddings = embedding_service.encode_place_data(
            place_name=place_data.place_name,
            category=place_data.category or "",
            context=place_data.context or "",
            latitude=float(place_data.latitude) if place_data.latitude else None,
            longitude=float(place_data.longitude) if place_data.longitude else None
        )
        
        # Create PlaceVector instance
        place_vector = PlaceVector(
            poi_id=place_data.poi_id,
            place_embedding=embeddings["place_embedding"],
            context_embedding=embeddings["context_embedding"],
            morning_embedding=embeddings["morning_embedding"],
            afternoon_embedding=embeddings["afternoon_embedding"],
            evening_embedding=embeddings["evening_embedding"],
            location_vector=embeddings.get("location_vector"),
            latitude=place_data.latitude,
            longitude=place_data.longitude,
            category=place_data.category,
            region=place_data.region,
            popularity_score=place_data.popularity_score
        )
        
        # Save to database
        db.add(place_vector)
        await db.commit()
        await db.refresh(place_vector)
        
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        logger.info(f"Created place {place_data.poi_id} with embeddings in {processing_time:.2f}ms")
        
        return place_vector
        
    except IntegrityError as e:
        await db.rollback()
        if "duplicate key" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Place with poi_id {place_data.poi_id} already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create place: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create place with embeddings"
        )


@app.post("/places/batch", response_model=BatchProcessResponse)
async def create_places_batch(
    places: List[PlaceCreateRequest],
    db: AsyncSession = Depends(get_database_session)
):
    """Create multiple places with embeddings in batch."""
    start_time = time.time()
    embedding_service = get_embedding_service()
    
    successful = 0
    failed = 0
    errors = []
    
    try:
        place_vectors = []
        
        for place_data in places:
            try:
                # Generate embeddings
                embeddings = embedding_service.encode_place_data(
                    place_name=place_data.place_name,
                    category=place_data.category or "",
                    context=place_data.context or "",
                    latitude=float(place_data.latitude) if place_data.latitude else None,
                    longitude=float(place_data.longitude) if place_data.longitude else None
                )
                
                # Create PlaceVector instance
                place_vector = PlaceVector(
                    poi_id=place_data.poi_id,
                    place_embedding=embeddings["place_embedding"],
                    context_embedding=embeddings["context_embedding"],
                    morning_embedding=embeddings["morning_embedding"],
                    afternoon_embedding=embeddings["afternoon_embedding"],
                    evening_embedding=embeddings["evening_embedding"],
                    location_vector=embeddings.get("location_vector"),
                    latitude=place_data.latitude,
                    longitude=place_data.longitude,
                    category=place_data.category,
                    region=place_data.region,
                    popularity_score=place_data.popularity_score
                )
                
                place_vectors.append(place_vector)
                successful += 1
                
            except Exception as e:
                failed += 1
                errors.append(f"Place {place_data.poi_id}: {str(e)}")
                logger.error(f"Failed to process place {place_data.poi_id}: {e}")
        
        # Bulk insert
        if place_vectors:
            db.add_all(place_vectors)
            await db.commit()
        
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Batch processed {len(places)} places in {processing_time:.2f}ms")
        
        return BatchProcessResponse(
            total_processed=len(places),
            successful=successful,
            failed=failed,
            errors=errors
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Batch processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch processing failed"
        )


@app.get("/places/{place_id}", response_model=PlaceResponse)
async def get_place(
    place_id: int,
    db: AsyncSession = Depends(get_database_session)
):
    """Get place by POI ID."""
    stmt = select(PlaceVector).where(PlaceVector.poi_id == place_id)
    result = await db.execute(stmt)
    place = result.scalar_one_or_none()
    
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Place with id {place_id} not found"
        )
    
    return place


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