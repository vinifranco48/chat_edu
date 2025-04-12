from core.state import ConversationState
from langchain_core.prompts import ChatPromptTemplate
from utils.llm import get_langchain_llm

def answer_preparation_agent(state: ConversationState) -> ConversationState:
    """Prepara uma resposta para a consulta com base nos documentos recuperados."""
    llm = get_langchain_llm()
    prompt = ChatPromptTemplate.from_template("""
    Com base nas informações, responda a pergunta em português do Brasil:
    
    Contexto: {context}
    
    Pergunta: {query}
    
    Sua resposta deve ser detalhada, educacional e facilitar o entendimento do estudante.
    Inclua explicações claras e exemplos quando relevante.
    
    Resposta:
    """)

    chain = prompt | llm
    response = chain.invoke({
        "query": state["query"],
        "context": "\n\n".join(state["retrieved_document"]),
    })
    return {
        **state,
        "proposed_answer": response.content
    }