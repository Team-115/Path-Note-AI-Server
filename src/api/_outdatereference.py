

# @app.put("/courses/{course_id}", response_model=CourseResponse)
# async def update_course(
#     course_id: int,
#     course_data: CourseCreateRequest,
#     db: AsyncSession = Depends(get_database_session)
# ):
#     """코스 업데이트 및 임베딩 재생성"""
#     try:
#         # 기존 코스 조회
#         stmt = select(CourseVector).where(CourseVector.mysql_course_id == course_id)
#         result = await db.execute(stmt)
#         course = result.scalar_one_or_none()
        
#         if not course:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"Course with id {course_id} not found"
#             )
        
#         # 임베딩 재생성
#         embedding_service = get_embedding_service()
#         embeddings = embedding_service.encode_course_data(
#             title=course_data.title,
#             description=course_data.description,
#             category=course_data.category or ""
#         )
        
#         # 코스 정보 업데이트
#         course.title_embedding = embeddings["title_embedding"]
#         course.description_embedding = embeddings["description_embedding"]
#         course.combined_embedding = embeddings["combined_embedding"]
#         course.region = course_data.region
#         course.category = course_data.category
        
#         await db.commit()
#         await db.refresh(course)
        
#         return course
        
#     except Exception as e:
#         await db.rollback()
#         logger.error(f"코스 업데이트 실패: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to update course: {str(e)}"
#         )


# @app.delete("/courses/{course_id}")
# async def delete_course(
#     course_id: int,
#     db: AsyncSession = Depends(get_database_session)
# ):
#     """코스 삭제"""
#     try:
#         stmt = select(CourseVector).where(CourseVector.mysql_course_id == course_id)
#         result = await db.execute(stmt)
#         course = result.scalar_one_or_none()
        
#         if not course:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"Course with id {course_id} not found"
#             )
        
#         await db.delete(course)
#         await db.commit()
        
#         return {"message": f"Course {course_id} deleted successfully"}
        
#     except Exception as e:
#         await db.rollback()
#         logger.error(f"코스 삭제 실패: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to delete course: {str(e)}"
#         )


# @app.get("/courses", response_model=List[CourseResponse])
# async def list_courses(
#     limit: int = Query(50, le=100),
#     offset: int = Query(0, ge=0),
#     region: Optional[str] = Query(None),
#     category: Optional[str] = Query(None),
#     db: AsyncSession = Depends(get_database_session)
# ):
#     """코스 목록 조회 (필터링 지원)"""
#     try:
#         stmt = select(CourseVector)
        
#         if region:
#             stmt = stmt.where(CourseVector.region == region)
#         if category:
#             stmt = stmt.where(CourseVector.category == category)
            
#         stmt = stmt.offset(offset).limit(limit)
        
#         result = await db.execute(stmt)
#         courses = result.scalars().all()
        
#         return courses
        
#     except Exception as e:
#         logger.error(f"코스 목록 조회 실패: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to list courses: {str(e)}"
#         )


# @app.post("/courses/search")
# async def search_courses(
#     query: str = Query(..., description="검색 쿼리"),
#     limit: int = Query(20, le=100),
#     threshold: float = Query(0.7, ge=0.0, le=1.0, description="유사도 임계값"),
#     region: Optional[str] = Query(None),
#     category: Optional[str] = Query(None),
#     db: AsyncSession = Depends(get_database_session)
# ):
#     """의미 기반 코스 검색"""
#     try:
#         # 검색 쿼리 임베딩 생성
#         embedding_service = get_embedding_service()
#         query_embedding = embedding_service.encode_text(query, normalize=False)
        
#         # 벡터 유사도 검색 쿼리 구성
#         similarity_expr = text(
#             "1 - (combined_embedding <=> :query_vector) as similarity"
#         )
        
#         stmt = select(CourseVector, similarity_expr).where(
#             text("1 - (combined_embedding <=> :query_vector) >= :threshold")
#         )
        
#         # 필터 조건 추가
#         if region:
#             stmt = stmt.where(CourseVector.region == region)
#         if category:
#             stmt = stmt.where(CourseVector.category == category)
            
#         stmt = stmt.order_by(text("similarity DESC")).limit(limit)
        
#         result = await db.execute(
#             stmt, 
#             {"query_vector": query_embedding.tolist(), "threshold": threshold}
#         )
        
