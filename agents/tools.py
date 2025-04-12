from langchain_core.tools import tool

@tool
def request_more_context(query: str) -> str:
    """Solicita mais contexto ao usuário para melhor entender a pergunta."""
    return "Preciso de mais informações para responder adequadamente à sua pergunta. Poderia fornecer mais detalhes?"
