from typing import List, Dict, Any, Optional 
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import PointStruct
from langchain_core.documents import Document
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings
import math
import uuid 
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
            self.client = QdrantClient(
                host=settings.qdrant_url, # Em versões mais recentes, pode ser 'url='
                api_key=settings.qdrant_api_key,
                # Considere adicionar um timeout, ex: timeout=20 (em segundos)
                # timeout=settings.qdrant_timeout or 20
            )
        else:
            raise ValueError(f"Modo qdrant inválido {settings.qdrant_mode}.")
        self._setup_collection()
        # É uma boa prática garantir que campos usados para filtragem estejam indexados
        self._ensure_payload_index("course_id")
        # Você também pode querer indexar 'source' se for filtrar por ele frequentemente
        # self._ensure_payload_index("source")


    def _setup_collection(self):
        print(f"Verificando/Configurando coleção: {self.collection_name}")
        try:
            self.client.get_collection(collection_name=self.collection_name)
            print(f"Coleção '{self.collection_name}' já existe. Usando a existente.")
        except Exception as e:
            # Em qdrant-client >= 1.1.1, um erro específico pode ser qdrant_client.http.exceptions.UnexpectedResponseError
            # ou um genérico se a conexão falhar.
            print(f"Coleção '{self.collection_name}' não encontrada ou erro ao acessá-la. Tentando criar... Erro original: {type(e).__name__} - {e}")
            try:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.vector_size,
                        distance=models.Distance.COSINE
                    )
                )
                print(f"Coleção '{self.collection_name}' criada com sucesso.")
            except Exception as create_e:
                print(f"Erro CRÍTICO ao TENTAR CRIAR a coleção '{self.collection_name}': {type(create_e).__name__} - {create_e}")
                raise RuntimeError(f"Falha ao garantir a existência/criação da coleção '{self.collection_name}': {create_e}")


    def _ensure_payload_index(self, field_name: str, field_type: models.PayloadSchemaType = models.PayloadSchemaType.KEYWORD):
        try:
            collection_info = self.client.get_collection(collection_name=self.collection_name)
            current_schema = getattr(collection_info.config.params, 'payload_schema', {}) 
            if not current_schema: 
                 current_schema = collection_info.payload_schema or {}


            if field_name not in current_schema:
                print(f"Criando indice payload para o campo '{field_name}' na coleção '{self.collection_name}'...")
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=field_type 
                )
                print(f"Índice de payload '{field_name}' criado com sucesso.")
            else:
                print(f"Índice de payload '{field_name}' já existe na coleção '{self.collection_name}'.")
        except Exception as e:
            print(f"Erro/Aviso ao garantir o índice de payload '{field_name}' na coleção '{self.collection_name}': {type(e).__name__} - {e}")
            print("Isso pode ser normal se o índice já existia e a verificação não o detectou precisamente ou se houve outro problema.")


    def upsert_documents(self,
                         documents: List[Document],
                         embeddings: List[List[float]],
                         id_course: str,
                         batch_size: int = 100):
        if not documents or not embeddings or len(documents) != len(embeddings):
            print("Erro: documentos e embeddings não podem ser vazios ou de tamanhos diferentes.")
            return False

        total_docs = len(documents)
        num_batches = math.ceil(total_docs / batch_size)
        print(f"Curso ID: {id_course}) Preparando para inserir/atualizar {total_docs} pontos em {num_batches} lotes de até {batch_size} pontos cada...")

        all_successful = True

        for i in range(num_batches):
            start_index = i * batch_size
            end_index = min((i + 1) * batch_size, total_docs)
            current_batch_docs = documents[start_index:end_index]
            current_batch_embeddings = embeddings[start_index:end_index]

            points_to_insert: List[PointStruct] = []
            for j, (doc, emb) in enumerate(zip(current_batch_docs, current_batch_embeddings)):
                if emb is None:
                    print(f"Erro: embedding para o documento no índice global {start_index + j} (batch index {j}) é None. Pulando.")
                    all_successful = False 
                    continue

                payload = {
                    "text": doc.page_content,
                    "course_id": id_course, 
                    **doc.metadata 
                }
                payload.setdefault('source', 'desconhecido')
                payload.setdefault('page', -1)
                point_id = str(uuid.uuid4())
                points_to_insert.append(
                    PointStruct(
                        id=point_id,
                        vector=emb,
                        payload=payload
                    )
                )

            if not points_to_insert:
                print(f"Lote {i+1}/{num_batches}: Nenhum ponto válido para inserir. Pulando lote.")
                continue

            print(f"Lote {i+1}/{num_batches}: Inserindo/Atualizando {len(points_to_insert)} pontos...")
            try:
                operation_info = self.client.upsert(
                    collection_name=self.collection_name,
                    wait=True,
                    points=points_to_insert
                )
                print(f" -> Lote {i+1} Upsert Status: {operation_info.status}")
                if operation_info.status != models.UpdateStatus.COMPLETED:
                    all_successful = False
                    print(f" -> AVISO: Lote {i+1} não foi completado com sucesso segundo o status retornado.")
            except Exception as e:
                print(f"Erro CRÍTICO durante o upsert do Lote {i+1}/{num_batches}: {type(e).__name__} - {e}")
                # Adicionar mais detalhes do erro se possível, especialmente se for erro do Qdrant
                if hasattr(e, 'details'):
                    print(f"   Detalhes do erro: {e.details}") 
                elif hasattr(e, 'response_content'):
                    print(f"   Conteúdo da resposta do erro: {e.response_content}") 

                all_successful = False
        
        if all_successful:
            print(f"Curso ID: {id_course} - Todos os {num_batches} lotes processados (ou nenhum erro crítico encontrado).")
        else:
            print(f"Curso ID: {id_course} - Processamento de lotes concluído, mas ocorreram erros ou avisos.")
        return all_successful

    def search(self, query_vector: List[float], limit: int = 3, filter: Optional[models.Filter] = None) -> List[Dict[str, Any]]: # Mudei Dict para models.Filter
        """Busca documentos relevantes no Qdrant, opcionalmente filtrando por course_id."""
        if not query_vector: 
            print("Erro: Vetor de busca vazio.")
            return []

        print(f"Buscando {limit} vizinhos mais próximos em '{self.collection_name}' com filtro: {filter}...")
        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=filter, 
                limit=limit,
                with_payload=True
            )
            # Formatar os resultados para serem mais consumíveis
            results = []
            for hit in search_result:
                payload = hit.payload or {} 
                results.append({
                    "id": hit.id, 
                    "text": payload.get("text", ""),
                    "source": payload.get("source", "desconhecido"),
                    "page": payload.get("page", -1),
                    "course_id": payload.get("course_id", "desconhecido"), # Retornar course_id também
                    "score": hit.score,
                    "metadata": payload 
                })
            return results
        except Exception as e:
            print(f"Erro durante a busca vetorial: {type(e).__name__} - {e}")
            return []

    def get_all_by_course_id(self, course_id_filter: str, limit: int = 1000, offset: Optional[Any] = None) -> List[Dict[str, Any]]: # Offset pode ser int ou UUID dependendo da versão
        """
        Recupera todos os documentos (apenas payload) para um course_id específico usando scroll.
        Lida com paginação básica até o limite especificado.
        """
        if not course_id_filter:
            print("Erro: Filtro de ID do curso vazio.")
            return []

        print(f"Buscando todos os documentos em '{self.collection_name}' para course_id: {course_id_filter} com limite de {limit}...")

        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="course_id",
                    match=models.MatchValue(value=course_id_filter)
                )
            ]
        )

        all_payloads: List[Dict[str, Any]] = []
        current_offset = offset 

        try:
            while len(all_payloads) < limit:
                scroll_batch_limit = min(100, limit - len(all_payloads))
                if scroll_batch_limit <= 0:
                    break

                scroll_response_tuple = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=query_filter,
                    limit=scroll_batch_limit,
                    offset=current_offset,
                    with_payload=True,
                    with_vectors=False
                )
                points = scroll_response_tuple[0]
                next_page_offset = scroll_response_tuple[1]

                for hit in points:
                    if hit.payload:
                        payload_to_return = {"id": hit.id, **hit.payload}
                        all_payloads.append(payload_to_return) 

                current_offset = next_page_offset 
                
                if not points or next_page_offset is None:
                    break 

            print(f"Busca por scroll para course_id '{course_id_filter}' encontrou {len(all_payloads)} resultados.")
            return all_payloads

        except Exception as e:
            print(f"Erro CRÍTICO durante a busca por scroll no Qdrant para course_id '{course_id_filter}': {type(e).__name__} - {e}")
            import traceback
            traceback.print_exc()
            return []