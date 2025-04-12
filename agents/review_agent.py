from core.state import ConversationState
from langchain_core.prompts import ChatPromptTemplate
from utils.llm import get_langchain_llm

def review_agent(state: ConversationState) -> ConversationState:
    """Revisa e melhora a resposta proposta."""
    llm = get_langchain_llm()
    
    prompt = ChatPromptTemplate.from_template("""
    Revise a seguinte resposta para uma pergunta educacional.
    
    Pergunta original: {query}
    
    Resposta proposta: {proposed_answer}
    
    Sua tarefa é:
    1. Verificar a precisão da informação
    2. Verificar a clareza e o formato educacional
    3. Adicionar exemplos ou explicações adicionais se necessário
    4. Garantir que a resposta esteja em português claro e correto
    
    Resposta revisada:
    """)
    
    chain = prompt | llm
    response = chain.invoke({
        "query": state["query"],
        "proposed_answer": state["proposed_answer"]
    })
    
    return {
        **state,
        "final_answer": response.content
    }
