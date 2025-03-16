import json
import requests
import base64
import io
import os
from typing import Dict, Any, Optional, List
from utils.config import settings
import logging
from utils.audio_utils import chunk_audio
import wave
import tempfile

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SarvamAIService:
    def __init__(self, api_key: str = None):
        """Initialize the Sarvam AI Service with API key"""
        self.api_key = api_key or settings.SARVAM_API_KEY
        if not self.api_key:
            logger.warning("Sarvam AI API key not provided. Some features may not work.")
        
        self.headers = {
            "Content-Type": "application/json",
            "api-subscription-key": self.api_key
        }
        
        # Define the API endpoints
        self.translate_endpoint = "https://api.sarvam.ai/translate"
        self.transliterate_endpoint = "https://api.sarvam.ai/transliterate"
        self.stt_endpoint = "https://api.sarvam.ai/speech-to-text"
        self.stt_translate_endpoint = "https://api.sarvam.ai/speech-to-text-translate"
        self.tts_endpoint = "https://api.sarvam.ai/text-to-speech"
    
    def speech_to_text(self, audio_data: bytes, source_language: str = None) -> Dict[str, Any]:
        """Convert speech to text using Sarvam AI speech recognition API"""
        try:
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                temp_file_path = temp_file.name
            
            try:
                # Open the file for reading in binary mode
                with open(temp_file_path, 'rb') as audio_file:
                    # Prepare the multipart/form-data request
                    files = {
                        'file': ('audio.wav', audio_file, 'audio/wav')
                    }
                    
                    # Ensure language_code is valid according to Sarvam API requirements
                    valid_languages = ['unknown', 'hi-IN', 'bn-IN', 'kn-IN', 'ml-IN', 'mr-IN', 
                                      'od-IN', 'pa-IN', 'ta-IN', 'te-IN', 'en-IN', 'gu-IN']
                    
                    # Map simple language code to valid Sarvam language code
                    language_map = {
                        'en': 'en-IN',
                        'hi': 'hi-IN',
                        'bn': 'bn-IN',
                        'kn': 'kn-IN',
                        'ml': 'ml-IN',
                        'mr': 'mr-IN',
                        'od': 'od-IN',
                        'pa': 'pa-IN',
                        'ta': 'ta-IN',
                        'te': 'te-IN',
                        'gu': 'gu-IN'
                    }
                    
                    # Set language code, handling simple codes and defaults
                    if source_language and source_language in valid_languages:
                        language_code = source_language
                    elif source_language and source_language in language_map:
                        language_code = language_map[source_language]
                    else:
                        language_code = "unknown"  # Default to unknown if language not specified or invalid
                    
                    logger.info(f"Using language code for speech recognition: {language_code}")
                    
                    # Create form data
                    data = {
                        'model': 'saarika:v2',
                        'language_code': language_code,
                        'with_timestamps': 'false',
                        'with_diarization': 'false',
                        'num_speakers': '1'
                    }
                    
                    # Create headers
                    headers = {
                        'api-subscription-key': self.api_key
                    }
                    
                    # Make API request
                    response = requests.post(
                        self.stt_endpoint,
                        files=files,
                        data=data,
                        headers=headers,
                        timeout=30
                    )
                    
                    # Check for successful response
                    if response.status_code == 200:
                        result = response.json()
                        logger.info(f"STT API result: {result}")
                        
                        # Extract text from the response
                        if "transcript" in result:
                            return {
                                "text": result["transcript"].strip(),
                                "chunks": 1,
                                "detailed_results": [result]
                            }
                        else:
                            logger.warning("No transcript detected in audio")
                            return {"error": "No text detected", "text": ""}
                    else:
                        logger.error(f"Error from Sarvam API: {response.status_code} - {response.text}")
                        return {"error": f"API Error: {response.status_code}", "text": ""}
            
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Error removing temporary file: {str(e)}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in speech to text conversion: {str(e)}")
            return {"error": str(e), "text": ""}
        except Exception as e:
            logger.error(f"Unexpected error in speech to text conversion: {str(e)}")
            return {"error": str(e), "text": ""}
    
    def speech_to_text_translate(self, audio_data: bytes, prompt: str = "") -> Dict[str, Any]:
        """Convert speech to text and translate using Sarvam AI API"""
        try:
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                temp_file_path = temp_file.name
            
            try:
                # Open the file for reading in binary mode
                with open(temp_file_path, 'rb') as audio_file:
                    # Prepare the multipart/form-data request
                    files = {
                        'file': ('audio.wav', audio_file, 'audio/wav')
                    }
                    
                    # Create form data
                    data = {
                        'model': 'saaras:v2',
                        'with_diarization': 'false',
                        'num_speakers': '1'
                    }
                    
                    # Add prompt if provided
                    if prompt:
                        data['prompt'] = prompt
                    
                    # Create headers
                    headers = {
                        'api-subscription-key': self.api_key
                    }
                    
                    logger.info(f"Making speech-to-text-translate request with data: {data}")
                    
                    # Make API request
                    response = requests.post(
                        self.stt_translate_endpoint,
                        files=files,
                        data=data,
                        headers=headers,
                        timeout=30
                    )
                    
                    # Check for successful response
                    if response.status_code == 200:
                        result = response.json()
                        logger.info(f"STT translate API result: {result}")
                        
                        # Extract translated text from the response
                        if "translation" in result:
                            return {
                                "translated_text": result["translation"],
                                "source_text": result.get("transcript", ""),
                                "source_language": result.get("source_language", "unknown"),
                                "target_language": result.get("target_language", "en")
                            }
                        else:
                            logger.warning("No translation in response")
                            return {"error": "No translation received", "translated_text": ""}
                    else:
                        logger.error(f"Error from STT Translate API: {response.status_code} - {response.text}")
                        return {"error": f"API Error: {response.status_code}", "translated_text": ""}
            
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Error removing temporary file: {str(e)}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in speech to text translation: {str(e)}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in speech to text translation: {str(e)}")
            return {"error": str(e)}
    
    def text_to_speech(self, text: str, target_language: str = "en-IN") -> Optional[bytes]:
        """Convert text to speech using Sarvam AI text-to-speech API"""
        try:
            # Check if the text exceeds the length limit
            if len(text) > 450:
                logger.info(f"Text length ({len(text)} chars) exceeds chunk size limit. Chunking text...")
                # Use the chunk_text method to split text into smaller chunks
                audio_chunks = self.process_text_chunks(text, target_language)
                if audio_chunks:
                    # Combine all audio chunks into a single audio file
                    return self.combine_audio_chunks(audio_chunks)
                else:
                    logger.error("Failed to process text chunks")
                    return self.generate_fallback_audio(text[:450], target_language)
            
            # For short texts, process normally
            # Determine the speaker based on the language
            speaker = "meera"  # Default speaker for English
            if target_language.startswith("hi"):
                speaker = "neel"  # Hindi speaker
            elif target_language.startswith("ta"):
                speaker = "amol"  # Tamil speaker
            
            # Map simple language code to valid Sarvam language code
            language_map = {
                'en': 'en-IN',
                'hi': 'hi-IN',
                'bn': 'bn-IN',
                'kn': 'kn-IN',
                'ml': 'ml-IN',
                'mr': 'mr-IN',
                'od': 'od-IN',
                'pa': 'pa-IN',
                'ta': 'ta-IN',
                'te': 'te-IN',
                'gu': 'gu-IN'
            }
            
            # Set language code, handling simple codes
            if target_language in language_map:
                target_language = language_map[target_language]
            
            # Prepare payload according to Sarvam API structure
            payload = {
                "inputs": [text],
                "target_language_code": target_language,
                "speaker": speaker,
                "loudness": 1,
                "speech_sample_rate": 22050,
                "enable_preprocessing": False,
                "override_triplets": {}
            }
            
            logger.info(f"Making TTS request with text length: {len(text)}, language: {target_language}, speaker: {speaker}")
            
            # Create headers
            headers = {
                "api-subscription-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Make API request
            response = requests.post(
                self.tts_endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # Log the response for debugging
            logger.info(f"TTS API response status: {response.status_code}")
            
            # Check for successful response
            if response.status_code == 200:
                result = response.json()
                logger.info(f"TTS API response: {result.keys()}")
                
                if "audios" in result and len(result["audios"]) > 0:
                    audio_content = result["audios"][0]
                    return base64.b64decode(audio_content)
                else:
                    logger.error(f"Unexpected response format from Sarvam TTS API: {result}")
                    return self.generate_fallback_audio(text, target_language)
            else:
                logger.error(f"Error from Sarvam TTS API: {response.status_code} - {response.text}")
                return self.generate_fallback_audio(text, target_language)
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in text to speech conversion: {str(e)}")
            return self.generate_fallback_audio(text, target_language)
        except Exception as e:
            logger.error(f"Unexpected error in text to speech conversion: {str(e)}")
            return self.generate_fallback_audio(text, target_language)
    
    def chunk_text(self, text: str, max_chunk_size: int = 450) -> List[str]:
        """
        Split text into chunks of specified maximum size, attempting to break at sentence boundaries.
        
        Args:
            text: The text to chunk
            max_chunk_size: Maximum size of each chunk in characters
            
        Returns:
            List of text chunks
        """
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
            
            # If still no good breaking point, just break at the max size
            if best_break == chunk_end and best_break < len(text):
                pass  # Use the calculated chunk_end
            
            # Add the chunk and update the start index
            chunks.append(text[start_idx:best_break])
            start_idx = best_break
        
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
    
    def process_text_chunks(self, text: str, target_language: str) -> List[bytes]:
        """
        Process text by splitting into chunks and converting each to speech.
        
        Args:
            text: The text to process
            target_language: The target language for TTS
            
        Returns:
            List of audio bytes for each chunk
        """
        chunks = self.chunk_text(text)
        audio_chunks = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")
            
            # Determine the speaker based on the language
            speaker = "meera"  # Default speaker for English
            if target_language.startswith("hi"):
                speaker = "neel"  # Hindi speaker
            elif target_language.startswith("ta"):
                speaker = "amol"  # Tamil speaker
            
            # Map simple language code to valid Sarvam language code
            language_map = {
                'en': 'en-IN',
                'hi': 'hi-IN',
                'bn': 'bn-IN',
                'kn': 'kn-IN',
                'ml': 'ml-IN',
                'mr': 'mr-IN',
                'od': 'od-IN',
                'pa': 'pa-IN',
                'ta': 'ta-IN',
                'te': 'te-IN',
                'gu': 'gu-IN'
            }
            
            # Set language code, handling simple codes
            if target_language in language_map:
                lang_code = language_map[target_language]
            else:
                lang_code = target_language
            
            # Prepare payload according to Sarvam API structure
            payload = {
                "inputs": [chunk],
                "target_language_code": lang_code,
                "speaker": speaker,
                "loudness": 1,
                "speech_sample_rate": 22050,
                "enable_preprocessing": False,
                "override_triplets": {}
            }
            
            # Create headers
            headers = {
                "api-subscription-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            try:
                # Make API request
                response = requests.post(
                    self.tts_endpoint,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                # Check for successful response
                if response.status_code == 200:
                    result = response.json()
                    
                    if "audios" in result and len(result["audios"]) > 0:
                        audio_content = result["audios"][0]
                        audio_chunks.append(base64.b64decode(audio_content))
                    else:
                        logger.error(f"Unexpected response format from Sarvam TTS API: {result}")
                        # Use fallback for this chunk
                        fallback_audio = self.generate_fallback_audio(chunk, lang_code)
                        if fallback_audio:
                            audio_chunks.append(fallback_audio)
                else:
                    logger.error(f"Error from Sarvam TTS API for chunk {i+1}: {response.status_code} - {response.text}")
                    # Use fallback for this chunk
                    fallback_audio = self.generate_fallback_audio(chunk, lang_code)
                    if fallback_audio:
                        audio_chunks.append(fallback_audio)
            
            except Exception as e:
                logger.error(f"Error processing chunk {i+1}: {str(e)}")
                # Use fallback for this chunk
                fallback_audio = self.generate_fallback_audio(chunk, lang_code)
                if fallback_audio:
                    audio_chunks.append(fallback_audio)
        
        return audio_chunks
    
    def combine_audio_chunks(self, audio_chunks: List[bytes]) -> bytes:
        """
        Combine multiple WAV audio chunks into a single WAV file.
        
        Args:
            audio_chunks: List of audio data as bytes
            
        Returns:
            Combined audio data as bytes
        """
        if not audio_chunks:
            return self.generate_silent_wav(500)  # Return silence if no chunks
        
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
            return audio_chunks[0] if audio_chunks else self.generate_silent_wav(500)
        
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"Error removing temporary file {temp_file}: {str(e)}")
    
    def generate_fallback_audio(self, text: str, target_language: str = "en-IN") -> Optional[bytes]:
        """Generate audio using gTTS as a fallback if Sarvam API fails"""
        try:
            from gtts import gTTS
            
            # Extract the language code without the region part
            lang_code = target_language.split('-')[0]
            
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
            return self.generate_silent_wav(1000)  # 1 second of silence
    
    def generate_silent_wav(self, duration_ms: int = 500) -> bytes:
        """Generate a silent WAV file of specified duration"""
        try:
            # Parameters for audio creation
            sample_rate = 16000
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
    
    def translate_text(self, text: str, source_language: str = "en-IN", target_language: str = "en-IN") -> Dict[str, Any]:
        """Translate text from source language to target language"""
        try:
            # Log the translation request
            logger.info(f"Translating text from {source_language} to {target_language}")
            
            # Prepare payload according to Sarvam API structure
            payload = {
                "input": text,
                "source_language_code": source_language,
                "target_language_code": target_language,
                "speaker_gender": "Female",
                "mode": "formal",
                "model": "mayura:v1",
                "enable_preprocessing": False,
                "output_script": "roman",
                "numerals_format": "international"
            }
            
            # Create headers
            headers = {
                "api-subscription-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Make API request
            response = requests.post(
                self.translate_endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            # Check for successful response
            if response.status_code == 200:
                result = response.json()
                translated_text = result.get("translated_text", text)
                
                # Log successful translation (truncate long texts)
                display_text = text[:50] + "..." if len(text) > 50 else text
                display_translated = translated_text[:50] + "..." if len(translated_text) > 50 else translated_text
                logger.info(f"Translation successful: '{display_text}' → '{display_translated}'")
                
                return {
                    "translated_text": translated_text,
                    "source_language": source_language,
                    "target_language": target_language
                }
            else:
                # Extract and format error details
                error_message = f"API Error {response.status_code}"
                try:
                    error_details = response.json()
                    error_message += f": {error_details.get('detail', error_details)}"
                except:
                    error_message += f": {response.text}"
                
                logger.error(f"Translation failed: {error_message}")
                return {"error": error_message, "translated_text": text}
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error in translation: {str(e)}")
            return {"error": f"Network error: {str(e)}", "translated_text": text}
        except Exception as e:
            logger.error(f"Unexpected error in translation: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}", "translated_text": text}
    
    def transliterate_text(self, text: str, source_language: str = "en-IN", target_language: str = "en-IN") -> Dict[str, Any]:
        """Transliterate text from source language to target language"""
        try:
            # Prepare payload according to Sarvam API structure
            payload = {
                "input": text,
                "source_language_code": source_language,
                "target_language_code": target_language,
                "numerals_format": "international",
                "spoken_form_numerals_language": "native",
                "spoken_form": False
            }
            
            # Make API request
            response = requests.post(
                self.transliterate_endpoint,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            # Check for successful response
            if response.status_code == 200:
                result = response.json()
                return {
                    "transliterated_text": result.get("transliterated_text", text),
                    "source_language": source_language,
                    "target_language": target_language
                }
            else:
                logger.error(f"Error from Sarvam Transliterate API: {response.status_code} - {response.text}")
                return {"error": f"API Error: {response.status_code}", "transliterated_text": text}
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in transliteration: {str(e)}")
            return {"error": str(e), "transliterated_text": text}  # Return original text on error
        except Exception as e:
            logger.error(f"Unexpected error in transliteration: {str(e)}")
            return {"error": str(e), "transliterated_text": text} 