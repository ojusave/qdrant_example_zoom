import json
import os
import uuid
import base64
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer
import warnings

warnings.filterwarnings('ignore', category=FutureWarning)

model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize Qdrant client
qdrant_client = QdrantClient("localhost", port=6333)

# Define collection name
collection_name = "user_recordings"

def ensure_collection_exists():
    collections = qdrant_client.get_collections().collections
    if collection_name not in [c.name for c in collections]:
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
    print(f"Collection '{collection_name}' is ready.")

def load_data(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def base64_to_uuid(base64_string):
    try:
        # Remove any padding and convert to bytes
        base64_string = base64_string.rstrip('=')
        byte_string = base64.urlsafe_b64decode(base64_string + '=='*(-len(base64_string) % 4))
        
        # Convert bytes to UUID
        return str(uuid.UUID(bytes=byte_string[:16]))
    except:
        # If conversion fails, generate a new UUID
        return str(uuid.uuid4())

def insert_data_to_qdrant(data):
    try:
        points = []
        for i, recording in enumerate(data.get('recordings', [])):
            summary = recording.get('summary', {})
            if isinstance(summary, dict):
                summary_text = summary.get('summary_overview', recording.get('topic', ''))
            else:
                summary_text = recording.get('topic', '')

            if not summary_text:
                summary_text = "No summary or topic available"

            vector = model.encode(summary_text).tolist()

            point_id = base64_to_uuid(recording['uuid'])

            print(f"Inserting recording {i + 1}:")
            print(f"  UUID: {point_id}")
            print(f"  Topic: {recording['topic']}")
            print(f"  Summary text: {summary_text}")
            print(f"  Vector (first 5 elements): {vector[:5]}")

            point = PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    'topic': recording['topic'],
                    'start_time': recording['start_time'],
                    'duration': recording['duration'],
                    'summary': summary if isinstance(summary, dict) else {}
                }
            )
            points.append(point)

        if points:
            print(f"Total points prepared for insertion: {len(points)}")
            response = qdrant_client.upsert(collection_name=collection_name, points=points)
            print(f"Qdrant response: {response}")
            print(f"Inserted {len(points)} points into Qdrant.")
        else:
            print("No valid points to insert.")

        # Verify insertion
        collection_info = qdrant_client.get_collection(collection_name)
        print(f"Collection info after insertion: {collection_info}")

    except Exception as e:
        print(f"Error inserting data to Qdrant: {e}")

if __name__ == "__main__":
    ensure_collection_exists()
    
    data_dir = '/Users/ojusave/Desktop/QDrant example/data'  # Replace with the actual path

    for file_name in os.listdir(data_dir):
        if file_name.endswith('.txt'):
            file_path = os.path.join(data_dir, file_name)
            print(f"Processing file: {file_path}")
            data = load_data(file_path)
            insert_data_to_qdrant(data)

print("Data insertion complete.")