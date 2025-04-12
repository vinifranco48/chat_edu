import logging
from qdrant_client import QdrantClient
from qdrant_client import models
from qdrant_client.http import models as rest
from qdrant_client.models import PointStruct
from langchain_community.vectorstores import Qdrant
from langchain_huggingface import HuggingFaceEmbeddings
from core.config import VECTOR_STORE_COLLECTION, EMBEDDING_MODEL
from sentence_transformers import SentenceTransformer
from typing import List, Tuple
from utils.embeddings import generate_embeddings

logger = logging.getLogger(__name__)

def get_embedding_model():
    """Retorna o modelo de embedding"""
    model = SentenceTransformer(EMBEDDING_MODEL)
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'}
    )

def get_qdrant_client():
    """Retorna o cliente Qdrant"""
    client = QdrantClient(":memory:")
    # Garantir que a collection existe
    if not client.get_collections().collections:
        model = SentenceTransformer(EMBEDDING_MODEL)
        client.create_collection(
            collection_name=VECTOR_STORE_COLLECTION,
            vectors_config=models.VectorParams(
                size=model.get_sentence_embedding_dimension(),
                distance=models.Distance.COSINE
            ),
        )
    return client

def ingest_database(client: QdrantClient, chunk_embedding: List[Tuple[str, List[float]]], collection_name="chat-edu"):
    """
    Ingere os documentos no Qdrant usando o formato de points
    Args:
        client: Cliente Qdrant
        chunk_embedding: Lista de tuplas (texto, embedding)
        collection_name: Nome da coleção
    """
    try:
        logger.info(f"Iniciando ingestão de {len(chunk_embedding)} documentos")
        points = []
        for i in range(len(chunk_embedding)):
            point = PointStruct(
                id=i+1,
                vector=chunk_embedding[i][1],
                payload={"document": chunk_embedding[i][0]},
            )
            points.append(point)
        
        operation_info = client.upsert(
            collection_name=collection_name,
            wait=True,
            points=points 
        )
        logger.info(f"Ingestão concluída: {operation_info}")
        return operation_info
    except Exception as e:
        logger.error(f"Erro na ingestão: {str(e)}")
        raise

def setup_vector_store(client, documents):
    """Configura e popula o vector database"""
    try:
        logger.info("Iniciando configuração do vector store")
        
        # Configurar collection
        logger.info("Configurando collection no Qdrant")
        client.recreate_collection(
            collection_name=VECTOR_STORE_COLLECTION,
            vectors_config=models.VectorParams(
                size=768,  # Tamanho fixo para o modelo multilingual-mpnet-base-v2
                distance=models.Distance.COSINE
            ),
        )
        
        if documents:
            # Preparar textos e gerar embeddings
            logger.info("Gerando embeddings para os documentos")
            texts = [doc.page_content for doc in documents]
            embeddings = generate_embeddings(texts)
            
            # Preparar dados para ingestão
            chunk_embedding = list(zip(texts, embeddings))
            
            # Ingerir documentos
            ingest_database(client, chunk_embedding, VECTOR_STORE_COLLECTION)
        
        # Criar e retornar vector store
        return get_vector_store(client)
    except Exception as e:
        logger.error(f"Erro ao configurar vector store: {str(e)}", exc_info=True)
        raise

def get_vector_store(client):
    """Retorna o vector store"""
    embedding_model = get_embedding_model()
    return Qdrant(
        client=client,
        collection_name=VECTOR_STORE_COLLECTION,
        embeddings=embedding_model,
    )
