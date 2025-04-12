from groq import Groq, APIError
from config.settings import settings

class LLMService:
    def __init__(self):
        print(f"Inicializando LLmService com Groq em {settings.llm_model_name}")
        if not settings.groq_api_key:
            raise ValueError("API key do Groq não configurada. Configure a variável de ambiente GROQ_API_KEY.")
        try:
            self.client = Groq(api_key=settings.groq_api_key)
            self.client.models.list()
            print("Conexão com o Groq estabelecida com sucesso.")
        except APIError as e:
            print(f"Erro de API ao conectar ao Groq: {e}")
            raise RuntimeError(f"Erro ao conectar ao Groq: {e}")
        except Exception as e:
            print(f"Erro ao conectar ao Groq: {e}")
            raise RuntimeError(f"Erro ao conectar ao Groq: {e}")
    
    def generate_response(self, prompt:str) -> str | None:
        """Gerar uma resposta usando o modelo LLM baseado no prompt."""
        print(f"Enviando prompt para LLM: {prompt[:200]}...")
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=settings.llm_model_name,
            )

            response = chat_completion.choices[0].message.content.strip()
            print(f"Resposta LLM recebida")
            return response
        except APIError as e:
            error_detail = str(e)
            try:
                error_detail = e.response.json().get("error", {}).get("message", str(e))
            except: pass
            print(f"Erro de API ao gerar resposta: {error_detail}")
            return None
        except Exception as e:
            print(f"Erro ao gerar resposta: {str(e)}")
            return None