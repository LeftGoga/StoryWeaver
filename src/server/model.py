import whisper
from mistralai import Mistral

from src.configs import device, whisper_model_size ,api_key

def create_whisper_model(whisper_model_size:str = whisper_model_size):
    return whisper.load_model(whisper_model_size).to(device)

def create_mistral_agent(api_key = api_key):
    return Mistral(api_key=api_key)