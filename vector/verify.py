from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# Initialize Qdrant client
client = QdrantClient("localhost", port=6333)

# Initialize embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Define collection name
collection_name = 'user_recordings'

# Define the query
query = "Zoom developer platform"
query_vector = model.encode(query).tolist()

# Perform search instead of using the scroll function with an unsupported filter argument
search_result = client.search(
    collection_name=collection_name,
    query_vector=query_vector,
    limit=10  # Adjust limit as needed
)

# Print the search results
for hit in search_result:
    print(f"ID: {hit.id}, Payload: {hit.payload}")
