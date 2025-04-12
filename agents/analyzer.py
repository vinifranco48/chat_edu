import logging
from utils.llm import get_langchain_llm
from typing import Dict, Any

logger = logging.getLogger(__name__)

def need_more_info_analyzer(state: Dict[str, Any]) -> Dict[str, Any]:
    """Analisa se é necessário mais informações do usuário."""
    query = state["query"]
    retrieved_docs = state.get("retrieved_document", [])
    
    logger.info(f"Analisando query: '{query}' com {len(retrieved_docs)} documentos")
    
    # Se encontrou documentos relevantes, podemos tentar responder
    if retrieved_docs:
        logger.info("Documentos encontrados, tentando responder")
        return {**state, "needs_more_info": False}
    
    # Se a pergunta for muito genérica (mesmo com documentos)
    if len(query.split()) < 2 and not any(word.lower() in query.lower() for word in ["ti", "tecnologia", "plano"]):
        logger.info("Query muito genérica, solicitando mais informações")
        return {**state, "needs_more_info": True}
    
    # Em outros casos, tentamos responder com o que temos
    logger.info("Tentando responder com contexto disponível")
    return {**state, "needs_more_info": False}
