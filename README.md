# Multilingual Conversational Loan Advisor

A multilingual conversational AI assistant that helps users understand loan eligibility, guides them through the loan application process, and provides basic financial literacy tips.

## Features

- **Loan Eligibility Check**: Ask a few questions, understand the user's financial situation, and provide an eligibility check for different types of loans.
- **Loan Application Guidance**: Guide users through the steps to apply for a loan, helping them with required documents and information.
- **Financial Literacy Tips**: Offer simple, easy-to-understand financial tips, such as saving strategies or tips on improving credit scores.
- **Multilingual Support**: Interact with users in multiple Indian languages.
- **Voice & Text Input**: Support for both voice and text-based interactions.
- **30-Second Audio Limit**: Audio processing is limited to 30 seconds to ensure efficient processing.
- **Language-Preserving Responses**: Responses are delivered in the same language as the input.
- **Exclusive Sarvam AI Translation**: Uses only Sarvam AI for all translation needs, ensuring high-quality, consistent translations.

## Setup

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your API keys:
   ```
   SARVAM_API_KEY=your_sarvam_api_key
   GEMINI_API_KEY=your_gemini_api_key  # Only needed for the Gemini fallback example
   ```
4. Run the application:
   ```
   streamlit run app.py
   ```

## Usage

1. Select your preferred language from the dropdown menu.
2. Choose between voice or text input.
3. If using voice, click the "Record" button and speak your query.
4. If using text, type your query in the text box and press Enter.
5. The assistant will respond in the same language you used for your input, regardless of the language selected in the sidebar.

## Language Handling

The system now uses a two-step approach for handling multilingual responses:
1. **Translation**: First, the English response is translated to the detected input language.
2. **Transliteration**: Then, the translated text is transliterated to ensure it uses the correct script for the language.

This ensures that responses are not only in the same language as the input, but also use the appropriate script and formatting.

### Example:
For a Kannada input like:
```
ನನಗೆ 32 ವರ್ಷ ವಯಸ್ಸು, ತಿಂಗಳಿಗೆ 45,000 ರೂಪಾಯಿ ಸಂಬಳ ಇದೆ, ಮತ್ತು 750 ಕ್ರೆಡಿಟ್ ಸ್ಕೋರ್ ಇದೆ.. ನಾನು ಗೃಹ ಸಾಲದ ಅರ್ಹತೆ ಹೊಂದಿದ್ದೇನೆಯೇ? ನಾನು ಕಳೆದ ಐದು ವರ್ಷಗಳಿಂದ ವೇತನಭೋಗಿ ಉದ್ಯೋಗಿಯಾಗಿದ್ದೇನೆ.
```

The system will:
1. Detect the language as Kannada
2. Translate it to English for processing
3. Generate a response in English
4. Translate the response back to Kannada
5. Transliterate the translated text to ensure proper Kannada script


Available modes:
- **translate**: Translate text
- **transliterate**: Transliterate text
- **stt**: Speech-to-Text conversion (requires --audio-file)
- **tts**: Text-to-Speech conversion
- **record**: Record audio and convert to text
- **all**: Run all demo functions

## Supported Languages

- English (en-IN)
- Hindi (hi-IN)
- Tamil (ta-IN)
- Telugu (te-IN)
- Bengali (bn-IN)
- Kannada (kn-IN)
- Malayalam (ml-IN)
- Punjabi (pa-IN)
- Marathi (mr-IN)
- Gujarati (gu-IN)

## Sarvam AI API Implementation

The application uses the Sarvam AI API for the following functions:

1. **Text Translation**: Translate text between languages
2. **Text Transliteration**: Transliterate text between scripts
3. **Speech-to-Text**: Convert audio to text
4. **Speech-to-Text Translation**: Convert audio to text and translate
5. **Text-to-Speech**: Convert text to audio

All API interactions are implemented using the `requests` library with support for multipart form data where needed. The application relies exclusively on Sarvam AI for all translation needs, with no fallback to third-party translation services.

## Technology Stack

- Frontend: Streamlit
- Language Processing: Sarvam AI API (via requests)
- LLM Provider: GORQ
- Data Storage: Local JSON
- Audio Processing: pydub, sounddevice 
