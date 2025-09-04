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


# 전역 인스턴스
_embedding_service = None

def get_embedding_service() -> KoSimCSEEmbeddingService:
    """싱글톤 임베딩 서비스 인스턴스 반환"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = KoSimCSEEmbeddingService()
    return _embedding_service