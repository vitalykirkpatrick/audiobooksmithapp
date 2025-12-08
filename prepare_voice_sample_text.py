"""
Helper function to prepare text for voice sample generation with proper name pronunciation.
This ensures that foreign names are converted to their native spelling (e.g., Cyrillic)
so the AI narrator pronounces them correctly with the appropriate accent.
"""

import os
import json
from openai import OpenAI

def prepare_voice_sample_text(raw_excerpt: str, book_info: dict, max_length: int = 500) -> str:
    """
    Transform a raw text excerpt into a narration-ready version with proper name pronunciation.
    
    Args:
        raw_excerpt: The original text excerpt (first ~1000 characters of the book)
        book_info: Dictionary containing book metadata (title, author, genre, etc.)
        max_length: Maximum length of the prepared excerpt (default 500 chars)
    
    Returns:
        Narration-ready text with native-language names for proper pronunciation
    """
    
    # Extract key information
    title = book_info.get('title', 'Unknown')
    author = book_info.get('author', 'Unknown')
    genre = book_info.get('genre', 'Fiction')
    
    # Build the AI prompt for name conversion
    prompt = f"""You are a professional audiobook narrator preparation assistant. Your task is to prepare text for AI voice narration by converting foreign names and places to their native language spelling to ensure correct pronunciation.

**Book Information:**
- Title: {title}
- Author: {author}
- Genre: {genre}

**Cultural Context Analysis:**
Based on the book title "{title}" and author "{author}", identify the cultural/linguistic background (e.g., Ukrainian, Russian, German, French, etc.).

**Task:**
1. Identify all proper nouns (names of people and places) in the excerpt below.
2. Determine their likely native language spelling based on the cultural context.
3. Replace the English transliterations with the native language spelling (e.g., Cyrillic for Ukrainian/Russian names).
4. Preserve the rest of the text exactly as-is.
5. Return ONLY the transformed text, with no explanations or additional commentary.

**Example:**
If the book is Ukrainian, convert:
- "Vitaly" → "Віталій"
- "Evheniya" → "Євгенія"
- "Vasyl" → "Василь"
- "Chernivtsi" → "Чернівці"

**Original Excerpt:**
{raw_excerpt[:max_length]}

**Narration-Ready Text (with native spellings):**"""

    try:
        client = OpenAI()
        
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are an expert in multilingual text preparation for audiobook narration. You convert transliterated names to their native language spelling for accurate pronunciation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        prepared_text = response.choices[0].message.content.strip()
        
        # Ensure we don't exceed max_length
        if len(prepared_text) > max_length:
            prepared_text = prepared_text[:max_length].rsplit(' ', 1)[0] + '...'
        
        return prepared_text
        
    except Exception as e:
        print(f"⚠️ Error preparing voice sample text: {e}")
        print(f"   Falling back to raw excerpt")
        return raw_excerpt[:max_length]


# Test function
if __name__ == "__main__":
    test_excerpt = """VITALY: The MisAdventures of a Ukrainian Orphan
By Vitaly Magidov

PROLOGUE

The rain fell steadily on the streets of Chernivtsi that November evening in 1979. In a small hospital room, a young woman named Evheniya Mikitivna held her newborn son for the first time. She named him Vitaly, which means "full of life" in Ukrainian.

But life had other plans. Within weeks, little Vitaly would find himself at the orphanage on Fastivska Street, under the care of the headmaster Vasyl Ivanovych and the kind nurse everyone called Mamochka."""
    
    test_book_info = {
        "title": "VITALY: The MisAdventures of a Ukrainian Orphan",
        "author": "Vitaly Magidov",
        "genre": "Memoir"
    }
    
    print("Testing voice sample text preparation...")
    print("=" * 70)
    print("\nOriginal Excerpt:")
    print(test_excerpt[:500])
    print("\n" + "=" * 70)
    print("\nPrepared for Narration:")
    
    prepared = prepare_voice_sample_text(test_excerpt, test_book_info, max_length=500)
    print(prepared)
    
    print("\n" + "=" * 70)
    print("\n✅ Test complete!")
