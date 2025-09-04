-- Extensions 활성화
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;


-- 1. 장소 패턴 테이블 (순서 및 조합 기반 추천)
CREATE TABLE place_patterns (
    id SERIAL PRIMARY KEY,
    poi_ids INTEGER[] NOT NULL UNIQUE,  -- 장소 ID 배열 (순서 유지)
    pattern_embedding vector(768);

    -- 사용 통계
    sequence_count INTEGER DEFAULT 0,     -- 이 순서로 방문한 횟수
    relation_count INTEGER DEFAULT 0,
    total_usage INTEGER GENERATED ALWAYS AS (sequence_count + relation_count) STORED,       -- 이 조합 총 방문 횟수

    -- 점수 (계산된 값)
    sequence_score FLOAT DEFAULT 0.0,      -- 순서 추천 점수
    relation_score FLOAT DEFAULT 0.0,      -- 관계 추천 점수

    -- 메타데이터 (검색 최적화용)
    pattern_length SMALLINT GENERATED ALWAYS AS (array_length(poi_ids, 1)) STORED,
    first_poi INTEGER GENERATED ALWAYS AS (poi_ids[1]) STORED,  -- 시작 POI (인덱스용)
    last_poi INTEGER GENERATED ALWAYS AS (poi_ids[array_length(poi_ids, 1)]) STORED,  -- 마지막 POI

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- 1. 코스 벡터 테이블 (의미 기반 검색)
CREATE TABLE IF NOT EXISTS course_vectors (
    id SERIAL PRIMARY KEY,
    mysql_course_id INTEGER UNIQUE NOT NULL,

    -- 의미 검색용 임베딩 (원본 벡터 저장)
    title_embedding vector(768),
    description_embedding vector(768), 
    combined_embedding vector(768),

    -- 패턴 참조
    main_pattern_id INTEGER REFERENCES place_patterns(id) ON DELETE SET NULL, -- 메인 패턴
    sub_pattern_ids INTEGER[],                             -- 서브 패턴들 (부분 패턴)

    -- 하이브리드 검색용 (벡터 + 필터)
    region VARCHAR(50),
    category VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 사용자 선호 벡터 (개인화 추천)
CREATE TABLE IF NOT EXISTS user_preference_vectors (
    id SERIAL PRIMARY KEY,
    mysql_user_id INTEGER UNIQUE NOT NULL,
    
    -- 사용자 선호도 임베딩
    preference_embedding vector(768),         -- 전체 선호도
    category_preference_embedding vector(768), -- 카테고리별 선호
    behavior_embedding vector(768),           -- 행동 패턴
    
    
    -- 선호도 가중치 (0.0 ~ 1.0)
    preference_weight FLOAT DEFAULT 0.4,
    category_weight FLOAT DEFAULT 0.3,
    behavior_weight FLOAT DEFAULT 0.3,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 코스 반응 테이블 (패턴 가중치 조정용)
CREATE TABLE IF NOT EXISTS course_reactions (
    id SERIAL PRIMARY KEY,
    mysql_user_id INTEGER NOT NULL,
    mysql_course_id INTEGER NOT NULL,
    
    -- 반응 정보
    reaction_type VARCHAR(50) NOT NULL CHECK (
        reaction_type IN ('like', 'save', 'share')
    ),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    
    -- 가중치 계산 정보
    weight_applied BOOLEAN DEFAULT FALSE,
    weight_value FLOAT DEFAULT 0.0,                      -- 적용된 가중치 값
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 중복 방지
    UNIQUE(mysql_user_id, mysql_course_id, reaction_type)
);

-- 1. place_patterns 인덱스 (패턴 검색 최적화)
CREATE INDEX idx_place_patterns_poi_ids ON place_patterns USING gin(poi_ids);
CREATE INDEX idx_place_patterns_first_poi ON place_patterns(first_poi, sequence_score DESC);
CREATE INDEX idx_place_patterns_last_poi ON place_patterns(last_poi);
CREATE INDEX idx_place_patterns_length_score ON place_patterns(pattern_length, total_usage DESC);
CREATE INDEX idx_pattern_embedding ON place_patterns USING hnsw (pattern_embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);


-- 패턴 점수별 정렬 (추천용)
CREATE INDEX idx_place_patterns_sequence_score ON place_patterns(sequence_score DESC) WHERE sequence_count > 0;
CREATE INDEX idx_place_patterns_relation_score ON place_patterns(relation_score DESC) WHERE relation_count > 0;

-- 2. course_vectors 벡터 검색 인덱스 (HNSW)
CREATE INDEX idx_course_combined_embedding 
    ON course_vectors USING hnsw (combined_embedding vector_cosine_ops) 
    WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_course_title_embedding 
    ON course_vectors USING hnsw (title_embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- 패턴 참조 인덱스
CREATE INDEX idx_course_main_pattern ON course_vectors(main_pattern_id) WHERE main_pattern_id IS NOT NULL;
CREATE INDEX idx_course_sub_patterns ON course_vectors USING gin(sub_pattern_ids);

-- 하이브리드 검색용 복합 인덱스
CREATE INDEX idx_course_region_category ON course_vectors(region, category);

-- 3. user_preference_vectors 인덱스
CREATE INDEX idx_user_preference_embedding 
    ON user_preference_vectors USING hnsw (preference_embedding vector_cosine_ops)
    WITH (m = 8, ef_construction = 32);  -- 사용자 데이터는 상대적으로 적으므로 작은 값

-- 4. course_reactions 인덱스 (배치 처리 최적화)
CREATE INDEX idx_reactions_unprocessed ON course_reactions(weight_applied, created_at) 
    WHERE weight_applied = FALSE;

CREATE INDEX idx_reactions_user_course ON course_reactions(mysql_user_id, mysql_course_id);
CREATE INDEX idx_reactions_course_type ON course_reactions(mysql_course_id, reaction_type);

-- =====================================================
-- 성능 최적화 설정
-- =====================================================

-- HNSW 검색 성능 향상
SET hnsw.ef_search = 40;  -- 검색 시 탐색할 후보 수

-- 벡터 연산 최적화
SET max_parallel_workers_per_gather = 2;
SET work_mem = '256MB';

-- 통계 수집 (쿼리 플랜 최적화)
ANALYZE place_patterns;
ANALYZE course_vectors;
ANALYZE user_preference_vectors;
ANALYZE course_reactions;