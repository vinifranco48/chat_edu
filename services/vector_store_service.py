from typing import List, Dict, Any
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from langchain_core.documents import Document
from config.settings import settings
import math
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
                host=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
            )
        else:
            raise ValueError(f"Modo qdrant invalido {settings.qdrant_mode}.")
        self._setup_collection()

    def _setup_collection(self):
        """Verifica se a coleção existe no Qdrant e a cria se necessário."""
        print(f"Verificando/Configurando coleção: {self.collection_name}")
        try:
            # Tenta obter informações da coleção para verificar se ela existe
            self.client.get_collection(collection_name=self.collection_name)
            print(f"Coleção '{self.collection_name}' já existe. Usando a existente.")

        except Exception as e:
            # Se get_collection falhar, assumimos que a coleção não existe
            # (Idealmente, verificar o tipo de erro específico, mas simplificando)
            print(f"Coleção '{self.collection_name}' não encontrada ou erro ao acessá-la. Tentando criar... Erro original: {type(e).__name__}")
            try:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams( # Usar models.VectorParams
                        size=self.vector_size,
                        distance=models.Distance.COSINE # Usar models.Distance
                    )
                    # Adicione outros parâmetros como on_disk=True se necessário
                )
                print(f"Coleção '{self.collection_name}' criada com sucesso.")
            except Exception as create_e:
                # Captura erro específico da tentativa de criação
                print(f"Erro CRÍTICO ao TENTAR CRIAR a coleção '{self.collection_name}': {type(create_e).__name__} - {create_e}")
                # É importante parar a aplicação se não puder garantir a coleção
                raise RuntimeError(f"Falha ao garantir a existência/criação da coleção '{self.collection_name}': {create_e}")

    def upsert_documents(self, documents: List[Document], embeddings:List[List[float]], batch_size: int = 100): # Adicionado batch_size
        """Ingere documentos e seus embeddings no Qdrant em lotes."""
        if not documents or not embeddings or len(documents) != len(embeddings):
            print("Erro: documentos e embeddings não podem ser vazios ou de tamanhos diferentes.")
            return False

        total_docs = len(documents)
        num_batches = math.ceil(total_docs / batch_size) # Calcula quantos lotes serão necessários
        print(f"Preparando para inserir/atualizar {total_docs} pontos em {num_batches} lotes de até {batch_size} pontos cada...")

        all_successful = True # Flag para rastrear o sucesso geral

        for i in range(num_batches):
            start_index = i * batch_size
            end_index = min((i + 1) * batch_size, total_docs)
            current_batch_docs = documents[start_index:end_index]
            current_batch_embeddings = embeddings[start_index:end_index]

            points_to_insert: List[PointStruct] = []
            # Usamos o índice global (start_index + j) para um ID único simples nesta ingestão
            # ATENÇÃO: Se re-ingerir, isso pode não ser ideal. Veja nota sobre IDs no final.
            for j, (doc, emb) in enumerate(zip(current_batch_docs, current_batch_embeddings)):
                if emb is None:
                    print(f"Erro: embedding para o documento no índice global {start_index + j} é None. Pulando.")
                    continue # Pula este documento específico

                payload = {
                    "text": doc.page_content,
                    "source": doc.metadata.get('source', 'desconhecido'),
                    "page": doc.metadata.get('page', -1),
                    **doc.metadata # Adiciona todos os outros metadados
                }
                points_to_insert.append(
                    PointStruct(
                        # ID do Ponto: Use start_index + j para um ID numérico sequencial simples.
                        # Alternativas melhores para produção: UUIDs ou Hashes do conteúdo.
                        id=start_index + j,
                        vector=emb,
                        payload=payload
                    )
                )

            if not points_to_insert:
                print(f"Lote {i+1}/{num_batches}: Nenhum ponto válido para inserir. Pulando lote.")
                continue # Pula para o próximo lote

            print(f"Lote {i+1}/{num_batches}: Inserindo/Atualizando {len(points_to_insert)} pontos...")
            try:
                operation_info = self.client.upsert(
                    collection_name=self.collection_name,
                    wait=True, # Espera a operação ser concluída no servidor
                    points=points_to_insert
                )
                print(f" -> Lote {i+1} Upsert Status: {operation_info.status}")
                if operation_info.status != models.UpdateStatus.COMPLETED:
                    all_successful = False # Marca falha se algum lote não completar
                    print(f" -> AVISO: Lote {i+1} não foi completado com sucesso.")

            except Exception as e:
                print(f"Erro CRÍTICO durante o upsert do Lote {i+1}/{num_batches}: {type(e).__name__} - {e}")
                # Você pode decidir parar tudo ou apenas marcar como falha e continuar
                all_successful = False
                # Poderia adicionar um 'return False' aqui se quiser parar na primeira falha de lote
                # return False # Descomente para parar na primeira falha

        if all_successful:
            print(f"Todos os {num_batches} lotes processados.")
        else:
            print("Processamento de lotes concluído, mas ocorreram erros em um ou mais lotes.")

        return all_successful # Retorna True se todos os lotes foram COMPLETED


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