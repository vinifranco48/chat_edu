from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct


def ingest_database(client: QdrantClient, chunk_embedding, collection_name="chat-edu"):
    points = []
    for i in range(1, len(chunk_embedding)):
        point = PointStruct(
            id=i,
            vector=chunk_embedding[i-1][1],
            payload={"document": chunk_embedding[i-1][0]},
        )
        points.append(point)
    operation_info = client.upsert(
        collection_name = collection_name,
        wait=True,
        points=points 
    )