from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from ingestor import fetch_data
from ingestor import vector_database_ingest
from ingestor import embeddings
from ingestor.embeddings import embedding_document
from groq import Groq
from qdrant_client import models
qdrant = QdrantClient(":memory:")
chunks = fetch_data.file_to_documents("/home/noise/Documentos/chat_edu/data/Orientações para Elaborar o Plano Estratégico de TI.pdf")

qdrant.create_collection("chat-edu", vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE))
embeddings = [(i.page_content, embeddings.embedding_document(i.page_content)) for i in chunks]
vector_database_ingest.ingest_database(qdrant, embeddings)



client = Groq(
    api_key=""
)

def generate_response(query, context, client):
    prompt = f"""
            Com base nas informações, responda a pergunta em portugues do Brasil:
            Contexto: {context}
            Pergunta: {query}
            Resposta: 
            """
    
    # Criando a requisição para o modelo usando o cliente
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="qwen-qwq-32b",  # ou outro modelo de sua escolha
    )
    
    # Extraindo a resposta do objeto retornado
    return response.choices[0].message.content.strip()

while True:

    query = input('Fala comigo')
    question_embeddings = embedding_document(query)


    search = qdrant.search(
        collection_name="chat-edu",
        query_vector= question_embeddings,
        limit = 3
    )
    context = [i.payload['document'] for i in search]
    response = generate_response(query, context, client)
    print(response)