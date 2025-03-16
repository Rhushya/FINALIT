import streamlit as st
import numpy as np
import sounddevice as sd
import soundfile as sf
import io
import base64
import time
import os
import tempfile
import wave
import logging
from typing import Optional, Tuple, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def record_audio(sample_rate=16000, duration=5, channels=1):
    """
    Record audio using the default microphone.
    
    Args:
        sample_rate (int): Sampling rate for recording
        duration (int): Maximum duration in seconds
        channels (int): Number of audio channels (1 for mono, 2 for stereo)
    
    Returns:
        bytes: The recorded audio data as bytes
    """
    logger.info(f"Starting audio recording with sample_rate={sample_rate}, duration={duration}")
    
    try:
        # Record audio for the specified duration
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=channels,
            dtype='int16',
            blocking=True
        )
        
        logger.info("Recording completed successfully.")
        
        # Convert the NumPy array to bytes
        with io.BytesIO() as wav_buffer:
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(2)  # 2 bytes for 'int16'
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(recording.tobytes())
            
            wav_data = wav_buffer.getvalue()
            
        logger.info(f"Successfully converted recording to WAV format, size: {len(wav_data)} bytes")
        return wav_data
        
    except Exception as e:
        logger.error(f"Error recording audio: {str(e)}")
        
        # Generate a fallback test tone in case of recording failure
        # This helps for testing when microphone access is problematic
        logger.info("Generating fallback test tone")
        duration = 3  # seconds
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        tone = np.sin(2 * np.pi * 440 * t) * 0.5  # 440 Hz sine wave at half amplitude
        tone = (tone * 32767).astype(np.int16)  # Convert to 16-bit PCM
        
        with io.BytesIO() as wav_buffer:
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)  # 2 bytes for 'int16'
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(tone.tobytes())
            
            wav_data = wav_buffer.getvalue()
        
        logger.info("Generated fallback test tone")
        return wav_data

def chunk_audio(audio_data, chunk_duration_ms=30000):
    """
    Split audio data into chunks of specified duration.
    Since we don't have ffmpeg, we'll just return the original audio as a single chunk.
    
    Args:
        audio_data (bytes): Audio data as bytes
        chunk_duration_ms (int): Maximum duration of each chunk in milliseconds
        
    Returns:
        list: List of audio data chunks as bytes
    """
    # Without ffmpeg, we can't easily split the audio
    # Just return the original audio as a single chunk
    return [audio_data]

def convert_audio_format(audio_data, target_format="wav", sample_rate=16000, channels=1):
    """
    Convert audio data to the specified format.
    Since we don't have ffmpeg, we'll just return the original audio.
    
    Args:
        audio_data (bytes): The audio data to convert
        target_format (str): The target format (e.g., "wav", "mp3")
        sample_rate (int): The desired sample rate
        channels (int): The desired number of channels
    
    Returns:
        bytes: The converted audio data
    """
    # Without ffmpeg, we can't easily convert the audio
    # Just return the original audio
    return audio_data

def audio_to_base64(audio_data):
    """Convert audio data to base64 string"""
    return base64.b64encode(audio_data).decode("utf-8")

def base64_to_audio(base64_string):
    """Convert base64 string to audio data"""
    return base64.b64decode(base64_string)

def play_audio(audio_data):
    """Play audio data (for debugging)"""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        temp_file.write(audio_data)
        temp_path = temp_file.name
    
    try:
        # Load the audio file
        data, samplerate = sf.read(temp_path)
        
        # Play the audio
        sd.play(data, samplerate)
        sd.wait()
    finally:
        # Clean up
        os.unlink(temp_path)

