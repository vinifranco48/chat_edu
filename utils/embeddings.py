from fastembed import TextEmbedding
from typing import List
import logging

logger = logging.getLogger(__name__)

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

def get_embeddings_model():
    """Retorna o modelo de embedding FastEmbed"""
    return TextEmbedding(MODEL_NAME)

def generate_embeddings(texts: List[str]):
    """Gera embeddings para uma lista de textos"""
    try:
        embedding_model = get_embeddings_model()
        embeddings_generator = embedding_model.embed(texts)
        embeddings = list(embeddings_generator)
        logger.info(f"Gerados {len(embeddings)} embeddings")
        return embeddings
    except Exception as e:
        logger.error(f"Erro ao gerar embeddings: {str(e)}")
        raise
