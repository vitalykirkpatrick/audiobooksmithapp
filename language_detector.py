"""
Language Detector for AudiobookSmith
Detects book language from 74 languages supported by ElevenLabs Eleven v3 model
"""

# 74 languages supported by ElevenLabs Eleven v3 model
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'pl': 'Polish',
    'tr': 'Turkish',
    'ru': 'Russian',
    'nl': 'Dutch',
    'cs': 'Czech',
    'ar': 'Arabic',
    'zh': 'Chinese',
    'ja': 'Japanese',
    'ko': 'Korean',
    'hi': 'Hindi',
    'uk': 'Ukrainian',
    'sv': 'Swedish',
    'da': 'Danish',
    'fi': 'Finnish',
    'no': 'Norwegian',
    'ro': 'Romanian',
    'sk': 'Slovak',
    'el': 'Greek',
    'hu': 'Hungarian',
    'id': 'Indonesian',
    'ms': 'Malay',
    'th': 'Thai',
    'vi': 'Vietnamese',
    'bg': 'Bulgarian',
    'hr': 'Croatian',
    'sr': 'Serbian',
    'ca': 'Catalan',
    'lt': 'Lithuanian',
    'lv': 'Latvian',
    'et': 'Estonian',
    'sl': 'Slovenian',
    'mt': 'Maltese',
    'ga': 'Irish',
    'cy': 'Welsh',
    'is': 'Icelandic',
    'mk': 'Macedonian',
    'sq': 'Albanian',
    'az': 'Azerbaijani',
    'kk': 'Kazakh',
    'uz': 'Uzbek',
    'hy': 'Armenian',
    'ka': 'Georgian',
    'he': 'Hebrew',
    'fa': 'Persian',
    'ur': 'Urdu',
    'bn': 'Bengali',
    'ta': 'Tamil',
    'te': 'Telugu',
    'mr': 'Marathi',
    'gu': 'Gujarati',
    'kn': 'Kannada',
    'ml': 'Malayalam',
    'pa': 'Punjabi',
    'ne': 'Nepali',
    'si': 'Sinhala',
    'my': 'Burmese',
    'km': 'Khmer',
    'lo': 'Lao',
    'am': 'Amharic',
    'sw': 'Swahili',
    'af': 'Afrikaans',
    'zu': 'Zulu',
    'xh': 'Xhosa',
    'tl': 'Filipino',
    'jv': 'Javanese',
    'su': 'Sundanese'
}


def detect_language(text):
    """
    Detect language of text using langdetect library
    Returns language code (e.g., 'en', 'ru', 'uk')
    """
    try:
        from langdetect import detect
        lang_code = detect(text[:5000])  # Use first 5000 chars for detection
        
        # Verify it's a supported language
        if lang_code in SUPPORTED_LANGUAGES:
            return lang_code
        else:
            # Default to English if not supported
            return 'en'
    except Exception as e:
        print(f"⚠️ Language detection failed: {e}, defaulting to English")
        return 'en'


def get_language_name(lang_code):
    """Get full language name from code"""
    return SUPPORTED_LANGUAGES.get(lang_code, 'English')


def is_cyrillic_language(lang_code):
    """Check if language uses Cyrillic script"""
    cyrillic_languages = ['ru', 'uk', 'bg', 'sr', 'mk', 'kk', 'uz']
    return lang_code in cyrillic_languages


if __name__ == "__main__":
    # Test language detection
    test_texts = {
        'en': "This is a test in English",
        'ru': "Это тест на русском языке",
        'uk': "Це тест українською мовою",
        'es': "Esta es una prueba en español",
        'fr': "Ceci est un test en français"
    }
    
    for expected_lang, text in test_texts.items():
        detected = detect_language(text)
        print(f"Expected: {expected_lang}, Detected: {detected}, Name: {get_language_name(detected)}")
