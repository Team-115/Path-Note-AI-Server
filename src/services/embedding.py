import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Union, Optional
import logging

logger = logging.getLogger(__name__)


class KoSimCSEEmbeddingService:
    """Korean-optimized embedding service using KoSimCSE-roberta model."""
    
    def __init__(self, model_name: str = "BM-K/KoSimCSE-roberta-multitask"):
        """Initialize the embedding service with KoSimCSE-roberta model."""
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Loaded embedding model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def encode_text(self, text: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
        """
        Encode text into embeddings.
        
        Args:
            text: Single text or list of texts to encode
            normalize: Whether to normalize the embeddings for cosine similarity
            
        Returns:
            Numpy array of embeddings
        """
        try:
            embeddings = self.model.encode(text, convert_to_numpy=True)
            
            if normalize:
                # Normalize for cosine similarity optimization
                norm = np.linalg.norm(embeddings, axis=-1, keepdims=True)
                embeddings = embeddings / (norm + 1e-8)  # Add small epsilon to avoid division by zero
            
            return embeddings
        except Exception as e:
            logger.error(f"Failed to encode text: {e}")
            raise
    
    def encode_course_data(self, title: str, description: str, category: str = "") -> dict:
        """
        Generate embeddings for course data.
        
        Args:
            title: Course title
            description: Course description
            category: Course category (optional)
            
        Returns:
            Dictionary containing different types of embeddings
        """
        try:
            # Individual embeddings
            title_embedding = self.encode_text(title, normalize=False)
            description_embedding = self.encode_text(description, normalize=False)
            
            # Combined embedding for comprehensive search
            combined_text = f"{title} {description}"
            if category:
                combined_text += f" {category}"
            combined_embedding = self.encode_text(combined_text, normalize=False)
            
            # Normalized versions for cosine similarity
            title_embedding_norm = self.encode_text(title, normalize=True)
            combined_embedding_norm = self.encode_text(combined_text, normalize=True)
            
            # Semantic tags embedding (combining all metadata)
            semantic_text = f"{title} {description} {category}".strip()
            semantic_tags = self.encode_text(semantic_text, normalize=False)
            
            return {
                "title_embedding": title_embedding.tolist(),
                "description_embedding": description_embedding.tolist(),
                "combined_embedding": combined_embedding.tolist(),
                "title_embedding_norm": title_embedding_norm.tolist(),
                "combined_embedding_norm": combined_embedding_norm.tolist(),
                "semantic_tags": semantic_tags.tolist(),
            }
        except Exception as e:
            logger.error(f"Failed to encode course data: {e}")
            raise
    
    def encode_place_data(self, 
                         place_name: str, 
                         category: str = "", 
                         context: str = "",
                         latitude: Optional[float] = None,
                         longitude: Optional[float] = None) -> dict:
        """
        Generate embeddings for place data.
        
        Args:
            place_name: Name of the place
            category: Place category
            context: Additional context about the place
            latitude: Place latitude
            longitude: Place longitude
            
        Returns:
            Dictionary containing different types of embeddings
        """
        try:
            # Place embedding (name + category)
            place_text = f"{place_name}"
            if category:
                place_text += f" {category}"
            place_embedding = self.encode_text(place_text, normalize=False)
            
            # Context embedding
            context_text = context if context else place_text
            context_embedding = self.encode_text(context_text, normalize=False)
            
            # Location vector (normalized lat/lng)
            location_vector = None
            if latitude is not None and longitude is not None:
                # Normalize coordinates to [-1, 1] range
                # This is a simple normalization; in production, consider more sophisticated methods
                norm_lat = latitude / 90.0  # Latitude range: -90 to 90
                norm_lng = longitude / 180.0  # Longitude range: -180 to 180
                location_vector = [norm_lat, norm_lng]
            
            # Time-specific embeddings (can be enhanced with actual time-based context)
            time_contexts = {
                "morning": f"{place_text} 아침 오전",
                "afternoon": f"{place_text} 오후 점심",
                "evening": f"{place_text} 저녁 밤"
            }
            
            time_embeddings = {}
            for time_period, time_text in time_contexts.items():
                time_embeddings[f"{time_period}_embedding"] = self.encode_text(time_text, normalize=False).tolist()
            
            result = {
                "place_embedding": place_embedding.tolist(),
                "context_embedding": context_embedding.tolist(),
                **time_embeddings
            }
            
            if location_vector:
                result["location_vector"] = location_vector
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to encode place data: {e}")
            raise


# Global instance
_embedding_service = None

def get_embedding_service() -> KoSimCSEEmbeddingService:
    """Get singleton embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = KoSimCSEEmbeddingService()
    return _embedding_service