from fastembed import TextEmbedding

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

def embedding_document(documents):
    embedding_model = TextEmbedding(MODEL_NAME)
    embeddings_generator = embedding_model.embed(documents)
    embeddings_docs = list(embeddings_generator)
    return embeddings_docs[0]