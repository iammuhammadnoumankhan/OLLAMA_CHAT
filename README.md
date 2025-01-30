Here's a comprehensive README.md for your GitHub repository:

```markdown
# Ollama AI Assistant

A ChatGPT-like AI Assistant powered by Ollama, built with FastAPI backend and Streamlit frontend.

![Alt text](samples/sample1.png)


## Features

- 🚀 Separate backend (FastAPI) and frontend (Streamlit) architecture
- 💬 ChatGPT-like chat interface
- ⚡ Real-time streaming responses
- 🤖 Multiple Ollama model support
- ⚙️ Sidebar configuration panel
- 🔄 Session persistence
- 🌐 CORS-enabled API
- 🔌 Environment configuration support

## Prerequisites

- Python >= 3.10
- [Ollama](https://ollama.ai/) installed and running
- At least one Ollama model pulled (e.g., `llama3.2:latest`)

## Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-username/ollama-ai-assistant.git
cd ollama-ai-assistant
```

2. **Set up backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Set up frontend**
```bash
cd ../frontend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

1. **Ollama Setup**
```bash
# Start Ollama service (in separate terminal)
ollama serve

# Pull a model (example)
ollama pull llama3.2:latest
```

2. **Environment Variables**

Create `.env` files:

**backend/.env**
```env
OLLAMA_HOST=http://localhost:11434
```
or any other url if your ollama is running on a different machine in your network: eg: `http://x.x.x.x:11434`

**frontend/.env**
```env
BACKEND_URL=http://localhost:8000
```

## Usage

1. **Start Backend**
```bash
cd backend
uvicorn app.main:app --reload
```

2. **Start Frontend**
```bash
cd frontend
streamlit run app.py
```

3. **Access the Application**
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- Ollama: http://localhost:11434

## Tech Stack

- **Backend**: 
  - Python FastAPI
  - Ollama Python Client
  - CORS Middleware
- **Frontend**:
  - Streamlit
  - Requests
- **AI**:
  - Ollama
  - Supported LLMs (Llama3, Deepseek, Qwen, etc.)

## Troubleshooting

**Common Issues**:
1. **Ollama not running**:
   - Verify `ollama serve` is running
   - Check OLLAMA_HOST in backend/.env

2. **Model not found**:
   - Pull the model: `ollama pull <model-name>`
   - Refresh model list in frontend

3. **CORS Errors**:
   - Ensure backend CORS middleware is configured
   - Verify frontend/backend URLs match

4. **Streaming issues**:
   - Check network connectivity
   - Verify streaming toggle is enabled

## Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## License

MIT License

