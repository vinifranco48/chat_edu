# services/vector_store_service.py
from typing import List, Dict, Any, Optional # Adicionar Optional
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import PointStruct
from langchain_core.documents import Document
from config.settings import settings
import math
import uuid # <--- ADICIONAR IMPORT DO UUID

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
            
            # A verificação de índice de payload pode ser um pouco diferente dependendo da versão do cliente
            # Esta é uma abordagem comum: tentar criar e capturar exceção se já existir, ou verificar
            # o campo 'payload_schema' em collection_info.config.params (se disponível e populado assim)
            # Para simplificar e ser mais direto com as versões recentes:
            # Verificamos se já existe no payload_schema da coleção.
            # No entanto, a API get_collection pode não popular isso detalhadamente em todas as circunstâncias.
            # Uma maneira segura é verificar se a *tentativa* de criação falha porque já existe.
            # Ou, como você fez, que é bom:
            
            current_schema = getattr(collection_info.config.params, 'payload_schema', {}) # Acesso mais seguro
            if not current_schema: # Se payload_schema não existe ou está vazio
                 # Em algumas versões mais antigas, o payload_schema pode não ser diretamente acessível ou populado como esperado.
                 # Se a linha acima não funcionar como esperado, pode ser necessário inspecionar `collection_info`
                 # ou simplesmente tentar criar o índice e tratar uma possível exceção se ele já existir.
                 # Por exemplo, com `collection_info.payload_schema` como você usou:
                 current_schema = collection_info.payload_schema or {}


            if field_name not in current_schema:
                print(f"Criando indice payload para o campo '{field_name}' na coleção '{self.collection_name}'...")
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=field_type # Em versões mais recentes, isso pode ser field_type=field_type ou models.PayloadFieldSchema(...)
                )
                print(f"Índice de payload '{field_name}' criado com sucesso.")
            else:
                print(f"Índice de payload '{field_name}' já existe na coleção '{self.collection_name}'.")
        except Exception as e:
            # Um erro comum aqui pode ser se o índice já existe e a lógica de verificação não pegou.
            # Qdrant pode retornar um erro indicando que o índice já existe.
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
                    all_successful = False # Marcar que houve um problema
                    continue

                # O payload já contém course_id, source, page, e o texto.
                # **doc.metadata espalha o restante dos metadados do documento LangChain.
                payload = {
                    "text": doc.page_content,
                    "course_id": id_course, # Garante que o id_course específico da ingestão seja usado
                    **doc.metadata # Inclui 'source', 'page' e qualquer outro metadado do Langchain Document
                }
                # Assegurar que 'source' e 'page' estejam presentes, caso não venham de doc.metadata
                payload.setdefault('source', 'desconhecido')
                payload.setdefault('page', -1)


                # --- MUDANÇA PRINCIPAL AQUI ---
                # Gerar um UUID v4 para cada chunk. Isso garante um ID único e válido.
                point_id = str(uuid.uuid4())
                # -----------------------------

                # Opcional: Se você precisar rastrear o índice original do chunk dentro do documento
                # para fins de depuração ou lógica específica, você pode adicioná-lo ao payload:
                # payload["original_chunk_index_in_doc"] = doc.metadata.get('chunk_index', start_index + j) # Supondo que 'chunk_index' exista ou use o global
                # payload["original_doc_batch_index"] = start_index + j


                points_to_insert.append(
                    PointStruct(
                        id=point_id,
                        vector=emb,
                        payload=payload
                    )
                )

            if not points_to_insert:
                # Isso pode acontecer se todos os embeddings em um lote forem None
                print(f"Lote {i+1}/{num_batches}: Nenhum ponto válido para inserir. Pulando lote.")
                continue

            print(f"Lote {i+1}/{num_batches}: Inserindo/Atualizando {len(points_to_insert)} pontos...")
            try:
                operation_info = self.client.upsert(
                    collection_name=self.collection_name,
                    wait=True, # Esperar a operação completar é bom para consistência, mas pode ser mais lento.
                               # Defina como False para maior throughput se a consistência imediata não for crítica.
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
                    print(f"   Detalhes do erro: {e.details}") # type: ignore
                elif hasattr(e, 'response_content'):
                    print(f"   Conteúdo da resposta do erro: {e.response_content}") # type: ignore

                all_successful = False
        
        if all_successful:
            print(f"Curso ID: {id_course} - Todos os {num_batches} lotes processados (ou nenhum erro crítico encontrado).")
        else:
            print(f"Curso ID: {id_course} - Processamento de lotes concluído, mas ocorreram erros ou avisos.")
        return all_successful

    def search(self, query_vector: List[float], limit: int = 3, filter: Optional[models.Filter] = None) -> List[Dict[str, Any]]: # Mudei Dict para models.Filter
        """Busca documentos relevantes no Qdrant, opcionalmente filtrando por course_id."""
        if not query_vector: # Adicionar verificação para self.vector_size se for usar para validação
            print("Erro: Vetor de busca vazio.")
            return []
        
        # Opcional: Validar o tamanho do query_vector
        # if len(query_vector) != self.vector_size:
        #     print(f"Erro: O tamanho do query_vector ({len(query_vector)}) é diferente do tamanho configurado para a coleção ({self.vector_size}).")
        #     return []


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
                payload = hit.payload or {} # Garantir que payload seja um dict mesmo se None
                results.append({
                    "id": hit.id, # Pode ser útil retornar o ID do ponto
                    "text": payload.get("text", ""),
                    "source": payload.get("source", "desconhecido"),
                    "page": payload.get("page", -1),
                    "course_id": payload.get("course_id", "desconhecido"), # Retornar course_id também
                    "score": hit.score,
                    "metadata": payload # Para ter acesso a todos os outros metadados
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
                    key="course_id", # Certifique-se que 'course_id' está indexado para performance
                    match=models.MatchValue(value=course_id_filter)
                )
            ]
        )

        all_payloads: List[Dict[str, Any]] = []
        # O tipo de 'offset' para scroll pode ser um ID de ponto (UUID/int) ou um contador numérico dependendo
        # da versão do Qdrant e do cliente. Para UUIDs, o offset inicial é None.
        current_offset = offset 

        try:
            # O método scroll pode ser chamado repetidamente com o next_page_offset
            while len(all_payloads) < limit:
                # Define o limite para a chamada atual do scroll, não excedendo o limite total desejado.
                # E também não excedendo um limite razoável por chamada (ex: 10-100).
                scroll_batch_limit = min(100, limit - len(all_payloads))
                if scroll_batch_limit <= 0: # Já coletamos o suficiente
                    break

                scroll_response_tuple = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=query_filter,
                    limit=scroll_batch_limit,
                    offset=current_offset,
                    with_payload=True,
                    with_vectors=False
                )
                # scroll_response é uma tupla: (list_of_points, next_page_offset_id)
                points = scroll_response_tuple[0]
                next_page_offset = scroll_response_tuple[1]

                for hit in points:
                    if hit.payload:
                        # Adicionando o ID do ponto e o course_id ao payload retornado, para consistência
                        payload_to_return = {"id": hit.id, **hit.payload}
                        all_payloads.append(payload_to_return) 

                current_offset = next_page_offset # Atualiza o offset para a próxima iteração
                
                if not points or next_page_offset is None: # Não há mais pontos ou não há próxima página
                    break 
                # A verificação de len(all_payloads) >= limit é feita no início do loop e pelo scroll_batch_limit

            print(f"Busca por scroll para course_id '{course_id_filter}' encontrou {len(all_payloads)} resultados.")
            return all_payloads

        except Exception as e:
            print(f"Erro CRÍTICO durante a busca por scroll no Qdrant para course_id '{course_id_filter}': {type(e).__name__} - {e}")
            import traceback
            traceback.print_exc()
            return []