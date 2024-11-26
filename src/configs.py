import torch
import os

whisper_model_size = "turbo"

device = "cuda" if torch.cuda.is_available() else "cpu"
api_key = os.environ.get("MISTRAL_API_KEY")
model_name = "mistral-large-latest"
rag_url = "http://213.139.208.158:8000/search"
playlist_url = "https://www.youtube.com/playlist?list=PLyuFRDBGJOtkrKhMrPtFT6MqJX9MtlRHq"