#         search_results = []
#         for course, similarity in result:
#             search_results.append({
#                 "course": {
#                     "id": course.id,
#                     "mysql_course_id": course.mysql_course_id,
#                     "region": course.region,
#                     "category": course.category,
#                     "created_at": course.created_at,
#                     "updated_at": course.updated_at
#                 },
#                 "similarity": float(similarity)
#             })
        
#         return {
#             "query": query,
#             "results": search_results,
#             "total": len(search_results)
#         }
        
#     except Exception as e:
#         logger.error(f"코스 검색 실패: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to search courses: {str(e)}"
#         )


# # 장소 패턴 관련 API
# @app.post("/patterns", response_model=PlacePatternResponse)
# async def create_place_pattern(
#     pattern_data: PlacePatternRequest,
#     db: AsyncSession = Depends(get_database_session)
# ):
#     """장소 패턴 생성"""
#     try:
#         # 중복 패턴 확인
#         stmt = select(PlacePattern).where(PlacePattern.poi_ids == pattern_data.poi_ids)
#         result = await db.execute(stmt)
#         existing_pattern = result.scalar_one_or_none()
        
#         if existing_pattern:
#             raise HTTPException(
#                 status_code=status.HTTP_409_CONFLICT,
#                 detail="Pattern with same POI sequence already exists"
#             )
#         embedding_service = get_embedding_service()
        
#         # 새 패턴 생성
#         pattern = PlacePattern(
#             poi_ids=pattern_data.poi_ids,
#             pattern_embedding = embedding_service.encode_pattern_sequence(pattern_data.poi_name)
#         )
        
#         db.add(pattern)
#         await db.commit()
#         await db.refresh(pattern)
        
#         return pattern
        
#     except IntegrityError:
#         await db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail="Pattern already exists"
#         )
#     except Exception as e:
#         await db.rollback()
#         logger.error(f"패턴 생성 실패: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to create pattern: {str(e)}"
#         )


# @app.get("/patterns/{pattern_id}", response_model=PlacePatternResponse)
# async def get_pattern(
#     pattern_id: int,
#     db: AsyncSession = Depends(get_database_session)
# ):
#     """패턴 ID로 패턴 조회"""
#     stmt = select(PlacePattern).where(PlacePattern.id == pattern_id)
#     result = await db.execute(stmt)
#     pattern = result.scalar_one_or_none()
    
#     if not pattern:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Pattern with id {pattern_id} not found"
#         )
    
#     return pattern


# @app.get("/patterns", response_model=List[PlacePatternResponse])
# async def list_patterns(
#     limit: int = Query(50, le=100),
#     offset: int = Query(0, ge=0),
#     min_length: Optional[int] = Query(None, ge=1),
#     max_length: Optional[int] = Query(None, ge=1),
#     min_score: Optional[float] = Query(None, ge=0.0),
#     sort_by: str = Query("sequence_score", regex="^(sequence_score|relation_score|total_usage)$"),
#     db: AsyncSession = Depends(get_database_session)
# ):
#     """패턴 목록 조회 (필터링 및 정렬 지원)"""
#     try:
#         stmt = select(PlacePattern)
        
#         # 필터 조건
#         if min_length:
#             stmt = stmt.where(PlacePattern.pattern_length >= min_length)
#         if max_length:
#             stmt = stmt.where(PlacePattern.pattern_length <= max_length)
#         if min_score:
#             if sort_by == "sequence_score":
#                 stmt = stmt.where(PlacePattern.sequence_score >= min_score)
#             elif sort_by == "relation_score":
#                 stmt = stmt.where(PlacePattern.relation_score >= min_score)
        
#         # 정렬
#         if sort_by == "sequence_score":
#             stmt = stmt.order_by(PlacePattern.sequence_score.desc())
#         elif sort_by == "relation_score":
#             stmt = stmt.order_by(PlacePattern.relation_score.desc())
#         else:  # total_usage
#             stmt = stmt.order_by((PlacePattern.sequence_count + PlacePattern.relation_count).desc())
            
#         stmt = stmt.offset(offset).limit(limit)
        
#         result = await db.execute(stmt)
#         patterns = result.scalars().all()
        
#         return patterns
        
#     except Exception as e:
#         logger.error(f"패턴 목록 조회 실패: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to list patterns: {str(e)}"
#         )


