import sys
import os
import re
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import anthropic

# Load configuration
def load_config():
    # Get the directory of the current script (query.py)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to the root directory
    root_dir = os.path.dirname(current_dir)
    # Construct the path to config.js in the root folder
    config_path = os.path.join(root_dir, 'config.js')
    
    with open(config_path, 'r') as f:
        config_content = f.read()
    
    # Use regex to extract key-value pairs
    config = {}
    pattern = r"(\w+):\s*['\"]?([\w\-]+)['\"]?"
    matches = re.findall(pattern, config_content)
    for key, value in matches:
        config[key] = value
    
    return config

config = load_config()

# Initialize Qdrant client
client = QdrantClient("localhost", port=6333)

# Initialize embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Define collection name
collection_name = 'user_recordings'

def query_vector_db(query):
    query_vector = model.encode(query).tolist()
    
    # Perform search
    search_result = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=5  # Adjust limit as needed
    )

    # Format the search results
    formatted_results = []
    for hit in search_result:
        result = {
            "Score": hit.score,
            "Topic": hit.payload.get('topic', 'N/A'),
            "Start Time": hit.payload.get('start_time', 'N/A'),
            "Duration": hit.payload.get('duration', 'N/A'),
            "Summary": hit.payload.get('summary', {}).get('summary_overview', 'N/A')
        }
        formatted_results.append(result)
    
    return formatted_results

def get_anthropic_response(query, search_results):
    # Use the API key from the config
    api_key = config.get('anthropic_api_key')
    
    if not api_key:
        raise ValueError("Anthropic API key not set in config.")

    client = anthropic.Anthropic(api_key=api_key)
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1000,
        temperature=0,
        system="You are an AI assistant tasked with answering queries based on search results.",
        messages=[
            {
                "role": "user",
                "content": f"Based on the following search results, please provide a concise answer to the query: '{query}'\n\nSearch Results:\n{search_results}\n\nPlease synthesize the information from these results to directly answer the query. If the information is not sufficient to answer the query, please state that clearly. Please read the json data properly."
            }
        ]
    )
    
    return message.content

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = sys.argv[1]
        search_results = query_vector_db(query)
        answer = get_anthropic_response(query, search_results)
        print(f"Answer: {answer}")
    else:
        print("No query provided.")