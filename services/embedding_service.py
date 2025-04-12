from typing import List
from fastembed import TextEmbedding
from langchain_core.documents import Document
from config.settings import settings 

class EmbeddingService:
    def __init__(self):
        print(f"Inicializando embeddings com {settings.embedding_model_name}")
        try:
            self.model = TextEmbedding(settings.embedding_model_name, cache_dir=settings.embedding_cache_dir)
            self._determine_dimension()
        except Exception as e:
            print(f"Erro ao inicializar o modelo de embeddings: {e}")
            raise RuntimeError(f"Erro ao inicializar o modelo de embeddings: F{e}")
    
    def _determine_dimension(self):
        """Tenta determinar a dimensão do vetor de embedding."""
        try:
            teste_embedding = list(self.model.embed(['test']))[0]
            self.dimension = len(teste_embedding)
            print(f"Dimensão do embedding: {self.dimension}")
        except Exception as e:
            print(f"Erro ao determinar a dimensão do embedding: {e}")
            raise RuntimeError(f"Erro ao determinar a dimensão do embedding: {e}")

    def get_embedding_dimension(self) -> int:
        """Retorna a dimensão do vetor de embedding."""
        if not hasattr(self, 'dimension'):
            raise RuntimeError("Dimensão do embedding não foi determinada.")
        return self.dimension

    def embed_texts(self, texts: List[str] | List[Document]) -> List[List[float]]:
        """Gera embeddings para uma lista de textos ou documentos."""
        if not texts:
            return []
        print(f"Gerando embeddings para {len(texts)} itens...")
        try:
            embeddings_generator = self.model.embed(texts)
            embeddings_list = [emb.tolist() for emb in embeddings_generator]
            print("Embeddings gerados.")
            return embeddings_list
        except Exception as e:
            print(f"Erro ao gerar embeddings: {e}")
            return []
    def embed_single_text(self, text:str) -> List[float] | None:
        """Gera um embedding para um único texto."""
        if not text:
            return None
        try:
            embedding = list(self.model.embed([text]))[0]
            return embedding.tolist()
        except Exception as e:
            print(f"Erro ao gerar embedding: {e}")
            return None
