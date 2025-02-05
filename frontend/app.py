import streamlit as st
import requests
from dotenv import load_dotenv
import os
import re
import time
from codecs import getincrementaldecoder

load_dotenv()

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
DEFAULT_MODEL = "llama3.2:latest"
THINKING_STYLE = """
<div style="
    background: #f8f9fa;
    border-left: 4px solid #dee2e6;
    color: #6c757d;
    padding: 0.5rem 1rem;
    margin: 1rem 0;
    border-radius: 0.25rem;
    font-size: 0.9em;
">
🤔 <strong>Thinking:</strong><br/>
{}
</div>
"""

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

def process_response(content):
    """Parse response content and extract thinking process"""
    think_blocks = re.findall(r'<think>(.*?)</think>', content, re.DOTALL)
    answer = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
    return think_blocks, answer

def display_message(role, content):
    """Display message with proper formatting"""
    with st.chat_message(role):
        if role == "assistant":
            think_blocks, answer = process_response(content)
            for block in think_blocks:
                st.markdown(THINKING_STYLE.format(block), unsafe_allow_html=True)
            if answer:
                st.markdown(answer)
        else:
            st.markdown(content)

def main():
    st.title("AI Assistant 🤖")
    initialize_session()
    
    # Sidebar components
    with st.sidebar:
        st.header("Settings")
        
        # Model selection
        models = get_models()
        if models:
            model_names = [model['name'] for model in models]
            current_model = next(
                (m for m in model_names if "llama3.2:latest" in m),
                model_names[0] if model_names else DEFAULT_MODEL
            )
            
            st.session_state.model = st.selectbox(
                "Select Model",
                model_names,
                index=model_names.index(current_model) if current_model in model_names else 0
            )
        
        # Streaming toggle
        streaming = st.toggle("Enable Streaming", value=True)
        
        st.markdown("---")
        st.markdown(f"**Selected Model:**  \n`{st.session_state.model}`")
        st.markdown("""
            **Markdown/Latex Support:**  
            - Use `$$...$$` for LaTeX equations  
            - **Bold**, *italic*, `code`, [links](https://streamlit.io)  
            - Tables, lists, and other Markdown features
        """)

    # Chat interface
    for message in st.session_state.messages:
        display_message(message["role"], message["content"])
    
    if prompt := st.chat_input("How can I help you?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        display_message("user", prompt)
        
        with st.chat_message("assistant"):
            try:
                if streaming:
                    response_container = st.empty()
                    full_response = ""
                    text_buffer = ""
                    decoder = getincrementaldecoder('utf-8')()

                    response = chat_completion(
                        st.session_state.messages, 
                        stream=True
                    )
                    
                    for chunk in response.iter_content(chunk_size=1024):
                        # Decode the chunk using incremental decoder
                        text_chunk = decoder.decode(chunk)
                        text_buffer += text_chunk

                        # Process thinking blocks incrementally
                        while True:
                            start = text_buffer.find('<think>')
                            end = text_buffer.find('</think>')
                            
                            if start != -1 and end != -1:
                                think_content = text_buffer[start+7:end]
                                st.markdown(
                                    THINKING_STYLE.format(think_content), 
                                    unsafe_allow_html=True
                                )
                                text_buffer = text_buffer[end+8:]
                            else:
                                break

                        # Display remaining content as stream
                        if text_buffer:
                            response_container.markdown(text_buffer + "▌")

                    # Process final chunk
                    text_buffer += decoder.decode(b'', final=True)
                    if text_buffer:
                        response_container.markdown(text_buffer)
                        full_response += text_buffer
                    
                    st.session_state.messages.append(
                        {"role": "assistant", "content": full_response}
                    )
                    
                else:
                    response = chat_completion(
                        st.session_state.messages
                    ).json()["response"]
                    
                    think_blocks, answer = process_response(response)
                    for block in think_blocks:
                        st.markdown(THINKING_STYLE.format(block), unsafe_allow_html=True)
                    if answer:
                        st.markdown(answer)
                    full_response = response
                
                st.session_state.messages.append(
                    {"role": "assistant", "content": full_response}
                )
                
            except Exception as e:
                st.error(f"Error generating response: {str(e)}")

if __name__ == "__main__":
    main()