# @app.post("/patterns/{pattern_id}/usage")
# async def update_pattern_usage(
#     pattern_id: int,
#     usage_type: str = Query(..., regex="^(sequence|relation)$"),
#     increment: int = Query(1, ge=1),
#     db: AsyncSession = Depends(get_database_session)
# ):
#     """패턴 사용 통계 업데이트"""
#     try:
#         stmt = select(PlacePattern).where(PlacePattern.id == pattern_id)
#         result = await db.execute(stmt)
#         pattern = result.scalar_one_or_none()
        
#         if not pattern:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"Pattern with id {pattern_id} not found"
#             )
        
#         # 사용 카운트 증가
#         if usage_type == "sequence":
#             pattern.sequence_count += increment
#         else:  # relation
#             pattern.relation_count += increment
            
#         await db.commit()
#         await db.refresh(pattern)
        
#         return {
#             "pattern_id": pattern_id,
#             "usage_type": usage_type,
#             "new_count": pattern.sequence_count if usage_type == "sequence" else pattern.relation_count,
#             "total_usage": pattern.sequence_count + pattern.relation_count
#         }
        
#     except Exception as e:
#         await db.rollback()
#         logger.error(f"패턴 사용 통계 업데이트 실패: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to update pattern usage: {str(e)}"
#         )


# @app.post("/patterns/recommend")
# async def recommend_next_places(
#     req: RecommendRequest,
#     limit: int = Query(10, le=50),
#     db: AsyncSession = Depends(get_database_session)
# ):
#     """단순한 패턴 매칭 기반 다음 장소 추천"""
#     try:
#         if not req.current_poi_sequence:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Current POI sequence cannot be empty"
#             )
        
#         # 모든 패턴 조회
#         stmt = select(PlacePattern)
#         result = await db.execute(stmt)
#         all_patterns = result.scalars().all()
        
#         recommendations = []
        
#         # 각 패턴을 확인하여 매칭되는 다음 POI 찾기
#         for pattern in all_patterns:
#             next_poi = find_next_poi_simple(req.current_poi_sequence, pattern.poi_ids)
#             if next_poi:
#                 recommendations.append({
#                     'next_poi': next_poi,
#                     'pattern_id': pattern.id,
#                     'pattern': pattern.poi_ids,
#                     'usage_count': pattern.sequence_count
#                 })
        
#         # 사용 빈도순으로 정렬
#         recommendations.sort(key=lambda x: x['usage_count'], reverse=True)
        
#         # 중복 POI 제거 (첫 번째 것만 유지)
#         seen_pois = set()
#         unique_recommendations = []
#         for rec in recommendations:
#             if rec['next_poi'] not in seen_pois:
#                 seen_pois.add(rec['next_poi'])
#                 unique_recommendations.append(rec)
#                 if len(unique_recommendations) >= limit:
#                     break
        
#         return {
#             "current_sequence": req.current_poi_sequence,
#             "recommendations": unique_recommendations,
#             "total": len(unique_recommendations)
#         }
        
#     except Exception as e:
#         logger.error(f"다음 장소 추천 실패: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to recommend next places: {str(e)}"
#         )


# def find_next_poi_simple(user_sequence, pattern_sequence):
#     """사용자 시퀀스와 패턴을 비교하여 다음 POI 찾기 (단순 버전)"""
#     # 사용자 시퀀스가 패턴의 일부와 매칭되는지 확인
#     user_len = len(user_sequence)
#     pattern_len = len(pattern_sequence)
    
#     # 사용자 시퀀스의 끝부분이 패턴의 시작부분과 일치하는지 확인
#     for i in range(1, min(user_len, pattern_len) + 1):
#         user_suffix = user_sequence[-i:]  # 사용자 시퀀스의 뒤쪽 i개
#         pattern_prefix = pattern_sequence[:i]  # 패턴의 앞쪽 i개
        
#         if user_suffix == pattern_prefix:
#             # 매칭되면 패턴에서 다음 POI 반환
#             if i < pattern_len:
#                 return pattern_sequence[i]
    
#     return None




# # 사용자 선호도 관련 API
# @app.post("/preferences", response_model=UserPreferenceResponse)
# async def create_user_preference(
#     preference_data: UserPreferenceRequest,
#     db: AsyncSession = Depends(get_database_session)
# ):
#     """사용자 선호도 생성"""
#     try:
#         # 기존 선호도 확인
#         stmt = select(UserPreferenceVector).where(UserPreferenceVector.mysql_user_id == preference_data.mysql_user_id)
#         result = await db.execute(stmt)
#         existing_preference = result.scalar_one_or_none()
        
