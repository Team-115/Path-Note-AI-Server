# from sqlalchemy import Column, Integer, String, TIMESTAMP, FLOAT, ARRAY, Boolean, SmallInteger, ForeignKey, Computed
# from sqlalchemy.sql import func
# from sqlalchemy.dialects.postgresql import JSONB
# from pgvector.sqlalchemy import Vector
# from .base import Base


# class PlacePattern(Base):
#     __tablename__ = "place_patterns"
    
#     id = Column(Integer, primary_key=True)
#     poi_ids = Column(ARRAY(Integer), unique=True, nullable=False)
#     pattern_embedding = Column(Vector(768))
    
#     # 사용 통계
#     sequence_count = Column(Integer, default=0)
#     relation_count = Column(Integer, default=0)
    
#     # 점수 (계산된 값)
#     sequence_score = Column(FLOAT, default=0.0)
#     relation_score = Column(FLOAT, default=0.0)
    
#     # 메타데이터 (검색 최적화용 - computed columns)
#     pattern_length = Column(
#         SmallInteger,
#         Computed("array_length(poi_ids, 1)"),
#         nullable=False
#     )
#     first_poi = Column(
#         Integer,
#         Computed("poi_ids[1]", persisted=True),
#         nullable=False
#     )
#     last_poi = Column(
#         Integer,
#         Computed("poi_ids[array_length(poi_ids, 1)]", persisted=True),
#         nullable=False
#     )
    
#     created_at = Column(TIMESTAMP, server_default=func.now())
#     updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


# class CourseVector(Base):
#     __tablename__ = "course_vectors"
    
#     id = Column(Integer, primary_key=True)
#     mysql_course_id = Column(Integer, unique=True, nullable=False)
    
#     # 의미 검색용 임베딩 (원본 벡터 저장, 코사인 유사도는 런타임 계산)
#     title_embedding = Column(Vector(768))
#     description_embedding = Column(Vector(768))
#     combined_embedding = Column(Vector(768))
    
#     # 패턴 참조
#     main_pattern_id = Column(Integer, ForeignKey('place_patterns.id', ondelete='SET NULL'))
#     sub_pattern_ids = Column(ARRAY(Integer))
    
#     # 하이브리드 검색용 (벡터 + 필터)
#     region = Column(String(50))
#     category = Column(String(100))
    
#     created_at = Column(TIMESTAMP, server_default=func.now())
#     updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())




# class UserPreferenceVector(Base):
#     __tablename__ = "user_preference_vectors"
    
#     id = Column(Integer, primary_key=True)
#     mysql_user_id = Column(Integer, unique=True, nullable=False)
    
#     # 사용자 선호도 임베딩
#     preference_embedding = Column(Vector(768))
#     category_preference_embedding = Column(Vector(768))
#     behavior_embedding = Column(Vector(768))
    
#     # 선호도 가중치 (0.0 ~ 1.0)
#     preference_weight = Column(FLOAT, default=0.4)
#     category_weight = Column(FLOAT, default=0.3)
#     behavior_weight = Column(FLOAT, default=0.3)
    
#     created_at = Column(TIMESTAMP, server_default=func.now())
#     updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


# class CourseReaction(Base):
#     __tablename__ = "course_reactions"
    
#     id = Column(Integer, primary_key=True)
#     mysql_user_id = Column(Integer, nullable=False)
#     mysql_course_id = Column(Integer, nullable=False)
    
#     # 반응 정보
#     reaction_type = Column(String(50), nullable=False)
#     rating = Column(Integer)
    
#     # 가중치 계산 정보
#     weight_applied = Column(Boolean, default=False)
#     weight_value = Column(FLOAT, default=0.0)
    
#     created_at = Column(TIMESTAMP, server_default=func.now())