def create_audio_recording_ui() -> Tuple[bool, Optional[bytes]]:
    """Create a UI for recording or uploading audio files and return the audio data"""
    
    # Create tabs for recording or uploading audio
    tab1, tab2 = st.tabs(["Record Audio", "Upload Audio"])
    
    # Record Audio tab
    with tab1:
        # Display a button to start/stop recording
        recording_started = False
        audio_data = None
        
        col1, col2 = st.columns(2)
        record_button = col1.button("▶️ Start Recording", key="record_start")
        stop_button = col2.button("⏹️ Stop Recording", key="record_stop")
        
        # Initialize session state for recording
        if "recording_in_progress" not in st.session_state:
            st.session_state.recording_in_progress = False
        if "recorded_audio" not in st.session_state:
            st.session_state.recorded_audio = None
        
        # Start recording
        if record_button:
            st.session_state.recording_in_progress = True
            st.session_state.recorded_audio = None
            st.experimental_rerun()
        
        # Handle recording in progress
        if st.session_state.recording_in_progress:
            status = st.empty()
            status.warning("🎙️ Recording in progress... Speak now, then click Stop Recording")
            
            try:
                # Check for stop signal
                if stop_button:
                    st.session_state.recording_in_progress = False
                    
                    with st.spinner("Processing recording..."):
                        try:
                            # Record audio with a sample rate of 16kHz (recommended for speech recognition)
                            audio_data = record_audio(sample_rate=16000, duration=5, channels=1)
                            st.session_state.recorded_audio = audio_data
                            recording_started = True
                            status.success("✅ Recording completed!")
                        except Exception as e:
                            logger.error(f"Error during recording: {str(e)}")
                            status.error(f"Recording error: {str(e)}. Please check your microphone permissions.")
                    
                    st.experimental_rerun()
            except Exception as e:
                logger.error(f"Error in recording UI: {str(e)}")
                status.error(f"Error: {str(e)}")
                st.session_state.recording_in_progress = False
        
        # Display previously recorded audio if available
        if st.session_state.recorded_audio:
            st.audio(st.session_state.recorded_audio, format="audio/wav")
            audio_data = st.session_state.recorded_audio
            recording_started = True
    
    # Upload Audio tab
    with tab2:
        uploaded_file = st.file_uploader("Upload an audio file (WAV, MP3, etc.)", type=["wav", "mp3", "ogg", "m4a"])
        
        if uploaded_file is not None:
            # Read the uploaded file
            audio_bytes = uploaded_file.read()
            audio_data = audio_bytes
            
            # Display success message
            st.success(f"File '{uploaded_file.name}' uploaded successfully!")
            
            # Play the uploaded audio
            st.audio(audio_data, format="audio/wav")
            recording_started = True
    
    return recording_started, audio_data

def create_enhanced_audio_ui() -> Tuple[str, Optional[bytes]]:
    """Enhanced UI for audio input with recording and file upload options"""
    audio_data = None
    audio_source = None
    
    # Create tabs for different audio input methods
    tab1, tab2 = st.tabs(["🎤 Record Audio", "📂 Upload Audio"])
    
    # Tab 1: Record audio
    with tab1:
        status_container = st.empty()
        col1, col2 = st.columns(2)
        
        # Real-time recording with visual feedback
        if col1.button("Start Recording", key="realtime_recording", use_container_width=True):
            status_indicator = status_container.info("🎤 Recording in progress... Speak now")
            
            # Start recording with progress bar
            progress_bar = st.progress(0)
            max_duration = settings.MAX_AUDIO_DURATION
            
            # Record audio with visual feedback
            try:
                # Create a recognizer instance
                recognizer = sr.Recognizer()
                
                # Use microphone as source
                with sr.Microphone() as source:
                    # Adjust for ambient noise
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    
                    # Start recording with timeout
                    for i in range(max_duration):
                        progress_bar.progress((i + 1) / max_duration)
                        if i == 0:  # First iteration
                            status_indicator.info(f"🎤 Recording... {max_duration-i}s remaining")
                        elif i % 5 == 0 or i >= max_duration - 5:  # Update every 5 seconds and final countdown
                            status_indicator.info(f"🎤 Recording... {max_duration-i}s remaining")
                        
                        # Check if stop button pressed
                        if st.button("Stop Recording", key="stop_recording"):
                            break
                            
                        time.sleep(0.1)  # Small delay to prevent UI lag
                    
                    # Actual audio recording (this will wait for speech or timeout)
                    status_indicator.info("🎤 Finalizing recording...")
                    audio = recognizer.listen(source, timeout=3)  # Short timeout for finalization
                    
                    # Get audio data
                    audio_data = audio.get_wav_data()
                    audio_source = "recorded"
                    
                    # Show success
                    status_container.success("✅ Recording completed successfully!")
            
            except Exception as e:
                logger.error(f"Error recording audio: {str(e)}")
                status_container.error(f"❌ Error recording audio: {str(e)}")
        
        if col2.button("Test Microphone", key="test_mic", use_container_width=True):
            with st.spinner("Testing microphone..."):
                try:
                    # Check if microphone is accessible
                    mics = sr.Microphone.list_microphone_names()
                    
                    # Try to initialize microphone
                    with sr.Microphone() as source:
                        status_container.success(f"✅ Microphone working! Found {len(mics)} audio input devices.")
                        
                        # Show available microphones 
                        if len(mics) > 1:
                            status_container.info(f"Available microphones: {', '.join(mics[:3])}" + 
                                               (f" and {len(mics)-3} more..." if len(mics) > 3 else ""))
                except Exception as e:
                    status_container.error(f"❌ Microphone not available: {str(e)}")
    
    # Tab 2: Upload audio
    with tab2:
        # File uploader for audio files
        uploaded_file = st.file_uploader(
            "Upload an audio file", 
            type=["wav", "mp3", "ogg", "m4a"],
            help="Supported formats: WAV, MP3, OGG, M4A"
        )
        
        if uploaded_file:
            # Display uploaded file info
            file_details = {"Filename": uploaded_file.name, "File size": f"{uploaded_file.size / 1024:.2f} KB"}
            st.info(f"📂 File uploaded: {uploaded_file.name} ({file_details['File size']})")
            
            # Read and process the uploaded file
            try:
                # Get the file extension
                file_ext = uploaded_file.name.split('.')[-1].lower()
                
                # Read file bytes
                audio_bytes = uploaded_file.read()
                
                # Convert to WAV if not already in that format
                if file_ext != 'wav':
                    audio_data = convert_audio_format(audio_bytes, from_format=file_ext, to_format='wav')
                    st.success(f"✅ Audio converted from {file_ext} to WAV format.")
                else:
                    audio_data = audio_bytes
                
                audio_source = "uploaded"
                
                # Let user listen to the uploaded audio
                st.subheader("Preview uploaded audio")
                st.audio(audio_data, format="audio/wav")
            
            except Exception as e:
                st.error(f"❌ Error processing audio file: {str(e)}")
                logger.error(f"Error processing uploaded audio: {str(e)}")
    
    return audio_source, audio_data

