from ollama import Client
import os

def get_ollama_client():
    return Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))