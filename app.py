import streamlit as st
import os
import tempfile
import base64
import io
from typing import Dict, Any, List, Optional, Tuple
import logging
import time
from langdetect import detect
from googletrans import Translator
from gtts import gTTS
import hashlib

# Import utility modules
from utils.config import settings
from utils.sarvam_api import SarvamAIService
from utils.llm_service import LLMService
from utils.loan_manager import LoanDataManager
from utils.session import (
    init_session_state, add_message_to_history, get_conversation_history,
    clear_conversation_history, update_user_context, get_user_context,
    set_language, get_language, get_language_code, set_input_mode,
    get_input_mode, set_audio_data, get_audio_data, extract_entities_from_conversation
)
from utils.audio_utils import (
    record_audio, convert_audio_format, audio_to_base64,
    base64_to_audio, play_audio, create_audio_recording_ui, chunk_audio,
    create_continuous_conversation_ui
)
# Import the new TTS service
from utils.tts_service import text_to_speech, get_voice_for_language

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
sarvam_service = SarvamAIService()
llm_service = LLMService()
loan_manager = LoanDataManager()

# Page setup
st.set_page_config(
    page_title="Multilingual Loan Advisor",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables for preventing duplicate processing
if 'processed_inputs' not in st.session_state:
    st.session_state.processed_inputs = set()

if 'processing_in_progress' not in st.session_state:
    st.session_state.processing_in_progress = False

if 'current_input_id' not in st.session_state:
    st.session_state.current_input_id = None

def setup_sidebar():
    """Setup sidebar UI components"""
    st.sidebar.title("Settings")
    
    # Language selection
    language_options = list(settings.SUPPORTED_LANGUAGES.keys())
    
    # Initialize language in session state if not set
    if "language" not in st.session_state:
        st.session_state.language = language_options[0]  # Default to first language
    
    selected_language = st.sidebar.selectbox(
        "Select Language",
        language_options,
        index=language_options.index(get_language())
    )
    
    if selected_language != get_language():
        language_code = settings.SUPPORTED_LANGUAGES[selected_language]
        set_language(selected_language, language_code)
        st.sidebar.success(f"Language set to {selected_language}")
    
    # Input mode selection
    input_mode_options = ["Text", "Voice"]
    selected_input_mode = st.sidebar.radio(
        "Input Mode",
        input_mode_options,
        index=input_mode_options.index(get_input_mode())
    )
    
    if selected_input_mode != get_input_mode():
        set_input_mode(selected_input_mode)
        st.sidebar.success(f"Input mode set to {selected_input_mode}")
    
    # Audio playback and download options
    st.sidebar.subheader("Audio Settings")
    
    # Audio autoplay option
    if "autoplay_audio" not in st.session_state:
        st.session_state.autoplay_audio = True
        
    st.session_state.autoplay_audio = st.sidebar.checkbox(
        "Auto-play audio responses", 
        value=st.session_state.autoplay_audio
    )
    
    # Auto-download option
    if "auto_download_audio" not in st.session_state:
        st.session_state.auto_download_audio = False
        
    st.session_state.auto_download_audio = st.sidebar.checkbox(
        "Auto-download audio responses", 
        value=st.session_state.auto_download_audio
    )
    
    # Collapsible area for showing user information
    st.sidebar.markdown("---")
    
    # User information section
    st.sidebar.subheader("Your Information")
    
    # Display current user context
    user_context = get_user_context()
    if user_context:
        for key, value in user_context.items():
            if key == "age":
                st.sidebar.text(f"Age: {value}")
            elif key == "income":
                st.sidebar.text(f"Income: ₹{value:,}/month")
            elif key == "credit_score":
                st.sidebar.text(f"Credit Score: {value}")
            elif key == "employment_type":
                st.sidebar.text(f"Employment: {value.replace('_', ' ').title()}")
    else:
        st.sidebar.text("No user information saved yet.")
    
    # Clear conversation button
    if st.sidebar.button("Clear Conversation"):
        clear_conversation_history()
        st.session_state.processed_inputs = set()

def display_conversation():
    """Display the conversation history"""
    st.title("Multilingual Loan Advisor 💰")
    
    # Display welcome message
    if not get_conversation_history():
        st.markdown("""
        👋 **Welcome to the Multilingual Loan Advisor!**
        
        I'm here to help you with loan-related queries in multiple languages. You can ask me about:
        
        - Loan eligibility criteria
        - Application process for different types of loans
        - Financial advice and tips
        
        You'll receive both **text and audio responses** for a better experience. Feel free to type your question or use voice input.
        
        **New Features**:
        - Improved voice recording with start/stop buttons
        - **NEW! Continuous Conversation Mode** - talk back and forth naturally without clicking buttons
        - Audio responses now automatically play (can be disabled in Settings)
        - Multiple options to download audio responses
        - Option to automatically download audio responses (enable in Settings)
        """)
    
    # Display conversation history
    for message in get_conversation_history():
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
            # Show translation if available
            if message.get("translated_content") and message["content"] != message["translated_content"]:
                with st.expander("Show translation"):
                    st.write(message["translated_content"])

@st.cache_data(show_spinner=False)
def process_text(text: str, is_voice: bool = False):
    """
    Process text input and return response with audio
    
    Args:
        text (str): The text input to process
        is_voice (bool): Whether the input came from voice recording (affects language detection)
    
    Returns:
        Tuple containing:
        - response (str): The assistant's response in the detected language
        - english_response (str): The assistant's response in English
        - input_hash (str): A hash of the input for caching
        - audio_response (bytes): The assistant's response as audio data
    """
    # Generate hash for this input
    input_hash = hashlib.md5(text.encode()).hexdigest()
    
    # Detect language if not from voice (voice is already in the correct language)
    detected_lang_code = get_language_code()  # Default to user's selected language
    translated_input = text
    
    try:
        # Try to detect language if not voice input (voice is handled by Sarvam)
        if not is_voice:
            detected_lang = detect(text)
            # Map detected language to language code format "xx-IN"
            for lang_name, lang_code in settings.SUPPORTED_LANGUAGES.items():
                if lang_code.startswith(detected_lang):
                    detected_lang_code = lang_code
                    break
            
            logger.info(f"Detected language code: {detected_lang_code}")
        else:
            # For voice input in continuous mode, try to use the last detected language
            # This helps maintain language continuity in conversations
            if st.session_state.continuous_voice_mode:
                # Check if there's a stored language from previous interaction
                if "last_detected_language" in st.session_state:
                    detected_lang_code = st.session_state.last_detected_language
                    logger.info(f"Using stored language from previous interaction: {detected_lang_code}")
        
        # Store the detected language code for response generation
        input_language = detected_lang_code
        # Save the detected language for future interactions in continuous mode
        if is_voice and st.session_state.continuous_voice_mode:
            st.session_state.last_detected_language = input_language
        
        # Translate to English for LLM processing if not in English
        if not input_language.startswith("en"):
            try:
                # Use only Sarvam AI for translation
                translation_result = sarvam_service.translate_text(
                    text, 
                    source_language=input_language, 
                    target_language="en-IN"
                )
                if "error" not in translation_result:
                    translated_input = translation_result.get("translated_text", text)
                    logger.info(f"Successfully translated input to English using Sarvam AI")
                else:
                    logger.error(f"Sarvam translation error: {translation_result.get('error')}")
                    # If Sarvam translation fails, keep original text - don't use Google fallback
                    translated_input = text
            except Exception as e:
                logger.error(f"Translation error: {str(e)}")
                # Keep original text if translation fails
                translated_input = text
    except Exception as e:
        logger.error(f"Language detection error: {str(e)}")
    
    # Generate response using LLM
    english_response = llm_service.generate_response(
        translated_input,
        language_code=input_language,  # Use detected language instead of user's selected language
        user_context=get_user_context()
    )
    
    # Translate response back to the detected language (if not English)
    response = english_response
    
    # Always translate back to the language of the input (not the user's selected language)
    if not input_language.startswith("en"):
        try:
            # First, translate the English response to the detected language
            translation_result = sarvam_service.translate_text(
                english_response,
                source_language="en-IN",
                target_language=input_language
            )
            
            if "error" not in translation_result:
                translated_response = translation_result.get("translated_text", english_response)
                logger.info(f"Successfully translated response to {input_language} using Sarvam AI")
                
                # Then, ensure the response is in the same script as the input language
                # by using the transliteration API
                transliteration_result = sarvam_service.transliterate_text(
                    translated_response,
                    source_language="en-IN",
                    target_language=input_language
                )
                
                if "error" not in transliteration_result:
                    response = transliteration_result.get("transliterated_text", translated_response)
                    logger.info(f"Successfully transliterated response using Sarvam AI")
                else:
                    logger.error(f"Sarvam transliteration error: {transliteration_result.get('error')}")
                    # If transliteration fails, use the translated response
                    response = translated_response
            else:
                logger.error(f"Sarvam response translation error: {translation_result.get('error')}")
                # If Sarvam translation fails, use English response
                response = english_response
        except Exception as e:
            logger.error(f"Response translation/transliteration error: {str(e)}")
            response = english_response
    
    # Generate audio response 
    audio_response = None
    try:
        # Use the new TTS service with the detected language code
        # Get appropriate voice for the language
        voice = get_voice_for_language(input_language)
        
        # Convert text to speech in the input language
        audio_response = text_to_speech(
            response,  # Use the translated response
            language_code=input_language,  # Use the detected input language
            voice=voice,
            pace=1.0
        )
        
        # Fallback to gTTS if new service fails
        if not audio_response:
            logger.warning("TTS service failed, falling back to gTTS")
            tts = gTTS(text=response, lang=input_language[:2])
            audio_file = io.BytesIO()
            tts.write_to_fp(audio_file)
            audio_file.seek(0)
            audio_response = audio_file.read()
            logger.info(f"Using gTTS for audio generation in {input_language}")
    except Exception as e:
        logger.error(f"Text-to-speech error: {str(e)}")
    
    return response, english_response, input_hash, audio_response

def handle_user_input():
    """Handle user input based on mode"""
    # Initialize session state as needed
    if 'processed_inputs' not in st.session_state:
        st.session_state.processed_inputs = set()
    
    if 'processing_in_progress' not in st.session_state:
        st.session_state.processing_in_progress = False
    
    # Check for setting from localStorage about language continuity
    check_last_language_js = """
    <script>
        // Function to check and retrieve last detected language
        function checkAndPassLanguage() {
            var lastLanguage = localStorage.getItem('lastDetectedLanguage');
            if (lastLanguage) {
                // We use an event to pass this to Streamlit
                const event = new CustomEvent('streamlit:language', {
                    detail: { language: lastLanguage }
                });
                window.dispatchEvent(event);
                console.log("Passed language to Streamlit: " + lastLanguage);
                
                // Store in a hidden input element as well
                var input = document.createElement('input');
                input.type = 'hidden';
                input.id = 'detected_language_input';
                input.value = lastLanguage;
                document.body.appendChild(input);
            }
        }
        
        // Run on page load
        window.addEventListener('DOMContentLoaded', checkAndPassLanguage);
    </script>
    """
    st.markdown(check_last_language_js, unsafe_allow_html=True)
    
    # Check for input mode
    if st.session_state.input_mode == "Text":
        # Text input
        text_input = st.chat_input("Type your message here...")
        
        if text_input and not st.session_state.processing_in_progress:
            # Check if we've already processed this input
            input_hash = hashlib.md5(text_input.encode()).hexdigest()
            
            if input_hash in st.session_state.processed_inputs:
                return
            
            st.session_state.processing_in_progress = True
            st.session_state.current_input_id = input_hash
            
            # Add user message to history
            add_message_to_history("user", text_input)
            
            with st.spinner("Processing..."):
                # Process the text input
                response, english_response, _, audio_response = process_text(text_input)
                
                # Add assistant message to history
                add_message_to_history(
                    "assistant", 
                    response, 
                    english_response if response != english_response else None
                )
                
                # If audio response was generated, play it (regardless of input mode)
                if audio_response:
                    # Create a clear visual response section
                    st.markdown("---")
                    st.markdown("### 🤖 Assistant Response")
                    
                    # Display text response in a highlighted container
                    with st.container():
                        st.markdown(f"**Text Response:**")
                        st.markdown(f"<div style='background-color: #f0f2f6; padding: 15px; border-radius: 5px;'>{response}</div>", unsafe_allow_html=True)
                        
                        # Show translation if available and different
                        if english_response and response != english_response:
                            with st.expander("Show English translation"):
                                st.markdown(f"<div style='background-color: #e6f3ff; padding: 10px; border-radius: 5px;'>{english_response}</div>", unsafe_allow_html=True)
                    
                    # Display audio response with a clear label
                    st.markdown("### 🔊 Audio Response")
                    
                    # Create a unique ID for the audio element
                    audio_element_id = f"audio_element_{input_hash}"
                    
                    # Create a visually distinct container for the audio player
                    with st.container():
                        st.markdown("""
                            <style>
                                .audio-container {
                                    background-color: #f0f2f6;
                                    padding: 20px;
                                    border-radius: 10px;
                                    margin: 10px 0;
                                    border: 1px solid #e0e0e0;
                                }
                                audio {
                                    width: 100%;
                                    margin: 10px 0;
                                }
                                .stAudio {
                                    background-color: white !important;
                                    padding: 10px !important;
                                    border-radius: 8px !important;
                                }
                            </style>
                            <div class="audio-container">
                        """, unsafe_allow_html=True)
                        
                        if st.session_state.continuous_voice_mode:
                            # Custom audio element with autoplay for continuous mode
                            audio_element_html = f"""
                                <audio id="{audio_element_id}" controls autoplay="autoplay" style="width: 100%;">
                                    <source src="data:audio/wav;base64,{base64.b64encode(audio_response).decode()}" type="audio/wav">
                                    Your browser does not support the audio element.
                                </audio>
                            """
                            st.markdown(audio_element_html, unsafe_allow_html=True)
                            
                            # Add JavaScript to ensure audio plays and handle continuous conversation
                            continuous_convo_js = f"""
                                <script>
                                    document.addEventListener('DOMContentLoaded', function() {{
                                        var audioElement = document.getElementById('{audio_element_id}');
                                        if (audioElement) {{
                                            console.log('Setting up audio element for continuous conversation');
                                            
                                            // Force audio play when ready
                                            audioElement.play().catch(function(error) {{
                                                console.log('Auto-play failed, waiting for user interaction');
                                            }});
                                            
                                            // When audio finishes playing, trigger next recording
                                            audioElement.addEventListener('ended', function() {{
                                                console.log('Audio playback ended, triggering new recording');
                                                localStorage.setItem('autoRecordingTriggered', 'true');
                                                window.location.reload();
                                            }});
                                        }}
                                    }});
                                </script>
                            """
                            st.markdown(continuous_convo_js, unsafe_allow_html=True)
                        else:
                            # Standard Streamlit audio player for single recording mode
                            st.audio(audio_response, format="audio/wav", start_time=0)
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Display status message for continuous mode
                    if st.session_state.continuous_voice_mode:
                        st.info("🔄 Continuous conversation mode active - The next recording will start automatically after the response finishes playing.")
                    
                    # Generate a unique ID for the download link
                    download_id = f"download_link_{input_hash}"
                    timestamp = int(time.time())
                    
                    # Add multiple download options for better compatibility
                    audio_b64 = base64.b64encode(audio_response).decode()
                    
                    # Create download buttons columns
                    col1, col2 = st.columns(2)
                    
                    # Method 1: Direct href download link
                    href = f'<a id="{download_id}" href="data:audio/wav;base64,{audio_b64}" download="assistant_response_{timestamp}.wav" style="display: inline-block; padding: 0.25em 0.75em; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px; cursor: pointer;">Download audio</a>'
                    col1.markdown(href, unsafe_allow_html=True)
                    
                    # Method 2: Save the audio data to a temporary file
                    # and provide a download button
                    if "temp_audio_file" not in st.session_state:
                        st.session_state.temp_audio_file = {}
                    
                    # Store the audio data with the timestamp as key
                    st.session_state.temp_audio_file[timestamp] = audio_response
                    
                    # Create a download button
                    if col2.download_button(
                        label="Save audio",
                        data=audio_response,
                        file_name=f"assistant_response_{timestamp}.wav",
                        mime="audio/wav"
                    ):
                        st.success("Audio downloaded successfully!")
                    
                    # Auto-download script if enabled
                    if st.session_state.auto_download_audio:
                        # Add JavaScript to auto-trigger the download
                        auto_download_js = f"""
                        <script>
                            (function() {{
                                // Function to try different download methods
                                function tryDownload() {{
                                    // Try the link click first
                                    var link = document.getElementById('{download_id}');
                                    if (link) {{
                                        console.log('Triggering download via link click');
                                        link.click();
                                        return true;
                                    }}
                                    return false;
                                }}
                                
                                // Wait for DOM to be ready
                                if (document.readyState === 'complete') {{
                                    setTimeout(tryDownload, 1500);
                                }} else {{
                                    window.addEventListener('load', function() {{
                                        setTimeout(tryDownload, 1500);
                                    }});
                                }}
                            }})();
                        </script>
                        """
                        st.markdown(auto_download_js, unsafe_allow_html=True)
                    
                    st.markdown("---")
                
                # Extract entities and update user context
                entities = extract_entities_from_conversation()
                if entities:
                    update_user_context(entities)
                
                # Mark this input as processed
                st.session_state.processed_inputs.add(input_hash)
                st.session_state.processing_in_progress = False
                # Trigger a refresh but only if this input hasn't been processed
                st.rerun()
    else:
        # Voice input handling with Continuous Conversation mode
        
        # First check if we're in continuous conversation mode
        if "continuous_voice_mode" not in st.session_state:
            st.session_state.continuous_voice_mode = False
        
        # Mode selection tabs
        tab1, tab2 = st.tabs(["Single Recording", "Continuous Conversation"])
        
        with tab1:
            # Original voice input handling
            recording_started, audio_data = create_audio_recording_ui()
            if recording_started:
                st.session_state.continuous_voice_mode = False
                
        with tab2:
            # Continuous conversation mode
            cont_recording_started, cont_audio_data, end_conversation = create_continuous_conversation_ui()
            if cont_recording_started:
                st.session_state.continuous_voice_mode = True
                recording_started = True
                audio_data = cont_audio_data
        
        # Process the audio data (from either mode)
        if audio_data and not st.session_state.processing_in_progress:
            # Generate a unique hash for this audio
            audio_hash = hashlib.md5(audio_data).hexdigest()
            
            if audio_hash in st.session_state.processed_inputs:
                return
                
            st.session_state.processing_in_progress = True
            st.session_state.current_input_id = audio_hash
            
            with st.spinner("Processing your voice input..."):
                try:
                    # Store audio data for potential debugging
                    set_audio_data(audio_data)
                    
                    # Display audio player for the input
                    st.audio(audio_data, format="audio/wav")
                    
                    # Step 1: Convert audio to text using Sarvam API
                    source_language = get_language_code()
                    logger.info(f"Using language code for speech recognition: {source_language}")
                    
                    stt_result = sarvam_service.speech_to_text(
                        audio_data,
                        source_language=source_language
                    )
                    
                    if "error" not in stt_result and "text" in stt_result and stt_result["text"].strip():
                        user_text = stt_result["text"].strip()
                        
                        # Show what user said
                        st.success(f"You said: {user_text}")
                        
                        # Add user message to history
                        add_message_to_history("user", user_text)
                        
                        # Step 2: Detect language and translate to English if necessary
                        detected_lang_code = source_language
                        english_input = user_text
                        
                        # If the detected language is not English, translate to English
                        if not detected_lang_code.startswith("en"):
                            try:
                                translation_result = sarvam_service.translate_text(
                                    user_text,
                                    source_language=detected_lang_code,
                                    target_language="en-IN"
                                )
                                
                                if "error" not in translation_result:
                                    english_input = translation_result.get("translated_text", user_text)
                                    logger.info(f"Successfully translated input to English: {english_input}")
                            except Exception as e:
                                logger.error(f"Error translating input: {str(e)}")
                        
                        # Step 3: Generate response using LLM
                        english_response = llm_service.generate_response(
                            english_input,
                            language_code=detected_lang_code,  # Use detected language code, not user selected
                            user_context=get_user_context()
                        )
                        
                        # Step 4: Translate response back to the detected language if needed
                        response = english_response
                        
                        if not detected_lang_code.startswith("en"):
                            try:
                                # Translate the English response to the detected language
                                translation_result = sarvam_service.translate_text(
                                    english_response,
                                    source_language="en-IN",
                                    target_language=detected_lang_code
                                )
                                
                                if "error" not in translation_result:
                                    translated_response = translation_result.get("translated_text", english_response)
                                    
                                    # Transliterate to ensure correct script
                                    transliteration_result = sarvam_service.transliterate_text(
                                        translated_response,
                                        source_language="en-IN",
                                        target_language=detected_lang_code
                                    )
                                    
                                    if "error" not in transliteration_result:
                                        response = transliteration_result.get("transliterated_text", translated_response)
                                    else:
                                        response = translated_response
                                else:
                                    response = english_response
                            except Exception as e:
                                logger.error(f"Error in translation/transliteration: {str(e)}")
                                response = english_response
                        
                        # Step 5: Add assistant message to history
                        add_message_to_history(
                            "assistant", 
                            response, 
                            english_response if response != english_response else None
                        )
                        
                        # Step 6: Generate audio response using the new TTS service
                        # Get appropriate voice for the detected language (not user selected)
                        voice = get_voice_for_language(detected_lang_code)
                        
                        # Convert text to speech in the detected language
                        audio_response = text_to_speech(
                            response,  # Use the translated response text
                            language_code=detected_lang_code,  # Use detected language, not user selected
                            voice=voice,
                            pace=1.0
                        )
                        
                        # Fallback to old method if new service fails
                        if not audio_response:
                            logger.warning(f"New TTS service failed, falling back to old method with language {detected_lang_code}")
                            audio_response = sarvam_service.text_to_speech(
                                response,
                                target_language=detected_lang_code  # Use detected language, not user selected
                            )
                        
                        # Step 7: Create a clear visual response section
                        st.markdown("---")
                        st.markdown("### 🤖 Assistant Response")
                        
                        # Display text response in a highlighted container
                        with st.container():
                            st.markdown(f"**Text Response:**")
                            st.markdown(f"<div style='background-color: #f0f2f6; padding: 15px; border-radius: 5px;'>{response}</div>", unsafe_allow_html=True)
                            
                            # Show translation if available and different
                            if english_response and response != english_response:
                                with st.expander("Show English translation"):
                                    st.markdown(f"<div style='background-color: #e6f3ff; padding: 10px; border-radius: 5px;'>{english_response}</div>", unsafe_allow_html=True)
                        
                        # Display audio response with a clear label
                        st.markdown("### 🔊 Audio Response")
                        
                        # Create a unique ID for the audio element
                        audio_element_id = f"audio_element_{audio_hash}"
                        
                        # Create a visually distinct container for the audio player
                        with st.container():
                            st.markdown("""
                                <style>
                                    .audio-container {
                                        background-color: #f0f2f6;
                                        padding: 20px;
                                        border-radius: 10px;
                                        margin: 10px 0;
                                        border: 1px solid #e0e0e0;
                                    }
                                    audio {
                                        width: 100%;
                                        margin: 10px 0;
                                    }
                                    .stAudio {
                                        background-color: white !important;
                                        padding: 10px !important;
                                        border-radius: 8px !important;
                                    }
                                </style>
                                <div class="audio-container">
                            """, unsafe_allow_html=True)
                            
                            if st.session_state.continuous_voice_mode:
                                # Custom audio element with autoplay for continuous mode
                                audio_element_html = f"""
                                    <audio id="{audio_element_id}" controls autoplay="autoplay" style="width: 100%;">
                                        <source src="data:audio/wav;base64,{base64.b64encode(audio_response).decode()}" type="audio/wav">
                                        Your browser does not support the audio element.
                                    </audio>
                                """
                                st.markdown(audio_element_html, unsafe_allow_html=True)
                                
                                # Add JavaScript to ensure audio plays and handle continuous conversation
                                continuous_convo_js = f"""
                                    <script>
                                        document.addEventListener('DOMContentLoaded', function() {{
                                            var audioElement = document.getElementById('{audio_element_id}');
                                            if (audioElement) {{
                                                console.log('Setting up audio element for continuous conversation');
                                                
                                                // Store the detected language for the next recording
                                                localStorage.setItem('lastDetectedLanguage', '{detected_lang_code}');
                                                console.log('Stored detected language: {detected_lang_code}');
                                                
                                                // Force audio play when ready
                                                audioElement.play().catch(function(error) {{
                                                    console.log('Auto-play failed, waiting for user interaction');
                                                }});
                                                
                                                // When audio finishes playing, trigger next recording
                                                audioElement.addEventListener('ended', function() {{
                                                    console.log('Audio playback ended, triggering new recording');
                                                    localStorage.setItem('autoRecordingTriggered', 'true');
                                                    window.location.reload();
                                                }});
                                            }}
                                        }});
                                    </script>
                                """
                                st.markdown(continuous_convo_js, unsafe_allow_html=True)
                            else:
                                # Standard Streamlit audio player for single recording mode
                                st.audio(audio_response, format="audio/wav", start_time=0)
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Display status message for continuous mode
                        if st.session_state.continuous_voice_mode:
                            st.info(f"🔄 Continuous conversation active in {detected_lang_code} - The next recording will start automatically after the response finishes playing.")
                        
                        # Generate a unique ID for the download link
                        download_id = f"download_link_{audio_hash}"
                        timestamp = int(time.time())
                        
                        # Add multiple download options for better compatibility
                        audio_b64 = base64.b64encode(audio_response).decode()
                        
                        # Create download buttons columns
                        col1, col2 = st.columns(2)
                        
                        # Method 1: Direct href download link
                        href = f'<a id="{download_id}" href="data:audio/wav;base64,{audio_b64}" download="assistant_response_{timestamp}.wav" style="display: inline-block; padding: 0.25em 0.75em; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px; cursor: pointer;">Download audio</a>'
                        col1.markdown(href, unsafe_allow_html=True)
                        
                        # Method 2: Save the audio data to a temporary file
                        # and provide a download button
                        if "temp_audio_file" not in st.session_state:
                            st.session_state.temp_audio_file = {}
                        
                        # Store the audio data with the timestamp as key
                        st.session_state.temp_audio_file[timestamp] = audio_response
                        
                        # Create a download button
                        if col2.download_button(
                            label="Save audio",
                            data=audio_response,
                            file_name=f"assistant_response_{timestamp}.wav",
                            mime="audio/wav"
                        ):
                            st.success("Audio downloaded successfully!")
                        
                        # Auto-download script if enabled
                        if st.session_state.auto_download_audio:
                            # Add JavaScript to auto-trigger the download
                            auto_download_js = f"""
                            <script>
                                (function() {{
                                    // Function to try different download methods
                                    function tryDownload() {{
                                        // Try the link click first
                                        var link = document.getElementById('{download_id}');
                                        if (link) {{
                                            console.log('Triggering download via link click');
                                            link.click();
                                            return true;
                                        }}
                                        return false;
                                    }}
                                    
                                    // Wait for DOM to be ready
                                    if (document.readyState === 'complete') {{
                                        setTimeout(tryDownload, 1500);
                                    }} else {{
                                        window.addEventListener('load', function() {{
                                            setTimeout(tryDownload, 1500);
                                        }});
                                    }}
                                }})();
                            </script>
                            """
                            st.markdown(auto_download_js, unsafe_allow_html=True)
                        
                        st.markdown("---")
                    
                    # Step 8: Extract entities and update user context
                    entities = extract_entities_from_conversation()
                    if entities:
                        update_user_context(entities)
                    
                    # Mark this input as processed
                    st.session_state.processed_inputs.add(audio_hash)
                    st.session_state.processing_in_progress = False
                    
                    # For continuous mode, set the auto_recording flag after processing
                    if st.session_state.continuous_voice_mode:
                        # This will be set to true when the audio finishes playing
                        if 'trigger_auto_recording' not in st.session_state:
                            st.session_state.trigger_auto_recording = False
                    
                    # Trigger a refresh
                    st.rerun()
                except Exception as e:
                    logger.error(f"Error processing voice input: {str(e)}")
                    st.error(f"Error processing voice input: {str(e)}")
                    
                    # For continuous mode, re-enable recording even after error
                    if st.session_state.continuous_voice_mode:
                        st.session_state.auto_recording = True
                    
                    st.session_state.processing_in_progress = False

def main():
    """Main application function"""
    # Initialize session state
    init_session_state()
    
    # Add JavaScript to check for continuous conversation flag on page load
    continuous_check_js = """
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Check if we should continue the conversation based on localStorage flag
            if (localStorage.getItem('continueConversation') === 'true') {
                console.log('Continuous conversation flag detected, clearing it');
                localStorage.removeItem('continueConversation');
                
                // Set timeout to give page time to load, then click the tab for continuous conversation
                setTimeout(function() {
                    console.log('Selecting continuous conversation tab');
                    // Find the tab buttons (they're usually aria-selected attributes or data-baseweb attributes)
                    var tabButtons = document.querySelectorAll('[role="tab"]');
                    if (tabButtons.length >= 2) {
                        // Second tab should be continuous conversation
                        tabButtons[1].click();
                        
                        // After tab is shown, find and click the Start Continuous Conversation button
                        setTimeout(function() {
                            var buttons = document.querySelectorAll('button');
                            for(var i=0; i<buttons.length; i++) {
                                if(buttons[i].innerText.includes('Start Continuous Conversation')) {
                                    console.log('Found and clicking Start Continuous Conversation button');
                                    buttons[i].click();
                                    break;
                                }
                            }
                        }, 500);
                    }
                }, 1000);
            }
        });
    </script>
    """
    st.markdown(continuous_check_js, unsafe_allow_html=True)
    
    # Setup sidebar
    setup_sidebar()
    
    # Display conversation
    display_conversation()
    
    # Handle user input
    handle_user_input()

if __name__ == "__main__":
    main()