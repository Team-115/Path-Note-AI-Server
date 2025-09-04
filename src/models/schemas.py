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


class ReactionType(str, Enum):
    """Enum for reaction types."""
    LIKE = "like"
    SAVE = "save"
    SHARE = "share"


class PlacePatternRequest(BaseModel):
    """Request model for creating place patterns."""
    poi_ids: List[int] = Field(..., description="List of POI IDs in order")
    poi_name: List[str] = Field(..., description="POI Name")
    
class RecommendRequest(BaseModel):
    """다음 장소 추천 리퀘스트"""
    current_poi_sequence: List[int] = Field(..., description="Current POI sequence visited by user")
    limit: int = 10
    min_similarity: float = 0.3

class PlacePatternResponse(BaseModel):
    """Response model for place pattern operations."""
    id: int
    poi_ids: List[int]
    sequence_count: int
    relation_count: int
    sequence_score: float
    relation_score: float
    pattern_length: Optional[int]
    first_poi: Optional[int]
    last_poi: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserPreferenceRequest(BaseModel):
    """Request model for creating user preferences."""
    mysql_user_id: int = Field(..., description="Unique user ID from MySQL database")
    preference_weight: Optional[float] = Field(0.4, description="Preference weight")
    category_weight: Optional[float] = Field(0.3, description="Category weight")
    behavior_weight: Optional[float] = Field(0.3, description="Behavior weight")


class UserPreferenceResponse(BaseModel):
    """Response model for user preference operations."""
    id: int
    mysql_user_id: int
    preference_weight: float
    category_weight: float
    behavior_weight: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CourseReactionRequest(BaseModel):
    """Request model for course reactions."""
    mysql_user_id: int = Field(..., description="User ID")
    mysql_course_id: int = Field(..., description="Course ID")
    reaction_type: ReactionType = Field(..., description="Type of reaction")
    rating: Optional[int] = Field(None, description="Rating (1-5)", ge=1, le=5)


class CourseReactionResponse(BaseModel):
    """Response model for course reaction operations."""
    id: int
    mysql_user_id: int
    mysql_course_id: int
    reaction_type: str
    rating: Optional[int]
    weight_applied: bool
    weight_value: float
    created_at: datetime
    
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