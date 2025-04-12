import logging
from utils.database import get_vector_store

logger = logging.getLogger(__name__)

def retriever_agent(state, qdrant_client):
    """Recupera documentos relevantes do vector store."""
    try:
        query = state["query"]
        vectorstore = get_vector_store(qdrant_client)
        
        # Buscar documentos relevantes
        retrieved_docs = vectorstore.similarity_search(query, k=3)
        logger.info(f"Encontrados {len(retrieved_docs)} documentos relevantes")
        
        # Sempre retornar uma lista, mesmo que vazia
        return {
            **state,
            "retrieved_document": retrieved_docs,
            "context": "\n".join([doc.page_content for doc in retrieved_docs]) if retrieved_docs else ""
        }
    except Exception as e:
        logger.error(f"Erro no retriever: {str(e)}")
        return {
            **state,
            "retrieved_document": [],
            "context": ""
        }
