"""
Database models matching the new PostgreSQL schema.
"""
from sqlalchemy import Column, Integer, String, BigInteger, TIMESTAMP, FLOAT, ARRAY, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from .base import Base


class Place(Base):
    __tablename__ = "places"
    
    place_id = Column(BigInteger, primary_key=True, autoincrement=True)
    poi_id = Column(BigInteger, nullable=False)
    place_name = Column(String(100), nullable=False)
    place_category = Column(String(50), nullable=False)
    place_address = Column(String(100), nullable=False)
    place_coordinate_x = Column(FLOAT, nullable=False)
    place_coordinate_y = Column(FLOAT, nullable=False)


class User(Base):
    __tablename__ = "users"
    
    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    kakao_id = Column(String(100), nullable=False, unique=True)
    nickname = Column(String(50))
    profile_preset = Column(String(10), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    preference_embedding = Column(Vector(768))
    
    # Relationships
    courses = relationship("Course", back_populates="user")
    likes = relationship("Like", back_populates="user")
    comments = relationship("Comment", back_populates="user")


class Course(Base):
    __tablename__ = "courses"
    
    course_id = Column(BigInteger, primary_key=True, autoincrement=True)
    course_name = Column(String(100), nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    course_description = Column(Text)
    course_category = Column(String(50))
    embedding_vector = Column(Vector(768))
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    # 추가 컬럼들 (실제 데이터베이스에 있는 것들)
    center_x = Column(FLOAT)
    center_y = Column(FLOAT)
    like_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="courses")
    course_places = relationship("CoursePlace", back_populates="course")
    likes = relationship("Like", back_populates="course")
    comments = relationship("Comment", back_populates="course")


class CoursePlace(Base):
    __tablename__ = "course_places"
    
    course_place_id = Column(BigInteger, primary_key=True, autoincrement=True)
    course_id = Column(BigInteger, ForeignKey('courses.course_id', ondelete='CASCADE'), nullable=False)
    place_id = Column(BigInteger, ForeignKey('places.place_id', ondelete='CASCADE'), nullable=False)
    sequence_index = Column(BigInteger, nullable=False)
    leave_time = Column(TIMESTAMP)
    enter_time = Column(TIMESTAMP)
    
    # Relationships
    course = relationship("Course", back_populates="course_places")
    place = relationship("Place")


class Like(Base):
    __tablename__ = "likes"
    
    like_id = Column(BigInteger, primary_key=True, autoincrement=True)
    course_id = Column(BigInteger, ForeignKey('courses.course_id', ondelete='CASCADE'), nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    # Relationships
    course = relationship("Course", back_populates="likes")
    user = relationship("User", back_populates="likes")


class Comment(Base):
    __tablename__ = "comments"
    
    comment_id = Column(BigInteger, primary_key=True, autoincrement=True)
    course_id = Column(BigInteger, ForeignKey('courses.course_id', ondelete='CASCADE'), nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    # Relationships
    course = relationship("Course", back_populates="comments")
    user = relationship("User", back_populates="comments")


class PlacePattern(Base):
    __tablename__ = "place_patterns"
    
    place_patterns_id = Column(BigInteger, primary_key=True, autoincrement=True)
    poi_ids = Column(ARRAY(Integer), nullable=False, unique=True)
    pattern_embedding = Column(Vector(768))
    
    # 사용 통계
    sequence_count = Column(Integer, default=0)
    relation_count = Column(Integer, default=0)
    
    # 점수
    sequence_score = Column(FLOAT, default=0.0)
    relation_score = Column(FLOAT, default=0.0)
    
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())