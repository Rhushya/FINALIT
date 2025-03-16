import streamlit as st
from typing import Dict, Any, List, Optional
import json
import datetime

def init_session_state():
    """Initialize session state variables if they don't exist"""
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    if 'user_context' not in st.session_state:
        st.session_state.user_context = {}
    
    if 'language' not in st.session_state:
        st.session_state.language = "English"
    
    if 'language_code' not in st.session_state:
        st.session_state.language_code = "en"
    
    if 'input_mode' not in st.session_state:
        st.session_state.input_mode = "Text"
    
    if 'audio_data' not in st.session_state:
        st.session_state.audio_data = None

def add_message_to_history(role: str, content: str, translated_content: Optional[str] = None):
    """Add a message to the conversation history"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    message = {
        "role": role,
        "content": content,
        "translated_content": translated_content,
        "timestamp": timestamp
    }
    
    st.session_state.conversation_history.append(message)

def get_conversation_history() -> List[Dict[str, Any]]:
    """Get the conversation history"""
    return st.session_state.conversation_history

def clear_conversation_history():
    """Clear the conversation history"""
    st.session_state.conversation_history = []

def update_user_context(context_data: Dict[str, Any]):
    """Update the user context with new data"""
    st.session_state.user_context.update(context_data)

def get_user_context() -> Dict[str, Any]:
    """Get the user context"""
    return st.session_state.user_context

def set_language(language: str, language_code: str):
    """Set the current language and language code"""
    st.session_state.language = language
    st.session_state.language_code = language_code

def get_language() -> str:
    """Get the current language"""
    return st.session_state.language

def get_language_code() -> str:
    """Get the current language code"""
    return st.session_state.language_code

def set_input_mode(mode: str):
    """Set the input mode (Text or Voice)"""
    st.session_state.input_mode = mode

def get_input_mode() -> str:
    """Get the current input mode"""
    return st.session_state.input_mode

def set_audio_data(audio_data: bytes):
    """Set the recorded audio data"""
    st.session_state.audio_data = audio_data

def get_audio_data() -> Optional[bytes]:
    """Get the recorded audio data"""
    return st.session_state.audio_data

def extract_entities_from_conversation() -> Dict[str, Any]:
    """Extract entities from conversation history to update user context using LLM scanning"""
    entities = {}
    from utils.llm_service import LLMService
    llm_service = LLMService()
    
    # Get the most recent user message
    recent_user_messages = []
    for message in st.session_state.conversation_history:
        if message["role"] == "user":
            content = message.get("translated_content", "") or message["content"]
            recent_user_messages.append(content)
    
    # Only process if we have user messages
    if recent_user_messages:
        # Get the most recent messages (up to 3)
        recent_text = " ".join(recent_user_messages[-3:])
        
        # Use the LLM to extract entities
        extracted_entities = llm_service.extract_user_entities(recent_text)
        if extracted_entities:
            entities.update(extracted_entities)
    
    return entities