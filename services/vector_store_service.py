# services/vector_store_service.py
from typing import List, Dict, Any, Optional # Adicionar Optional
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import PointStruct
from langchain_core.documents import Document
from config.settings import settings
import math

class VectorStoreService:
    def __init__(self, vector_size: int):
        self.collection_name = settings.qdrant_collection_name
        self.vector_size = vector_size # Guardar para uso potencial, ex: fallback para search
        print(f"Inicializando VectorStoreService para coleção: {self.collection_name}")

        if settings.qdrant_mode == "memory":
            print("Usando Qdrant in-memory")
            self.client = QdrantClient(":memory:")
        elif settings.qdrant_mode == "url":
            print(f"Conectando ao Qdrant em {settings.qdrant_url}")
            self.client =QdrantClient(
                host=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
            )
        else:
            raise ValueError(f"Modo qdrant invalido {settings.qdrant_mode}.")
        self._setup_collection()
        # É uma boa prática garantir que campos usados para filtragem estejam indexados
        self._ensure_payload_index("course_id")

    def _setup_collection(self):
        # ... (seu método _setup_collection existente)
        print(f"Verificando/Configurando coleção: {self.collection_name}")
        try:
            self.client.get_collection(collection_name=self.collection_name)
            print(f"Coleção '{self.collection_name}' já existe. Usando a existente.")
        except Exception as e:
            print(f"Coleção '{self.collection_name}' não encontrada ou erro ao acessá-la. Tentando criar... Erro original: {type(e).__name__}")
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
        # ... (seu método _ensure_payload_index existente)
        try:
            collection_info = self.client.get_collection(collection_name=self.collection_name)
            # Ajuste para verificar se o esquema de payload existe e o campo nele
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
            print(f"Erro ao garantir o índice de payload '{field_name}' na coleção '{self.collection_name}': {type(e).__name__} - {e}")


    def upsert_documents(self,
                         documents: List[Document],
                         embeddings: List[List[float]],
                         id_course: str,
                         batch_size: int = 100):
        # ... (seu método upsert_documents existente)
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
                    print(f"Erro: embedding para o documento no índice global {start_index + j} é None. Pulando.")
                    continue

                payload = {
                    "text": doc.page_content,
                    "source": doc.metadata.get('source', 'desconhecido'),
                    "page": doc.metadata.get('page', -1),
                    "course_id": id_course,
                    **doc.metadata
                }
                # É crucial ter um ID único e estável para cada documento/chunk
                # Usar start_index + j é simples mas pode causar colisões se re-ingerir sem limpar.
                # Considere um UUID ou hash do conteúdo + source + page.
                point_id = f"{id_course}_{doc.metadata.get('source', 'unknown')}_{doc.metadata.get('page', -1)}_{start_index + j}"
                # Ou, se os documentos já tiverem IDs estáveis, use-os.

                points_to_insert.append(
                    PointStruct(
                        id=point_id, # Usar um ID mais robusto
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
                    print(f" -> AVISO: Lote {i+1} não foi completado com sucesso.")
            except Exception as e:
                print(f"Erro CRÍTICO durante o upsert do Lote {i+1}/{num_batches}: {type(e).__name__} - {e}")
                all_successful = False
        if all_successful:
            print(f"Curso ID: {id_course} - Todos os {num_batches} lotes processados.")
        else:
            print(f"Curso ID: {id_course} - Processamento de lotes concluído, mas ocorreram erros.")
        return all_successful

    def search(self, query_vector: List[float], limit: int = 3, filter: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Busca documentos relevantes no Qdrant, opcionalmente filtrando por course_id."""
        if not query_vector:
            print("Erro: Vetor de busca vazio.")
            return []



        print(f"Buscando {limit} vizinhos mais próximos em '{self.collection_name}'...")
        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=filter, # Aplicar filtro se existir
                limit=limit,
                with_payload=True
            )
            return [
                {
                    "text": hit.payload.get("text", ""),
                    "source": hit.payload.get("source", ""),
                    "page": hit.payload.get("page", -1),
                    "score": hit.score
                }
                for hit in search_result
            ]
        except Exception as e:
            print(f"Error during vector search: {e}")
            return []

    def get_all_by_course_id(self, course_id_filter: str, limit: int = 1000, offset: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Recupera todos os documentos (apenas payload) para um course_id específico usando scroll.
        Lida com paginação básica até o limite especificado. Para datasets muito grandes,
        uma paginação mais robusta no lado do cliente (API) pode ser necessária.
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
                scroll_response = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=query_filter,
                    limit=min(100, limit - len(all_payloads)), # Pega em chunks menores ou o que falta para o limite
                    offset=current_offset,
                    with_payload=True, # Queremos o payload
                    with_vectors=False # Não precisamos dos vetores aqui
                )
                points = scroll_response[0] # A tupla é (points, next_page_offset)
                next_page_offset = scroll_response[1]

                for hit in points:
                    if hit.payload:
                        all_payloads.append(hit.payload) # Adiciona apenas o payload

                if next_page_offset is None or not points: # Se não há mais páginas ou não retornou pontos
                    break
                current_offset = next_page_offset
                if len(all_payloads) >= limit: # Se atingimos o limite global
                    break

            print(f"Busca por scroll para course_id '{course_id_filter}' encontrou {len(all_payloads)} resultados.")
            return all_payloads
        except Exception as e:
            print(f"Erro CRÍTICO durante a busca por scroll no Qdrant para course_id '{course_id_filter}': {type(e).__name__} - {e}")
            import traceback
            traceback.print_exc()
            return []

