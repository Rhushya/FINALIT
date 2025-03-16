import requests
import base64
import io
import os
import logging
import wave
import tempfile
from typing import Dict, Any, Optional, List, Tuple
from utils.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextToSpeechService:
    """Service to handle text-to-speech conversion using Sarvam AI API"""
    
    def __init__(self, api_key: str = None):
        """Initialize the Text-to-Speech Service with API key"""
        self.api_key = api_key or settings.SARVAM_API_KEY
        if not self.api_key:
            logger.warning("Sarvam AI API key not provided. TTS features may not work.")
        
        # Define the API endpoint
        self.tts_endpoint = "https://api.sarvam.ai/text-to-speech"
        
        # Map for matching voices to languages
        self.voice_map = {
            "en-IN": "meera",  # English - Professional female voice
            "hi-IN": "neel",   # Hindi - Male voice
            "ta-IN": "amol",   # Tamil - Narrational male voice
            "te-IN": "meera",  # Telugu - Default to meera
            "bn-IN": "meera",  # Bengali - Default to meera
            "kn-IN": "meera",  # Kannada - Default to meera
            "ml-IN": "meera",  # Malayalam - Default to meera
            "pa-IN": "meera",  # Punjabi - Default to meera
            "mr-IN": "meera",  # Marathi - Default to meera
            "gu-IN": "meera"   # Gujarati - Default to meera
        }
        
        # Available voices
        self.available_voices = [
            "meera",      # Professional and calm
            "pavithra",   # Dramatic and engaging  
            "maitreyi",   # Engaging and informational
            "arvind",     # Conversational and articulate
            "amol",       # Narrational and mature
            "amartya",    # Expressive and distinct
            "diya",       
            "neel",       
            "misha",      
            "vian",       
            "arjun",      
            "maya"        
        ]
    
    def convert_text_to_speech(self, text: str, language_code: str = "en-IN", 
                               voice: str = None, pace: float = 1.0) -> Optional[bytes]:
        """
        Convert text to speech using Sarvam AI TTS API
        
        Args:
            text: The text to convert to speech
            language_code: The BCP-47 language code (e.g., "en-IN", "hi-IN")
            voice: The voice to use (if None, selects based on language)
            pace: Speaking pace (0.5-2.0, default 1.0)
            
        Returns:
            Audio data as bytes or None if conversion failed
        """
        # Check if text is empty
        if not text or text.strip() == "":
            logger.warning("Empty text provided for TTS conversion")
            return self._generate_silent_audio(500)  # Return 500ms of silence
        
        # Check if text exceeds max length
        if len(text) > 450:
            logger.info(f"Text length ({len(text)} chars) exceeds limit. Chunking text...")
            return self._process_long_text(text, language_code, voice, pace)
        
        # Process normal-length text
        return self._convert_single_chunk(text, language_code, voice, pace)
    
    def _convert_single_chunk(self, text: str, language_code: str, 
                              voice: str = None, pace: float = 1.0) -> Optional[bytes]:
        """Convert a single chunk of text to speech"""
        try:
            # Determine voice if not provided
            if not voice:
                voice = self.voice_map.get(language_code, "meera")
            
            # Ensure language code is valid
            if language_code not in settings.SUPPORTED_LANGUAGES.values():
                logger.warning(f"Unsupported language code: {language_code}. Defaulting to en-IN")
                language_code = "en-IN"
            
            # Prepare payload for Sarvam AI TTS API
            payload = {
                "inputs": [text],
                "target_language_code": language_code,
                "speaker": voice,
                "pitch": 0,
                "pace": pace,
                "loudness": 1.0,
                "speech_sample_rate": 22050,
                "enable_preprocessing": True,
                "model": "bulbul:v1",
                "override_triplets": {}
            }
            
            # Prepare headers
            headers = {
                "api-subscription-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            logger.info(f"Making TTS request: language={language_code}, voice={voice}, text_length={len(text)}")
            
            # Make API request
            response = requests.post(
                self.tts_endpoint,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            # Check for successful response
            if response.status_code == 200:
                result = response.json()
                
                # Extract audio data
                if "audios" in result and len(result["audios"]) > 0:
                    audio_base64 = result["audios"][0]
                    return base64.b64decode(audio_base64)
                else:
                    logger.error(f"Unexpected response format from TTS API: {result}")
                    return self._generate_fallback_audio(text, language_code)
            else:
                logger.error(f"Error from TTS API: {response.status_code} - {response.text}")
                return self._generate_fallback_audio(text, language_code)
                
        except Exception as e:
            logger.error(f"Error in TTS conversion: {str(e)}")
            return self._generate_fallback_audio(text, language_code)
    
    def _process_long_text(self, text: str, language_code: str, 
                          voice: str = None, pace: float = 1.0) -> Optional[bytes]:
        """Process long text by splitting into chunks and converting each to speech"""
        # Split text into chunks
        chunks = self._chunk_text(text)
        
        # Process each chunk
        audio_chunks = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")
            audio_data = self._convert_single_chunk(chunk, language_code, voice, pace)
            if audio_data:
                audio_chunks.append(audio_data)
        
        # Combine audio chunks
        if audio_chunks:
            return self._combine_audio_chunks(audio_chunks)
        else:
            logger.error("Failed to process any text chunks")
            return self._generate_fallback_audio(text[:200], language_code)  # Generate fallback for part of the text
    
    def _chunk_text(self, text: str, max_chunk_size: int = 450) -> List[str]:
        """Split text into chunks at natural boundaries"""
        # If text is already small enough, return it as a single chunk
        if len(text) <= max_chunk_size:
            return [text]
        
        # Define sentence-ending punctuation
        sentence_endings = ['.', '!', '?', '।', '॥', '၊', '။']
        
        chunks = []
        start_idx = 0
        
        while start_idx < len(text):
            # If the remaining text fits in one chunk, add it and break
            if start_idx + max_chunk_size >= len(text):
                chunks.append(text[start_idx:])
                break
            
            # Look for a sentence boundary within the max chunk size
            chunk_end = start_idx + max_chunk_size
            best_break = chunk_end
            
            # Try to find a sentence boundary by going backwards from the max position
            for i in range(chunk_end, start_idx, -1):
                if i < len(text) and text[i] in sentence_endings:
                    best_break = i + 1  # Include the punctuation
                    break
            
            # If no suitable sentence boundary found, look for a space
            if best_break == chunk_end:
                for i in range(chunk_end, start_idx, -1):
                    if i < len(text) and text[i].isspace():
                        best_break = i + 1  # Include the space
                        break
            
            # Add the chunk and update the start index
            chunks.append(text[start_idx:best_break])
            start_idx = best_break
        
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
    
    def _combine_audio_chunks(self, audio_chunks: List[bytes]) -> bytes:
        """Combine multiple WAV audio chunks into a single WAV file"""
        if not audio_chunks:
            return self._generate_silent_audio(500)  # Return silence if no chunks
        
        if len(audio_chunks) == 1:
            return audio_chunks[0]  # Return the single chunk directly
        
        # Create temporary files for all chunks
        temp_files = []
        try:
            # Write each chunk to a temporary file
            for i, chunk in enumerate(audio_chunks):
                temp_file = tempfile.NamedTemporaryFile(suffix=f"_chunk_{i}.wav", delete=False)
                temp_file.write(chunk)
                temp_file.close()
                temp_files.append(temp_file.name)
            
            # Prepare for reading the first file to get audio parameters
            with wave.open(temp_files[0], 'rb') as first_wav:
                params = first_wav.getparams()
                
                # Create output WAV file
                with io.BytesIO() as output_wav_io:
                    with wave.open(output_wav_io, 'wb') as output_wav:
                        output_wav.setparams(params)
                        
                        # Read and write data from all files
                        for temp_file in temp_files:
                            with wave.open(temp_file, 'rb') as wav_file:
                                output_wav.writeframes(wav_file.readframes(wav_file.getnframes()))
                    
                    # Get the combined WAV data
                    output_wav_io.seek(0)
                    return output_wav_io.read()
        
        except Exception as e:
            logger.error(f"Error combining audio chunks: {str(e)}")
            # Return the first chunk if combination fails
            return audio_chunks[0] if audio_chunks else self._generate_silent_audio(500)
        
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"Error removing temporary file {temp_file}: {str(e)}")
    
    def _generate_fallback_audio(self, text: str, language_code: str) -> bytes:
        """Generate audio using gTTS as a fallback if Sarvam API fails"""
        try:
            from gtts import gTTS
            
            # Extract the language code without the region part
            lang_code = language_code.split('-')[0]
            
            # Generate audio using gTTS
            tts = gTTS(text=text, lang=lang_code)
            
            # Save to a BytesIO object
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            # Return the audio data
            return audio_buffer.read()
        except Exception as e:
            logger.error(f"Error generating fallback audio: {str(e)}")
            # Return a minimal WAV file with silence
            return self._generate_silent_audio(1000)  # 1 second of silence
    
    def _generate_silent_audio(self, duration_ms: int = 500) -> bytes:
        """Generate a silent WAV file of specified duration"""
        try:
            # Parameters for audio creation
            sample_rate = 22050
            num_channels = 1
            sample_width = 2  # 16-bit
            
            # Calculate the number of samples
            num_samples = int(duration_ms * sample_rate / 1000)
            
            # Create a buffer of zeros (silence)
            silence_data = bytearray(num_samples * sample_width)
            
            # Create a BytesIO buffer for the WAV file
            wav_buffer = io.BytesIO()
            
            # Create a WAV file using the wave module
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(num_channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(silence_data)
            
            # Get the WAV data
            wav_buffer.seek(0)
            return wav_buffer.read()
        except Exception as e:
            logger.error(f"Error generating silent WAV: {str(e)}")
            
            # Last resort: Return a hard-coded minimal valid WAV file (44 bytes header + 1 sample)
            return bytes.fromhex(
                '52494646' +  # "RIFF"
                '2C000000' +  # Chunk size (44 + 0 bytes of data)
                '57415645' +  # "WAVE"
                '666D7420' +  # "fmt "
                '10000000' +  # Subchunk1 size (16 bytes)
                '0100' +      # Audio format (1 = PCM)
                '0100' +      # Num channels (1)
                '80BB0000' +  # Sample rate (48000 Hz)
                '00770100' +  # Byte rate (48000 * 2)
                '0200' +      # Block align (2 bytes)
                '1000' +      # Bits per sample (16)
                '64617461' +  # "data"
                '00000000'    # Subchunk2 size (0 bytes of data)
            )

# Create a function to get a singleton instance of the TTS service
_tts_service_instance = None

def get_tts_service(api_key: str = None) -> TextToSpeechService:
    """Get a singleton instance of the TextToSpeechService"""
    global _tts_service_instance
    if _tts_service_instance is None:
        _tts_service_instance = TextToSpeechService(api_key)
    return _tts_service_instance

def text_to_speech(text: str, language_code: str = "en-IN", voice: str = None, pace: float = 1.0) -> Optional[bytes]:
    """
    Convert text to speech using Sarvam AI TTS API
    
    Args:
        text: The text to convert to speech
        language_code: The BCP-47 language code (e.g., "en-IN", "hi-IN")
        voice: The voice to use (if None, selects based on language)
        pace: Speaking pace (0.5-2.0, default 1.0)
        
    Returns:
        Audio data as bytes or None if conversion failed
    """
    service = get_tts_service()
    return service.convert_text_to_speech(text, language_code, voice, pace)

def get_voice_for_language(language_code: str) -> str:
    """Get the recommended voice for a language"""
    service = get_tts_service()
    return service.voice_map.get(language_code, "meera")

def get_available_voices() -> List[str]:
    """Get a list of all available voices"""
    service = get_tts_service()
    return service.available_voices 