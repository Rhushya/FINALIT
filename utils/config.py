import os
from dotenv import load_dotenv

# Load environment variables from .env file in parent directory
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

# Load environment variables from .env file in utils directory as fallback
utils_dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(utils_dotenv_path):
    load_dotenv(utils_dotenv_path)

class Settings:
    def __init__(self):
        # API Keys
        self.SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
        
        # Supported languages with their codes
        self.SUPPORTED_LANGUAGES = {
            "English": "en-IN",
            "Hindi": "hi-IN",
            "Tamil": "ta-IN",
            "Telugu": "te-IN",
            "Bengali": "bn-IN",
            "Kannada": "kn-IN",
            "Malayalam": "ml-IN",
            "Punjabi": "pa-IN",
            "Marathi": "mr-IN",
            "Gujarati": "gu-IN"
        }
        
        # Sarvam AI API endpoints
        self.SARVAM_BASE_URL = "https://api.sarvam.ai"
        self.SARVAM_STT_ENDPOINT = f"{self.SARVAM_BASE_URL}/speech/recognize"
        self.SARVAM_TTS_ENDPOINT = f"{self.SARVAM_BASE_URL}/speech/synthesize"
        self.SARVAM_TRANSLATE_ENDPOINT = f"{self.SARVAM_BASE_URL}/translate"
        
        # GORQ LLM API settings
        self.GORQ_API_URL = "https://api.gorq.ai/v1"
        
        # Application settings
        self.MAX_AUDIO_DURATION = 30  # seconds - limited to 30s as per user requirement
        self.SAMPLE_RATE = 16000
        self.AUDIO_FORMAT = "wav"
        
        # Loan-related constants
        self.MIN_CREDIT_SCORE = 650
        self.MIN_LOAN_AMOUNT = 10000
        self.MAX_LOAN_AMOUNT = 50000000  # 5 crores

# Create a singleton instance
settings = Settings()