#         if existing_preference:
#             raise HTTPException(
#                 status_code=status.HTTP_409_CONFLICT,
#                 detail=f"Preference for user {preference_data.mysql_user_id} already exists"
#             )
        
#         # 새 선호도 생성 (초기 임베딩은 빈 벡터)
#         preference = UserPreferenceVector(
#             mysql_user_id=preference_data.mysql_user_id,
#             preference_weight=preference_data.preference_weight,
#             category_weight=preference_data.category_weight,
#             behavior_weight=preference_data.behavior_weight,
#             preference_embedding=[0.0] * 768,  # 초기값
#             category_preference_embedding=[0.0] * 768,  # 초기값
#             behavior_embedding=[0.0] * 768  # 초기값
#         )
        
#         db.add(preference)
#         await db.commit()
#         await db.refresh(preference)
        
#         return preference
        
#     except IntegrityError:
#         await db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail="User preference already exists"
#         )
#     except Exception as e:
#         await db.rollback()
#         logger.error(f"사용자 선호도 생성 실패: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to create user preference: {str(e)}"
#         )


# @app.get("/preferences/{user_id}", response_model=UserPreferenceResponse)
# async def get_user_preference(
#     user_id: int,
#     db: AsyncSession = Depends(get_database_session)
# ):
#     """사용자 선호도 조회"""
#     stmt = select(UserPreferenceVector).where(UserPreferenceVector.mysql_user_id == user_id)
#     result = await db.execute(stmt)
#     preference = result.scalar_one_or_none()
    
#     if not preference:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"User preference for user {user_id} not found"
#         )
    
#     return preference


# @app.put("/preferences/{user_id}", response_model=UserPreferenceResponse)
# async def update_user_preference(
#     user_id: int,
#     preference_data: UserPreferenceRequest,
#     db: AsyncSession = Depends(get_database_session)
# ):
#     """사용자 선호도 업데이트"""
#     try:
#         stmt = select(UserPreferenceVector).where(UserPreferenceVector.mysql_user_id == user_id)
#         result = await db.execute(stmt)
#         preference = result.scalar_one_or_none()
        
#         if not preference:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"User preference for user {user_id} not found"
#             )
        
#         # 가중치 업데이트
#         preference.preference_weight = preference_data.preference_weight
#         preference.category_weight = preference_data.category_weight
#         preference.behavior_weight = preference_data.behavior_weight
        
#         await db.commit()
#         await db.refresh(preference)
        
#         return preference
        
#     except Exception as e:
#         await db.rollback()
#         logger.error(f"사용자 선호도 업데이트 실패: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to update user preference: {str(e)}"
#         )


# @app.post("/preferences/{user_id}/embeddings")
# async def update_user_preference_embeddings(
#     user_id: int,
#     preference_texts: List[str] = [],
#     category_texts: List[str] = [],
#     behavior_texts: List[str] = [],
#     db: AsyncSession = Depends(get_database_session)
# ):
#     """사용자 선호도 임베딩 업데이트"""
#     try:
#         stmt = select(UserPreferenceVector).where(UserPreferenceVector.mysql_user_id == user_id)
#         result = await db.execute(stmt)
#         preference = result.scalar_one_or_none()
        
#         if not preference:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"User preference for user {user_id} not found"
#             )
        
#         # 임베딩 서비스로 새 임베딩 생성
#         embedding_service = get_embedding_service()
#         embeddings = embedding_service.encode_user_preference(
#             preference_texts=preference_texts,
#             category_texts=category_texts if category_texts else None,
#             behavior_texts=behavior_texts if behavior_texts else None
#         )
        
#         # 임베딩 업데이트
#         preference.preference_embedding = embeddings["preference_embedding"]
#         preference.category_preference_embedding = embeddings["category_preference_embedding"]
#         preference.behavior_embedding = embeddings["behavior_embedding"]
        
#         await db.commit()
#         await db.refresh(preference)
        
#         return {
#             "user_id": user_id,
#             "updated_embeddings": [
#                 "preference_embedding" if preference_texts else None,
#                 "category_preference_embedding" if category_texts else None,
#                 "behavior_embedding" if behavior_texts else None
#             ],
#             "embedding_dimensions": 768,
#             "message": "User preference embeddings updated successfully"
#         }
        
#     except Exception as e:
#         await db.rollback()
#         logger.error(f"사용자 선호도 임베딩 업데이트 실패: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to update user preference embeddings: {str(e)}"
#         )


