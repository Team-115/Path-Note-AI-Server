from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class CourseCreateRequest(BaseModel):
    """Request model for creating a course with embeddings."""
    mysql_course_id: int = Field(..., description="Unique course ID from MySQL database")
    title: str = Field(..., description="Course title")
    description: str = Field(..., description="Course description")
    category: Optional[str] = Field(None, description="Course category")
    region: Optional[str] = Field(None, description="Course region")
    duration_minutes: Optional[int] = Field(None, description="Course duration in minutes")


class CourseResponse(BaseModel):
    """Response model for course operations."""
    id: int
    mysql_course_id: int
    region: Optional[str]
    duration_minutes: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PlaceCreateRequest(BaseModel):
    """Request model for creating a place with embeddings."""
    poi_id: int = Field(..., description="Unique POI ID")
    place_name: str = Field(..., description="Name of the place")
    category: Optional[str] = Field(None, description="Place category")
    context: Optional[str] = Field(None, description="Additional context about the place")
    latitude: Optional[Decimal] = Field(None, description="Place latitude")
    longitude: Optional[Decimal] = Field(None, description="Place longitude")
    region: Optional[str] = Field(None, description="Place region")
    popularity_score: Optional[float] = Field(0.0, description="Popularity score")


class PlaceResponse(BaseModel):
    """Response model for place operations."""
    id: int
    poi_id: int
    category: Optional[str]
    region: Optional[str]
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    popularity_score: Optional[float]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BatchProcessResponse(BaseModel):
    """Response for batch operations."""
    total_processed: int
    successful: int
    failed: int
    errors: List[str] = []


class EmbeddingResponse(BaseModel):
    """Response model for embedding operations."""
    embeddings_generated: List[str] = Field(description="List of embedding types generated")
    vector_dimensions: int = Field(description="Dimension of the vectors")
    processing_time_ms: float = Field(description="Processing time in milliseconds")