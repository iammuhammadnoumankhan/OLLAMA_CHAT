from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ollama import Client
from dotenv import load_dotenv
import os
from fastapi.responses import StreamingResponse

load_dotenv()

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ollama Client
client = Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))

class ChatRequest(BaseModel):
    model: str
    messages: list
    stream: bool = False

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        if not request.stream:
            response = client.chat(
                model=request.model,
                messages=request.messages
            )
            return {"response": response.message.content}
        else:
            def generate():
                stream = client.chat(
                    model=request.model,
                    messages=request.messages,
                    stream=True
                )
                for chunk in stream:
                    yield chunk.message.content

            return StreamingResponse(generate(), media_type="text/event-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def get_models():
    try:
        list_response = client.list()
        models_list = []
        for model_obj in list_response.models:
            model_dict = model_obj.dict()
            model_dict["name"] = model_dict.pop("model")
            models_list.append(model_dict)
        return {"models": models_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))