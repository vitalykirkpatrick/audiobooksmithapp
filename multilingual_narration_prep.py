"""
Multilingual Narration Preparation System
Supports 74 languages via ElevenLabs Eleven v3 model
"""

import os
from openai import OpenAI

# Top 20 languages for audiobooks
SUPPORTED_LANGUAGES = {
    "eng": "English", "spa": "Spanish", "fra": "French", "deu": "German",
    "ita": "Italian", "por": "Portuguese", "rus": "Russian", "ukr": "Ukrainian",
    "pol": "Polish", "jpn": "Japanese", "cmn": "Mandarin Chinese", "ara": "Arabic",
    "hin": "Hindi", "kor": "Korean", "nld": "Dutch", "swe": "Swedish",
    "tur": "Turkish", "heb": "Hebrew", "ell": "Greek", "fas": "Persian"
}

def detect_book_language(book_info, text_sample):
    """Detect primary language and cultural context"""
    client = OpenAI()
    
    prompt = f"""Analyze this book and determine its primary language/cultural context.

Book: {book_info.get('title')} by {book_info.get('author')}
Sample: {text_sample[:500]}

Identify the primary language code (eng, spa, fra, deu, ita, por, rus, ukr, pol, jpn, cmn, ara, hin, kor, etc.)

Response (JSON only):
{{
    "primary_language": "ukr",
    "language_name": "Ukrainian",
    "script": "Cyrillic",
    "confidence": 0.95
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        import json
        return json.loads(response.choices[0].message.content)
    except:
        return {"primary_language": "eng", "language_name": "English", "script": "Latin", "confidence": 0.5}

print("✅ Multilingual narration prep module loaded")