# @app.delete("/preferences/{user_id}")
# async def delete_user_preference(
#     user_id: int,
#     db: AsyncSession = Depends(get_database_session)
# ):
#     """사용자 선호도 삭제"""
#     try:
#         stmt = select(UserPreferenceVector).where(UserPreferenceVector.mysql_user_id == user_id)
#         result = await db.execute(stmt)
#         preference = result.scalar_one_or_none()
        
#         if not preference:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"User preference for user {user_id} not found"
#             )
        
#         await db.delete(preference)
#         await db.commit()
        
#         return {"message": f"User preference for user {user_id} deleted successfully"}
        
#     except Exception as e:
#         await db.rollback()
#         logger.error(f"사용자 선호도 삭제 실패: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to delete user preference: {str(e)}"
#         )


# # 코스 반응 관련 API
# @app.post("/reactions", response_model=CourseReactionResponse)
# async def create_course_reaction(
#     reaction_data: CourseReactionRequest,
#     db: AsyncSession = Depends(get_database_session)
# ):
#     """코스 반응 생성"""
#     try:
#         # 기존 반응 확인 (동일한 사용자, 코스, 반응 타입)
#         stmt = select(CourseReaction).where(
#             CourseReaction.mysql_user_id == reaction_data.mysql_user_id,
#             CourseReaction.mysql_course_id == reaction_data.mysql_course_id,
#             CourseReaction.reaction_type == reaction_data.reaction_type.value
#         )
#         result = await db.execute(stmt)
#         existing_reaction = result.scalar_one_or_none()
        
#         if existing_reaction:
#             raise HTTPException(
#                 status_code=status.HTTP_409_CONFLICT,
#                 detail=f"Reaction of type '{reaction_data.reaction_type}' already exists for this user and course"
#             )
        
#         # 새 반응 생성
#         reaction = CourseReaction(
#             mysql_user_id=reaction_data.mysql_user_id,
#             mysql_course_id=reaction_data.mysql_course_id,
#             reaction_type=reaction_data.reaction_type.value,
#             rating=reaction_data.rating
#         )
        
#         db.add(reaction)
#         await db.commit()
#         await db.refresh(reaction)
        
#         return reaction
        
#     except IntegrityError:
#         await db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail="Course reaction already exists"
#         )
#     except Exception as e:
#         await db.rollback()
#         logger.error(f"코스 반응 생성 실패: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to create course reaction: {str(e)}"
#         )


# @app.get("/reactions/{reaction_id}", response_model=CourseReactionResponse)
# async def get_course_reaction(
#     reaction_id: int,
#     db: AsyncSession = Depends(get_database_session)
# ):
#     """코스 반응 조회"""
#     stmt = select(CourseReaction).where(CourseReaction.id == reaction_id)
#     result = await db.execute(stmt)
#     reaction = result.scalar_one_or_none()
    
#     if not reaction:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Course reaction with id {reaction_id} not found"
#         )
    
#     return reaction


# @app.get("/reactions", response_model=List[CourseReactionResponse])
# async def list_course_reactions(
#     user_id: Optional[int] = Query(None),
#     course_id: Optional[int] = Query(None),
#     reaction_type: Optional[ReactionType] = Query(None),
#     weight_applied: Optional[bool] = Query(None),
#     limit: int = Query(50, le=100),
#     offset: int = Query(0, ge=0),
#     db: AsyncSession = Depends(get_database_session)
# ):
#     """코스 반응 목록 조회 (필터링 지원)"""
#     try:
#         stmt = select(CourseReaction)
        
#         # 필터 조건
#         if user_id:
#             stmt = stmt.where(CourseReaction.mysql_user_id == user_id)
#         if course_id:
#             stmt = stmt.where(CourseReaction.mysql_course_id == course_id)
#         if reaction_type:
#             stmt = stmt.where(CourseReaction.reaction_type == reaction_type.value)
#         if weight_applied is not None:
#             stmt = stmt.where(CourseReaction.weight_applied == weight_applied)
            
#         stmt = stmt.order_by(CourseReaction.created_at.desc()).offset(offset).limit(limit)
        
#         result = await db.execute(stmt)
#         reactions = result.scalars().all()
        
#         return reactions
        
#     except Exception as e:
#         logger.error(f"코스 반응 목록 조회 실패: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to list course reactions: {str(e)}"
#         )


