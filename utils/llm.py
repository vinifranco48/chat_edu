from groq import Groq
from langchain_groq import ChatGroq
from core.config import GROQ_API_KEY, LLM_MODEL

def get_groq_client():
    """Retorna o cliente Groq"""
    return Groq(api_key=GROQ_API_KEY)

def get_langchain_llm():
    """Retorna um modelo Langchin configurado"""
    return ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model_name=LLM_MODEL,
    )
