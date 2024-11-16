
import json
import requests
from src.configs import rag_url

def retrieve_related_chunks(query: str) -> str:
    url = rag_url
    params = {
        "query": query,
        "search_type": "embedding"  # or "fulltext" if preferred
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        chunks = response.json()[:3]
        print(chunks)
        return json.dumps({"chunks": chunks})
    else:
        return json.dumps({"error": f"API request failed with status code {response.status_code}"})
