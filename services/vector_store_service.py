from typing import List, Dict, Any
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from langchain_core.documents import Document
from config.settings import settings

class VectorStoreService:
    def __init__(self, vector_size: int):
        self.collection_name = settings.qdrant_collection_name
        self.vector_size = vector_size
        print(f"Inicializando VectorStoreService para coleção: {self.collection_name}")

        if settings.qdrant_mode == "memory":
            print("Usando Qdrant in-memory")
            self.client = QdrantClient(":memory:")
        elif settings.qdrant_mode == "url":
            print(f"Conectando ao Qdrant em {settings.qdrant_url}")
            self.client =QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
            )
        else:
            raise ValueError(f"Modo qdrant invalido {settings.qdrant_mode}.")
        self._setup_collection()

    def _setup_collection(self):
        """Configura a coleção no Qdrant."""
        print(f"Configurando coleção: {self.collection_name}")
        try:
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            print(f"Coleção {self.collection_name} configurada com sucesso.")
        except Exception as e:
            print(f"Erro ao configurar coleção: {e}")
            raise RuntimeError(f"Erro ao configurar coleção: {e}")
    def upsert_documents(self, documents: List[Document], embeddings:List[List[float]]):
        """Ingere documentos e seus embeddings no Qdrant."""
        if not documents or not embeddings or len(documents) != len(embeddings):
            print("Erro: documentos e embeddings não podem ser vazios ou de tamanhos diferentes.")
            return False
        
        points_to_insert: List[PointStruct] = []
        for i, (doc, emb) in enumerate(zip(documents, embeddings)):
            if emb is None:
                print(f"Erro: embedding para o documento {i} é None.")
                continue

            payload = {
                "text": doc.page_content,
                "source": doc.metadata.get('source', 'desconhecido'),
                "page": doc.metadata.get('page', -1),
                # Adicionar outros metadados se relevante
                **doc.metadata # Adiciona todos os outros metadados
            }
            points_to_insert.append(
                PointStruct(
                    id=i, # Usar um UUID seria mais robusto: import uuid; id=str(uuid.uuid4())
                    vector=emb,
                    payload=payload
                )
            )

        if not points_to_insert:
            print("Nenhum ponto válido para inserir no Qdrant.")
            return False

        print(f"Inserindo/Atualizando {len(points_to_insert)} pontos em '{self.collection_name}'...")
        try:
            operation_info = self.client.upsert(
                collection_name=self.collection_name,
                wait=True, # Espera a operação ser concluída
                points=points_to_insert
            )
            print(f"Upsert no Qdrant concluído: {operation_info.status}")
            return operation_info.status == models.UpdateStatus.COMPLETED
        except Exception as e:
            print(f"Erro durante o upsert no Qdrant: {e}")
            return False

    def search(self, query_vector: List[float], limit: int = 3) -> List[Dict[str, Any]]:
        """Busca documentos relevantes no Qdrant."""
        if not query_vector:
            print("Erro: Vetor de busca vazio.")
            return []
        print(f"Buscando {limit} vizinhos mais próximos em '{self.collection_name}'...")
        try:
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                # score_threshold=0.5 # Opcional: definir um limiar de similaridade
            )
            # Retorna os payloads dos documentos encontrados
            # O objeto ScoredPoint tem id, version, score, payload, vector
            results = [hit.payload for hit in search_results if hit.payload]
            print(f"Busca encontrou {len(results)} resultados.")
            return results
        except Exception as e:
            print(f"Erro durante a busca no Qdrant: {e}")
            return []