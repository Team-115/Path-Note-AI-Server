from sqlalchemy import Column, Integer, String, TIMESTAMP, DECIMAL, FLOAT, Text, ARRAY, text
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from .base import Base


class CourseVector(Base):
    __tablename__ = "course_vectors"
    
    id = Column(Integer, primary_key=True)
    mysql_course_id = Column(Integer, unique=True, nullable=False)
    
    # 다각도 의미 검색(제목+설명+카테고리)
    title_embedding = Column(Vector(768))
    description_embedding = Column(Vector(768))
    combined_embedding = Column(Vector(768))
    
    # 하이브리드 검색용 (벡터 + 필터)
    region = Column(String(50))
    duration_minutes = Column(Integer)
    
    # 의미 검색용 메타데이터
    semantic_tags = Column(Vector(768))
    user_profile_embedding = Column(Vector(768))
    
    # 검색 최적화용 정규화된 벡터 (코사인 유사도 최적화)
    title_embedding_norm = Column(Vector(768))
    description_embedding_norm = Column(Vector(768))
    combined_embedding_norm = Column(Vector(768))
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class PlaceVector(Base):
    __tablename__ = "place_vectors"
    
    id = Column(Integer, primary_key=True)
    poi_id = Column(Integer, unique=True, nullable=False)
    
    # 장소 임베딩
    place_embedding = Column(Vector(768))
    context_embedding = Column(Vector(768))
    
    # 위치 벡터 (지리적 유사도)
    location_vector = Column(Vector(2))
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    
    # 시간대별 임베딩 (시간 맥락 추천)
    morning_embedding = Column(Vector(768))
    afternoon_embedding = Column(Vector(768))
    evening_embedding = Column(Vector(768))
    
    # 하이브리드 검색용
    category = Column(String(100))
    region = Column(String(50))
    popularity_score = Column(FLOAT, default=0)
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class UserPreferenceVector(Base):
    __tablename__ = "user_preference_vectors"
    
    id = Column(Integer, primary_key=True)
    mysql_user_id = Column(Integer, unique=True, nullable=False)
    
    # 사용자 선호도 임베딩 (학습된)
    preference_embedding = Column(Vector(768))
    
    # 카테고리별 선호 벡터
    category_preference_embedding = Column(Vector(768))
    
    # 행동 패턴 임베딩
    behavior_embedding = Column(Vector(768))
    
    # 동적 컨텍스트 임베딩
    recent_context_embedding = Column(Vector(768))
    
    # 선호도 강도 (가중치)
    preference_weights = Column(JSONB, default=lambda: {})
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class VectorPattern(Base):
    __tablename__ = "vector_patterns"
    
    id = Column(Integer, primary_key=True)
    
    # 패턴 식별
    pattern_key = Column(String(255), unique=True, nullable=False)
    pattern_type = Column(String(50), nullable=False)
    
    # 데이터
    items = Column(ARRAY(Integer), nullable=False)
    items_length = Column(Integer)
    embedding = Column(Vector(768))
    
    # 학습 정보
    occurrence_count = Column(Integer, default=1)
    confidence = Column(FLOAT, default=0.5)
    
    # 메타데이터
    metadata_ = Column(JSONB, default=lambda: {})
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())