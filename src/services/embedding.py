import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Union, Optional, Dict
import logging

# 로거 설정
logger = logging.getLogger(__name__)


class KoSimCSEEmbeddingService:
    """한국어 최적화 임베딩 서비스 (KoSimCSE-roberta 모델 사용)"""
    
    def __init__(self, model_name: str = "BM-K/KoSimCSE-roberta-multitask"):
        """KoSimCSE-roberta 모델로 임베딩 서비스 초기화"""
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"임베딩 모델 로드 완료: {model_name}")
        except Exception as e:
            logger.error(f"임베딩 모델 로드 실패: {e}")
            raise
    
    def encode_text(self, text: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
        """
        텍스트를 임베딩으로 변환
        
        Args:
            text: 단일 텍스트 또는 텍스트 리스트
            normalize: 코사인 유사도를 위한 정규화 여부
            
        Returns:
            임베딩 numpy 배열
        """
        try:
            embeddings = self.model.encode(text, convert_to_numpy=True)
            
            if normalize:
                # 코사인 유사도 최적화를 위한 정규화
                norm = np.linalg.norm(embeddings, axis=-1, keepdims=True)
                embeddings = embeddings / (norm + 1e-8)  # 0으로 나누는 것을 방지하기 위한 작은 값 추가
            
            return embeddings
        except Exception as e:
            logger.error(f"텍스트 인코딩 실패: {e}")
            raise
    
    def encode_course_data(self, title: str, description: str, category: str = "") -> Dict:
        """
        코스 데이터에 대한 임베딩 생성
        
        Args:
            title: 코스 제목
            description: 코스 설명
            category: 코스 카테고리 (선택사항)
            
        Returns:
            다양한 유형의 임베딩을 포함한 딕셔너리
        """
        try:
            # 개별 임베딩 (정규화되지 않은 버전)
            title_embedding = self.encode_text(title, normalize=False)
            description_embedding = self.encode_text(description, normalize=False)
            
            # 통합 임베딩 (포괄적 검색용)
            combined_text = f"{title} {description}"
            if category:
                combined_text += f" {category}"
            combined_embedding = self.encode_text(combined_text, normalize=False)
            
            # 정규화된 임베딩들은 이제 저장하지 않음
            return {
                "title_embedding": title_embedding.tolist(),
                "description_embedding": description_embedding.tolist(),
                "combined_embedding": combined_embedding.tolist(),
            }
        except Exception as e:
            logger.error(f"코스 데이터 인코딩 실패: {e}")
            raise
    
    def encode_user_preference(self, 
                              preference_texts: List[str], 
                              category_texts: List[str] = None,
                              behavior_texts: List[str] = None) -> Dict:
        """
        사용자 선호도 데이터에 대한 임베딩 생성
        
        Args:
            preference_texts: 사용자 선호도를 나타내는 텍스트 리스트
            category_texts: 카테고리별 선호도 텍스트 (선택사항)
            behavior_texts: 행동 패턴 텍스트 (선택사항)
            
        Returns:
            사용자 선호도 임베딩을 포함한 딕셔너리
        """
        try:
            # 전체 선호도 임베딩
            if preference_texts:
                combined_preference_text = " ".join(preference_texts)
                preference_embedding = self.encode_text(combined_preference_text, normalize=False)
            else:
                # 빈 선호도의 경우 제로 벡터 생성
                preference_embedding = np.zeros(768)
            
            # 카테고리별 선호도 임베딩
            if category_texts:
                combined_category_text = " ".join(category_texts)
                category_preference_embedding = self.encode_text(combined_category_text, normalize=False)
            else:
                category_preference_embedding = np.zeros(768)
            
            # 행동 패턴 임베딩
            if behavior_texts:
                combined_behavior_text = " ".join(behavior_texts)
                behavior_embedding = self.encode_text(combined_behavior_text, normalize=False)
            else:
                behavior_embedding = np.zeros(768)
            
            return {
                "preference_embedding": preference_embedding.tolist(),
                "category_preference_embedding": category_preference_embedding.tolist(),
                "behavior_embedding": behavior_embedding.tolist(),
            }
            
        except Exception as e:
            logger.error(f"사용자 선호도 데이터 인코딩 실패: {e}")
            raise
    
    def encode_pattern_sequence(self, poi_names: List[str]) -> np.ndarray:
        """
        장소 패턴 시퀀스에 대한 임베딩 생성
        
        Args:
            poi_names: 해당 POI 이름들
            
        Returns:
            패턴 임베딩 numpy 배열
        """
        try:
            # POI 이름들을 순서대로 결합하여 패턴 텍스트 생성
            pattern_text = " → ".join(poi_names)
            pattern_embedding = self.encode_text(pattern_text, normalize=False)
            
            return pattern_embedding
        except Exception as e:
            logger.error(f"패턴 시퀀스 인코딩 실패: {e}")
            raise
        
    def encode_search_query(self, keyword: str) -> Dict:
        """
        사용자 검색어(keyword)를 분석하여 임베딩을 위한 '가상 코스' 필드를 생성하고 벡터를 반환합니다.

        Args:
            keyword: 사용자 검색어

        Returns:
            분석된 필드와 임베딩 벡터를 포함한 딕셔너리 (FastAPI 응답 DTO에 매핑됨)
        """

        # 1. 텍스트 분리 및 분석 로직 (NLP 기반의 역할)
        # ----------------------------------------------------
        # title: 전체 검색어를 대표 이름으로 사용
        title = f"사용자 검색: {keyword}" 

        # description: 검색어를 그대로 설명으로 사용 (가장 높은 의미적 연관성 유지)
        description = keyword

        # category: 내부 추론 함수를 통해 추론
        category = self._infer_category_from_keyword(keyword)
        # ----------------------------------------------------

        try:
            # 2. 통합 임베딩 생성 (기존 encode_course_data 로직과 유사)
            combined_text = f"{title} {description}"
            if category:
                combined_text += f" {category}"

            # KoSimCSE 모델을 사용하여 의미 기반 분석 및 벡터 생성
            combined_embedding = self.encode_text(combined_text, normalize=False)

            # 3. Spring에 반환할 형태로 데이터 구조화
            return {
                "course_name": title,
                "course_description": description,
                "category": category,
                "embeddings": {
                    # 검색 쿼리는 주로 하나의 통합 벡터만 사용합니다.
                    "search_query_combined": combined_embedding.tolist(),
                }
            }
        except Exception as e:
            logger.error(f"검색어 인코딩 실패: {e}")
            raise

    def _infer_category_from_keyword(self, keyword: str) -> Optional[str]:
        """
        (가정) 단순 규칙 기반으로 키워드에서 카테고리를 추론하는 내부 함수
        실제 서비스에서는 복잡한 맵핑 테이블, 분류 모델 또는 NER이 필요합니다.
        """
        keyword_lower = keyword.lower()
        if '맛집' in keyword_lower or '카페' in keyword_lower or '식당' in keyword_lower:
            return "음식/식도락"
        if '등산' in keyword_lower or '트레킹' in keyword_lower or '자전거' in keyword_lower:
            return "액티비티/운동"
        if '역사' in keyword_lower or '박물관' in keyword_lower or '전시' in keyword_lower:
            return "문화/역사"
        return None

# 전역 인스턴스
_embedding_service = None

def get_embedding_service() -> KoSimCSEEmbeddingService:
    """싱글톤 임베딩 서비스 인스턴스 반환"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = KoSimCSEEmbeddingService()
    return _embedding_service