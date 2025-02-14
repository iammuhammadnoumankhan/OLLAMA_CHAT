import streamlit as st
import requests
import os
import re
import time
from dotenv import load_dotenv
from codecs import getincrementaldecoder
from langchain_community.document_loaders import (
    PDFPlumberLoader, 
    TextLoader,
    CSVLoader,
    Docx2txtLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_ollama import OllamaEmbeddings

load_dotenv()

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
DEFAULT_MODEL = "llama3.2:latest"
DEFAULT_EMBED_MODEL = "nomic-embed-text:latest"
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
RAG_TEMPLATE = """
You are an assistant for question-answering tasks. Use the following context to answer the question. 
If you don't know the answer, say you don't know. Be concise and helpful.

Context: {context}

Question: {question}

Answer:
"""

def initialize_session():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "model" not in st.session_state:
        st.session_state.model = DEFAULT_MODEL
    if "embed_model" not in st.session_state:
        st.session_state.embed_model = DEFAULT_EMBED_MODEL
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = None

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

def process_documents(files):
    """Process uploaded documents and create vector store"""
    try:
        documents = []
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # Get Ollama host from environment
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

        for file in files:
            # Validate file size
            if file.size > 200 * 1024 * 1024:  # 200MB
                st.error(f"File {file.name} exceeds 200MB limit")
                continue

            temp_path = f"temp_{file.name}"
            try:
                with open(temp_path, "wb") as f:
                    f.write(file.getbuffer())
                
                # Determine loader based on file type
                if file.type == "application/pdf":
                    loader = PDFPlumberLoader(temp_path)
                elif file.type == "text/plain":
                    loader = TextLoader(temp_path)
                elif file.type == "text/csv":
                    loader = CSVLoader(temp_path)
                elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    loader = Docx2txtLoader(temp_path)
                else:
                    st.error(f"Unsupported file type: {file.type}")
                    continue
                
                loaded_docs = loader.load()
                documents.extend(text_splitter.split_documents(loaded_docs))
                
            except Exception as e:
                st.error(f"Error processing {file.name}: {str(e)}")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        if documents:
            try:
                # Verify Ollama connection
                test_embeddings = OllamaEmbeddings(model=st.session_state.embed_model)
                test_embeddings.embed_query("test connection")
                
                embeddings = OllamaEmbeddings(model=st.session_state.embed_model, base_url=ollama_host)
                return InMemoryVectorStore.from_documents(
                    documents=documents,
                    embedding=embeddings
                )
            except requests.exceptions.ConnectionError:
                st.error("Failed to connect to Ollama. Make sure it's running and accessible.")
                return None
        return None
        
    except Exception as e:
        st.error(f"Document processing error: {str(e)}")
        return None

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
                "Select Chat Model",
                model_names,
                index=model_names.index(current_model) if current_model in model_names else 0
            )
            
            # Embedding model selection
            current_embed = next(
                (m for m in model_names if "nomic-embed-text" in m),
                model_names[0] if model_names else DEFAULT_EMBED_MODEL
            )
            st.session_state.embed_model = st.selectbox(
                "Select Embedding Model",
                model_names,
                index=model_names.index(current_embed) if current_embed in model_names else 0
            )
        
        # Document upload
        st.markdown("---")
        uploaded_files = st.file_uploader(
            "Upload Documents (PDF, TXT, CSV, DOCX)",
            type=["pdf", "txt", "csv", "docx"],
            accept_multiple_files=True
        )
        if uploaded_files:
            with st.spinner("Processing documents..."):
                st.session_state.vector_store = process_documents(uploaded_files)
        
        # Streaming toggle
        streaming = st.toggle("Enable Streaming", value=True)
        
        st.markdown("---")
        st.markdown(f"**Chat Model:**  \n`{st.session_state.model}`")
        st.markdown(f"**Embed Model:**  \n`{st.session_state.embed_model}`")

    # Chat interface
    for message in st.session_state.messages:
        display_message(message["role"], message["content"])
    
    if prompt := st.chat_input("How can I help you?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        display_message("user", prompt)
        
        with st.chat_message("assistant"):
            try:
                # Retrieve relevant context if documents are uploaded
                context = ""
                if st.session_state.vector_store:
                    related_docs = st.session_state.vector_store.similarity_search(prompt, k=3)
                    context = "\n\n".join([doc.page_content for doc in related_docs])
                
                # Build final prompt
                final_prompt = RAG_TEMPLATE.format(
                    context=context,
                    question=prompt
                ) if context else prompt
                
                # Create messages copy with final prompt
                rag_messages = [msg.copy() for msg in st.session_state.messages]
                rag_messages[-1]["content"] = final_prompt
                
                if streaming:
                    response_container = st.empty()
                    full_response = ""
                    text_buffer = ""
                    decoder = getincrementaldecoder('utf-8')()

                    response = chat_completion(rag_messages, stream=True)
                    
                    for chunk in response.iter_content(chunk_size=1024):
                        text_chunk = decoder.decode(chunk)
                        text_buffer += text_chunk

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

                        if text_buffer:
                            response_container.markdown(text_buffer + "▌")

                    text_buffer += decoder.decode(b'', final=True)
                    if text_buffer:
                        response_container.markdown(text_buffer)
                        full_response += text_buffer
                    
                    st.session_state.messages.append(
                        {"role": "assistant", "content": full_response}
                    )
                    
                else:
                    response = chat_completion(rag_messages).json()["response"]
                    
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