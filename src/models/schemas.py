from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


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
    category: Optional[str]
    main_pattern_id: Optional[int]
    sub_pattern_ids: Optional[List[int]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True



class EmbeddingResponse(BaseModel):
    """Response model for embedding operations."""
    embeddings_generated: List[str] = Field(description="List of embedding types generated")
    vector_dimensions: int = Field(description="Dimension of the vectors")
    processing_time_ms: float = Field(description="Processing time in milliseconds")


class CourseEmbeddingRequest(BaseModel):
    """Request model for course embedding generation via WebClient."""
    course_name: str = Field(..., description="Name/title of the course")
    course_description: str = Field(..., description="Description of the course")
    category: Optional[str] = Field(None, description="Course category")
    

class CourseEmbeddingResponse(BaseModel):
    """Response model for course embedding operations."""
    course_name: str = Field(description="Name/title of the course")
    course_description: str = Field(description="Description of the course")
    category: Optional[str] = Field(None, description="Course category")
    embeddings: dict = Field(description="Generated embeddings (title, description, combined)")
    processing_time_ms: float = Field(description="Processing time in milliseconds")