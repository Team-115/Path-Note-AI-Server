-- Extensions 활성화
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 1. 코스 벡터 테이블 (의미 기반 검색)
CREATE TABLE IF NOT EXISTS course_vectors (
    id SERIAL PRIMARY KEY,
    mysql_course_id INTEGER UNIQUE NOT NULL,

    -- 다각도 의미 검색(제목+설명+카테고리)
    title_embedding vector(768),        -- 제목 임베딩
    description_embedding vector(768),   -- 설명 임베딩
    combined_embedding vector(768),      -- 통합 임베딩 (제목+설명+카테고리)

    -- 하이브리드 검색용 (벡터 + 필터)
    region VARCHAR(50),
    duration_minutes INTEGER, -- minutes

    -- 의미 검색용 메타데이터
    semantic_tags vector(768),          -- 태그 통합 임베딩
    user_profile_embedding vector(768),  -- 타겟 사용자 프로필 임베딩

    -- 검색 최적화용 정규화된 벡터 (코사인 유사도 최적화)
    title_embedding_norm vector(768),
    description_embedding_norm vector(768),
    combined_embedding_norm vector(768),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 장소 벡터 테이블 (의미 기반 장소 추천)
CREATE TABLE place_vectors (
    id SERIAL PRIMARY KEY,
    poi_id INTEGER UNIQUE NOT NULL,
    
    -- 장소 임베딩
    place_embedding vector(768),         -- 장소명 + 카테고리 임베딩
    context_embedding vector(768),       -- 주변 맥락 임베딩
    
    -- 위치 벡터 (지리적 유사도)
    -- 2D 벡터로 위도/경도를 정규화하여 저장
    location_vector vector(2),           -- [normalized_lat, normalized_lng]
    latitude DECIMAL(10, 8),    -- 실제 좌표(거리계산용)
    longitude DECIMAL(11, 8),
    
    -- 시간대별 임베딩 (시간 맥락 추천)
    morning_embedding vector(768),       -- 아침 문맥 임베딩
    afternoon_embedding vector(768),     -- 오후 문맥 임베딩
    evening_embedding vector(768),       -- 저녁 문맥 임베딩
    
    -- 하이브리드 검색용
    category VARCHAR(100),
    region VARCHAR(50),
    popularity_score FLOAT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 사용자 선호 벡터 (개인화 추천)
CREATE TABLE user_preference_vectors (
    id SERIAL PRIMARY KEY,
    mysql_user_id INTEGER UNIQUE NOT NULL,
    
    -- 사용자 선호도 임베딩 (학습된)
    preference_embedding vector(768),     -- 전체 선호도
    
    -- 카테고리별 선호 벡터
    category_preference_embedding vector(768),
    
    -- 행동 패턴 임베딩
    behavior_embedding vector(768),       -- 검색/클릭 패턴 기반
    
    -- 동적 컨텍스트 임베딩
    recent_context_embedding vector(768), -- 최근 활동 기반
    
    -- 선호도 강도 (가중치)
    preference_weights JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 코스 패턴 벡터 (순서 패턴 학습)
CREATE TABLE vector_patterns (
    id SERIAL PRIMARY KEY,
    
    -- 패턴 식별
    pattern_key VARCHAR(255) UNIQUE NOT NULL,  -- 'seq:101-102-103' or 'rel:101-102'
    pattern_type VARCHAR(50) NOT NULL,  -- 'sequence_full', 'sequence_partial', 'relation'
    
    -- 데이터
    items INTEGER[] NOT NULL,
    items_length INTEGER GENERATED ALWAYS AS (array_length(items, 1)) STORED,
    embedding vector(768),
    
    -- 학습 정보
    occurrence_count INTEGER DEFAULT 1,
    confidence FLOAT DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
    
    -- 메타데이터
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 1. course_vectors 인덱스
-- =====================================================

-- 벡터 검색 인덱스 (IVFFlat - 빠른 근사 검색)
CREATE INDEX idx_course_title_emb 
    ON course_vectors USING ivfflat (title_embedding vector_cosine_ops) 
    WITH (lists = 100);

CREATE INDEX idx_course_desc_emb 
    ON course_vectors USING ivfflat (description_embedding vector_cosine_ops) 
    WITH (lists = 100);

CREATE INDEX idx_course_combined_emb 
    ON course_vectors USING ivfflat (combined_embedding vector_cosine_ops) 
    WITH (lists = 100);

-- 정규화된 벡터 인덱스 (내적 연산용)
CREATE INDEX idx_course_title_norm 
    ON course_vectors USING ivfflat (title_embedding_norm vector_ip_ops) 
    WITH (lists = 100);

CREATE INDEX idx_course_combined_norm 
    ON course_vectors USING ivfflat (combined_embedding_norm vector_ip_ops) 
    WITH (lists = 100);

-- 필터링용 인덱스
CREATE INDEX idx_course_region ON course_vectors(region);
CREATE INDEX idx_course_duration ON course_vectors(duration_minutes);
-- CREATE INDEX idx_course_price ON course_vectors(price_level); -- price_level column not defined

-- 복합 인덱스 (자주 함께 사용되는 필터)
CREATE INDEX idx_course_region_duration 
    ON course_vectors(region, duration_minutes);

-- 유니크 제약
CREATE UNIQUE INDEX idx_course_mysql_id ON course_vectors(mysql_course_id);

-- =====================================================
-- 2. place_vectors 인덱스
-- =====================================================

-- 벡터 검색 인덱스
CREATE INDEX idx_place_emb 
    ON place_vectors USING ivfflat (place_embedding vector_cosine_ops) 
    WITH (lists = 100);

CREATE INDEX idx_place_context_emb 
    ON place_vectors USING ivfflat (context_embedding vector_cosine_ops) 
    WITH (lists = 100);

-- 위치 벡터 인덱스 (L2 거리)
CREATE INDEX idx_place_location 
    ON place_vectors USING ivfflat (location_vector vector_l2_ops) 
    WITH (lists = 50);

-- 시간대별 임베딩 인덱스 (선택적)
CREATE INDEX idx_place_morning_emb 
    ON place_vectors USING ivfflat (morning_embedding vector_cosine_ops) 
    WITH (lists = 50);

-- 지리적 검색용 인덱스
CREATE INDEX idx_place_coords ON place_vectors(latitude, longitude);
CREATE INDEX idx_place_region_category ON place_vectors(region, category);

-- 인기도 인덱스
CREATE INDEX idx_place_popularity ON place_vectors(popularity_score DESC);

-- 유니크 제약
CREATE UNIQUE INDEX idx_place_poi_id ON place_vectors(poi_id);

-- =====================================================
-- 3. user_preference_vectors 인덱스
-- =====================================================

-- 벡터 검색 인덱스 (사용자 수가 적으므로 lists 작게)
CREATE INDEX idx_user_pref_emb 
    ON user_preference_vectors USING ivfflat (preference_embedding vector_cosine_ops) 
    WITH (lists = 10);

CREATE INDEX idx_user_category_emb 
    ON user_preference_vectors USING ivfflat (category_preference_embedding vector_cosine_ops) 
    WITH (lists = 10);

-- 메타데이터 인덱스
CREATE INDEX idx_user_updated ON user_preference_vectors(updated_at DESC);
CREATE INDEX idx_user_interactions ON user_preference_vectors(total_interactions DESC);

-- 유니크 제약
CREATE UNIQUE INDEX idx_user_mysql_id ON user_preference_vectors(mysql_user_id);

-- =====================================================
-- 4. vector_patterns 인덱스
-- =====================================================

-- 벡터 검색 인덱스
CREATE INDEX idx_pattern_emb 
    ON vector_patterns USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);

-- 패턴 검색용 인덱스
CREATE INDEX idx_pattern_type ON vector_patterns(pattern_type);
CREATE INDEX idx_pattern_items ON vector_patterns USING gin(items);
CREATE INDEX idx_pattern_length ON vector_patterns(items_length);

-- 신뢰도/빈도 인덱스
CREATE INDEX idx_pattern_confidence ON vector_patterns(confidence DESC);
CREATE INDEX idx_pattern_occurrence ON vector_patterns(occurrence_count DESC);

-- 복합 인덱스 (자주 사용되는 쿼리)
CREATE INDEX idx_pattern_type_confidence 
    ON vector_patterns(pattern_type, confidence DESC);

-- 메타데이터 인덱스 (JSONB)
CREATE INDEX idx_pattern_metadata ON vector_patterns USING gin(metadata);


-- =====================================================
-- 통계 수집 (성능 최적화)
-- =====================================================

-- 테이블 통계 수집
ANALYZE course_vectors;
ANALYZE place_vectors;
ANALYZE user_preference_vectors;
ANALYZE vector_patterns;