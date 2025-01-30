import streamlit as st
import requests
from dotenv import load_dotenv
import os

load_dotenv()

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
DEFAULT_MODEL = "llama3.2:latest"

def initialize_session():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "model" not in st.session_state:
        st.session_state.model = DEFAULT_MODEL

def get_models():
    try:
        response = requests.get(f"{BACKEND_URL}/models")
        return response.json().get('models', [])
    except Exception as e:
        st.error(f"Error fetching models: {e}")
        return []

def chat_completion(messages, stream=False):
    payload = {
        "model": st.session_state.model,
        "messages": messages,
        "stream": stream
    }
    
    if stream:
        return requests.post(
            f"{BACKEND_URL}/chat",
            json=payload,
            stream=True
        )
    else:
        return requests.post(
            f"{BACKEND_URL}/chat",
            json=payload
        )

def main():
    st.title("AI Assistant 🤖")
    initialize_session()
    
    # Model selection
    models = get_models()
    if models:
        model_names = [model['name'] for model in models]
        current_model = next(
            (m for m in model_names if "llama3.2" in m),
            model_names[0] if model_names else DEFAULT_MODEL
        )
        
        st.session_state.model = st.selectbox(
            "Select Model",
            model_names,
            index=model_names.index(current_model) if current_model in model_names else 0
        )
    
    # Chat interface
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Streaming toggle
    streaming = st.sidebar.toggle("Enable Streaming", value=True)
    
    if prompt := st.chat_input("How can I help you?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            try:
                if streaming:
                    response = st.write_stream(
                        chunk.decode() if isinstance(chunk, bytes) else chunk
                        for chunk in chat_completion(
                            st.session_state.messages, 
                            stream=True
                        ).iter_content()
                    )
                else:
                    response = chat_completion(
                        st.session_state.messages
                    ).json()["response"]
                    st.markdown(response)
                
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )
            except Exception as e:
                st.error(f"Error generating response: {str(e)}")

if __name__ == "__main__":
    main()