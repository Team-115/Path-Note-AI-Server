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
    """사용자가 Spring에 보낸 단일 검색어를 받기 위한 모델"""
    keyword: str = Field(..., description="사용자 입력 검색어")
    

class CourseEmbeddingResponse(BaseModel):
    """검색어 분석 결과 및 임베딩 벡터 응답 모델"""
    course_name: str
    course_description: str
    category: Optional[str]
    # embeddings 필드의 구조를 명확히 함
    embeddings: dict[str, List[float]] = Field(description="생성된 검색어 임베딩 벡터")
    processing_time_ms: Optional[float] = Field(None) # 임베딩 생성에 걸린 시간