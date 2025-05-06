import streamlit as st
import requests
import json
from typing import List
import os

# Configure the API endpoint
API_URL = "https://sweeping-moth-probably.ngrok-free.app/"  # Change this if your API is hosted elsewhere

def upload_pdfs(files):
    """Upload multiple PDF files to the API"""
    if not files:
        return {"status": "error", "message": "No files selected"}
    
    # Prepare files for upload
    files_data = [("files", (file.name, file.getvalue(), "application/pdf")) for file in files]
    
    try:
        response = requests.post(f"{API_URL}/upload_pdfs/", files=files_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"API error: {str(e)}"}

def query_rag(query, mode="hybrid"):
    """Query the RAG system"""
    try:
        response = requests.post(
            f"{API_URL}/query/",
            json={"query": query, "mode": mode}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"API error: {str(e)}"}

def check_api_status():
    """Check if the API is running and RAG is initialized"""
    try:
        response = requests.get(f"{API_URL}/status/")
        response.raise_for_status()
        return response.json()
    except:
        return {"status": "error", "message": "API is not available"}

def get_available_modes():
    """Get available search modes from the API"""
    try:
        response = requests.get(f"{API_URL}/modes/")
        response.raise_for_status()
        return response.json()
    except:
        # Default modes if API call fails
        return {
            "available_modes": [
                {"name": "hybrid", "description": "Combines local and global approaches"},
                {"name": "local", "description": "Uses local context for retrieving relevant information"},
                {"name": "global", "description": "Uses global context for broader information retrieval"},
                {"name": "naive", "description": "Simple text matching without context awareness"},
                {"name": "mix", "description": "Mix of different search strategies"}
            ],
            "default_mode": "hybrid"
        }

# Set up the Streamlit app
st.set_page_config(
    page_title="LightRAG - BulkChat",
    layout="wide"
)

# Main title
st.title("LightRAG - BulkChat")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Check API status
api_status = check_api_status()
api_ready = api_status.get("status") == "ready"

# Sidebar for uploading files and configuration
with st.sidebar:
    st.header("Upload PDFs")
    
    uploaded_files = st.file_uploader(
        "Upload PDF documents",
        type=["pdf"],
        accept_multiple_files=True
    )
    
    if st.button("Process PDFs", disabled=not uploaded_files):
        with st.spinner("Processing PDFs..."):
            result = upload_pdfs(uploaded_files)
            if result.get("status") == "success":
                st.success(result.get("message"))
                if "details" in result and "results" in result["details"]:
                    for file_result in result["details"]["results"]:
                        status_icon = "✅" if file_result["status"] == "success" else "❌"
                        st.text(f"{status_icon} {file_result['file']}")
            else:
                st.error(result.get("message", "Unknown error"))
    
    st.divider()
    
    # Search mode selection
    st.header("Settings")
    modes = get_available_modes()
    mode_options = {mode["name"]: mode["description"] for mode in modes.get("available_modes", [])}
    
    default_mode = modes.get("default_mode", "hybrid")
    selected_mode = st.selectbox(
        "Search Mode",
        options=list(mode_options.keys()),
        index=list(mode_options.keys()).index(default_mode) if default_mode in mode_options else 0,
        format_func=lambda x: f"{x} - {mode_options[x]}"
    )
    
    st.divider()
    
    # Show API status
    st.subheader("System Status")
    status_color = "green" if api_ready else "red"
    status_text = "Ready" if api_ready else "Not Ready"
    st.markdown(f"API: <span style='color:{status_color};'>{status_text}</span>", unsafe_allow_html=True)
    
    if not api_ready:
        st.info("System is not ready. Upload some PDFs broo.")

# Display chat messages
st.subheader("Chat")
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("Ask questions about ur docs..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            if api_ready:
                response = query_rag(prompt, mode=selected_mode)
                if "response" in response:
                    result = response["response"]
                    st.write(result)
                    # Add response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": result})
                else:
                    error_msg = response.get("message", "Unknown error occurred")
                    st.error(f"Error: {error_msg}")
                    # Add error to chat history
                    st.session_state.messages.append({"role": "assistant", "content": f"Error: {error_msg}"})
            else:
                st.warning("Upload and process some PDFs broo!")
                # Add warning to chat history
                st.session_state.messages.append({"role": "assistant", "content": "Upload and process some PDFs broo!"})

# Footer
st.markdown("---")
st.caption("Upload A LOT of PDF's cause u can't read on your own!")