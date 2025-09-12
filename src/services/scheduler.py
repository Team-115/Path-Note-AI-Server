"""
Scheduled tasks for embedding processing and maintenance.
"""
import logging
import asyncio
from typing import Dict, List, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text

from ..api.config import get_settings
from ..api.database import async_session_factory
from ..models.database_models import Course
from .embedding import get_embedding_service

logger = logging.getLogger(__name__)


class EmbeddingScheduler:
    """스케줄러 클래스 - null embedding 처리 및 배치 작업 관리"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.settings = get_settings()
        self.is_running = False
    
    async def start(self):
        """스케줄러 시작"""
        if not self.is_running:
            logger.info("Starting embedding scheduler...")
            
            # 5분마다 null embedding 처리
            self.scheduler.add_job(
                func=self.process_null_embeddings,
                trigger=IntervalTrigger(minutes=1),
                id="process_null_embeddings",
                name="Process courses with null embeddings",
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            logger.info("✓ Embedding scheduler started successfully")
    
    async def stop(self):
        """스케줄러 중지"""
        if self.is_running:
            logger.info("Stopping embedding scheduler...")
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("✓ Embedding scheduler stopped")
    
    async def process_null_embeddings(self):
        """null embedding을 가진 코스들을 처리하는 스케줄된 작업"""
        try:
            logger.info("Starting null embeddings processing...")
            
            # 1. PostgreSQL에서 null embedding 코스들 조회
            async with async_session_factory() as db:
                null_courses = await self._fetch_null_embedding_courses(db)
                
                if not null_courses:
                    logger.info("No courses with null embeddings found")
                    return
                
                logger.info(f"Found {len(null_courses)} courses with null embeddings")
                
                # 2. 각 코스에 대해 임베딩 생성 및 업데이트
                processed_count = 0
                failed_count = 0
                
                for course in null_courses:
                    try:
                        await self._process_single_course(db, course)
                        processed_count += 1
                        logger.debug(f"Processed course {course.course_id}")
                        
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"Failed to process course {course.course_id}: {e}")
                
                logger.info(f"Batch processing completed: {processed_count} processed, {failed_count} failed")
            
        except Exception as e:
            logger.error(f"Error in null embeddings processing: {e}")
    
    async def _fetch_null_embedding_courses(self, db: AsyncSession) -> List[Course]:
        """PostgreSQL에서 null embedding을 가진 코스들 조회"""
        try:
            # course_embedding이 null인 코스들 조회
            stmt = select(Course).where(
                Course.embedding_vector.is_(None)
            ).limit(50)  # 한 번에 최대 50개까지 처리
            
            result = await db.execute(stmt)
            courses = result.scalars().all()
            return list(courses)
                
        except Exception as e:
            logger.error(f"Error fetching null embedding courses from database: {e}")
            return []
    
    async def _process_single_course(self, db: AsyncSession, course: Course):
        """단일 코스에 대한 임베딩 생성 및 업데이트"""
        try:
            # 새로운 courses 테이블에는 course_name과 course_description이 있으므로
            # 별도의 API 호출 없이 바로 임베딩을 생성할 수 있습니다.
            
            # 임베딩 생성
            embedding_service = get_embedding_service()
            embeddings = embedding_service.encode_course_data(
                title=course.course_name or "",
                description=course.course_description or "",
                category=course.course_category or ""
            )
            
            # PostgreSQL에서 임베딩 업데이트
            await self._update_course_embedding_in_db(db, course.course_id, embeddings["combined_embedding"])
            
        except Exception as e:
            logger.error(f"Error processing course {course.course_id}: {e}")
            raise
    
    async def _update_course_embedding_in_db(self, db: AsyncSession, course_id: int, embedding: List[float]):
        """PostgreSQL에서 코스 임베딩 직접 업데이트"""
        try:
            stmt = update(Course).where(
                Course.course_id == course_id
            ).values(
                embedding_vector=embedding
            )
            
            await db.execute(stmt)
            await db.commit()
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating course embedding in database: {e}")
            raise


# 전역 스케줄러 인스턴스
_scheduler_instance = None

def get_scheduler() -> EmbeddingScheduler:
    """스케줄러 인스턴스 반환 (싱글톤 패턴)"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = EmbeddingScheduler()
    return _scheduler_instance