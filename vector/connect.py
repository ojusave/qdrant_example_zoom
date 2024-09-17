from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

# Connect to Qdrant
qdrant_client = QdrantClient("localhost", port=6333)

# Check if collection exists
collection_name = "user_recordings"
collections = qdrant_client.get_collections().collections
existing_collections = [collection.name for collection in collections]

if collection_name not in existing_collections:
    # Create a new collection if it doesn't exist
    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
    print(f"Collection '{collection_name}' created successfully.")
else:
    print(f"Collection '{collection_name}' already exists.")

# Optionally, you can retrieve and print collection info
collection_info = qdrant_client.get_collection(collection_name)
print(f"Collection info: {collection_info}")