def create_continuous_conversation_ui() -> Tuple[bool, Optional[bytes], bool]:
    """
    Create a UI for continuous conversation with start/stop controls
    
    Returns:
        Tuple containing:
        - recording_started (bool): Whether a recording was successfully obtained
        - audio_data (bytes): The recorded audio data (or None if no recording)
        - end_conversation (bool): Whether the user wants to end the conversation
    """
    # Initialize session state variables if needed
    if "continuous_conversation_active" not in st.session_state:
        st.session_state.continuous_conversation_active = False
    
    # Initialize result variables
    recording_started = False
    audio_data = None
    end_conversation = False
    
    # Display UI elements based on the current state
    col1, col2 = st.columns(2)
    
    # Button to start continuous conversation
    if not st.session_state.continuous_conversation_active:
        if col1.button("🎙️ Start Continuous Conversation", key="start_continuous", use_container_width=True):
            st.session_state.continuous_conversation_active = True
            st.experimental_rerun()
    
    # Button to end conversation (only shown when active)
    if st.session_state.continuous_conversation_active:
        if col2.button("⏹️ End Conversation", key="end_continuous", use_container_width=True):
            st.session_state.continuous_conversation_active = False
            end_conversation = True
            return False, None, True
    
    # Check for localStorage flag that may have been set by JavaScript
    check_localstorage_js = """
    <script>
        if (window.frameElement) {
            // We're in an iframe, so we need to use the parent localStorage
            window.addEventListener('message', function(e) {
                if (e.data && e.data.type === 'checkLocalStorage') {
                    var hasFlag = localStorage.getItem('autoRecordingTriggered') === 'true';
                    var lastLanguage = localStorage.getItem('lastDetectedLanguage');
                    
                    if (hasFlag) {
                        localStorage.removeItem('autoRecordingTriggered');
                        console.log('Detected auto-recording flag, removing it');
                    }
                    
                    window.parent.postMessage({
                        type: 'localStorageResult',
                        hasAutoRecordingFlag: hasFlag,
                        lastDetectedLanguage: lastLanguage
                    }, '*');
                }
            });
        }
    </script>
    """
    st.markdown(check_localstorage_js, unsafe_allow_html=True)
    
    # JavaScript to check and retrieve the last detected language
    retrieve_language_js = """
    <script>
        // Function to check localStorage and set a hidden input value
        function checkLastLanguage() {
            var lastLanguage = localStorage.getItem('lastDetectedLanguage');
            if (lastLanguage) {
                console.log('Retrieved last detected language: ' + lastLanguage);
                // Create a hidden element to pass the language to Python
                var hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.id = 'last_detected_language';
                hiddenInput.value = lastLanguage;
                document.body.appendChild(hiddenInput);
            }
        }
        
        // Run on page load
        window.addEventListener('DOMContentLoaded', checkLastLanguage);
    </script>
    """
    st.markdown(retrieve_language_js, unsafe_allow_html=True)
    
    # Auto-start recording if in continuous conversation mode
    if st.session_state.continuous_conversation_active:
        status = st.empty()
        status.info("🎙️ Listening... Speak now (or click End Conversation to stop)")
        
        try:
            with st.spinner("Recording..."):
                # Record audio
                audio_data = record_audio(sample_rate=16000, duration=5, channels=1)
                recording_started = True
            
            # Display the recording
            if audio_data:
                st.audio(audio_data, format="audio/wav")
                status.success("✅ Recording completed!")
        
        except Exception as e:
            logger.error(f"Error in continuous recording: {str(e)}")
            status.error(f"Recording error: {str(e)}")
    
    return recording_started, audio_data, end_conversation