# @app.put("/reactions/{reaction_id}", response_model=CourseReactionResponse)
# async def update_course_reaction(
#     reaction_id: int,
#     reaction_data: CourseReactionRequest,
#     db: AsyncSession = Depends(get_database_session)
# ):
#     """코스 반응 업데이트"""
#     try:
#         stmt = select(CourseReaction).where(CourseReaction.id == reaction_id)
#         result = await db.execute(stmt)
#         reaction = result.scalar_one_or_none()
        
#         if not reaction:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"Course reaction with id {reaction_id} not found"
#             )
        
#         # 반응 정보 업데이트
#         reaction.reaction_type = reaction_data.reaction_type.value
#         reaction.rating = reaction_data.rating
#         reaction.weight_applied = False  # 업데이트 시 가중치 적용 상태 리셋
#         reaction.weight_value = 0.0
        
#         await db.commit()
#         await db.refresh(reaction)
        
#         return reaction
        
#     except Exception as e:
#         await db.rollback()
#         logger.error(f"코스 반응 업데이트 실패: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to update course reaction: {str(e)}"
#         )


# @app.delete("/reactions/{reaction_id}")
# async def delete_course_reaction(
#     reaction_id: int,
#     db: AsyncSession = Depends(get_database_session)
# ):
#     """코스 반응 삭제"""
#     try:
#         stmt = select(CourseReaction).where(CourseReaction.id == reaction_id)
#         result = await db.execute(stmt)
#         reaction = result.scalar_one_or_none()
        
#         if not reaction:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"Course reaction with id {reaction_id} not found"
#             )
        
#         await db.delete(reaction)
#         await db.commit()
        
#         return {"message": f"Course reaction {reaction_id} deleted successfully"}
        
#     except Exception as e:
#         await db.rollback()
#         logger.error(f"코스 반응 삭제 실패: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to delete course reaction: {str(e)}"
#         )


# @app.put("/reactions/{reaction_id}/weight")
# async def apply_reaction_weight(
#     reaction_id: int,
#     weight_value: float = Query(..., ge=0.0, le=1.0, description="가중치 값 (0.0 - 1.0)"),
#     db: AsyncSession = Depends(get_database_session)
# ):
#     """반응에 가중치 적용 (배치 처리용)"""
#     try:
#         stmt = select(CourseReaction).where(CourseReaction.id == reaction_id)
#         result = await db.execute(stmt)
#         reaction = result.scalar_one_or_none()
        
#         if not reaction:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"Course reaction with id {reaction_id} not found"
#             )
        
#         # 가중치 적용
#         reaction.weight_applied = True
#         reaction.weight_value = weight_value
        
#         await db.commit()
#         await db.refresh(reaction)
        
#         return {
#             "reaction_id": reaction_id,
#             "weight_applied": True,
#             "weight_value": weight_value,
#             "message": "Weight applied successfully"
#         }
        
#     except Exception as e:
#         await db.rollback()
#         logger.error(f"반응 가중치 적용 실패: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to apply reaction weight: {str(e)}"
#         )


# @app.get("/reactions/unprocessed")
# async def get_unprocessed_reactions(
#     limit: int = Query(100, le=500),
#     db: AsyncSession = Depends(get_database_session)
# ):
#     """가중치가 적용되지 않은 반응 목록 조회 (배치 처리용)"""
#     try:
#         stmt = select(CourseReaction).where(
#             CourseReaction.weight_applied == False
#         ).order_by(CourseReaction.created_at.asc()).limit(limit)
        
#         result = await db.execute(stmt)
#         reactions = result.scalars().all()
        
#         return {
#             "unprocessed_reactions": [
#                 {
#                     "id": reaction.id,
#                     "mysql_user_id": reaction.mysql_user_id,
#                     "mysql_course_id": reaction.mysql_course_id,
#                     "reaction_type": reaction.reaction_type,
#                     "rating": reaction.rating,
#                     "created_at": reaction.created_at
#                 }
#                 for reaction in reactions
#             ],
#             "total": len(reactions)
#         }
        
#     except Exception as e:
#         logger.error(f"미처리 반응 목록 조회 실패: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to get unprocessed reactions: {str(e)}"
#         )


# @app.get("/courses/{course_id}", response_model=CourseResponse)
# async def get_course(
#     course_id: int,
#     db: AsyncSession = Depends(get_database_session)
# ):
#     """MySQL 코스 ID로 코스 조회"""
#     stmt = select(CourseVector).where(CourseVector.mysql_course_id == course_id)
#     result = await db.execute(stmt)
#     course = result.scalar_one_or_none()
    
#     if not course:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Course with id {course_id} not found"
#         )
    
#     return course

